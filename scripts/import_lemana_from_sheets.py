import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import re
import json

# Load environment variables
load_dotenv()

# Database configuration
DB_URL = os.getenv('DATABASE_URL') or os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    if DB_USER and DB_PASS:
        DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        print("[ERROR] Database credentials not found in environment variables!")
        exit(1)

# Ensure psycopg2-compatible schema
if DB_URL and 'postgresql+psycopg2://' in DB_URL:
    DB_URL = DB_URL.replace('postgresql+psycopg2://', 'postgresql://')

# Load Lemana Google Sheets URL from config.json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    SPREADSHEET_URL = config.get('lemana_spreadsheet_url', '')

if not SPREADSHEET_URL:
    print("[ERROR] Lemana Sheet URL not found in config.json! Please add it.")
    # For now, we allow the script to exist but it will exit if URL is missing
    exit(1)

print(f"[INFO] Using Lemana Sheet URL: {SPREADSHEET_URL}")

def get_export_url(url):
    """Конвертирует обычную ссылку Google Sheets в ссылку для экспорта CSV"""
    if not url: return None
    if '/export?format=csv' in url: return url
    match_id = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match_id:
        spreadsheet_id = match_id.group(1)
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
        
        # Extract gid if present
        match_gid = re.search(r'gid=([0-9]+)', url)
        if match_gid:
            gid = match_gid.group(1)
            export_url += f"&gid={gid}"
            
        return export_url
    return url

SPREADSHEET_URL = get_export_url(SPREADSHEET_URL)

def extract_sku_from_url(value):
    """
    Извлекает SKU из URL или возвращает значение как есть, если это уже SKU.
    Поддерживает Lemana Pro URLs.
    """
    if pd.isna(value) or value == '':
        return None
    
    value = str(value).strip()
    
    # Lemana Pro URL patterns
    # Example: https://lemana-pro.ru/product/nabor-kleyashchikh-lent-skotch-dlya-upakovki-unibob-601-up-12-sht-90240393/
    # The SKU is usually the last number in the URL, optionally followed by slash or query params
    lemana_match = re.search(r'product/.*?/?(\d+)(?:/|\?|$)', value)
    if lemana_match:
        return lemana_match.group(1)
    
    # If it's already a number, return as is
    if value.replace('.', '').replace(',', '').isdigit():
        return value.replace('.0', '').replace(',', '')
    
    return None

def load_from_google_sheets():
    """
    Загружает данные из Google Sheets в таблицу lemana_prices.
    """
    print("[SHEETS] Загрузка данных из Google Sheets (Lemana Pro)...")
    
    try:
        df = pd.read_csv(SPREADSHEET_URL, header=0)
        
        # Identify columns
        sp_kod_col = None
        name_col = None
        ric_leroy_col = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(word in col_lower for word in ['сп-код', 'спкод', 'sp-kod', 'сп']):
                sp_kod_col = col
            elif any(word in col_lower for word in ['номенклатура', 'наименование', 'название', 'name']):
                if name_col is None:
                    name_col = col
            elif 'риц леруа' in col_lower:
                ric_leroy_col = col

        # Fallbacks
        if sp_kod_col is None: sp_kod_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
        if name_col is None: name_col = df.columns[0]

        sku_columns = []
        for c in df.columns:
            if c == sp_kod_col or c == name_col: continue
            c_low = c.lower()
            # Skip known price/info columns
            if any(p in c_low for p in ['риц', 'параметры', 'артикул', 'цена', 'стоимость']):
                continue
            # Allow Lemana, Ozon, WB or Unnamed (if it's a URL) or 'Код партнера' (SKU)
            if any(k in c_low for k in ['лемана', 'озон', 'вб', 'unnamed', 'код партнера']):
                sku_columns.append(c)
        
        if not sku_columns and len(df.columns) > 1:
            # Last resort: just try everything else that isn't name/sp_code
            sku_columns = [c for c in df.columns if c != sp_kod_col and c != name_col]
        
        print(f"[SHEETS] Найдено {len(sku_columns)} колонок с SKU/URL")
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("[DB] Очистка таблицы lemana_prices...")
        cur.execute("DELETE FROM public.lemana_prices")
        conn.commit()
        
        imported_products = 0
        total_skus = 0
        
        for idx, row in df.iterrows():
            sp_kod = str(row[sp_kod_col]).strip() if pd.notna(row[sp_kod_col]) else ''
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ''
            
            if not sp_kod or sp_kod == 'nan': continue
            
            # Extract RIC Leroy price
            ric_leroy = None
            if ric_leroy_col:
                val = str(row[ric_leroy_col])
                val_cleaned = "".join(c for c in val if c.isdigit() or c == '.' or c == ',').replace(',', '.')
                try:
                    ric_leroy = float(val_cleaned)
                except:
                    ric_leroy = None
            
            # Find the best SKU for Lemana Pro
            lemana_sku = None
            
            # 1. Search for a column with a URL containing lemanapro.ru
            for col in df.columns:
                val = str(row[col])
                if 'lemanapro.ru' in val or 'lemana-pro.ru' in val:
                    sku = extract_sku_from_url(val)
                    if sku:
                        lemana_sku = sku
                        break
            
            # 2. If no URL found, search for 'Код партнера'
            if not lemana_sku:
                for col in df.columns:
                    if 'код партнера' in col.lower():
                        sku = extract_sku_from_url(row[col])
                        if sku:
                            lemana_sku = sku
                            break
            
            # 3. Last fallback: use АРТИКУЛ or the second column
            if not lemana_sku:
                for col in df.columns:
                    if 'артикул' in col.lower():
                        sku = extract_sku_from_url(row[col])
                        if sku:
                            lemana_sku = sku
                            break

            if lemana_sku:
                # Find the actual URL for this SKU to store it
                # Prefer the longest URL (likely the full slug) over shorter ones
                full_url = None
                
                candidates = []
                for col in df.columns:
                    val = str(row[col])
                    if lemana_sku in val and ('lemanapro.ru' in val or 'lemana-pro.ru' in val):
                         candidates.append(val.strip())
                
                if candidates:
                    # Pick longest one
                    full_url = max(candidates, key=len)
                else:
                     # Construct default if none found (fallback)
                     full_url = f"https://lemanapro.ru/product/{lemana_sku}/"
                
                cur.execute("""
                    INSERT INTO public.lemana_prices (sku, name, competitor_name, sp_code, region_id, url, ric_leroy_price) 
                    VALUES (%s, %s, %s, %s, 34, %s, %s)
                    ON CONFLICT (sku, competitor_name, region_id) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        sp_code = EXCLUDED.sp_code,
                        url = EXCLUDED.url,
                        ric_leroy_price = EXCLUDED.ric_leroy_price
                """, (lemana_sku, name if name else None, 'Lemana Pro', sp_kod, full_url, ric_leroy))
                total_skus += 1
            
            imported_products += 1
            if imported_products % 50 == 0:
                conn.commit()
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[SHEETS] OK Завершено. SKU: {total_skus}")
        
    except Exception as e:
        print(f"[SHEETS] ERROR: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        os.system('title Lemana Pro - Import from Sheets')
    load_from_google_sheets()
