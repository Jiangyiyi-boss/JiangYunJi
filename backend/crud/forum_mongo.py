"""
匠人雅集模块 - MongoDB CRUD 服务
集合说明：
- forum_posts: 帖子
- forum_comments: 评论
- post_likes: 点赞
- post_favorites: 收藏
- user_follows: 用户关注
- notifications: 通知
"""
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from mongo_client import get_mongo_collection

CST = timezone(timedelta(hours=8))

def now_cst():
    """获取当前时间戳（毫秒），时区无关"""
    import time
    return int(time.time() * 1000)


# ==================== 帖子 ====================

def create_forum_post(user_id: int, data: dict) -> dict:
    """创建帖子"""
    status = "draft" if data.get("is_draft") else "pending"
    post = {
        "user_id": user_id,
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "images": data.get("images", []),
        "video_url": data.get("video_url", ""),
        "category": data.get("category", "share"),
        "like_count": 0,
        "comment_count": 0,
        "status": status,
        "linked_products": data.get("linked_products", [])[:3],
        "created_at": now_cst(),
        "updated_at": now_cst(),
    }
    collection = get_mongo_collection("forum_posts")
    result = collection.insert_one(post)
    post["_id"] = result.inserted_id
    return post


def update_forum_post(post_id: str, data: dict) -> dict:
    """更新帖子"""
    collection = get_mongo_collection("forum_posts")
    update_fields = {}
    if "title" in data and data["title"] is not None:
        update_fields["title"] = data["title"]
    if "content" in data and data["content"] is not None:
        update_fields["content"] = data["content"]
    if "images" in data and data["images"] is not None:
        update_fields["images"] = data["images"]
    if "video_url" in data and data["video_url"] is not None:
        update_fields["video_url"] = data["video_url"]
    if "category" in data and data["category"] is not None:
        update_fields["category"] = data["category"]
    if "linked_products" in data and data["linked_products"] is not None:
        update_fields["linked_products"] = data["linked_products"][:3]
    if "status" in data and data["status"] is not None:
        update_fields["status"] = data["status"]
    update_fields["updated_at"] = now_cst()

    collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_fields})
    return get_forum_post_by_id(post_id)


def get_forum_posts(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    status: str = "approved",
    user_id: int = None,
    liked_by: int = None,
) -> tuple:
    """查询帖子列表"""
    collection = get_mongo_collection("forum_posts")
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if user_id is not None:
        query["user_id"] = user_id

    # 如果按点赞用户筛选，先获取该用户点赞的帖子ID列表
    if liked_by is not None:
        likes_collection = get_mongo_collection("post_likes")
        liked_post_ids = [like["post_id"] for like in likes_collection.find({"user_id": liked_by})]
        if liked_post_ids:
            query["_id"] = {"$in": liked_post_ids}
        else:
            return [], 0

    total = collection.count_documents(query)
    cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = list(cursor)
    return items, total


def get_forum_post_by_id(post_id: str) -> dict:
    """根据 ID 查询帖子"""
    collection = get_mongo_collection("forum_posts")
    try:
        return collection.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None


def update_forum_post_status(post_id: str, status: str, reject_reason: str = "") -> bool:
    """审核帖子（通过/拒绝）"""
    collection = get_mongo_collection("forum_posts")
    update_fields = {"status": status, "updated_at": now_cst()}
    if reject_reason:
        update_fields["reject_reason"] = reject_reason
    result = collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_fields})
    return result.modified_count > 0


def delete_forum_post(post_id: str) -> bool:
    """删除帖子"""
    collection = get_mongo_collection("forum_posts")
    result = collection.delete_one({"_id": ObjectId(post_id)})
    # 同时删除相关评论、点赞、收藏
    get_mongo_collection("forum_comments").delete_many({"post_id": ObjectId(post_id)})
    get_mongo_collection("post_likes").delete_many({"post_id": ObjectId(post_id)})
    get_mongo_collection("post_favorites").delete_many({"post_id": ObjectId(post_id)})
    return result.deleted_count > 0


def draft_posts_by_product(product_id: int) -> int:
    """将关联某商品的所有已发布帖子改为草稿状态"""
    collection = get_mongo_collection("forum_posts")
    # linked_products 格式: [{id: product_id, ...}, ...] 或 [product_id, ...]
    result = collection.update_many(
        {
            "status": {"$in": ["approved", "pending"]},
            "linked_products": {"$elemMatch": {"id": product_id}}
        },
        {"$set": {"status": "draft", "updated_at": now_cst()}}
    )
    # 也处理旧格式（直接存 product_id 的数组）
    result2 = collection.update_many(
        {
            "status": {"$in": ["approved", "pending"]},
            "linked_products": product_id
        },
        {"$set": {"status": "draft", "updated_at": now_cst()}}
    )
    return result.modified_count + result2.modified_count


