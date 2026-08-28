"""Add lesson_id and chapter_id columns to comments table."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine


def migrate():
    with engine.connect() as conn:
        # Check if lesson_id column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'comments'
            AND COLUMN_NAME = 'lesson_id'
        """))
        lesson_exists = result.scalar() > 0

        # Check if chapter_id column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'comments'
            AND COLUMN_NAME = 'chapter_id'
        """))
        chapter_exists = result.scalar() > 0

        if lesson_exists and chapter_exists:
            print("Columns lesson_id and chapter_id already exist in comments table")
            return

        # Add columns
        if not lesson_exists:
            conn.execute(text("""
                ALTER TABLE comments
                ADD COLUMN lesson_id INT NULL,
                ADD CONSTRAINT fk_comments_lesson
                FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
            """))
            print("Added lesson_id column to comments table")

        if not chapter_exists:
            conn.execute(text("""
                ALTER TABLE comments
                ADD COLUMN chapter_id INT NULL,
                ADD CONSTRAINT fk_comments_chapter
                FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
            """))
            print("Added chapter_id column to comments table")

        conn.commit()
        print("Migration completed successfully")


if __name__ == "__main__":
    migrate()