import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_db_stats():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Total rows
    cur.execute("SELECT COUNT(*) FROM public.prices")
    total_rows = cur.fetchone()[0]
    
    # Rows with prices
    cur.execute("SELECT COUNT(*) FROM public.prices WHERE price_card IS NOT NULL")
    with_prices = cur.fetchone()[0]
    
    # Rows by status
    cur.execute("""
        SELECT status, COUNT(*) as count 
        FROM public.prices 
        GROUP BY status 
        ORDER BY count DESC
    """)
    
    print(f"Всего строк в базе: {total_rows}")
    print(f"Строк с ценами: {with_prices}")
    print(f"\nРаспределение по статусам:")
    for status, count in cur.fetchall():
        print(f"  {status}: {count}")
    
    # Unique SKUs
    cur.execute("SELECT COUNT(DISTINCT sku) FROM public.prices")
    unique_skus = cur.fetchone()[0]
    print(f"\nУникальных SKU: {unique_skus}")
    
    # Competitor names
    cur.execute("""
        SELECT competitor_name, COUNT(*) as count 
        FROM public.prices 
        GROUP BY competitor_name 
        ORDER BY count DESC
    """)
    
    print(f"\nРаспределение по магазинам:")
    for name, count in cur.fetchall():
        print(f"  {name}: {count}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_db_stats()