# ==================== 点赞 ====================

def toggle_post_like(user_id: int, post_id: str) -> dict:
    """切换点赞状态"""
    collection = get_mongo_collection("post_likes")
    post_collection = get_mongo_collection("forum_posts")
    existing = collection.find_one({"user_id": user_id, "post_id": ObjectId(post_id)})

    if existing:
        collection.delete_one({"_id": existing["_id"]})
        post_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"like_count": -1}})
        return {"action": "unliked"}
    else:
        collection.insert_one({
            "user_id": user_id,
            "post_id": ObjectId(post_id),
            "created_at": now_cst(),
        })
        post_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"like_count": 1}})
        return {"action": "liked"}


def is_post_liked(user_id: int, post_id: str) -> bool:
    """检查是否已点赞"""
    collection = get_mongo_collection("post_likes")
    return collection.find_one({"user_id": user_id, "post_id": ObjectId(post_id)}) is not None


# ==================== 收藏 ====================

def toggle_post_favorite(user_id: int, post_id: str) -> dict:
    """切换收藏状态"""
    collection = get_mongo_collection("post_favorites")
    existing = collection.find_one({"user_id": user_id, "post_id": ObjectId(post_id)})

    if existing:
        collection.delete_one({"_id": existing["_id"]})
        return {"action": "unfavorited"}
    else:
        collection.insert_one({
            "user_id": user_id,
            "post_id": ObjectId(post_id),
            "created_at": now_cst(),
        })
        return {"action": "favorited"}


def is_post_favorited(user_id: int, post_id: str) -> bool:
    """检查是否已收藏"""
    collection = get_mongo_collection("post_favorites")
    return collection.find_one({"user_id": user_id, "post_id": ObjectId(post_id)}) is not None


def get_user_favorites(user_id: int, skip: int = 0, limit: int = 20) -> tuple:
    """获取用户收藏的帖子"""
    collection = get_mongo_collection("post_favorites")
    post_collection = get_mongo_collection("forum_posts")

    total = collection.count_documents({"user_id": user_id})
    cursor = collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    favorites = list(cursor)

    posts = []
    for fav in favorites:
        post = post_collection.find_one({"_id": fav["post_id"]})
        if post:
            post["favorited_at"] = fav["created_at"]
            posts.append(post)
    return posts, total


# ==================== 关注 ====================

def toggle_user_follow(follower_id: int, following_id: int) -> dict:
    """切换关注状态（原子操作）"""
    collection = get_mongo_collection("user_follows")
    query = {"follower_id": follower_id, "following_id": following_id}

    # 检查是否已关注
    existing = collection.find_one(query)

    if existing:
        # 已关注 → 取消关注
        collection.delete_one(query)
        return {"action": "unfollowed"}
    else:
        # 未关注 → 关注（使用 upsert 防止并发重复）
        try:
            collection.update_one(
                query,
                {"$setOnInsert": {"created_at": now_cst()}},
                upsert=True
            )
            return {"action": "followed"}
        except Exception:
            # 并发冲突，视为已关注
            return {"action": "unfollowed"}


def is_user_following(follower_id: int, following_id: int) -> bool:
    """检查是否已关注"""
    collection = get_mongo_collection("user_follows")
    return collection.find_one({"follower_id": follower_id, "following_id": following_id}) is not None


