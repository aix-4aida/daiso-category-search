"""
Daiso Mall Page Inspector
Dumps HTML of Ranking Page and First Product Detail Page
to verify structure for category extraction.
"""
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://www.daisomall.co.kr/ds"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'debug_html')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

def create_driver():
    options = Options()
    # options.add_argument('--headless=new') # Run visibly to ensure it works
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def save_html(content, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Saved: {filepath}")

def inspect():
    print("🚀 Inspecting Daiso Mall Structure...")
    driver = create_driver()
    try:
        # 1. Main Page (For Categories)
        print(f"📍 Visiting {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(5)
        
        save_html(driver.page_source, "main_page.html")
        print("✅ Saved main_page.html - Check this for GNB/Category structure")

        # 2. Try to click a "All Category" menu or similar if possible (simplified: just dump main)
        # Usually nav is in <nav> or GNB class
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect()
