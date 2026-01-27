import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_stats():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        table = 'wb_prices'
        
        # Total products (unique SKUs)
        cur.execute(f"SELECT COUNT(DISTINCT sku) FROM {table}")
        total_products = cur.fetchone()[0]
        print(f"Total Products (WB): {total_products}")
        
        # Products with prices
        cur.execute(f"""
            SELECT COUNT(DISTINCT sku) FROM {table}
            WHERE price_card IS NOT NULL 
            AND NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC > 0
        """)
        products_with_prices = cur.fetchone()[0]
        print(f"Products with prices (WB): {products_with_prices}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_stats()
