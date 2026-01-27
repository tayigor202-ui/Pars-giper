import requests
import json

skus = ["169380926", "504869177"]
endpoints = [
    "https://card.wb.ru/cards/v1/detail",
    "https://www.wildberries.ru/webapi/product/{sku}/data",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://www.wildberries.ru",
}

for sku in skus:
    url = f"{base_url}?{params_base}{sku}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"[{res.status_code}] SKU: {sku}")
        if res.status_code == 200:
            data = res.json()
            prods = data.get('data', {}).get('products', [])
            if prods:
                print(f"!!! SUCCESS !!! Name: {prods[0].get('name')} | Price: {prods[0].get('salePriceU')/100}")
            else:
                print("Data found but products list is empty.")
    except Exception as e:
        print(f"Error: {e}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

for ep_raw in endpoints:
    for sku in skus:
        ep = ep_raw.format(sku=sku)
        
        # Test nm vs nmID
        for param_type in ["nm", "nmID"]:
            try:
                p = {param_type: sku, "appType": 1, "curr": "rub", "dest": -1257786}
                # For webapi, we don't need nm params usually
                if "webapi" in ep:
                    res = requests.get(ep, headers=headers, timeout=5)
                    print(f"[{res.status_code}] WebAPI: {ep}")
                    if res.status_code == 200:
                        print("SUCCESS (WebAPI)")
                    break # Only one SKU/test for webapi

                res = requests.get(ep, params=p, headers=headers, timeout=5)
                print(f"[{res.status_code}] EP: {ep} | Params: {param_type}={sku}")
                if res.status_code == 200:
                    print("SUCCESS")
            except Exception as e:
                pass

print("\n--- Testing Baskets ---")
for sku in skus:
    for url in get_basket_url(sku):
        try:
            res = requests.get(url, headers=headers, timeout=2)
            if res.status_code == 200:
                print(f"[OK] Basket URL: {url}")
                print(f"Data: {res.text[:100]}...")
                break
        except:
            pass