def get_user_followers(user_id: int, skip: int = 0, limit: int = 20) -> tuple:
    """获取用户的粉丝列表"""
    collection = get_mongo_collection("user_follows")
    total = collection.count_documents({"following_id": user_id})
    items = list(collection.find({"following_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))
    return items, total


def get_user_following(user_id: int, skip: int = 0, limit: int = 20) -> tuple:
    """获取用户的关注列表"""
    collection = get_mongo_collection("user_follows")
    total = collection.count_documents({"follower_id": user_id})
    items = list(collection.find({"follower_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))
    return items, total


def is_mutual_following(user_id_a: int, user_id_b: int) -> bool:
    """检查两个用户是否互相关注"""
    collection = get_mongo_collection("user_follows")
    a_follows_b = collection.find_one({"follower_id": user_id_a, "following_id": user_id_b}) is not None
    b_follows_a = collection.find_one({"follower_id": user_id_b, "following_id": user_id_a}) is not None
    return a_follows_b and b_follows_a


def get_following_ids(user_id: int) -> list:
    """获取用户关注的用户ID列表"""
    collection = get_mongo_collection("user_follows")
    cursor = collection.find({"follower_id": user_id})
    return [item["following_id"] for item in cursor]


# ==================== 评论 ====================

def create_forum_comment(user_id: int, data: dict) -> dict:
    """创建评论"""
    comment = {
        "post_id": ObjectId(data["post_id"]),
        "user_id": user_id,
        "parent_id": ObjectId(data["parent_id"]) if data.get("parent_id") else None,
        "content": data["content"],
        "like_count": 0,
        "created_at": now_cst(),
    }
    collection = get_mongo_collection("forum_comments")
    result = collection.insert_one(comment)
    comment["_id"] = result.inserted_id

    # 更新帖子评论数
    post_collection = get_mongo_collection("forum_posts")
    post_collection.update_one({"_id": ObjectId(data["post_id"])}, {"$inc": {"comment_count": 1}})

    return comment




def get_forum_comments(post_id: str) -> list:
    """获取帖子所有评论（包含一级和回复）"""
    collection = get_mongo_collection("forum_comments")
    return list(collection.find({"post_id": ObjectId(post_id)}).sort("created_at", 1))


# ==================== 通知 ====================

def create_notification(user_id: int, notif_type: str, actor_id: int, post_id: str = None, comment_id: str = None):
    """创建通知"""
    collection = get_mongo_collection("notifications")
    # 检查是否已存在相同通知（防止重复）
    query = {
        "user_id": user_id,
        "type": notif_type,
        "actor_id": actor_id,
    }
    if post_id:
        query["post_id"] = ObjectId(post_id)
    if comment_id:
        query["comment_id"] = ObjectId(comment_id)
    existing = collection.find_one(query)
    if existing:
        return existing

    notif = {
        "user_id": user_id,
        "type": notif_type,
        "actor_id": actor_id,
        "post_id": ObjectId(post_id) if post_id else None,
        "comment_id": ObjectId(comment_id) if comment_id else None,
        "is_read": False,
        "created_at": now_cst(),
    }
    collection.insert_one(notif)
    return notif


def get_notifications(user_id: int, skip: int = 0, limit: int = 20, notif_type: str = None) -> tuple:
    """获取用户通知"""
    collection = get_mongo_collection("notifications")
    query = {"user_id": user_id}
    if notif_type:
        # 支持逗号分隔的多个类型，如 "follow,friend"
        types = [t.strip() for t in notif_type.split(",")]
        if len(types) == 1:
            query["type"] = types[0]
        else:
            query["type"] = {"$in": types}
    # 不传 type 则返回所有类型（包含 follow）

    total = collection.count_documents(query)
    items = list(collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
    return items, total


def mark_notification_read(notification_id: str, user_id: int) -> bool:
    """标记通知已读"""
    collection = get_mongo_collection("notifications")
    result = collection.update_one(
        {"_id": ObjectId(notification_id), "user_id": user_id},
        {"$set": {"is_read": True}},
    )
    return result.modified_count > 0


def mark_all_notifications_read(user_id: int):
    """标记所有通知已读"""
    collection = get_mongo_collection("notifications")
    collection.update_many({"user_id": user_id, "is_read": False}, {"$set": {"is_read": True}})


def get_unread_notification_count(user_id: int) -> int:
    """获取未读通知数"""
    collection = get_mongo_collection("notifications")
    return collection.count_documents({"user_id": user_id, "is_read": False})


# ==================== 论坛浏览记录 ====================

def record_forum_browse(user_id: int, post_id: str):
    """记录论坛帖子浏览"""
    collection = get_mongo_collection("forum_browse_history")
    # 更新或插入（同一用户同一帖子只保留最新浏览时间）
    collection.update_one(
        {"user_id": user_id, "post_id": ObjectId(post_id)},
        {"$set": {"browsed_at": now_cst()}},
        upsert=True,
    )


def get_forum_browse_history(user_id: int, skip: int = 0, limit: int = 20) -> tuple:
    """获取论坛浏览记录"""
    collection = get_mongo_collection("forum_browse_history")
    post_collection = get_mongo_collection("forum_posts")
    total = collection.count_documents({"user_id": user_id})
    cursor = collection.find({"user_id": user_id}).sort("browsed_at", -1).skip(skip).limit(limit)
    items = []
    for b in cursor:
        post = post_collection.find_one({"_id": b["post_id"]})
        images = post.get("images", []) if post else []
        items.append({
            "id": str(b["_id"]),
            "post_id": str(b["post_id"]),
            "post_title": post.get("title", "") if post else "",
            "post_content": (post.get("content", "") or "")[:100] if post else "",
            "post_image": images[0] if images else "",
            "post_category": post.get("category", "") if post else "",
            "browsed_at": b["browsed_at"],
        })
    return items, total


def delete_forum_browse(user_id: int, browse_id: str) -> bool:
    """删除单条浏览记录"""
    collection = get_mongo_collection("forum_browse_history")
    result = collection.delete_one({"_id": ObjectId(browse_id), "user_id": user_id})
    return result.deleted_count > 0


def clear_forum_browse_history(user_id: int):
    """清空论坛浏览记录"""
    collection = get_mongo_collection("forum_browse_history")
    collection.delete_many({"user_id": user_id})
