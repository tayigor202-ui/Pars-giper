
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("--- CHECKING ORPHANED RECORDS ---")
cursor.execute("""
    SELECT count(*) 
    FROM public.prices 
    WHERE sp_code IS NULL OR sp_code = ''
""")
orphans = cursor.fetchone()[0]

cursor.execute("SELECT count(*) FROM public.prices")
total = cursor.fetchone()[0]

print(f"Total Records: {total}")
print(f"Records without SP-Code (Excluded from Report): {orphans}")

if orphans > 0:
    cursor.execute("""
        SELECT sku, name 
        FROM public.prices 
        WHERE sp_code IS NULL OR sp_code = '' 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    print("Examples of missing items:")
    for r in rows:
        print(f"SKU: {r[0]} | Name: {r[1]}")

conn.close()
