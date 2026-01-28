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
    print("УВЕЛИЧЕНИЕ ЛИМИТОВ VARCHAR В ТАБЛИЦЕ wb_prices")
    print("=" * 60)
    
    # Increase VARCHAR limits for all text columns
    print("\n[1] Увеличение competitor_name до 500...")
    cur.execute("ALTER TABLE public.wb_prices ALTER COLUMN competitor_name TYPE VARCHAR(500)")
    
    print("[2] Увеличение name до 500...")
    cur.execute("ALTER TABLE public.wb_prices ALTER COLUMN name TYPE VARCHAR(500)")
    
    print("[3] Увеличение sp_code до 500...")
    cur.execute("ALTER TABLE public.wb_prices ALTER COLUMN sp_code TYPE VARCHAR(500)")
    
    conn.commit()
    print("\n✅ Все колонки успешно обновлены!")
    
    # Show new structure
    print("\n[INFO] Новая структура таблицы:")
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'wb_prices' 
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}" + (f"({row[2]})" if row[2] else ""))
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("ГОТОВО! Теперь можно импортировать WB данные")
    print("=" * 60)
    
except Exception as e:
    print(f"ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
