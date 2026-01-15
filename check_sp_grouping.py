
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_grouping():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Find SP Codes that have more than 1 distinct SKU associated with them
        query = """
            SELECT sp_code, COUNT(DISTINCT sku) as sku_count, COUNT(DISTINCT competitor_name) as comp_count
            FROM public.prices
            WHERE sp_code IS NOT NULL AND sp_code != ''
            GROUP BY sp_code
            HAVING COUNT(DISTINCT competitor_name) > 1
            LIMIT 10;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} SP-Codes with multiple competitors:")
        for row in rows:
            print(f"SP-Code: {row[0]} | SKUs: {row[1]} | Competitors: {row[2]}")
            
            # Show details for the first one
            cur.execute(f"SELECT sku, competitor_name, price_nocard FROM public.prices WHERE sp_code = '{row[0]}'")
            details = cur.fetchall()
            for d in details:
                print(f"   - SKU: {d[0]} | Store: {d[1]} | Price: {d[2]}")
            print("-" * 40)

        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_grouping()
