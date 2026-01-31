import os, sys, time, random, json, re, threading, requests, io, shutil
from curl_cffi import requests as cffi_requests
# Force UTF-8 encoding for stdout and stderr to handle emojis and Russian text
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import undetected_chromedriver as uc
from dotenv import load_dotenv
import psycopg2
from core.lemana_utils import LEMANA_REGION_SUBDOMAINS, get_lemana_regional_url, kill_lemana_browsers
from datetime import datetime

load_dotenv()

# Import status tracker
try:
    from core.parser_status import set_status, mark_complete, mark_error
except ImportError:
    # Fallback if core is not in path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.parser_status import set_status, mark_complete, mark_error


# Define project root (parent of parsers/ directory)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

# --- Config ---
CHROME_PATH = find_chrome()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

class LemanaSilentParser:
    def __init__(self, profile_id=None):
        self.driver = None
        self.proxy_url = None
        self.profile = None
        if profile_id:
            self.profile = os.path.join(r"F:\Temp\chrome_profiles\lemana", f"profile_{profile_id}")
            if not os.path.exists(os.path.dirname(self.profile)):
                try: os.makedirs(os.path.dirname(self.profile), exist_ok=True)
                except: pass
        self._setup_proxy()
        
    def _setup_proxy(self):
        host = os.getenv('MOBILE_PROXY_HOST')
        port = os.getenv('MOBILE_PROXY_PORT')
        user = os.getenv('MOBILE_PROXY_USERNAME')
        pw = os.getenv('MOBILE_PROXY_PASSWORD')
        if host and port:
            self.proxy_url = f"http://{user}:{pw}@{host}:{port}"
            
    def start_driver(self, headless=True):
        """Initialize undetected chromedriver with speed optimizations."""
        print(f"[LEMANA] Using Chrome at: {CHROME_PATH} (Headless: {headless})")
        
        options = uc.ChromeOptions()
        if self.profile:
            options.add_argument(f"--user-data-dir={self.profile}")
        options.binary_location = CHROME_PATH
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=ru-RU")
        
        # User-Agent rotation
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(ua_list)}")
        
        # Speed optimizations
        options.add_argument("--disable-canvas-aa")
        options.add_argument("--disable-2d-canvas-clip-aa")
        options.add_argument("--disable-gl-drawing-for-tests")
        options.add_argument("--disable-webgl")
        options.add_argument("--mute-audio")
        
        # Enable images to capture useful screenshots for violations
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_settings.images": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

        if self.proxy_url:
            # Fix proxy_pool import path. Module is in parsers/proxies/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            proxy_dir = os.path.join(current_dir, "proxies")
            if os.path.exists(proxy_dir) and proxy_dir not in sys.path: 
                sys.path.append(proxy_dir)
            try:
                from proxy_pool import Proxy, ProxyPool
                p = Proxy(os.getenv('MOBILE_PROXY_HOST'), int(os.getenv('MOBILE_PROXY_PORT')), 
                          os.getenv('MOBILE_PROXY_USERNAME'), os.getenv('MOBILE_PROXY_PASSWORD'))
                pool = ProxyPool(healthcheck=False) 
                ext_path = pool.build_chrome_auth_extension(p)
                options.add_argument(f"--load-extension={ext_path}")
            except Exception as e:
                print(f"[LEMANA] Proxy extension error: {e}")

        # Substantial stagger start to avoid "thundering herd" on DNS/storage during massive regional startup
        stagger_wait = random.uniform(2.0, 20.0)
        time.sleep(stagger_wait)

        max_retries = 15 # Increased retries for stability
        for attempt in range(max_retries):
            try:
                major_version = get_chrome_major_version()
                port = random.randint(9500, 9999)
                self.driver = uc.Chrome(
                    options=options, 
                    browser_executable_path=CHROME_PATH,
                    version_main=major_version or 144,
                    port=port,
                    suppress_welcome=True,
                    headless=headless
                )
                self.driver.set_page_load_timeout(60) 
                return True
            except Exception as e:
                err_str = str(e)
                # Specific Windows errors for file locking or race conditions during UC patching
                if any(x in err_str for x in ["WinError 183", "WinError 32", "already exists", "occupied"]):
                    wait = random.uniform(1.0, 5.0)
                    time.sleep(wait)
                    continue
                
                # DNS / Connection errors (e.g., Errno 11001 / getaddrinfo failed)
                if "getaddrinfo" in err_str or "11001" in err_str:
                    wait = random.uniform(5.0, 15.0)
                    print(f"[LEMANA] DNS/Connection failure during start (Attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    continue

                print(f"[LEMANA] Browser start failed (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)
        return False

    def resolve_lemana_url(self, sku):
        """Resolves numeric SKU to full SEO URL on main domain to avoid regional 404s"""
        if not hasattr(self, 'url_cache'):
            self.url_cache = {}
            
        if sku in self.url_cache:
            return self.url_cache[sku]
            
        print(f"[LEMANA] Resolving slug for SKU {sku} on main domain...")
        main_url = f"https://lemanapro.ru/product/{sku}/"
        try:
            # We need the driver to be started
            if not self.driver:
                self.start_driver(headless=True)
                
            self.driver.get(main_url)
            time.sleep(3) # Small wait for redirect
            real_url = self.driver.current_url
            if '/product/' in real_url and any(c.isalpha() for c in real_url):
                self.url_cache[sku] = real_url
                print(f"[LEMANA] Resolved to: {real_url}")
                return real_url
        except Exception as e:
            print(f"[LEMANA] Resolution error for {sku}: {e}")
            
        return main_url

    def get_product_data(self, product_url, region_id=34):
        """
        Parses product data from Lemana Pro.
        :param product_url: Full URL or SKU
        :param region_id: Region ID (default 34 for Moscow)
        """
        if not product_url:
            return None
            
        # If it's just a numeric SKU, build the URL
        if str(product_url).strip().isdigit() and 'lemanapro.ru' not in str(product_url):
            sku = str(product_url).strip()
            url = f"https://lemanapro.ru/product/{sku}/"
        else:
            url = product_url
            # Extract SKU for logs/DB if possible
            sku_match = re.search(r'([0-9]+)/?$', url)
            sku = sku_match.group(1) if sku_match else "unknown"

        if str(url).strip().isdigit() or (url.startswith('https://') and url.strip('/').split('/')[-1].isdigit()):
            # If numeric SKU, resolve it to SEO slug on main domain first to avoid regional 404s
            sku_to_resolve = sku if sku else url.strip('/').split('/')[-1]
            resolved_url = self.resolve_lemana_url(sku_to_resolve)
            if resolved_url:
                url = resolved_url

        # Apply regional subdomain and fromRegion parameter
        url = get_lemana_regional_url(url, region_id)

        # print(f"[LEMANA] Parsing product: {url} (Region: {region_id})")
        
        if not self.driver:
            if not self.start_driver(): return None

        # Set regional cookie - hit product URL directly
        load_success = False
        for attempt in range(2):
            try:
                # First hit the URL
                self.driver.get(url) 
                time.sleep(random.uniform(2, 4))
                
                # Set cookie for BOTH variations to be safe
                for dom in ['.lemanapro.ru', '.lemana-pro.ru']:
                    try:
                        self.driver.execute_cdp_cmd('Network.setCookie', {
                            'domain': dom,
                            'name': 'regionId',
                            'value': str(region_id),
                            'path': '/'
                        })
                    except: pass
                
                # Refresh to apply cookie
                self.driver.refresh()
                time.sleep(random.uniform(7, 10)) # Stable wait for hydration
                load_success = True
                break # Success
            except Exception as e:
                if attempt == 0:
                    time.sleep(2)
                    continue
                else:
                    print(f"[LEMANA] Load Persistent Failure (Region {region_id}): {e}")
                    return None
        
        if not load_success: return None

        try:
            title = self.driver.title.lower()
            if "server error" in title or "доступ ограничен" in title:
                print(f"[LEMANA] Blocked/Error (Region {region_id}): {title}")
                return None

            # Get current HTML and URL
            html = self.driver.page_source
            current_url = self.driver.current_url
            
            # Method 1: Meta tags (Og/Product schemas) - Very fast
            try:
                price_meta = self.driver.find_elements("xpath", "//meta[@property='product:price:amount'] | //meta[@name='twitter:data1']")
                for m in price_meta:
                    p = m.get_attribute("content") or m.get_attribute("value")
                    if p:
                        p_cleaned = "".join(filter(lambda x: x.isdigit() or x in ".,", p)).replace(',', '.')
                        if p_cleaned:
                            return {
                                "sku": sku,
                                "price": float(p_cleaned),
                                "name": self.driver.title.split('-')[0].strip(),
                                "url": current_url
                            }
            except: pass
                
            # Fallback 1: JSON-LD (Most robust)
            try:
                json_ld_scripts = self.driver.find_elements("xpath", "//script[@type='application/ld+json']")
                for script in json_ld_scripts:
                    try:
                        ld_text = script.get_attribute("innerHTML")
                        if not ld_text: continue
                        ld_data = json.loads(ld_text)
                        objects = ld_data if isinstance(ld_data, list) else [ld_data]
                        for obj in objects:
                            if isinstance(obj, dict) and obj.get("@graph"): 
                                objects.extend(obj.get("@graph"))
                            if isinstance(obj, dict) and obj.get("@type") == "Product":
                                offers = obj.get("offers")
                                if isinstance(offers, dict) and offers.get("price"):
                                    p_val = str(offers["price"]).replace(',', '.').replace(' ', '')
                                    p_val = "".join(c for c in p_val if c.isdigit() or c == '.')
                                    return {
                                        "sku": sku,
                                        "price": float(p_val),
                                        "name": obj.get("name", ""),
                                        "url": current_url
                                    }
                    except: continue
            except Exception as e:
                print(f"[LEMANA] JSON-LD error: {e}")
                
            # Fallback 2: Visual elements (last resort for dynamic pages)
            try:
                # Look for price strings in common containers
                price_elems = self.driver.find_elements("xpath", "//span[contains(@class, 'price')] | //div[contains(@data-qa, 'price')]")
                for elem in price_elems:
                    text = elem.text.strip()
                    if text:
                        p_cleaned = "".join(filter(lambda x: x.isdigit(), text))
                        if p_cleaned and 2 < len(p_cleaned) < 10: # Sanity check for price length
                            return {
                                "sku": sku,
                                "price": float(p_cleaned),
                                "name": self.driver.title.split('-')[0].strip(),
                                "url": current_url
                            }
            except: pass

            # Fallback 3: Regex in page source
            price_match = re.search(r'"price":\s*"?([\d\s\.,]+)"?', html)
            name_match = re.search(r'"name":\s*"([^"]+)"', html)
            if price_match and name_match:
                try:
                    p_text = price_match.group(1).replace(',', '.').replace(' ', '')
                    p_text = "".join(c for c in p_text if c.isdigit() or c == '.')
                    return {
                        "sku": sku,
                        "price": float(p_text),
                        "name": name_match.group(1),
                        "url": current_url
                    }
                except: pass
                
            return None
        except Exception as e:
            print(f"[LEMANA] Error processing {product_url}: {e}")
            return None

    def save_to_db(self, sku, price, stock, name=None, region_id=34, url=None, violation=False, screenshot=None):
        """Saves parsed data to the database."""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO public.lemana_prices (
                    sku, price, stock, name, last_updated, region_id, url, 
                    competitor_name, violation_detected, violation_screenshot
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, 'Lemana Pro', %s, %s)
                ON CONFLICT (sku, competitor_name, region_id) 
                DO UPDATE SET 
                    price = EXCLUDED.price,
                    stock = EXCLUDED.stock,
                    name = COALESCE(EXCLUDED.name, lemana_prices.name),
                    last_updated = CURRENT_TIMESTAMP,
                    url = COALESCE(EXCLUDED.url, lemana_prices.url),
                    violation_detected = EXCLUDED.violation_detected,
                    violation_screenshot = EXCLUDED.violation_screenshot
            """, (sku, price, stock, name, region_id, url, violation, screenshot))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[LEMANA] DB Save error: {e}")
            return False

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def process_region_task(skus_list, region_id, headless=True):
    """Worker function to process all SKUs for a single region."""
    # User F: drive for profiles to save space on C:
    profile_base = r"F:\Temp\chrome_profiles\lemana"
    if not os.path.exists(profile_base):
        try: os.makedirs(profile_base, exist_ok=True)
        except: pass
    
    # Stagger starts to avoid literal "thundering herd" on start
    time.sleep(random.uniform(1, 15))
    
    parser = LemanaSilentParser(profile_id=region_id)
    try:
        if not parser.start_driver(headless=headless):
            return False
            
        # print(f"[LEMANA] Worker started for Region ID: {region_id}")
        total_items = len(skus_list)
        for idx, item in enumerate(skus_list, 1):
            # Update progress status (simple per-region update for now)
            # In a more complex setup, we'd aggregate across regions
            if region_id == 34: # Main region update
                set_status('lemana', idx, total_items)
                
            sku = item['sku']
            url = item.get('url') or sku
            ric_price = item.get('ric_leroy_price')
            
            # Start timer for product
            start_t = time.time()
            data = parser.get_product_data(url, region_id=region_id)
            if data:
                price = data['price']
                violation = False
                screenshot_rel_path = None
                
                # Violation detection: price < ric_price
                if ric_price and float(price) < float(ric_price):
                    violation = True
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_dir = os.path.join(ROOT_DIR, 'static', 'screenshots', 'lemana')
                    if not os.path.exists(screenshot_dir):
                        os.makedirs(screenshot_dir, exist_ok=True)
                    
                    filename = f"violation_{sku}_{region_id}_{timestamp}.png"
                    screenshot_path = os.path.join(screenshot_dir, filename)
                    
                    try:
                        parser.driver.save_screenshot(screenshot_path)
                        # Relative path for the web app/Excel
                        screenshot_rel_path = f"static/screenshots/lemana/{filename}"
                        print(f"[VIOLATION] 📸 Screenshot saved for {sku}: {price} < {ric_price}")
                    except Exception as e:
                        print(f"[ERROR] Failed to take screenshot: {e}")
                
                parser.save_to_db(
                    sku, price, 1, 
                    name=data['name'], 
                    region_id=region_id, 
                    url=data.get('url'),
                    violation=violation,
                    screenshot=screenshot_rel_path
                )
                
                elapsed = time.time() - start_t
                status_msg = "VIOLATION" if violation else "OK"
                print(f"[LEMANA] {status_msg} (Region {region_id}): {sku} -> {price} руб. ({elapsed:.1f}s)")
            else:
                # Capture failures without verbose snippets unless critical
                print(f"[LEMANA] FAIL (Region {region_id}): {sku}")
                
            # Add random sleep between items to avoid detection and reduce load
            time.sleep(random.uniform(1.0, 3.0))
            
    except Exception as e:
        print(f"[LEMANA] Worker Error (Region {region_id}): {e}")
    finally:
        parser.close()

def run_lemana_parsing(skus_list, region_ids=[34], max_workers=20, headless=True):
    """Entry point for parallel regional parsing."""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    
    print(f"[LEMANA] Starting parallel parsing: {len(skus_list)} items, {len(region_ids)} regions, {max_workers} workers")
    start_total = time.time()
    
    # Process regions in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_region_task, skus_list, rid, headless): rid for rid in region_ids}
        
        for future in as_completed(futures):
            rid = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[LEMANA] Region {rid} future error: {e}")
                
    total_elapsed = time.time() - start_total
    print(f"[LEMANA] Parallel parsing finished in {total_elapsed/60:.1f} minutes.")
    
    # Final cleanup to ensure no orphan processes
    kill_lemana_browsers()
    
    # Mark as complete
    mark_complete('lemana')

if __name__ == "__main__":
    # Test
    test_skus = [{"sku": "90240393", "competitor": "Lemana_Test", "sp_code": "TEST-123"}]
    run_lemana_parsing(test_skus)
