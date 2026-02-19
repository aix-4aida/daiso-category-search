from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

def inspect_nuxt():
    driver = setup_driver()
    debug_dir = "backend/database/debug_html"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    try:
        print("Loading main page...")
        driver.get("https://www.daisomall.co.kr/ds")
        time.sleep(5)
        
        # Click Category button
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        print("Clicking Category button...")
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-btn"))
            )
            driver.execute_script("arguments[0].click();", btn)
            print("Clicked Category button via JS")
            time.sleep(5)
        except Exception as e:
            print(f"Error clicking category button: {e}")

        print("Traversing Vue component tree for all matches...")
        script = """
        var matches = [];
        function traverse(node, depth) {
            if (!node) return;
            if (depth > 15) return; 
            
            var name = node.$options.name || (node.$vnode ? node.$vnode.tag : 'Anonymous');
            
            // Collect if name contains relevant keywords or data has relevant keys
            var relevantName = /Gnb|Header|Category|Menu/i.test(name);
            var hasData = node.$data && (node.$data.depth1List || node.$data.categoryList || node.$data.gnb || node.$data.categories);
            
            if (relevantName || hasData) {
                matches.push({
                    name: name,
                    data: node.$data,
                });
            }
            
            // Traverse children
            if (node.$children) {
                for (var i = 0; i < node.$children.length; i++) {
                    traverse(node.$children[i], depth + 1);
                }
            }
        }
        
        try {
            var root = window.$nuxt ? window.$nuxt.$root : (document.querySelector('#__nuxt') ? document.querySelector('#__nuxt').__vue__ : null);
            if (root) {
                traverse(root, 0);
                return matches;
            } else {
                return { error: 'Root Vue instance not found' };
            }
        } catch(e) {
            return { error: e.toString() };
        }
        """
        component_state = driver.execute_script(script)
        
        if component_state:
            print("Found Component state.")
            with open(os.path.join(debug_dir, "component_tree_search.json"), "w", encoding="utf-8") as f:
                json.dump(component_state, f, ensure_ascii=False, indent=2)
            print("Saved component_tree_search.json")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_nuxt()
