import json

keywords = ["스펀지", "네일", "청소포", "건전지", "음식물", "아세톤"]
db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    found_products = []
    seen_ids = set()
    
    for product in db:
        combined_text = (product.get('name', '') + " " + str(product.get('keywords', ''))).lower()
        for kw in keywords:
            if kw in combined_text and product['id'] not in seen_ids:
                found_products.append(product)
                seen_ids.add(product['id'])
                break
            
    # Print first few matches for each keyword
    print(json.dumps(found_products[:10], indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
