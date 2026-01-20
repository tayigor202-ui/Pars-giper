#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка структуры БД и наличия данных
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_database():
    """Проверить структуру и содержимое БД."""
    try:
        print(f"[DB] Подключение к базе данных...")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"\n📊 Таблицы в БД:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Проверяем структуру таблицы products
        if ('products',) in tables:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'products'
            """)
            columns = cursor.fetchall()
            print(f"\n📋 Колонки в таблице 'products':")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
            
            # Считаем количество записей
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            print(f"\n📈 Всего записей в products: {count}")
            
            if count > 0:
                # Показываем первые 5 записей
                cursor.execute("SELECT * FROM products LIMIT 5")
                rows = cursor.fetchall()
                print(f"\nПервые 5 записей:")
                for row in rows:
                    print(f"  {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()
