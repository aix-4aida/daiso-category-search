
# backend/main.py
import sys
from pathlib import Path

# Add project root to sys.path to ensure imports work correctly
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
