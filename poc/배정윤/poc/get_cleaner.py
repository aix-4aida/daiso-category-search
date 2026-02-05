import json

db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    for product in db:
        if "클리너" in product['name']:
            print(json.dumps(product, indent=2, ensure_ascii=False))
            break

except Exception as e:
    print(f"Error: {e}")
