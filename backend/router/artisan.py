from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    ArtisanApply, ArtisanResponse, ArtisanUpdate,
    CustomOrderCreate, CustomOrderResponse, CustomMessageCreate, CustomMessageResponse, CustomQuote,
    TransactionResponse,
)
from crud.users import (
    get_artisan_by_user_id, create_artisan_application,
    get_all_artisans, approve_artisan, reject_artisan, update_artisan,
)
from crud.services import (
    toggle_artisan_follow,
    create_custom_order, get_custom_orders, get_custom_order_by_id,
    quote_custom_order, accept_custom_order, update_custom_progress,
    create_custom_message, get_custom_messages,
    get_transactions,
)
from dependencies import get_current_user, get_current_user_or_none, require_role
from models import User

router = APIRouter(prefix="/api/artisan", tags=["匠人"])


# ==================== 匠人认证 ====================

@router.post("/apply", response_model=ArtisanResponse)
def apply_artisan(
    data: ArtisanApply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = get_artisan_by_user_id(db, current_user.id)
    # 店铺头像直接使用用户当前头像，申请页不再手动填写
    data.shop_avatar = current_user.avatar or ""
    if existing:
        if existing.status == "rejected":
            # Allow re-application: update existing record and reset to pending
            existing.real_name = data.real_name
            existing.id_card = data.id_card
            existing.specialty = data.specialty
            existing.bio = data.bio
            existing.certifications = data.certifications
            existing.contact = data.contact
            existing.shop_name = data.shop_name
            existing.shop_avatar = data.shop_avatar
            existing.status = "pending"
            existing.reject_reason = ""
            db.commit()
            db.refresh(existing)
            return ArtisanResponse.model_validate(existing)
        raise HTTPException(status_code=400, detail="已提交过申请，请等待审核")
    return ArtisanResponse.model_validate(create_artisan_application(db, current_user.id, data))


@router.get("/my", response_model=ArtisanResponse)
def get_my_artisan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=404, detail="未找到匠人信息")
    return ArtisanResponse.model_validate(artisan)


@router.put("/my", response_model=ArtisanResponse)
def update_my_artisan(
    data: ArtisanUpdate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """匠人更新店铺信息（入驻成功后可编辑店铺名称、头像、公告、简介）"""
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=404, detail="未找到匠人信息")
    if artisan.status != "approved":
        raise HTTPException(status_code=403, detail="入驻审核通过后才能修改店铺信息")
    kwargs = {}
    if data.shop_name is not None:
        kwargs["shop_name"] = data.shop_name
    if data.shop_avatar is not None:
        kwargs["shop_avatar"] = data.shop_avatar
    if data.shop_notice is not None:
        kwargs["shop_notice"] = data.shop_notice
    if data.bio is not None:
        kwargs["bio"] = data.bio
    return ArtisanResponse.model_validate(update_artisan(db, artisan, **kwargs))


# ==================== 匠人关注 ====================

