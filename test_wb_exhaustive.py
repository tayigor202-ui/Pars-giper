import requests
import json
import time
from curl_cffi.requests import Session as CffiSession

skus = ["504869177", "169380926"]
# Moscow dest
dest = -1257786
# Extensive regions string
regions = "80,38,4,64,83,33,68,70,69,30,86,40,1,48,66,31,22,110"

endpoints = [
    ("v4-global", "https://card.wb.ru/cards/v4/detail", {"appType": 1, "curr": "rub", "dest": dest, "regions": regions, "spp": 0}),
    ("v4-minimal", "https://card.wb.ru/cards/v4/detail", {"appType": 1, "curr": "rub", "dest": dest, "nm": "{sku}"}),
    ("catalog-v2", "https://catalog.wb.ru/catalog/v2/detail", {"appType": 1, "curr": "rub", "dest": dest, "nm": "{sku}"}),
    ("webapi", "https://www.wildberries.ru/webapi/product/{sku}/data", {}),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.wildberries.ru/",
}

def test_endpoint(session_type, name, url_tmpl, p_tmpl, sku):
    url = url_tmpl.format(sku=sku)
    p = {k: v.format(sku=sku) if isinstance(v, str) else v for k, v in p_tmpl.items()}
    if "nm" not in p and "webapi" not in url:
        p["nm"] = sku
        
    try:
        if session_type == "requests":
            res = requests.get(url, params=p, headers=headers, timeout=10)
        else:
            s = CffiSession(impersonate="chrome124")
            res = s.get(url, params=p, headers=headers, timeout=10)
            
        print(f"[{res.status_code}] {name} ({session_type}) -> ", end="")
        if res.status_code == 200:
            data = res.json()
            # Handle different JSON structures
            prods = data.get('data', {}).get('products', [])
            val = data.get('value', {})
            if prods:
                print(f"SUCCESS: {prods[0].get('name')} | Price: {prods[0].get('salePriceU')/100 if prods[0].get('salePriceU') else 'N/A'}")
                return True
            elif val:
                print(f"SUCCESS (Web): {val.get('name')}")
                return True
            else:
                print("EMPTY")
        else:
            print(f"FAIL")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")
    return False

print("--- STARTING LAYERED DIAGNOSTIC ---")
for sku in skus:
    print(f"\nSKU: {sku}")
    for name, url, p in endpoints:
        # Try requests first
        if test_endpoint("requests", name, url, p, sku):
            continue # If success, move to next ep or sku
        # Try CFFI if requests failed
        time.sleep(2)
        test_endpoint("cffi", name, url, p, sku)
        time.sleep(2)
