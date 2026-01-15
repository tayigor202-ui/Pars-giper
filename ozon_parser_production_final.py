#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os,re,time,json,psycopg2,subprocess,threading,shutil,random,string,psutil
from queue import Queue
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import requests
import check_violations

load_dotenv()

ip_timezone_cache={}
ip_cache_lock=threading.Lock()

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


DB_URL=f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
TG_BOT_TOKEN=os.getenv('TG_BOT_TOKEN')
TG_CHAT_ID=os.getenv('TG_CHAT_ID')
CHROME_PATH=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT_START=9222
NUM_WORKERS=30
BATCH_SIZE=500
USE_HEADLESS=True
MAX_PRODUCTS_PER_BATCH=3200
RESUME_FROM_LAST_N=0
DELAY_BETWEEN_PRODUCTS=(3.0,7.0)
BATCH_PAUSE_INTERVAL=100
BATCH_PAUSE_DURATION=(5.0,10.0)
MAX_RETRIES_PER_PRODUCT=3


product_queue=Queue()
results=[]
results_lock=threading.Lock()
db_save_counter=0
db_save_lock=threading.Lock()
processed_count=0
processed_lock=threading.Lock()
stop_flag=False
retry_queue=Queue()
retry_counts={}
retry_lock=threading.Lock()
batch_complete=False
batch_lock=threading.Lock()
last_processed_skus=[]
antibot_detected=False
antibot_lock=threading.Lock()

def generate_random_user_agent():
    chrome_versions=['131.0.6778.86','131.0.6778.85','131.0.6778.70','131.0.6778.69']
    chrome_ver=random.choice(chrome_versions)
    return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36'

def start_chrome(port,unique_id=None,user_agent=None,proxy_host=None,proxy_port=None,proxy_user=None,proxy_pass=None):
    if unique_id is None:
        unique_id=port
    profile=f"C:\\Temp\\chrome_profiles\\ozon\\persistent_p{port}"
    Path(profile).mkdir(parents=True,exist_ok=True)
    if not user_agent:
        user_agent=generate_random_user_agent()
    desktop_resolutions=['1920,1080','1366,768','1536,864','1440,900','1600,900','2560,1440','1280,720']
    window_size=random.choice(desktop_resolutions)
    cmd=[CHROME_PATH,f"--remote-debugging-port={port}",f"--user-data-dir={profile}",f"--user-agent={user_agent}",f"--window-size={window_size}",f"--proxy-server=http://{proxy_host}:{proxy_port}",f"--proxy-bypass-list=<-loopback>","--no-sandbox","--disable-blink-features=AutomationControlled","--disable-features=IsolateOrigins,site-per-process","--disable-web-security","--no-first-run","--no-default-browser-check","--disable-popup-blocking","--disable-infobars","--disable-notifications","--disable-default-apps","--lang=ru-RU","--disable-dev-shm-usage","--disable-gpu","--disable-software-rasterizer","--disable-component-extensions-with-background-pages","--disable-background-networking","--disable-sync","--disable-translate","--hide-scrollbars","--metrics-recording-only","--mute-audio","--no-pings","--safebrowsing-disable-auto-update","--disable-domain-reliability","--disable-background-timer-throttling","--disable-backgrounding-occluded-windows","--disable-renderer-backgrounding","--disable-ipc-flooding-protection","--blink-settings=imagesEnabled=false"]
    if USE_HEADLESS:
        cmd.insert(6,"--headless=new")
    print(f"[PROXY] Chrome будет использовать HTTP прокси: {proxy_host}:{proxy_port}")
    proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return proc,profile

def check_current_ip(driver,worker_id):
    try:
        driver.execute_script("window.open('https://httpbin.org/ip','_blank');")
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        try:
            WebDriverWait(driver,10).until(lambda d:d.find_element(By.TAG_NAME,'body').text.strip()!='')
        except:
            print(f"[W{worker_id}] ⏳ Timeout waiting for IP check")
        body_text=driver.find_element(By.TAG_NAME,'body').text
        try:
            ip_data=json.loads(body_text)
            ip=ip_data.get('origin','Unknown').split(',')[0].strip()
        except json.JSONDecodeError:
            import re
            ip_match=re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',body_text)
            if ip_match:
                ip=ip_match.group(0)
            else:
                ip='Error'
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return ip
    except Exception as e:
        print(f"[W{worker_id}] ⚠️ IP Check Error: {e}")
        try:
            if len(driver.window_handles)>1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return 'Error'

