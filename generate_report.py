
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

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

def generate_excel_report():
    print("\n[EXCEL] Generating report...")
    try:
        conn = psycopg2.connect(DB_URL)
        # Select ALL items, including status and price details
        # Added sp_code for grouping
        query = """
            SELECT sp_code, sku, name, competitor_name, price_card, price_nocard, price_old, status 
            FROM public.prices 
            ORDER BY sp_code, competitor_name
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if len(df) == 0:
            print("[EXCEL] No data to report")
            return None
        
        # Mapping technical names to readable store names
        store_mapping = {
            'Ссылка на наш магазин': 'Наш магазин',
            'DeLonghi Group': 'DeLonghi Group',
            'Delonghi Official Store': 'DeLonghi Official'
        }
        df['competitor_name'] = df['competitor_name'].map(lambda x: store_mapping.get(x, x))
        
        print("\n[DEBUG] Competitors in Report DF:")
        print(df['competitor_name'].unique())

        
        # Normalize SP-Codes to ensure matching (Trim whitespace)
        df['sp_code'] = df['sp_code'].astype(str).str.strip()
        
        unique_products = df['sp_code'].unique()
        unique_products = sorted([x for x in unique_products if x and x.lower() != 'none' and x != 'nan'])
        
        report_rows = []
        for code in unique_products:
            # Get all entries for this SP-Code
            product_data = df[df['sp_code'] == code]
            
            # Base Row Data
            row = {
                'SP-Code': code,
                'Артикул (Ozon)': product_data.iloc[0]['sku'], 
                'Наименование': product_data.iloc[0]['name']
            }
            
            # Iterate through competitors for this product
            for _, item in product_data.iterrows():
                store = item['competitor_name']
                price_card = item['price_card']
                price_nocard = item['price_nocard']
                price_old = item['price_old']
                status = item.get('status')
                
                # Determine display text
                def format_val(val, item_status):
                    # PRIORITY 1: Explicit Status
                    if item_status == 'OUT_OF_STOCK':
                        return 'Товар закончился'
                    
                    # PRIORITY 2: Explicit Text in Price (e.g. from parser)
                    if isinstance(val, str) and 'закончился' in val.lower():
                        return 'Товар закончился'
                        
                    # PRIORITY 3: Value exists
                    if pd.notna(val):
                        return val
                        
                    # PRIORITY 4: Fallback Status
                    if item_status == 'ANTIBOT':
                        return 'Ошибка (Антибот)'
                    if item_status == 'ERROR':
                        return 'Ошибка парсинга'
                    if item_status == 'NO_PRICE':
                        return 'Нет цены'
                    return ''

                row[f"{store} - С картой"] = format_val(price_card, status)
                row[f"{store} - Без карты"] = format_val(price_nocard, status)
                row[f"{store} - Старая цена"] = format_val(price_old, status)
            
            report_rows.append(row)
        
        result_df = pd.DataFrame(report_rows)
        
        # Sort columns: SP-Code, Articul, Name, then Stores
        base_cols = ['SP-Code', 'Артикул (Ozon)', 'Наименование']
        store_cols = [col for col in result_df.columns if col not in base_cols]
        store_cols.sort()
        
        # Ensure base cols exist (in case df was empty differently)
        final_cols = []
        for c in base_cols:
            if c in result_df.columns:
                final_cols.append(c)
        final_cols.extend(store_cols)
        
        result_df = result_df[final_cols]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ozon_prices_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='Цены', index=False)
            worksheet = writer.sheets['Цены']
            
            # Styles
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Apply header styles
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border
            
            # Auto-width
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        val_len = len(str(cell.value))
                        if val_len > max_length:
                            max_length = val_len
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Freeze panes
            worksheet.freeze_panes = 'A2'
        
        print(f"[EXCEL] ✅ Report created: {filename}")
        print(f"[EXCEL] 📊 Rows: {len(result_df)}, Columns: {len(result_df.columns)}")
        return filename
    except Exception as e:
        print(f"[EXCEL] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("ГЕНЕРАЦИЯ ОТЧЁТА OZON")
    print("=" * 60)
    filename = generate_excel_report()
    if filename:
        print(f"\n✅ Отчёт успешно создан: {filename}")
        os.system(f"start {filename}") # Open file automatically
    else:
        print("\n❌ Не удалось создать отчёт")
