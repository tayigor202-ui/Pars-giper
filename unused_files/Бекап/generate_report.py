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
        query = """SELECT sku,name,competitor_name,price_card,price_nocard,price_old FROM public.prices WHERE price_card IS NOT NULL ORDER BY name, competitor_name"""
        df = pd.read_sql(query, conn)
        conn.close()
        
        if len(df) == 0:
            print("[EXCEL] No data to report")
            return None
        
        # Маппинг технических названий на нормальные названия магазинов
        store_mapping = {
            'Ссылка на наш магазин': 'Наш магазин',
            'Магазин DeLonghi Group': 'DeLonghi Group',
            'Delonghi official store': 'DeLonghi Official 1',
            'Delonghi official store.1': 'DeLonghi Official 2'
        }
        df['competitor_name'] = df['competitor_name'].map(lambda x: store_mapping.get(x, x))
        
        # Создаём строки для отчёта
        report_rows = []
        for sku in df['sku'].unique():
            sku_data = df[df['sku'] == sku]
            row = {'Артикул': sku, 'Наименование': sku_data.iloc[0]['name']}
            
            for _, item in sku_data.iterrows():
                store = item['competitor_name']
                row[f"{store} - С картой"] = item['price_card'] if pd.notna(item['price_card']) else ''
                row[f"{store} - Без карты"] = item['price_nocard'] if pd.notna(item['price_nocard']) else ''
                row[f"{store} - Старая цена"] = item['price_old'] if pd.notna(item['price_old']) else ''
            
            report_rows.append(row)
        
        result_df = pd.DataFrame(report_rows)
        
        # Сортируем колонки: Артикул, Наименование, затем по магазинам
        base_cols = ['Артикул', 'Наименование']
        store_cols = [col for col in result_df.columns if col not in base_cols]
        store_cols.sort()
        result_df = result_df[base_cols + store_cols]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ozon_prices_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='Цены', index=False)
            worksheet = writer.sheets['Цены']
            
            # Стили для заголовков
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Применяем стили к заголовкам
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border
            
            # Автоширина колонок
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Закрепляем первую строку
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
    else:
        print("\n❌ Не удалось создать отчёт")
