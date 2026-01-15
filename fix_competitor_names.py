
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("--- FIXING COMPETITOR NAMES ---")

# 1. Update 'Delonghi official store' to 'DeLonghi Official Store' (or similar standard)
# Actually, let's map it to what the report expects or make it standard.
updates = {
    'Delonghi official store': 'Delonghi Official Store',
    'delonghi official store': 'Delonghi Official Store',
    'Магазин DeLonghi Group': 'DeLonghi Group', # Ensure consistency
}

for old, new in updates.items():
    cursor.execute("UPDATE public.prices SET competitor_name = %s WHERE competitor_name = %s", (new, old))
    print(f"Updated '{old}' -> '{new}' : {cursor.rowcount} rows")

conn.commit()
conn.close()
