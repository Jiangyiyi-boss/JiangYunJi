"""给 users 表添加 bio 字段（兼容 SQLite / MySQL）"""
from database import engine
from sqlalchemy import text, inspect

def migrate():
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        if 'bio' not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN bio VARCHAR(200) DEFAULT ''"))
            conn.commit()
            print("已添加 users.bio 列")
        else:
            print("users.bio 列已存在，跳过")

if __name__ == "__main__":
    migrate()
