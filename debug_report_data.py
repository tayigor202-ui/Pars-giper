
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("--- CHECKING SP-CODES ---")
# Check for potential whitespace duplicates
cursor.execute("""
    SELECT sp_code, length(sp_code), count(*)
    FROM public.prices
    GROUP BY sp_code, length(sp_code)
    ORDER BY sp_code
""")
rows = cursor.fetchall()
print(f"Total Unique SP-Codes (raw): {len(rows)}")
for r in rows[:10]:
    print(f"SP: '{r[0]}' | Len: {r[1]} | Count: {r[2]}")

print("\n--- CHECKING STATUS vs PRICE ---")
# Check rows where status is OUT_OF_STOCK but price is present
cursor.execute("""
    SELECT count(*) 
    FROM public.prices 
    WHERE status = 'OUT_OF_STOCK' AND price_nocard IS NOT NULL
""")
conflict_count = cursor.fetchone()[0]
print(f"Items with OUT_OF_STOCK but have Price: {conflict_count}")

cursor.execute("""
    SELECT sku, competitor_name, price_nocard, status
    FROM public.prices
    WHERE status = 'OUT_OF_STOCK'
    LIMIT 5
""")
examples = cursor.fetchall()
for e in examples:
    print(f"Example: {e} - Logic 'if price return price' will hide status!")

conn.close()
