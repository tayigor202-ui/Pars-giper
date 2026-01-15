
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_PORT = os.getenv("DB_PORT", "5432")

def clean():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM public.prices WHERE competitor_name = 'Test Competitor';")
        conn.commit()
        print(f"Deleted {cur.rowcount} rows (Test Competitor).")
        cur.close()
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    clean()
