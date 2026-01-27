import requests
import json
import time
from curl_cffi.requests import Session as CffiSession

skus = ["169380926", "504869177"]
endpoints = [
    "https://catalog.wb.ru/catalog/v2/detail",
]

headers_list = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.wildberries.ru/",
    },
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    }
]

skus = ["169380926", "504869177"]
regions = "80,38,4,64,83,33,68,70,69,30,86,40,1,48,66,31,22,110"

for sku in skus:
    url = f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1257786&regions={regions}&nm={sku}"
    try:
        res = requests.get(url, headers=headers_list[0], timeout=5)
        print(f"[{res.status_code}] SKU {sku}: {url[:100]}...")
        if res.status_code == 200:
            data = res.json()
            prods = data.get('data', {}).get('products', [])
            if prods:
                print(f"   SUCCESS! Name: {prods[0].get('name')} | Price: {prods[0].get('salePriceU')/100}")
            else:
                print("   STILL EMPTY")
    except:
        pass

for ep in endpoints:
    for sku in skus:
        for h in headers_list:
            try:
                params = {"appType": 1, "curr": "rub", "dest": -1257786, "nm": sku}
                res = requests.get(ep, params=params, headers=h, timeout=5)
                print(f"[{res.status_code}] EP: {ep} | SKU: {sku} | UA: {h.get('User-Agent')[:50]}...")
                if res.status_code == 200:
                    print("   SUCCESS!")
            except:
                pass
