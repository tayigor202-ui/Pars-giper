import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

cur = conn.cursor()
cur.execute("SELECT sku, name FROM public.wb_prices WHERE sku IS NOT NULL AND sku != '' LIMIT 3")
rows = cur.fetchall()

print("\n=== 3 SKU из таблицы Wildberries ===")
for i, (sku, name) in enumerate(rows, 1):
    print(f"{i}. SKU: {sku} | Название: {name}")

cur.close()
conn.close()
