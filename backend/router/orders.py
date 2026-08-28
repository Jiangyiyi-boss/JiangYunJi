from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    CartItemCreate, CartItemResponse,
    OrderCreate, OrderResponse,
    AddressCreate, AddressResponse,
)
from crud.carts import (
    get_cart_items, add_to_cart, update_cart_item,
    remove_cart_item, clear_cart,
)
from crud.orders import (
    create_order, get_order_by_id, get_user_orders, get_all_orders, get_artisan_orders,
    cancel_order, pay_order, ship_order, complete_order,
    get_order_stats,
)
from crud.services import (
    get_addresses, create_address, update_address, delete_address,
)
from dependencies import get_current_user, require_role
from models import User, Artisan
from utils.es_sync_helper import safe_update_product_stock, safe_update_product_sales
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["订单"])


def _sync_order_product_stats(db: Session, order) -> None:
    """订单创建/取消后，把商品最新库存与销量同步到 ES（失败不影响订单流程）"""
    from models import Product
    try:
        for item in order.items:
            if not item.product_id:
                continue
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            safe_update_product_stock(item.product_id, product.stock or 0)
            safe_update_product_sales(item.product_id, product.sales or 0)
    except Exception as e:
        logger.error("同步订单商品 ES 数据异常 order_id=%s: %s", getattr(order, "id", "?"), e)


# ==================== 购物车 ====================

@router.get("/cart", response_model=list[CartItemResponse])
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [CartItemResponse.model_validate(item) for item in get_cart_items(db, current_user.id)]


@router.post("/cart", response_model=CartItemResponse)
def add_cart(
    data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return CartItemResponse.model_validate(add_to_cart(db, current_user.id, data))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/cart/{item_id}", response_model=CartItemResponse)
def update_cart(
    item_id: int,
    qty: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = update_cart_item(db, item_id, qty)
    if result is None:
        return {"message": "已删除"}
    return CartItemResponse.model_validate(result)


@router.delete("/cart/{item_id}")
def remove_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    remove_cart_item(db, item_id)
    return {"message": "已删除"}


@router.delete("/cart")
def clear_user_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clear_cart(db, current_user.id)
    return {"message": "购物车已清空"}


# ==================== 地址 ====================

@router.get("/addresses", response_model=list[AddressResponse])
def get_user_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [AddressResponse.model_validate(a) for a in get_addresses(db, current_user.id)]


@router.post("/addresses", response_model=AddressResponse)
def create_user_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AddressResponse.model_validate(create_address(db, current_user.id, data))


@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_user_address(
    address_id: int,
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from crud.services import get_addresses as _get_addrs
    address = next((a for a in _get_addrs(db, current_user.id) if a.id == address_id), None)
    if not address:
        raise HTTPException(status_code=404, detail="地址不存在")
    return AddressResponse.model_validate(update_address(db, address, data))


@router.delete("/addresses/{address_id}")
def delete_user_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not delete_address(db, address_id, current_user.id):
        raise HTTPException(status_code=404, detail="地址不存在")
    return {"message": "删除成功"}


# ==================== 订单 ====================

@router.post("", response_model=OrderResponse)
def create_new_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        order = create_order(db, current_user, data)
        logger.info("订单创建成功 order_no=%s user_id=%s amount=%s", order.order_no, current_user.id, order.pay_amount)
        # 同步 ES 中商品库存/销量
        _sync_order_product_stats(db, order)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        logger.warning("订单创建失败 user_id=%s error=%s", current_user.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=dict)
def get_my_orders(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    goods_type: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = get_user_orders(db, current_user.id, skip=skip, limit=limit, status=status, goods_type=goods_type)
    return {"total": total, "items": [OrderResponse.model_validate(o) for o in items]}


@router.post("/course", response_model=OrderResponse)
def create_course_order_api(
    course_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建课程订单（无需地址）"""
    from crud.orders import create_course_order as _create_course_order
    try:
        order = _create_course_order(db, current_user, course_id)
        logger.info("课程订单创建成功 order_no=%s user_id=%s course_id=%s", order.order_no, current_user.id, course_id)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        logger.warning("课程订单创建失败 user_id=%s error=%s", current_user.id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 匠人订单（商家看自己商品的订单） ====================
# 注意：必须在 /{order_id} 之前定义，否则会被动态路由拦截

@router.get("/artisan", response_model=dict)
def get_artisan_order_list(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    goods_type: Optional[int] = None,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    artisan = db.query(Artisan).filter(Artisan.user_id == current_user.id).first()
    if not artisan:
        raise HTTPException(status_code=404, detail="匠人信息不存在")
    items, total = get_artisan_orders(db, artisan.id, skip=skip, limit=limit, status=status, goods_type=goods_type)
    # 查询已申诉的订单ID
    from crud.commissions import get_artisan_appeals
    appeal_orders, _ = get_artisan_appeals(db, artisan.id, skip=0, limit=9999)
    appealed_order_ids = {a.order_id for a in appeal_orders}

    result_items = []
    for o in items:
        item = OrderResponse.model_validate(o)
        item.has_appeal = o.id in appealed_order_ids
        result_items.append(item)
    return {"total": total, "items": result_items}


@router.post("/artisan/{order_id}/ship", response_model=OrderResponse)
def ship_artisan_order(
    order_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """匠人发货"""
    artisan = db.query(Artisan).filter(Artisan.user_id == current_user.id).first()
    if not artisan:
        raise HTTPException(status_code=404, detail="匠人信息不存在")

    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 检查订单中是否包含该匠人的商品
    from models import OrderItem, Product
    has_product = db.query(OrderItem).filter(
        OrderItem.order_id == order_id,
        OrderItem.product_id == Product.id,
        Product.artisan_id == artisan.id,
    ).first()
    if not has_product:
        raise HTTPException(status_code=403, detail="无权操作此订单")

    try:
        order = ship_order(db, order_id)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 管理员订单 ====================
# 注意：必须在 /{order_id} 之前定义

@router.get("/admin/all", response_model=dict)
def get_all_orders_admin(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_all_orders(db, skip=skip, limit=limit, status=status, keyword=keyword)
    return {"total": total, "items": [OrderResponse.model_validate(o) for o in items]}


@router.post("/admin/{order_id}/ship", response_model=OrderResponse)
def ship_admin_order(
    order_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    try:
        order = ship_order(db, order_id)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/stats")
def get_stats(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return get_order_stats(db)


# ==================== 动态路由（放在最后） ====================

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_user_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        order = cancel_order(db, order_id, current_user.id)
        logger.info("订单取消 order_id=%s user_id=%s", order_id, current_user.id)
        # 取消订单恢复了库存，同步 ES 中商品库存/销量
        _sync_order_product_stats(db, order)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        logger.warning("订单取消失败 order_id=%s error=%s", order_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/pay", response_model=OrderResponse)
def pay_user_order(
    order_id: int,
    pay_method: str = "wechat",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        order = pay_order(db, order_id, pay_method)
        logger.info("订单支付成功 order_id=%s method=%s", order_id, pay_method)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        logger.warning("订单支付失败 order_id=%s error=%s", order_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/complete", response_model=OrderResponse)
def complete_user_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        order = complete_order(db, order_id)
        logger.info("订单完成 order_id=%s user_id=%s", order_id, current_user.id)
        return OrderResponse.model_validate(order)
    except ValueError as e:
        logger.warning("订单完成失败 order_id=%s error=%s", order_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))
