# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-10

### Added
- **Real Voice Search**: Replaced simulated voice search with real browser `MediaRecorder` API and backend STT processing.
- **Image-based Maps**: Migrated from grid-based maps to actual store layout images (`.png`) with percentage-based coordinate mapping.
- **UX/UI Derivation Process**: Added comprehensive documentation on the design system origin (`docs/ux_ui_derivation_process.md`).

### Fixed
- **Search Fallback**: Improved backend robustnes by adding automatic fallback to local SQLite BM25 search when remote engines (Qdrant/Elastic) are unreachable.
- **Nginx 502 Error**: Resolved proxy communication issues in AWS Lightsail by updating internal service routing.
- **STT Environment**: Fixed audio conversion failures by installing FFmpeg in the Docker container and optimizing the Whisper model for low-resource environments.

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
