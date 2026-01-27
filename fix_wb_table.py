import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_table():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        print("Dropping and recreating wb_prices table with CORRECT schema...")
        cur.execute("DROP TABLE IF EXISTS public.wb_prices CASCADE")
        
        cur.execute("""
            CREATE TABLE public.wb_prices (
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
        
        conn.commit()
        print("Success: wb_prices table recreated with all price columns.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_table()
