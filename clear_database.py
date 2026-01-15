import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# You may have DB_URL defined in environment, otherwise construct from individual vars
DB_URL = os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def clear_prices_table():
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Clear price data but keep SKUs
        cur.execute("""
            UPDATE public.prices 
            SET price_card = NULL, 
                price_nocard = NULL, 
                price_old = NULL, 
                competitor_name = NULL, 
                name = NULL, 
                created_at = NULL
        """)
        
        rows_affected = cur.rowcount
        print(f"[DB] ✅ Очищено {rows_affected} записей в таблице prices")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] ❌ Ошибка при очистке таблицы prices: {e}")

if __name__ == "__main__":
    print("[DB] Очистка базы данных...")
    clear_prices_table()
    print("[DB] Готово!")
