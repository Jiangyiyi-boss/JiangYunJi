"""给 courses 表添加 reject_reason 字段"""
from database import engine
from sqlalchemy import text, inspect

def migrate():
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('courses')]
        if 'reject_reason' not in columns:
            conn.execute(text("ALTER TABLE courses ADD COLUMN reject_reason VARCHAR(500) DEFAULT ''"))
            conn.commit()
            print("已添加 courses.reject_reason 列")
        else:
            print("courses.reject_reason 列已存在，跳过")

if __name__ == "__main__":
    migrate()
