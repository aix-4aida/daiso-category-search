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

def fetch_categories():
    driver = setup_driver()
    output_file = "backend/database/categories.json"
    
    try:
        print("Loading main page...")
        driver.get("https://www.daisomall.co.kr/ds")
        time.sleep(5)
        
        print("Traversing Vue component tree to find CtgrLayer...")
        # Script to traverse tree and find CtgrLayer
        script = """
        function traverse(node, depth) {
            if (!node) return null;
            if (depth > 20) return null; 
            
            var name = node.$options.name || (node.$vnode ? node.$vnode.tag : 'Anonymous');
            
            if (name === 'CtgrLayer') {
                return {
                    name: name,
                    data: node.$data
                };
            }
            
            if (node.$children) {
                for (var i = 0; i < node.$children.length; i++) {
                    var result = traverse(node.$children[i], depth + 1);
                    if (result) return result;
                }
            }
            return null;
        }
        
        try {
            var root = window.$nuxt ? window.$nuxt.$root : (document.querySelector('#__nuxt') ? document.querySelector('#__nuxt').__vue__ : null);
            if (root) {
                return traverse(root, 0) || { error: 'CtgrLayer not found' };
            } else {
                return { error: 'Root Vue instance not found' };
            }
        } catch(e) {
            return { error: e.toString() };
        }
        """
        
        result = driver.execute_script(script)
        
        if not result or result.get('error'):
            print(f"Failed to find CtgrLayer: {result.get('error') if result else 'Unknown error'}")
            # Try clicking category matching to ensure it loads
            print("Trying to click category button...")
            try:
                btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-btn"))
                )
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(5)
                # Retry script
                result = driver.execute_script(script)
            except Exception as e:
                print(f"Click failed: {e}")

        if not result or result.get('error'):
             print("Final attempt failed.")
             return

        print("CtgrLayer found. Extracting categories...")
        layer_data = result.get('data', {})
        category_tree = layer_data.get('categoryTree', [])
        
        all_categories = []
        
        for d1 in category_tree:
            if not isinstance(d1, dict): continue
            
            d1_title = d1.get('title') or d1.get('name') or d1.get('dispCtgrNm') or d1.get('ctgrNm') or d1.get('iconAlt') or d1.get('menu') or "Unknown"
            d1_link = d1.get('link') or d1.get('subMenuLink')
            
            # debug if unknown
            if d1_title == "Unknown":
                 print(f"Unknown D1 Keys: {list(d1.keys())}")
                 if 'menu' in d1:
                     print(f"Menu content: {d1['menu']}")
            
            # Add Depth 1 itself? Usually depth 1 is just a container, but it has a link.
            if d1_link:
                 all_categories.append({
                    "name": d1_title,
                    "link": d1_link,
                    "depth": 1,
                    "parent": None
                })
            
            sub_arr = d1.get('subCateArr', [])
            if not sub_arr: continue
            
            if isinstance(sub_arr, list):
                for item in sub_arr:
                    # Item could be dict or list
                    items_to_process = [item] if isinstance(item, dict) else (item if isinstance(item, list) else [])
                    
                    for sub in items_to_process:
                        if not isinstance(sub, dict): continue
                        
                        sub_title = sub.get('subTitle') or sub.get('name') or sub.get('title')
                        if not sub_title: continue
                        
                        sub_link = sub.get('link') or sub.get('subMenuLink')
                        
                        if sub_link:
                            all_categories.append({
                                "name": sub_title,
                                "link": sub_link,
                                "depth": 2,
                                "parent": d1_title
                            })

        print(f"Extracted {len(all_categories)} categories.")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_categories, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_categories()
