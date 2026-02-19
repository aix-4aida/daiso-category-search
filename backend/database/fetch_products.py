import json
import os
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
CATEGORIES_FILE = 'backend/database/categories.json'
OUTPUT_FILE = 'backend/database/products.json'
MAX_PRODUCTS_PER_CATEGORY = 20
MAX_CATEGORIES = 1 # Set high to do all, or low for testing

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def clean_price(price_text):
    if not price_text: return 0
    # Remove '원', ',', and whitespace
    clean = re.sub(r'[^\d]', '', price_text)
    return int(clean) if clean else 0

def fetch_products():
    # Load categories
    if not os.path.exists(CATEGORIES_FILE):
        print(f"Categories file not found: {CATEGORIES_FILE}")
        return

    with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    print(f"Loaded {len(categories)} categories.")
    
    products = []
    
    driver = setup_driver()
    
    try:
        processed_count = 0
        for cat in categories:
            if processed_count >= MAX_CATEGORIES:
                break
                
            # Prefer leaf categories (Depth 2), but if it's a Depth 1 with no parent, use it.
            # Actually, we should probably crawl all distinct links.
            # But let's prioritize Depth 2 or Depth 1 if it has a link.
            
            cat_name = cat.get('name')
            cat_link = cat.get('link')
            
            if not cat_link:
                continue
                
            full_url = f"https://www.daisomall.co.kr{cat_link}"
            print(f"Crawling category: {cat_name} ({full_url})")
            
            try:
                driver.get(full_url)
                time.sleep(3)
                
                # Wait for products
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".card__inner"))
                    )
                except:
                    print(f"  No products found for {cat_name}")
                    continue
                
                # Scroll a bit
                driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(2)
                
                product_elements = driver.find_elements(By.CSS_SELECTOR, ".card__inner")
                print(f"  Found {len(product_elements)} products")
                
                count = 0
                for el in product_elements:
                    if count >= MAX_PRODUCTS_PER_CATEGORY:
                        break
                    
                    try:
                        # Extract data
                        title = el.find_element(By.CSS_SELECTOR, ".product-title").text.strip()
                        
                        # Price is tricky. Try finding element with '원' text or just get all text
                        price_text = ""
                        try:
                            # Try generic price classes first if known, otherwise search text
                            # From debug, structure is complex. Let's look for any child with text containing '원'
                            # Optimize: Get all text and regex it
                            full_text = el.text
                            # Find format like "1,000원" or "1000원"
                            match = re.search(r'([\d,]+)\s*원', full_text)
                            if match:
                                price_text = match.group(1)
                        except:
                            pass
                            
                        price = clean_price(price_text)
                        
                        # Image
                        img_src = ""
                        try:
                            img = el.find_element(By.TAG_NAME, "img")
                            img_src = img.get_attribute("src")
                        except:
                            pass
                            
                        # Link
                        # Try to find 'a' tag in the thumb area
                        link = ""
                        try:
                            link_el = el.find_element(By.TAG_NAME, "a")
                            link = link_el.get_attribute("href")
                        except:
                            pass
                        
                        # Rank (Category based)
                        # We don't have global rank, but we can store category_rank
                        rank = count + 1
                        
                        product = {
                            "category": cat_name,
                            "category_id": cat.get('id', ''),
                            "rank": rank,
                            "name": title,
                            "price": price,
                            "image": img_src,
                            "link": link
                        }
                        
                        products.append(product)
                        count += 1
                        
                    except Exception as ex:
                        # product might be missing title etc
                        continue
                        
                processed_count += 1
                
            except Exception as e:
                print(f"Error crawling category {cat_name}: {e}")
                
            time.sleep(random.uniform(1, 2))
            
    finally:
        driver.quit()
        
    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(products)} products to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_products()
