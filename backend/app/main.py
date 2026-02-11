
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.app.core.config import get_settings
from backend.app.routers import voice, product, health
# Initialize services on startup
from backend.app.services.stt_service import get_stt_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Daiso ML API Service...")
    
    # Initialize settings and services
    settings = get_settings()
    stt_service = get_stt_service() # This triggers strict initialization
    
    print("✅ Services initialized")
    yield
    print("👋 Shutting down...")

app = FastAPI(
    title="Daiso Category Search ML API",
    description="Unified ML API for STT, Product Search, and Pipeline Logic",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for now, or strict ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)

# voice router has:
# @router.post("/stt/process") -> /api/stt/process
# @router.post("/api/search/voice") -> /api/api/search/voice (Doubled?)
# voice.py defined router = APIRouter(tags=["Voice"]) without prefix.
# But inside it: @router.post("/stt/process") and @router.post("/api/search/voice").
# So if I include it with prefix="/api", it becomes /api/stt/process and /api/api/search/voice.
# Existing frontend probably uses /api/search/voice.
# So I should include it without prefix, or fix the paths in router.

# Let's include without prefix for voice router to match existing paths
app.include_router(voice.router) 
app.include_router(product.router) # product router has prefix="/api/products"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
