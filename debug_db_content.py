
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("--- COMPETITORS IN DB ---")
cursor.execute("SELECT DISTINCT competitor_name FROM public.prices")
rows = cursor.fetchall()
for r in rows:
    print(f"'{r[0]}'")

print("\n--- STATUS COUNTS ---")
cursor.execute("SELECT status, COUNT(*) FROM public.prices GROUP BY status")
rows = cursor.fetchall()
for r in rows:
    print(f"{r[0]}: {r[1]}")

print("\n--- OUT OF STOCK SAMPLE ---")
cursor.execute("""
    SELECT sku, competitor_name, price_card, status 
    FROM public.prices 
    WHERE status = 'OUT_OF_STOCK' OR price_card = 'Товар закончился' OR price_card IS NULL
    LIMIT 5
""")
rows = cursor.fetchall()
for r in rows:
    print(r)

conn.close()
