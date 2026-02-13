# 🚀 Lightsail Container Deployment Guide

This document assists in deploying the **Daiso Category Search** application to AWS Lightsail Container Services.

## 1. Architecture Overview
- **Deployment Strategy**: Single Container (Nginx + Uvicorn) OR Multi-Container (Frontend + Backend).
    - *Current Codebase* supports Multi-Container logic (Frontend/Nginx container + Backend/Python container).
- **Communication**: 
    - Frontend JS calls `/api/search/...`.
    - Nginx proxies `/api/*` to the Backend container (`backend:8000`).
    - **Note**: Ensure your Lightsail deployment or Docker Compose defines a service named `backend`.

## 2. Changes Applied for Production
### ✅ Frontend
- **Current State**: `app.js` uses `http://localhost:8000/search/text` for local development (no Nginx).
- **For Production**: Change this to `/api/search/text` in `app.js` before building the Docker image. This allows Nginx to handle routing.

### ✅ Backend (Optimization)
- **Whisper Control**: Added `DISABLE_WHISPER` environment variable.
    - Set `DISABLE_WHISPER=true` in Lightsail to skip loading the heavy Whisper model (saves ~500MB RAM).
    - The system will fallback to Google STT or no STT.

### ✅ Nginx Configuration
- **Proxy Rules**: Configured to proxy `/api/` requests to `http://backend:8000`.
- **SPA Support**: `try_files $uri /index.html` added for Single Page Application routing.

## 3. Environment Variables (Lightsail Console)
Set these variables in yourLightsail Container Service configuration:

| Variable | Recommended Value | Description |
|----------|-------------------|-------------|
| `DISABLE_WHISPER` | `true` | Skip Whisper model loading (Save RAM) |
| `GOOGLE_API_KEY` | `(Your Key)` | For Reranking (Gemini) |
| `QDRANT_URL` | `http://localhost:6333` | If running Qdrant sidecar |
| `ELASTIC_URL` | `http://localhost:9200` | If running Elastic sidecar |
| `OPENAI_API_KEY` | `(Your Key)` | (If used elsewhere) |

## 4. Docker Build & Push
Ensure your local `products.db` and `chroma_db` are up to date before building, as they are copied into the image.

```bash
# Backend Build
docker build -t daiso-backend .

# Frontend Build
docker build -f Dockerfile.frontend -t daiso-frontend .
```

## 5. Deployment Step Verification
1.  **Frontend Load**: Open the public URL. Static files should load.
2.  **Search Test**: Try a text search.
    - Check Network tab: Request should go to `GET /api/search/text`.
    - Nginx should proxy to Backend.
    - Backend should respond with JSON.
3.  **Logs**: Check Container logs if 500 errors occur.

## 6. Local Testing (Simulating Production)
To test the "Production" setup (Nginx + Backend) locally on Windows:

1.  **Frontend URL**: Ensure `app.js` uses `/api/search/text` (Relative Path).
2.  **Run Docker Compose**:
    ```bash
    # Run all services (Frontend, Backend, DBs)
    docker-compose -f docker-compose.prod.yml up --build
    ```
3.  **Access App**: Open Browser at `http://localhost:3000`.
    - Nginx is running on port 3000.
    - It proxies `/api/` to the backend container.
