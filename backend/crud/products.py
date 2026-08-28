from sqlalchemy.orm import Session
from models import Category, Product, ProductFavorite
from schemas import CategoryCreate, ProductCreate, ProductUpdate
import redis
import json
from config import settings


class RedisCache:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=2,
            )
            self.client.ping()
            self.available = True
        except Exception:
            self.available = False
            self.client = None

    def get(self, key):
        if not self.available:
            return None
        try:
            return self.client.get(key)
        except Exception:
            return None

    def setex(self, key, ttl, value):
        if not self.available:
            return
        try:
            self.client.setex(key, ttl, value)
        except Exception:
            pass

    def delete(self, key):
        if not self.available:
            return
        try:
            self.client.delete(key)
        except Exception:
            pass


redis_client = RedisCache()

CACHE_KEY_CATEGORIES = "jiangyunji:categories:tree"
CACHE_KEY_CATEGORY_TTL = 3600
CACHE_KEY_CAT_DESC = "jiangyunji:category:{}:descendants"   # 子孙分类 ID 集合
CACHE_KEY_CAT_COUNT = "jiangyunji:category:{}:product_count"  # 分类商品数量
CACHE_KEY_CAT_DESC_TTL = 1800  # 30 分钟
CACHE_KEY_CAT_COUNT_TTL = 600  # 10 分钟


# ==================== 分类-Redis 挂载辅助 ====================

def _walk_tree_collect(node, target_id, collected):
    """递归遍历分类树，收集 target_id 的所有子孙节点 ID"""
    if node.get("id") == target_id:
        _collect_descendants(node, collected)
        return True
    for child in node.get("children", []):
        if _walk_tree_collect(child, target_id, collected):
            return True
    return False


def _collect_descendants(node, collected):
    """收集某个节点下所有子孙的 ID"""
    for child in node.get("children", []):
        collected.append(child["id"])
        _collect_descendants(child, collected)


def get_category_descendant_ids(category_id: int) -> list:
    """从 Redis 缓存的分类树中获取某个分类的所有子孙分类 ID（含自身）"""
    cache_key = CACHE_KEY_CAT_DESC.format(category_id)
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 从分类树中提取
    tree = json.loads(redis_client.get(CACHE_KEY_CATEGORIES) or "[]")
    if not tree:
        return [category_id]

    descendants = [category_id]
    for root in tree:
        if _walk_tree_collect(root, category_id, descendants):
            break

    redis_client.setex(cache_key, CACHE_KEY_CAT_DESC_TTL, json.dumps(descendants))
    return descendants


def get_category_product_count(category_id: int, db: Session) -> int:
    """获取某个分类及其子孙分类下的商品总数（优先 Redis 缓存）"""
    cache_key = CACHE_KEY_CAT_COUNT.format(category_id)
    cached = redis_client.get(cache_key)
    if cached is not None:
        return int(cached)

    # 从 MySQL 统计
    from sqlalchemy import func
    descendant_ids = get_category_descendant_ids(category_id)
    count = db.query(func.count(Product.id)).filter(
        Product.category_id.in_(descendant_ids),
        Product.status == "approved",
    ).scalar() or 0

    redis_client.setex(cache_key, CACHE_KEY_CAT_COUNT_TTL, str(count))
    return count


def invalidate_category_cache(category_id: int = None):
    """失效分类相关缓存
    如果 category_id 为 None，清除所有分类缓存
    """
    if category_id:
        # 失效该分类及其所有祖先分类的缓存（因为祖先的商品数量也变了）
        tree = json.loads(redis_client.get(CACHE_KEY_CATEGORIES) or "[]")
        ids_to_invalidate = {category_id}

        # 向上查找所有祖先
        def _find_ancestors(node, target, ancestors):
            for child in node.get("children", []):
                if child["id"] == target:
                    ancestors.append(node["id"])
                    return True
                if _find_ancestors(child, target, ancestors):
                    ancestors.append(node["id"])
                    return True
            return False

        for root in tree:
            ancestors = []
            if root["id"] == category_id:
                break
            if _find_ancestors(root, category_id, ancestors):
                ids_to_invalidate.update(ancestors)
                break

        for cid in ids_to_invalidate:
            redis_client.delete(CACHE_KEY_CAT_DESC.format(cid))
            redis_client.delete(CACHE_KEY_CAT_COUNT.format(cid))
    else:
        # 清除所有 match 到的缓存 key（简单方式：逐个已知分类）
        pass  # 大规模清理可通过 SCAN 实现，按需调用


