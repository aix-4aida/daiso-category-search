
# backend/main.py
import sys
from pathlib import Path

# Add project root to sys.path to ensure imports work correctly
sys.path.append(str(Path(__file__).resolve().parent.parent))

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

@app.get("/api/recommended")
def get_recommended():
    import json, os, random
    products_path = os.path.join(os.path.dirname(__file__), "database", "products.json")
    try:
        with open(products_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        # Filter: 국민득템 with valid name, price, image
        valid = [p for p in products if p.get("name") and p.get("price") and p.get("image") and "noimage" not in p["image"]]
        # Pick 4 random items (or fewer if not enough)
        selected = random.sample(valid, min(4, len(valid)))
        return {"products": selected}
    except Exception as e:
        return {"products": [], "error": str(e)}

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
