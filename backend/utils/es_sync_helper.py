"""
ES 数据同步安全辅助模块

业务操作成功后调用，将 MySQL 变更同步到 Elasticsearch。
所有函数统一吞掉异常只记日志 —— ES 故障绝不影响主业务流程。

用法示例（router 层）：
    from utils.es_sync_helper import safe_sync_product
    update_product_status(db, product_id, "approved")
    safe_sync_product(db, product_id)   # 失败仅记日志，不影响接口返回
"""
import logging

from es.es_client import es_client
from es.es_sync import (
    sync_product,
    delete_product_from_es,
    sync_course,
    delete_course_from_es,
    update_product_stock,
    update_product_sales,
)

logger = logging.getLogger(__name__)


def safe_sync_product(db, product_id: int) -> None:
    """同步商品到 ES（新增或更新），失败仅记日志"""
    try:
        ok = sync_product(db, product_id, es_client)
        if ok:
            logger.info("ES 同步商品成功 product_id=%s", product_id)
        else:
            logger.warning("ES 同步商品返回失败 product_id=%s", product_id)
    except Exception as e:
        logger.error("ES 同步商品异常 product_id=%s: %s", product_id, e)


def safe_delete_product(product_id: int) -> None:
    """从 ES 删除商品（不存在时自动忽略 404），失败仅记日志"""
    try:
        delete_product_from_es(product_id, es_client)
        logger.info("ES 删除商品成功 product_id=%s", product_id)
    except Exception as e:
        logger.error("ES 删除商品异常 product_id=%s: %s", product_id, e)


def safe_sync_course(db, course_id: int) -> None:
    """同步课程到 ES（新增或更新），失败仅记日志"""
    try:
        ok = sync_course(db, course_id, es_client)
        if ok:
            logger.info("ES 同步课程成功 course_id=%s", course_id)
        else:
            logger.warning("ES 同步课程返回失败 course_id=%s", course_id)
    except Exception as e:
        logger.error("ES 同步课程异常 course_id=%s: %s", course_id, e)


def safe_delete_course(course_id: int) -> None:
    """从 ES 删除课程（不存在时自动忽略 404），失败仅记日志"""
    try:
        delete_course_from_es(course_id, es_client)
        logger.info("ES 删除课程成功 course_id=%s", course_id)
    except Exception as e:
        logger.error("ES 删除课程异常 course_id=%s: %s", course_id, e)


def safe_update_product_stock(product_id: int, stock: int) -> None:
    """更新 ES 商品库存，失败仅记日志"""
    try:
        update_product_stock(product_id, stock, es_client)
    except Exception as e:
        logger.error("ES 更新商品库存异常 product_id=%s: %s", product_id, e)


def safe_update_product_sales(product_id: int, sales: int) -> None:
    """更新 ES 商品销量，失败仅记日志"""
    try:
        update_product_sales(product_id, sales, es_client)
    except Exception as e:
        logger.error("ES 更新商品销量异常 product_id=%s: %s", product_id, e)
