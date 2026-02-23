# Changelog

All notable changes to this project will be documented in this file.

## [0.7.0] - 2026-02-24

### Added
- **NLU Natural Language Search**: Enhanced NLU prompt to handle situation/description/problem-solving queries (8 scenarios).
  - "욕실 바닥이 미끄러운데 뭐 깔면?" → 욕실매트
  - "벽에 못 안 박고 액자 걸고 싶어" → 접착후크/액자걸이
  - "투명하고 동그란 거 화장품 담는 거" → 화장품 정리함
  - "냉장고에서 냄새 나는데?" → 냉장고 탈취제
  - Broad category expansion (e.g., "컴퓨터 용품" → USB, 마우스, 키보드)
- **TDD Test Suite**: 8 natural language search scenario tests (`_test/test_search_scenarios.py`).
- **Homepage Card**: Added `ssakstick_banner.png` for 싹스틱 card (was using wipes_banner).
- **Category Map Page**: SVG section labels with category filter sidebar (B1/B2 floors).
- **Mobile QR Page PoC**: SVG map overlay with route, product card, action buttons.

### Fixed
- **Search Query Priority**: Changed `query = item or query_rewrite` → `query_rewrite or item` for richer contextual search.
- **API URL**: Replaced hardcoded `localhost:8000` with relative `/search/text` in `app.js` (was breaking Edge browser).
- **Mobile Handoff Page**: Fixed logo color ('있' now red), AR navi text (PoC, not kiosk), map rendering (`object-fit: contain`).
- **Cache Busting**: Updated all HTML cache busters to v=51.
- **Map SVG Alignment**: Fixed CSS aspect-ratio and B1 waypoint coordinates for accurate marker placement.
- **Score Gap Filter**: Relaxed from 30% to 20% threshold for more inclusive search results.

### Changed
- **Reranker Prompt**: Improved ranking rules with direct match priority and accessory demotion.
- **Category SVG**: Changed `preserveAspectRatio` from `none` to `xMidYMid meet`.


## [0.3.1] - 2026-02-22

### Fixed
- **ChromaDB Index**: Fixed an issue where the `알콜솜` query returned incorrect results in production by rebuilding the local ChromaDB index using `rebuild_chroma_index.py` and pushing the updated index to AWS Lightsail.
- **Git Tracking**: Added temporary deployment configs (`deploy_*.json`), test scripts, and system logs to `.gitignore` to prevent repository clutter.


## [0.1.0] - 2026-02-10

### Added
- **Real Voice Search**: Replaced simulated voice search with real browser `MediaRecorder` API and backend STT processing.
- **Image-based Maps**: Migrated from grid-based maps to actual store layout images (`.png`) with percentage-based coordinate mapping.
- **UX/UI Derivation Process**: Added comprehensive documentation on the design system origin (`docs/ux_ui_derivation_process.md`).

### Fixed
- **Search Fallback**: Improved backend robustnes by adding automatic fallback to local SQLite BM25 search when remote engines (Qdrant/Elastic) are unreachable.
- **Nginx 502 Error**: Resolved proxy communication issues in AWS Lightsail by updating internal service routing.
- **STT Environment**: Fixed audio conversion failures by installing FFmpeg in the Docker container and optimizing the Whisper model for low-resource environments.

## [0.3.0] - 2026-02-19

### Changed
- **Crawler Logic**: Updated `crawler_full.py` to allow updating existing products (`ON CONFLICT DO UPDATE`) instead of skipping them, enabling detail data backfilling.
- **Database**: Modified `insert_product` in `database.py` to support upsert operations for seamless data updates.
- **Git Config**: Optimized `.gitignore` to exclude heavy virtual environment files (`.venv`) and temporary debug files (`debug_html`).

## [0.2.0] - 2026-02-13

### Added
- **Lightsail Deployment Prep**:
  - Created `DEPLOYMENT.md` guide for AWS Lightsail Container Service.
  - Added `docker-compose.prod.yml` for local production simulation (Nginx + Backend).
  - Configured `nginx.conf` and `Dockerfile.frontend` for proper API proxying (`/api/` -> `backend:8000`).
- **Map System v14**:
  - **BFS Pathfinding**: Implemented Breadth-First Search to draw realistic walking paths instead of straight lines.
  - **Smart Mapping**: Added category-based fallback logic (Middle -> Major -> Default) for products without specific location codes.
  - **Enhanced UI**: Added "Current Location" label and truncated product name tooltips on map markers.

### Changed
- **Resource Optimization**: Added `DISABLE_WHISPER` environment variable to optionally skip loading the heavy Whisper model on low-memory instances.
- **Frontend API**: Updated `app.js` to support relative paths (`/api/...`) for Nginx routing (rolled back to absolute for local dev with instructions).
- **Dependency Management**: Created `requirements-lightsail.txt` (MVP) and `.dockerignore` for lighter builds.

### Fixed
- **Local Dev 404**: Resolved API 404 errors in local environments by clarifying absolute vs relative path usage in docs and code.
- **Whisper Safety**: Added error handling in `stt_service.py` to prevent crashes if `faster-whisper` is missing or fails to load.

## [0.0.1] - 2026-02-06

### Initial Release
- **Unified Search Service**: Consolidating Backend and Frontend.
- **Backend Architecture**:
  - `backend/api`: FastAPI Endpoints (Search, STT).
  - `backend/services`: Business Logic (Search, STT, Intent, Pipeline).
  - `backend/search`: Search Infrastructure (Elasticsearch, Qdrant Adapters).
  - `backend/stt`: STT Infrastructure (Google, Whisper Adapters).
- **Frontend**:
  - `kiosk`: Tablet UI for product search.
  - `mobile`: AR Navigation UI.
- **Infrastructure**:
  - Docker Compose for Qdrant (Vector DB) and Elasticsearch (Sparse DB).
