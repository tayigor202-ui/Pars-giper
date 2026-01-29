import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL') or os.getenv('DB_URL')
if DB_URL and 'postgresql+psycopg2://' in DB_URL:
    DB_URL = DB_URL.replace('postgresql+psycopg2://', 'postgresql://')

print(f"[FIX] Connecting to DB...")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

try:
    print("[FIX] Dropping old table...")
    cur.execute("DROP TABLE IF EXISTS public.lemana_prices CASCADE")
    
    print("[FIX] Creating new table with correct constraints...")
    cur.execute("""
        CREATE TABLE public.lemana_prices (
            id SERIAL PRIMARY KEY,
            sku TEXT NOT NULL,
            name TEXT,
            sp_code TEXT,
            competitor_name TEXT NOT NULL,
            price NUMERIC,
            stock INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            region_id INT NOT NULL DEFAULT 34,
            url TEXT
        )
    """)
    
    print("[FIX] Adding unique index...")
    # This is what ON CONFLICT matches against
    cur.execute("CREATE UNIQUE INDEX idx_lemana_prices_unique ON public.lemana_prices (sku, competitor_name, region_id)")
    
    conn.commit()
    print("[FIX] Success! Table recreated with unique index on (sku, competitor_name, region_id)")
except Exception as e:
    conn.rollback()
    print(f"[FIX] ERROR: {e}")
finally:
    cur.close()
    conn.close()
