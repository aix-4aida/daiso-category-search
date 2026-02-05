import json

# Target Keywords for Representative Examples
# 1. Test Case #1 (Synonym): "테이프 클리너" (Dol-dol-i)
# 2. Product DB #1 (Category: 뷰티/위생): Any item with category_major="뷰티/위생"

db_path = 'c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json'

try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    example_synonym = None
    example_category = None
    
    for product in db:
        # 1. Find Synonym Example (Tape Cleaner)
        if "테이프 클리너" in product['name'] and not example_synonym:
            example_synonym = product
            
        # 2. Find Category Example (Beauty/Hygiene)
        if product.get('category_major', '') == "뷰티/위생" and not example_category:
            example_category = product # Just take the first one or a good one like Wet Wipes (501)
            
        if example_synonym and example_category:
            break
            
    print("=== Example 1: Synonym (테이프 클리너) ===")
    if example_synonym:
        print(json.dumps(example_synonym, indent=2, ensure_ascii=False))
    else:
        print("Not Found")

    print("\n=== Example 2: Category (뷰티/위생) ===")
    if example_category:
        print(json.dumps(example_category, indent=2, ensure_ascii=False))
    else:
        print("Not Found")

except Exception as e:
    print(f"Error: {e}")
