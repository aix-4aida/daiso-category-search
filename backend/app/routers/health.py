
from fastapi import APIRouter
from backend.app.services.stt_service import get_stt_service

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

@router.get("")
def health_check():
    """Health check endpoint"""
    stt_service = get_stt_service()
    return {
        "status": "healthy",
        "whisper_loaded": stt_service.whisper_adapter is not None,
        "google_ready": stt_service.google_adapter.client is not None if stt_service.google_adapter else False,
        "version": "2.0.0-ml-api"
    }