@router.post("/{artisan_id}/follow")
def follow_artisan(
    artisan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return toggle_artisan_follow(db, current_user.id, artisan_id)


# ==================== 定制服务 ====================

@router.post("/custom", response_model=CustomOrderResponse)
def create_custom(
    data: CustomOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = create_custom_order(db, current_user.id, data)
    return order


@router.get("/custom", response_model=dict)
def get_custom_list(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_or_none),
):
    if current_user and current_user.role == "artisan":
        artisan = get_artisan_by_user_id(db, current_user.id)
        items, total = get_custom_orders(db, artisan_id=artisan.id, skip=skip, limit=limit)
    elif current_user:
        items, total = get_custom_orders(db, user_id=current_user.id, skip=skip, limit=limit)
    else:
        items, total = get_custom_orders(db, skip=skip, limit=limit)
    return {"total": total, "items": [CustomOrderResponse.model_validate(o) for o in items]}


@router.get("/custom/{order_id}", response_model=CustomOrderResponse)
def get_custom(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="定制订单不存在")
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/quote", response_model=CustomOrderResponse)
def quote_custom(
    order_id: int,
    data: CustomQuote,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    from crud.services import get_custom_order_by_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    order = get_custom_order_by_id(db, order_id)
    if not order or order.artisan_id != artisan.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="当前状态不可报价")
    return CustomOrderResponse.model_validate(quote_custom_order(db, order_id, artisan.id, data))


@router.post("/custom/{order_id}/accept", response_model=CustomOrderResponse)
def accept_custom(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from crud.services import get_custom_order_by_id
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if order.status != "quoted":
        raise HTTPException(status_code=400, detail="当前状态不可接受")
    return CustomOrderResponse.model_validate(accept_custom_order(db, order_id, current_user.id))


@router.post("/custom/{order_id}/reject", response_model=CustomOrderResponse)
def reject_custom(
    order_id: int,
    reason: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from crud.services import get_custom_order_by_id
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 用户拒绝报价（用户端）：仅已报价状态可拒绝
    if order.user_id == current_user.id:
        if order.status != "quoted":
            raise HTTPException(status_code=400, detail="当前状态不可拒绝")
        order.rejected_by = "user"
    # 匠人拒绝需求（匠人端）：仅待处理状态可拒绝
    elif current_user.role == "artisan":
        artisan = get_artisan_by_user_id(db, current_user.id)
        if not artisan or order.artisan_id != artisan.id:
            raise HTTPException(status_code=404, detail="订单不存在")
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="当前状态不可拒绝")
        order.rejected_by = "artisan"
    else:
        raise HTTPException(status_code=403, detail="无权操作")

    order.status = "rejected"
    order.reject_reason = reason
    db.commit()
    db.refresh(order)
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/cancel", response_model=CustomOrderResponse)
def cancel_custom(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户取消已接受的定制订单（超时后用户主动取消）"""
    from crud.services import get_custom_order_by_id
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if order.status != "accepted" or order.pay_status == "paid":
        raise HTTPException(status_code=400, detail="当前状态不可取消")
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/ship", response_model=CustomOrderResponse)
def ship_custom(
    order_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    artisan = get_artisan_by_user_id(db, current_user.id)
    order = get_custom_order_by_id(db, order_id)
    if not order or order.artisan_id != artisan.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_status != "paid":
        raise HTTPException(status_code=400, detail="用户尚未付款，无法发货")
    order.status = "shipped"
    db.commit()
    db.refresh(order)
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/complete", response_model=CustomOrderResponse)
def complete_custom(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_custom_order_by_id(db, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "shipped":
        raise HTTPException(status_code=400, detail="订单状态不正确")
    order.status = "completed"
    db.commit()
    db.refresh(order)
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/address", response_model=CustomOrderResponse)
def update_custom_address(
    order_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_custom_order_by_id(db, order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    order.receiver_name = data.get("name", "")
    order.receiver_phone = data.get("phone", "")
    order.receiver_address = f"{data.get('province', '')}{data.get('city', '')}{data.get('district', '')}{data.get('detail', '')}"
    db.commit()
    db.refresh(order)
    return CustomOrderResponse.model_validate(order)


@router.post("/custom/{order_id}/progress", response_model=CustomOrderResponse)
def update_progress(
    order_id: int,
    progress: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    artisan = get_artisan_by_user_id(db, current_user.id)
    return CustomOrderResponse.model_validate(update_custom_progress(db, order_id, artisan.id, progress))


@router.post("/custom/{order_id}/messages", response_model=CustomMessageResponse)
def send_message(
    order_id: int,
    data: CustomMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CustomMessageResponse.model_validate(create_custom_message(db, current_user.id, data))


@router.get("/custom/{order_id}/messages", response_model=list[CustomMessageResponse])
def get_messages(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [CustomMessageResponse.model_validate(m) for m in get_custom_messages(db, order_id)]


# ==================== 财务管理 ====================

@router.get("/transactions", response_model=dict)
def get_my_transactions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    artisan = get_artisan_by_user_id(db, current_user.id)
    items, total = get_transactions(db, artisan_id=artisan.id, skip=skip, limit=limit)
    return {
        "total": total,
        "items": [TransactionResponse.model_validate(t) for t in items],
    }


# ==================== 管理员审核 (放在 {artisan_id} 之前) ====================

@router.get("/admin/applications", response_model=dict)
def get_applications(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_all_artisans(db, skip=skip, limit=limit, status=status, keyword=keyword)
    return {"total": total, "items": [ArtisanResponse.model_validate(a) for a in items]}


@router.post("/admin/{artisan_id}/approve")
def approve_app(
    artisan_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    approve_artisan(db, artisan_id)
    return {"message": "审核通过"}


@router.post("/admin/{artisan_id}/reject")
def reject_app(
    artisan_id: int,
    reason: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    reject_artisan(db, artisan_id, reason)
    return {"message": "已拒绝"}



# ==================== 匠人仪表盘 ====================

@router.get("/dashboard")
def artisan_dashboard(
    period: str = "7d",
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    """匠人中心仪表盘数据"""
    from models import Artisan, Product, Order, OrderItem, Course, CustomOrder
    from sqlalchemy import func
    from datetime import timedelta, date

    artisan = db.query(Artisan).filter(Artisan.user_id == current_user.id).first()
    if not artisan:
        raise HTTPException(status_code=404, detail="匠人信息不存在")

    # 时间范围
    today = date.today()
    if period == "today":
        start_date = today
        trend_days = 1
    elif period == "30d":
        start_date = today - timedelta(days=29)
        trend_days = 30
    else:  # 7d
        start_date = today - timedelta(days=6)
        trend_days = 7

    # 在售商品数
    products_count = db.query(func.count(Product.id)).filter(
        Product.artisan_id == artisan.id,
        Product.status == "approved",
    ).scalar() or 0

    # 有效订单状态
    valid_statuses = ["paid", "shipped", "completed"]

    # ---- 商品订单查询（Order → OrderItem → Product）----
    def product_order_query_distinct():
        return db.query(Order).join(OrderItem).join(Product).filter(
            Product.artisan_id == artisan.id,
            Order.status.in_(valid_statuses),
        ).distinct()

    # ---- 课程订单查询（Order → OrderItem → Course）----
    def course_order_query_distinct():
        return db.query(Order).join(OrderItem).join(Course, OrderItem.course_id == Course.id).filter(
            Course.artisan_id == artisan.id,
            Order.status.in_(valid_statuses),
        ).distinct()

    # ---- 定制订单查询 ----
    def custom_order_base():
        return db.query(CustomOrder).filter(
            CustomOrder.artisan_id == artisan.id,
            CustomOrder.pay_status == "paid",
        )

    # 今日订单
    today_orders_product = product_order_query_distinct().filter(
        func.date(Order.pay_time) == today,
    ).count()
    today_orders_course = course_order_query_distinct().filter(
        func.date(Order.pay_time) == today,
    ).count()
    today_orders_custom = custom_order_base().filter(
        func.date(CustomOrder.updated_at) == today,
    ).count()

    # 今日营收
    today_revenue_product = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Product).filter(
        Product.artisan_id == artisan.id,
        Order.status.in_(valid_statuses),
        func.date(Order.pay_time) == today,
    ).scalar() or 0
    today_revenue_course = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Course, OrderItem.course_id == Course.id).filter(
        Course.artisan_id == artisan.id,
        Order.status.in_(valid_statuses),
        func.date(Order.pay_time) == today,
    ).scalar() or 0
    today_revenue_custom = db.query(func.sum(CustomOrder.quote_amount)).filter(
        CustomOrder.artisan_id == artisan.id,
        CustomOrder.pay_status == "paid",
        func.date(CustomOrder.updated_at) == today,
    ).scalar() or 0

    # 待处理订单（待发货的商品订单 + 定制订单）
    pending_orders = db.query(func.count(Order.id)).join(OrderItem).join(Product).filter(
        Product.artisan_id == artisan.id,
        Order.status == "paid",
    ).scalar() or 0
    pending_orders += custom_order_base().filter(
        CustomOrder.status.in_(["accepted", "in_progress"]),
    ).count()

    # 累计总营收
    total_revenue_product = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Product).filter(
        Product.artisan_id == artisan.id,
        Order.status.in_(valid_statuses),
    ).scalar() or 0
    total_revenue_course = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Course, OrderItem.course_id == Course.id).filter(
        Course.artisan_id == artisan.id,
        Order.status.in_(valid_statuses),
    ).scalar() or 0
    total_revenue_custom = db.query(func.sum(CustomOrder.quote_amount)).filter(
        CustomOrder.artisan_id == artisan.id,
        CustomOrder.pay_status == "paid",
    ).scalar() or 0

    # 趋势数据
    revenue_trend = []
    order_trend = []
    for i in range(trend_days):
        d = start_date + timedelta(days=i)
        day_str = d.strftime("%m-%d")

        rp = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Product).filter(
            Product.artisan_id == artisan.id,
            Order.status.in_(valid_statuses),
            func.date(Order.pay_time) == d,
        ).scalar() or 0
        rc = db.query(func.sum(Order.pay_amount)).join(OrderItem).join(Course, OrderItem.course_id == Course.id).filter(
            Course.artisan_id == artisan.id,
            Order.status.in_(valid_statuses),
            func.date(Order.pay_time) == d,
        ).scalar() or 0
        rcu = db.query(func.sum(CustomOrder.quote_amount)).filter(
            CustomOrder.artisan_id == artisan.id,
            CustomOrder.pay_status == "paid",
            func.date(CustomOrder.updated_at) == d,
        ).scalar() or 0
        revenue_trend.append({"date": day_str, "product": float(rp), "course": float(rc), "custom": float(rcu)})

        op = product_order_query_distinct().filter(func.date(Order.pay_time) == d).count()
        oc = course_order_query_distinct().filter(func.date(Order.pay_time) == d).count()
        ocu = custom_order_base().filter(func.date(CustomOrder.updated_at) == d).count()
        order_trend.append({"date": day_str, "product": op, "course": oc, "custom": ocu})

    return {
        "products": products_count,
        "today_orders": today_orders_product + today_orders_course + today_orders_custom,
        "today_orders_product": today_orders_product,
        "today_orders_course": today_orders_course,
        "today_orders_custom": today_orders_custom,
        "today_revenue": float(today_revenue_product) + float(today_revenue_course) + float(today_revenue_custom),
        "today_revenue_product": float(today_revenue_product),
        "today_revenue_course": float(today_revenue_course),
        "today_revenue_custom": float(today_revenue_custom),
        "pending_orders": pending_orders,
        "total_revenue": float(total_revenue_product) + float(total_revenue_course) + float(total_revenue_custom),
        "total_revenue_product": float(total_revenue_product),
        "total_revenue_course": float(total_revenue_course),
        "total_revenue_custom": float(total_revenue_custom),
        "revenue_trend": revenue_trend,
        "order_trend": order_trend,
    }


# ==================== 匠人详情 (放在最后，避免与具体路径冲突) ====================

@router.get("/{artisan_id}", response_model=ArtisanResponse)
def get_artisan(artisan_id: int, db: Session = Depends(get_db)):
    from crud.users import get_artisan_by_id
    artisan = get_artisan_by_id(db, artisan_id)
    if not artisan:
        raise HTTPException(status_code=404, detail="匠人不存在")
    return ArtisanResponse.model_validate(artisan)
