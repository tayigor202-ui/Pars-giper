import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def clean():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM public.prices WHERE competitor_name = 'Test Competitor'")
    print(f"Deleted {cur.rowcount} test rows.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean()
