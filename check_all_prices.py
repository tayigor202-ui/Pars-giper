import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# Check prices table (Ozon data)
cur.execute('SELECT COUNT(*) FROM prices')
prices_total = cur.fetchone()[0]

cur.execute('SELECT COUNT(DISTINCT competitor_name) FROM prices')
competitors = cur.fetchone()[0]

cur.execute('SELECT sku, name, competitor_name, sp_code FROM prices LIMIT 10')
price_samples = cur.fetchall()

# Check wb_prices table (WB data)
cur.execute('SELECT COUNT(*) FROM wb_prices')
wb_prices_total = cur.fetchone()[0]

cur.execute('SELECT sku, name, competitor_name, sp_code FROM wb_prices LIMIT 10')
wb_price_samples = cur.fetchall()

print(f'\n=== ТАБЛИЦА PRICES (OZON) ===')
print(f'Всего записей: {prices_total}')
print(f'Уникальных магазинов: {competitors}')
print(f'\nПримеры данных:')
for sku, name, comp, sp in price_samples[:5]:
    print(f'  SKU: {sku}')
    print(f'  Название: {name[:60] if name else "N/A"}...')
    print(f'  Магазин: {comp}')
    print(f'  СП-код: {sp}')
    print()

print(f'\n=== ТАБЛИЦА WB_PRICES (WILDBERRIES) ===')
print(f'Всего записей: {wb_prices_total}')
print(f'\nПримеры данных:')
for sku, name, comp, sp in wb_price_samples[:5]:
    print(f'  SKU: {sku}')
    print(f'  Название: {name[:60] if name else "N/A"}...')
    print(f'  Магазин: {comp}')
    print(f'  СП-код: {sp}')
    print()

cur.close()
conn.close()
