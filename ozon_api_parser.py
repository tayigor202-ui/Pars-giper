#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from curl_cffi import requests
import json
import time
import random
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
API_ENDPOINT = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
PROXY_URL = "http://127.0.0.1:8118" # Residential proxy forwarder

def get_product_details_dynamic(product_link):
    """
    1. Initialize a fresh session.
    2. Visit Homepage via proxy to get IP-bound cookies (xcid).
    3. Call the API with the fresh cookies.
    """
    session = requests.Session(impersonate="chrome120")
    
    headers = {
        "authority": "www.ozon.ru",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru-RU,ru;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    proxies = {"http": PROXY_URL, "https": PROXY_URL}

    try:
        # Step 1: Visit Home to get fresh cookies
        print("[STEP 1] Visiting Ozon Home via Proxy to establish session...")
        res_home = session.get("https://www.ozon.ru/", headers=headers, proxies=proxies, timeout=30)
        
        if res_home.status_code != 200:
            print(f"[WARN] Home visit status: {res_home.status_code}")
            # Continue anyway, maybe session still valid
            
        xcid = session.cookies.get("xcid")
        print(f"[SESSION] Fresh xcid acquired: {xcid}")

        # Step 2: Call the API
        payload = {"url": product_link}
        api_headers = {
            "authority": "www.ozon.ru",
            "accept": "application/json",
            "x-o3-app-name": "entrypoint-api",
            "x-o3-app-version": "master",
            "referer": "https://www.ozon.ru" + product_link,
            "user-agent": headers["user-agent"],
            "sec-ch-ua": '"Not_A Brand";v="120", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        print(f"[STEP 2] Fetching API for {product_link}...")
        response = session.get(
            API_ENDPOINT, 
            params=payload, 
            headers=api_headers,
            proxies=proxies,
            timeout=30
        )

        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code}: {response.reason}")
            # If 403, it might be the x-o3 headers or fingerprint
            return None

        data = response.json()
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
        print(f"[ERROR] Dynamic fetch failed: {e}")
        return None

if __name__ == "__main__":
    link = "/product/1067025156/"
    info = get_product_details_dynamic(link)
    if info:
        print(f"\nSUCCESS! Title: {info['title']}, Price: {info['price']}")
    else:
        print("\nFAILED: Dynamic session did not bypass 403.")
