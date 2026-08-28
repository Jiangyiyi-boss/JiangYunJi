"""Router for online education — courses, chapters, lessons, enrollments."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse,
    ChapterCreate, ChapterUpdate, ChapterResponse,
    LessonCreate, LessonUpdate, LessonResponse,
    EnrollmentResponse, ProgressUpdate, BrowseHistoryResponse,
)
from crud.courses import (
    create_course, get_course_by_id, get_courses, get_artisan_courses,
    update_course, delete_course,
    create_chapter, get_chapter_by_id, get_chapters, update_chapter,
    delete_chapter,
    create_lesson, get_lesson_by_id, get_lessons, update_lesson, delete_lesson,
    enroll_course, drop_course, get_enrollment, get_user_enrollments, update_enrollment_progress,
    record_browse, get_user_browse_history, delete_browse_history, clear_browse_history,
    create_comment, get_course_comments,
    create_note, update_note, get_user_notes, delete_note,
)
from crud.users import get_artisan_by_user_id
from dependencies import get_current_user, get_current_user_or_none, require_role
from models import User
from es import SearchService
from utils.es_sync_helper import safe_sync_course, safe_delete_course

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/courses", tags=["在线教育"])


def get_search_service() -> SearchService:
    return SearchService()


# ==================== Public ====================

@router.get("", response_model=dict)
def list_courses(
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    keyword: str = None,
    artisan_id: int = None,
    price_type: str = None,
    sort_by: str = Query("_score", description="排序字段: _score, price, enrolled_count, created_at"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    difficulty: str = Query(None, description="难度筛选"),
    is_free: bool = Query(None, description="是否免费"),
    price_min: float = Query(None, ge=0, description="最低价格"),
    price_max: float = Query(None, ge=0, description="最高价格"),
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    # 兼容前端 price_type 参数（free/paid）与 ES 的 is_free 参数
    if price_type == "free":
        is_free = True
    elif price_type == "paid":
        is_free = False

    # 尝试使用 ES 搜索
    if keyword or sort_by != "_score" or category or difficulty or is_free is not None or price_min is not None or price_max is not None:
        try:
            result = search_service.search_courses(
                keyword=keyword or "",
                page=(skip // limit) + 1 if limit > 0 else 1,
                size=limit,
                sort_by=sort_by,
                sort_order=sort_order,
                category=category,
                difficulty=difficulty,
                price_min=price_min,
                price_max=price_max,
                is_free=is_free,
            )
            if "error" not in result:
                # ES 返回 0 条 + 有关键词 → 可能索引不同步，降级到 MySQL 兜底
                if result.get("total", 0) == 0 and keyword:
                    logger.info(f"ES 课程搜索结果为空，尝试 MySQL 兜底: keyword={keyword}")
                else:
                    return {
                        "items": result.get("results", []),
                        "total": result.get("total", 0),
                        "page": result.get("page", 1),
                        "size": result.get("size", limit),
                        "has_more": result.get("has_more", False),
                        "fallback": False,
                    }
            else:
                logger.warning(f"课程搜索 ES 异常，降级到 MySQL: {result['error']}")
        except Exception as e:
            logger.warning(f"课程搜索 ES 异常，降级到 MySQL: {e}")

    # 降级到 MySQL 查询
    items, total = get_courses(
        db, skip=skip, limit=limit, category=category,
        artisan_id=artisan_id, keyword=keyword, status="published",
        price_type=price_type, difficulty=difficulty,
        is_free=is_free, price_min=price_min, price_max=price_max,
    )
    return {
        "total": total,
        "items": [
            {
                **CourseResponse.model_validate(c).model_dump(),
                "artisan_name": c.artisan.shop_name or c.artisan.real_name or "",
                "chapter_count": len(c.chapters),
                "lesson_count": sum(len(ch.lessons) for ch in c.chapters),
                "enrolled_count": sum(1 for e in c.enrollments if e.status == "active"),
                "review_count": 0,
            }
            for c in items
        ],
        "fallback": True,
    }


@router.get("/suggest", response_model=dict)
def suggest_courses(
    prefix: str = Query(..., min_length=1, max_length=50, description="搜索前缀"),
    size: int = Query(10, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    search_service: SearchService = Depends(get_search_service),
):
    """课程搜索建议（自动补全）"""
    from sensitive_words import sensitive_filter

    is_safe, matched = sensitive_filter.check(prefix)
    if not is_safe:
        return {"code": 400, "message": "搜索词包含违规内容", "data": []}

    # 尝试 ES 搜索建议
    try:
        suggestions = search_service.suggest_courses(prefix=prefix, size=size)
        if suggestions:
            return {"code": 200, "message": "success", "data": suggestions}
    except Exception:
        pass

    # 降级到 MySQL 查询
    from models import Course
    items = db.query(Course).filter(
        Course.status == "published",
        Course.title.contains(prefix),
    ).limit(size).all()
    suggestions = [c.title for c in items]
    return {"code": 200, "message": "success", "data": suggestions}


# ==================== 管理员课程审核（必须在 /{course_id} 之前） ====================

@router.get("/admin/pending", response_model=dict)
def admin_all_courses(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """管理员查看所有课程（支持按状态筛选）"""
    items, total = get_courses(db, skip=skip, limit=limit, status=status)
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "cover_image": c.cover_image,
                "category": c.category,
                "price": float(c.price),
                "status": c.status,
                "reject_reason": c.reject_reason or "",
                "artisan_id": c.artisan_id,
                "artisan_name": c.artisan.shop_name or c.artisan.real_name or "",
                "difficulty": c.difficulty or "",
                "duration_hours": c.duration_hours or 0,
                "lesson_limit": c.lesson_limit or 0,
                "tags": c.tags or [],
                "created_at": str(c.created_at),
            }
            for c in items
        ],
    }


@router.get("/admin/{course_id}/detail", response_model=dict)
def admin_course_detail(
    course_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """管理员查看课程详情（含章节和课时）"""
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    chapters = get_chapters(db, course_id)
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "cover_image": course.cover_image,
        "category": course.category,
        "price": float(course.price),
        "status": course.status,
        "reject_reason": course.reject_reason or "",
        "artisan_id": course.artisan_id,
        "artisan_name": course.artisan.shop_name or course.artisan.real_name or "",
        "difficulty": course.difficulty or "",
        "duration_hours": course.duration_hours or 0,
        "lesson_limit": course.lesson_limit or 0,
        "target_audience": course.target_audience or "",
        "tags": course.tags or [],
        "free_preview_count": course.free_preview_count or 0,
        "craft_intro": course.craft_intro or "",
        "purchase_notice": course.purchase_notice or "",
        "material_type": course.material_type or "none",
        "material_desc": course.material_desc or "",
        "material_price": float(course.material_price or 0),
        "material_shipping": course.material_shipping or "",
        "created_at": str(course.created_at),
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "sort_order": ch.sort_order,
                "lessons": [
                    {
                        "id": le.id,
                        "title": le.title,
                        "description": le.description or "",
                        "video_url": le.video_url,
                        "duration": le.duration or 0,
                        "is_free": le.is_free,
                    }
                    for le in ch.lessons
                ],
            }
            for ch in chapters
        ],
    }


@router.post("/admin/{course_id}/approve")
def admin_approve_course(
    course_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """管理员审核通过课程"""
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    course.status = "published"
    course.reject_reason = ""
    db.commit()
    # 课程发布后同步到 ES，之后可被搜索
    safe_sync_course(db, course_id)
    return {"message": "课程已发布"}


@router.post("/admin/{course_id}/reject")
def admin_reject_course(
    course_id: int,
    reason: str = None,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """管理员驳回课程（需填写驳回原因）"""
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="驳回时必须填写驳回原因")
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    course.status = "rejected"
    course.reject_reason = reason.strip()
    db.commit()
    # 驳回后清理 ES 文档
    safe_delete_course(course_id)
    return {"message": "课程已驳回"}


# ==================== Artisan course management (artisan role required) ====================
# 注意：必须在 /{course_id} 之前定义，否则 "manage" 会被当作 course_id 解析

@router.get("/manage", response_model=dict)
def manage_courses(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    import json
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=404, detail="请先完成匠人认证")
    items, total = get_artisan_courses(db, artisan.id, skip=skip, limit=limit)
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "artisan_id": c.artisan_id,
                "title": c.title,
                "description": c.description or "",
                "cover_image": c.cover_image or "",
                "category": c.category or "",
                "price": float(c.price or 0),
                "status": c.status,
                "reject_reason": c.reject_reason or "",
                "difficulty": c.difficulty or "",
                "duration_hours": c.duration_hours or 0,
                "lesson_limit": c.lesson_limit or 0,
                "tags": _parse_tags(c.tags),
                "created_at": str(c.created_at) if c.created_at else "",
                "artisan_name": artisan.shop_name or artisan.real_name,
                "chapter_count": len(c.chapters),
                "lesson_count": sum(len(ch.lessons) for ch in c.chapters),
                "enrolled_count": sum(1 for e in c.enrollments if e.status == "active"),
            }
            for c in items
        ],
    }


def _parse_tags(raw):
    """解析 MySQL JSON 字段返回的 tags（可能是字符串或列表）"""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


# ==================== Browse History & My Courses ====================
# 注意：必须在 /{course_id} 之前定义，否则会被当作 course_id 解析

@router.post("/browse/{course_id}")
def record_browse_history(
    course_id: int,
    lesson_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录课程浏览历史"""
    record_browse(db, current_user.id, course_id, lesson_id)
    return {"message": "浏览记录已更新"}


