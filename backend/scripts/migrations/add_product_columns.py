from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE products ADD COLUMN sku VARCHAR(100) DEFAULT ""'))
    conn.execute(text('ALTER TABLE products ADD COLUMN limit_per_user INT DEFAULT 0'))
    conn.execute(text('ALTER TABLE products ADD COLUMN shipping_type ENUM("free", "fixed") DEFAULT "free"'))
    conn.execute(text('ALTER TABLE products ADD COLUMN shipping_fee DECIMAL(10,2) DEFAULT 0'))
    conn.execute(text('ALTER TABLE products ADD COLUMN ship_address VARCHAR(200) DEFAULT ""'))
    conn.execute(text('ALTER TABLE products ADD COLUMN ship_time ENUM("48h", "7days") DEFAULT "48h"'))
    conn.execute(text('ALTER TABLE products ADD COLUMN specs JSON DEFAULT NULL'))
    conn.commit()

print('Database columns added successfully')
