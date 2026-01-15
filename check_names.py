import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT competitor_name FROM public.prices ORDER BY competitor_name")
    rows = cur.fetchall()
    print(f"Found {len(rows)} unique seller names:")
    for row in rows:
        print(f"- {row[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
