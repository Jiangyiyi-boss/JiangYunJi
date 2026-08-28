from pydantic import BaseModel, EmailStr, field_validator, field_serializer
from typing import Optional, List
from datetime import datetime, date, timezone
from enum import Enum


# ==================== 用户相关 ====================

class UserRole(str, Enum):
    USER = "user"
    ARTISAN = "artisan"
    ADMIN = "admin"


class UserCreate(BaseModel):
    phone: str
    password: str
    code: str  # 短信验证码
    nickname: Optional[str] = ""


class UserLogin(BaseModel):
    phone: str  # 手机号或账号
    password: str
    remember: Optional[bool] = False


class SendSmsRequest(BaseModel):
    phone: str
    purpose: Optional[str] = "login"


class SmsLoginRequest(BaseModel):
    phone: str
    code: str


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    password: str


class RegisterBySmsRequest(BaseModel):
    """短信验证码注册：用户设置密码后完成注册并登录"""
    phone: str
    code: str
    password: str




class AdminLogin(BaseModel):
    username: str
    password: str
    admin_secret: str


class UserResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    nickname: str
    avatar: str
    bio: str = ""
    role: str
    status: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== 分类相关 ====================

class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    icon: str = ""
    sort: int = 0


class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    icon: str
    sort: Optional[int] = 0
    level: int
    children: Optional[List["CategoryResponse"]] = None

    class Config:
        from_attributes = True


# ==================== 商品相关 ====================

class ProductCreate(BaseModel):
    name: str
    description: str = ""
    price: Optional[float] = None  # 由 SKU specs 自动计算最低价
    original_price: Optional[float] = None  # deprecated
    stock: Optional[int] = None  # 由 SKU specs 自动计算总库存
    images: List[str] = []
    category_id: int
    limit_per_user: Optional[int] = None  # deprecated, 迁移至 SKU specs 内
    listing_mode: str = "auto"  # "auto"=审核通过自动上架 "manual"=审核通过手动上架
    shipping_type: str = "free"
    shipping_fee: float = 0
    ship_address: str = ""
    ship_time: str = "48h"
    specs: List[dict] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    stock: Optional[int] = None
    images: Optional[List[str]] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    limit_per_user: Optional[int] = None
    listing_mode: Optional[str] = None
    shipping_type: Optional[str] = None
    shipping_fee: Optional[float] = None
    ship_address: Optional[str] = None
    ship_time: Optional[str] = None
    specs: Optional[List[dict]] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    stock: int
    stock_display: str = ""  # 模糊库存展示，仅消费者端可见
    sales: int
    images: List[str] = []
    category_id: int
    category_name: str = ""
    artisan_id: int
    status: str
    listing_mode: str = "auto"
    commission_status: str = "pending"
    is_recommend: bool
    created_at: datetime
    limit_per_user: int = 0
    shipping_type: str = "free"
    shipping_fee: float = 0
    ship_address: str = ""
    ship_time: str = "48h"
    specs: Optional[List[dict]] = None
    commission_rate: float = 0.1
    reject_reason: str = ""

    @field_validator('specs', 'images', mode='before')
    @classmethod
    def normalize_lists(cls, v, info):
        if info.field_name == 'specs':
            return v or []
        return v or []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    total: int
    items: List[ProductResponse]


# ==================== 购物车 ====================

class CartItemCreate(BaseModel):
    product_id: int
    qty: int = 1
    spec_name: str = ""
    spec_price: Optional[float] = None
    spec_sku: str = ""


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    qty: int
    spec_name: str = ""
    spec_price: Optional[float] = None
    spec_sku: str = ""
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True


# ==================== 订单相关 ====================

class OrderCreate(BaseModel):
    items: List[dict]
    address_id: int
    remark: str = ""


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: Optional[int] = None
    course_id: Optional[int] = None
    product_name: str
    product_image: str
    price: float
    qty: int
    subtotal: float
    commission_rate: float = 0.1
    commission_amount: float = 0
    artisan_income: float = 0

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_no: str
    user_id: int
    total_amount: float
    pay_amount: float
    shipping_fee: float = 0
    commission_amount: float = 0
    goods_type: int = 1  # 1=实物 2=课程
    status: str
    pay_method: Optional[str] = None
    pay_time: Optional[datetime] = None
    ship_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    remark: str
    created_at: datetime
    payment_started_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    has_appeal: bool = False

    @field_serializer('payment_started_at')
    def serialize_payment_started_at(self, value):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat()

    class Config:
        from_attributes = True


# ==================== 课程报名管理 ====================

class CourseEnrollmentItem(BaseModel):
    id: int
    user_id: int
    user_nickname: str = ""
    user_avatar: str = ""
    type: str  # "free" or "purchased"
    status: str
    progress: int
    enrolled_at: str
    order_no: Optional[str] = None
    order_id: Optional[int] = None


# ==================== 地址 ====================

