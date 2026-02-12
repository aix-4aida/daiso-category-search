"""Product service - wraps database layer"""
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from database.database import (
    get_all_products as db_get_all_products,
    search_products as db_search_products,
    get_connection,
)
from database.category_matcher import CATEGORIES


class ProductService:
    """Service for product data access"""

    def get_all_products(self) -> list[dict]:
        """Get all products ordered by rank"""
        return db_get_all_products()

    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """Get a single product by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def search_products(self, keyword: str) -> list[dict]:
        """Search products by keyword (simple LIKE)"""
        return db_search_products(keyword)

    def get_categories(self) -> list[dict]:
        """Get all category groups"""
        result = []
        for major, middles in CATEGORIES.items():
            result.append({"major": major, "middles": list(middles.keys())})
        return result
