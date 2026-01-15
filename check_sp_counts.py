
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_counts():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT("sp_code"), COUNT("SP-Code") FROM public.prices')
        row = cur.fetchone()
        print(f"Count sp_code: {row[0]}")
        print(f"Count SP-Code: {row[1]}")
        
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_counts()
