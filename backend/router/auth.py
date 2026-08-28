from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    UserCreate, UserLogin, AdminLogin, TokenResponse, UserResponse,
    SendSmsRequest, SmsLoginRequest, ResetPasswordRequest, RegisterBySmsRequest,
)
from crud.users import get_user_by_username, get_user_by_phone, create_user
from auth_utils import verify_password, hash_password, validate_password
from auth_token import create_access_token
from config import settings
from sms_service import send_sms_code, verify_sms_code
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 密码错误次数记录 {user_id: count}
_login_fails = {}
MAX_LOGIN_FAILS = 5


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """手机号 + 验证码注册"""
    # 校验验证码
    if not verify_sms_code(data.phone, data.code, purpose="register"):
        logger.warning("注册失败: 验证码错误 phone=%s", data.phone[-4:])
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 校验手机号是否已注册
    if get_user_by_phone(db, data.phone):
        logger.warning("注册失败: 手机号已注册 phone=%s", data.phone[-4:])
        raise HTTPException(status_code=400, detail="该手机号已注册")

    # 校验密码强度
    valid, msg = validate_password(data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # 自动生成用户名
    username = f"u{data.phone[-8:]}"
    nickname = data.nickname or f"用户{data.phone[-4:]}"

    from crud.users import get_user_by_username
    base_username = username
    counter = 1
    while get_user_by_username(db, username):
        username = f"{base_username}{counter}"
        counter += 1

    user = create_user(db, UserCreate(
        phone=data.phone,
        password=data.password,
        code=data.code,
        nickname=nickname,
    ))
    # 覆盖自动生成的用户名
    user.username = username
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role})
    logger.info("用户注册成功 user_id=%s phone=***%s", user.id, data.phone[-4:])
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """手机号或账号 + 密码登录"""
    # 先尝试按手机号查找，再尝试按账号查找
    user = get_user_by_phone(db, data.phone)
    if not user:
        user = get_user_by_username(db, data.phone)
    if not user:
        logger.warning("登录失败: 账号不存在 account=%s", data.phone)
        raise HTTPException(status_code=401, detail="手机号或账号未注册")

    # 检查账户锁定
    if not user.status:
        logger.warning("登录失败: 账号已被禁用 user_id=%s", user.id)
        raise HTTPException(status_code=403, detail="账号已被禁用")

    fails = _login_fails.get(user.id, 0)
    if fails >= MAX_LOGIN_FAILS:
        logger.warning("登录失败: 密码错误次数过多 user_id=%s", user.id)
        raise HTTPException(status_code=403, detail="密码错误次数过多，账号已锁定，请联系客服")

    if not verify_password(data.password, user.password):
        _login_fails[user.id] = fails + 1
        remaining = MAX_LOGIN_FAILS - _login_fails[user.id]
        logger.warning("登录失败: 密码错误 user_id=%s remaining=%s", user.id, remaining)
        raise HTTPException(status_code=401, detail=f"密码错误，还剩{remaining}次机会")

    # 登录成功，清除失败计数
    _login_fails.pop(user.id, None)

    expires_delta = timedelta(days=7) if data.remember else None  # 记住登录：7天
    token = create_access_token({"sub": user.id, "role": user.role}, expires_delta)
    logger.info("用户登录成功 user_id=%s role=%s", user.id, user.role)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    if data.admin_secret != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="管理员密钥错误")

    user = get_user_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="非管理员账号")

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/send-sms")
def send_sms(data: SendSmsRequest):
    """发送短信验证码，purpose 区分不同场景（login/register/reset）"""
    purpose = data.purpose or "login"
    result = send_sms_code(data.phone, purpose=purpose)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "发送失败"))
    return result


@router.post("/login-by-sms")
def login_by_sms(data: SmsLoginRequest, db: Session = Depends(get_db)):
    """手机号 + 验证码登录，未注册时返回 need_register 让前端引导用户设置密码"""
    user = get_user_by_phone(db, data.phone)
    # 已注册用户：验证码一次性消耗
    # 未注册用户：只校验不消耗，保留给 register-by-sms 使用
    consume = user is not None
    if not verify_sms_code(data.phone, data.code, purpose="login", consume=consume):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    if not user:
        # 手机号未注册，返回 need_register 标记，前端弹出设置密码对话框
        return {"need_register": True, "phone": data.phone}

    if not user.status:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    _login_fails.pop(user.id, None)
    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register-by-sms", response_model=TokenResponse)
def register_by_sms(data: RegisterBySmsRequest, db: Session = Depends(get_db)):
    """短信验证码注册：用户设置密码后完成注册并登录"""
    if not verify_sms_code(data.phone, data.code, purpose="login"):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    if get_user_by_phone(db, data.phone):
        raise HTTPException(status_code=400, detail="该手机号已注册")

    valid, msg = validate_password(data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    username = f"u{data.phone[-8:]}"
    nickname = f"用户{data.phone[-4:]}"

    from crud.users import get_user_by_username
    base_username = username
    counter = 1
    while get_user_by_username(db, username):
        username = f"{base_username}{counter}"
        counter += 1

    user = create_user(db, UserCreate(
        phone=data.phone,
        password=data.password,
        code=data.code,
        nickname=nickname,
    ))
    user.username = username
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role})
    logger.info("短信注册成功 user_id=%s phone=***%s", user.id, data.phone[-4:])
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """通过短信验证码重置密码"""
    if not verify_sms_code(data.phone, data.code, purpose="reset"):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    valid, msg = validate_password(data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    user = get_user_by_phone(db, data.phone)
    if not user:
        raise HTTPException(status_code=404, detail="该手机号未注册")

    user.password = hash_password(data.password)
    _login_fails.pop(user.id, None)
    db.commit()
    return {"message": "密码重置成功"}
