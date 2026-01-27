import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_wb_api_with_proxy():
    proxy_host = os.getenv('MOBILE_PROXY_HOST')
    proxy_port = os.getenv('MOBILE_PROXY_PORT')
    proxy_user = os.getenv('MOBILE_PROXY_USERNAME')
    proxy_pass = os.getenv('MOBILE_PROXY_PASSWORD')
    
    sku = "504869177"
    # Moscow dest
    url = f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub&dest=-1257786&nm={sku}"
    
    proxies = {
        "http": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}",
        "https": f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://www.wildberries.ru/"
    }
    
    print(f"Testing WB API via proxy {proxy_host}...")
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            prods = data.get('data', {}).get('products', [])
            if prods:
                p = prods[0]
                print(f"SUCCESS! Name: {p.get('name')} | Price: {p.get('salePriceU')/100}")
            else:
                print("FAILED: Result is empty (prods list empty)")
        else:
            print(f"FAILED: Connection error or block. Text: {res.text[:100]}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_wb_api_with_proxy()
