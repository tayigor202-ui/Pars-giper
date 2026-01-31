import os
import time
import random
import re
import json
import psycopg2
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Add project root to sys.path
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from core.ym_utils import YM_REGION_NAMES, get_ym_search_url, YM_ALL_REGION_IDS
from core.status_utils import set_status, mark_complete

load_dotenv()

class YandexMarketParser:
    def __init__(self, region_id=213, city_name=None):
        self.region_id = region_id
        self.city_name = city_name or YM_REGION_NAMES.get(region_id, "moscow")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.proxy = self._setup_proxy()
        
    def _setup_proxy(self):
        # MangoProxy logic from guide: user-yourlogin-city-moscow
        # Using environment variables for base credentials
        host = "p1.mangoproxy.com"
        port = 2333
        # In a real scenario, these would be in .env. 
        # Using placeholders if not found.
        user_base = os.getenv('MANGO_PROXY_USER', 'user-placeholder')
        password = os.getenv('MANGO_PROXY_PASS', 'pass-placeholder')
        
        # City-specific targeting
        target_city = self.city_name.lower().replace(" ", "")
        username = f"{user_base}-city-{target_city}"
        
        return {
            "server": f"http://{host}:{port}",
            "username": username,
            "password": password
        }

    def start(self, headless=True):
        self.playwright = sync_playwright().start()
        
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-position=0,0',
            '--ignore-certifcate-errors',
            '--ignore-certifcate-errors-spki-list',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ]
        
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=launch_args,
            proxy=self.proxy
        )
        
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ]
        
        self.context = self.browser.new_context(
            user_agent=random.choice(ua_list),
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Set Region Cookie
        self.context.add_cookies([{
            'name': 'yandex_gid', 
            'value': str(self.region_id), 
            'domain': '.yandex.ru', 
            'path': '/'
        }])
        
        self.page = self.context.new_page()
        
        # CSS Injection to hide popups
        self.page.add_init_script("""
            const style = document.createElement('style');
            style.innerHTML = `
                div[data-apiary-widget-name="@light/Popup"],
                div[aria-label="Закрыть"],
                .CheckboxCaptcha,
                .gdpr-popup-overlay,
                .gdpr-popup,
                div[class*='gdpr'],
                div[class*='cookie'],
                .popup2 {
                    display: none !important; 
                    visibility: hidden !important; 
                    pointer-events: none !important;
                }
            `;
            document.head.appendChild(style);
        """)

    def stop(self):
        if self.page: self.page.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()

    def clean_price(self, price_str):
        if not price_str: return None
        # Extract digits
        digits = re.sub(r'[^\d]', '', price_str)
        return int(digits) if digits else None

    def get_product_data(self, query):
        url = get_ym_search_url(query)
        print(f"[YM] Searching: {query} in Region {self.region_id}")
        
        try:
            self.page.goto(url, wait_until='domcontentloaded', timeout=45000)
            # Short wait for any dynamic price load
            time.sleep(random.uniform(2, 4))
            
            # Selectors from guide
            price_container_sel = "[data-auto='snippet-price-current']"
            old_price_sel = "[data-auto='snippet-price-old']"
            
            # Check for Captain / Bot detection
            if "captcha" in self.page.url.lower() or self.page.query_selector(".CheckboxCaptcha"):
                print(f"[YM] CAPTCHA detected for {query}")
                return {"status": "ANTIBOT"}

            price_els = self.page.query_selector_all(price_container_sel)
            if not price_els:
                print(f"[YM] No products found for {query}")
                return {"status": "NOT_FOUND"}

            # Take the first snippet as the most relevant
            first_price_el = price_els[0]
            price_text = first_price_el.inner_text().lower()
            
            data = {
                "sku": query,
                "name": "---",
                "price_base": None,
                "price_pay": None,
                "price_old": None,
                "status": "OK",
                "url": self.page.url
            }

            # Try to get product name from the snippet
            name_el = self.page.query_selector("[data-auto='snippet-title-product'], [data-auto='snippet-title']")
            if name_el:
                data["name"] = name_el.inner_text().strip()

            # Logic for Pay vs Base price
            if "пэй" in price_text or "pay" in price_text:
                data["price_pay"] = self.clean_price(price_text)
                
                # Try to click to find base price
                try:
                    # Look for a button or interactive element in the price container
                    btn = first_price_el.query_selector("button, div[role='button']")
                    if btn:
                        btn.click()
                        time.sleep(1)
                        # Look for "без карты" text in the newly rendered content
                        popup_text = self.page.content()
                        # This is tricky without knowing the exact popup structure, 
                        # but we search for price near "без карты"
                        matches = re.findall(r'(\d[\d\s]*)\s*₽\s*без\s*карты', popup_text)
                        if matches:
                            data["price_base"] = self.clean_price(matches[0])
                except:
                    pass
            else:
                data["price_base"] = self.clean_price(price_text)

            # Old price
            old_price_el = self.page.query_selector(old_price_sel)
            if old_price_el:
                data["price_old"] = self.clean_price(old_price_el.inner_text())

            return data

        except Exception as e:
            print(f"[YM] Error parsing {query}: {e}")
            return {"status": "ERROR"}

    def save_to_db(self, data):
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO ym_prices (
                    sku, region_id, name, price_base, price_pay, price_old, 
                    url, last_updated, status, competitor_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Yandex Market')
                ON CONFLICT (sku, competitor_name, region_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    price_base = EXCLUDED.price_base,
                    price_pay = EXCLUDED.price_pay,
                    price_old = EXCLUDED.price_old,
                    url = EXCLUDED.url,
                    last_updated = EXCLUDED.last_updated,
                    status = EXCLUDED.status
            """, (
                data['sku'], self.region_id, data['name'], 
                data.get('price_base'), data.get('price_pay'), data.get('price_old'),
                data.get('url'), datetime.now(), data.get('status')
            ))
            
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"[YM] DB Error: {e}")
        finally:
            if conn: conn.close()

if __name__ == "__main__":
    # Test run
    parser = YandexMarketParser(region_id=213) # Moscow
    try:
        parser.start(headless=False)
        res = parser.get_product_data("90240393")
        print(f"Result: {res}")
        if res.get("status") == "OK":
            parser.save_to_db(res)
    finally:
        parser.stop()

def process_ym_region_task(skus_list, region_id, headless=True):
    """Worker function to process all SKUs for a single region."""
    # Stagger starts to avoid literal "thundering herd" on start
    time.sleep(random.uniform(1, 15))
    
    city_name = YM_REGION_NAMES.get(region_id, "moscow")
    parser = YandexMarketParser(region_id=region_id, city_name=city_name)
    try:
        parser.start(headless=headless)
        
        total_items = len(skus_list)
        for idx, item in enumerate(skus_list, 1):
            # Update progress status for the first region (or aggregate if needed)
            if region_id == 213: # Moscow as primary reference
                set_status('ym', idx, total_items)
                
            sku = item['sku']
            data = parser.get_product_data(sku)
            if data:
                parser.save_to_db(data)
                status_msg = data.get('status', 'OK')
                print(f"[YM] {status_msg} (Region {region_id}): {sku} ({idx}/{total_items})")
            else:
                print(f"[YM] FAIL (Region {region_id}): {sku}")
                
            # Random sleep between items
            time.sleep(random.uniform(2.0, 5.0))
            
    except Exception as e:
        print(f"[YM] Worker Error (Region {region_id}): {e}")
    finally:
        parser.stop()

def run_ym_parsing(skus_list, region_ids=[213], max_workers=5, headless=True):
    """Entry point for parallel regional YM parsing."""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    
    print(f"[YM] Starting parallel parsing: {len(skus_list)} items, {len(region_ids)} regions, {max_workers} workers")
    start_total = time.time()
    
    # Process regions in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_ym_region_task, skus_list, rid, headless): rid for rid in region_ids}
        
        for future in as_completed(futures):
            rid = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[YM] Region {rid} future error: {e}")
                
    total_elapsed = time.time() - start_total
    print(f"[YM] YM Parallel parsing finished in {total_elapsed/60:.1f} minutes.")
    
    # Mark as complete
    mark_complete('ym')
