"""Search router"""
from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])
search_service = SearchService()


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """Main search endpoint - hybrid search pipeline"""
    return await search_service.search(request.query)
