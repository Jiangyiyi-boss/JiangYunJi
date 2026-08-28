"""为 courses 表添加新字段（修复 TEXT/JSON 默认值问题）"""
from sqlalchemy import text
from database import engine

conn = engine.connect()

# 先添加不带默认值的列
columns_no_default = [
    "tags", "craft_intro", "purchase_notice", "material_desc", "reject_reason"
]

for col_name in columns_no_default:
    try:
        conn.execute(text(f"ALTER TABLE courses ADD COLUMN {col_name} TEXT"))
        conn.commit()
        print(f"已添加列: {col_name}")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print(f"列已存在: {col_name}")
        else:
            print(f"添加列失败 {col_name}: {e}")

# 更新现有数据为默认值
try:
    conn.execute(text("UPDATE courses SET tags = '[]' WHERE tags IS NULL"))
    conn.execute(text("UPDATE courses SET craft_intro = '' WHERE craft_intro IS NULL"))
    conn.execute(text("UPDATE courses SET purchase_notice = '' WHERE purchase_notice IS NULL"))
    conn.execute(text("UPDATE courses SET material_desc = '' WHERE material_desc IS NULL"))
    conn.execute(text("UPDATE courses SET reject_reason = '' WHERE reject_reason IS NULL"))
    conn.commit()
    print("已更新现有数据默认值")
except Exception as e:
    print(f"更新默认值失败: {e}")

conn.close()
print("迁移完成")
