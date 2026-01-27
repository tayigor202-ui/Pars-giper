import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

cur = conn.cursor()

# Проверяем права admin
cur.execute("SELECT username, can_edit_database_settings FROM public.users WHERE username = 'admin'")
row = cur.fetchone()

if row:
    print(f"User: {row[0]}, can_edit_database_settings: {row[1]}")
    
    if not row[1]:
        print("\n⚠️ У admin НЕТ прав can_edit_database_settings!")
        print("Обновляю права...")
        cur.execute("UPDATE public.users SET can_edit_database_settings = TRUE WHERE username = 'admin'")
        conn.commit()
        print("✅ Права обновлены!")
    else:
        print("✅ У admin есть все необходимые права")
else:
    print("❌ Пользователь admin не найден!")

cur.close()
conn.close()
