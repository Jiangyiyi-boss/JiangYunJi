"""CRUD operations for online education (courses, chapters, lessons, enrollments)."""
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from models import Course, Chapter, Lesson, Enrollment, BrowseHistory, Comment, StudyNote
from schemas import CourseCreate, CourseUpdate, ChapterCreate, LessonCreate


# ==================== Course ====================

def create_course(db: Session, artisan_id: int, data: CourseCreate) -> Course:
    # 付费课程默认购买须知
    default_notice = ""
    if data.price and float(data.price) > 0:
        default_notice = "1、本课程为付费内容，购买后永久观看\n2、支付完成后自动开通学习权限\n3、一经购买不退不换"

    course = Course(
        artisan_id=artisan_id,
        title=data.title,
        description=data.description,
        cover_image=data.cover_image,
        category=data.category,
        price=data.price,
        purchase_notice=data.purchase_notice or default_notice,
        difficulty=data.difficulty,
        duration_hours=data.duration_hours,
        lesson_limit=data.lesson_limit,
        target_audience=data.target_audience,
        tags=data.tags,
        craft_intro=data.craft_intro,
        free_preview_count=data.free_preview_count,
        status="pending",
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def get_course_by_id(db: Session, course_id: int) -> Optional[Course]:
    return db.query(Course).filter(Course.id == course_id).first()


def get_courses(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category: str = None,
    artisan_id: int = None,
    status: str = "published",
    keyword: str = None,
    price_type: str = None,
    difficulty: str = None,
    is_free: bool = None,
    price_min: float = None,
    price_max: float = None,
) -> Tuple[List[Course], int]:
    query = db.query(Course)
    if status:
        query = query.filter(Course.status == status)
    if category:
        query = query.filter(Course.category == category)
    if artisan_id:
        query = query.filter(Course.artisan_id == artisan_id)
    if keyword:
        query = query.filter(Course.title.contains(keyword))
    if difficulty:
        query = query.filter(Course.difficulty == difficulty)
    if is_free is True:
        query = query.filter(Course.price == 0)
    elif is_free is False:
        query = query.filter(Course.price > 0)
    elif price_type == "free":
        query = query.filter(Course.price == 0)
    elif price_type == "paid":
        query = query.filter(Course.price > 0)
    if price_min is not None:
        query = query.filter(Course.price >= price_min)
    if price_max is not None:
        query = query.filter(Course.price <= price_max)
    total = query.count()
    items = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_artisan_courses(
    db: Session, artisan_id: int, skip: int = 0, limit: int = 20
) -> Tuple[List[Course], int]:
    query = db.query(Course).filter(Course.artisan_id == artisan_id)
    total = query.count()
    items = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.cover_image is not None:
        course.cover_image = data.cover_image
    if data.category is not None:
        course.category = data.category
    if data.price is not None:
        course.price = data.price
    if data.status is not None:
        if data.status == "published" and course.status != "published":
            course.status = "pending"
        else:
            course.status = data.status
    if data.difficulty is not None:
        course.difficulty = data.difficulty
    if data.duration_hours is not None:
        course.duration_hours = data.duration_hours
    if data.lesson_limit is not None:
        course.lesson_limit = data.lesson_limit
    if data.target_audience is not None:
        course.target_audience = data.target_audience
    if data.tags is not None:
        course.tags = data.tags
    if data.craft_intro is not None:
        course.craft_intro = data.craft_intro
    if data.free_preview_count is not None:
        course.free_preview_count = data.free_preview_count
    if data.purchase_notice is not None:
        course.purchase_notice = data.purchase_notice
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: int) -> bool:
    course = get_course_by_id(db, course_id)
    if not course:
        return False
    db.delete(course)
    db.commit()
    return True


# ==================== Chapter ====================

def create_chapter(db: Session, course_id: int, data: ChapterCreate) -> Chapter:
    chapter = Chapter(course_id=course_id, title=data.title, sort_order=data.sort_order)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def get_chapter_by_id(db: Session, chapter_id: int) -> Optional[Chapter]:
    return db.query(Chapter).filter(Chapter.id == chapter_id).first()


def get_chapters(db: Session, course_id: int) -> List[Chapter]:
    return db.query(Chapter).filter(
        Chapter.course_id == course_id
    ).order_by(Chapter.sort_order).all()


def update_chapter(db: Session, chapter: Chapter, title: str = None, sort_order: int = None) -> Chapter:
    if title is not None:
        chapter.title = title
    if sort_order is not None:
        chapter.sort_order = sort_order
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, chapter_id: int) -> bool:
    chapter = get_chapter_by_id(db, chapter_id)
    if not chapter:
        return False
    db.delete(chapter)
    db.commit()
    return True


def reorder_chapters(db: Session, course_id: int, chapter_ids: List[int]):
    for idx, chapter_id in enumerate(chapter_ids):
        chapter = get_chapter_by_id(db, chapter_id)
        if chapter and chapter.course_id == course_id:
            chapter.sort_order = idx
    db.commit()


# ==================== Lesson ====================

def create_lesson(db: Session, course_id: int, chapter_id: int, data: LessonCreate) -> Lesson:
    lesson = Lesson(
        course_id=course_id,
        chapter_id=chapter_id,
        title=data.title,
        description=data.description,
        video_url=data.video_url,
        duration=data.duration,
        sort_order=data.sort_order,
        is_free=data.is_free,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def get_lesson_by_id(db: Session, lesson_id: int) -> Optional[Lesson]:
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def get_lessons(db: Session, course_id: int, chapter_id: int = None) -> List[Lesson]:
    query = db.query(Lesson).filter(Lesson.course_id == course_id)
    if chapter_id is not None:
        query = query.filter(Lesson.chapter_id == chapter_id)
    return query.order_by(Lesson.sort_order).all()


def update_lesson(db: Session, lesson: Lesson, **kwargs) -> Lesson:
    for key, value in kwargs.items():
        if value is not None and hasattr(lesson, key):
            setattr(lesson, key, value)
    db.commit()
    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, lesson_id: int) -> bool:
    lesson = get_lesson_by_id(db, lesson_id)
    if not lesson:
        return False
    db.delete(lesson)
    db.commit()
    return True


