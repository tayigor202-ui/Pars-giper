from curl_cffi.requests import Session as CffiSession
import json
import time

sku = "169380926"
url = "https://catalog.wb.ru/catalog/v2/detail"
params = {
    "appType": 1,
    "curr": "rub",
    "dest": -1257786,
    "spp": 30,
    "nm": sku
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://www.wildberries.ru",
    "Referer": f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"
}

session = CffiSession(impersonate="chrome124")
print(f"Testing {url} for SKU {sku}...")

try:
    res = session.get(url, params=params, headers=headers, timeout=10)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        prods = data.get('data', {}).get('products', [])
        if prods:
            print(f"Name: {prods[0].get('name')}")
            print(f"Price: {prods[0].get('salePriceU') / 100}")
        else:
            print("Products list is empty!")
    else:
        print(f"Error Body: {res.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