@router.get("/browse-history", response_model=dict)
def get_browse_history(
    skip: int = 0,
    limit: int = 20,
    type: str = "course",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户浏览历史（type=product|course）"""
    from models import BrowseHistory

    query = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == current_user.id,
        BrowseHistory.type == type,
    )

    if type == "product":
        query = query.filter(BrowseHistory.product_id.isnot(None))
    else:
        query = query.filter(BrowseHistory.course_id.isnot(None))

    total = query.count()
    items = query.order_by(BrowseHistory.browsed_at.desc()).offset(skip).limit(limit).all()

    result = []
    for h in items:
        data = {
            "id": h.id,
            "type": h.type,
            "browsed_at": str(h.browsed_at) if h.browsed_at else "",
        }
        if h.type == "product" and h.product:
            data["product"] = {
                "id": h.product.id,
                "name": h.product.name,
                "price": float(h.product.price or 0),
                "images": h.product.images or [],
            }
            data["product_id"] = h.product_id
        elif h.course:
            data["course_id"] = h.course_id
            data["lesson_id"] = h.lesson_id
            data["course"] = {
                "id": h.course.id,
                "title": h.course.title,
                "description": h.course.description or "",
                "cover_image": h.course.cover_image or "",
                "category": h.course.category or "",
                "price": float(h.course.price or 0),
            }
            data["lesson"] = {
                "id": h.lesson.id,
                "title": h.lesson.title,
                "video_url": h.lesson.video_url or "",
            } if h.lesson else None
        result.append(data)

    return {"total": total, "items": result}


@router.delete("/browse-history/{history_id}")
def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除单条浏览记录"""
    if not delete_browse_history(db, current_user.id, history_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "已删除"}


@router.delete("/browse-history")
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空全部浏览记录"""
    count = clear_browse_history(db, current_user.id)
    return {"message": f"已清空 {count} 条记录"}


@router.get("/my-courses", response_model=dict)
def get_my_courses(
    skip: int = 0,
    limit: int = 20,
    course_type: str = "all",  # all, free, purchased
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户已加入的课程列表"""
    enrollments, total = get_user_enrollments(db, current_user.id, skip=skip, limit=limit)
    if course_type == "free":
        enrollments = [e for e in enrollments if e.type == "free"]
    elif course_type == "purchased":
        enrollments = [e for e in enrollments if e.type == "purchased"]

    return {
        "total": len(enrollments),
        "items": [
            {
                "id": e.course.id,
                "title": e.course.title,
                "description": e.course.description or "",
                "cover_image": e.course.cover_image or "",
                "category": e.course.category or "",
                "price": float(e.course.price or 0),
                "progress": e.progress,
                "type": e.type,
                "enrolled_at": str(e.enrolled_at) if e.enrolled_at else "",
                "artisan_name": e.course.artisan.shop_name or e.course.artisan.real_name if e.course.artisan else "",
                "lesson_count": sum(len(ch.lessons) for ch in e.course.chapters),
            }
            for e in enrollments if e.course
        ],
    }


# ==================== User enrollment (auth required) ====================
# 注意：必须在 /{course_id} 之前定义，否则 "enrollments" 会被当作 course_id 解析

@router.get("/enrollments", response_model=dict)
def my_enrollments(
    skip: int = 0,
    limit: int = 20,
    type: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = get_user_enrollments(db, current_user.id, skip=skip, limit=limit, enroll_type=type)
    return {
        "total": total,
        "items": [
            EnrollmentResponse(
                id=e.id,
                user_id=e.user_id,
                course_id=e.course_id,
                progress=e.progress,
                type=e.type,
                status=e.status,
                enrolled_at=e.enrolled_at,
                course=CourseResponse(
                    id=e.course.id,
                    artisan_id=e.course.artisan_id,
                    title=e.course.title,
                    description=e.course.description,
                    cover_image=e.course.cover_image,
                    category=e.course.category,
                    price=float(e.course.price),
                    status=e.course.status,
                    created_at=e.course.created_at,
                    artisan_name="",
                    chapter_count=0,
                    lesson_count=0,
                    enrolled_count=0,
                ) if e.course else None,
            )
            for e in items
        ],
    }


# ==================== Comments & Notes ====================
# 注意：必须在 /{course_id} 之前定义，否则 "comments"/"notes" 会被当作 course_id 解析

@router.get("/{course_id}/comments", response_model=dict)
def get_comments(
    course_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """获取课程评论（所有人可看）"""
    items, total = get_course_comments(db, course_id, skip=skip, limit=limit)
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "course_id": c.course_id,
                "user_id": c.user_id,
                "parent_id": c.parent_id,
                "content": c.content,
                "created_at": str(c.created_at) if c.created_at else "",
                "user": {
                    "id": c.user.id,
                    "username": c.user.username,
                    "nickname": c.user.nickname or "",
                    "avatar": c.user.avatar or "",
                } if c.user else None,
            }
            for c in items
        ],
    }


