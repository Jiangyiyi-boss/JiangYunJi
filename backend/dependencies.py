from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth_token import decode_access_token
from config import settings


def get_token_from_request(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误")
    return auth_header.replace("Bearer ", "")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = get_token_from_request(request)
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的 Token")
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token 已过期")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.status:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return role_checker


def get_current_user_or_none(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        token = get_token_from_request(request)
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None
    except (JWTError, HTTPException, ValueError, TypeError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.status:
        return None
    return user
