"""
数据库迁移脚本 - 添加 custom_orders 支付字段
运行: python migrate_custom_pay.py
"""
import pymysql
import sys
sys.stdout.reconfigure(encoding='utf-8')
from config import settings


def migrate():
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
    )
    cursor = conn.cursor()

    # 检查并添加 custom_orders.order_no
    try:
        cursor.execute("SELECT order_no FROM custom_orders LIMIT 1")
        print("[OK] custom_orders.order_no 已存在")
    except Exception:
        cursor.execute("ALTER TABLE custom_orders ADD COLUMN order_no VARCHAR(64) NULL UNIQUE")
        print("[ADD] custom_orders.order_no")

    # 检查并添加 custom_orders.pay_status
    try:
        cursor.execute("SELECT pay_status FROM custom_orders LIMIT 1")
        print("[OK] custom_orders.pay_status 已存在")
    except Exception:
        cursor.execute("ALTER TABLE custom_orders ADD COLUMN pay_status ENUM('unpaid','paid') DEFAULT 'unpaid'")
        print("[ADD] custom_orders.pay_status")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()