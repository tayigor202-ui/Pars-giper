
import os
import time
import psycopg2
import requests
import io
import re
import json
import random
import shutil
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

OUR_STORE_NAME = 'Ссылка на наш магазин'
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USE_HEADLESS = True

# --- BROWSER UTILS (COPIED FROM MAIN PARSER) ---

ip_timezone_cache = {}
ip_cache_lock = threading.Lock()

def get_ip_geolocation(ip):
    try:
        response=requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,city,timezone',timeout=5)
        if response.status_code==200:
            data=response.json()
            if data.get('status')=='success':
                return {'country':data.get('country','Russia'),'city':data.get('city','Moscow'),'timezone':data.get('timezone','Europe/Moscow')}
    except:
        pass
    return {'country':'Russia','city':'Moscow','timezone':'Europe/Moscow'}

def get_timezone_offset(timezone_name):
    timezone_offsets={'Europe/Moscow':-180,'Europe/Kaliningrad':-120,'Europe/Samara':-240,'Asia/Yekaterinburg':-300,'Asia/Omsk':-360,'Asia/Krasnoyarsk':-420,'Asia/Irkutsk':-480,'Asia/Yakutsk':-540,'Asia/Vladivostok':-600,'Asia/Magadan':-660,'Asia/Kamchatka':-720}
    return timezone_offsets.get(timezone_name,-180)

def get_timezone_for_ip(ip):
    with ip_cache_lock:
        if ip in ip_timezone_cache:
            return ip_timezone_cache[ip]
    geo=get_ip_geolocation(ip)
    timezone_name=geo.get('timezone','Europe/Moscow')
    offset=get_timezone_offset(timezone_name)
    with ip_cache_lock:
        ip_timezone_cache[ip]={'offset':offset,'name':timezone_name,'city':geo.get('city','Moscow')}
    return ip_timezone_cache[ip]

def generate_random_user_agent():
    chrome_versions=['131.0.6778.86','131.0.6778.85','131.0.6778.70','131.0.6778.69']
    chrome_ver=random.choice(chrome_versions)
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36'

def start_chrome(port,unique_id=None,user_agent=None,proxy_host=None,proxy_port=None):
    if unique_id is None:
        unique_id=port
    profile=f"C:\\Temp\\chrome_profiles\\ozon\\violation_p{port}"
    # Clean previous profile to ensure fresh start
    shutil.rmtree(profile, ignore_errors=True)
    Path(profile).mkdir(parents=True,exist_ok=True)
    
    if not user_agent:
        user_agent=generate_random_user_agent()
    # FORCE HD RESOLUTION for better visibility as per user request
    window_size='1920,1080'
    
    cmd=[CHROME_PATH,
         f"--remote-debugging-port={port}",
         f"--user-data-dir={profile}",
         f"--user-agent={user_agent}",
         f"--window-size={window_size}",
         f"--proxy-server=http://{proxy_host}:{proxy_port}",
         f"--proxy-bypass-list=<-loopback>",
         "--no-sandbox",
         "--disable-blink-features=AutomationControlled",
         "--disable-features=IsolateOrigins,site-per-process",
         "--disable-web-security",
         "--no-first-run",
         "--no-default-browser-check",
         "--disable-popup-blocking",
         "--disable-infobars",
         "--disable-notifications",
         "--disable-default-apps",
         "--lang=ru-RU",
         "--disable-dev-shm-usage",
         "--disable-gpu",
         "--disable-software-rasterizer",
         "--disable-component-extensions-with-background-pages",
         "--disable-background-networking",
         "--disable-sync",
         "--disable-translate",
         "--hide-scrollbars",
         "--metrics-recording-only",
         "--mute-audio",
         "--no-pings",
         "--safebrowsing-disable-auto-update",
         "--disable-domain-reliability",
         "--disable-background-timer-throttling",
         "--disable-backgrounding-occluded-windows",
         "--disable-renderer-backgrounding",
         "--disable-ipc-flooding-protection",
         "--blink-settings=imagesEnabled=true"] # Enable images for screenshots!
         
    if USE_HEADLESS:
        cmd.insert(6,"--headless=new")
        
    print(f"[VIOLATION_CHECK] Chrome Launching on port {port} with proxy {proxy_host}:{proxy_port}")
    proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return proc,profile

