"""
RabbitMQ 消费者 - 处理过期未支付的订单（商品/课程/定制/广告位）
单独运行: python consumer.py
"""
import json
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from rabbitmq import consume, setup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def callback(ch, method, properties, body):
    data = json.loads(body)
    order_id = data.get("order_id")
    order_type = data.get("order_type", "product")

    db = SessionLocal()
    try:
        if order_type == "product":
            from crud.orders import cancel_order
            from models import Order, Product
            from utils.es_sync_helper import safe_update_product_stock, safe_update_product_sales

            cancel_order(db, order_id)
            # 库存已恢复，同步 ES 中商品库存与销量，避免搜索页库存显示过期
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                for item in order.items:
                    if not item.product_id:
                        continue
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    if product:
                        safe_update_product_stock(item.product_id, product.stock or 0)
                        safe_update_product_sales(item.product_id, product.sales or 0)
            logger.info(f"[CANCELLED] 商品订单 {order_id} 超时未支付，已自动取消（库存已恢复）")

        elif order_type == "course":
            from crud.orders import cancel_course_order
            from models import Order
            from utils.es_sync_helper import safe_sync_course

            cancel_course_order(db, order_id)
            # 报名已失效，同步 ES 中的报名人数
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                for item in order.items:
                    if item.course_id:
                        safe_sync_course(db, item.course_id)
            logger.info(f"[CANCELLED] 课程订单 {order_id} 超时未支付，已自动取消（报名已失效）")

        elif order_type == "custom":
            # 定制订单超时后不自动取消，保留 accepted 状态供用户选择重新支付或主动取消
            logger.info(f"[TIMEOUT] 定制订单 {order_id} 支付超时，未自动取消，等待用户操作")

        else:
            logger.warning(f"[UNKNOWN] 未知订单类型: {order_type}, order_id={order_id}")

    except ValueError as e:
        # 订单状态已变更（已支付或已取消），跳过
        logger.info(f"[SKIP] 订单 {order_id} ({order_type}): {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] 订单 {order_id} ({order_type}): {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    setup()
    logger.info("消费者已启动，等待过期订单...")
    consume(callback)