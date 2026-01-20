#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid Ozon Parser: Browser Warmup + curl-cffi API Speed

This script combines the reliability of undetected_chromedriver with the 
performance of curl-cffi by:
1. Warming up a session via browser (UC) to get IP-bound cookies
2. Transferring the session to curl-cffi for fast API requests

Based on curl-cffi documentation: https://curl-cffi.readthedocs.io/
"""
import json
import time
import os
import re
from datetime import datetime
from curl_cffi.requests import Session as CffiSession  # Correct import per docs
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION ---
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROXY_SERVER = "127.0.0.1:8118"
API_ENDPOINT = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"

def warmup_session_with_browser(product_link):
    """
    Step 1: Use UC to visit Ozon and establish a valid session.
    Returns: (cookies_dict, user_agent_string)
    """
    options = uc.ChromeOptions()
    options.binary_location = CHROME_PATH
    options.add_argument(f"--proxy-server=http://{PROXY_SERVER}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ru-RU")
    # Headless can work if UC supports it well, otherwise visible is safer
    # options.add_argument("--headless=new")
    
    driver = None
    try:
        print("[WARMUP] Starting browser session...")
        driver = uc.Chrome(options=options, browser_executable_path=CHROME_PATH)
        
        # Visit home page first
        print("[WARMUP] Visiting Ozon home page...")
        driver.get("https://www.ozon.ru")
        time.sleep(5)
        
        # Visit the product page to establish context
        product_url = f"https://www.ozon.ru{product_link}"
        print(f"[WARMUP] Visiting product page: {product_url}")
        driver.get(product_url)
        time.sleep(8)  # Wait for page to fully load and JS to execute
        
        # Extract cookies
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        
        # Extract User-Agent
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        print(f"[WARMUP] Session established. Extracted {len(cookies_dict)} cookies.")
        print(f"[WARMUP] User-Agent: {user_agent[:50]}...")
        
        return cookies_dict, user_agent
        
    except Exception as e:
        print(f"[ERROR] Browser warmup failed: {e}")
        return None, None
    finally:
        if driver:
            driver.quit()
            print("[WARMUP] Browser closed.")

def fetch_api_with_cffi(product_link, cookies_dict, user_agent):
    """
    Step 2: Use curl-cffi with the warmed-up session to fetch API data.
    Uses chrome124 impersonation for better compatibility.
    """
    # Use correct Session class with impersonate parameter
    session = CffiSession(impersonate="chrome124")
    
    payload = {"url": product_link}
    
    headers = {
        "authority": "www.ozon.ru",
        "accept": "application/json",
        "accept-language": "ru-RU,ru;q=0.9",
        "user-agent": user_agent,
        "x-o3-app-name": "entrypoint-api",
        "x-o3-app-version": "master",
        "referer": f"https://www.ozon.ru{product_link}",
        "sec-ch-ua": '"Not_A Brand";v="120", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    
    proxies = {
        "http": f"http://{PROXY_SERVER}",
        "https": f"http://{PROXY_SERVER}",
    }
    
    try:
        print(f"[API] Fetching data via curl-cffi for {product_link}...")
        response = session.get(
            API_ENDPOINT,
            params=payload,
            headers=headers,
            cookies=cookies_dict,
            proxies=proxies,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[ERROR] API returned status {response.status_code}")
            return None
        
        print(f"[API] Success! Status 200 OK")
        data = response.json()
        
        # Extract from SEO key as per user template
        seo_data = data.get("seo") or data.get("SEO")
        
        if seo_data:
            # Extract price from JSON-LD if not directly available
            price = seo_data.get("price")
            currency = seo_data.get("currency", "RUB")
            
            if price is None and "script" in seo_data:
                for script in seo_data["script"]:
                    if "application/ld+json" in script.get("type", ""):
                        try:
                            ld_json = json.loads(script.get("innerHTML", "{}"))
                            if isinstance(ld_json, list):
                                ld_json = ld_json[0]
                            offers = ld_json.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0]
                            price = offers.get("price")
                            currency = offers.get("priceCurrency", currency)
                            break
                        except:
                            pass
            
            return {
                "title": seo_data.get("title") or "Unknown",
                "description": seo_data.get("description"),
                "price": price,
                "currency": currency,
                "status": "OK"
            }
        else:
            print("[WARN] SEO key not found in API response.")
            return None
            
    except Exception as e:
        print(f"[ERROR] API fetch failed: {e}")
        return None

def get_product_hybrid(product_link):
    """
    Main hybrid function: warmup + API fetch.
    """
    # Step 1: Browser warmup
    cookies, user_agent = warmup_session_with_browser(product_link)
    
    if not cookies or not user_agent:
        print("[FAIL] Could not establish browser session.")
        return None
    
    # Step 2: API fetch with inherited session
    result = fetch_api_with_cffi(product_link, cookies, user_agent)
    
    return result

if __name__ == "__main__":
    test_link = "/product/1067025156/"
    
    print("="*60)
    print(" HYBRID OZON PARSER TEST ")
    print("="*60)
    
    start_time = time.time()
    info = get_product_hybrid(test_link)
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print(" RESULT ")
    print("="*60)
    
    if info:
        print(f"✅ SUCCESS!")
        print(f"Title:    {info['title']}")
        print(f"Price:    {info['price']} {info['currency']}")
        print(f"Status:   {info['status']}")
        print(f"Time:     {elapsed:.2f}s")
    else:
        print("❌ FAILED: Could not extract product data.")
    
    print("="*60)
