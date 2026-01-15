import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

print("="*70)
print("ДИАГНОСТИКА: ОТСУТСТВУЮЩИЕ НАЗВАНИЯ")
print("="*70)

# Find SP-CODEs with missing or inconsistent names
cur.execute("""
    SELECT sp_code, competitor_name, name
    FROM public.prices 
    WHERE sp_code IS NOT NULL AND sp_code != ''
    ORDER BY sp_code, competitor_name
""")

rows = cur.fetchall()
cur.close()
conn.close()

# Group by SP-CODE
from collections import defaultdict
sp_groups = defaultdict(list)
for sp_code, comp, name in rows:
    sp_groups[sp_code].append((comp, name))

print(f"\nВсего уникальных SP-CODE: {len(sp_groups)}\n")

# Find SP-CODEs with missing names
print("SP-CODE с пустыми названиями у некоторых магазинов:")
print("-" * 70)

empty_count = 0
for sp_code, entries in sp_groups.items():
    names = [name for comp, name in entries]
    # Check if any name is None or empty
    if any(not name or str(name).strip() == '' or str(name).lower() == 'none' for name in names):
        empty_count += 1
        if empty_count <= 5:  # Show first 5 examples
            print(f"\n{sp_code}:")
            for comp, name in entries:
                name_display = name if name and str(name).strip() else "❌ ПУСТО"
                print(f"  {comp}: {name_display}")

print(f"\n\nИТОГО: {empty_count} SP-CODE имеют пустые названия у некоторых магазинов")

# Check unique names per SP-CODE
print("\n" + "="*70)
print("SP-CODE с РАЗНЫМИ названиями у разных магазинов:")
print("-" * 70)

diff_count = 0
for sp_code, entries in sp_groups.items():
    names = [name for comp, name in entries if name and str(name).strip() and str(name).lower() != 'none']
    unique_names = set(names)
    if len(unique_names) > 1:
        diff_count += 1
        if diff_count <= 3:  # Show first 3 examples
            print(f"\n{sp_code} имеет {len(unique_names)} разных названий:")
            for comp, name in entries:
                print(f"  {comp}: {name}")

print(f"\n\nИТОГО: {diff_count} SP-CODE имеют разные названия")
print("="*70)
