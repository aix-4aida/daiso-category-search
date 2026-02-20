"""
Daiso Mall Full Product Crawler
Crawls products from all categories found in categories.json
"""
import os
import sys
import time
import random
import requests
import ctypes
import json
import re
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database.database import init_database, insert_product, product_exists

CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), 'categories.json')
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')
MAX_PRODUCTS_PER_CATEGORY = 50 # Increase as needed
MAX_CATEGORIES = 2000 # Set high to crawl all

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

KEYWORDS = ["자취", "꿀템", "신박", "아이디어", "추천", "재구매", "가성비", "편리", "정리", "수납", "청소"]

def prevent_sleep():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
        print("💡 Sleep prevention enabled")

def allow_sleep():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

def random_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def create_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def download_image(url: str, filename: str) -> str:
    if not url: return None
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    try:
        response = requests.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=30)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"⚠️ Image download failed: {e}")
    return None

def scroll_slowly(driver, scroll_amount=500):
    current = driver.execute_script("return window.pageYOffset;")
    target = current + scroll_amount
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {current + (target - current) * (i + 1) / 10});")
        time.sleep(random.uniform(0.05, 0.15))

def clean_price(price_text):
    if not price_text: return 0
    clean = re.sub(r'[^\d]', '', price_text)
    return int(clean) if clean else 0

def analyze_text(text: str) -> str:
    if not text: return None
    found_tags = []
    # Simple keyword matching
    for kw in KEYWORDS:
        if kw in text:
            tag = f"#{kw}"
            # Special case for composite
            if kw == "자취" and "꿀템" in text:
                if "#자취꿀템" not in found_tags: found_tags.append("#자취꿀템")
            
            if tag not in found_tags:
                found_tags.append(tag)
                
    return ",".join(found_tags) if found_tags else None

def crawl_detail(driver, product_url):
    description = ""
    reviews = ""
    
    try:
        driver.get(product_url)
        # Safety delay as requested by user
        time.sleep(random.uniform(2, 3))
        
        # 1. Description (Wait up to 3s)
        try:
             desc_el = WebDriverWait(driver, 3).until(
                 EC.presence_of_element_located((By.CSS_SELECTOR, ".product_detail_area, #productDetail, .product-description"))
             )
             description = desc_el.text[:1000] 
        except: pass
        
        # 2. Reviews
        try:
            # Click Review Tab
            try:
                # Wait for tabs
                tabs = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '리뷰') or contains(text(), '후기')]"))
                )
                for t in tabs:
                    if t.tag_name in ['a', 'button', 'li', 'span']:
                         # Check if clickable
                         class_attr = t.get_attribute("class") or ""
                         if "review" in class_attr or "tab" in class_attr or "menu" in class_attr:
                             driver.execute_script("arguments[0].click();", t) # JS Click is faster/safer
                             time.sleep(1) # Short wait for API load
                             break
            except: pass
            
            # Extract reviews (Wait needed for dynamic load)
            try:
                review_els = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".review-item, .review_list li, .comment_list li"))
                )
                review_texts = []
                for r in review_els[:5]: # Top 5 reviews
                    review_texts.append(r.text.replace('\n', ' '))
                reviews = " || ".join(review_texts)
            except: pass
            
        except Exception as e:
            pass
            
    except Exception as e:
        print(f"Detail crawl failed: {e}")
        
    return description, reviews

