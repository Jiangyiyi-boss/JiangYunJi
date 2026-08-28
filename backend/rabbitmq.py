"""
RabbitMQ 延时支付死信队列
"""
import json
import pika
from config import settings

EXCHANGE = "payment.exchange"
QUEUE_DELAY = "payment.delay"
QUEUE_PROCESS = "payment.process"
DLX_EXCHANGE = "payment.dlx"


def get_connection():
    """创建 RabbitMQ 连接（使用 config.py 配置）"""
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
    )
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=credentials,
        )
    )


def setup():
    """初始化队列和交换机（仅首次运行需要）"""
    conn = get_connection()
    ch = conn.channel()

    ttl_ms = settings.RABBITMQ_PAYMENT_TTL_MS

    # 死信交换机
    ch.exchange_declare(exchange=DLX_EXCHANGE, exchange_type="direct")

    # 延时队列：消息过期后自动转发到死信交换机
    ch.queue_declare(
        queue=QUEUE_DELAY,
        arguments={
            "x-message-ttl": ttl_ms,
            "x-dead-letter-exchange": DLX_EXCHANGE,
            "x-dead-letter-routing-key": QUEUE_PROCESS,
        },
    )

    # 处理队列：绑定到死信交换机
    ch.queue_declare(queue=QUEUE_PROCESS)
    ch.queue_bind(
        queue=QUEUE_PROCESS,
        exchange=DLX_EXCHANGE,
        routing_key=QUEUE_PROCESS,
    )

    conn.close()


def publish_delay(order_id: int, order_type: str = "product"):
    """发布延时消息

    Args:
        order_id: 订单 ID
        order_type: 订单类型 - "product" | "course" | "custom"
    """
    conn = get_connection()
    ch = conn.channel()
    ch.basic_publish(
        exchange="",
        routing_key=QUEUE_DELAY,
        body=json.dumps({"order_id": order_id, "order_type": order_type}),
    )
    conn.close()


def consume(callback):
    """消费到期订单消息"""
    conn = get_connection()
    ch = conn.channel()
    ch.basic_consume(
        queue=QUEUE_PROCESS,
        on_message_callback=callback,
        auto_ack=True,
    )
    ch.start_consuming()