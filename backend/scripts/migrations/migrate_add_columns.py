"""
数据库迁移脚本 - 添加缺失的字段和新表
运行: python migrate_add_columns.py
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

    def ok(msg):
        print(f"[OK] {msg}")

    def add(msg):
        print(f"[ADD] {msg}")

    # 检查并添加 orders.commission_amount
    try:
        cursor.execute("SELECT commission_amount FROM orders LIMIT 1")
        ok("orders.commission_amount 已存在")
    except Exception:
        cursor.execute("ALTER TABLE orders ADD COLUMN commission_amount DECIMAL(10,2) DEFAULT 0")
        add("orders.commission_amount")

    # 检查并添加 order_items.commission_rate
    try:
        cursor.execute("SELECT commission_rate FROM order_items LIMIT 1")
        ok("order_items.commission_rate 已存在")
    except Exception:
        cursor.execute("ALTER TABLE order_items ADD COLUMN commission_rate DECIMAL(5,4) DEFAULT 0.1000")
        add("order_items.commission_rate")

    # 检查并添加 order_items.commission_amount
    try:
        cursor.execute("SELECT commission_amount FROM order_items LIMIT 1")
        ok("order_items.commission_amount 已存在")
    except Exception:
        cursor.execute("ALTER TABLE order_items ADD COLUMN commission_amount DECIMAL(10,2) DEFAULT 0")
        add("order_items.commission_amount")

    # 检查并添加 order_items.artisan_income
    try:
        cursor.execute("SELECT artisan_income FROM order_items LIMIT 1")
        ok("order_items.artisan_income 已存在")
    except Exception:
        cursor.execute("ALTER TABLE order_items ADD COLUMN artisan_income DECIMAL(10,2) DEFAULT 0")
        add("order_items.artisan_income")

    # 检查并添加 products.commission_rate
    try:
        cursor.execute("SELECT commission_rate FROM products LIMIT 1")
        ok("products.commission_rate 已存在")
    except Exception:
        cursor.execute("ALTER TABLE products ADD COLUMN commission_rate DECIMAL(5,4) DEFAULT 0.1000")
        add("products.commission_rate")

    # 检查并添加 products.reject_reason
    try:
        cursor.execute("SELECT reject_reason FROM products LIMIT 1")
        ok("products.reject_reason 已存在")
    except Exception:
        cursor.execute("ALTER TABLE products ADD COLUMN reject_reason TEXT DEFAULT ''")
        add("products.reject_reason")

    # 创建 commission_rates 表
    try:
        cursor.execute("SELECT id FROM commission_rates LIMIT 1")
        ok("commission_rates 表已存在")
    except Exception:
        cursor.execute("""
            CREATE TABLE commission_rates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT NULL,
                rate DECIMAL(5,4) NOT NULL,
                remark VARCHAR(200) DEFAULT '',
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        add("commission_rates 表")

    # 创建 commission_appeals 表
    try:
        cursor.execute("SELECT id FROM commission_appeals LIMIT 1")
        ok("commission_appeals 表已存在")
    except Exception:
        cursor.execute("""
            CREATE TABLE commission_appeals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                artisan_id INT NOT NULL,
                product_id INT NULL,
                order_id INT NULL,
                reason TEXT NOT NULL,
                status ENUM('pending','approved','rejected') DEFAULT 'pending',
                admin_note TEXT DEFAULT '',
                created_at DATETIME DEFAULT NOW(),
                processed_at DATETIME NULL,
                FOREIGN KEY (artisan_id) REFERENCES artisans(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        add("commission_appeals 表")

    # 为 commission_appeals 添加 product_id 列（兼容旧表）
    try:
        cursor.execute("SELECT product_id FROM commission_appeals LIMIT 1")
        ok("product_id 列已存在")
    except Exception:
        cursor.execute("ALTER TABLE commission_appeals ADD COLUMN product_id INT NULL AFTER artisan_id")
        cursor.execute("ALTER TABLE commission_appeals ADD CONSTRAINT fk_appeal_product FOREIGN KEY (product_id) REFERENCES products(id)")
        add("commission_appeals.product_id 列")

    # 为 commission_appeals 的 order_id 改为可空
    try:
        cursor.execute("ALTER TABLE commission_appeals MODIFY COLUMN order_id INT NULL")
        ok("order_id 已改为可空")
    except Exception:
        pass

    # 创建 banners 表
    try:
        cursor.execute("SELECT id FROM banners LIMIT 1")
        ok("banners 表已存在")
    except Exception:
        cursor.execute("""
            CREATE TABLE banners (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) DEFAULT '',
                image_url VARCHAR(500) NOT NULL,
                link_url VARCHAR(500) DEFAULT '',
                source_type ENUM('platform_activity','merchant_promo','platform_pick') DEFAULT 'platform_activity',
                sort INT DEFAULT 0,
                enabled BOOLEAN DEFAULT TRUE,
                start_date DATETIME NULL,
                end_date DATETIME NULL,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        add("banners 表")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