def crawl_products():
    print("=" * 50)
    print("🚀 Daiso Mall Full Crawler (With Details)")
    print("=" * 50)
    
    init_database()
    os.makedirs(IMAGES_DIR, exist_ok=True)
    prevent_sleep()
    
    if not os.path.exists(CATEGORIES_FILE):
        print(f"Categories file not found: {CATEGORIES_FILE}")
        return

    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    print(f"Loaded {len(categories)} categories.")
    
    print("Initializing WebDriver...")
    try:
        driver = create_driver()
        print("WebDriver initialized successfully.")
    except Exception as e:
        print(f"WebDriver init failed: {e}")
        return

    total_products_crawled = 0
    
    try:
        processed_count = 0
        for cat in categories:
            if processed_count >= MAX_CATEGORIES:
                break
                
            cat_name = cat.get('name')
            cat_link = cat.get('link')
            cat_depth = cat.get('depth', 1)
            cat_parent = cat.get('parent')
            
            category_major = cat_parent if cat_depth == 2 else cat_name
            category_middle = cat_name if cat_depth == 2 else None
            
            if not cat_link:
                continue
                
            full_url = f"https://www.daisomall.co.kr{cat_link}"
            print(f"\n📂 [{processed_count+1}/{len(categories)}] Category: {cat_name} (Depth {cat_depth})")
            
            try:
                driver.get(full_url)
                time.sleep(3)
                
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".card__inner"))
                    )
                except:
                    print(f"  ⚠️ No products found (timeout)")
                    continue
                
                # Scroll loop
                last_count = 0
                scroll_attempts = 0
                target_per_cat = MAX_PRODUCTS_PER_CATEGORY
                
                while scroll_attempts < 20:
                    scroll_slowly(driver, random.randint(600, 1000))
                    random_delay(0.5, 1.5)
                    items = driver.find_elements(By.CSS_SELECTOR, ".card__inner")
                    if len(items) >= target_per_cat or (len(items) == last_count and scroll_attempts > 5):
                        break
                    scroll_attempts = 0 if len(items) != last_count else scroll_attempts + 1
                    last_count = len(items)
                
                # Extract products list first
                product_elements = driver.find_elements(By.CSS_SELECTOR, ".card__inner")
                products_to_crawl = []
                
                for el in product_elements:
                    if len(products_to_crawl) >= target_per_cat: break
                    try:
                        title_els = el.find_elements(By.CSS_SELECTOR, ".product-title")
                        if not title_els: continue
                        name = title_els[0].text.strip()
                        if not name: continue
                        
                        # Use insert_product's ignore policy instead of checking manually each time?
                        # Manual check saves visiting detail page.
                        # if product_exists(name):
                             # print(f"  Skipping existing: {name}")
                             # continue

                        # Extract Price
                        price_text = ""
                        try:
                            full_text = el.text
                            match = re.search(r'([\d,]+)\s*원', full_text)
                            if match: price_text = match.group(1)
                        except: pass
                        price = clean_price(price_text)
                        
                        # Extract Image
                        img_src = ""
                        try:
                            imgs = el.find_elements(By.TAG_NAME, "img")
                            if imgs: img_src = imgs[0].get_attribute("src")
                        except: pass
                        
                        # Link
                        link = ""
                        try:
                            links = el.find_elements(By.XPATH, ".//a[contains(@href, 'pdNo')]")
                            if links: link = links[0].get_attribute("href")
                            else:
                                links = el.find_elements(By.TAG_NAME, "a")
                                if links: link = links[0].get_attribute("href")
                        except: pass
                        
                        if name and link:
                            products_to_crawl.append({
                                "name": name, "price": price, "img_src": img_src, "link": link
                            })
                            
                    except: continue

                # Now process each product
                start_rank = 1
                for p in products_to_crawl:
                     print(f"   Crawling detail: {p['name'][:20]}...")
                     
                     original_window = driver.current_window_handle
                     driver.switch_to.new_window('tab')
                     
                     desc, reviews = crawl_detail(driver, p['link'])
                     
                     driver.close()
                     driver.switch_to.window(original_window)
                     
                     if desc: p['description'] = desc
                     if reviews: p['reviews'] = reviews
                     
                     full_text_for_analysis = (p['name'] + " " + (desc or "") + " " + (reviews or ""))
                     p['tags'] = analyze_text(full_text_for_analysis)
                     
                     image_name = None
                     image_path = None
                     if p['img_src']:
                        safe_name = "".join(c for c in p['name'][:20] if c.isalnum() or c in ' _-').strip()
                        image_name = f"{random.randint(1000,9999)}_{safe_name}.jpg"
                        image_path = download_image(p['img_src'], image_name)
                     
                     if insert_product(
                            rank=start_rank, 
                            name=p['name'], 
                            price=p['price'], 
                            image_url=p['img_src'], 
                            image_name=image_name, 
                            image_path=image_path,
                            category_major=category_major,
                            category_middle=category_middle,
                            description=p.get('description'),
                            reviews=p.get('reviews'),
                            tags=p.get('tags')
                        ):
                             print(f"   ✅ Saved {p['name'][:20]} (Tags: {p.get('tags')})")
                             total_products_crawled += 1
                             start_rank += 1
                             
                     time.sleep(1) 
                            
            except Exception as e:
                print(f"  ❌ Error crawling category: {e}")
                
            processed_count += 1
            
    except KeyboardInterrupt:
        print("\n🛑 Crawler stopped by user")
    finally:
        driver.quit()
        allow_sleep()
        
    print(f"\n🎉 COMPLETE! Total {total_products_crawled} new products crawled.")

if __name__ == "__main__":
    crawl_products()
