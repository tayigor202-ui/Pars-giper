import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_none_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Get all rows with competitor_name = NULL
    cur.execute("""
        SELECT sku, competitor_name, status, price_card, name 
        FROM public.prices 
        WHERE competitor_name IS NULL
        LIMIT 20
    """)
    
    print("Rows with competitor_name = NULL:")
    for row in cur.fetchall():
        print(f"  SKU: {row[0]}, Status: {row[2]}, Price: {row[3]}, Name: {row[4][:40] if row[4] else 'None'}...")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_none_entries()
