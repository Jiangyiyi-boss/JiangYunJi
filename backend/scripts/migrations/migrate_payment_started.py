"""
数据库迁移 - 添加 custom_orders.payment_started_at
运行: python migrate_payment_started.py
"""
import pymysql
import sys
sys.stdout.reconfigure(encoding='utf-8')
from config import settings


def migrate():
    conn = pymysql.connect(
        host=settings.DB_HOST, port=settings.DB_PORT,
        user=settings.DB_USER, password=settings.DB_PASSWORD,
        database=settings.DB_NAME, charset='utf8mb4',
    )
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT payment_started_at FROM custom_orders LIMIT 1")
        print("[OK] custom_orders.payment_started_at 已存在")
    except Exception:
        cursor.execute("ALTER TABLE custom_orders ADD COLUMN payment_started_at DATETIME NULL")
        print("[ADD] custom_orders.payment_started_at")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()