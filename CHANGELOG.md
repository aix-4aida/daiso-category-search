# Changelog

All notable changes to this project will be documented in this file.

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
