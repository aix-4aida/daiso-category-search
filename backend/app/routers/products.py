"""Products router"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ProductResponse, CategoryResponse
from app.services.product_service import ProductService

router = APIRouter(tags=["products"])
service = ProductService()


@router.get("/products", response_model=list[ProductResponse])
async def get_products(skip: int = 0, limit: int = 50) -> list[ProductResponse]:
    """Get all products with pagination"""
    products = service.get_all_products()
    return [ProductResponse(**p) for p in products[skip : skip + limit]]


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int) -> ProductResponse:
    """Get a single product by ID"""
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(**product)


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories() -> list[CategoryResponse]:
    """Get all categories"""
    categories = service.get_categories()
    return [CategoryResponse(**c) for c in categories]
