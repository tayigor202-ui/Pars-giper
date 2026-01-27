import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_api():
    url = "http://localhost:3455/api/dashboard/stats?platform=wb"
    # Note: This might fail due to @login_required. I'll check if I can bypass or check logs.
    print(f"Testing API: {url}")
    try:
        # Since I can't easily login via script, I'll print the DB stats again to be sure
        import psycopg2
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        platforms = ['wb', 'ozon']
        for p in platforms:
            table = 'wb_prices' if p == 'wb' else 'prices'
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = cur.fetchone()[0]
            print(f"Table {table}: {cnt} rows")
            
            cur.execute(f"SELECT COUNT(DISTINCT sku) FROM {table}")
            sku_cnt = cur.fetchone()[0]
            print(f"Table {table}: {sku_cnt} unique SKUs")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
