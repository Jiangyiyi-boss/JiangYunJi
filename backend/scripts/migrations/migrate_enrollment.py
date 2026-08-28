"""给 enrollments 表添加 type 和 status 字段"""
from database import engine
from sqlalchemy import text, inspect

def migrate():
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('enrollments')]
        if 'type' not in columns:
            conn.execute(text("ALTER TABLE enrollments ADD COLUMN type VARCHAR(10) DEFAULT 'free' NOT NULL"))
            print("已添加 enrollments.type 列")
        if 'status' not in columns:
            conn.execute(text("ALTER TABLE enrollments ADD COLUMN status VARCHAR(10) DEFAULT 'active' NOT NULL"))
            print("已添加 enrollments.status 列")
        conn.commit()
        print("迁移完成")

if __name__ == "__main__":
    migrate()
