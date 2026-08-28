"""
Migration: add order_id and payment_started_at to enrollments table
for course payment tracking.
"""
import pymysql
from config import settings


def migrate():
    conn = pymysql.connect(
        host=settings.DB_HOST, port=settings.DB_PORT,
        user=settings.DB_USER, password=settings.DB_PASSWORD,
        database=settings.DB_NAME, charset='utf8mb4'
    )
    cursor = conn.cursor()
    try:
        # Add order_id to enrollments
        cursor.execute("SHOW COLUMNS FROM enrollments LIKE 'order_id'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE enrollments ADD COLUMN order_id INT NULL "
                "COMMENT '关联订单ID'"
            )
            print("Added enrollments.order_id")

        # Add payment_started_at to enrollments
        cursor.execute("SHOW COLUMNS FROM enrollments LIKE 'payment_started_at'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE enrollments ADD COLUMN payment_started_at DATETIME NULL "
                "COMMENT '支付开始时间（倒计时用）'"
            )
            print("Added enrollments.payment_started_at")

        conn.commit()
        print("Migration complete!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()