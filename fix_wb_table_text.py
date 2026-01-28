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
    print("ИЗМЕНЕНИЕ ТИПОВ КОЛОНОК НА TEXT В ТАБЛИЦЕ wb_prices")
    print("=" * 60)
    
    # Change to TEXT for all potentially long columns
    columns_to_fix = ['competitor_name', 'name', 'sp_code', 'sku', 'price_card', 'price_nocard', 'price_old']
    
    for col in columns_to_fix:
        print(f"[*] Изменение {col} на TEXT...")
        cur.execute(f"ALTER TABLE public.wb_prices ALTER COLUMN {col} TYPE TEXT")
    
    conn.commit()
    print("\n✅ Все колонки успешно изменены на TEXT!")
    
    # Show new structure
    print("\n[INFO] Новая структура таблицы:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'wb_prices' 
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("ГОТОВО! Теперь можно импортировать WB данные без лимитов")
    print("=" * 60)
    
except Exception as e:
    print(f"ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
