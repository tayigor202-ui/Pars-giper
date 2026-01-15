import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    print("Checking seller distribution for items WITH prices:")
    cur.execute("""
        SELECT competitor_name, COUNT(*) 
        FROM public.prices 
        WHERE price_card IS NOT NULL 
        GROUP BY competitor_name 
        ORDER BY COUNT(*) DESC
    """)
    rows = cur.fetchall()
    for row in rows:
        print(f"{row[0]}: {row[1]}")
        
    print("\nChecking total items with prices:")
    cur.execute("SELECT COUNT(*) FROM public.prices WHERE price_card IS NOT NULL")
    print(f"Total: {cur.fetchone()[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
