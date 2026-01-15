import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def add_column():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='prices' AND column_name='sp_code'")
        if not cur.fetchone():
            print("Adding sp_code column...")
            cur.execute("ALTER TABLE public.prices ADD COLUMN sp_code TEXT")
            conn.commit()
            print("✅ Column sp_code added")
        else:
            print("ℹ️ Column sp_code already exists")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_column()