def attach_selenium_with_proxy(port,proxy_host,proxy_port,proxy_user,proxy_pass,worker_id=0):
    for attempt in range(3):
        try:
            opts=Options()
            opts.add_experimental_option("debuggerAddress",f"127.0.0.1:{port}")
            driver=webdriver.Chrome(options=opts)
            current_ip=None
            timezone_offset=-180
            timezone_name='Europe/Moscow'
            city_name='Moscow'
            try:
                current_ip=check_current_ip(driver,worker_id)
                if current_ip and current_ip!='Error' and current_ip!='Unknown':
                    tz_info=get_timezone_for_ip(current_ip)
                    timezone_offset=tz_info['offset']
                    timezone_name=tz_info['name']
                    city_name=tz_info['city']
                    print(f"[W{worker_id}] 🌍 IP: {current_ip} → {city_name} ({timezone_name}, UTC{timezone_offset//60:+d})")
                else:
                    print(f"[W{worker_id}] ⚠️ Не удалось определить IP, используем Moscow timezone")
            except Exception as e:
                print(f"[W{worker_id}] ⚠️ Ошибка определения timezone: {e}")
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':f'''Object.defineProperty(navigator,'webdriver',{{get:()=>undefined}});Object.defineProperty(navigator,'languages',{{get:()=>['ru-RU','ru']}});Object.defineProperty(navigator,'language',{{get:()=>'ru-RU'}});Date.prototype.getTimezoneOffset=function(){{return {timezone_offset};}};window.chrome={{runtime:{{}}}};const origQuery=window.navigator.permissions.query;window.navigator.permissions.query=(params)=>(params.name==='notifications'?Promise.resolve({{state:'prompt'}}):origQuery(params));Object.defineProperty(navigator,'plugins',{{get:()=>[{{name:'Chrome PDF Plugin',filename:'internal-pdf-viewer',description:'Portable Document Format'}},{{name:'Chrome PDF Viewer',filename:'mhjfbmdgcfjbbpaeojofohoefgiehjai',description:'Portable Document Format'}},{{name:'Native Client',filename:'internal-nacl-plugin',description:'Native Client Executable'}}]}});delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;const originalError=console.error;console.error=function(){{if(arguments[0]&&typeof arguments[0]==='string'&&arguments[0].includes('automation')){{return;}}return originalError.apply(console,arguments);}};'''})
            # Aggressive blocking of all media types to save traffic
            driver.execute_cdp_cmd('Network.setBlockedURLs',{'urls':['*.jpg','*.jpeg','*.png','*.gif','*.webp','*.svg','*.ico','*.mp4','*.webm','*.woff','*.woff2','*.ttf','*.otf','*google-analytics*','*yandex.ru/metrika*','*doubleclick*','*facebook*','*vk.com*','*mail.ru*','*criteo*','*hotjar*','*mc.yandex.ru*','*ads*']})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders',{'headers':{'Accept-Language':'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8','Accept-Encoding':'gzip, deflate, br','Cache-Control':'max-age=0','sec-ch-ua':'"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"','sec-ch-ua-mobile':'?0','sec-ch-ua-platform':'"Windows"','Sec-Fetch-Dest':'document','Sec-Fetch-Mode':'navigate','Sec-Fetch-Site':'none','Sec-Fetch-User':'?1','Upgrade-Insecure-Requests':'1'}})
            try:
                driver.get('https://www.ozon.ru')
                time.sleep(random.uniform(1.5,3.0))
                random_cookies=[{'name':'__Secure-ab-group','value':str(random.randint(0,999)),'domain':'.ozon.ru','path':'/','secure':True},{'name':'__Secure-user-id','value':f"{random.randint(10000000,99999999)}",'domain':'.ozon.ru','path':'/','secure':True},{'name':'abt_data','value':f"{random.randint(1000,9999)}.{random.randint(1000,9999)}",'domain':'.ozon.ru','path':'/','secure':False}]
                for cookie in random_cookies:
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass
            except:
                pass
            return driver
        except:
            if attempt<2:
                time.sleep(0.5)
    return None

def extract_prices(driver,sku,worker_id):
    try:
        WebDriverWait(driver,10).until(lambda d:d.execute_script("return document.readyState")=="complete")
        time.sleep(random.uniform(2.0,3.0))
        seller_name=None
        product_name=None
        try:
            name_selectors=["h1[data-widget='webProductHeading']","h1","div[data-widget='webProductHeading'] h1","span[data-widget='webProductHeading']"]
            for selector in name_selectors:
                try:
                    name_elem=driver.find_element(By.CSS_SELECTOR,selector)
                    if name_elem and name_elem.text.strip():
                        product_name=name_elem.text.strip()
                        print(f"[W{worker_id}] 📝 Название: {product_name[:50]}...")
                        break
                except:
                    continue
        except:
            pass
        try:
            # Improved Seller Extraction
            seller_selectors=["a[href*='/seller/']","a[data-widget='sellerLink']","span[data-widget='sellerName']","div[data-widget='sellerName']"]
            for selector in seller_selectors:
                try:
                    seller_elem=driver.find_element(By.CSS_SELECTOR,selector)
                    if seller_elem and seller_elem.text.strip():
                        candidate_name=seller_elem.text.strip()
                        if len(candidate_name)<40 and "подписаться" not in candidate_name.lower():
                            seller_name=candidate_name
                            break
                except:
                    continue
            
            if not seller_name:
                # Try to find by "Магазин" label proximity (Robust fallback)
                try:
                    # Find element containing "Магазин" text
                    label_elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'Магазин') or contains(text(), 'Продавец')]")
                    for label in label_elems:
                        try:
                            # Look for the next clickable element or text element nearby
                            # This is a bit heuristic but handles the "Магазин" -> "Seller Name" structure
                            parent = label.find_element(By.XPATH, "./..")
                            # Try to find a link or span with text in the parent's siblings or children
                            candidates = parent.find_elements(By.XPATH, ".//*[string-length(text()) > 1] | ./following-sibling::*[1]//*[string-length(text()) > 1]")
                            for cand in candidates:
                                txt = cand.text.strip()
                                if txt and txt != label.text and len(txt) < 40 and "подписаться" not in txt.lower() and "перейти" not in txt.lower():
                                    seller_name = txt
                                    break
                            if seller_name:
                                break
                        except:
                            continue
                except:
                    pass

        except:
            pass
        if not seller_name:
            seller_name="Ozon"
        unavailable=False
        unavailable_phrases=['Товар закончился','Товара нет в наличии','нет в наличии','Нет в продаже','Закончился','Недоступен для заказа','Временно недоступен']
        try:
            page_text=driver.find_element(By.TAG_NAME,'body').text
            for phrase in unavailable_phrases:
                if phrase.lower() in page_text.lower():
                    unavailable=True
                    break
        except:
            pass
        price_block=None
        candidates=["[data-widget='webSale']","[data-widget*='webPrice']","section[data-widget*='webPrice']","div[data-widget*='price']","div[class*='price']","span[class*='price']"]
        for attempt in range(5):
            for css in candidates:
                try:
                    els=driver.find_elements(By.CSS_SELECTOR,css)
                    for el in els:
                        if el and el.is_displayed():
                            price_block=el
                            break
                except:
                    continue
            if price_block:
                break
            time.sleep(0.5)
        if unavailable:
            return {'price_card':'Товара нет в наличии','price_nocard':None,'price_old':None,'is_antibot':False,'seller_name':seller_name,'product_name':product_name}
        if not price_block:
            if unavailable:
                return {'price_card':'Товара нет в наличии','price_nocard':'Товара нет в наличии','price_old':'','is_antibot':False,'seller_name':seller_name,'product_name':product_name}
            antibot_markers=['Проверка безопасности','Checking your browser','cloudflare','captcha','Пройдите проверку']
            page_text=driver.page_source.lower()
            is_antibot=any(marker.lower() in page_text for marker in antibot_markers)
            return {'price_card':None,'price_nocard':None,'price_old':None,'is_antibot':is_antibot,'seller_name':seller_name,'product_name':product_name}
        txt=re.sub(r'\s+',' ',price_block.text.replace('\n',' ').strip())
        price_re=re.compile(r'[\d\s]+₽')
        low=txt.lower()
        if ("ozon карт" in low) or ("с картой" in low):
            parts=re.split(r'[cс] Ozon Картой|без Ozon Карты|[cс] картой|без карты',txt,flags=re.IGNORECASE)
            if len(parts)>=2:
                m_card=price_re.search(parts[0])
                price_card=m_card.group(0) if m_card else None
                nums=price_re.findall(parts[1])
                price_nocard=nums[0] if len(nums)>0 else None
                price_old=nums[1] if len(nums)>1 else ''
                return {'price_card':price_card,'price_nocard':price_nocard,'price_old':price_old,'is_antibot':False,'seller_name':seller_name,'product_name':product_name}
        price_old=''
        for sel in ["del","span[style*='line-through']",".price-old"]:
            try:
                old_els=price_block.find_elements(By.CSS_SELECTOR,sel)
                for o in old_els:
                    if o and o.is_displayed():
                        m=price_re.search(o.text or "")
                        if m:
                            price_old=m.group(0)
                            break
                if price_old:
                    break
            except:
                pass
        prices=price_re.findall(txt)
        if prices:
            p=prices[0]
            return {'price_card':p,'price_nocard':p,'price_old':price_old,'is_antibot':False,'seller_name':seller_name,'product_name':product_name}
        return {'price_card':None,'price_nocard':None,'price_old':None,'is_antibot':False,'seller_name':seller_name,'product_name':product_name}
    except Exception as e:
        return {'price_card':None,'price_nocard':None,'price_old':None,'seller_name':'Ozon','product_name':None}

def save_batch_to_db(batch):
    if not batch:
        return 0
    conn=psycopg2.connect(DB_URL)
    cur=conn.cursor()
    saved=0
    for item in batch:
        # Always save, even if status is not OK (to track Out of Stock/Errors)
        try:
            # Use SAVEPOINT to prevent transaction abortion on error
            # Use INSERT ON CONFLICT to handle multiple sellers per SKU correctly
            cur.execute("""
                INSERT INTO public.prices (sku, competitor_name, price_card, price_nocard, price_old, name, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (sku, competitor_name) 
                DO UPDATE SET 
                    price_card = EXCLUDED.price_card,
                    price_nocard = EXCLUDED.price_nocard,
                    price_old = EXCLUDED.price_old,
                    name = EXCLUDED.name,
                    status = EXCLUDED.status,
                    created_at = NOW()
            """, (
                item['sku'], 
                item['competitor_name'], # Use the preserved competitor name from DB/Import
                item['price_card'], 
                item['price_nocard'], 
                item['price_old'], 
                item.get('product_name'), 
                item.get('status')
            ))
            saved+=1
        except Exception as e:
            cur.execute("ROLLBACK TO SAVEPOINT sp1")
            print(f"[DB ERROR] {item['sku']}: {e}")
    conn.commit()
    cur.close()
    conn.close()
    return saved

def worker(worker_id,port,proxies):
    global db_save_counter,processed_count,stop_flag,antibot_detected,antibot_lock,product_queue
    driver=None
    proc=None
    proxy_rotation=0
    local_batch=[]
    worker_products_count=0
    browser_products_count=0
    print(f"[W{worker_id}] 🚀 Запускаем воркер на порту {port}...")
    def create_browser():
        nonlocal proc,driver
        proxy_base=proxies[0]
        unique_id=int(time.time()*1000)+worker_id+browser_products_count
        proc,profile=start_chrome(port,unique_id,proxy_host="127.0.0.1",proxy_port=8118)
        if not proc:
            print(f"[W{worker_id}] ❌ Не удалось запустить Chrome на порту {port}")
            return False
        print(f"[W{worker_id}] ⏳ Chrome запущен, подключаем Selenium с прокси...")
        time.sleep(2)
        driver=attach_selenium_with_proxy(port,proxy_base['host'],proxy_base['port'],proxy_base['user'],proxy_base['pass'],worker_id)
        if not driver:
            print(f"[W{worker_id}] ❌ Не удалось подключить Selenium на порту {port}")
            if proc:
                proc.terminate()
            return False
        print(f"[W{worker_id}] ✅ Браузер готов к работе!")
        return True
    if not create_browser():
        return
    while not stop_flag:
        try:
            item=None
            try:
                item=retry_queue.get_nowait()
            except:
                pass
            if not item:
                try:
                    item=product_queue.get(timeout=30)
                except:
                    break
            if len(item)==5:
                # Retry item with competitor_name: (sku, name, brand, url, competitor_name)
                sku,name,brand,url,competitor_name=item
                idx=0
            elif len(item)==4:
                # Main queue item: (idx, sku, name, competitor_name)
                idx,sku,name,competitor_name=item
                brand=None
                url=f"https://www.ozon.ru/product/{sku}/"
            else:
                # Fallback
                idx,sku,name=item
                competitor_name=None
                brand=None
                url=f"https://www.ozon.ru/product/{sku}/"
            time.sleep(random.uniform(0.5,1.5))
            success=False
            try:
                driver.get(f"https://www.ozon.ru/product/{sku}/")
                try:
                    WebDriverWait(driver,5).until(lambda d:d.execute_script("return document.readyState")=="complete")
                    try:
                        WebDriverWait(driver,2).until_not(EC.presence_of_element_located((By.CSS_SELECTOR,"[class*='spinner'], [class*='loader'], [class*='loading']")))
                    except:
                        pass
                    WebDriverWait(driver,3).until(EC.presence_of_element_located((By.CSS_SELECTOR,"span, button, div")))
                    time.sleep(random.uniform(0.5,1.0))
                except TimeoutException:
                    time.sleep(1)
                prices=extract_prices(driver,sku,worker_id)
                if idx==1 and not prices.get('price_card'):
                    try:
                        with open(f"debug_html_{sku}.html",'w',encoding='utf-8') as f:
                            f.write(driver.page_source)
                    except:
                        pass
                success=False
                status='ERROR'
                retry_needed=False
                if prices:
                    if prices.get('is_antibot'):
                        status='ANTIBOT'
                        retry_needed=True
                    elif prices.get('price_card')=='Товара нет в наличии':
                        status='OUT_OF_STOCK'
                    elif prices.get('price_card') and prices.get('price_card')!='Товара нет в наличии':
                        success=True
                        status='OK'
                    else:
                        status='NO_PRICE'
                else:
                    status='ERROR'
                    retry_needed=True
                extracted_seller = prices.get('seller_name') if prices else None
                # Если имя конкурента не задано (в очереди), используем то что спарсили
                final_competitor = competitor_name if competitor_name else extracted_seller
                result={'sku':sku,'competitor_name':final_competitor,'price_card':prices.get('price_card') if success and prices else None,'price_nocard':prices.get('price_nocard') if success and prices else None,'price_old':prices.get('price_old') if success and prices else None,'product_name':prices.get('product_name') if prices else None,'status':status}
                with results_lock:
                    results.append(result)
                with processed_lock:
                    processed_count+=1
                    current_count=processed_count
                    if current_count%10==0:
                        print(f"\n📊 ПРОГРЕСС: {current_count}/3100 товаров обработано\n")
                if retry_needed:
                    with retry_lock:
                        attempt_count=retry_counts.get(sku,0)
                        if attempt_count<MAX_RETRIES_PER_PRODUCT:
                            retry_counts[sku]=attempt_count+1
                            retry_queue.put((sku,name,brand if brand else 'Unknown',url if url else f"https://www.ozon.ru/product/{sku}/",competitor_name))
                            if status=='ANTIBOT':
                                print(f"🤖 ANTIBOT (попытка {attempt_count+1}/{MAX_RETRIES_PER_PRODUCT}) → в очередь")
                            else:
                                print(f"⚠️ ERROR (попытка {attempt_count+1}/{MAX_RETRIES_PER_PRODUCT}) → в очередь")
                        else:
                            if status=='ANTIBOT':
                                print(f"🤖 ANTIBOT (MAX попыток)")
                            else:
                                print(f"⚠️ ERROR (MAX попыток)")
                else:
                    if status=='OK':
                        price_card=prices.get('price_card','-')
                        price_nocard=prices.get('price_nocard','-')
                        price_old=prices.get('price_old','-')
                        print(f"✅ SKU {sku}: С картой: {price_card} | Без карты: {price_nocard} | Старая: {price_old}")
                    elif status=='OUT_OF_STOCK':
                        print(f"📦 SKU {sku}: Товар закончился")
                    elif status=='ANTIBOT':
                        print(f"🤖 SKU {sku}: АНТИБОТ ОБНАРУЖЕН!")
                delay=random.uniform(DELAY_BETWEEN_PRODUCTS[0],DELAY_BETWEEN_PRODUCTS[1])
                time.sleep(delay)
                if random.random()>0.85:
                    long_pause=random.uniform(10.0,20.0)
                    print(f"[W{worker_id}] 💤 Долгая пауза {long_pause:.1f}с (имитация отвлечения)")
                    time.sleep(long_pause)
                worker_products_count+=1
                browser_products_count+=1
                if worker_products_count%BATCH_PAUSE_INTERVAL==0:
                    batch_pause=random.uniform(BATCH_PAUSE_DURATION[0],BATCH_PAUSE_DURATION[1])
                    print(f"[W{worker_id}] 🛑 БАТЧ-ПАУЗА {batch_pause:.1f}с после {worker_products_count} товаров")
                    time.sleep(batch_pause)
                recreate_threshold=random.randint(15,20)
                if browser_products_count>=recreate_threshold:
                    print(f"[W{worker_id}] 🔄 Пересоздаем браузер после {browser_products_count} товаров (новый fingerprint)")
                    try:
                        if driver:
                            driver.quit()
                            time.sleep(0.5)
                    except:
                        pass
                    try:
                        if proc:
                            proc.kill()
                            time.sleep(0.5)
                    except:
                        pass
                    browser_products_count=0
                    if not create_browser():
                        print(f"[W{worker_id}] ❌ Не удалось пересоздать браузер, завершаем воркер")
                        break
                    print(f"[W{worker_id}] ✅ Браузер пересоздан, продолжаем работу")
            except TimeoutException:
                with retry_lock:
                    attempt_count=retry_counts.get(sku,0)
                    if attempt_count<MAX_RETRIES_PER_PRODUCT:
                        retry_counts[sku]=attempt_count+1
                        retry_queue.put((sku,name,brand if brand else 'Unknown',url if url else f"https://www.ozon.ru/product/{sku}/",competitor_name))
                    else:
                        with results_lock:
                            results.append({'sku':sku,'competitor_name':competitor_name,'price_card':None,'price_nocard':None,'price_old':None,'status':'TIMEOUT'})
            except Exception as e:
                error_msg=str(e).lower()
                if '404' in error_msg or 'not found' in error_msg:
                    status='404_NO_PAGE'
                elif 'timeout' in error_msg:
                    status='TIMEOUT'
                elif 'connection' in error_msg or 'proxy' in error_msg:
                    status='PROXY_ERROR'
                else:
                    status='ERROR'
                if status=='ANTIBOT':
                    print(f"🤖 SKU {sku}: АНТИБОТ ОБНАРУЖЕН!")
                elif status not in ['TIMEOUT','PROXY_ERROR']:
                    print(f"⚠️ SKU {sku}: {status}")
                with retry_lock:
                    attempt_count=retry_counts.get(sku,0)
                    if attempt_count<MAX_RETRIES_PER_PRODUCT:
                        retry_counts[sku]=attempt_count+1
                        retry_queue.put((sku,name,brand if brand else 'Unknown',url if url else f"https://www.ozon.ru/product/{sku}/",competitor_name))
                    else:
                        with results_lock:
                            results.append({'sku':sku,'competitor_name':competitor_name,'price_card':None,'price_nocard':None,'price_old':None,'status':status})
            finally:
                try:
                    if driver:
                        try:
                            while len(driver.window_handles)>1:
                                try:
                                    driver.switch_to.window(driver.window_handles[-1])
                                    driver.close()
                                except:
                                    break
                            try:
                                driver.switch_to.window(driver.window_handles[0])
                            except:
                                pass
                        except:
                            pass
                        try:
                            driver.delete_all_cookies()
                        except:
                            pass
                except:
                    pass
        except KeyboardInterrupt:
            print(f"\n[W{worker_id}] Interrupted by user")
            break
        except:
            pass
    if local_batch:
        print(f"\n[W{worker_id}] Saving final batch ({len(local_batch)} items)...")
        saved=save_batch_to_db(local_batch)
        print(f"[W{worker_id}] Saved {saved} items")
    try:
        if driver:
            driver.quit()
            time.sleep(0.2)
    except:
        pass
    try:
        if proc:
            proc.kill()
            time.sleep(0.2)
    except:
        pass
    try:
        import psutil
        for p in psutil.process_iter(['pid','name','cmdline']):
            try:
                if p.info['name'] and 'chrome' in p.info['name'].lower():
                    cmdline=p.info.get('cmdline',[])
                    if cmdline and any(f'--remote-debugging-port={port}' in str(arg) for arg in cmdline):
                        p.kill()
            except:
                pass
    except:
        pass
    print(f"[W{worker_id}] Closed")

def clean_old_chrome_profiles(max_age_minutes=30):
    try:
        profiles_dir=Path("C:/Temp/chrome_profiles/ozon")
        if not profiles_dir.exists():
            return 0
        now=time.time()
        max_age_seconds=max_age_minutes*60
        deleted=0
        total_size=0
        for profile_path in profiles_dir.glob("p*"):
            if profile_path.is_dir():
                try:
                    profile_age=now-profile_path.stat().st_mtime
                    if profile_age>max_age_seconds:
                        try:
                            size=sum(f.stat().st_size for f in profile_path.rglob('*') if f.is_file())
                            total_size+=size
                        except:
                            pass
                        shutil.rmtree(profile_path,ignore_errors=True)
                        deleted+=1
                except:
                    pass
        if deleted>0:
            size_mb=total_size/(1024*1024)
            print(f"[CLEANUP] Удалено {deleted} старых профилей ({size_mb:.1f} MB освобождено)")
        return deleted
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
        return 0

def load_proxies():
    # Now reading from upstreams.txt to single source truth
    with open('upstreams.txt','r') as f:
        line=f.readline().strip()
    parts=line.split(':')
    if len(parts)==4:
        proxy={'host':parts[0],'port':parts[1],'user':parts[2],'pass':parts[3]}
        print(f"[OK] ROTATING MangoProxy загружен (каждый запрос = новый IP)")
        print(f"     Прокси: {parts[0]}:{parts[1]}")
        return [proxy]
    print("[ERROR] Не удалось загрузить rotating прокси!")
    return []

def load_products_from_db():
    conn=psycopg2.connect(DB_URL)
    cur=conn.cursor()
    # Fetch competitor_name and sp_code as well
    cur.execute("""SELECT sku, name, competitor_name, sp_code FROM public.prices WHERE sku IS NOT NULL ORDER BY sku""")
    products=[(sku,name or '', comp_name or '', sp_code or '') for (sku,name,comp_name,sp_code) in cur.fetchall()]
    cur.close()
    conn.close()
    return products

def generate_excel_report():
    print("\n[EXCEL] Generating report...")
    try:
        conn=psycopg2.connect(DB_URL)
        # Select ALL items, regardless of price
        query="""SELECT sku,name,competitor_name,price_card,price_nocard,price_old,status,sp_code FROM public.prices ORDER BY name, competitor_name"""
        df=pd.read_sql(query,conn)
        conn.close()
        if len(df)==0:
            print("[EXCEL] No data to report")
            return None
        
        # Data Cleaning
        df['competitor_name'] = df['competitor_name'].astype(str).str.strip()
        df['sp_code'] = df['sp_code'].astype(str).str.strip()
        print(f"\n[DEBUG] Raw Competitors from DB: {df['competitor_name'].unique()}")

        # Optional Mapping - but keep original if not found
        store_mapping={
            'Ссылка на наш магазин':'Наш магазин',
            'Магазин DeLonghi Group':'DeLonghi Group',
            'DeLonghi Group':'DeLonghi Group',
            'Delonghi Official Store':'DeLonghi Official',
            'Delonghi official store':'DeLonghi Official', # Case variant
            'DeLonghi Official Store':'DeLonghi Official'  # Case variant
        }
        # Use get(x, x) to keep original name if not in map
        df['competitor_name']=df['competitor_name'].map(lambda x:store_mapping.get(x,x))
        
        print(f"[DEBUG] Mapped Competitors: {df['competitor_name'].unique()}")

        # Apply status logic
        def fill_status(row):
            def check_val(val):
                if pd.isna(val): return True
                if str(val).lower().strip() in ['','none','nan']: return True
                return False

            status = row.get('status')
            p_card = row.get('price_card')
            
            # Text to display
            out_text = 'Товар закончился'
            
            # Condition 1: Explicit Status
            if status == 'OUT_OF_STOCK':
                return pd.Series([out_text, out_text, out_text, status], index=['price_card', 'price_nocard', 'price_old', 'status'])
            
            # Condition 2: Text in Price fields
            if isinstance(p_card, str) and ('закончился' in p_card.lower() or 'нет' in p_card.lower()):
                 return pd.Series([out_text, out_text, out_text, status], index=['price_card', 'price_nocard', 'price_old', 'status'])

            # Condition 3: Missing Price but NOT Error
            if check_val(p_card):
                if status == 'ANTIBOT':
                    text = 'Ошибка (Антибот)'
                    return pd.Series([text, text, text, text], index=['price_card', 'price_nocard', 'price_old', 'status'])
                elif status == 'ERROR':
                    text = 'Ошибка парсинга'
                    return pd.Series([text, text, text, text], index=['price_card', 'price_nocard', 'price_old', 'status'])
                elif status == 'NO_PRICE':
                    text = 'Нет цены'
                    return pd.Series([text, text, text, text], index=['price_card', 'price_nocard', 'price_old', 'status'])
                else:
                    # NO TEXT - leave empty for missing data
                    return pd.Series([None, None, None, status], index=['price_card', 'price_nocard', 'price_old', 'status'])
                
            return pd.Series([row['price_card'], row['price_nocard'], row['price_old'], row.get('status', 'OK')], index=['price_card', 'price_nocard', 'price_old', 'status'])

        # Apply transformation
        df[['price_card', 'price_nocard', 'price_old', 'status']] = df.apply(fill_status, axis=1)

        # PRE-PROCESSING: Fill missing names per SP-CODE
        # For each SP-CODE, use the first non-empty name found across all stores
        def get_sp_name(sp_code):
            sp_data = df[df['sp_code'] == sp_code]['name']
            valid_names = sp_data.dropna()
            valid_names = valid_names[valid_names.astype(str).str.strip() != '']
            valid_names = valid_names[valid_names.astype(str).str.lower() != 'none']
            return valid_names.iloc[0] if len(valid_names) > 0 else None
        
        sp_name_map = {sp: get_sp_name(sp) for sp in df['sp_code'].unique() if sp}
        df['name'] = df.apply(lambda row: sp_name_map.get(row['sp_code']) if pd.isna(row['name']) or str(row['name']).strip() == '' else row['name'], axis=1)

        # Pivot the table
        # INDEX: ONLY SP_CODE (not name!) - one row per product
        # COLUMNS: COMPETITOR (Columns)
        # VALUES: SKU + NAME + PRICES
        # CRITICAL: Use dropna=False to preserve ALL stores even if they have sparse data
        pivot_df = df.pivot_table(
            index='sp_code',  # CHANGED: Only sp_code, not ['sp_code', 'name']
            columns='competitor_name', 
            values=['name', 'sku', 'price_card', 'price_nocard', 'price_old'],  # Added 'name'
            aggfunc='first',
            dropna=False  # THIS PRESERVES ALL COLUMNS!
        )
        
        # Swap levels to get Seller -> Attribute
        pivot_df.columns = pivot_df.columns.swaplevel(0, 1)
        
        # Rename attributes to Russian
        rename_map = {
            'name': 'Название',  # NEW: Add name column
            'sku': 'SKU',
            'price_card': 'Цена с картой',
            'price_nocard': 'Цена без карты',
            'price_old': 'Старая цена'
        }
        pivot_df = pivot_df.rename(columns=rename_map, level=1)
        
        # Leave empty cells blank (no "Нет данных" text)

        # Sort columns to group by Seller, then by Attribute order
        sellers = sorted(pivot_df.columns.get_level_values(0).unique())
        desired_order = ['Название', 'SKU', 'Цена с картой', 'Цена без карты', 'Старая цена']  # Added Название
        
        # Reindex columns
        new_columns = []
        for seller in sellers:
            for attr in desired_order:
                if (seller, attr) in pivot_df.columns:
                    new_columns.append((seller, attr))
        
        pivot_df = pivot_df.reindex(columns=new_columns)

        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        filename=f"ozon_prices_report_{timestamp}.xlsx"
        
        print(f"[EXCEL] Saving to {filename}...")
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            pivot_df.to_excel(writer, sheet_name='Цены')
            worksheet = writer.sheets['Цены']
            
            # Formatting
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
            
            # Green header style
            header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=10, name='Roboto')
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Apply styles to headers (rows 1 and 2)
            for row in worksheet.iter_rows(min_row=1, max_row=2):
                for cell in row:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                    cell.border = border
            
            # Auto-width
            for i, column in enumerate(worksheet.columns, 1):
                max_length = 0
                column_letter = get_column_letter(i)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Freeze panes (skip 2 header rows)
            worksheet.freeze_panes = 'C3' 

        print(f"[EXCEL] Report created: {filename}")
        return filename
    except Exception as e:
        print(f"[EXCEL] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_to_telegram(filename,stats_text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("[TG] Token or Chat ID not configured")
        return
    if not filename or not os.path.exists(filename):
        print("[TG] No file to send")
        return
    print("[TG] Sending to Telegram...")
    try:
        url=f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendDocument"
        with open(filename,'rb') as f:
            files={'document':f}
            data={'chat_id':TG_CHAT_ID}
            response=requests.post(url,data=data,files=files,timeout=60)
            print(f"[TG] Response status: {response.status_code}")  # DEBUG
            if response.status_code==200:
                print("[TG] Report sent successfully")
                try:
                    os.remove(filename)
                    print(f"[TG] ✅ File deleted: {filename}")
                except Exception as del_err:
                    print(f"[TG] ❌ Failed to delete file: {del_err}")
            else:
                print(f"[TG] Error: {response.text}")
    except Exception as e:
        print(f"[TG] Error sending file: {e}")

def kill_all_browsers():
    import subprocess
    try:
        subprocess.run('Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue',shell=True,capture_output=True,timeout=10)
        time.sleep(1)
        current_pid=os.getpid()
        for proc in psutil.process_iter(['pid','name']):
            try:
                if proc.info['name']=='python.exe' and proc.info['pid']!=current_pid:
                    psutil.Process(proc.info['pid']).kill()
            except:
                pass
        time.sleep(2)
        print("[CLEANUP] ✅ Все процессы убиты")
    except Exception as e:
        print(f"[CLEANUP] ⚠️ Ошибка при убийстве процессов: {e}")

def run_single_batch(batch_products):
    global processed_count,stop_flag,product_queue,results,db_save_counter
    processed_count=0
    stop_flag=False
    db_save_counter=0
    start_time=time.time()
    proxies=load_proxies()
    print(f"[OK] ROTATING MangoProxy загружен (каждый запрос = новый IP)")
    for idx,(sku,name,comp_name,sp_code) in enumerate(batch_products,1):
        product_queue.put((idx,sku,name,comp_name))
    print(f"\n{'='*100}")
    print(f"[INIT] Starting {NUM_WORKERS} workers...\n")
    print(f"{'='*100}\n")
    workers=[]
    for worker_id in range(NUM_WORKERS):
        port=DEBUG_PORT_START+worker_id
        t=threading.Thread(target=worker,args=(worker_id,port,proxies),daemon=True)
        t.start()
        workers.append(t)
        time.sleep(0.5)
    for t in workers:
        t.join()
    elapsed=time.time()-start_time
    total=len(results)
    ok_count=sum(1 for r in results if r.get('status')=='OK')
    out_of_stock=sum(1 for r in results if r.get('status')=='OUT_OF_STOCK')
    no_price=sum(1 for r in results if r.get('status')=='NO_PRICE')
    errors=sum(1 for r in results if r.get('status') in ['ERROR','TIMEOUT','PROXY_ERROR'])
    if total>0:
        print(f"\n{'='*100}")
        print(f"БАТЧ ЗАВЕРШЁН: {ok_count}/{total} цен найдено ({int(elapsed//60)}m {int(elapsed%60)}s)")
        print(f"  ✅ OK (цена):          {ok_count:4d} ({ok_count/total*100:.1f}%)")
        print(f"  📦 OUT_OF_STOCK:       {out_of_stock:4d} ({out_of_stock/total*100:.1f}%)")
        print(f"  ❌ NO_PRICE:           {no_price:4d} ({no_price/total*100:.1f}%)")
        print(f"  ⚠️ ERRORS:            {errors:4d} ({errors/total*100:.1f}%)")
        print(f"{'='*100}\n")
    return True

def main():
    global processed_count,stop_flag,results,product_queue,last_processed_skus,batch_complete
    print("="*100)
    print("OZON PRODUCTION PARSER - РЕЖИМ НЕПРЕРЫВНЫХ БАТЧЕЙ")
    print(f"СТРАТЕГИЯ: {MAX_PRODUCTS_PER_BATCH} товаров -> сохранить -> убить всё -> БЕЗ ПАУЗ -> новые воркеры -> следующие {MAX_PRODUCTS_PER_BATCH}")
    print(f"СКОРОСТЬ: Максимальная! Без задержек между батчами!")
    print("="*100)
    batch_number=1
    total_parsed=0
    all_products=load_products_from_db()
    print(f"\n[INIT] Загружено {len(all_products)} товаров")
    print("[RANDOMIZE] Перемешиваем товары для естественного поведения...")
    random.shuffle(all_products)
    print("[RANDOMIZE] OK - Товары перемешаны!\n")
    current_offset=0
    while current_offset<len(all_products):
        print(f"\n{'='*100}")
        print(f"\n[BATCH #{batch_number}] Товары {current_offset+1} - {min(current_offset+MAX_PRODUCTS_PER_BATCH,len(all_products))}")
        print(f"{'='*100}\n")
        results=[]
        product_queue=Queue()
        processed_count=0
        stop_flag=False
        batch_complete=False
        last_processed_skus=[]
        batch_products=all_products[current_offset:current_offset+MAX_PRODUCTS_PER_BATCH]
        print(f"[INIT] Загружено {len(batch_products)} товаров для обработки\n")
        success=run_single_batch(batch_products)
        if not success:
            print("[ERROR] Ошибка при обработке батча")
            break
        batch_processed=len(results)
        total_parsed+=batch_processed
        if len(results)>=RESUME_FROM_LAST_N:
            last_processed_skus=[r['sku'] for r in results[-RESUME_FROM_LAST_N:]]
        print(f"\n{'='*100}")
        print(f"✅ БАТЧ #{batch_number} ЗАВЕРШЁН")
        print(f"   Обработано: {batch_processed} товаров")
        print(f"   Всего обработано: {total_parsed}/{len(all_products)}")
        print(f"{'='*100}\n")
        print(f"[CLEANUP] 🔪 УБИВАЕМ ВСЁ: процессы Python и Chrome...")
        kill_all_browsers()
        time.sleep(3)
        print(f"[CLEANUP] 🗑️ Удаляем ВСЕ профили Chrome...")
        clean_old_chrome_profiles(max_age_minutes=0)
        time.sleep(2)
        profiles_dir=Path("C:/Temp/chrome_profiles/ozon")
        remaining_profiles=list(profiles_dir.glob("p*")) if profiles_dir.exists() else []
        if remaining_profiles:
            print(f"[WARNING] ⚠️ Осталось {len(remaining_profiles)} профилей! Удаляем повторно...")
            for profile in remaining_profiles:
                try:
                    shutil.rmtree(profile,ignore_errors=True)
                except:
                    pass
            time.sleep(2)
        else:
            print(f"[CLEANUP] ✅ Все профили удалены")
        if results:
            print(f"\n[DB] 💾 Сохранение {len(results)} товаров в базу данных...")
            saved=save_batch_to_db(results)
            print(f"[DB] ✅ Сохранено {saved} товаров")
        if current_offset+MAX_PRODUCTS_PER_BATCH>=len(all_products):
            print("[COMPLETE] Все товары обработаны!")
            break
        current_offset+=MAX_PRODUCTS_PER_BATCH
        print(f"{'='*100}")
        print(f"🚀 СЛЕДУЮЩИЙ БАТЧ: товары {current_offset+1} - {min(current_offset+MAX_PRODUCTS_PER_BATCH,len(all_products))}")
        print(f"   Запускаем новые воркеры...")
        print(f"{'='*100}\n")
        time.sleep(2)
        batch_number+=1

    print(f"\n{'='*100}")
    print(f"\n[COMPLETE] ВСЕ БАТЧИ ЗАВЕРШЕНЫ!")
    print(f"   Всего батчей: {batch_number}")
    print(f"   Всего товаров обработано: {total_parsed}/{len(all_products)}")
    print(f"{'='*100}\n")
    print("[INFO] Проверяем сколько цен в базе данных...")
    try:
        conn=psycopg2.connect(DB_URL)
        cur=conn.cursor()
        cur.execute("SELECT COUNT(*) FROM public.prices WHERE price_card IS NOT NULL")
        count=cur.fetchone()[0]
        print(f"[INFO] ✅ Цен в БД: {count}/{len(all_products)}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Не удалось проверить БД: {e}")
    print("\n"+"="*100)
    print("📊 ГЕНЕРАЦИЯ ОТЧЕТА И ОТПРАВКА В TELEGRAM")
    print("="*100)
    try:
        excel_file=generate_excel_report()
        if excel_file:
            print(f"[REPORT] ✅ Отчет создан: {excel_file}")
            print("[TELEGRAM] 📤 Отправка отчета в Telegram...")
            send_to_telegram(excel_file,"")
            print("[TELEGRAM] ✅ Отчет отправлен!")
        else:
            print("[REPORT] ⚠️ Не удалось создать отчет")
            
        # VIOLATION CHECK
        print("\n"+"="*100)
        print("🕵️ ПРОВЕРКА НАРУШЕНИЙ (Скрины + Telegram)")
        print("="*100)
        check_violations.run_check()
            
    except Exception as e:
        print(f"[ERROR] Ошибка при генерации/отправке отчета: {e}")
        import traceback
        traceback.print_exc()
    print("\n"+"="*100)
    print("✅ ВСЁ ГОТОВО!")
    print("="*100+"\n")

if __name__=='__main__':
    print("DEBUG: Starting parser...")
    print("\n"+"="*70)
    print("ВАЖНО: Убедитесь что 3proxy запущен!")
    print("="*70)
    print("\nЕсли 3proxy НЕ запущен:")
    print("   1. Откройте новое окно терминала")
    print("   2. Запустите: start_3proxy.bat")
    print("   3. Дождитесь сообщения '3proxy started'")
    print("\n3proxy должен слушать на 127.0.0.1:8118 (SOCKS5)")
    print("="*70)
    time.sleep(2)
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[STOP] Ostanovleno polzovatelem")
    except Exception as e:
        print(f"\n\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "="*70)
        print("ПАРСИНГ ЗАВЕРШЁН - Закрытие всех окон через 3 секунды...")
        print("="*70)
        
        # Terminate proxy server
        try:
            import subprocess
            print("[CLEANUP] Останавливаем прокси-сервер...")
            subprocess.run('taskkill /F /IM 3proxy.exe /T', shell=True, capture_output=True, timeout=5)
            print("[CLEANUP] ✅ Прокси-сервер остановлен")
        except Exception as e:
            print(f"[CLEANUP] ⚠️ Не удалось остановить прокси: {e}")
        
        time.sleep(3)
        # Close the terminal window
        import sys
        sys.exit(0)
