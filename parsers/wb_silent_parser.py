import os, sys, time, random, json, re, threading, requests, io, shutil
# Force UTF-8 encoding for stdout and stderr to handle emojis and Russian text
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import undetected_chromedriver as uc
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

load_dotenv()

# Import status tracker
try:
    from core.parser_status import set_status, mark_complete, mark_error
except ImportError:
    # Fallback if core is not in path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.parser_status import set_status, mark_complete, mark_error


def find_chrome():
    """Find chrome executable automatically"""
    env_path = os.getenv('CHROME_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
        
    # Common Windows paths
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
            
    # Check PATH
    path_chrome = shutil.which('chrome')
    if path_chrome:
        return path_chrome
        
    return "chrome.exe" # Fallback to default

# --- Config ---
CHROME_PATH = find_chrome()

def get_chrome_major_version():
    """Detect installed Chrome major version on Windows."""
    try:
        import subprocess
        cmd = 'powershell -Command "(Get-Item \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\').VersionInfo.ProductVersion"'
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        if output:
            return int(output.split('.')[0])
    except:
        pass
    return None
WB_INTERNAL_API = "https://www.wildberries.ru/__internal/u-card/cards/v4/detail"
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

class WildberriesSilentParser:
    def __init__(self):
        self.session = requests.Session()
        self.cookies = {}
        self.ua = ""
        self.spa_version = "13.20.2"
        self.proxy_url = None
        self._setup_proxy()
        
    def _setup_proxy(self):
        host = os.getenv('MOBILE_PROXY_HOST')
        port = os.getenv('MOBILE_PROXY_PORT')
        user = os.getenv('MOBILE_PROXY_USERNAME')
        pw = os.getenv('MOBILE_PROXY_PASSWORD')
        if host and port:
            self.proxy_url = f"http://{user}:{pw}@{host}:{port}"
            # self.session.proxies = {"http": self.proxy_url, "https": self.proxy_url}
            print(f"[SILENT] Proxy found in env but DISABLED for API (using Direct Connection)")

    def warmup(self):
        """Warmup session to get fresh tokens."""
        print(f"[SILENT] Using Chrome at: {CHROME_PATH}")
        print("[SILENT] Starting browser session to get WB tokens...")
        
        options = uc.ChromeOptions()
        options.binary_location = CHROME_PATH
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--lang=ru-RU")
        
        # Setup proxy for warmup if available
        proxy_dir = os.path.abspath(os.path.join(os.getcwd(), "proxies"))
        if proxy_dir not in sys.path: sys.path.append(proxy_dir)
        try:
            from proxy_pool import Proxy, ProxyPool
            p = Proxy(os.getenv('MOBILE_PROXY_HOST'), int(os.getenv('MOBILE_PROXY_PORT')), 
                      os.getenv('MOBILE_PROXY_USERNAME'), os.getenv('MOBILE_PROXY_PASSWORD'))
            pool = ProxyPool(healthcheck=False) 
            ext_path = pool.build_chrome_auth_extension(p)
            options.add_argument(f"--load-extension={ext_path}")
        except: pass

        # Setup profile on F: drive
        profile_dir = r"F:\Temp\chrome_profiles\wb_warmup"
        if not os.path.exists(profile_dir):
            try: os.makedirs(profile_dir, exist_ok=True)
            except: pass
        options.add_argument(f"--user-data-dir={profile_dir}")

        driver = None
        max_retries = 10
        major_version = get_chrome_major_version()
        
        for attempt in range(max_retries):
            try:
                # Random port like in Ozon to avoid conflicts
                port = random.randint(9300, 9500)
                driver = uc.Chrome(
                    options=options, 
                    browser_executable_path=CHROME_PATH,
                    driver_executable_path=None,
                    version_main=major_version or 144,
                    port=port,
                    suppress_welcome=True
                )
                break # Success
            except Exception as e:
                err_str = str(e)
                if "WinError 183" in err_str or "WinError 32" in err_str or "already exists" in err_str or "occupied" in err_str:
                    wait = random.uniform(2, 5)
                    print(f"[SILENT] Driver lock detected (Attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    continue
                
                print(f"[SILENT] ❌ Warmup ERROR (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)
        
        try:
            if not driver: return False
            driver.set_page_load_timeout(30)
            driver.get("https://www.wildberries.ru")
            time.sleep(10)
            
            # Navigate to generic product to ensure all tokens are baked
            driver.get("https://www.wildberries.ru/catalog/504869177/detail.aspx")
            time.sleep(15)
            
            cookies = driver.get_cookies()
            self.cookies = {c['name']: c['value'] for c in cookies}
            self.ua = driver.execute_script("return navigator.userAgent;")
            
            if 'x_wbaas_token' in self.cookies:
                print(f"[SILENT] ✅ Tokens captured successfully.")
                return True
            else:
                print(f"[SILENT] ⚠️ Token 'x_wbaas_token' missing. Retrying might be needed.")
                return True # Try anyway with cookies
        except Exception as e:
            print(f"[SILENT] ❌ Warmup ERROR: {e}")
            return False
        finally:
            if driver: driver.quit()

    def fetch_price(self, sku):
        """Direct API call with token reuse."""
        params = {
            "appType": 1, "curr": "rub", "dest": "-1257786",
            "spp": 30, "hide_vflags": "4294967296",
            "hide_dtype": 9, "ab_testing": "false",
            "lang": "ru", "nm": sku
        }
        headers = {
            "User-Agent": self.ua,
            "Accept": "*/*",
            "Referer": f"https://www.wildberries.ru/catalog/{sku}/detail.aspx",
            "x-requested-with": "XMLHttpRequest",
            "x-spa-version": self.spa_version
        }
        
        try:
            resp = self.session.get(WB_INTERNAL_API, params=params, headers=headers, cookies=self.cookies, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                # Check root first, then data.products
                prods = data.get('products') or data.get('data', {}).get('products', [])
                if prods:
                    p = prods[0]
                    # Check stock in sizes
                    sizes = p.get('sizes', [])
                    if not sizes:
                        return {'status': 'OUT_OF_STOCK'}
                        
                    # Usually first size has the price for single items
                    size = sizes[0]
                    stocks = size.get('stocks', [])
                    
                    if not stocks:
                         return {'status': 'OUT_OF_STOCK'}
                         
                    price_data = size.get('price')
                    if not price_data:
                        # Sometimes price is missing if out of stock but stocks not empty? Rare.
                        return {'status': 'OUT_OF_STOCK'}

                    sale_price = price_data.get('product', 0) / 100
                    orig_price = price_data.get('basic', 0) / 100
                    # 'total' is often the price before WB Wallet discount but after promo codes
                    nocard_price = price_data.get('total', sale_price * 100) / 100
                    
                    return {
                        'status': 'OK',
                        'price_card': sale_price,
                        'price_nocard': nocard_price,
                        'price_old': orig_price,
                        'product_name': p.get('name')
                    }
                return {'status': 'NOT_FOUND'}
            elif resp.status_code in [498, 403]:
                return {'status': 'EXPIRED'}
            else:
                 return {'status': f"HTTP_{resp.status_code}", 'msg': resp.text[:100]}
        except Exception as e:
            return {'status': 'ERROR', 'msg': str(e)}
        return {'status': 'FAIL', 'code': resp.status_code}

def save_to_db(data):
    """Reliable DB saving matching Ozon logic with SAVEPOINTS."""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        try:
            cur.execute("SAVEPOINT sp_wb")
            cur.execute("""
                INSERT INTO public.wb_prices (sku, name, competitor_name, price_card, price_nocard, price_old, status, created_at, sp_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                ON CONFLICT (sku, competitor_name) 
                DO UPDATE SET 
                    price_card = EXCLUDED.price_card,
                    price_nocard = EXCLUDED.price_nocard,
                    price_old = EXCLUDED.price_old,
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    sp_code = EXCLUDED.sp_code,
                    created_at = NOW()
            """, (
                str(data['sku']), 
                data.get('product_name'), 
                data['competitor_name'],
                data.get('price_card'), 
                data.get('price_nocard'),
                data.get('price_old'), 
                data.get('status'),
                data.get('sp_code')
            ))
            cur.execute("RELEASE SAVEPOINT sp_wb")
            conn.commit()
        except Exception as inner_e:
            cur.execute("ROLLBACK TO SAVEPOINT sp_wb")
            print(f"[DB ERROR] In-trans SKU {data['sku']}: {inner_e}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Connection SKU {data['sku']}: {e}")

def run_wb_silent_parsing(items_to_parse=None):
    parser = WildberriesSilentParser()
    if not parser.warmup():
        print("[SILENT] Failed to start. Warmup unsuccessful.")
        return

    # Load from DB or use provided list
    if items_to_parse:
        items = []
        for item in items_to_parse:
            if isinstance(item, dict):
                items.append((item.get('sku'), item.get('competitor_name', 'Wildberries'), item.get('sp_code', '---')))
            else:
                items.append((str(item), 'Wildberries', '---'))
        print(f"[SILENT] Targeted parsing requested for {len(items)} items.")
    else:
        # Load from DB - ONLY items with valid SKU
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("SELECT sku, competitor_name, sp_code FROM public.wb_prices WHERE sku IS NOT NULL AND sku != ''")
            items = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[SILENT] DB Load Error: {e}")
            return

    print(f"[SILENT] Starting parsing for {len(items)} items...")
    
    for idx, (sku, comp_name, sp_code) in enumerate(items, 1):
        # Update progress status
        set_status('wb', idx, len(items))
        
        print(f"[{idx}/{len(items)}] WB SKU {sku}...", end=' ', flush=True)
        res = parser.fetch_price(sku)
        
        if res['status'] == 'EXPIRED':
            print("Token expired! Re-warming...", end=' ')
            parser.warmup()
            res = parser.fetch_price(sku)

        res['sku'] = sku
        res['competitor_name'] = comp_name
        res['sp_code'] = sp_code
        
        if res['status'] == 'OK':
            print(f"OK! {res['price_card']} / {res.get('price_nocard')} / {res.get('price_old')} руб.")
            save_to_db(res)
        else:
            msg = res.get('msg', '')
            print(f"FAILED ({res['status']}) {msg}")
            save_to_db(res)
            
        time.sleep(random.uniform(0.1, 0.5)) # Fast mode active!
    
    # Mark as complete
    mark_complete('wb')
    
    cleanup_resources()

def cleanup_resources():
    print("\n[CLEANUP] Cleaning up temporary files and processes...")
    
    # Files to remove
    temp_files = ["session_data.json", "network_logs.json", "debug_api_*.json"]
    for f in temp_files:
        try:
            # Simple glob support if needed, but for now exact or pre-known
            if '*' in f:
                import glob
                for gf in glob.glob(f):
                    try: os.remove(gf)
                    except: pass
            else:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"[CLEANUP] Removed {f}")
        except Exception as e:
            print(f"[CLEANUP] Error removing {f}: {e}")

    # Kill chrome processes to free memory
    try:
        if os.name == 'nt':
            os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
            os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
            print("[CLEANUP] Browser processes terminated.")
    except: pass

if __name__ == "__main__":
    try:
        run_wb_silent_parsing()
    finally:
        cleanup_resources()
