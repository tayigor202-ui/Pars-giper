import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def clean_database():
    print("Cleaning database...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Reset names that are too long (likely reviews)
        cur.execute("UPDATE public.prices SET competitor_name = 'Ozon' WHERE length(competitor_name) > 40")
        print(f"Reset {cur.rowcount} rows with names > 40 chars")
        
        # 2. Reset specific bad names
        bad_names = ['Подписаться', 'Ссылка на наш магазин']
        cur.execute("UPDATE public.prices SET competitor_name = 'Ozon' WHERE competitor_name = ANY(%s)", (bad_names,))
        print(f"Reset {cur.rowcount} rows with specific bad names")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database cleaning complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_database()
