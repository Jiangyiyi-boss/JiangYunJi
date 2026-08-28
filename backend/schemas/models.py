from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Enum, DECIMAL, Date, Time, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# ==================== 用户与角色 ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    nickname = Column(String(50), default="")
    avatar = Column(String(255), default="")
    bio = Column(String(200), default="")
    role = Column(Enum("user", "artisan", "admin"), default="user", nullable=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    artisan_profile = relationship("Artisan", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    favorites = relationship("ProductFavorite", back_populates="user")
    artisan_follows = relationship("ArtisanFollow", back_populates="user")
    posts = relationship("ForumPost", back_populates="user")
    artisan_reviews = relationship("ArtisanReview", back_populates="user")
    custom_orders = relationship("CustomOrder", foreign_keys="[CustomOrder.user_id]", back_populates="user")


class Artisan(Base):
    __tablename__ = "artisans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    real_name = Column(String(50), default="")
    id_card = Column(String(18), default="")
    specialty = Column(String(100), default="")
    bio = Column(Text, default="")
    certifications = Column(Text, default="")
    contact = Column(String(100), default="")
    shop_name = Column(String(100), default="")
    shop_avatar = Column(String(255), default="")
    shop_notice = Column(Text, default="")
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    reject_reason = Column(Text, default="")
    fans_count = Column(Integer, default=0)
    total_sales = Column(DECIMAL(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="artisan_profile")
    products = relationship("Product", back_populates="artisan")
    custom_orders = relationship("CustomOrder", foreign_keys="[CustomOrder.artisan_id]", back_populates="artisan")
    reviews = relationship("ArtisanReview", back_populates="artisan")
    follows = relationship("ArtisanFollow", back_populates="artisan")
    courses = relationship("Course", back_populates="artisan")


# ==================== 商品与分类 ====================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    icon = Column(String(10), default="")
    sort = Column(Integer, default=0)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2), nullable=True)
    stock = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    images = Column(JSON, default=list)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    status = Column(Enum("pending", "approved", "rejected", "offline", "reviewed"), default="pending")
    reject_reason = Column(Text, default="")
    is_recommend = Column(Boolean, default=False)
    listing_mode = Column(String(10), default="auto")  # "auto"=审核通过自动上架 "manual"=审核通过手动上架
    commission_status = Column(String(20), default="pending")  # pending/confirmed/appealing/appeal_rejected
    # 新增字段
    sku = Column(String(100), default="")
    limit_per_user = Column(Integer, default=0)  # deprecated, 迁移至 SKU specs 内
    shipping_type = Column(Enum("free", "fixed"), default="free")
    shipping_fee = Column(DECIMAL(10, 2), default=0)
    ship_address = Column(String(200), default="")
    ship_time = Column(Enum("48h", "7days"), default="48h")
    specs = Column(JSON, default=list)
    commission_rate = Column(DECIMAL(5, 4), default=0.1000)  # 默认10%
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    category = relationship("Category", back_populates="products")
    artisan = relationship("Artisan", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    favorites = relationship("ProductFavorite", back_populates="product")

    @property
    def category_name(self):
        return self.category.name if self.category else ""


class ProductFavorite(Base):
    __tablename__ = "product_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")


# ==================== 购物车与订单 ====================

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty = Column(Integer, default=1)
    spec_name = Column(String(100), default="")
    spec_price = Column(DECIMAL(10, 2), nullable=True)
    spec_sku = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    pay_amount = Column(DECIMAL(10, 2), nullable=False)
    goods_type = Column(Integer, default=1)  # 1=实物 2=课程
    status = Column(
        Enum("pending", "paid", "shipped", "completed", "cancelled"),
        default="pending"
    )
    pay_method = Column(String(20), default="")
    pay_time = Column(DateTime, nullable=True)
    ship_time = Column(DateTime, nullable=True)
    complete_time = Column(DateTime, nullable=True)
    cancel_time = Column(DateTime, nullable=True)
    receiver_name = Column(String(50), default="")
    receiver_phone = Column(String(20), default="")
    receiver_address = Column(Text, default="")
    remark = Column(Text, default="")
    shipping_fee = Column(DECIMAL(10, 2), default=0)  # 运费
    commission_amount = Column(DECIMAL(10, 2), default=0)  # 平台佣金总额
    payment_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    product_name = Column(String(200), default="")
    product_image = Column(String(255), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    qty = Column(Integer, nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    commission_rate = Column(DECIMAL(5, 4), default=0.1000)  # 佣金比例
    commission_amount = Column(DECIMAL(10, 2), default=0)  # 佣金金额
    artisan_income = Column(DECIMAL(10, 2), default=0)  # 匠人实收

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    course = relationship("Course")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    province = Column(String(50), default="")
    city = Column(String(50), default="")
    district = Column(String(50), default="")
    detail = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


# ==================== 匠人互动 ====================

class ArtisanFollow(Base):
    __tablename__ = "artisan_follows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="artisan_follows")
    artisan = relationship("Artisan", back_populates="follows")


class ArtisanReview(Base):
    __tablename__ = "artisan_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="artisan_reviews")
    artisan = relationship("Artisan", back_populates="reviews")


# ==================== 社区论坛 ====================

class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True, default="")
    content = Column(Text, nullable=True, default="")
    images = Column(JSON, default=list)
    video_url = Column(String(500), default="")
    category = Column(Enum("appreciation", "story", "knowledge", "share"), default="share")
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    status = Column(Enum("draft", "pending", "approved", "rejected"), default="approved")
    linked_products = Column(JSON, default=list)  # 关联商品ID列表，最多3个
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="posts")
    comments = relationship("ForumComment", back_populates="post")
    likes = relationship("PostLike", back_populates="post")
    favorites = relationship("PostFavorite", back_populates="post")


class ForumComment(Base):
    __tablename__ = "forum_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("ForumPost", back_populates="comments")
    parent = relationship("ForumComment", remote_side=[id], backref="replies")


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("ForumPost", back_populates="likes")


class PostFavorite(Base):
    __tablename__ = "post_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("ForumPost", back_populates="favorites")


class UserFollow(Base):
    """用户关注用户（非匠人关注）"""
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    follower = relationship("User", foreign_keys=[follower_id], backref="following")
    following = relationship("User", foreign_keys=[following_id], backref="followers")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum("like", "comment", "favorite", "follow", "comment_reply", "course_comment"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 触发通知的用户
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=True)
    comment_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)
    title = Column(String(200), default="")
    content = Column(Text, default="")
    link = Column(String(500), default="")
    course_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
    post = relationship("ForumPost")
    comment = relationship("ForumComment")


