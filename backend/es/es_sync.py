"""
Elasticsearch 数据同步
"""
import logging
from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session
from config import settings
from models import Product, Course, Artisan, Category, Chapter, Lesson, Enrollment

logger = logging.getLogger(__name__)

PRODUCT_INDEX = settings.ES_INDEX
COURSE_INDEX = settings.ES_COURSE_INDEX


def _product_to_doc(product: Product) -> dict:
    """将 Product 模型转换为 ES 文档"""
    category_name = ""
    if product.category:
        category_name = product.category.name

    artisan_name = ""
    artisan_id = None
    if product.artisan:
        artisan_name = product.artisan.shop_name or ""
        artisan_id = product.artisan.id

    return {
        "id": product.id,
        "name": product.name or "",
        "description": product.description or "",
        "price": float(product.price) if product.price else 0.0,
        "original_price": float(product.original_price) if product.original_price else None,
        "stock": product.stock or 0,
        "sales": product.sales or 0,
        "category": category_name,
        "brand": artisan_name,
        "images": product.images or [],
        "status": product.status or "pending",
        "artisan_id": artisan_id,
        "artisan_name": artisan_name,
        "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S") if product.created_at else None,
    }


def _course_to_doc(course: Course) -> dict:
    """将 Course 模型转换为 ES 文档"""
    artisan_name = ""
    artisan_id = None
    if course.artisan:
        artisan_name = course.artisan.shop_name or course.artisan.real_name or ""
        artisan_id = course.artisan.id

    # 统计课时数
    lesson_count = 0
    for chapter in course.chapters:
        lesson_count += len(chapter.lessons)

    # 统计报名人数（只统计 active 报名：未支付/已取消/已退出的不计入）
    enrolled_count = sum(1 for e in course.enrollments if e.status == "active")

    # 判断是否免费
    is_free = float(course.price or 0) == 0

    return {
        "id": course.id,
        "title": course.title or "",
        "description": course.description or "",
        "craft_intro": course.craft_intro or "",
        "price": float(course.price or 0),
        "category": course.category or "",
        "difficulty": course.difficulty or "",
        "tags": course.tags or [],
        "status": course.status or "pending",
        "artisan_id": artisan_id,
        "artisan_name": artisan_name,
        "enrolled_count": enrolled_count,
        "lesson_count": lesson_count,
        "is_free": is_free,
        "cover_image": course.cover_image or "",
        "created_at": course.created_at.strftime("%Y-%m-%d %H:%M:%S") if course.created_at else None,
    }


def sync_product(db: Session, product_id: int, es: Elasticsearch) -> bool:
    """同步单个商品到 ES"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"商品 {product_id} 不存在")
            return False

        doc = _product_to_doc(product)
        es.index(index=PRODUCT_INDEX, id=str(product_id), document=doc)
        logger.info(f"商品 {product_id} 同步成功")
        return True
    except Exception as e:
        logger.error(f"同步商品 {product_id} 失败: {e}")
        return False


def sync_course(db: Session, course_id: int, es: Elasticsearch) -> bool:
    """同步单个课程到 ES"""
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            logger.warning(f"课程 {course_id} 不存在")
            return False

        doc = _course_to_doc(course)
        es.index(index=COURSE_INDEX, id=str(course_id), document=doc)
        logger.info(f"课程 {course_id} 同步成功")
        return True
    except Exception as e:
        logger.error(f"同步课程 {course_id} 失败: {e}")
        return False


def sync_all_products(db: Session, es: Elasticsearch) -> int:
    """全量同步所有已审核商品到 ES"""
    products = db.query(Product).filter(Product.status == "approved").all()
    count = 0
    for product in products:
        if sync_product(db, product.id, es):
            count += 1
    logger.info(f"全量同步完成，共同步 {count} 个商品")
    return count


def sync_all_courses(db: Session, es: Elasticsearch) -> int:
    """全量同步所有已发布课程到 ES"""
    courses = db.query(Course).filter(Course.status == "published").all()
    count = 0
    for course in courses:
        if sync_course(db, course.id, es):
            count += 1
    logger.info(f"全量同步完成，共同步 {count} 个课程")
    return count


def delete_product_from_es(product_id: int, es: Elasticsearch) -> bool:
    """从 ES 中删除商品"""
    try:
        es.delete(index=PRODUCT_INDEX, id=str(product_id), ignore=[404])
        logger.info(f"商品 {product_id} 已从 ES 删除")
        return True
    except Exception as e:
        logger.error(f"删除商品 {product_id} 失败: {e}")
        return False


def delete_course_from_es(course_id: int, es: Elasticsearch) -> bool:
    """从 ES 中删除课程"""
    try:
        es.delete(index=COURSE_INDEX, id=str(course_id), ignore=[404])
        logger.info(f"课程 {course_id} 已从 ES 删除")
        return True
    except Exception as e:
        logger.error(f"删除课程 {course_id} 失败: {e}")
        return False


def update_product_stock(product_id: int, stock: int, es: Elasticsearch) -> bool:
    """更新商品库存"""
    try:
        es.update(index=PRODUCT_INDEX, id=str(product_id), body={"doc": {"stock": stock}})
        return True
    except Exception as e:
        logger.error(f"更新商品 {product_id} 库存失败: {e}")
        return False


def update_product_sales(product_id: int, sales: int, es: Elasticsearch) -> bool:
    """更新商品销量"""
    try:
        es.update(index=PRODUCT_INDEX, id=str(product_id), body={"doc": {"sales": sales}})
        return True
    except Exception as e:
        logger.error(f"更新商品 {product_id} 销量失败: {e}")
        return False


def update_product_status(product_id: int, status: str, es: Elasticsearch) -> bool:
    """更新商品状态"""
    try:
        es.update(index=PRODUCT_INDEX, id=str(product_id), body={"doc": {"status": status}})
        return True
    except Exception as e:
        logger.error(f"更新商品 {product_id} 状态失败: {e}")
        return False


def update_course_status(course_id: int, status: str, es: Elasticsearch) -> bool:
    """更新课程状态"""
    try:
        es.update(index=COURSE_INDEX, id=str(course_id), body={"doc": {"status": status}})
        return True
    except Exception as e:
        logger.error(f"更新课程 {course_id} 状态失败: {e}")
        return False
