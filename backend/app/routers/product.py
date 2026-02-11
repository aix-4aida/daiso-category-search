
from fastapi import APIRouter, HTTPException
from backend.app.services.product_service import get_product_service, ProductService

router = APIRouter(
    prefix="/api/products",
    tags=["Product"]
)

@router.get("/search")
async def products_search(q: str = ""):
    """Text-based product search"""
    if not q:
        return []
    service = get_product_service()
    return service.search(q)

@router.get("/category/{category}")
async def products_by_category(category: str):
    """Get products by category"""
    service = get_product_service()
    return service.get_by_category(category)

@router.get("/{product_id}")
async def product_by_id(product_id: int):
    """Get single product by ID"""
    service = get_product_service()
    result = service.get_by_id(product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result
