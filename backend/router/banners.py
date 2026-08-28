from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import BannerCreate, BannerUpdate, BannerResponse
from crud.banners import (
    get_banners, get_enabled_banners, get_banner_by_id,
    create_banner, update_banner, delete_banner,
)
from dependencies import require_role
from models import User

router = APIRouter(prefix="/api/banners", tags=["轮播图"])


# 公开接口 - 首页获取启用的轮播图
@router.get("", response_model=list[BannerResponse])
def list_banners(db: Session = Depends(get_db)):
    return get_enabled_banners(db)


# 管理员接口
@router.get("/admin", response_model=dict)
def admin_list_banners(
    skip: int = 0,
    limit: int = 50,
    source_type: str = None,
    enabled: bool = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items, total = get_banners(db, skip=skip, limit=limit, source_type=source_type, enabled=enabled)
    return {"total": total, "items": [BannerResponse.model_validate(i) for i in items]}


@router.post("/admin", response_model=BannerResponse)
def admin_create_banner(
    data: BannerCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return BannerResponse.model_validate(create_banner(db, data.model_dump()))


@router.put("/admin/{banner_id}", response_model=BannerResponse)
def admin_update_banner(
    banner_id: int,
    data: BannerUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    banner = get_banner_by_id(db, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    update_data = data.model_dump(exclude_unset=True)
    return BannerResponse.model_validate(update_banner(db, banner, update_data))


@router.delete("/admin/{banner_id}")
def admin_delete_banner(
    banner_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if not delete_banner(db, banner_id):
        raise HTTPException(status_code=404, detail="轮播图不存在")
    return {"message": "删除成功"}
