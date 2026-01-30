import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def update_schema():
    print(f"Connecting to {os.getenv('DB_NAME')}...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        print("Adding columns...")
        cur.execute("ALTER TABLE public.lemana_prices ADD COLUMN IF NOT EXISTS ric_leroy_price NUMERIC;")
        cur.execute("ALTER TABLE public.lemana_prices ADD COLUMN IF NOT EXISTS violation_screenshot TEXT;")
        cur.execute("ALTER TABLE public.lemana_prices ADD COLUMN IF NOT EXISTS violation_detected BOOLEAN DEFAULT FALSE;")
        conn.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_schema()
