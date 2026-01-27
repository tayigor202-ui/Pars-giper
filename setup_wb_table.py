import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_wb_table():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        print("Creating wb_prices table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.wb_prices (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(255),
                name VARCHAR(255),
                competitor_name TEXT,
                price_card VARCHAR(255),
                price_nocard VARCHAR(255),
                price_old VARCHAR(255),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                sp_code TEXT,
                status VARCHAR(255),
                UNIQUE (sku, competitor_name)
            )
        """)
        
        # Also clean up main prices table from WB data to be 100% clean
        print("Cleaning up WB data from main prices table...")
        cur.execute("DELETE FROM public.prices WHERE platform = 'wb'")
        
        conn.commit()
        print("Success: wb_prices table created and main prices table cleaned.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_wb_table()
