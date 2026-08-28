"""
Migration: add goods_type to products and orders,
add course_id to order_items, make product_id nullable.
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
        # Add goods_type to products
        cursor.execute("SHOW COLUMNS FROM products LIKE 'goods_type'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE products ADD COLUMN goods_type INT DEFAULT 1 "
                "COMMENT '商品类型 1=实物 2=线上课程'"
            )
            print("Added products.goods_type")

        # Add goods_type to orders
        cursor.execute("SHOW COLUMNS FROM orders LIKE 'goods_type'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE orders ADD COLUMN goods_type INT DEFAULT 1 "
                "COMMENT '订单类型 1=实物 2=课程'"
            )
            print("Added orders.goods_type")

        # Add course_id to order_items
        cursor.execute("SHOW COLUMNS FROM order_items LIKE 'course_id'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE order_items ADD COLUMN course_id INT NULL"
            )
            print("Added order_items.course_id")

        # Make product_id nullable (allows NULL for course orders)
        cursor.execute(
            "ALTER TABLE order_items MODIFY COLUMN product_id INT NULL"
        )
        print("order_items.product_id set to nullable")

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
