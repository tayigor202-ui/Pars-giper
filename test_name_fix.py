import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print("="*70)
print("ТЕСТ: НАЗВАНИЯ С FIRST_NON_EMPTY")
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

# Status transformation
def fill_status(row):
    status = row.get('status')
    p_card = row.get('price_card')
    
    if status == 'OUT_OF_STOCK':
        return pd.Series(['Товар закончился', 'Товар закончился', 'Товар закончился'], index=['price_card', 'price_nocard', 'price_old'])
    
    if pd.isna(p_card) or str(p_card).lower().strip() in ['', 'none', 'nan']:
        if status in ['ANTIBOT', 'ERROR', 'NO_PRICE']:
            return pd.Series([status, status, status], index=['price_card', 'price_nocard', 'price_old'])
        return pd.Series([None, None, None], index=['price_card', 'price_nocard', 'price_old'])
        
    return pd.Series([row['price_card'], row['price_nocard'], row['price_old']], index=['price_card', 'price_nocard', 'price_old'])

df[['price_card', 'price_nocard', 'price_old']] = df.apply(fill_status, axis=1)

# Custom aggregation for name
def first_non_empty(series):
    valid = series.dropna()
    valid = valid[valid.astype(str).str.strip() != '']
    valid = valid[valid.astype(str).str.lower() != 'none']
    return valid.iloc[0] if len(valid) > 0 else None

# Pivot with custom aggfunc
pivot_df = df.pivot_table(
    index='sp_code',
    columns='competitor_name',
    values=['name', 'sku', 'price_card', 'price_nocard', 'price_old'],
    aggfunc={
        'name': first_non_empty,  # Custom: first non-empty
        'sku': 'first',
        'price_card': 'first',
        'price_nocard': 'first',
        'price_old': 'first'
    },
    dropna=False
)

# Check for missing names
print(f"\nПроверка названий:")
print(f"  Всего SP-CODE: {len(pivot_df)}")

# Count how many have at least one name column filled
name_cols = [col for col in pivot_df.columns if col[1] == 'name']
has_name = 0
for idx, row in pivot_df.iterrows():
    if any(pd.notna(row[col]) and str(row[col]).strip() != '' for col in name_cols):
        has_name += 1

print(f"  SP-CODE с хотя бы одним названием: {has_name}")
print(f"  SP-CODE БЕЗ названий: {len(pivot_df) - has_name}")

# Show examples of previously empty SP-CODEs
test_codes = ['MCO00015384', 'СП-00003461', 'СП-00008782']
print(f"\nПримеры (ранее проблемные SP-CODE):")
for code in test_codes:
    if code in pivot_df.index:
        print(f"\n{code}:")
        for col in name_cols:
            store = col[0]
            name = pivot_df.loc[code, col]
            name_display = name if pd.notna(name) and str(name).strip() else "❌ ПУСТО"
            print(f"  {store}: {name_display}")

print("\n" + "="*70)
