import pandas as pd

# Check the generated report
df = pd.read_excel('ozon_prices_report_20251209_124446.xlsx')

print("="*70)
print("АНАЛИЗ ГОТОВОГО ОТЧЁТА")
print("="*70)

print(f"\nВсего строк (товаров): {len(df)}")
print(f"Всего колонок: {len(df.columns)}")

print("\nВСЕ КОЛОНКИ:")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

# Count store columns
stores = set()
for col in df.columns:
    if ' - ' in col:
        store_name = col.split(' - ')[0]
        stores.add(store_name)

print(f"\n✅ МАГАЗИНОВ В ОТЧЁТЕ: {len(stores)}")
for store in sorted(stores):
    print(f"   - {store}")

# Check if all products have data or "Товар закончился"
print(f"\n📊 ПРИМЕР ПЕРВОГО ТОВАРА:")
print(df.iloc[0].to_string())

print("\n" + "="*70)
