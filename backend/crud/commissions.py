from sqlalchemy.orm import Session
from models import CommissionRate, CommissionAppeal, Category
from schemas import CommissionRateCreate, CommissionRateUpdate
from decimal import Decimal


def get_default_commission_rate(db: Session) -> Decimal:
    """获取默认佣金比例"""
    default = db.query(CommissionRate).filter(CommissionRate.category_id.is_(None)).first()
    if default:
        return Decimal(str(default.rate))
    return Decimal('0.1000')  # 默认10%


def get_commission_rate_for_category(db: Session, category_id: int) -> Decimal:
    """获取指定分类的佣金比例"""
    rate = db.query(CommissionRate).filter(
        CommissionRate.category_id == category_id
    ).first()
    if rate:
        return Decimal(str(rate.rate))
    return get_default_commission_rate(db)


def get_all_commission_rates(db: Session, skip: int = 0, limit: int = 50):
    """获取所有佣金配置"""
    query = db.query(CommissionRate).order_by(
        CommissionRate.category_id.is_(None).desc(),
        CommissionRate.id
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_commission_rate(db: Session, data: CommissionRateCreate) -> CommissionRate:
    """创建佣金配置"""
    rate = CommissionRate(
        category_id=data.category_id,
        rate=data.rate,
        remark=data.remark,
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_commission_rate(db: Session, rate_id: int, data: CommissionRateUpdate) -> CommissionRate:
    """更新佣金配置"""
    rate = db.query(CommissionRate).filter(CommissionRate.id == rate_id).first()
    if not rate:
        return None
    if data.rate is not None:
        rate.rate = data.rate
    if data.remark is not None:
        rate.remark = data.remark
    db.commit()
    db.refresh(rate)
    return rate


def delete_commission_rate(db: Session, rate_id: int) -> bool:
    """删除佣金配置"""
    rate = db.query(CommissionRate).filter(CommissionRate.id == rate_id).first()
    if rate:
        db.delete(rate)
        db.commit()
        return True
    return False


# ==================== 佣金申诉 ====================

def create_commission_appeal(db: Session, artisan_id: int, product_id: int = None, order_id: int = None, reason: str = "") -> CommissionAppeal:
    """创建佣金申诉"""
    appeal = CommissionAppeal(
        artisan_id=artisan_id,
        product_id=product_id,
        order_id=order_id,
        reason=reason,
        status="pending",
    )
    db.add(appeal)
    db.commit()
    db.refresh(appeal)
    return appeal


def has_product_appeal(db: Session, artisan_id: int, product_id: int) -> bool:
    """检查匠人是否已对某商品提交过申诉"""
    return db.query(CommissionAppeal).filter(
        CommissionAppeal.artisan_id == artisan_id,
        CommissionAppeal.product_id == product_id,
    ).first() is not None


def get_artisan_appeals(db: Session, artisan_id: int, skip: int = 0, limit: int = 20):
    """获取匠人的申诉列表"""
    query = db.query(CommissionAppeal).filter(CommissionAppeal.artisan_id == artisan_id)
    total = query.count()
    items = query.order_by(CommissionAppeal.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_all_appeals(db: Session, skip: int = 0, limit: int = 20, status: str = None):
    """管理员获取所有申诉"""
    query = db.query(CommissionAppeal)
    if status:
        query = query.filter(CommissionAppeal.status == status)
    total = query.count()
    items = query.order_by(CommissionAppeal.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def process_appeal(db: Session, appeal_id: int, status: str, admin_note: str = "") -> CommissionAppeal:
    """处理申诉"""
    appeal = db.query(CommissionAppeal).filter(CommissionAppeal.id == appeal_id).first()
    if not appeal:
        return None
    appeal.status = status
    appeal.admin_note = admin_note
    from datetime import datetime
    appeal.processed_at = datetime.now()
    db.commit()
    db.refresh(appeal)
    return appeal
