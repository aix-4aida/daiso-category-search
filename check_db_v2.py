from backend.database.database import get_all_products, get_product_count

try:
    count = get_product_count()
    print(f"Total products: {count}")
    
    products = get_all_products()
    if products:
        ids = [p['id'] for p in products]
        print(f"ID Range: {min(ids)} ~ {max(ids)}")
        print(f"ID 549 exists: {549 in ids}")
        print(f"Sample IDs: {ids[:10]}")
    else:
        print("No products found in DB.")

except Exception as e:
    print(f"Error: {e}")
