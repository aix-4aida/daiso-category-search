import json

target_ids = ["1601", "3701"]
db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    found_products = []
    for product in db:
        if str(product.get('id')) in target_ids:
            found_products.append(product)
            
    print(json.dumps(found_products, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