# ==================== 定制服务 ====================

class CustomOrder(Base):
    __tablename__ = "custom_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    description = Column(Text, nullable=False)
    budget_min = Column(DECIMAL(10, 2), nullable=True)
    budget_max = Column(DECIMAL(10, 2), nullable=True)
    deadline = Column(Date, nullable=True)
    reference_images = Column(JSON, default=list)
    order_no = Column(String(64), unique=True, nullable=True)
    status = Column(
        Enum("pending", "quoted", "accepted", "in_progress", "shipped", "completed", "rejected", "cancelled"),
        default="pending"
    )
    pay_status = Column(Enum("unpaid", "paid"), default="unpaid")
    quote_amount = Column(DECIMAL(10, 2), nullable=True)
    quote_deadline = Column(Integer, nullable=True)
    deposit_amount = Column(DECIMAL(10, 2), default=0)
    final_amount = Column(DECIMAL(10, 2), default=0)
    progress = Column(Integer, default=0)
    reject_reason = Column(String(500), default="")
    rejected_by = Column(String(10), default=None)  # "user" 或 "artisan"
    receiver_name = Column(String(50), default="")
    receiver_phone = Column(String(20), default="")
    receiver_address = Column(Text, default="")
    payment_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", foreign_keys="[CustomOrder.user_id]", back_populates="custom_orders")
    artisan = relationship("Artisan", foreign_keys="[CustomOrder.artisan_id]", back_populates="custom_orders")
    messages = relationship("CustomMessage", back_populates="custom_order")


