# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered product search kiosk for Daiso stores. Users speak or type natural language queries in Korean; the system transcribes speech (STT), understands intent (NLU via Gemini), searches a SQLite product database, and returns results or asks clarifying questions.

## Commands

### Backend (Python 3.10, FastAPI)
```bash
pip install -r requirements.txt
uvicorn backend.api:app --reload --port 8000      # STT pipeline API
uvicorn backend.main:app --reload --port 8000      # Main comparison API
```

### Frontend (Next.js 14, React 18, TypeScript)
```bash
cd frontend
npm install
npm run dev       # Dev server on port 3000
npm run build     # Production build
npm run lint      # ESLint
```

### Utilities
```bash
python stt_to_json.py <input_audio_dir> <output.json>   # Batch audio transcription
python run_all_pipeline.py                                # Full pipeline orchestrator
```

### Environment
Requires `.env` in project root with `GEMINI_API_KEY`. Google Cloud Speech also needs `google_key.json` (path configured in `backend/config.yaml`).

## Architecture

### Data Flow
```
Audio/Text → STT (Whisper/Google) → Quality Gate → Policy Gate → NLU (Gemini 2.0 Flash) → DB Search → Response
```

### Backend (`backend/`)

**API Layer** — Two FastAPI apps coexist:
- `api.py` — STT pipeline endpoints (`POST /stt/process`, `POST /stt/compare`, `GET /health`)
- `main.py` — Chat endpoint with LangGraph agent (`POST /api/chat`)
- `ws_stt.py` — WebSocket real-time streaming STT (`WS /ws/stt`)

**STT Module** (`backend/stt/`) — Speech-to-text with dual provider support:
- `adapters.py` — `WhisperAdapter` (faster-whisper, local) and `GoogleSTTAdapter` (Cloud Speech v1)
- `quality_gate.py` — Validates transcription (min length, confidence threshold, nonsense pattern rejection)
- `policy_gate.py` — Routes by intent: fixed locations (화장실, 계산대), unsupported queries (배달, 환불), or product search
- `types.py` — Pydantic models for STT results and pipeline stages
- Config lives in `backend/config.yaml` (model sizes, thresholds, gate rules)

**LangGraph Agent** (`backend/logic/agent_graph.py`) — 5-node cyclic state machine:
1. **NLU** — Gemini 2.0 Flash intent classification + slot extraction (item, attrs, category_hint, query_rewrite)
2. **Search** — SQLite keyword search; falls back to LLM keyword inference on zero results
3. **Ambiguity Check** — Triggers clarification if >5 results, 0 results, or NLU flags ambiguity; loop prevention detects if previous turn was already a question
4. **Clarification** — Generates drill-down tail question with category context
5. **Response** — Formats final answer

State is persisted per session via `MemorySaver`. Conversation history is passed to NLU for context resolution.

**NLU** (`backend/logic/nlu.py`) — Gemini API calls for intent analysis, tail question generation, and keyword inference. System prompts in `prompts.py` enforce Korean output.

**Database** (`backend/database/`) — SQLite (`products.db`) with 601 Daiso products. `database.py` handles search (LIKE queries) and insert operations. `category_matcher.py` provides keyword-based category matching and drill-down context. `embeddings.py` has CLIP-based multimodal embedding support.

### Frontend (`frontend/`)
Next.js 14 App Router with Tailwind CSS:
- `/` — Landing page (entry to kiosk)
- `/kioskmode` — Interactive chat UI for product search

### POC Directory (`poc/`)
Experimental scripts organized by contributor (bjy, kdg, kms, lyg, lsy, intent). These are research artifacts, not production code.

## Key Conventions

- All user-facing text and LLM responses are in Korean
- Intent types: `PRODUCT_LOCATION`, `OTHER_INQUIRY`, `UNSUPPORTED`
- Whisper defaults to "medium" model on CPU with int8 quantization; falls back to "small" on OOM
- No formal test suite exists; testing is done via POC scripts and manual verification
- Main branch is `dev`
