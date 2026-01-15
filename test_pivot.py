import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn=psycopg2.connect(DB_URL)
query="""SELECT sku,name,competitor_name,price_card,price_nocard,price_old,status,sp_code FROM public.prices ORDER BY name, competitor_name"""
df=pd.read_sql(query,conn)
conn.close()

print("="*70)
print("ДИАГНОСТИКА PIVOT TABLE")
print("="*70)

# 1. Unique competitors
print(f"\n1. Уникальные магазины в БД ({len(df['competitor_name'].unique())}):")
for c in sorted(df['competitor_name'].unique()):
    count = len(df[df['competitor_name']==c])
    print(f"   - {c}: {count} записей")

# 2. Sample products
print(f"\n2. Пример: Первый SP-CODE с несколькими магазинами:")
first_sp = df['sp_code'].iloc[0]
sample = df[df['sp_code']==first_sp][['sp_code','name','competitor_name','price_nocard','status']]
print(sample.to_string(index=False))

# 3. Apply mapping
store_mapping={
    'Ссылка на наш магазин':'Наш магазин',
    'Магазин DeLonghi Group':'DeLonghi Group',
    'DeLonghi Group':'DeLonghi Group',
    'Delonghi Official Store':'DeLonghi Official',
    'Delonghi official store':'DeLonghi Official',
    'DeLonghi Official Store':'DeLonghi Official'
}
df['competitor_name']=df['competitor_name'].map(lambda x:store_mapping.get(x,x))

print(f"\n3. После маппинга ({len(df['competitor_name'].unique())} магазинов):")
for c in sorted(df['competitor_name'].unique()):
    count = len(df[df['competitor_name']==c])
    print(f"   - {c}: {count} записей")

# 4. Pivot test
pivot_df = df.pivot_table(
    index=['sp_code', 'name'], 
    columns='competitor_name', 
    values=['sku'],
    aggfunc='first'
)

print(f"\n4. PIVOT TABLE:")
print(f"   Строк (товаров): {len(pivot_df)}")
print(f"   Колонок магазинов: {pivot_df.columns.get_level_values(1).unique().tolist()}")

print("\n" + "="*70)
