from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def inspect_category():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    debug_dir = "backend/database/debug_html"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    try:
        # URL for "신상" (New Products) or similar
        url = "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_01042?newPdYn=Y"
        # Or a standard category if that one is special
        # Try "뷰티/위생" -> /ds/exhCtgr/C208/CTGR_00014
        url = "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014"
        
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(10) # Wait for load
        
        driver.save_screenshot(os.path.join(debug_dir, "category_page.png"))
        print("Saved category_page.png")
        
        # Try to find product elements
        print("Searching for product elements...")
        potential_selectors = [
            ".product-item", ".goods-item", ".card", ".item", 
            "ul > li .image", ".goods_list .item", ".list_goods .item",
            ".product_list .item", "div[class*='product']", "div[class*='goods']"
        ]
        
        # Inspect .card__inner structure
        print("Inspecting .card__inner structure...")
        try:
            items = driver.find_elements(By.CSS_SELECTOR, ".card__inner")
            if len(items) > 0:
                print(f"Found {len(items)} .card__inner elements")
                el = items[0]
                print(f"  OuterHTML (first 1000 chars): {el.get_attribute('outerHTML')[:1000]}")
                
                # Check for specific children
                title = el.find_elements(By.CSS_SELECTOR, ".product-title")
                print(f"  Has .product-title: {len(title) > 0}")
                if len(title) > 0:
                    print(f"  Title text: {title[0].text}")
                    
                price = el.find_elements(By.CSS_SELECTOR, ".cost") # guessed class
                print(f"  Has .cost: {len(price) > 0}")
                
                img = el.find_elements(By.TAG_NAME, "img")
                print(f"  Has img: {len(img) > 0}")
                if len(img) > 0:
                    print(f"  Img src: {img[0].get_attribute('src')}")
        except Exception as e:
            print(f"Error inspecting card__inner: {e}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_category()
