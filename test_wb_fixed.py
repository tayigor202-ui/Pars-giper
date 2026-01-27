import requests
import json
import time
from curl_cffi.requests import Session as CffiSession

# User's failing SKUs from screenshot
skus = ["504869177", "505719868", "169380926"]

# Potential working regions string
regions = "80,38,4,64,83,33,68,70,69,30,86,40,1,48,66,31,22,110"

endpoints = [
    "https://card.wb.ru/cards/v4/detail",
    "https://card.wb.ru/cards/v2/detail",
    "https://card.wb.ru/cards/v1/detail",
    "https://catalog.wb.ru/catalog/v2/detail",
    "https://www.wildberries.ru/webapi/product/{sku}/data"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
}

def test_combination(session, url_pattern, sku, params):
    url = url_pattern.format(sku=sku)
    try:
        res = session.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            products = data.get('data', {}).get('products', [])
            if not products and "webapi" in url:
                if data.get('value'):
                   return f"SUCCESS (WEBAPI): {data.get('value').get('name')}"
            
            if products:
                return f"SUCCESS: {products[0].get('name')} | Price: {products[0].get('salePriceU')/100}"
            else:
                return "EMPTY (No products)"
        else:
            return f"HTTP {res.status_code}"
    except Exception as e:
        return f"ERROR: {str(e)[:50]}"

skus = ["504869177", "169380926"]
for sku in skus:
    url = f"https://www.wildberries.ru/webapi/product/{sku}/data"
    print(f"\nTesting WebAPI for {sku}: {url}")
    try:
        session = CffiSession(impersonate="chrome124")
        # WebAPI needs specific referer and headers
        headers = {
            "Referer": f"https://www.wildberries.ru/catalog/{sku}/detail.aspx",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        res = session.get(url, headers=headers, timeout=10)
        print(f"[{res.status_code}] -> ", end="")
        if res.status_code == 200:
            data = res.json()
            # webapi returns "value" key
            val = data.get('value', {})
            if val:
                print(f"SUCCESS: {val.get('name')} | Generic Price: {val.get('price')}")
            else:
                print("EMPTY value")
        else:
            print(f"FAIL: {res.text[:100]}")
    except Exception as e:
        print(f"ERROR: {e}")
