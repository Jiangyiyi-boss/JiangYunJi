"""
数据库迁移 - 添加 custom_orders.reject_reason
运行: python migrate_custom_reject.py
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
        cursor.execute("SELECT reject_reason FROM custom_orders LIMIT 1")
        print("[OK] custom_orders.reject_reason 已存在")
    except Exception:
        cursor.execute("ALTER TABLE custom_orders ADD COLUMN reject_reason VARCHAR(500) DEFAULT ''")
        print("[ADD] custom_orders.reject_reason")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()