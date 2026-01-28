import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import re

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

# Load Wildberries Google Sheets URL from config.json
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    SPREADSHEET_URL = config.get('wb_spreadsheet_url', '')

if not SPREADSHEET_URL:
    print("[ERROR] Wildberries Sheet URL not found in config.json!")
    exit(1)

print(f"[INFO] Using Wildberries Sheet URL: {SPREADSHEET_URL}")

def extract_sku_from_url(value):
    """
    Извлекает SKU из URL или возвращает значение как есть, если это уже SKU.
    Поддерживает Wildberries URLs.
    """
    if pd.isna(value) or value == '':
        return None
    
    value = str(value).strip()
    
    # Wildberries URL patterns
    # Example: https://www.wildberries.ru/catalog/123456789/detail.aspx
    wb_match = re.search(r'wildberries\.ru/catalog/(\d+)', value)
    if wb_match:
        return wb_match.group(1)
    
    # If it's already a number, return as is
    if value.replace('.', '').replace(',', '').isdigit():
        return value.replace('.0', '').replace(',', '')
    
    return None

def load_from_google_sheets():
    """
    Загружает данные из Google Sheets в таблицу wb_prices.
    Структура: СП-КОД | Название | SKU_магазин1 | SKU_магазин2 | ...
    """
    
    print("[SHEETS] Загрузка данных из Google Sheets (Wildberries)...")
    
    try:
        # Read CSV directly from Google Sheets export URL
        # The first row contains the actual column names, so we use it as header
        df = pd.read_csv(SPREADSHEET_URL, header=0)
        
        # Check if columns are still "Unnamed" - if so, the first row is the header
        if all('unnamed' in str(col).lower() for col in df.columns):
            # Re-read with first row as header
            df = pd.read_csv(SPREADSHEET_URL)
            # Use first row as column names
            df.columns = df.iloc[0]
            # Drop the first row since it's now the header
            df = df[1:].reset_index(drop=True)
        
        print(f"[SHEETS] OK Загружено {len(df)} строк из Google Sheets")
        print(f"[SHEETS] Колонки: {list(df.columns)}")
        
        # Определяем колонки
        sp_kod_col = None
        name_col = None
        sku_columns = []
        
        # 1. Identify Metadata Columns
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'сп-код' in col_lower or 'спкод' in col_lower or 'sp-kod' in col_lower:
                sp_kod_col = col
                print(f"[SHEETS] Найдена колонка СП-КОД: {col}")
            elif any(word in col_lower for word in ['наименование', 'название', 'name']):
                if name_col is None:
                    name_col = col
                    print(f"[SHEETS] Найдена колонка Название: {col}")

        # Fallbacks
        if sp_kod_col is None:
            # Assume 2nd column if not found
            candidate = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            print(f"[SHEETS] WARNING Колонка СП-КОД не найдена явно. Используем: {candidate}")
            sp_kod_col = candidate
        
        if name_col is None:
            # Assume 1st column
            print(f"[SHEETS] WARNING Колонка Название не найдена явно. Используем: {df.columns[0]}")
            name_col = df.columns[0]

        # 2. Treat ALL other columns as Competitor Columns
        sku_columns = [c for c in df.columns if c != sp_kod_col and c != name_col]
        
        # Remove empty or unnamed columns if any
        sku_columns = [c for c in sku_columns if "unnamed" not in c.lower() and c.strip() != ""]
        
        print(f"\n[SHEETS] Структура импорта:")
        print(f"  - СП-КОД: {sp_kod_col}")
        print(f"  - Название: {name_col}")
        print(f"  - SKU магазинов ({len(sku_columns)}): {sku_columns}")
        
        # Connect to database
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()
        
        # CLEAR OLD DATA BEFORE IMPORT
        print("[DB] Очистка таблицы wb_prices (Wildberries)...")
        cur.execute("DELETE FROM public.wb_prices")
        conn.commit()
        print("[DB] OK Данные Wildberries очищены, начинаем импорт")
        
        # Import data
        imported_products = 0
        total_skus = 0
        skipped_rows = 0
        
        for idx, row in df.iterrows():
            sp_kod = str(row[sp_kod_col]).strip() if pd.notna(row[sp_kod_col]) else ''
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ''
            
            if not sp_kod or sp_kod == 'nan':
                skipped_rows += 1
                continue
            
            product_has_skus = False
            
            for sku_col in sku_columns:
                raw_value = row[sku_col]
                sku = extract_sku_from_url(raw_value)
                competitor_name = sku_col.strip()
                
                if sku:  # Only insert if SKU is not None
                    # Use ON CONFLICT to be safe
                    cur.execute("""
                        INSERT INTO public.wb_prices (sku, name, competitor_name, sp_code) 
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (sku, competitor_name) 
                        DO UPDATE SET 
                            name = EXCLUDED.name,
                            sp_code = EXCLUDED.sp_code
                    """, (sku, name if name else None, competitor_name, sp_kod))
                    
                    total_skus += 1
                    product_has_skus = True
            
            if product_has_skus:
                imported_products += 1
            
            # Commit every 50 products
            if imported_products % 50 == 0:
                conn.commit()
                print(f"[SHEETS] Обработано {imported_products} товаров, добавлено {total_skus} SKU...")
        
        # Final commit
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"\n[SHEETS] OK Обработано товаров: {imported_products}")
        print(f"[SHEETS] OK Добавлено SKU в базу: {total_skus}")
        print(f"[SHEETS] WARNING Пропущено строк: {skipped_rows}")
        
        # Verify import
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM public.wb_prices WHERE sku IS NOT NULL")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT competitor_name) FROM public.wb_prices WHERE competitor_name IS NOT NULL")
        stores = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT name) FROM public.wb_prices WHERE name IS NOT NULL")
        products = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        print(f"\n[DB] Всего SKU в базе (wb_prices): {total}")
        print(f"[DB] Уникальных товаров: {products}")
        print(f"[DB] Уникальных магазинов: {stores}")
        
    except Exception as e:
        print(f"[SHEETS] ERROR Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_from_google_sheets()
