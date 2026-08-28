"""
匠人雅集模块 - MongoDB 版本路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from bson import ObjectId
from crud.forum_mongo import (
    create_forum_post, update_forum_post, get_forum_posts, get_forum_post_by_id,
    toggle_post_like, toggle_post_favorite, get_user_favorites, is_post_liked, is_post_favorited,
    create_forum_comment, get_forum_comments,
    delete_forum_post, update_forum_post_status,
    toggle_user_follow, get_user_followers, get_user_following, is_user_following, is_mutual_following, get_following_ids,
    get_notifications, get_unread_notification_count, create_notification,
    mark_notification_read, mark_all_notifications_read,
    record_forum_browse, get_forum_browse_history, delete_forum_browse, clear_forum_browse_history,
)
from schemas import ForumPostCreate, ForumPostUpdate, ForumCommentCreate
from dependencies import get_current_user, get_current_user_or_none, require_role
from models import User
from database import get_db

router = APIRouter(prefix="/api/forum", tags=["论坛"])


def _get_user_info(db, user_id: int) -> dict:
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"nickname": "", "avatar": "", "role": "", "artisan_id": None, "shop_name": ""}
    result = {
        "nickname": user.nickname or user.username,
        "avatar": user.avatar or "",
        "role": user.role,
        "artisan_id": None,
        "shop_name": "",
    }
    if user.role == "artisan" and hasattr(user, "artisan_profile") and user.artisan_profile:
        result["artisan_id"] = user.artisan_profile.id
        result["shop_name"] = user.artisan_profile.shop_name or ""
    return result


def _enrich_post(db, post: dict, current_user: User = None) -> dict:
    """为帖子添加作者信息和互动状态"""
    user_id = post.get("user_id")
    author = _get_user_info(db, user_id)

    result = {
        "id": str(post["_id"]),
        "user_id": user_id,
        "title": post.get("title", ""),
        "content": post.get("content", ""),
        "images": post.get("images", []),
        "video_url": post.get("video_url", ""),
        "category": post.get("category", "share"),
        "like_count": post.get("like_count", 0),
        "comment_count": post.get("comment_count", 0),
        "status": post.get("status", "approved"),
        "linked_products": post.get("linked_products", []),
        "created_at": post.get("created_at"),
        "is_liked": False,
        "is_favorited": False,
        "is_followed": False,
        "is_mutual_followed": False,
        "author_nickname": author["nickname"],
        "author_avatar": author["avatar"],
        "author_role": author["role"],
        "author_artisan_id": author["artisan_id"],
        "author_shop_name": author["shop_name"],
    }

    if current_user:
        result["is_liked"] = is_post_liked(current_user.id, str(post["_id"]))
        result["is_favorited"] = is_post_favorited(current_user.id, str(post["_id"]))
        result["is_followed"] = is_user_following(current_user.id, user_id)
        result["is_mutual_followed"] = is_mutual_following(current_user.id, user_id)

    return result


def _enrich_comment(db, comment: dict, current_user: User = None) -> dict:
    """为评论添加作者信息"""
    author = _get_user_info(db, comment.get("user_id"))
    result = {
        "id": str(comment["_id"]),
        "post_id": str(comment.get("post_id")),
        "user_id": comment.get("user_id"),
        "parent_id": str(comment.get("parent_id")) if comment.get("parent_id") else None,
        "content": comment.get("content", ""),
        "like_count": comment.get("like_count", 0),
        "created_at": comment.get("created_at"),
        "author_nickname": author["nickname"],
        "author_avatar": author["avatar"],
    }
    return result


def _enrich_notification(db, notif: dict) -> dict:
    """为通知添加关联信息"""
    actor = _get_user_info(db, notif.get("actor_id"))
    post_id = notif.get("post_id")
    post_title = ""
    if post_id:
        post = get_forum_post_by_id(str(post_id))
        post_title = post.get("title", "") if post else ""

    created_at = notif.get("created_at")
    # 保持为数字时间戳（毫秒），前端直接解析
    if created_at and not isinstance(created_at, (int, float)):
        if hasattr(created_at, 'timestamp'):
            created_at = int(created_at.timestamp() * 1000)
        else:
            created_at = int(created_at)

    notif_type = notif.get("type")
    notif_user_id = notif.get("user_id")
    notif_actor_id = notif.get("actor_id")

    # 对关注类通知，检查是否互相关注
    is_mutual = False
    if notif_type in ("follow", "friend") and notif_user_id and notif_actor_id:
        is_mutual = is_mutual_following(notif_user_id, notif_actor_id)

    return {
        "id": str(notif["_id"]),
        "user_id": notif_user_id,
        "type": notif_type,
        "actor_id": notif_actor_id,
        "post_id": str(post_id) if post_id else None,
        "comment_id": str(notif.get("comment_id")) if notif.get("comment_id") else None,
        "is_read": notif.get("is_read", False),
        "created_at": created_at,
        "actor_nickname": actor["nickname"],
        "actor_avatar": actor["avatar"],
        "post_title": post_title,
        "is_mutual_followed": is_mutual,
    }


# ==================== 帖子 CRUD ====================

@router.post("")
def create_post(
    data: ForumPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 验证：至少包含文字/图片/视频其中一项
    if not data.content and not data.images and not data.video_url:
        raise HTTPException(status_code=400, detail="帖子内容不能为空（文字、图片、视频至少包含一项）")
    # 图片和视频不可同时存在
    if data.images and data.video_url:
        raise HTTPException(status_code=400, detail="图片和视频不可同时上传")

    post_data = data.model_dump()
    post = create_forum_post(current_user.id, post_data)
    return _enrich_post(db, post, current_user)


@router.put("/{post_id}")
def update_post(
    post_id: str,
    data: ForumPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_forum_post_by_id(post_id)
    if not post or post.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="帖子不存在或无权限")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = update_forum_post(post_id, update_data)
    return _enrich_post(db, updated, current_user)


@router.get("")
def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    category: str = Query(None),
    tab: str = Query("all"),
    user_id: int = Query(None),
    status: str = Query(None),
    liked_by: int = Query(None),
    current_user: User = Depends(get_current_user_or_none),
    db: Session = Depends(get_db),
):
    # 草稿只能看自己的
    if status == "draft":
        if not current_user:
            return {"total": 0, "items": []}
        user_id = current_user.id

    # 如果传了 user_id / status / liked_by，直接使用（用于个人主页等场景）
    if user_id is not None or liked_by is not None:
        items, total = get_forum_posts(
            skip=skip, limit=limit, category=category,
            status=status, user_id=user_id, liked_by=liked_by,
        )
        return {
            "total": total,
            "items": [_enrich_post(db, p, current_user) for p in items],
        }

    # Tab 模式
    if tab == "following" and current_user:
        following_ids = get_following_ids(current_user.id)
        if following_ids:
            items, total = get_forum_posts(skip=skip, limit=limit, category=category, status="approved")
            items = [p for p in items if p.get("user_id") in following_ids]
            total = len(items)
        else:
            items, total = [], 0
    elif tab == "artisan":
        # 获取所有匠人用户ID
        artisan_ids = [u.id for u in db.query(User).filter(User.role == "artisan").all()]
        if artisan_ids:
            items, total = get_forum_posts(skip=skip, limit=limit, category=category, status="approved")
            items = [p for p in items if p.get("user_id") in artisan_ids]
            total = len(items)
        else:
            items, total = [], 0
    elif tab == "hot":
        items, total = get_forum_posts(skip=skip, limit=limit, category=category, status="approved")
        items = sorted(items, key=lambda p: p.get("like_count", 0) + p.get("comment_count", 0), reverse=True)
        total = len(items)
    else:
        items, total = get_forum_posts(skip=skip, limit=limit, category=category, status="approved")

    return {
        "total": total,
        "items": [_enrich_post(db, p, current_user) for p in items],
    }


# ==================== 收藏（必须在 /{post_id} 之前） ====================

@router.get("/favorites")
def get_my_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts, total = get_user_favorites(current_user.id, skip, limit)
    return {
        "total": total,
        "items": [_enrich_post(db, p, current_user) for p in posts],
    }


# ==================== 通知（必须在 /{post_id} 之前） ====================

@router.get("/notifications")
def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = get_notifications(current_user.id, skip, limit, type)
    return {
        "total": total,
        "items": [_enrich_notification(db, n) for n in items],
    }


@router.get("/notifications/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = get_unread_notification_count(current_user.id)
    return {"count": count}


@router.post("/notifications/read-all")
def mark_all_notifications_read_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mark_all_notifications_read(current_user.id)
    return {"message": "ok"}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read_endpoint(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mark_notification_read(notification_id, current_user.id)
    return {"message": "ok"}


# ==================== 论坛浏览记录 ====================

@router.post("/posts/{post_id}/browse")
def browse_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录论坛帖子浏览"""
    record_forum_browse(current_user.id, post_id)
    return {"message": "ok"}


