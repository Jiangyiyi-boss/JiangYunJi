"""Migration: add notification fields for course comments."""
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
        # Add title column
        cursor.execute("SHOW COLUMNS FROM notifications LIKE 'title'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN title VARCHAR(200) DEFAULT '' "
                "COMMENT '通知标题'"
            )
            print("Added notifications.title")

        # Add content column
        cursor.execute("SHOW COLUMNS FROM notifications LIKE 'content'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN content TEXT "
                "COMMENT '通知内容'"
            )
            print("Added notifications.content")

        # Add link column
        cursor.execute("SHOW COLUMNS FROM notifications LIKE 'link'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN link VARCHAR(500) DEFAULT '' "
                "COMMENT '跳转链接'"
            )
            print("Added notifications.link")

        # Add course_id column
        cursor.execute("SHOW COLUMNS FROM notifications LIKE 'course_id'")
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE notifications ADD COLUMN course_id INT NULL"
            )
            print("Added notifications.course_id")

        # Update the enum type to include new notification types
        cursor.execute(
            "ALTER TABLE notifications MODIFY COLUMN type "
            "ENUM('like','comment','favorite','follow','comment_reply','course_comment') "
            "NOT NULL"
        )
        print("Updated notifications.type enum")

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
