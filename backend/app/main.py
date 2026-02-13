"""FastAPI application entry point"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, products, search

app = FastAPI(
    title="어디다있소 - Daiso Kiosk API",
    version="0.1.0",
    description="다이소 매장 내 상품 위치 안내 키오스크 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(search.router, prefix="/api")

# Static files: product images
if os.path.isdir(settings.IMAGES_DIR):
    app.mount("/static/images", StaticFiles(directory=settings.IMAGES_DIR), name="images")

# Static files: store maps
maps_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "maps")
if os.path.isdir(maps_dir):
    app.mount("/maps", StaticFiles(directory=maps_dir), name="maps")

# Production: serve React SPA from frontend/dist
frontend_dist = os.path.normpath(settings.FRONTEND_DIST)
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="spa-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str) -> FileResponse:
        """Serve React SPA - all non-API routes return index.html"""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
