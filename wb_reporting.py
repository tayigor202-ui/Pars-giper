
import os
import psycopg2
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

def generate_wb_report():
    print("\n[EXCEL] Generating WB report...")
    try:
        conn = psycopg2.connect(DB_URL)
        query = """
            SELECT sp_code, sku, name, competitor_name, price_card, price_nocard, price_old, status 
            FROM public.prices 
            WHERE platform = 'wb'
            ORDER BY sp_code, competitor_name
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if len(df) == 0:
            print("[EXCEL] No WB data to report")
            return None
            
        # Normalize SP-Codes
        df['sp_code'] = df['sp_code'].astype(str).str.strip()
        unique_products = sorted([x for x in df['sp_code'].unique() if x and x.lower() != 'none'])
        
        report_rows = []
        for code in unique_products:
            product_data = df[df['sp_code'] == code]
            if len(product_data) == 0: continue
            
            row = {
                'SP-Code': code,
                'Артикул (WB)': product_data.iloc[0]['sku'], 
                'Наименование': product_data.iloc[0]['name']
            }
            
            for _, item in product_data.iterrows():
                store = item['competitor_name']
                status = item.get('status')
                
                def format_val(val, st):
                    if st == 'OUT_OF_STOCK': return 'Товар закончился'
                    if pd.notna(val) and val != 0: return val
                    if st == 'ANTIBOT': return 'Ошибка (Антибот)'
                    if st == 'ERROR': return 'Ошибка парсинга'
                    return ''

                row[f"{store} - С картой"] = format_val(item['price_card'], status)
                row[f"{store} - Без карты"] = format_val(item['price_nocard'], status)
                row[f"{store} - Старая цена"] = format_val(item['price_old'], status)
            
            report_rows.append(row)
        
        result_df = pd.DataFrame(report_rows)
        
        # Column sorting
        base_cols = ['SP-Code', 'Артикул (WB)', 'Наименование']
        store_cols = sorted([c for c in result_df.columns if c not in base_cols])
        result_df = result_df[base_cols + store_cols]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wb_prices_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='Цены WB', index=False)
            ws = writer.sheets['Цены WB']
            
            # Styles
            header_fill = PatternFill(start_color="800080", end_color="800080", fill_type="solid") # Purple for WB
            header_font = Font(bold=True, color="FFFFFF", size=11)
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border
                
            for column in ws.columns:
                max_len = 0
                col_letter = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value: max_len = max(max_len, len(str(cell.value)))
                    except: pass
                ws.column_dimensions[col_letter].width = min(max_len + 2, 50)
                
        print(f"[EXCEL] ✅ WB Report created: {filename}")
        return filename
    except Exception as e:
        print(f"[EXCEL] ❌ Error: {e}")
        return None

def send_wb_report(filename):
    if not filename: return
    print(f"[TELEGRAM] 📤 Sending {filename}...")
    
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[TELEGRAM] ❌ Token or Chat ID missing")
        return
        
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendDocument"
    try:
        with open(filename, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': TG_CHAT_ID, 'caption': f'🟣 Отчёт по ценам Wildberries\n\n✅ Файл: {filename}'}
            resp = requests.post(url, files=files, data=data, timeout=30)
            if resp.status_code == 200 and resp.json().get('ok'):
                print("[TG] ✅ Report sent successfully")
            else:
                print(f"[TG] ❌ Failed: {resp.text}")
    except Exception as e:
        print(f"[TG] ❌ Error: {e}")

if __name__ == "__main__":
    f = generate_wb_report()
    send_wb_report(f)