class CustomMessage(Base):
    __tablename__ = "custom_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    custom_order_id = Column(Integer, ForeignKey("custom_orders.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now)

    custom_order = relationship("CustomOrder", back_populates="messages")


# ArtisanWallet 模型已移除 — 匠人收入统一通过仪表盘 total_revenue 展示


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=True)
    type = Column(Enum("order_income", "commission", "deposit", "custom_income"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    order_id = Column(Integer, nullable=True)
    status = Column(Enum("pending", "success", "failed"), default="success")
    remark = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

# Withdrawal 模型已移除 — 平台不支持提现功能


# ==================== 在线教育 ====================

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    cover_image = Column(String(500), default="")
    category = Column(String(50), default="")
    price = Column(DECIMAL(10, 2), default=0)
    status = Column(Enum("draft", "pending", "published", "rejected"), default="draft")
    reject_reason = Column(String(500), default="")
    # 新增字段
    difficulty = Column(String(20), default="")
    duration_hours = Column(Float, default=0)
    lesson_limit = Column(Integer, default=0)  # 商家设定的总课时上限, 0=不限制
    target_audience = Column(String(50), default="")
    tags = Column(JSON, default=list)
    free_preview_count = Column(Integer, default=0)
    craft_intro = Column(Text, default="")
    purchase_notice = Column(Text, default="")
    material_type = Column(String(20), default="none")
    material_desc = Column(Text, default="")
    material_price = Column(DECIMAL(10, 2), default=0)
    material_shipping = Column(String(20), default="express")
    material_ship_address = Column(String(500), default="")
    material_ship_time = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    artisan = relationship("Artisan", back_populates="courses")

    chapters = relationship("Chapter", back_populates="course", order_by="Chapter.sort_order",
                            cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    artisan = relationship("Artisan")


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)

    course = relationship("Course", back_populates="chapters")
    lessons = relationship("Lesson", back_populates="chapter", order_by="Lesson.sort_order",
                           cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    video_url = Column(String(500), default="")
    duration = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_free = Column(Boolean, default=False)

    chapter = relationship("Chapter", back_populates="lessons")
    course = relationship("Course")


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    progress = Column(Integer, default=0)
    type = Column(Enum("free", "purchased"), default="free", nullable=False)
    status = Column(Enum("active", "inactive"), default="active", nullable=False)
    enrolled_at = Column(DateTime, default=datetime.now)
    payment_started_at = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="enrollments")
    user = relationship("User")


class BrowseHistory(Base):
    __tablename__ = "browse_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    type = Column(String(10), default="course")  # "product" or "course"
    browsed_at = Column(DateTime, default=datetime.now)

    course = relationship("Course")
    lesson = relationship("Lesson")
    product = relationship("Product")
    user = relationship("User")


# ==================== 佣金管理 ====================

class CommissionRate(Base):
    __tablename__ = "commission_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    rate = Column(DECIMAL(5, 4), nullable=False)  # e.g. 0.1000 = 10%
    remark = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    category = relationship("Category")


class CommissionAppeal(Base):
    __tablename__ = "commission_appeals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    admin_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime, nullable=True)

    artisan = relationship("Artisan")
    product = relationship("Product")
    order = relationship("Order")


# ==================== 轮播图 ====================

class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), default="")
    image_url = Column(String(500), nullable=False)
    link_url = Column(String(500), default="")
    product_id = Column(Integer, nullable=True, comment="关联商品ID")
    source_type = Column(Enum("platform_activity", "merchant_promo", "platform_pick"), default="platform_activity")
    sort = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==================== 课程评论 ====================

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    course = relationship("Course")
    user = relationship("User")
    parent = relationship("Comment", remote_side=[id], backref="replies")


# ==================== 学习笔记 ====================

class StudyNote(Base):
    __tablename__ = "study_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    course = relationship("Course")
    lesson = relationship("Lesson")
    user = relationship("User")
