from sqlalchemy.orm import Session
from models import CartItem, Product
from schemas import CartItemCreate


def get_cart_items(db: Session, user_id: int):
    return db.query(CartItem).filter(CartItem.user_id == user_id).all()


def add_to_cart(db: Session, user_id: int, data: CartItemCreate) -> CartItem:
    # 校验库存
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise ValueError("商品不存在")

    # 如果有规格，检查对应规格的库存和限购
    max_per_user = None
    stock = product.stock or 0
    if data.spec_name and product.specs:
        import json
        specs = product.specs if isinstance(product.specs, list) else json.loads(product.specs or "[]")
        for spec in specs:
            if spec.get("name") == data.spec_name:
                stock = spec.get("stock", 0) or 0
                limit = spec.get("limit_per_user", 0)
                if limit > 0:
                    max_per_user = limit
                break

    if stock <= 0:
        raise ValueError("该商品已售罄")

    # If same product + same spec, increase qty; otherwise create new item
    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == data.product_id,
        CartItem.spec_name == (data.spec_name or ""),
    ).first()

    new_qty = (existing.qty if existing else 0) + data.qty

    if new_qty > stock:
        raise ValueError(f"库存不足，最多可购买 {stock} 件")

    if max_per_user and new_qty > max_per_user:
        raise ValueError(f"该规格限购 {max_per_user} 件")

    if existing:
        existing.qty = new_qty
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(
        user_id=user_id,
        product_id=data.product_id,
        qty=data.qty,
        spec_name=data.spec_name or "",
        spec_price=data.spec_price,
        spec_sku=data.spec_sku or "",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_cart_item(db: Session, item_id: int, qty: int) -> CartItem:
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if item:
        if qty <= 0:
            db.delete(item)
            db.commit()
            return None
        item.qty = qty
        db.commit()
        db.refresh(item)
    return item


def remove_cart_item(db: Session, item_id: int) -> bool:
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def clear_cart(db: Session, user_id: int):
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
