"""
迁移脚本：为 orders 表添加 shipping_fee 字段
"""
import pymysql
from config import settings

def migrate():
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute("SHOW COLUMNS FROM orders LIKE 'shipping_fee'")
        if not cursor.fetchone():
            print("添加 shipping_fee 字段...")
            cursor.execute("ALTER TABLE orders ADD COLUMN shipping_fee DECIMAL(10,2) DEFAULT 0 COMMENT '运费'")
        
        conn.commit()
        print("迁移完成！")
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
