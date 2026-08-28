from sqlalchemy.orm import Session
from models import (
    ArtisanFollow,
    ForumPost, ForumComment, PostLike, PostFavorite, UserFollow, Notification,
    CustomOrder, CustomMessage,
    Address, Transaction,
    User, Artisan,
)
from schemas import (
    ForumPostCreate, ForumCommentCreate,
    CustomOrderCreate, CustomMessageCreate, CustomQuote,
    AddressCreate,
)


# ==================== 匠人关注 ====================

def toggle_artisan_follow(db: Session, user_id: int, artisan_id: int):
    existing = db.query(ArtisanFollow).filter(
        ArtisanFollow.user_id == user_id,
        ArtisanFollow.artisan_id == artisan_id,
    ).first()

    if existing:
        db.delete(existing)
        db.flush()
        # Update fans count
        count = db.query(ArtisanFollow).filter(ArtisanFollow.artisan_id == artisan_id).count()
        from models import Artisan
        art = db.query(Artisan).filter(Artisan.id == artisan_id).first()
        if art:
            art.fans_count = max(0, count)
        db.commit()
        return {"action": "unfollowed"}
    else:
        follow = ArtisanFollow(user_id=user_id, artisan_id=artisan_id)
        db.add(follow)
        db.flush()
        from models import Artisan
        count = db.query(ArtisanFollow).filter(ArtisanFollow.artisan_id == artisan_id).count()
        art = db.query(Artisan).filter(Artisan.id == artisan_id).first()
        if art:
            art.fans_count = count
        db.commit()
        return {"action": "followed"}


