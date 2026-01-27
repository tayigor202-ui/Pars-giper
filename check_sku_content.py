import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_content():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        print("--- Table: wb_prices (First 5 rows) ---")
        cur.execute("SELECT sku, name, competitor_name, price_card FROM wb_prices LIMIT 5")
        for row in cur.fetchall():
            print(row)
            
        print("\n--- Rows with NULL SKU ---")
        cur.execute("SELECT count(*) FROM wb_prices WHERE sku IS NULL OR sku = ''")
        print(f"Empty/NULL SKUs: {cur.fetchone()[0]}")
        
        print("\n--- Rows with valid SKU ---")
        cur.execute("SELECT count(*) FROM wb_prices WHERE sku IS NOT NULL AND sku != ''")
        print(f"Valid SKUs: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_content()
