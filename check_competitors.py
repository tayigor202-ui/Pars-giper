
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    print("--- DISTINCT COMPETITORS IN DB ---")
    cursor.execute("SELECT DISTINCT competitor_name FROM public.prices ORDER BY competitor_name")
    rows = cursor.fetchall()
    
    for r in rows:
        print(f"'{r[0]}'")
        
    print(f"\nTotal Competitors: {len(rows)}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