# ==================== Enrollment ====================

def enroll_course(db: Session, user_id: int, course_id: int, enroll_type: str = "free") -> Enrollment:
    """加入课程（免费加入或购买后创建）"""
    existing = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
    ).first()
    if existing:
        # 如果之前退出了免费课程，重新激活
        if existing.status == "inactive" and existing.type == "free":
            existing.status = "active"
            existing.enrolled_at = datetime.now()
            db.commit()
            db.refresh(existing)
        return existing
    enrollment = Enrollment(
        user_id=user_id, course_id=course_id, type=enroll_type, status="active"
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_enrollment(db: Session, user_id: int, course_id: int) -> Optional[Enrollment]:
    return db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
        Enrollment.status == "active",
    ).first()


def get_user_enrollments(
    db: Session, user_id: int, skip: int = 0, limit: int = 20, enroll_type: str = None,
) -> Tuple[List[Enrollment], int]:
    query = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "active",
    )
    if enroll_type:
        query = query.filter(Enrollment.type == enroll_type)
    total = query.count()
    items = query.order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit).all()
    return items, total


def drop_course(db: Session, user_id: int, course_id: int) -> bool:
    """退出免费课程（仅免费课程可退出）"""
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
        Enrollment.type == "free",
        Enrollment.status == "active",
    ).first()
    if enrollment:
        enrollment.status = "inactive"
        db.commit()
        return True
    return False


def update_enrollment_progress(db: Session, user_id: int, course_id: int, progress: int) -> Enrollment:
    enrollment = get_enrollment(db, user_id, course_id)
    if enrollment:
        enrollment.progress = min(max(progress, 0), 100)
        db.commit()
        db.refresh(enrollment)
    return enrollment


# ==================== Browse History ====================

def record_browse(db: Session, user_id: int, course_id: int, lesson_id: int = None) -> BrowseHistory:
    """记录浏览历史（如果已存在则更新浏览时间）"""
    existing = db.query(BrowseHistory).filter(
        BrowseHistory.user_id == user_id,
        BrowseHistory.course_id == course_id,
    ).first()
    if existing:
        existing.browsed_at = datetime.now()
        if lesson_id:
            existing.lesson_id = lesson_id
        db.commit()
        db.refresh(existing)
        return existing
    history = BrowseHistory(user_id=user_id, course_id=course_id, lesson_id=lesson_id)
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_user_browse_history(
    db: Session, user_id: int, skip: int = 0, limit: int = 20,
) -> Tuple[List[BrowseHistory], int]:
    query = db.query(BrowseHistory).filter(BrowseHistory.user_id == user_id)
    total = query.count()
    items = query.order_by(BrowseHistory.browsed_at.desc()).offset(skip).limit(limit).all()
    return items, total


def delete_browse_history(db: Session, user_id: int, history_id: int) -> bool:
    history = db.query(BrowseHistory).filter(
        BrowseHistory.id == history_id,
        BrowseHistory.user_id == user_id,
    ).first()
    if history:
        db.delete(history)
        db.commit()
        return True
    return False


def clear_browse_history(db: Session, user_id: int) -> int:
    count = db.query(BrowseHistory).filter(BrowseHistory.user_id == user_id).delete()
    db.commit()
    return count


# ==================== Comments ====================

def create_comment(db: Session, course_id: int, user_id: int, content: str, parent_id: int = None) -> Comment:
    comment = Comment(course_id=course_id, user_id=user_id, content=content, parent_id=parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_course_comments(db: Session, course_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[Comment], int]:
    # Get ALL comments for the course
    query = db.query(Comment).filter(Comment.course_id == course_id)
    total = query.count()
    comments = query.order_by(Comment.created_at.asc()).offset(skip).limit(limit).all()
    
    return comments, total


def delete_comment(db: Session, user_id: int, comment_id: int) -> bool:
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.user_id == user_id
    ).first()
    if comment:
        db.delete(comment)
        db.commit()
        return True
    return False


# ==================== Study Notes ====================

def create_note(db: Session, course_id: int, user_id: int, title: str, content: str, lesson_id: int = None) -> StudyNote:
    note = StudyNote(course_id=course_id, user_id=user_id, title=title, content=content, lesson_id=lesson_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, user_id: int, note_id: int, title: str, content: str) -> StudyNote:
    note = db.query(StudyNote).filter(
        StudyNote.id == note_id,
        StudyNote.user_id == user_id
    ).first()
    if note:
        note.title = title
        note.content = content
        db.commit()
        db.refresh(note)
    return note


def get_user_notes(db: Session, user_id: int, course_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[StudyNote], int]:
    query = db.query(StudyNote).filter(
        StudyNote.user_id == user_id,
        StudyNote.course_id == course_id
    )
    total = query.count()
    items = query.order_by(StudyNote.updated_at.desc()).offset(skip).limit(limit).all()
    return items, total


def delete_note(db: Session, user_id: int, note_id: int) -> bool:
    note = db.query(StudyNote).filter(
        StudyNote.id == note_id,
        StudyNote.user_id == user_id
    ).first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False
