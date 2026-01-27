#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы warmup_session()
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def generate_random_user_agent():
    """Простой UA для теста"""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.85 Safari/537.36"

def warmup_session():
    """Прогрев сессии напрямую (без прокси) для получения актуальных куки и User-Agent."""
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ru-RU")
    
    # Не используем headless для диагностики
    USE_HEADLESS = False
    if USE_HEADLESS:
        options.add_argument("--headless=new")
    
    # Добавляем случайный UA
    ua = generate_random_user_agent()
    options.add_argument(f"user-agent={ua}")
    
    driver = None
    try:
        print("[WARMUP] Запуск браузера (ПРЯМОЕ СОЕДИНЕНИЕ - быстрый тест)...")
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        
        print("[WARMUP] Посещение Ozon...")
        driver.get("https://www.ozon.ru")
        time.sleep(3)
        
        # Прогрев на странице любого товара (как в тесте)
        print("[WARMUP] Прогрев на странице товара...")
        driver.get("https://www.ozon.ru/product/1067025156/")
        time.sleep(5)
            
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        print(f"[WARMUP] ✅ Сессия прогрета. Извлечено {len(cookies_dict)} куки.")
        print(f"[WARMUP] User-Agent: {user_agent}")
        print(f"[WARMUP] Извлеченные куки: {list(cookies_dict.keys())[:5]}...")
        
        return cookies_dict, user_agent
    except Exception as e:
        print(f"[WARMUP] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        if driver:
            try: 
                print("[WARMUP] Закрытие браузера...")
                driver.quit()
            except: 
                pass

if __name__ == "__main__":
    print("="*70)
    print("ТЕСТ ПРОГРЕВА СЕССИИ")
    print("="*70)
    
    cookies, ua = warmup_session()
    
    if cookies and ua:
        print("\n" + "="*70)
        print("✅ ТЕСТ УСПЕШЕН!")
        print(f"   Количество куки: {len(cookies)}")
        print(f"   User-Agent: {ua[:50]}...")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ ТЕСТ ПРОВАЛЕН!")
        print("="*70)
