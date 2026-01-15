import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def add_status_column():
    print("Adding status column to prices table...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("ALTER TABLE public.prices ADD COLUMN IF NOT EXISTS status VARCHAR(50)")
        conn.commit()
        cur.close()
        conn.close()
        print("Column 'status' added successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_status_column()
