import json

db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    for product in db:
        combined = (product['name'] + " " + str(product.get('keywords', ''))).lower()
        if "크리너" in combined or "클리너" in combined:
            if "테이프" in combined or "롤" in combined or "먼지" in combined:
                 print(json.dumps(product, indent=2, ensure_ascii=False))
                 break

except Exception as e:
    print(f"Error: {e}")
