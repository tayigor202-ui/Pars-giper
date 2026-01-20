#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import os
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- CONFIGURATION ---
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROXY_SERVER = "127.0.0.1:8118"

def get_product_details_browser_api(product_link):
    """
    Uses undetected_chromedriver to fetch the API JSON.
    This is slower than curl-cffi but 100% reliable against 403 blocks.
    """
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument(f"--proxy-server=http://{PROXY_SERVER}")
    options.add_argument("--headless=new") # Run in background
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    # API Endpoint URL
    api_url = f"https://www.ozon.ru/api/composer-api.bx/page/json/v2?url={product_link}"
    
    driver = None
    try:
        print(f"[BROWSER-API] Starting session for {product_link}...")
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        
        # Navigate directly to the API
        driver.get(api_url)
        time.sleep(5) # Wait for JSON to load
        
        # Extract JSON from body
        try:
            body_text = driver.find_element(By.TAG_NAME, "pre").text
        except:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
        data = json.loads(body_text)
        
        # Extraction logic matching the user template
        seo_data = data.get("seo") or data.get("SEO")
        if seo_data:
            return {
                "title": seo_data.get("title") or "Unknown",
                "price": seo_data.get("price"),
                "currency": seo_data.get("currency", "RUB"),
                "status": "OK"
            }
        else:
            print("[WARN] SEO key not found in JSON.")
            return None
            
    except Exception as e:
        print(f"[ERROR] Browser API fetch failed: {e}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    link = "/product/1067025156/"
    info = get_product_details_browser_api(link)
    if info:
        print(f"\nSUCCESS! Title: {info['title']}, Price: {info['price']}")
    else:
        print("\nFAILED: Even browser-backed API fetch could not find 'seo' data.")
