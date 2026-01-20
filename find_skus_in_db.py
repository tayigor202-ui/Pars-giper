#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск SKU в разных таблицах БД
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def find_skus():
    """Найти SKU в разных таблицах."""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Проверяем parse_queue
        print("\n📋 Таблица parse_queue:")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'parse_queue'")
        cols = cursor.fetchall()
        print(f"Колонки: {[c[0] for c in cols]}")
        
        cursor.execute("SELECT COUNT(*) FROM parse_queue")
        count = cursor.fetchone()[0]
        print(f"Записей: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM parse_queue LIMIT 3")
            rows = cursor.fetchall()
            print(f"Примеры:")
            for row in rows:
                print(f"  {row}")
        
        # Проверяем ozon_competitors
        print("\n📋 Таблица ozon_competitors:")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'ozon_competitors'")
        cols = cursor.fetchall()
        print(f"Колонки: {[c[0] for c in cols]}")
        
        cursor.execute("SELECT COUNT(*) FROM ozon_competitors")
        count = cursor.fetchone()[0]
        print(f"Записей: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM ozon_competitors LIMIT 3")
            rows = cursor.fetchall()
            print(f"Примеры:")
            for row in rows:
                print(f"  {row}")
        
        # Проверяем client_products
        print("\n📋 Таблица client_products:")
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'client_products'")
        cols = cursor.fetchall()
        print(f"Колонки: {[c[0] for c in cols]}")
        
        cursor.execute("SELECT COUNT(*) FROM client_products")
        count = cursor.fetchone()[0]
        print(f"Записей: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM client_products LIMIT 3")
            rows = cursor.fetchall()
            print(f"Примеры:")
            for row in rows:
                print(f"  {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_skus()
