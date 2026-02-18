from backend.database.database import get_product_by_id, get_product_count, get_all_products

print(f"Total products: {get_product_count()}")
p81 = get_product_by_id(81)
print(f"Product 81: {p81}")

if not p81:
    print("Product 81 not found. Checking first 5 products:")
    all_p = get_all_products()
    for p in all_p[:5]:
        print(p)
