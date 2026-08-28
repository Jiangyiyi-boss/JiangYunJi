from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserResponse, UserListResponse, UserListResult, UserStatusUpdate
from dependencies import get_current_user, require_role
from models import User
from crud.users import get_all_users, toggle_user_status

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(
    nickname: str = None,
    avatar: str = None,
    phone: str = None,
    bio: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if nickname is not None:
        current_user.nickname = nickname
    if avatar is not None:
        current_user.avatar = avatar
    if phone is not None:
        current_user.phone = phone
    if bio is not None:
        current_user.bio = bio
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


# ==================== 管理员用户管理 ====================

@router.get("/admin/list", response_model=UserListResult)
def admin_list_users(
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[bool] = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    from crud.users import get_all_users
    items, total = get_all_users(db, skip=skip, limit=limit, keyword=keyword)
    
    # 额外筛选
    if role:
        items = [u for u in items if u.role == role]
        total = len(items)
    if status is not None:
        items = [u for u in items if u.status == status]
        total = len(items)
    
    return UserListResult(
        total=total,
        items=[UserListResponse.model_validate(u) for u in items],
    )


@router.put("/admin/{user_id}/status")
def admin_toggle_user_status(
    user_id: int,
    data: UserStatusUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="不能修改管理员状态")
    user.status = data.status
    db.commit()
    return {"message": "操作成功", "status": user.status}
