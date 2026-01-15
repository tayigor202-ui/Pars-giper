import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print("="*70)
print("ТЕСТ: ЗАПОЛНЕНИЕ НАЗВАНИЙ ПЕРЕД PIVOT")
print("="*70)

conn = psycopg2.connect(DB_URL)
query = """SELECT sku,name,competitor_name,price_card,price_nocard,price_old,status,sp_code FROM public.prices ORDER BY name, competitor_name"""
df = pd.read_sql(query, conn)
conn.close()

# Apply mapping
store_mapping = {
    'Ссылка на наш магазин': 'Наш магазин',
    'Магазин DeLonghi Group': 'DeLonghi Group',
    'Delonghi official store': 'DeLonghi Official'
}
df['competitor_name'] = df['competitor_name'].map(lambda x: store_mapping.get(x, x))

print(f"\nПеред заполнением:")
print(f"  Записей с пустым name: {df['name'].isna().sum()}")

# Fill missing names per SP-CODE
def get_sp_name(sp_code):
    sp_data = df[df['sp_code'] == sp_code]['name']
    valid_names = sp_data.dropna()
    valid_names = valid_names[valid_names.astype(str).str.strip() != '']
    valid_names = valid_names[valid_names.astype(str).str.lower() != 'none']
    return valid_names.iloc[0] if len(valid_names) > 0 else None

sp_name_map = {sp: get_sp_name(sp) for sp in df['sp_code'].unique() if sp}
df['name'] = df.apply(lambda row: sp_name_map.get(row['sp_code']) if pd.isna(row['name']) or str(row['name']).strip() == '' else row['name'], axis=1)

print(f"\nПосле заполнения:")
print(f"  Записей с пустым name: {df['name'].isna().sum()}")

# Check specific SP-CODEs
test_codes = ['MCO00015384', 'СП-00003461', 'СП-00008782']
print(f"\nПримеры:")
for code in test_codes:
    sp_rows = df[df['sp_code'] == code]
    if len(sp_rows) > 0:
        print(f"\n{code}:")
        for _, row in sp_rows.iterrows():
            name_display = row['name'] if pd.notna(row['name']) and str(row['name']).strip() else "❌ ПУСТО"
            print(f"  {row['competitor_name']}: {name_display}")

print("\n" + "="*70)
