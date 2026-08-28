"""
数据库迁移 - 添加 custom_orders 地址字段和 shipped 状态
运行: python migrate_custom_address.py
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

    for col, col_type in [
        ("receiver_name", "VARCHAR(50) DEFAULT ''"),
        ("receiver_phone", "VARCHAR(20) DEFAULT ''"),
        ("receiver_address", "TEXT"),
    ]:
        try:
            cursor.execute(f"SELECT {col} FROM custom_orders LIMIT 1")
            print(f"[OK] custom_orders.{col} 已存在")
        except Exception:
            cursor.execute(f"ALTER TABLE custom_orders ADD COLUMN {col} {col_type}")
            print(f"[ADD] custom_orders.{col}")

    # 修改 status 枚举以包含 shipped
    try:
        cursor.execute("ALTER TABLE custom_orders MODIFY COLUMN status ENUM('pending','quoted','accepted','in_progress','shipped','completed','rejected','cancelled') DEFAULT 'pending'")
        print("[OK] status 枚举已更新")
    except Exception:
        print("[OK] status 枚举已是最新")

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()