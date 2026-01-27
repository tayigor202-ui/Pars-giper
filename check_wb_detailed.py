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

# Проверяем общее количество
cur.execute("SELECT COUNT(*) FROM public.wb_prices")
total = cur.fetchone()[0]
print(f"Всего строк в wb_prices: {total}")

# Проверяем с валидным SKU
cur.execute("SELECT COUNT(*) FROM public.wb_prices WHERE sku IS NOT NULL AND sku != ''")
valid = cur.fetchone()[0]
print(f"Строк с валидным SKU: {valid}")

# Получаем первые 3 записи (любые, даже с NULL)
cur.execute("SELECT sku, name, competitor_name FROM public.wb_prices LIMIT 5")
rows = cur.fetchall()
print(f"\nПервые 5 записей (включая NULL):")
for i, (sku, name, comp) in enumerate(rows, 1):
    print(f"{i}. SKU: {sku} | NAME: {name} | COMP: {comp}")

cur.close()
conn.close()
