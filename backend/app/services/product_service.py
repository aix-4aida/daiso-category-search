
from backend.database.database import search_products, get_products_by_category, get_product_by_id

class ProductService:
    def search(self, query: str):
        return search_products(query)
    
    def get_by_category(self, category: str):
        return get_products_by_category(category)
    
    def get_by_id(self, product_id: int):
        return get_product_by_id(product_id)

_product_service = None

def get_product_service():
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service