def get_user_follows(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    from models import Artisan
    query = db.query(Artisan).join(
        ArtisanFollow, Artisan.id == ArtisanFollow.artisan_id
    ).filter(ArtisanFollow.user_id == user_id)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


# ==================== 论坛帖子 ====================


# ==================== 论坛 ====================

def create_forum_post(db: Session, user_id: int, data: ForumPostCreate) -> ForumPost:
    status = "draft" if data.is_draft else "approved"
    post = ForumPost(
        user_id=user_id,
        title=data.title or "",
        content=data.content or "",
        images=data.images or [],
        video_url=data.video_url or "",
        category=data.category,
        status=status,
        linked_products=data.linked_products[:3] if data.linked_products else [],
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_forum_post(db: Session, post_id: int, data) -> ForumPost:
    post = get_forum_post_by_id(db, post_id)
    if not post:
        return None
    if data.title is not None:
        post.title = data.title
    if data.content is not None:
        post.content = data.content
    if data.images is not None:
        post.images = data.images
    if data.video_url is not None:
        post.video_url = data.video_url
    if data.category is not None:
        post.category = data.category
    if data.linked_products is not None:
        post.linked_products = data.linked_products[:3]
    if data.status is not None:
        post.status = data.status
    db.commit()
    db.refresh(post)
    return post


def get_forum_posts(db: Session, skip: int = 0, limit: int = 20, category: str = None, status: str = "approved", user_id: int = None, liked_by: int = None):
    query = db.query(ForumPost)
    if category:
        query = query.filter(ForumPost.category == category)
    if status:
        query = query.filter(ForumPost.status == status)
    if user_id is not None:
        query = query.filter(ForumPost.user_id == user_id)
    if liked_by is not None:
        query = query.join(PostLike).filter(PostLike.user_id == liked_by)
    total = query.count()
    items = query.order_by(ForumPost.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_forum_post_by_id(db: Session, post_id: int):
    return db.query(ForumPost).filter(ForumPost.id == post_id).first()


def toggle_post_like(db: Session, user_id: int, post_id: int):
    existing = db.query(PostLike).filter(
        PostLike.user_id == user_id,
        PostLike.post_id == post_id,
    ).first()

    post = get_forum_post_by_id(db, post_id)
    if existing:
        db.delete(existing)
        if post:
            post.like_count = max(0, post.like_count - 1)
        db.commit()
        return {"action": "unliked"}
    else:
        like = PostLike(user_id=user_id, post_id=post_id)
        db.add(like)
        if post:
            post.like_count += 1
            # 发送通知
            if post.user_id != user_id:
                _create_notification(db, post.user_id, "like", user_id, post_id)
        db.commit()
        return {"action": "liked"}


def toggle_post_favorite(db: Session, user_id: int, post_id: int):
    existing = db.query(PostFavorite).filter(
        PostFavorite.user_id == user_id,
        PostFavorite.post_id == post_id,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "unfavorited"}
    else:
        fav = PostFavorite(user_id=user_id, post_id=post_id)
        db.add(fav)
        post = get_forum_post_by_id(db, post_id)
        if post and post.user_id != user_id:
            _create_notification(db, post.user_id, "favorite", user_id, post_id)
        db.commit()
        return {"action": "favorited"}


def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(PostFavorite).filter(PostFavorite.user_id == user_id)
    total = query.count()
    items = query.order_by(PostFavorite.created_at.desc()).offset(skip).limit(limit).all()
    posts = [get_forum_post_by_id(db, f.post_id) for f in items]
    posts = [p for p in posts if p is not None]
    return posts, total


def create_forum_comment(db: Session, user_id: int, data: ForumCommentCreate) -> ForumComment:
    comment = ForumComment(
        post_id=data.post_id,
        user_id=user_id,
        parent_id=data.parent_id,
        content=data.content,
    )
    db.add(comment)

    post = get_forum_post_by_id(db, data.post_id)
    if post:
        post.comment_count += 1
        # 发送通知
        if post.user_id != user_id:
            _create_notification(db, post.user_id, "comment", user_id, post_id, comment.id)

    db.commit()
    db.refresh(comment)
    return comment


def delete_forum_comment(db: Session, comment_id: int, user_id: int, is_artisan: bool = False) -> bool:
    """删除评论：评论作者、帖子作者(商家)可删除"""
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    if not comment:
        return False
    post = get_forum_post_by_id(db, comment.post_id)
    # 评论作者可以删除，帖子作者(商家)可以删除自己帖子下的评论
    if comment.user_id == user_id or (post and post.user_id == user_id):
        db.delete(comment)
        if post:
            post.comment_count = max(0, post.comment_count - 1)
        db.commit()
        return True
    return False


def get_forum_comments(db: Session, post_id: int, parent_id: int = None):
    query = db.query(ForumComment).filter(ForumComment.post_id == post_id)
    if parent_id is not None:
        query = query.filter(ForumComment.parent_id == parent_id)
    else:
        query = query.filter(ForumComment.parent_id.is_(None))
    return query.order_by(ForumComment.created_at.asc()).all()


def delete_forum_post(db: Session, post_id: int) -> bool:
    post = get_forum_post_by_id(db, post_id)
    if post:
        db.delete(post)
        db.commit()
        return True
    return False


def toggle_user_follow(db: Session, follower_id: int, following_id: int):
    """用户关注/取消关注用户"""
    existing = db.query(UserFollow).filter(
        UserFollow.follower_id == follower_id,
        UserFollow.following_id == following_id,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "unfollowed"}
    else:
        follow = UserFollow(follower_id=follower_id, following_id=following_id)
        db.add(follow)
        _create_notification(db, following_id, "follow", follower_id)
        db.commit()
        return {"action": "followed"}


def get_user_followers(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(UserFollow).filter(UserFollow.following_id == user_id)
    total = query.count()
    items = query.order_by(UserFollow.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_user_following(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    query = db.query(UserFollow).filter(UserFollow.follower_id == user_id)
    total = query.count()
    items = query.order_by(UserFollow.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def is_user_following(db: Session, follower_id: int, following_id: int) -> bool:
    return db.query(UserFollow).filter(
        UserFollow.follower_id == follower_id,
        UserFollow.following_id == following_id,
    ).first() is not None


def get_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 20, notification_type: str = None):
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False


def mark_all_notifications_read(db: Session, user_id: int):
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()


def get_unread_notification_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
    ).count()


def _create_notification(db: Session, user_id: int, notif_type: str, actor_id: int, post_id: int = None, comment_id: int = None):
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        actor_id=actor_id,
        post_id=post_id,
        comment_id=comment_id,
    )
    db.add(notif)


# ==================== 定制服务 ====================

def create_custom_order(db: Session, user_id: int, data: CustomOrderCreate) -> CustomOrder:
    from datetime import date as date_type
    deadline_val = None
    if data.deadline:
        try:
            deadline_val = date_type.fromisoformat(data.deadline)
        except (ValueError, TypeError):
            deadline_val = None

    order = CustomOrder(
        user_id=user_id,
        artisan_id=data.artisan_id,
        description=data.description,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        deadline=deadline_val,
        reference_images=data.reference_images or [],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_custom_orders(db: Session, user_id: int = None, artisan_id: int = None, skip: int = 0, limit: int = 20):
    query = db.query(CustomOrder)
    if user_id:
        query = query.filter(CustomOrder.user_id == user_id)
    if artisan_id:
        query = query.filter(CustomOrder.artisan_id == artisan_id)
    total = query.count()
    items = query.order_by(CustomOrder.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_custom_order_by_id(db: Session, order_id: int):
    return db.query(CustomOrder).filter(CustomOrder.id == order_id).first()


def quote_custom_order(db: Session, order_id: int, artisan_id: int, data: CustomQuote) -> CustomOrder:
    order = get_custom_order_by_id(db, order_id)
    if order and order.artisan_id == artisan_id:
        order.quote_amount = data.quote_amount
        order.quote_deadline = data.quote_deadline
        order.status = "quoted"
        order.reject_reason = ""  # 清除之前的拒绝理由
        order.rejected_by = None
        db.commit()
        db.refresh(order)
    return order


def accept_custom_order(db: Session, order_id: int, user_id: int) -> CustomOrder:
    order = get_custom_order_by_id(db, order_id)
    if order and order.user_id == user_id and order.status == "quoted":
        order.status = "accepted"
        db.commit()
        db.refresh(order)
    return order


def update_custom_progress(db: Session, order_id: int, artisan_id: int, progress: int) -> CustomOrder:
    order = get_custom_order_by_id(db, order_id)
    if order and order.artisan_id == artisan_id:
        order.progress = progress
        if progress < 0:
            order.status = "rejected"
        elif progress >= 100:
            order.status = "completed"
        else:
            order.status = "in_progress"
        db.commit()
        db.refresh(order)
    return order


def pay_custom_order(db: Session, order_id: int, user_id: int) -> CustomOrder:
    """标记定制订单已支付"""
    order = get_custom_order_by_id(db, order_id)
    if order and order.user_id == user_id and order.status == "accepted":
        order.status = "in_progress"
        order.pay_status = "paid"
        order.payment_started_at = None  # 清除倒计时
        if not order.order_no:
            order.order_no = f"CUSTOM-{order_id}"
        db.commit()
        db.refresh(order)
    return order


def cancel_custom_order_by_timeout(db: Session, order_id: int) -> CustomOrder:
    """超时取消定制订单（由 RabbitMQ 消费者调用）"""
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise ValueError("定制订单不存在")
    if order.status != "accepted" or order.pay_status == "paid":
        raise ValueError("订单状态不允许取消（已支付或状态已变更）")

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


def create_custom_message(db: Session, sender_id: int, data: CustomMessageCreate) -> CustomMessage:
    msg = CustomMessage(
        custom_order_id=data.custom_order_id,
        sender_id=sender_id,
        content=data.content,
        images=data.images,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_custom_messages(db: Session, order_id: int):
    return db.query(CustomMessage).filter(
        CustomMessage.custom_order_id == order_id
    ).order_by(CustomMessage.created_at.asc()).all()


# ==================== 地址 ====================

def get_addresses(db: Session, user_id: int):
    return db.query(Address).filter(Address.user_id == user_id).all()


def create_address(db: Session, user_id: int, data: AddressCreate) -> Address:
    if data.is_default:
        db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})

    address = Address(
        user_id=user_id,
        name=data.name,
        phone=data.phone,
        province=data.province,
        city=data.city,
        district=data.district,
        detail=data.detail,
        is_default=data.is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, address: Address, data: AddressCreate) -> Address:
    if data.is_default:
        db.query(Address).filter(
            Address.user_id == address.user_id,
            Address.id != address.id,
        ).update({"is_default": False})

    for key, value in data.model_dump().items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address_id: int, user_id: int) -> bool:
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if address:
        db.delete(address)
        db.commit()
        return True
    return False


# ==================== 财务管理 ====================

def get_transactions(db: Session, artisan_id: int = None, skip: int = 0, limit: int = 20):
    query = db.query(Transaction)
    if artisan_id:
        query = query.filter(Transaction.artisan_id == artisan_id)
    total = query.count()
    items = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
