import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_time():
    print(f"System Local Time: {datetime.now()}")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("SELECT now(), now()::time, current_setting('TIMEZONE');")
        row = cur.fetchone()
        print(f"DB 'now()': {row[0]}")
        print(f"DB Time: {row[1]}")
        print(f"DB Timezone Setting: {row[2]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_time()
