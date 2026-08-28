from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE cart_items ADD COLUMN spec_name VARCHAR(100) DEFAULT ""'))
    conn.execute(text('ALTER TABLE cart_items ADD COLUMN spec_price DECIMAL(10,2) DEFAULT NULL'))
    conn.execute(text('ALTER TABLE cart_items ADD COLUMN spec_sku VARCHAR(100) DEFAULT ""'))
    conn.commit()

print('Cart item spec columns added successfully')
