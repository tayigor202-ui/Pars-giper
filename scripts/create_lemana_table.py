import psycopg2
import os
from dotenv import load_dotenv

def create_table():
    load_dotenv()
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        sql = """
        CREATE TABLE IF NOT EXISTS public.lemana_prices (
            sku TEXT,
            name TEXT,
            competitor_name TEXT,
            price_card NUMERIC,
            price_nocard NUMERIC,
            price_old NUMERIC,
            status TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            sp_code TEXT,
            PRIMARY KEY (sku, competitor_name)
        );
        """
        
        cur.execute(sql)
        conn.commit()
        print("Table 'lemana_prices' created or already exists.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_table()