class AddressCreate(BaseModel):
    name: str
    phone: str
    province: str = ""
    city: str = ""
    district: str = ""
    detail: str = ""
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    user_id: int
    name: str = ""
    phone: str = ""
    province: str = ""
    city: str = ""
    district: str = ""
    detail: str = ""
    is_default: bool = False

    @field_validator('name', 'phone', 'province', 'city', 'district', 'detail', mode='before')
    @classmethod
    def normalize_empty(cls, v):
        return v if v is not None else ""

    @field_validator('is_default', mode='before')
    @classmethod
    def normalize_bool(cls, v):
        return v if v is not None else False

    class Config:
        from_attributes = True


# ==================== 匠人相关 ====================

class ArtisanApply(BaseModel):
    real_name: str
    id_card: str
    specialty: str
    bio: str
    certifications: str = ""
    contact: str
    shop_name: str
    shop_avatar: str = ""


class ArtisanResponse(BaseModel):
    id: int
    user_id: int
    real_name: str
    specialty: str
    bio: str
    shop_name: str
    shop_avatar: str
    shop_notice: str
    status: str
    fans_count: int
    total_sales: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArtisanUpdate(BaseModel):
    """匠人更新店铺信息（入驻成功后可编辑）"""
    shop_name: Optional[str] = None
    shop_avatar: Optional[str] = None
    shop_notice: Optional[str] = None
    bio: Optional[str] = None


class ArtisanFollowResponse(BaseModel):
    id: int
    artisan_id: int
    created_at: datetime

    class Config:
        from_attributes = True




# ==================== 论坛相关 ====================

class ForumPostCreate(BaseModel):
    title: Optional[str] = ""
    content: Optional[str] = ""
    images: List[str] = []
    video_url: Optional[str] = ""
    category: str = "share"
    linked_products: List = []
    is_draft: bool = False


class ForumPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    video_url: Optional[str] = None
    category: Optional[str] = None
    linked_products: Optional[List] = None
    status: Optional[str] = None


class ForumPostResponse(BaseModel):
    id: int
    user_id: int
    title: str = ""
    content: str = ""
    images: List[str] = []
    video_url: str = ""
    category: str
    like_count: int
    comment_count: int
    status: str
    linked_products: List = []
    created_at: datetime
    is_liked: bool = False
    is_favorited: bool = False
    is_followed: bool = False
    author_nickname: str = ""
    author_avatar: str = ""
    author_role: str = ""
    author_artisan_id: Optional[int] = None
    author_shop_name: str = ""

    @field_validator('images', 'linked_products', mode='before')
    @classmethod
    def normalize_lists(cls, v, info):
        return v or []

    class Config:
        from_attributes = True


class CourseCommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None
    lesson_id: Optional[int] = None


class CourseNoteCreate(BaseModel):
    title: str
    content: str


class CourseNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ForumCommentCreate(BaseModel):
    parent_id: Optional[str] = None
    content: str


class ForumCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_id: Optional[int] = None
    content: str
    like_count: int
    created_at: datetime
    author_nickname: str = ""
    author_avatar: str = ""

    class Config:
        from_attributes = True


class PostFavoriteResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserFollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
    follower_nickname: str = ""
    follower_avatar: str = ""

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    actor_id: Optional[int] = None
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    link: Optional[str] = None
    course_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    actor_nickname: str = ""
    actor_avatar: str = ""
    post_title: str = ""

    class Config:
        from_attributes = True


# ==================== 定制服务 ====================

class CustomOrderCreate(BaseModel):
    artisan_id: int
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    deadline: Optional[str] = None
    reference_images: List[str] = []


