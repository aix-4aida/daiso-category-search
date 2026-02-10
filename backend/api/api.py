
from fastapi import APIRouter
from backend.api.endpoints import stt, search, categories

api_router = APIRouter()
api_router.include_router(stt.router, prefix="/stt", tags=["stt"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(categories.router, tags=["categories"])
