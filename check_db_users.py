"""Check database and users setup"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*60)
print("ПРОВЕРКА БАЗЫ ДАННЫХ И ПОЛЬЗОВАТЕЛЕЙ")
print("="*60)

# Check environment variables
print("\n1. Переменные окружения:")
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'ozon_parser')
db_user = os.getenv('DB_USER', 'postgres')
db_pass = os.getenv('DB_PASS')

print(f"   DB_HOST: {db_host}")
print(f"   DB_PORT: {db_port}")
print(f"   DB_NAME: {db_name}")
print(f"   DB_USER: {db_user}")
print(f"   DB_PASS: {'***' if db_pass else 'НЕ УСТАНОВЛЕН'}")

# Check if database exists
print("\n2. Проверка базы данных:")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_pass,
        database='postgres'
    )
    cur = conn.cursor()
    cur.execute(f"SELECT datname FROM pg_database WHERE datname='{db_name}'")
    db_exists = cur.fetchone()
    
    if db_exists:
        print(f"   ✓ База данных '{db_name}' СУЩЕСТВУЕТ")
    else:
        print(f"   ✗ База данных '{db_name}' НЕ СУЩЕСТВУЕТ")
        print(f"   Попробуйте создать: CREATE DATABASE {db_name};")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ✗ Ошибка подключения к PostgreSQL: {e}")
    exit(1)

# Check users table
print("\n3. Проверка таблицы пользователей:")
try:
    conn = psycopg2.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_pass,
        database=db_name
    )
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        )
    """)
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        print("   ✓ Таблица 'users' СУЩЕСТВУЕТ")
        
        # Count users
        cur.execute("SELECT COUNT(*) FROM public.users")
        user_count = cur.fetchone()[0]
        print(f"   ✓ Найдено пользователей: {user_count}")
        
        # Show users
        if user_count > 0:
            cur.execute("""
                SELECT id, username, full_name, email, is_active, last_login 
                FROM public.users
            """)
            users = cur.fetchall()
            print("\n   Пользователи:")
            for user in users:
                status = "АКТИВЕН" if user[4] else "НЕАКТИВЕН"
                print(f"   - {user[1]} ({user[2]}) - {status}")
                print(f"     Email: {user[3] or 'не указан'}")
                print(f"     Последний вход: {user[5] or 'никогда'}")
    else:
        print("   ✗ Таблица 'users' НЕ СУЩЕСТВУЕТ")
        print("   Запустите: python init_users.py")
        
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

print("\n" + "="*60 + "\n")
