#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from curl_cffi import requests
import json

PROXY_URL = "http://127.0.0.1:8118"

def test_minimal():
    url = "https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/product/1067025156/"
    try:
        print(f"[TEST] Minimal curl-cffi call to {url}...")
        resp = requests.get(
            url, 
            impersonate="chrome110", 
            proxies={"http": PROXY_URL, "https": PROXY_URL},
            timeout=30
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS! Minimal request worked.")
            print(json.dumps(resp.json(), indent=2)[:500])
        else:
            print(f"FAILED with {resp.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_minimal()