class CustomOrderResponse(BaseModel):
    id: int
    user_id: int
    artisan_id: int
    description: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    deadline: Optional[str] = None
    reference_images: List[str]
    order_no: Optional[str] = None
    status: str
    pay_status: str = "unpaid"
    payment_started_at: Optional[datetime] = None
    quote_amount: Optional[float] = None
    quote_deadline: Optional[int] = None
    deposit_amount: float
    final_amount: float
    progress: int
    reject_reason: str = ""
    rejected_by: Optional[str] = None
    created_at: datetime

    @field_validator("deadline", mode="before")
    @classmethod
    def coerce_deadline(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v.isoformat()
        return str(v)

    @field_serializer('payment_started_at')
    def serialize_payment_started_at(self, value):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat()

    class Config:
        from_attributes = True


class CustomMessageCreate(BaseModel):
    custom_order_id: int
    content: str
    images: List[str] = []


class CustomMessageResponse(BaseModel):
    id: int
    custom_order_id: int
    sender_id: int
    content: str
    images: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CustomQuote(BaseModel):
    quote_amount: float
    quote_deadline: int


# ==================== 财务管理 ====================

class TransactionResponse(BaseModel):
    id: int
    artisan_id: Optional[int] = None
    type: str
    amount: float
    order_id: Optional[int] = None
    status: str
    remark: str
    created_at: datetime

    class Config:
        from_attributes = True


# ArtisanWalletResponse 已移除 — 匠人收入统一通过仪表盘 total_revenue 展示


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    message: str
    data: Optional[dict] = None


# ==================== 在线教育 ====================

class CourseCreate(BaseModel):
    title: str
    description: str = ""
    cover_image: str = ""
    category: str = ""
    price: float = 0
    status: str = "draft"
    # 新增字段
    difficulty: str = ""
    duration_hours: float = 0  # deprecated, 保留兼容
    lesson_limit: int = 0  # 商家设定的总课时上限, 0=不限制
    target_audience: str = ""
    tags: List[str] = []
    free_preview_count: int = 0
    craft_intro: str = ""
    purchase_notice: str = ""
    material_type: str = "none"
    material_desc: str = ""
    material_price: float = 0
    material_shipping: str = "express"
    material_ship_address: str = ""
    material_ship_time: str = ""
    status: str = "draft"


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    # 新增字段
    difficulty: Optional[str] = None
    duration_hours: Optional[float] = None  # deprecated, 保留兼容
    lesson_limit: Optional[int] = None  # 商家设定的总课时上限, 0=不限制
    target_audience: Optional[str] = None
    tags: Optional[List[str]] = None
    free_preview_count: Optional[int] = None
    craft_intro: Optional[str] = None
    purchase_notice: Optional[str] = None
    material_type: Optional[str] = None
    material_desc: Optional[str] = None
    material_price: Optional[float] = None
    material_shipping: Optional[str] = None
    material_ship_address: Optional[str] = None
    material_ship_time: Optional[str] = None
    reject_reason: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    artisan_id: int
    artisan_user_id: int = 0  # the User.id of the course owner
    title: str
    description: str
    cover_image: str
    category: str
    price: float
    status: str
    created_at: datetime
    chapter_count: int = 0
    lesson_count: int = 0  # 实际课时数(计算值)
    lesson_limit: int = 0  # 商家设定的课时上限, 0=不限制
    artisan_name: str = ""
    enrolled_count: int = 0
    review_count: int = 0
    reject_reason: str = ""
    # 新增字段
    difficulty: str = ""
    duration_hours: float = 0
    target_audience: str = ""
    tags: List[str] = []
    free_preview_count: int = 0
    craft_intro: str = ""
    purchase_notice: str = ""
    material_type: str = "none"
    material_desc: str = ""
    material_price: float = 0
    material_shipping: str = "express"
    material_ship_address: str = ""
    material_ship_time: str = ""

    @field_validator('tags', mode='before')
    @classmethod
    def normalize_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        return v if isinstance(v, list) else []

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    title: str
    sort_order: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None


class LessonCreate(BaseModel):
    title: str
    description: str = ""
    video_url: str = ""
    duration: int = 0
    sort_order: int = 0
    is_free: bool = False


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    sort_order: Optional[int] = None
    is_free: Optional[bool] = None


class LessonResponse(BaseModel):
    id: int
    chapter_id: int
    course_id: int
    title: str
    description: str
    video_url: str
    duration: int
    sort_order: int
    is_free: bool

    class Config:
        from_attributes = True


class ChapterResponse(BaseModel):
    id: int
    course_id: int
    title: str
    sort_order: int
    lessons: list[LessonResponse] = []

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    chapters: list[ChapterResponse] = []


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    order_id: Optional[int] = None
    progress: int
    type: str = "free"
    status: str = "active"
    enrolled_at: datetime
    payment_started_at: Optional[datetime] = None
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    lesson_id: int
    completed: bool = True


class BrowseHistoryResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    browsed_at: datetime
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True


# ==================== 佣金管理 ====================

class CommissionRateCreate(BaseModel):
    category_id: Optional[int] = None
    rate: float
    remark: str = ""


class CommissionRateUpdate(BaseModel):
    rate: Optional[float] = None
    remark: Optional[str] = None


class CommissionRateResponse(BaseModel):
    id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    rate: float
    remark: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommissionAppealCreate(BaseModel):
    product_id: Optional[int] = None
    order_id: Optional[int] = None
    reason: str


class CommissionAppealResponse(BaseModel):
    id: int
    artisan_id: int
    artisan_name: str = ""
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    order_id: Optional[int] = None
    order_no: Optional[str] = None
    order_amount: Optional[float] = None
    reason: str
    status: str
    admin_note: str = ""
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppealProcess(BaseModel):
    status: str  # approved or rejected
    admin_note: str = ""
    commission_rate: Optional[float] = None  # 通过申诉时可调整佣金比例


# ==================== 用户管理 ====================

class UserListResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str] = None
    nickname: str
    avatar: str
    role: str
    status: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResult(BaseModel):
    total: int
    items: List[UserListResponse]


class UserStatusUpdate(BaseModel):
    status: bool


# ==================== 轮播图 ====================

class BannerCreate(BaseModel):
    title: str = ""
    image_url: str
    link_url: str = ""
    product_id: Optional[int] = None
    source_type: str = "platform_activity"
    sort: int = 0
    enabled: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    product_id: Optional[int] = None
    source_type: Optional[str] = None
    sort: Optional[int] = None
    enabled: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BannerResponse(BaseModel):
    id: int
    title: str
    image_url: str
    link_url: str
    product_id: Optional[int] = None
    source_type: str
    sort: int
    enabled: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
