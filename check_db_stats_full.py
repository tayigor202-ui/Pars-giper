import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

print("\n" + "="*70)
print("СТАТИСТИКА БАЗЫ ДАННЫХ ПОСЛЕ ИМПОРТА")
print("="*70)

# Check all tables
tables_info = [
    ('prices', 'Ozon'),
    ('wb_prices', 'Wildberries'),
    ('products', 'Товары'),
    ('ozon_competitors', 'Конкуренты Ozon'),
    ('wb_competitors', 'Конкуренты WB'),
    ('price_history', 'История цен'),
]

for table, description in tables_info:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{description:25s}: {count:6d} записей")
    except Exception as e:
        print(f"{description:25s}: ❌ Ошибка")

# Detailed Ozon stats
print("\n" + "="*70)
print("ДЕТАЛЬНАЯ СТАТИСТИКА OZON (prices)")
print("="*70)
cur.execute("SELECT COUNT(*) FROM prices WHERE sku IS NOT NULL")
ozon_with_sku = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT competitor_name) FROM prices")
ozon_stores = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT sp_code) FROM prices WHERE sp_code IS NOT NULL")
ozon_products = cur.fetchone()[0]

print(f"Всего записей:           {ozon_with_sku}")
print(f"Уникальных магазинов:    {ozon_stores}")
print(f"Уникальных товаров:      {ozon_products}")

# Detailed WB stats
print("\n" + "="*70)
print("ДЕТАЛЬНАЯ СТАТИСТИКА WILDBERRIES (wb_prices)")
print("="*70)
cur.execute("SELECT COUNT(*) FROM wb_prices WHERE sku IS NOT NULL")
wb_with_sku = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT competitor_name) FROM wb_prices")
wb_stores = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT sp_code) FROM wb_prices WHERE sp_code IS NOT NULL")
wb_products = cur.fetchone()[0]

print(f"Всего записей:           {wb_with_sku}")
print(f"Уникальных магазинов:    {wb_stores}")
print(f"Уникальных товаров:      {wb_products}")

# Sample data
print("\n" + "="*70)
print("ПРИМЕРЫ ДАННЫХ OZON")
print("="*70)
cur.execute("SELECT sku, name, competitor_name, sp_code FROM prices WHERE sku IS NOT NULL LIMIT 3")
for sku, name, comp, sp in cur.fetchall():
    print(f"SKU: {sku}")
    print(f"  Название: {name[:50] if name else 'N/A'}...")
    print(f"  Магазин: {comp}")
    print(f"  СП-код: {sp}")
    print()

print("="*70)
print("ПРИМЕРЫ ДАННЫХ WILDBERRIES")
print("="*70)
cur.execute("SELECT sku, name, competitor_name, sp_code FROM wb_prices WHERE sku IS NOT NULL LIMIT 3")
for sku, name, comp, sp in cur.fetchall():
    print(f"SKU: {sku}")
    print(f"  Название: {name[:50] if name else 'N/A'}...")
    print(f"  Магазин: {comp}")
    print(f"  СП-код: {sp}")
    print()

cur.close()
conn.close()

print("="*70)
print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
print("="*70)
