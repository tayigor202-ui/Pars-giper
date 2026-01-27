import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Check prices table structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'prices' 
    ORDER BY ordinal_position
""")
prices_cols = cur.fetchall()

# Check wb_prices table structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'wb_prices' 
    ORDER BY ordinal_position
""")
wb_prices_cols = cur.fetchall()

print('\n=== СТРУКТУРА ТАБЛИЦЫ PRICES (OZON) ===')
for col, dtype in prices_cols:
    print(f'  {col}: {dtype}')

print('\n=== СТРУКТУРА ТАБЛИЦЫ WB_PRICES (WILDBERRIES) ===')
for col, dtype in wb_prices_cols:
    print(f'  {col}: {dtype}')

cur.close()
conn.close()
