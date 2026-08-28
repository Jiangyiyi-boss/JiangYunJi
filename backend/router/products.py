from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    CategoryResponse, CategoryCreate,
    ProductResponse, ProductCreate, ProductUpdate, ProductListResponse,
)
from crud.products import (
    get_category_tree, create_category, update_category, delete_category,
    get_products, get_product_by_id, create_product, update_product,
    update_product_status,
    toggle_favorite, get_user_favorites,
)
from dependencies import get_current_user, get_current_user_or_none, require_role
from models import User
from utils.es_sync_helper import safe_sync_product, safe_delete_product

router = APIRouter(prefix="/api/products", tags=["商品"])


# ==================== 分类 ====================

@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return get_category_tree(db)


@router.post("/categories", response_model=CategoryResponse)
def create_cat(
    data: CategoryCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return CategoryResponse.model_validate(create_category(db, data))


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_cat(
    category_id: int,
    name: str = None,
    icon: str = None,
    sort: int = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    from crud.products import get_category_by_id
    cat = get_category_by_id(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if icon is not None:
        kwargs["icon"] = icon
    if sort is not None:
        kwargs["sort"] = sort
    return CategoryResponse.model_validate(update_category(db, cat, **kwargs))


@router.delete("/categories/{category_id}")
def delete_cat(
    category_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if not delete_category(db, category_id):
        raise HTTPException(status_code=404, detail="分类不存在")
    return {"message": "删除成功"}


# ==================== 商品 ====================

@router.get("", response_model=ProductListResponse)
def list_products(
    skip: int = 0,
    limit: int = 20,
    category_id: int = None,
    artisan_id: int = None,
    keyword: str = None,
    sort_by: str = "created_at",
    is_recommend: bool = None,
    status: str = "approved",
    db: Session = Depends(get_db),
):
    items, total = get_products(
        db, skip=skip, limit=limit, category_id=category_id,
        artisan_id=artisan_id, keyword=keyword, sort_by=sort_by,
        is_recommend=is_recommend, status=status,
    )

    from crud.products import get_stock_display
    result = []
    for p in items:
        resp = ProductResponse.model_validate(p)
        resp.stock_display = get_stock_display(p.stock)
        if resp.specs:
            for spec in resp.specs:
                spec["stock_display"] = get_stock_display(spec.get("stock", 0) or 0)
        result.append(resp)

    return ProductListResponse(total=total, items=result)


@router.post("", response_model=ProductResponse)
def create_prod(
    data: ProductCreate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=400, detail="请先完成匠人认证")
    return ProductResponse.model_validate(create_product(db, artisan.id, data))


@router.get("/my", response_model=ProductListResponse)
def get_my_products(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """商家查看自己的商品列表（所有状态）"""
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=400, detail="请先完成匠人认证")

    items, total = get_products(
        db, skip=skip, limit=limit, artisan_id=artisan.id, status=status,
    )

    result = []
    for p in items:
        resp = ProductResponse.model_validate(p)
        resp.stock_display = f"库存: {p.stock} 件"
        result.append(resp)

    return ProductListResponse(total=total, items=result)


@router.get("/pending", response_model=ProductListResponse)
def get_pending_products(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_products(db, skip=skip, limit=limit, status="pending")
    return ProductListResponse(
        total=total,
        items=[ProductResponse.model_validate(p) for p in items],
    )


@router.get("/favorites", response_model=ProductListResponse)
def get_my_favorites(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = get_user_favorites(db, current_user.id, skip=skip, limit=limit)
    return ProductListResponse(
        total=total,
        items=[ProductResponse.model_validate(p) for p in items],
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_or_none),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    from crud.products import get_stock_display
    from crud.users import get_artisan_by_user_id

    # 判断是否为该商品的商家或管理员（可看精确库存）
    is_owner_or_admin = False
    if current_user:
        if current_user.role == "admin":
            is_owner_or_admin = True
        elif current_user.role == "artisan":
            artisan = get_artisan_by_user_id(db, current_user.id)
            if artisan and artisan.id == product.artisan_id:
                is_owner_or_admin = True

    # 下架/未上架商品仅商家/管理员可查看，普通用户和其他商家返回 404
    if product.status not in ("approved",) and not is_owner_or_admin:
        if product.status == "offline":
            raise HTTPException(status_code=404, detail="商品已下架")
        else:
            raise HTTPException(status_code=404, detail="商品暂不可查看")

    # 构建响应
    resp = ProductResponse.model_validate(product)

    # 消费者端：模糊库存展示
    if not is_owner_or_admin:
        resp.stock_display = get_stock_display(product.stock)
        # 对每个 SKU spec 也返回模糊库存
        if resp.specs:
            for spec in resp.specs:
                spec_stock = spec.get("stock", 0) or 0
                spec["stock_display"] = get_stock_display(spec_stock)
    else:
        # 商家/管理员：显示精确库存
        resp.stock_display = f"库存: {product.stock} 件"

    return resp


@router.put("/{product_id}", response_model=ProductResponse)
def update_prod(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if product.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权修改")
    updated = update_product(db, product, data)
    # 已上架商品编辑后同步 ES，保证搜索展示最新名称/价格/描述
    if updated.status == "approved":
        safe_sync_product(db, product_id)
    return ProductResponse.model_validate(updated)


@router.post("/{product_id}/approve")
def approve_product(
    product_id: int,
    commission_rate: float = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    from crud.commissions import get_commission_rate_for_category
    from decimal import Decimal
    product = db.query(__import__('models').Product).filter(__import__('models').Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 如果指定了佣金比例，使用指定的；否则根据分类自动匹配
    if commission_rate is not None:
        product.commission_rate = Decimal(str(commission_rate))
    else:
        product.commission_rate = get_commission_rate_for_category(db, product.category_id)

    # 佣金状态设为待确认
    product.commission_status = "pending"
    db.commit()

    # 根据 listing_mode 决定审核后的状态
    if product.listing_mode == "manual":
        update_product_status(db, product_id, "reviewed")
        # 审核后暂不上架，清理 ES 中可能存在的旧文档
        safe_delete_product(product_id)
        return {"message": "审核通过，等待商家确认佣金后手动上架", "commission_rate": float(product.commission_rate)}
    else:
        # auto 模式：佣金未确认前暂不自动上架，设为 reviewed
        update_product_status(db, product_id, "reviewed")
        # 审核后暂不上架，清理 ES 中可能存在的旧文档
        safe_delete_product(product_id)
        return {"message": "审核通过，请先确认佣金比例", "commission_rate": float(product.commission_rate)}


@router.post("/{product_id}/reject")
def reject_product(
    product_id: int,
    reason: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    update_product_status(db, product_id, "rejected", reason)
    # 驳回后清理 ES 文档
    safe_delete_product(product_id)
    return {"message": "已拒绝"}


@router.post("/{product_id}/list")
def list_product(
    product_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """商家手动上架已审核通过的商品"""
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan or product.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if product.status != "reviewed":
        raise HTTPException(status_code=400, detail="仅审核通过待上架的商品可手动上架")
    if product.commission_status != "confirmed":
        raise HTTPException(status_code=400, detail="请先确认佣金比例后再上架")

    update_product_status(db, product_id, "approved")
    # 商品上架后同步到 ES，之后可被搜索到
    safe_sync_product(db, product_id)
    return {"message": "已上架"}


@router.post("/{product_id}/confirm-commission")
def confirm_commission(
    product_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """商家确认佣金比例，锁定后不可再申诉"""
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan or product.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if product.commission_status not in ("pending", "appeal_rejected"):
        raise HTTPException(status_code=400, detail="当前佣金状态不可确认")

    product.commission_status = "confirmed"
    db.commit()

    return {"message": "佣金已确认", "commission_rate": float(product.commission_rate)}


@router.post("/{product_id}/offline")
def offline_product(
    product_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    update_product_status(db, product_id, "offline")
    # 下架后从 ES 删除，避免搜索到已下架商品
    safe_delete_product(product_id)
    return {"message": "已下架"}


# ==================== 收藏 ====================

@router.post("/{product_id}/browse")
def record_product_browse(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录商品浏览历史"""
    from models import BrowseHistory
    from datetime import datetime

    # 查已有记录（同一商品，当天只记一次）
    today = datetime.now().date()
    existing = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current_user.id,
        BrowseHistory.product_id == product_id,
        BrowseHistory.type == "product",
    ).order_by(BrowseHistory.browsed_at.desc()).first()

    if existing and existing.browsed_at.date() == today:
        existing.browsed_at = datetime.now()
        db.commit()
        return {"message": "已更新浏览时间"}

    record = BrowseHistory(
        user_id=current_user.id,
        product_id=product_id,
        type="product",
    )
    db.add(record)
    db.commit()
    return {"message": "已记录"}


@router.post("/{product_id}/favorite")
def favorite_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = toggle_favorite(db, current_user.id, product_id)
    return result


# ==================== 收藏 ====================
