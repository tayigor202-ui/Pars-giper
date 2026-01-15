import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    print("Checking items where seller is NOT Ozon:")
    cur.execute("""
        SELECT sku, competitor_name, price_card 
        FROM public.prices 
        WHERE competitor_name != 'Ozon'
    """)
    rows = cur.fetchall()
    if not rows:
        print("No items found with seller != Ozon")
    else:
        print(f"Found {len(rows)} items:")
        for row in rows:
            print(f"SKU: {row[0]}, Seller: {row[1]}, Price: {row[2]}")
            
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
