import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_URL = os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def truncate_prices_table():
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Полностью очистить таблицу
        cur.execute("TRUNCATE TABLE public.prices RESTART IDENTITY CASCADE;")
        
        print("[DB] ✅ Таблица prices полностью очищена")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] ❌ Ошибка при очистке таблицы: {e}")

if __name__ == "__main__":
    print("[DB] Полная очистка таблицы prices...")
    truncate_prices_table()
    print("[DB] Готово!")
