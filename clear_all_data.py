#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Очистка всех данных из всех таблиц базы данных
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def clear_all_data():
    """Очистить все данные из всех таблиц."""
    try:
        print(f"[DB] Подключение к базе данных...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Список таблиц для очистки
        tables = [
            'prices',           # Ozon prices
            'wb_prices',        # Wildberries prices
            'ozon_competitors', # Ozon competitors
            'wb_competitors',   # Wildberries competitors
            'delivery_info',    # Delivery information
            'parse_queue',      # Parse queue
            'price_history',    # Price history
            'products',         # Products
            'client_products',  # Client products
        ]
        
        print("\n" + "="*70)
        print("ОЧИСТКА ВСЕХ ДАННЫХ")
        print("="*70)
        
        for table in tables:
            try:
                # Проверяем существование таблицы
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    # Получаем количество записей до очистки
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count_before = cur.fetchone()[0]
                    
                    # Очищаем таблицу
                    cur.execute(f"DELETE FROM {table}")
                    conn.commit()
                    
                    print(f"✅ {table:20s} - удалено {count_before:5d} записей")
                else:
                    print(f"⚠️  {table:20s} - таблица не существует")
                    
            except Exception as e:
                print(f"❌ {table:20s} - ошибка: {e}")
                conn.rollback()
        
        # Проверяем результат
        print("\n" + "="*70)
        print("ПРОВЕРКА РЕЗУЛЬТАТА")
        print("="*70)
        
        for table in tables:
            try:
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    status = "✅ ПУСТО" if count == 0 else f"⚠️  {count} записей"
                    print(f"{table:20s}: {status}")
                    
            except Exception as e:
                print(f"{table:20s}: ❌ Ошибка проверки")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✅ ОЧИСТКА ЗАВЕРШЕНА")
        print("="*70)
        
    except Exception as e:
        print(f"[DB] ❌ Ошибка подключения: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Запрашиваем подтверждение
    print("\n⚠️  ВНИМАНИЕ! Это действие удалит ВСЕ данные из ВСЕХ таблиц!")
    print("Таблицы: prices, wb_prices, products, competitors, и другие")
    
    response = input("\nВы уверены? Введите 'YES' для подтверждения: ")
    
    if response == "YES":
        clear_all_data()
    else:
        print("\n❌ Операция отменена")
