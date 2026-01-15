import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_sellers():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print(f"Connecting to database...")
        cur.execute("""
            SELECT competitor_name, COUNT(*) 
            FROM public.prices 
            GROUP BY competitor_name 
            ORDER BY COUNT(*) DESC
        """)
        
        rows = cur.fetchall()
        print("\n=== SELLERS IN DATABASE ===")
        print(f"{'SELLER NAME':<40} | {'COUNT':<10}")
        print("-" * 55)
        
        for row in rows:
            name = row[0] if row[0] else "NULL"
            count = row[1]
            print(f"{name:<40} | {count:<10}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sellers()
