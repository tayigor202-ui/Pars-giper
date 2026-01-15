
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    print("--- SP-CODE STATS PER COMPETITOR ---")
    cursor.execute("""
        SELECT competitor_name, 
               COUNT(*) as total, 
               COUNT(CASE WHEN sp_code IS NULL OR sp_code = '' THEN 1 END) as empty_sp
        FROM public.prices 
        GROUP BY competitor_name
    """)
    rows = cursor.fetchall()
    
    for r in rows:
        print(f"Store: '{r[0]}' | Total: {r[1]} | Empty SP: {r[2]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
