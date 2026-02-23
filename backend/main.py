
# backend/main.py
import sys
import types
from pathlib import Path

# Add project root to sys.path to ensure imports work correctly
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ── Fix: backend/api.py(구버전)와 backend/api/ 패키지 이름 충돌 해결 ──
# backend/api.py 파일이 존재하면 Python이 api/ 디렉토리를 패키지로 인식하지 못하므로
# sys.modules에 backend.api를 패키지로 강제 등록
_api_pkg_dir = Path(__file__).resolve().parent / "api"
if _api_pkg_dir.is_dir():
    _pkg = types.ModuleType("backend.api")
    _pkg.__path__ = [str(_api_pkg_dir)]
    _pkg.__package__ = "backend.api"
    sys.modules["backend.api"] = _pkg

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.api.api import api_router

# Initialize FastAPI app
app = FastAPI(
    title="Daiso STT Pipeline API",
    description="Speech-to-Text pipeline with modular architecture",
    version="1.2.0-refactor"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router)

# WebSocket STT
from backend.ws_stt import handle_streaming_stt
@app.websocket("/ws/stt")
async def websocket_endpoint(websocket: WebSocket):
    await handle_streaming_stt(websocket)

@app.get("/")
def root():
    return {
        "service": "Daiso STT Pipeline",
        "version": "1.2.0-refactor",
        "status": "running"
    }

@app.get("/health")
def health_check():
    from backend.services.stt_service import whisper_adapter, google_adapter
    return {
        "status": "healthy",
        "whisper_model": whisper_adapter.model_size,
        "google_ready": google_adapter.client is not None
    }

if __name__ == "__main__":
    import uvicorn
    # Use import string for reload to work
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
