import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def delete_null_entries():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("DELETE FROM public.prices WHERE competitor_name IS NULL")
    deleted = cur.rowcount
    
    conn.commit()
    print(f"Deleted {deleted} rows with NULL competitor_name")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    delete_null_entries()