# ==================== 库存展示辅助 ====================

def get_stock_display(stock: int) -> str:
    """模糊库存展示（消费者端，不暴露任何数字）"""
    if stock > 20:
        return "有货"
    elif stock > 0:
        return "库存紧张"
    else:
        return "已售罄"


def get_category_by_id(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


def get_all_categories(db: Session):
    return db.query(Category).order_by(Category.sort, Category.id).all()


def get_category_tree(db: Session) -> list:
    """获取分类树，每个节点附带商品数量"""
    cached = redis_client.get(CACHE_KEY_CATEGORIES)
    if cached:
        tree = json.loads(cached)
        # 补充商品数量（轻量查询，不在树缓存中存储数量，因为数量变化频繁）
        _enrich_tree_with_counts(tree, db)
        return tree

    categories = get_all_categories(db)
    tree = build_category_tree(categories)

    redis_client.setex(CACHE_KEY_CATEGORIES, CACHE_KEY_CATEGORY_TTL, json.dumps(tree))
    _enrich_tree_with_counts(tree, db)
    return tree


def _enrich_tree_with_counts(tree: list, db: Session):
    """给分类树每个节点挂载商品数量"""
    # 收集所有分类 ID
    all_ids = []

    def _collect(node):
        all_ids.append(node["id"])
        for child in node.get("children", []):
            _collect(child)

    for root in tree:
        _collect(root)

    # 批量查询每个分类的商品数（含子孙）
    if all_ids:
        for node_id in all_ids:
            count = get_category_product_count(node_id, db)
            # 找到对应节点
            def _set_count(nodes):
                for n in nodes:
                    if n["id"] == node_id:
                        n["product_count"] = count
                    _set_count(n.get("children", []))

            _set_count(tree)


def build_category_tree(categories: list) -> list:
    category_map = {}
    roots = []

    for cat in categories:
        node = {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "icon": cat.icon,
            "sort": cat.sort or 0,
            "level": cat.level,
            "children": [],
        }
        category_map[cat.id] = node

    for cat in categories:
        node = category_map[cat.id]
        if cat.parent_id is None:
            roots.append(node)
        else:
            parent = category_map.get(cat.parent_id)
            if parent:
                parent["children"].append(node)

    roots.sort(key=lambda x: x["sort"] or 0)
    for root in roots:
        root["children"].sort(key=lambda x: x["sort"] or 0)

    return roots


def create_category(db: Session, data: CategoryCreate) -> Category:
    parent = None
    level = 1
    if data.parent_id:
        parent = get_category_by_id(db, data.parent_id)
        level = parent.level + 1 if parent else 1

    category = Category(
        name=data.name,
        parent_id=data.parent_id,
        icon=data.icon,
        sort=data.sort,
        level=level,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    # Invalidate cache
    redis_client.delete(CACHE_KEY_CATEGORIES)
    return category


def update_category(db: Session, category: Category, **kwargs) -> Category:
    for key, value in kwargs.items():
        if hasattr(category, key):
            setattr(category, key, value)
    db.commit()
    db.refresh(category)
    redis_client.delete(CACHE_KEY_CATEGORIES)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    category = get_category_by_id(db, category_id)
    if category:
        db.delete(category)
        db.commit()
        redis_client.delete(CACHE_KEY_CATEGORIES)
        return True
    return False


# ==================== 商品 ====================

def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 20,
                 category_id: int = None, artisan_id: int = None,
                 keyword: str = None, status: str = "approved",
                 sort_by: str = "created_at", is_recommend: bool = None):
    query = db.query(Product)

    if status:
        query = query.filter(Product.status == status)
    if category_id:
        # 从 Redis 分类树获取所有子孙分类 ID（含自身）
        descendant_ids = get_category_descendant_ids(category_id)
        query = query.filter(Product.category_id.in_(descendant_ids))
    if artisan_id:
        query = query.filter(Product.artisan_id == artisan_id)
    if keyword:
        query = query.filter(Product.name.contains(keyword))
    if is_recommend is not None:
        query = query.filter(Product.is_recommend == is_recommend)

    total = query.count()

    if sort_by == "sales":
        query = query.order_by(Product.sales.desc())
    elif sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    items = query.offset(skip).limit(limit).all()
    return items, total


def create_product(db: Session, artisan_id: int, data: ProductCreate) -> Product:
    # 从 SKU specs 自动计算价格和库存
    specs = data.specs or []
    if specs:
        computed_price = min(s.get("price", 0) or 0 for s in specs)
        computed_stock = sum(s.get("stock", 0) or 0 for s in specs)
    else:
        computed_price = data.price or 0
        computed_stock = data.stock or 0

    product = Product(
        name=data.name,
        description=data.description,
        price=computed_price,
        stock=computed_stock,
        images=data.images,
        category_id=data.category_id,
        artisan_id=artisan_id,
        status="pending",
        listing_mode=data.listing_mode,
        shipping_type=data.shipping_type,
        shipping_fee=data.shipping_fee,
        ship_address=data.ship_address,
        ship_time=data.ship_time,
        specs=specs,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    invalidate_category_cache(product.category_id)
    return product


def update_product(db: Session, product: Product, data: ProductUpdate) -> Product:
    update_data = data.model_dump(exclude_unset=True)

    # 如果更新了 specs，自动重新计算 price 和 stock
    if "specs" in update_data:
        specs = update_data["specs"] or []
        if specs:
            update_data["price"] = min(s.get("price", 0) or 0 for s in specs)
            update_data["stock"] = sum(s.get("stock", 0) or 0 for s in specs)
        else:
            # 没有 specs 时保留原 price/stock，或由调用方指定
            if "price" not in update_data:
                update_data["price"] = product.price
            if "stock" not in update_data:
                update_data["stock"] = product.stock

    # 记录旧状态，用于判断是否下架
    old_status = product.status

    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)

    # 失效分类缓存（如果分类变了，新旧分类都要失效）
    invalidate_category_cache(product.category_id)
    if "category_id" in update_data:
        invalidate_category_cache(update_data["category_id"])

    # 商品下架时，将关联该商品的帖子改为草稿，并禁用关联轮播图
    if old_status != "offline" and product.status == "offline":
        try:
            from crud.forum_mongo import draft_posts_by_product
            draft_posts_by_product(product.id)
        except Exception as e:
            print(f"下架商品时处理关联帖子失败: {e}")
        
        try:
            from crud.banners import disable_banners_by_product
            disable_banners_by_product(db, product.id)
        except Exception as e:
            print(f"下架商品时禁用关联轮播图失败: {e}")

    return product


def update_product_status(db: Session, product_id: int, status: str, reject_reason: str = "") -> Product:
    product = get_product_by_id(db, product_id)
    if product:
        product.status = status
        product.reject_reason = reject_reason
        db.commit()
        db.refresh(product)
        # 上下架状态变更时失效分类商品计数缓存
        invalidate_category_cache(product.category_id)
        # 商品下架时，将关联该商品的帖子改为草稿，并禁用关联轮播图
        if status == "offline":
            try:
                from crud.forum_mongo import draft_posts_by_product
                draft_posts_by_product(product_id)
            except Exception as e:
                print(f"下架商品时处理关联帖子失败: {e}")
            
            try:
                from crud.banners import disable_banners_by_product
                disable_banners_by_product(db, product_id)
            except Exception as e:
                print(f"下架商品时禁用关联轮播图失败: {e}")
    return product


def update_product_stock(db: Session, product_id: int, delta: int) -> Product:
    product = get_product_by_id(db, product_id)
    if product:
        product.stock += delta
        if product.stock < 0:
            product.stock = 0
        db.commit()
        db.refresh(product)
    return product


# ==================== 收藏 ====================

def toggle_favorite(db: Session, user_id: int, product_id: int):
    existing = db.query(ProductFavorite).filter(
        ProductFavorite.user_id == user_id,
        ProductFavorite.product_id == product_id,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "removed"}
    else:
        fav = ProductFavorite(user_id=user_id, product_id=product_id)
        db.add(fav)
        db.commit()
        return {"action": "added"}


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(Product).join(
        ProductFavorite, Product.id == ProductFavorite.product_id
    ).filter(ProductFavorite.user_id == user_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total
