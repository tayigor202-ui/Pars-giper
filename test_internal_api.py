import requests, json, os
from dotenv import load_dotenv

load_dotenv()

def test_internal_wb_api_with_session():
    # Load session data
    with open("session_data.json", "r", encoding="utf-8") as f:
        sess = json.load(f)
    
    sku = "504869177"
    url = f"https://www.wildberries.ru/__internal/u-card/cards/v4/detail"
    
    params = {
        "appType": 1,
        "curr": "rub",
        "dest": "-1257786",
        "spp": 30,
        "hide_vflags": "4294967296",
        "hide_dtype": 9,
        "ab_testing": "false",
        "lang": "ru",
        "nm": sku
    }
    
    headers = {
        "User-Agent": sess['ua'],
        "Accept": "*/*",
        "Referer": f"https://www.wildberries.ru/catalog/{sku}/detail.aspx",
        "x-requested-with": "XMLHttpRequest",
        "x-spa-version": "13.20.2"
    }
    
    cookies = sess['cookies']
    
    print(f"Testing INTERNAL WB API WITH TOKENS for SKU {sku}...")
    try:
        res = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            prods = data.get('data', {}).get('products', [])
            if prods:
                p = prods[0]
                print(f"SUCCESS! Name: {p.get('name')} | Price: {p.get('salePriceU')/100}")
            else:
                print(f"FAILED: Result is empty. Data: {json.dumps(data)[:200]}")
        else:
            print(f"FAILED: Code {res.status_code}. Text: {res.text[:200]}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_internal_wb_api_with_session()
