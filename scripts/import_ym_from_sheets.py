import os
import sys
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import re
import json

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

# Config file
CONFIG_FILE = 'config.json'

def get_config_url():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('ym_spreadsheet_url')
        except: pass
    return None

def get_export_url(url):
    """Конвертирует обычную ссылку Google Sheets в ссылку для экспорта CSV"""
    if not url: return None
    if '/export?format=csv' in url: return url
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        spreadsheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    return url

if len(sys.argv) > 1:
    SPREADSHEET_URL = get_export_url(sys.argv[1])
    print(f"[SHEETS] Using provided URL: {SPREADSHEET_URL}")
else:
    config_url = get_config_url()
    if config_url:
        SPREADSHEET_URL = get_export_url(config_url)
        print(f"[SHEETS] Using URL from config: {SPREADSHEET_URL}")
    else:
        print("[SHEETS] ERROR: No URL provided and no config found!")
        sys.exit(1)

def extract_sku_from_url(url_or_sku):
    """Извлекает SKU из URL или возвращает как есть"""
    if pd.isna(url_or_sku):
        return None
    
    value = str(url_or_sku).strip()
    if not value or value.lower() == 'nan':
        return None
    
    # Yandex Market URL patterns
    # Example: https://market.yandex.ru/product--name/123456789
    # Example: https://market.yandex.ru/offer/abcdef
    if 'market.yandex.ru' in value:
        # Try to find numeric SKU in product URL
        match = re.search(r'product(?:--[^/]+)?/(\d+)', value)
        if match:
            return match.group(1)
        # Try any numeric sequence at the end
        match = re.search(r'/(\d+)/?$', value)
        if match:
            return match.group(1)
        return None
    
    # If it's already a number, return as is
    if value.replace('.', '').replace(',', '').isdigit():
        return value.replace('.0', '').replace(',', '')
    
    return value

def load_from_google_sheets():
    """
    Загружает данные из Google Sheets в базу данных ym_prices.
    Структура: СП-КОД | Название | SKU_магазин1 | SKU_магазин2 | ...
    """
    
    print("[SHEETS] Загрузка данных из Google Sheets (Yandex Market)...")
    
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
            candidate = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            print(f"[SHEETS] WARNING Колонка СП-КОД не найдена явно. Используем: {candidate}")
            sp_kod_col = candidate
        
        if name_col is None:
            print(f"[SHEETS] WARNING Колонка Название не найдена явно. Используем: {df.columns[0]}")
            name_col = df.columns[0]

        # 2. Treat ALL other columns as Competitor Columns
        sku_columns = [c for c in df.columns if c != sp_kod_col and c != name_col]
        sku_columns = [c for c in sku_columns if "unnamed" not in c.lower() and c.strip() != ""]
        
        print(f"\n[SHEETS] Структура импорта:")
        print(f"  - СП-КОД: {sp_kod_col}")
        print(f"  - Название: {name_col}")
        print(f"  - SKU магазинов ({len(sku_columns)}): {sku_columns}")
        
        # Connect to database
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        cur = conn.cursor()
        
        # SMART SYNC: Upsert into ym_prices
        # We use region_id = 213 (Moscow) as default for imported SKUs
        DEFAULT_REGION = 213
        
        print(f"[DB] Начинаем умную синхронизацию Yandex Market (Region {DEFAULT_REGION})...")
        
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
                
                if not sku:
                    continue
                    
                competitor_name = sku_col.strip()
                
                # Use ON CONFLICT to update metadata 
                cur.execute("""
                    INSERT INTO public.ym_prices (sku, name, competitor_name, sp_code, region_id) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (sku, competitor_name, region_id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        sp_code = EXCLUDED.sp_code
                """, (sku, name if name else None, competitor_name, sp_kod, DEFAULT_REGION))
                
                total_skus += 1
                product_has_skus = True
            
            if product_has_skus:
                imported_products += 1
            
            if imported_products % 50 == 0:
                conn.commit()
                print(f"[SHEETS] Обработано {imported_products} товаров, добавлено {total_skus} SKU...")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"\n[SHEETS] OK Обработано товаров: {imported_products}")
        print(f"[SHEETS] OK Добавлено SKU в базу: {total_skus}")
        
    except Exception as e:
        print(f"[SHEETS] ERROR Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_from_google_sheets()
