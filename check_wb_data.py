import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Get total count
cur.execute('SELECT COUNT(*) FROM products')
total = cur.fetchone()[0]

# Get products with SKU
cur.execute('SELECT COUNT(*) FROM products WHERE sku IS NOT NULL')
with_sku = cur.fetchone()[0]

# Get sample SKUs
cur.execute('SELECT sku, name FROM products WHERE sku IS NOT NULL LIMIT 10')
samples = cur.fetchall()

print(f'\n=== СТАТИСТИКА БАЗЫ ДАННЫХ ===')
print(f'Всего товаров: {total}')
print(f'Товаров с SKU: {with_sku}')
print(f'\n=== ПРИМЕРЫ SKU ===')
for sku, name in samples:
    print(f'SKU: {sku}')
    print(f'  Название: {name[:80]}...')
    print()

cur.close()
conn.close()
