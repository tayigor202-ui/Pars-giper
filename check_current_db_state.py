import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

print("="*70)
print("DATABASE STATE CHECK")
print("="*70)

# Total entries
cur.execute("SELECT COUNT(*) FROM public.prices")
total = cur.fetchone()[0]
print(f"\n1. Total entries in database: {total}")

# Unique competitors
cur.execute("SELECT DISTINCT competitor_name FROM public.prices WHERE competitor_name IS NOT NULL ORDER BY competitor_name")
competitors = [r[0] for r in cur.fetchall()]
print(f"\n2. Unique Competitors ({len(competitors)}):")
for c in competitors:
    print(f"   - {c}")

# Entries with prices vs without
cur.execute("SELECT COUNT(*) FROM public.prices WHERE price_nocard IS NOT NULL")
with_prices = cur.fetchone()[0]
print(f"\n3. Entries WITH prices: {with_prices}")
print(f"   Entries WITHOUT prices: {total - with_prices}")

# Out of stock entries
cur.execute("SELECT COUNT(*) FROM public.prices WHERE status = 'OUT_OF_STOCK'")
out_of_stock = cur.fetchone()[0]
print(f"\n4. Entries marked OUT_OF_STOCK: {out_of_stock}")

# Sample of recent data
cur.execute("""
    SELECT sku, competitor_name, price_nocard, status, created_at 
    FROM public.prices 
    WHERE created_at IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 5
""")
recent = cur.fetchall()
print(f"\n5. Most recent 5 entries with timestamps:")
if recent:
    for r in recent:
        print(f"   SKU {r[0]} | {r[1]} | Price: {r[2]} | Status: {r[3]} | Time: {r[4]}")
else:
    print("   NO ENTRIES WITH TIMESTAMPS (Database was likely just reset!)")

print("\n" + "="*70)

cur.close()
conn.close()
