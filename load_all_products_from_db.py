#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка ВСЕХ товаров из ozon_competitors для парсинга
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def get_all_skus_from_competitors():
    """Получить все SKU из таблицы ozon_competitors."""
    try:
        print(f"[DB] Подключение к базе данных...")
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Получаем все уникальные SKU из public.prices
        query = """
        SELECT DISTINCT sku 
        FROM public.prices 
        WHERE sku IS NOT NULL AND sku != ''
        ORDER BY sku
        """
        
        cursor.execute(query)
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Формируем ссылки
        product_links = [f"/product/{sku[0]}/" for sku in products]
        
        print(f"✅ Загружено {len(product_links)} уникальных товаров из ozon_competitors")
        
        # Сохраняем в файл
        with open("all_products_from_db.txt", "w", encoding="utf-8") as f:
            for link in product_links:
                f.write(link + "\n")
        
        print(f"💾 Список сохранен в all_products_from_db.txt")
        
        # Показываем первые 10
        print(f"\nПервые 10 товаров:")
        for i, link in enumerate(product_links[:10], 1):
            print(f"  {i}. {link}")
        
        if len(product_links) > 10:
            print(f"  ... и еще {len(product_links) - 10} товаров")
        
        return product_links
        
    except Exception as e:
        print(f"❌ Ошибка загрузки из БД: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    products = get_all_skus_from_competitors()
    
    if len(products) > 0:
        print(f"\n{'='*70}")
        print(f"✅ Готово к парсингу: {len(products)} товаров")
        print(f"{'='*70}")
        print(f"\n🚀 Запускаю гибридный парсер...")
        
        # Автоматически запускаем парсинг
        import subprocess
        subprocess.run(["python", "ozon_hybrid_batch_fast.py"], cwd=os.getcwd())
    else:
        print("\n❌ Товары не найдены в БД!")
