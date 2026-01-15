import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def clean_null_sellers():
    print("Cleaning database of invalid sellers...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Delete NULL competitor_name
        cur.execute("DELETE FROM public.prices WHERE competitor_name IS NULL")
        deleted_null = cur.rowcount
        print(f"Deleted {deleted_null} rows with competitor_name = NULL")
        
        # 2. Delete 'Ozon' competitor_name (as per user request, only sheet competitors allowed)
        cur.execute("DELETE FROM public.prices WHERE competitor_name = 'Ozon'")
        deleted_ozon = cur.rowcount
        print(f"Deleted {deleted_ozon} rows with competitor_name = 'Ozon'")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database cleanup complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_null_sellers()
