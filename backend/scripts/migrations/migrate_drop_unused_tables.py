"""
数据库迁移脚本 - 删除未使用的表和字段
运行: python scripts/migrations/migrate_drop_unused_tables.py
"""
import pymysql
import sys
import os

# 将后端根目录加入 sys.path，使容器内运行 scripts/ 下脚本时能 import config
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_root)
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

    def ok(msg):
        print(f"[OK] {msg}")

    def drop(msg):
        print(f"[DROP] {msg}")

    # 删除未使用的表（先子表后父表，避免外键约束失败）
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    unused_tables = [
        "ad_slot_applications",
        "experience_bookings",
        "experiences",
        "withdrawals",
    ]
    for table in unused_tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        drop(f"{table} 表")

    # 删除 artisans.level 字段
    try:
        cursor.execute("ALTER TABLE artisans DROP COLUMN level")
        drop("artisans.level 字段")
    except Exception:
        ok("artisans.level 字段不存在或已删除")

    conn.commit()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.close()
    conn.close()
    print("\nDrop unused tables/columns complete!")


if __name__ == "__main__":
    migrate()
