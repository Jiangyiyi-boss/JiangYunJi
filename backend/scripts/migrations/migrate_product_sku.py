"""
Migration: add listing_mode to products, add reviewed to status enum,
add shipping fields (if not exist).
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
        # Add listing_mode to products
        cursor.execute("SHOW COLUMNS FROM products LIKE 'listing_mode'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE products ADD COLUMN listing_mode VARCHAR(10) DEFAULT 'auto' "
                "COMMENT '上架模式: auto=审核通过自动上架, manual=审核通过手动上架'"
            )
            print("Added products.listing_mode")

        # Alter status enum to include 'reviewed'
        cursor.execute("SHOW COLUMNS FROM products LIKE 'status'")
        col = cursor.fetchone()
        if col:
            cursor.execute(
                "ALTER TABLE products MODIFY COLUMN status "
                "ENUM('pending','approved','rejected','offline','reviewed') "
                "DEFAULT 'pending'"
            )
            print("Updated products.status enum (added 'reviewed')")

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