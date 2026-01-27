
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_PORT = os.getenv("DB_PORT", "5432")

def migrate():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        print("Adding 'platform' column to 'prices' table...")
        cur.execute("ALTER TABLE public.prices ADD COLUMN IF NOT EXISTS platform VARCHAR(20);")
        
        print("Setting default platform to 'ozon' for existing records...")
        cur.execute("UPDATE public.prices SET platform = 'ozon' WHERE platform IS NULL;")
        
        # Also let's make it have a default for future inserts
        cur.execute("ALTER TABLE public.prices ALTER COLUMN platform SET DEFAULT 'ozon';")
        
        conn.commit()
        print("Migration complete!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
