from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import sys

# Flush valid output immediately
sys.stdout.reconfigure(line_buffering=True)

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

def discover_categories():
    driver = setup_driver()
    debug_dir = "backend/database/debug_html"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    try:
        print("Loading main page...")
        driver.get("https://www.daisomall.co.kr/ds")
        time.sleep(5)
        
        # Click the Category button
        print("Clicking Category button...")
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-btn"))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
        except Exception as e:
            print(f"Error clicking category button: {e}")
            return

        # Find depth1 items
        print("Finding depth1 items...")
        depth1_items = driver.find_elements(By.CSS_SELECTOR, ".category-list.depth1 > li > button")
        print(f"Found {len(depth1_items)} depth1 items.")
        
        target_indices = [1] # Try '뷰티/위생' (index 1 usually, 0 is '국민득템')
        
        for idx in target_indices:
            if idx < len(depth1_items):
                item = depth1_items[idx]
                name = item.text
                print(f"Clicking depth1 item: {name}")
                driver.execute_script("arguments[0].click();", item)
                time.sleep(2)
                
                # Save HTML
                filename = f"depth1_clicked_{idx}.html"
                with open(os.path.join(debug_dir, filename), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Saved {filename}")
                
                 # Take screenshot
                driver.save_screenshot(os.path.join(debug_dir, f"depth1_clicked_{idx}.png"))

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.save_screenshot(os.path.join(debug_dir, "error_investigate.png"))
    finally:
        driver.quit()

if __name__ == "__main__":
    discover_categories()
