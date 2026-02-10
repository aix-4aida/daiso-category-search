import os
import sys
import io
from pathlib import Path

# Windows cp949 인코딩 문제 해결 (이모지 print 지원)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get('GOOGLE_API_KEY')
if api_key:
    print(f"DEBUG: GOOGLE_API_KEY loaded: {api_key[:10]}...")
else:
    print("WARNING: GOOGLE_API_KEY not found in environment")
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 1. Setup Sys Path to include Project Root
# (Allows importing 'backend', 'poc', etc.)
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# 2. Import New Backend Router
from backend.api.api import api_router

# 3. Create App
app = FastAPI(
    title="Daiso Category Search (Refactored)",
    description="Unified Entry Point for Kiosk & Backend",
    version="1.3.0"
)

# 4. Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include Backend Routers (STT, Search, Rerank)
# Prefix /search is defined in backend/api/api.py or endpoints?
# In backend/api/api.py: include_router(search.router, prefix="/search")
# So endpoints will be /search/audio, /search/rerank
app.include_router(api_router)

# 6. Mount Frontend (Kiosk/Admin/Mobile)
FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

@app.get("/")
def root():
    return {
        "message": "Daiso Category Search API is running.",
        "kiosk_url": "http://localhost:8000/frontend/kiosk/index.html"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
