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

# Default placeholder
DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yYpnpS0HkybD-Xsc5iPhlbPKC0r8yp3oG-HMDIVluvw/export?format=csv"

def get_export_url(url):
    """Конвертирует обычную ссылку Google Sheets в ссылку для экспорта CSV"""
    if not url: return None
    if '/export?format=csv' in url: return url
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        spreadsheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    return url

import sys
if len(sys.argv) > 1:
    SPREADSHEET_URL = get_export_url(sys.argv[1])
    print(f"[SHEETS] Using provided URL: {SPREADSHEET_URL}")
else:
    SPREADSHEET_URL = get_export_url(os.getenv('SPREADSHEET_URL', DEFAULT_SPREADSHEET_URL))
    print(f"[SHEETS] Using default/env URL: {SPREADSHEET_URL}")

def extract_sku_from_url(url_or_sku):
    """Извлекает SKU из URL или возвращает как есть, если это уже SKU"""
    if pd.isna(url_or_sku):
        return None
    
    value = str(url_or_sku).strip()
    
    # Если это URL, извлекаем SKU
    if 'ozon.ru' in value or 'http' in value:
        # Пытаемся найти числовой SKU в URL
        match = re.search(r'/(\d+)/?', value)
        if match:
            return match.group(1)
        return None
    
    # Если это уже число, возвращаем как есть
    if value.replace('.', '').replace(',', '').isdigit():
        return value.replace('.0', '').replace(',', '')
    
    return None

def load_from_google_sheets():
    """
    Загружает данные из Google Sheets в базу данных.
    Структура: СП-КОД | Название | SKU_магазин1 | SKU_магазин2 | ...
    """
    
    print("[SHEETS] Загрузка данных из Google Sheets...")
    
    try:
        # Read CSV directly from Google Sheets export URL
        df = pd.read_csv(SPREADSHEET_URL)
        
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
            # Assume 2nd column if not found (usually 1st is name, 2nd is code, or vice versa)
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
        print("[DB] Очистка таблицы prices...")
        cur.execute("TRUNCATE TABLE public.prices RESTART IDENTITY CASCADE")
        conn.commit()
        print("[DB] OK Таблица очищена, начинаем импорт новых данных")
        
        # Import data
        imported_products = 0
        total_skus = 0
        skipped_rows = 0
        skipped_skus = 0
        
        for idx, row in df.iterrows():
            sp_kod = str(row[sp_kod_col]).strip() if pd.notna(row[sp_kod_col]) else ''
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ''
            
            if not sp_kod or sp_kod == 'nan':
                skipped_rows += 1
                continue
            
            product_has_skus = False
            
            # Обрабатываем каждый SKU из разных магазинов
            for sku_col in sku_columns:
                raw_value = row[sku_col]
                sku = extract_sku_from_url(raw_value)
                
                # IMPORTANT: Create record even if SKU is empty!
                # This preserves name and sp_code for all stores
                
                # Извлекаем название магазина из названия колонки
                competitor_name = sku_col.strip()
                
                try:
                    if sku:
                        # Case 1: SKU exists - normal insert/update
                        cur.execute("""
                            SELECT sku FROM public.prices 
                            WHERE sku = %s AND competitor_name = %s
                        """, (sku, competitor_name))
                        
                        if cur.fetchone():
                            # Обновляем существующую запись
                            cur.execute("""
                                UPDATE public.prices 
                                SET name = %s, sp_code = %s
                                WHERE sku = %s AND competitor_name = %s
                            """, (name if name else None, sp_kod, sku, competitor_name))
                        else:
                            # Вставляем новую запись
                            cur.execute("""
                                INSERT INTO public.prices (sku, name, competitor_name, sp_code) 
                                VALUES (%s, %s, %s, %s)
                            """, (sku, name if name else None, competitor_name, sp_kod))
                        
                        total_skus += 1
                        product_has_skus = True
                    else:
                        # Case 2: NO SKU - but still create record with name and sp_code
                        # Check if record exists for this sp_code + competitor
                        cur.execute("""
                            SELECT sku FROM public.prices 
                            WHERE sp_code = %s AND competitor_name = %s AND (sku IS NULL OR sku = '')
                        """, (sp_kod, competitor_name))
                        
                        if cur.fetchone():
                            # Update existing placeholder record
                            cur.execute("""
                                UPDATE public.prices 
                                SET name = %s
                                WHERE sp_code = %s AND competitor_name = %s AND (sku IS NULL OR sku = '')
                            """, (name if name else None, sp_kod, competitor_name))
                        else:
                            # Insert placeholder record (no SKU, but has name and sp_code)
                            cur.execute("""
                                INSERT INTO public.prices (sku, name, competitor_name, sp_code) 
                                VALUES (%s, %s, %s, %s)
                            """, (None, name if name else None, competitor_name, sp_kod))
                        
                        product_has_skus = True  # Count it as processed
                    
                except Exception as e:
                    print(f"[DB ERROR] SKU {sku} (СП-КОД: {sp_kod}, Магазин: {competitor_name}): {e}")
                    conn.rollback()
                    skipped_skus += 1
                    continue
            
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
        print(f"[SHEETS] WARNING Пропущено SKU: {skipped_skus}")
        
        # Verify import
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM public.prices WHERE sku IS NOT NULL")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT competitor_name) FROM public.prices WHERE competitor_name IS NOT NULL")
        stores = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT name) FROM public.prices WHERE name IS NOT NULL")
        products = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        print(f"\n[DB] Всего SKU в базе: {total}")
        print(f"[DB] Уникальных товаров: {products}")
        print(f"[DB] Уникальных магазинов: {stores}")
        
    except Exception as e:
        print(f"[SHEETS] ERROR Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_from_google_sheets()
