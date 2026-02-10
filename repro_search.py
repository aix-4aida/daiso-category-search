import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from backend.database.database import search_products, get_products_by_category

print("Searching for '문구'...")
results = search_products("문구")
print(f"search_products('문구') results: {len(results)}")

print("\nSearching category '문구'...")
cat_results = get_products_by_category("문구")
print(f"get_products_by_category('문구') results: {len(cat_results)}")

if len(results) == 0 and len(cat_results) == 0:
    print("\nFAILURE: '문구' not found in name or category lookup.")
else:
    print("\nSUCCESS: '문구' found.")
