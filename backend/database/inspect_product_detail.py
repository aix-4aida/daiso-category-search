import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1043992&recmYn=N"

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Headless off to see if needed, maybe on for debug
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def inspect_detail():
    driver = setup_driver()
    debug_dir = "backend/database/debug_html"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
        
    try:
        print(f"Loading {TARGET_URL}...")
        driver.get(TARGET_URL)
        time.sleep(5)
        
        driver.save_screenshot(os.path.join(debug_dir, "product_detail.png"))
        print("Saved product_detail.png")
        
        # 1. Product Description
        # Look for typical detail containers
        print("Searching for product description...")
        desc_selectors = [
            ".product_detail_area", ".detail_area", "#productDetail", 
            ".product-description", "div[data-role='product-detail']"
        ]
        
        for sel in desc_selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    print(f"  Found description candidate: {sel} (Count: {len(els)})")
                    print(f"  Text excerpt: {els[0].text[:100]}")
            except: pass
            
        # 2. Reviews
        print("Searching for Reviews...")
        # Check if there is a review tab
        try:
            # Save html to debug
            with open(os.path.join(debug_dir, "detail_page.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
                
            # Try to find tab by text
            tabs = driver.find_elements(By.XPATH, "//*[contains(text(), '리뷰') or contains(text(), '후기')]")
            print(f"Found {len(tabs)} elements with '리뷰' or '후기'")
            
            for t in tabs:
                if t.tag_name in ['a', 'button', 'li', 'span']:
                    print(f"  candidate: {t.tag_name}, text: {t.text}, class: {t.get_attribute('class')}")
                    # Try clicking if it looks like a tab
                    if "tab" in t.get_attribute("class") or "menu" in t.get_attribute("class") or "tab" in t.find_element(By.XPATH, "./..").get_attribute("class"):
                         try:
                             t.click()
                             print("  Clicked review tab candidate")
                             time.sleep(3)
                             driver.save_screenshot(os.path.join(debug_dir, "after_click_review.png"))
                         except: pass
        except Exception as e:
            print(f"Error finding reviews: {e}")
            
        # Inspect review items
        review_item_selectors = [
             ".review_list li", ".review-item", ".comment_list li", 
             ".list_review li", "div[class*='review']"
        ]
        
        for sel in review_item_selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                if len(els) > 0:
                    print(f"  Found reviews with selector: {sel} (Count: {len(els)})")
                    print(f"  First review text: {els[0].text[:200]}")
            except: pass

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_detail()
