"""Health check router"""
from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health status"""
    from app.services.es_service import check_es_health
    from app.services.qdrant_service import check_qdrant_health

    db_ok = True
    try:
        from database.database import get_product_count
        get_product_count()
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if all([db_ok]) else "degraded",
        services={
            "database": db_ok,
            "elasticsearch": await check_es_health(),
            "qdrant": await check_qdrant_health(),
        },
    )
