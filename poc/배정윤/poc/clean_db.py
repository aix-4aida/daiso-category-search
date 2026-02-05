import json
import re
import os

INPUT_FILE = "data/poc_v4_mock_product_db.json"
OUTPUT_FILE = "data/poc_v5_mock_product_db.json"

def remove_html_tags(text):
    if not isinstance(text, str):
        return text
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cleaned_count = 0
    for product in data:
        # Clean specific fields that might contain HTML
        for field in ["searchable_desc", "raw_detail_text", "desc"]:
            if field in product:
                original = product[field]
                cleaned = remove_html_tags(original)
                if original != cleaned:
                    product[field] = cleaned
                    cleaned_count += 1
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Cleaned {cleaned_count} fields.")
    print(f"📁 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_data()