def check_current_ip(driver):
    try:
        driver.execute_script("window.open('https://httpbin.org/ip','_blank');")
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        try:
            WebDriverWait(driver,10).until(lambda d:d.find_element(By.TAG_NAME,'body').text.strip()!='')
        except:
            pass
        body_text=driver.find_element(By.TAG_NAME,'body').text
        try:
            ip_data=json.loads(body_text)
            ip=ip_data.get('origin','Unknown').split(',')[0].strip()
        except:
            ip='Unknown'
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return ip
    except Exception as e:
        print(f"[VIOLATION_CHECK] IP Check Error: {e}")
        try:
            if len(driver.window_handles)>1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return 'Error'

def attach_selenium_with_proxy(port):
    for attempt in range(3):
        try:
            opts=Options()
            opts.add_experimental_option("debuggerAddress",f"127.0.0.1:{port}")
            driver=webdriver.Chrome(options=opts)
            
            # Setup environment similar to production
            # current_ip=check_current_ip(driver)
            timezone_offset=-180
            # if current_ip and current_ip not in ['Error','Unknown']:
            #      tz_info=get_timezone_for_ip(current_ip)
            #      timezone_offset=tz_info['offset']
             
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':f'''Object.defineProperty(navigator,'webdriver',{{get:()=>undefined}});Object.defineProperty(navigator,'languages',{{get:()=>['ru-RU','ru']}});Object.defineProperty(navigator,'language',{{get:()=>'ru-RU'}});Date.prototype.getTimezoneOffset=function(){{return {timezone_offset};}};window.chrome={{runtime:{{}}}};const origQuery=window.navigator.permissions.query;window.navigator.permissions.query=(params)=>(params.name==='notifications'?Promise.resolve({{state:'prompt'}}):origQuery(params));'''})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders',{'headers':{'Accept-Language':'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7','Upgrade-Insecure-Requests':'1'}})
            
            return driver
        except:
            time.sleep(2)
    return None

def get_violations():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # New Logic: Group by SP-Code
        # 1. Fetch all prices
        cursor.execute("""
            SELECT sku, competitor_name, price_nocard, sp_code, name
            FROM public.prices 
            WHERE sp_code IS NOT NULL AND sp_code != ''
        """)
        rows = cursor.fetchall()
        conn.close()
        
        groups = {}
        for r in rows:
            r_sku, r_comp, r_price_str, r_sp, r_name = r
            
            if not r_sp: continue
            
            # Clean Price
            try:
                clean_price_str = re.sub(r'[^\\d.]', '', str(r_price_str).replace(',', '.'))
                if not clean_price_str: continue
                price_val = float(clean_price_str)
            except: continue

            if r_sp not in groups:
                groups[r_sp] = {'our_price': None, 'our_key': None, 'competitors': []}
                
            # Identify "Our Store"
            is_ours = False
            if 'наш магазин' in r_comp.lower() or 'my store' in r_comp.lower():
                is_ours = True
                
            if is_ours:
                groups[r_sp]['our_price'] = price_val
                groups[r_sp]['our_sku'] = r_sku
            else:
                groups[r_sp]['competitors'].append({
                    'sku': r_sku,
                    'competitor_name': r_comp,
                    'price': price_val,
                    'name': r_name
                })
        
        violations = []
        for sp_code, data in groups.items():
            our_price = data['our_price']
            if not our_price: continue
            
            for comp in data['competitors']:
                comp_price = comp['price']
                if comp_price < our_price:
                    diff = our_price - comp_price
                    violations.append({
                        'sku': comp['sku'], # Target SKU to open
                        'competitor': comp['competitor_name'],
                        'our_price': our_price,
                        'comp_price': comp_price, # Renamed to standard
                        'diff': diff,
                        'sp_code': sp_code
                    })
                    
        return violations
    except Exception as e:
        print(f"[VIOLATION_CHECK] DB Error: {e}")
        return []

def process_and_send(driver, violation):
    sku = violation['sku']
    url = f"https://www.ozon.ru/product/{sku}/"
    print(f"[VIOLATION_CHECK] Processing violation for SKU {sku} ({violation['competitor']})...")
    
    try:
        driver.get(url)
        time.sleep(random.uniform(3.0, 5.0))
        
        for attempt in range(2):
            if attempt > 0:
                 print(f"[VIOLATION_CHECK] Attempt {attempt+1} to load page...")
            try:
                 WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            except:
                 pass

            driver.execute_script("document.body.style.zoom='0.65'")
            time.sleep(2)

            real_seller = "Unknown"
            seller_element = None
            
            # 1. IMMEDIATE CHECK
            try:
                 top_selectors = [
                    {"sel": "//a[contains(text(), 'Перейти в магазин')]/../div", "by": By.XPATH, "color": "purple"},
                    {"sel": "//div[contains(text(), 'Перейти в магазин')]/preceding-sibling::div", "by": By.XPATH, "color": "purple"},
                    {"sel": "//div[@data-widget='webState']//span[contains(text(), 'официальный магазин')]", "by": By.XPATH, "color": "purple"}
                 ]
                 for cfg in top_selectors:
                     try:
                         els = driver.find_elements(cfg["by"], cfg["sel"])
                         for el in els:
                             if el.is_displayed() and el.text.strip():
                                 real_seller = el.text.strip()
                                 seller_element = el
                                 driver.execute_script("arguments[0].style.border='5px solid purple'; arguments[0].style.backgroundColor='yellow';", seller_element)
                                 break
                         if real_seller != "Unknown": break
                     except: pass
            except: pass

            # 2. IF NOT FOUND, SCROLL AND SEARCH DEEP
            if real_seller == "Unknown":
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1.5)
                try:
                    selectors_config = [
                        {"sel": "//div[contains(text(), 'Доставка')]/..//following-sibling::div//*[string-length(text()) > 0]", "by": By.XPATH, "color": "green", "anchor": True},
                        {"sel": "//div[contains(text(), 'Доставка')]/../following-sibling::div[1]//*[string-length(text()) > 0]", "by": By.XPATH, "color": "green", "anchor": True},
                        {"sel": "//div[contains(text(),'Продавец')]/following-sibling::div", "by": By.XPATH, "color": "blue", "anchor": False},
                        {"sel": "//span[contains(text(),'Продавец')]/../following-sibling::div", "by": By.XPATH, "color": "blue", "anchor": False},
                        {"sel": "//div[contains(text(), 'Магазин')]/following-sibling::div//span", "by": By.XPATH, "color": "magenta", "anchor": False},
                        {"sel": "a[href*='/seller/']", "by": By.CSS_SELECTOR, "color": "red", "anchor": False},
                        {"sel": "div[data-widget='sellerName']", "by": By.CSS_SELECTOR, "color": "red", "anchor": False}
                    ]
                    for cfg in selectors_config:
                        try:
                            els = driver.find_elements(cfg["by"], cfg["sel"])
                            for el in els:
                                if el.is_displayed() and el.text.strip():
                                    text_clean = el.text.strip()
                                    if len(text_clean) > 50: continue
                                    if "\n" in text_clean: continue
                                    if "Каталог" in text_clean: continue
                                    if "Ozon" in text_clean and "Fresh" in text_clean: continue
                                    if "доставка" in text_clean.lower(): continue
                                    
                                    real_seller = text_clean
                                    seller_element = el
                                    
                                    color = cfg["color"]
                                    driver.execute_script(f"arguments[0].style.border='5px solid {color}'; arguments[0].style.backgroundColor='yellow';", seller_element)
                                    if cfg.get("anchor"):
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});")
                                    else:
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});")
                                    time.sleep(0.5)
                                    break
                            if real_seller != "Unknown": break
                        except: continue
                except: pass
                    
                 # If still unknown
                if real_seller == "Unknown":
                     driver.execute_script("window.scrollBy(0, 1000);")
                     time.sleep(1)
                     try:
                         lbls = driver.find_elements(By.XPATH, "//*[contains(text(), 'Продавец') or contains(text(), 'Магазин')]")
                         for lbl in lbls:
                             try:
                                 parent = lbl.find_element(By.XPATH, "./..")
                                 txt = parent.text.replace(lbl.text, "").strip()
                                 if len(txt) > 50: continue
                                 if "\n" in txt: continue
                                 if "Каталог" in txt: continue
                                 if "Ozon" in txt and "Fresh" in txt: continue
                                 if len(txt) > 2:
                                     real_seller = txt
                                     seller_element = parent
                                     driver.execute_script("arguments[0].style.border='5px solid purple'; arguments[0].style.backgroundColor='yellow';", seller_element)
                                     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});")
                                     break
                             except: pass
                     except: pass
                     
            # 3. SPECIFIC FALLBACK
            if real_seller == "Unknown":
                try:
                    candidates = driver.find_elements(By.XPATH, "//*[contains(text(), 'официальн')]")
                    for cand in candidates:
                        if cand.is_displayed():
                            can_text = cand.text.strip()
                            if len(can_text) < 25:
                                try:
                                    parent = cand.find_element(By.XPATH, "..")
                                    can_text = parent.text.strip()
                                except: pass
                            
                            if len(can_text) < 50:
                                real_seller = can_text
                                seller_element = cand
                                driver.execute_script("arguments[0].style.border='5px solid orange'; arguments[0].style.backgroundColor='yellow';", seller_element)
                                break
                except: pass
    
            # FINAL FALLBACK
            if real_seller == "Unknown":
                try:
                    brand_el = driver.find_element(By.CSS_SELECTOR, "ol[itemscope] li:last-child a, div[data-widget='breadCrumbs'] a:last-child")
                    if brand_el:
                        real_seller = "Бренд: " + brand_el.text.strip()
                        seller_element = brand_el
                        driver.execute_script("arguments[0].style.border='5px solid orange'; arguments[0].style.backgroundColor='yellow';", seller_element)
                except: pass

            if real_seller == "Unknown" and attempt < 1:
                print("[VIOLATION_CHECK] Seller not found. Refreshing page...")
                driver.refresh()
                time.sleep(5)
                continue
            
            break

        if seller_element:
            try:
                driver.execute_script("arguments[0].style.border='5px solid red'; arguments[0].style.backgroundColor='yellow';", seller_element)
                rect = driver.execute_script("return arguments[0].getBoundingClientRect();", seller_element)
                if rect['top'] > 800:
                     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", seller_element)
                else:
                     driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
            except: pass
        else:
            driver.execute_script("window.scrollTo(0, 0);")

        png_data = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(png_data))
        draw = ImageDraw.Draw(image)
        width, height = image.size
        draw.rectangle([(0,0), (width-1, height-1)], outline="red", width=10)
        
        text = f"НАРУШЕНИЕ!\nSKU: {sku}\nБаза: {violation['competitor']}\nПо факту: {real_seller}\nИх цена: {violation['comp_price']} ₽\nНаша цена: {violation['our_price']} ₽"
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        text_bbox = draw.textbbox((50, 50), text, font=font)
        draw.rectangle([text_bbox[0]-10, text_bbox[1]-10, text_bbox[2]+10, text_bbox[3]+10], fill="red")
        draw.text((50, 50), text, fill="white", font=font)
        
        output = io.BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        safe_comp = (violation['competitor'] or "")[:50]
        safe_real = (real_seller or "")[:50]
        
        from datetime import datetime
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        files = {'photo': ('violation.png', output, 'image/png')}
        caption = (f"🚨 **НАРУШЕНИЕ ЦЕНЫ!**\n\n"
                   f"🕒 Время: {now_str}\n"
                   f"SKU: `{sku}`\n"
                   f"🔗 [Товар на Ozon]({url})\n\n"
                   f"Магазин (База): *{safe_comp}*\n"
                   f"Магазин (Факт): *{safe_real}*\n"
                   f"Цена: **{violation['comp_price']} ₽**\n"
                   f"(Наша: {violation['our_price']} ₽)")
                   
        data = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        resp = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto", data=data, files=files)
        print(f"[VIOLATION_CHECK] Sent report status: {resp.status_code}")
        
    except Exception as e:
        print(f"[VIOLATION_CHECK] Error processing {sku}: {e}")

def run_check():
    violations = get_violations()
    if not violations:
        return

    forwarder_port = 8121
    forwarder_proc = None
    try:
        print(f"[VIOLATION_CHECK] Starting local proxy forwarder on port {forwarder_port}...")
        forwarder_proc = subprocess.Popen(
            ['python', r'proxies/auth_forwarder.py', '--config', 'upstreams.txt', '--listen-start', str(forwarder_port)], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
    except Exception as e:
        print(f"[VIOLATION_CHECK] Failed to start local forwarder: {e}")
        return

    port = 9222
    proc, profile = start_chrome(port, unique_id=99999, proxy_host="127.0.0.1", proxy_port=forwarder_port)
    
    if not proc:
        print("[VIOLATION_CHECK] Failed to start Chrome")
        if forwarder_proc: forwarder_proc.kill()
        return
        
    time.sleep(3)
    driver = attach_selenium_with_proxy(port)
    
    try:
        if driver:
             for v in violations:
                 process_and_send(driver, v)
                 time.sleep(2)
        else:
             print("[VIOLATION_CHECK] Failed to attach Selenium")
    finally:
        try:
            if driver: driver.quit()
        except: pass
        try:
            if proc: proc.kill()
        except: pass
        try:
             if forwarder_proc: forwarder_proc.kill()
        except: pass
        try:
            shutil.rmtree(profile, ignore_errors=True)
        except: pass

if __name__ == "__main__":
    run_check()