@router.post("/{course_id}/comments")
def create_new_comment(
    course_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布评论或回复（需已报名）"""
    enrollment = get_enrollment(db, current_user.id, course_id)
    if not enrollment:
        raise HTTPException(status_code=403, detail="请先加入或购买课程")
    
    content = data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    
    parent_id = data.get("parent_id")
    comment = create_comment(db, course_id, current_user.id, content, parent_id)

    from models import Notification, Course
    course = db.query(Course).filter(Course.id == course_id).first()

    # 新评论 → 通知课程商家
    if not parent_id and course:
        artisan_user_id = course.artisan.user_id if course.artisan else None
        if artisan_user_id and artisan_user_id != current_user.id:
            notif = Notification(
                user_id=artisan_user_id,
                type="course_comment",
                actor_id=current_user.id,
                title=f"{current_user.nickname or current_user.username} 评论了你的课程",
                content=content[:200],
                link=f"/course/{course_id}/learn",
                course_id=course_id,
                is_read=False,
            )
            db.add(notif)
            db.commit()

    # 如果是回复，给被回复者发送通知
    if parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == parent_id).first()
        if parent_comment and parent_comment.user_id != current_user.id:
            from models import Notification
            notification = Notification(
                user_id=parent_comment.user_id,
                type="comment_reply",
                actor_id=current_user.id,
                title=f"{current_user.nickname or current_user.username} 回复了你的评论",
                content=content[:200],
                link=f"/course/{course_id}/learn",
                course_id=course_id,
                comment_id=comment.id,
                is_read=False,
            )
            db.add(notification)
            db.commit()
    
    return {"message": "评论发布成功", "comment_id": comment.id}



@router.get("/{course_id}/notes", response_model=dict)
def get_notes(
    course_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取个人学习笔记（仅本人可见）"""
    items, total = get_user_notes(db, current_user.id, course_id, skip=skip, limit=limit)
    return {
        "total": total,
        "items": [
            {
                "id": n.id,
                "course_id": n.course_id,
                "lesson_id": n.lesson_id,
                "title": n.title,
                "content": n.content,
                "created_at": str(n.created_at) if n.created_at else "",
                "updated_at": str(n.updated_at) if n.updated_at else "",
            }
            for n in items
        ],
    }


@router.post("/{course_id}/notes")
def create_new_note(
    course_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建学习笔记"""
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    lesson_id = data.get("lesson_id")
    
    if not title:
        raise HTTPException(status_code=400, detail="笔记标题不能为空")
    if not content:
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    
    note = create_note(db, course_id, current_user.id, title, content, lesson_id)
    return {"message": "笔记创建成功", "note_id": note.id}


@router.put("/notes/{note_id}")
def update_user_note(
    note_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新学习笔记"""
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    
    if not title:
        raise HTTPException(status_code=400, detail="笔记标题不能为空")
    if not content:
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    
    note = update_note(db, current_user.id, note_id, title, content)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权修改")
    return {"message": "笔记更新成功"}


@router.delete("/notes/{note_id}")
def delete_user_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除学习笔记"""
    if not delete_note(db, current_user.id, note_id):
        raise HTTPException(status_code=404, detail="笔记不存在或无权删除")
    return {"message": "笔记已删除"}


# ==================== 课程评论通知（必须在 /{course_id} 之前） ====================

@router.get("/notifications")
def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取课程评论通知"""
    from models import Notification, Course
    from sqlalchemy import func
    total = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id
    ).scalar() or 0
    items = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for n in items:
        actor = db.query(User).filter(User.id == n.actor_id).first()
        # 用数据库里已存的 title/content，若为空再动态生成
        title = n.title or ""
        content = n.content or ""
        course_id = n.course_id
        if not title:
            if n.type == "comment_reply":
                title = f"{actor.nickname if actor else '有人'} 回复了你的评论"
            elif n.type == "course_comment":
                course_obj = db.query(Course).filter(Course.id == n.course_id).first() if n.course_id else None
                title = f"{actor.nickname if actor else '有人'} 评论了你的课程「{course_obj.title}」" if course_obj else "你有新的课程评论"
            else:
                title = "你有新的消息"
        result.append({
            "id": n.id,
            "type": n.type,
            "actor_id": n.actor_id,
            "actor_nickname": (actor.nickname or actor.username) if actor else "",
            "actor_avatar": actor.avatar if actor else "",
            "comment_id": n.comment_id,
            "course_id": course_id,
            "title": title,
            "content": content,
            "is_read": n.is_read,
            "created_at": str(n.created_at) if n.created_at else "",
        })
    return {"total": total, "items": result}


@router.get("/notifications/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取未读课程评论通知数"""
    from models import Notification
    from sqlalchemy import func
    count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).scalar() or 0
    return {"count": count}



@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    chapters = get_chapters(db, course_id)
    # 统计评价数（课程暂无独立评价表，暂返回0）
    review_count = 0
    return CourseDetailResponse(
        id=course.id,
        artisan_id=course.artisan_id,
        title=course.title,
        description=course.description,
        cover_image=course.cover_image,
        category=course.category,
        price=float(course.price),
        status=course.status,
        created_at=course.created_at,
        artisan_name=course.artisan.shop_name or course.artisan.real_name or "",
        chapter_count=len(chapters),
        lesson_count=sum(len(ch.lessons) for ch in chapters),
        enrolled_count=len(course.enrollments),
        review_count=review_count,
        difficulty=getattr(course, 'difficulty', '') or '',
        duration_hours=getattr(course, 'duration_hours', 0) or 0,
        target_audience=getattr(course, 'target_audience', '') or '',
        tags=getattr(course, 'tags', []) or [],
        free_preview_count=getattr(course, 'free_preview_count', 0) or 0,
        craft_intro=getattr(course, 'craft_intro', '') or '',
        purchase_notice=getattr(course, 'purchase_notice', '') or '',
        material_type=getattr(course, 'material_type', 'none') or 'none',
        material_desc=getattr(course, 'material_desc', '') or '',
        material_price=float(getattr(course, 'material_price', 0) or 0),
        material_shipping=getattr(course, 'material_shipping', 'express') or 'express',
        material_ship_address=getattr(course, 'material_ship_address', '') or '',
        material_ship_time=getattr(course, 'material_ship_time', '') or '',
        reject_reason=getattr(course, 'reject_reason', '') or '',
        chapters=[
            ChapterResponse(
                id=ch.id,
                course_id=ch.course_id,
                title=ch.title,
                sort_order=ch.sort_order,
                lessons=[
                    LessonResponse.model_validate(ls)
                    for ls in ch.lessons
                ],
            )
            for ch in chapters
        ],
    )


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
def enroll(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """免费课程直接加入，付费课程需先购买后后端自动创建 enrollment"""
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    if course.status != "published":
        raise HTTPException(status_code=400, detail="课程未发布")
    if float(course.price) > 0:
        raise HTTPException(status_code=400, detail="付费课程请先购买")
    enrollment = enroll_course(db, current_user.id, course_id, "free")
    # 报名人数变化，刷新 ES 中的 enrolled_count
    safe_sync_course(db, course_id)
    return EnrollmentResponse.model_validate(enrollment)


@router.post("/{course_id}/drop")
def drop(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """退出免费课程（仅免费课程可退出）"""
    if not drop_course(db, current_user.id, course_id):
        raise HTTPException(status_code=404, detail="未找到可退出的免费课程")
    # 报名人数变化，刷新 ES 中的 enrolled_count
    safe_sync_course(db, course_id)
    return {"message": "已退出课程"}


@router.get("/{course_id}/enrollment", response_model=EnrollmentResponse)
def my_course_enrollment(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollment = get_enrollment(db, current_user.id, course_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="尚未报名")
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/{course_id}/learn")
def learn_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """进入学习（免费课时无需报名也可观看）"""
    enrollment = get_enrollment(db, current_user.id, course_id)
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    # 免费课程 / 已报名 / 有免费试听课 → 允许进入
    is_free_course = float(course.price or 0) == 0
    has_free_lesson = False
    for ch in course.chapters:
        for ls in ch.lessons:
            if ls.is_free:
                has_free_lesson = True
                break
    if not enrollment and not is_free_course and not has_free_lesson:
        raise HTTPException(status_code=403, detail="请先加入或购买课程")

    chapters = get_chapters(db, course_id)
    # 判断是否为课程讲师
    is_owner = False
    from crud.users import get_artisan_by_user_id
    artisan = get_artisan_by_user_id(db, current_user.id)
    if artisan and course.artisan_id == artisan.id:
        is_owner = True

    return {
        "id": course.id,
        "title": course.title,
        "artisan_user_id": course.artisan.user_id if course.artisan else None,
        "progress": enrollment.progress if enrollment else 0,
        "enrolled": enrollment is not None,
        "is_owner": is_owner,
        "free_preview_count": course.free_preview_count or 0,
        "chapters": [
            {
                "id": ch.id, "title": ch.title, "sort_order": ch.sort_order,
                "lessons": [
                    {"id": le.id, "title": le.title, "description": le.description or "",
                     "video_url": le.video_url, "duration": le.duration or 0, "is_free": le.is_free}
                    for le in ch.lessons
                ],
            } for ch in chapters
        ],
    }


@router.post("/{course_id}/progress")
def update_progress(
    course_id: int,
    data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrollment = get_enrollment(db, current_user.id, course_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="请先加入课程")
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    all_lessons = get_lessons(db, course_id)
    total_lessons = len(all_lessons)
    if total_lessons == 0:
        return {"progress": 0, "message": "课程暂无课时"}
    completed_count = int(enrollment.progress * total_lessons / 100)
    if data.completed:
        completed_count = max(completed_count, 1)
    else:
        completed_count = max(completed_count - 1, 0)
    new_progress = int(completed_count * 100 / total_lessons)
    update_enrollment_progress(db, current_user.id, course_id, new_progress)
    return {"progress": new_progress, "message": "进度已更新"}


@router.post("", response_model=CourseResponse)
def create_new_course(
    data: CourseCreate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    artisan = get_artisan_by_user_id(db, current_user.id)
    if not artisan:
        raise HTTPException(status_code=400, detail="请先完成匠人认证")
    course = create_course(db, artisan.id, data)
    return CourseResponse(
        id=course.id,
        artisan_id=course.artisan_id,
        title=course.title,
        description=course.description,
        cover_image=course.cover_image,
        category=course.category,
        price=float(course.price),
        status=course.status,
        created_at=course.created_at,
        lesson_limit=course.lesson_limit or 0,
        artisan_name=artisan.shop_name or artisan.real_name,
    )


@router.put("/{course_id}", response_model=CourseResponse)
def edit_course(
    course_id: int,
    data: CourseUpdate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    artisan = get_artisan_by_user_id(db, current_user.id)
    if course.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权修改此课程")
    course = update_course(db, course, data)
    # 已发布课程编辑后同步 ES，保证搜索展示最新内容
    if course.status == "published":
        safe_sync_course(db, course_id)
    return CourseResponse(
        id=course.id,
        artisan_id=course.artisan_id,
        title=course.title,
        description=course.description,
        cover_image=course.cover_image,
        category=course.category,
        price=float(course.price),
        status=course.status,
        created_at=course.created_at,
        lesson_limit=course.lesson_limit or 0,
        artisan_name=artisan.shop_name or artisan.real_name,
    )


@router.delete("/{course_id}")
def remove_course(
    course_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    artisan = get_artisan_by_user_id(db, current_user.id)
    if course.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权删除此课程")
    delete_course(db, course_id)
    # 删除课程后同步删除 ES 文档
    safe_delete_course(course_id)
    return {"message": "课程已删除"}


# ==================== Chapter management (artisan) ====================

@router.post("/{course_id}/chapters", response_model=ChapterResponse)
def add_chapter(
    course_id: int,
    data: ChapterCreate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    artisan = get_artisan_by_user_id(db, current_user.id)
    if course.artisan_id != artisan.id:
        raise HTTPException(status_code=403, detail="无权操作")
    chapter = create_chapter(db, course_id, data)
    return ChapterResponse(
        id=chapter.id,
        course_id=chapter.course_id,
        title=chapter.title,
        sort_order=chapter.sort_order,
        lessons=[],
    )


@router.put("/{course_id}/chapters/{chapter_id}", response_model=ChapterResponse)
def edit_chapter(
    course_id: int,
    chapter_id: int,
    data: ChapterUpdate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course or course.artisan_id != get_artisan_by_user_id(db, current_user.id).id:
        raise HTTPException(status_code=403, detail="无权操作")
    chapter = get_chapter_by_id(db, chapter_id)
    if not chapter or chapter.course_id != course_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    chapter = update_chapter(db, chapter, title=data.title, sort_order=data.sort_order)
    return ChapterResponse(
        id=chapter.id, course_id=chapter.course_id,
        title=chapter.title, sort_order=chapter.sort_order, lessons=[],
    )


@router.delete("/{course_id}/chapters/{chapter_id}")
def remove_chapter(
    course_id: int,
    chapter_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course or course.artisan_id != get_artisan_by_user_id(db, current_user.id).id:
        raise HTTPException(status_code=403, detail="无权操作")
    if not delete_chapter(db, chapter_id):
        raise HTTPException(status_code=404, detail="章节不存在")
    return {"message": "章节已删除"}




# ==================== Lesson management (artisan) ====================

@router.post("/{course_id}/chapters/{chapter_id}/lessons", response_model=LessonResponse)
def add_lesson(
    course_id: int,
    chapter_id: int,
    data: LessonCreate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course or course.artisan_id != get_artisan_by_user_id(db, current_user.id).id:
        raise HTTPException(status_code=403, detail="无权操作")
    chapter = get_chapter_by_id(db, chapter_id)
    if not chapter or chapter.course_id != course_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    lesson = create_lesson(db, course_id, chapter_id, data)
    return LessonResponse.model_validate(lesson)


@router.put("/{course_id}/lessons/{lesson_id}", response_model=LessonResponse)
def edit_lesson(
    course_id: int,
    lesson_id: int,
    data: LessonUpdate,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course or course.artisan_id != get_artisan_by_user_id(db, current_user.id).id:
        raise HTTPException(status_code=403, detail="无权操作")
    lesson = get_lesson_by_id(db, lesson_id)
    if not lesson or lesson.course_id != course_id:
        raise HTTPException(status_code=404, detail="课时不存在")
    update_data = data.model_dump(exclude_unset=True)
    lesson = update_lesson(db, lesson, **update_data)
    return LessonResponse.model_validate(lesson)


@router.delete("/{course_id}/lessons/{lesson_id}")
def remove_lesson(
    course_id: int,
    lesson_id: int,
    current_user: User = Depends(require_role("artisan")),
    db: Session = Depends(get_db),
):
    course = get_course_by_id(db, course_id)
    if not course or course.artisan_id != get_artisan_by_user_id(db, current_user.id).id:
        raise HTTPException(status_code=403, detail="无权操作")
    if not delete_lesson(db, lesson_id):
        raise HTTPException(status_code=404, detail="课时不存在")
    return {"message": "课时已删除"}

