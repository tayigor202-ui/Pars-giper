import requests

skus = ["504869177", "505719868", "169380926"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

for sku in skus:
    url = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"SKU {sku} Page: {res.status_code}")
        if res.status_code == 200:
            print(f"  Title contains WB: {'Wildberries' in res.text[:1000]}")
    except Exception as e:
        print(f"SKU {sku} Error: {e}")
