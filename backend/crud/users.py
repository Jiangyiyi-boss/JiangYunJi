from sqlalchemy.orm import Session
from models import User, Artisan
from schemas import UserCreate, ArtisanApply
from auth_utils import hash_password


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    username = getattr(user_data, 'username', None) or f"u{user_data.phone[-8:]}"
    user = User(
        username=username,
        password=hash_password(user_data.password),
        phone=user_data.phone,
        nickname=user_data.nickname or f"用户{user_data.phone[-4:]}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin(db: Session, username: str, password: str, phone: str = None) -> User:
    user = User(
        username=username,
        password=hash_password(password),
        phone=phone,
        nickname="管理员",
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 20, keyword: str = None):
    query = db.query(User)
    if keyword:
        query = query.filter(
            User.username.contains(keyword) | User.nickname.contains(keyword)
        )
    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all(), query.count()


def toggle_user_status(db: Session, user_id: int) -> User:
    user = get_user_by_id(db, user_id)
    if user:
        user.status = not user.status
        db.commit()
        db.refresh(user)
    return user


# ==================== 匠人相关 ====================

def get_artisan_by_user_id(db: Session, user_id: int):
    return db.query(Artisan).filter(Artisan.user_id == user_id).first()


def get_artisan_by_id(db: Session, artisan_id: int):
    return db.query(Artisan).filter(Artisan.id == artisan_id).first()


def create_artisan_application(db: Session, user_id: int, apply_data: ArtisanApply) -> Artisan:
    user = get_user_by_id(db, user_id)
    artisan = Artisan(
        user_id=user_id,
        real_name=apply_data.real_name,
        id_card=apply_data.id_card,
        specialty=apply_data.specialty,
        bio=apply_data.bio,
        certifications=apply_data.certifications,
        contact=apply_data.contact,
        shop_name=apply_data.shop_name,
        shop_avatar=apply_data.shop_avatar or (user.avatar if user else ""),
        status="pending",
    )
    db.add(artisan)
    db.commit()
    db.refresh(artisan)
    return artisan


def get_all_artisans(db: Session, skip: int = 0, limit: int = 20, status: str = None, keyword: str = None):
    query = db.query(Artisan)
    if status:
        query = query.filter(Artisan.status == status)
    if keyword:
        query = query.filter(
            Artisan.real_name.contains(keyword) | Artisan.specialty.contains(keyword)
        )
    total = query.count()
    items = query.order_by(Artisan.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def approve_artisan(db: Session, artisan_id: int) -> Artisan:
    artisan = get_artisan_by_id(db, artisan_id)
    if artisan:
        artisan.status = "approved"
        artisan.user.role = "artisan"
        db.commit()
        db.refresh(artisan)
    return artisan


def reject_artisan(db: Session, artisan_id: int, reason: str) -> Artisan:
    artisan = get_artisan_by_id(db, artisan_id)
    if artisan:
        artisan.status = "rejected"
        artisan.reject_reason = reason
        db.commit()
        db.refresh(artisan)
    return artisan


def update_artisan(db: Session, artisan: Artisan, **kwargs) -> Artisan:
    for key, value in kwargs.items():
        if hasattr(artisan, key):
            setattr(artisan, key, value)
    db.commit()
    db.refresh(artisan)
    return artisan
