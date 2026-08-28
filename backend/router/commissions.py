from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    CommissionRateCreate, CommissionRateUpdate, CommissionRateResponse,
    CommissionAppealCreate, CommissionAppealResponse, AppealProcess,
)
from crud.commissions import (
    get_all_commission_rates, create_commission_rate, update_commission_rate, delete_commission_rate,
    create_commission_appeal, get_all_appeals, process_appeal,
    get_commission_rate_for_category,
)
from crud.users import get_artisan_by_user_id
from dependencies import get_current_user, require_role
from models import User, Category, Order, Artisan

router = APIRouter(prefix="/api/commissions", tags=["佣金管理"])


# ==================== 佣金比例管理 ====================

@router.get("/rates", response_model=dict)
def get_commission_rates(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_all_commission_rates(db, skip=skip, limit=limit)
    result = []
    for item in items:
        data = CommissionRateResponse.model_validate(item)
        if item.category_id:
            cat = db.query(Category).filter(Category.id == item.category_id).first()
            data.category_name = cat.name if cat else None
        else:
            data.category_name = "默认"
        result.append(data)
    return {"total": total, "items": result}


@router.post("/rates", response_model=CommissionRateResponse)
def create_rate(
    data: CommissionRateCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if data.category_id:
        cat = db.query(Category).filter(Category.id == data.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="分类不存在")
    return CommissionRateResponse.model_validate(create_commission_rate(db, data))


@router.put("/rates/{rate_id}", response_model=CommissionRateResponse)
def update_rate(
    rate_id: int,
    data: CommissionRateUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rate = update_commission_rate(db, rate_id, data)
    if not rate:
        raise HTTPException(status_code=404, detail="佣金配置不存在")
    result = CommissionRateResponse.model_validate(rate)
    if rate.category_id:
        cat = db.query(Category).filter(Category.id == rate.category_id).first()
        result.category_name = cat.name if cat else None
    else:
        result.category_name = "默认"
    return result


@router.delete("/rates/{rate_id}")
def delete_rate(
    rate_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if not delete_commission_rate(db, rate_id):
        raise HTTPException(status_code=404, detail="佣金配置不存在")
    return {"message": "删除成功"}


@router.get("/rate/{category_id}")
def get_category_commission_rate(
    category_id: int,
    db: Session = Depends(get_db),
):
    """查询指定分类的佣金比例（无需登录，供商家发布商品时参考）"""
    rate = get_commission_rate_for_category(db, category_id)
    return {
        "category_id": category_id,
        "commission_rate": float(rate),
        "commission_rate_display": f"{float(rate) * 100:.1f}%",
    }


# ==================== 佣金申诉（匠人端） ====================

@router.post("/appeals", response_model=CommissionAppealResponse)
def create_appeal(
    data: CommissionAppealCreate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    from crud.commissions import has_product_appeal
    from models import Product

    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=404, detail="匠人信息不存在")

    # 商品申诉
    if data.product_id:
        product = db.query(Product).filter(Product.id == data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        if product.artisan_id != artisan.id:
            raise HTTPException(status_code=403, detail="无权申诉该商品")
        if has_product_appeal(db, artisan.id, data.product_id):
            raise HTTPException(status_code=400, detail="该商品已提交过申诉，请等待处理")
        if product.commission_status == "appeal_rejected":
            raise HTTPException(status_code=400, detail="该商品佣金申诉已被驳回，不可再次申诉")
        appeal = create_commission_appeal(db, artisan.id, product_id=data.product_id, reason=data.reason)
        # 设置商品佣金状态为申诉中
        product.commission_status = "appealing"
        db.commit()
        result = CommissionAppealResponse.model_validate(appeal)
        result.artisan_name = artisan.shop_name or artisan.real_name
        result.product_name = product.name
        result.product_price = float(product.price)
        return result

    # 订单申诉（兼容旧逻辑）
    if data.order_id:
        order = db.query(Order).filter(Order.id == data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        from models import OrderItem
        has_item = db.query(OrderItem).join(
            OrderItem, OrderItem.order_id == order.id
        ).filter(OrderItem.product_id.in_(
            db.query(Product.id).filter(Product.artisan_id == artisan.id)
        )).first()
        if not has_item:
            raise HTTPException(status_code=403, detail="无权申诉该订单")
        appeal = create_commission_appeal(db, artisan.id, order_id=data.order_id, reason=data.reason)
        result = CommissionAppealResponse.model_validate(appeal)
        result.artisan_name = artisan.shop_name or artisan.real_name
        result.order_no = order.order_no
        result.order_amount = float(order.total_amount)
        return result

    raise HTTPException(status_code=400, detail="请提供商品ID或订单ID")


# ==================== 佣金申诉（管理员端） ====================

@router.get("/admin/appeals", response_model=dict)
def get_all_appeals_admin(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_all_appeals(db, skip=skip, limit=limit, status=status)
    result = []
    for item in items:
        data = CommissionAppealResponse.model_validate(item)
        artisan = db.query(Artisan).filter(Artisan.id == item.artisan_id).first()
        data.artisan_name = artisan.shop_name or artisan.real_name if artisan else ""
        # 商品申诉：附上商品信息
        if item.product_id:
            from models import Product
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                data.product_name = product.name
                data.product_price = float(product.price)
        # 订单申诉：附上订单信息
        if item.order_id:
            order = db.query(Order).filter(Order.id == item.order_id).first()
            if order:
                data.order_no = order.order_no
                data.order_amount = float(order.total_amount)
        result.append(data)
    return {"total": total, "items": result}


@router.post("/admin/appeals/{appeal_id}/process")
def process_appeal_admin(
    appeal_id: int,
    data: AppealProcess,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    from models import Product
    from decimal import Decimal

    appeal = process_appeal(db, appeal_id, data.status, data.admin_note)
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉不存在")

    # 更新对应商品的佣金状态
    if appeal.product_id:
        product = db.query(Product).filter(Product.id == appeal.product_id).first()
        if product:
            if data.status == "approved":
                # 通过申诉：可调整佣金比例，交回商家确认
                if data.commission_rate is not None:
                    product.commission_rate = Decimal(str(data.commission_rate))
                product.commission_status = "pending"
            else:
                # 驳回申诉：不可再申诉
                product.commission_status = "appeal_rejected"
            db.commit()

    return {"message": "处理成功"}
