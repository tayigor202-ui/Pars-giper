import requests
import re

sku = "504869177"
url = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

try:
    res = requests.get(url, headers=headers, timeout=10)
    print(f"Page Status: {res.status_code}")
    if res.status_code == 200:
        # Search for JS variables
        nm_match = re.search(r'"nmId":\s*(\d+)', res.text)
        dest_match = re.search(r'dest=(\d+)', res.text)
        regions_match = re.search(r'regions=([\d,]+)', res.text)
        
        print(f"Found nmId: {nm_match.group(1) if nm_match else 'None'}")
        print(f"Found dest in HTML: {dest_match.group(1) if dest_match else 'None'}")
        print(f"Found regions in HTML: {regions_match.group(1) if regions_match else 'None'}")
        
        if not nm_match:
            # Try SSR data
            ssr_match = re.search(r'window\.__SSR_DATA__\s*=\s*(\{.*?\});', res.text)
            if ssr_match:
                print("Found SSR Data!")
except Exception as e:
    print(f"Error: {e}")
