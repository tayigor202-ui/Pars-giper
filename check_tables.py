import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    print("=" * 60)
    print("ПРОВЕРКА ДАННЫХ В ТАБЛИЦАХ")
    print("=" * 60)
    
    # Check OZON table
    print("\n[OZON] Таблица: public.prices")
    cur.execute("SELECT COUNT(*) FROM public.prices")
    ozon_count = cur.fetchone()[0]
    print(f"  Всего записей: {ozon_count}")
    
    if ozon_count > 0:
        cur.execute("SELECT * FROM public.prices LIMIT 3")
        print("  Первые 3 записи:")
        for row in cur.fetchall():
            print(f"    {row}")
    
    # Check WB table
    print("\n[WB] Таблица: public.wb_prices")
    cur.execute("SELECT COUNT(*) FROM public.wb_prices")
    wb_count = cur.fetchone()[0]
    print(f"  Всего записей: {wb_count}")
    
    if wb_count > 0:
        cur.execute("SELECT * FROM public.wb_prices LIMIT 3")
        print("  Первые 3 записи:")
        for row in cur.fetchall():
            print(f"    {row}")
    else:
        print("  ⚠️ ТАБЛИЦА ПУСТАЯ!")
    
    print("\n" + "=" * 60)
    print(f"ИТОГО: OZON={ozon_count}, WB={wb_count}")
    print("=" * 60)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