@router.get("/browse-history")
def get_browse_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取论坛浏览记录"""
    items, total = get_forum_browse_history(current_user.id, skip, limit)
    return {"total": total, "items": items}


@router.delete("/browse-history/{browse_id}")
def delete_browse_record(
    browse_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除单条浏览记录"""
    if not delete_forum_browse(current_user.id, browse_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "已删除"}


@router.delete("/browse-history")
def clear_browse_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空论坛浏览记录"""
    clear_forum_browse_history(current_user.id)
    return {"message": "已清空"}


# ==================== 管理员审核 ====================

@router.get("/admin/posts")
def admin_list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    status: str = Query(None),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """管理员查看帖子列表（可按状态筛选）"""
    items, total = get_forum_posts(skip=skip, limit=limit, status=status)
    return {
        "total": total,
        "items": [_enrich_post(db, p, current_user) for p in items],
    }


@router.post("/admin/posts/{post_id}/approve")
def admin_approve_post(
    post_id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """审核通过帖子"""
    if not update_forum_post_status(post_id, "approved"):
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"message": "审核通过"}


@router.post("/admin/posts/{post_id}/reject")
def admin_reject_post(
    post_id: str,
    reason: str = Query(""),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """拒绝帖子"""
    if not update_forum_post_status(post_id, "rejected", reason):
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"message": "已拒绝"}


# ==================== 用户关注（必须在 /{post_id} 之前） ====================

@router.post("/users/{user_id}/follow")
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    result = toggle_user_follow(current_user.id, user_id)
    # 如果是关注，创建通知（始终创建 follow 类型，前端根据关注状态判断是否互关）
    if result["action"] == "followed":
        create_notification(user_id, "follow", current_user.id)
        result["is_mutual_followed"] = is_mutual_following(current_user.id, user_id)
    else:
        result["is_mutual_followed"] = False
    return result


@router.get("/users/{user_id}")
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """获取用户基本信息"""
    user_info = _get_user_info(db, user_id)
    if not user_info["nickname"]:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户统计
    posts_count = get_mongo_collection("forum_posts").count_documents({"user_id": user_id})
    followers_count, _ = get_user_followers(user_id, 0, 1)
    following_count, _ = get_user_following(user_id, 0, 1)
    
    # 获取获赞数
    likes_count = 0
    user_posts = list(get_mongo_collection("forum_posts").find({"user_id": user_id}, {"_id": 1}))
    if user_posts:
        post_ids = [p["_id"] for p in user_posts]
        likes_count = get_mongo_collection("forum_likes").count_documents({
            "target_type": "post",
            "target_id": {"$in": post_ids}
        })
    
    return {
        **user_info,
        "stats": {
            "posts": posts_count,
            "followers": len(followers_count),
            "following": len(following_count),
            "likes": likes_count
        }
    }


@router.get("/users/{user_id}/followers")
def get_followers(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    items, total = get_user_followers(user_id, skip, limit)
    results = []
    for f in items:
        follower = _get_user_info(db, f["follower_id"])
        results.append({
            "id": str(f["_id"]),
            "follower_id": f["follower_id"],
            "following_id": f["following_id"],
            "created_at": f["created_at"],
            "follower_nickname": follower["nickname"],
            "follower_avatar": follower["avatar"],
        })
    return {"total": total, "items": results}


@router.get("/users/{user_id}/following")
def get_following(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    items, total = get_user_following(user_id, skip, limit)
    results = []
    for f in items:
        following = _get_user_info(db, f["following_id"])
        results.append({
            "id": str(f["_id"]),
            "follower_id": f["follower_id"],
            "following_id": f["following_id"],
            "created_at": f["created_at"],
            "follower_nickname": following["nickname"],
            "follower_avatar": following["avatar"],
        })
    return {"total": total, "items": results}


# ==================== 帖子详情/删除（动态路由放后面） ====================

@router.get("/{post_id}")
def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user_or_none),
    db: Session = Depends(get_db),
):
    post = get_forum_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return _enrich_post(db, post, current_user)


@router.delete("/{post_id}")
def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_forum_post_by_id(post_id)
    if not post or post.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="帖子不存在或无权限")
    if not delete_forum_post(post_id):
        raise HTTPException(status_code=404, detail="删除失败")
    return {"message": "删除成功"}


# ==================== 互动 ====================

@router.post("/{post_id}/like")
def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = toggle_post_like(current_user.id, post_id)
    # 如果是点赞，创建通知
    if result["action"] == "liked":
        post = get_forum_post_by_id(post_id)
        if post and post.get("user_id") != current_user.id:
            create_notification(post["user_id"], "like", current_user.id, post_id)
    return result


@router.post("/{post_id}/favorite")
def favorite_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = toggle_post_favorite(current_user.id, post_id)
    # 如果是收藏，创建通知
    if result["action"] == "favorited":
        post = get_forum_post_by_id(post_id)
        if post and post.get("user_id") != current_user.id:
            create_notification(post["user_id"], "favorite", current_user.id, post_id)
    return result


# ==================== 评论 ====================

@router.post("/{post_id}/comments")
def create_comment(
    post_id: str,
    data: ForumCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment_data = {
        "post_id": post_id,
        "parent_id": str(data.parent_id) if data.parent_id else None,
        "content": data.content,
    }
    comment = create_forum_comment(current_user.id, comment_data)

    # 创建通知
    post = get_forum_post_by_id(post_id)
    parent_comment = None

    # 如果是回复评论，给被回复评论的作者发通知
    if data.parent_id:
        from mongo_client import get_mongo_collection
        parent_comment = get_mongo_collection("forum_comments").find_one({"_id": ObjectId(str(data.parent_id))})
        if parent_comment and parent_comment.get("user_id") != current_user.id:
            create_notification(
                parent_comment["user_id"], "reply", current_user.id,
                post_id, str(comment["_id"]),
            )

    # 给帖子作者发通知（如果是回复，且帖子作者与被回复评论作者不是同一人）
    if post and post.get("user_id") != current_user.id:
        parent_author_id = parent_comment.get("user_id") if parent_comment else None
        if not data.parent_id or post.get("user_id") != parent_author_id:
            create_notification(post["user_id"], "comment", current_user.id, post_id, str(comment["_id"]))

    return _enrich_comment(db, comment, current_user)


@router.get("/{post_id}/comments")
def get_comments(
    post_id: str,
    current_user: User = Depends(get_current_user_or_none),
    db: Session = Depends(get_db),
):
    comments = get_forum_comments(post_id)
    return [_enrich_comment(db, c, current_user) for c in comments]


