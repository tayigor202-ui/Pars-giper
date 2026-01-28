import psycopg2
import os
from dotenv import load_dotenv

def cleanup_db():
    load_dotenv()
    db_url = os.getenv('DB_URL')
    if not db_url:
        db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    print(f"Connecting to {os.getenv('DB_NAME')}...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        for table in ['public.prices', 'public.wb_prices']:
            print(f"Processing table {table}...")
            
            # 1. Сначала очистим таблицу от пустых SKU
            print(f"  Cleaning empty SKUs in {table}...")
            cur.execute(f"DELETE FROM {table} WHERE sku IS NULL OR sku = '' OR sku = '---' OR sku = 'nan' OR sku = 'None'")
            
            # 2. Находим и удаляем дубликаты, которые появятся при переименовании %.0
            print(f"  Removing potential duplicates in {table}...")
            # Удаляем записи с .0, если уже существует такая же запись без .0
            cur.execute(f"""
                DELETE FROM {table} t1
                WHERE t1.sku LIKE '%.0'
                AND EXISTS (
                    SELECT 1 FROM {table} t2
                    WHERE t2.sku = REPLACE(t1.sku, '.0', '')
                    AND t2.competitor_name = t1.competitor_name
                )
            """)
            print(f"  Deleted duplicated entries: {cur.rowcount}")
            
            # 3. Теперь безопасно обновляем оставшиеся .0
            print(f"  Fixing .0 formatting in {table}...")
            cur.execute(f"UPDATE {table} SET sku = REPLACE(sku, '.0', '') WHERE sku LIKE '%.0'")
            print(f"  Updated .0 entries: {cur.rowcount}")
            
            # 4. Убираем лишние пробелы
            cur.execute(f"UPDATE {table} SET sku = TRIM(sku)")
        
        conn.commit()
        print("✅ DB Cleaned and deduplicated successfully!")
        
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    cleanup_db()
