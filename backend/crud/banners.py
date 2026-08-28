from sqlalchemy.orm import Session
from models import Banner, Product
from datetime import datetime


def get_banners(db: Session, skip: int = 0, limit: int = 50, source_type: str = None, enabled: bool = None):
    query = db.query(Banner)
    if source_type:
        query = query.filter(Banner.source_type == source_type)
    if enabled is not None:
        query = query.filter(Banner.enabled == enabled)
    total = query.count()
    items = query.order_by(Banner.sort, Banner.id).offset(skip).limit(limit).all()
    return items, total


def get_enabled_banners(db: Session):
    """获取启用的轮播图，自动过滤关联已下架商品的轮播图"""
    now = datetime.now()
    # 先获取所有符合条件的轮播图
    banners = db.query(Banner).filter(
        Banner.enabled == True,
        (Banner.start_date == None) | (Banner.start_date <= now),
        (Banner.end_date == None) | (Banner.end_date >= now),
    ).order_by(Banner.sort, Banner.id).all()
    
    # 过滤掉关联商品已下架的轮播图
    result = []
    for banner in banners:
        if banner.product_id:
            # 检查关联商品是否下架
            product = db.query(Product).filter(Product.id == banner.product_id).first()
            if not product or product.status == 'offline':
                # 自动禁用该轮播图
                banner.enabled = False
                db.commit()
                continue
        result.append(banner)
    
    return result


def get_banner_by_id(db: Session, banner_id: int):
    return db.query(Banner).filter(Banner.id == banner_id).first()


def create_banner(db: Session, data: dict) -> Banner:
    banner = Banner(**data)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(db: Session, banner: Banner, data: dict) -> Banner:
    for key, value in data.items():
        if hasattr(banner, key):
            setattr(banner, key, value)
    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, banner_id: int) -> bool:
    banner = get_banner_by_id(db, banner_id)
    if banner:
        db.delete(banner)
        db.commit()
        return True
    return False


def disable_banners_by_product(db: Session, product_id: int):
    """商品下架时，自动禁用关联该商品的轮播图"""
    banners = db.query(Banner).filter(
        Banner.product_id == product_id,
        Banner.enabled == True
    ).all()
    
    for banner in banners:
        banner.enabled = False
    
    if banners:
        db.commit()
    
    return len(banners)
