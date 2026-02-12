"""Initialize Elasticsearch index with product data from SQLite"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database.database import get_all_products
from database.category_matcher import init_category_tables, populate_categories, update_all_products
from app.services.es_service import ESService


async def main() -> None:
    print("=" * 50)
    print("[ES Index Initialization]")
    print("=" * 50)

    # Step 1: Ensure categories are populated
    print("\n[1/3] Updating product categories...")
    init_category_tables()
    populate_categories()
    update_all_products()

    # Step 2: Get all products
    products = get_all_products()
    print(f"\n[2/3] Found {len(products)} products in SQLite")

    # Step 3: Index to Elasticsearch
    print("\n[3/3] Indexing to Elasticsearch...")
    es = ESService()
    await es.create_index()
    count = await es.bulk_index(products)
    es.close()

    print(f"\n[OK] Indexed {count} products to Elasticsearch")


if __name__ == "__main__":
    asyncio.run(main())
