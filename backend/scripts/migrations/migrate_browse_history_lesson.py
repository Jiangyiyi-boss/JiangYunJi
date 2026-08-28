"""Add lesson_id column to browse_history table."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine

def migrate():
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'browse_history' 
            AND COLUMN_NAME = 'lesson_id'
        """))
        exists = result.scalar() > 0
        
        if exists:
            print("Column lesson_id already exists in browse_history table")
            return
        
        # Add lesson_id column
        conn.execute(text("""
            ALTER TABLE browse_history 
            ADD COLUMN lesson_id INT NULL,
            ADD CONSTRAINT fk_browse_history_lesson 
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE SET NULL
        """))
        conn.commit()
        print("Successfully added lesson_id column to browse_history table")

if __name__ == "__main__":
    migrate()
