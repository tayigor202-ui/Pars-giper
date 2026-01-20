#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка товаров из БД для тестирования гибридного парсера
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def get_test_products(limit=70):
    """Получить список товаров для тестирования."""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # Получаем товары из БД
        query = """
        SELECT DISTINCT sku 
        FROM products 
        WHERE sku IS NOT NULL 
        LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Формируем ссылки
        product_links = [f"/product/{sku[0]}/" for sku in products]
        
        print(f"✅ Загружено {len(product_links)} товаров из БД")
        
        # Сохраняем в файл для удобства
        with open("test_products_70.txt", "w", encoding="utf-8") as f:
            for link in product_links:
                f.write(link + "\n")
        
        print(f"💾 Список сохранен в test_products_70.txt")
        
        return product_links
        
    except Exception as e:
        print(f"❌ Ошибка загрузки из БД: {e}")
        return []

if __name__ == "__main__":
    products = get_test_products(70)
    print(f"\nПервые 5 товаров:")
    for i, link in enumerate(products[:5], 1):
        print(f"  {i}. {link}")
