# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ✅ 응답/문서 언어: **한국어**  
> ✅ 핵심 목표: **(1) Lightsail 배포 가능 유지 (2) STT 제외 E2E 지연 단축 (3) 기존 동작 회귀 방지(현상 유지 테스트)**  
> ✅ 작업 방식: **측정 → 가장 느린 스텝 개선 → 전후 비교 리포트**

---

## 0) CRITICAL RULES (반드시 준수)

### Deployment Target
- Target: **AWS Lightsail (Linux)**
- **Windows 전용 가정 금지** (예: `C:\Users\...` 경로, Windows 전용 명령)
- **DB/응답(payload)에 OS 종속 절대경로 저장 금지**
  - DB에는 **상대경로 또는 URL**만 저장/사용해야 함
  - 코드 내부에서 `Path(...).resolve()`로 **실행 시 경로 계산**을 하는 것은 가능하지만, **DB 컬럼/응답 JSON에는 절대경로를 넣지 말 것**

### poc/ Directory is READ-ONLY (팀 룰)
- `poc/` 폴더의 `.py` 파일은 **수정/이동/삭제 금지**
- 새 코드/수정 코드는 **`service/` 또는 `backend/`에만** 작성
- poc 스크립트 사용이 필요하면:
  - `service/pipeline/`에서 **import 또는 subprocess로만 조립**
  - poc 스크립트가 내부적으로 `poc/data/*.json`에 쓰는 것은 허용(스크립트 본래 동작)

### Git Rules
- Claude Code는 **git commit/push 금지**
- 작업 완료 후 사용자가 확인:
  - `git diff --name-only HEAD -- poc/` → poc 변경이 없는지 확인

### Code Change Rules
- 변경 전: **계획(가설/검증방법/측정 포인트)** 먼저 제시
- 성능 개선 PR은 **전/후 latency 리포트**가 반드시 포함되어야 함
- API/응답 스키마는 호환성 유지 (명시적 지시 없으면 breaking change 금지)

---

## 1) Project Overview

AI-powered product search kiosk for Daiso stores.  
Users speak or type Korean natural language queries; the system transcribes speech (STT), understands intent (NLU via Gemini),
searches a SQLite product database, and returns results or asks clarifying questions.

---

## 2) Performance Targets (STT 제외 기준)

- Current (local): **~19s** (STT excluded E2E)
- Target:
  - **P50: 10–12s**
  - **P90: 18–20s**
- Throughput requirement: **3 QPM** (per kiosk or service assumption depends on scenario)

> 측정 기준(반드시 명시):
> - “STT 제외”는 **텍스트 입력 → 최종 응답**까지의 처리시간을 의미
> - “사용자 체감(E2E)”는 **발화시간(말하는 시간)**을 포함할 수 있으므로 별도로 측정

---

## 3) Commands

### Backend (Python 3.10, FastAPI)
```bash
pip install -r requirements.txt

# Choose ONE app to run on port 8000 (avoid port conflict):
uvicorn backend.api:app --reload --port 8000       # STT pipeline API
# OR
uvicorn backend.main:app --reload --port 8000      # Main chat API (LangGraph)
```
> NOTE: If both apps must run simultaneously, use different ports (e.g., 8000/8001).

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
python run_all_pipeline.py                               # Full pipeline orchestrator (if present)
```

---

## 4) E2E Pipeline (STT 제외) — `service/pipeline/`

Run the full pipeline end-to-end (STT excluded):
```bash
python -m service.pipeline.run_e2e --text "볼펜 어디있어요"
```

### Outputs
- Output directory: `outputs/{run_id}/`
- `run_id` format: `YYYYMMDD_HHMMSS_{uuid4 first 8 chars}`
- Artifacts per step (example):
  - `transcript.json`, `nlu.json`, `keywords.json`, `expansion.json`, `search.json`, `final_response.json`

### Pipeline stages (conceptual)
- Step 0 (text_adapter): 텍스트 입력 → transcript artifact
- Step 1 (intent / NLU): 의도 분류 및 슬롯 추출 → nlu artifact
- Step 2 (keyword_extract): 키워드 추출 → keywords artifact
- Step 3 (keyword_expand): 키워드 확장 → expansion artifact
- Step 4 (search_rerank): 후보 검색 + rerank → search artifact
- Step 5 (final_output): 최종 응답 JSON 생성 → `final_response.json`

### Step 4 구현 상세 (현재 구조 기준)
> ⚠️ 아래는 “현재 repo 구현”을 기준으로 한 설명이며, 실제 파일/함수명은 코드가 소스임.

**Retrieve**
- SQLite `products.db`를 직접 조회 (약 601개 상품)
- 일반적으로 테이블은 `products`, 검색 대상 컬럼은 `name`, `category_major`, `category_middle` 등
- (예시) 토큰 AND + LIKE 기반으로 조회 후 결과가 없으면 OR로 완화하는 전략을 사용할 수 있음

**Rerank**
- `poc/` 내 실험 스크립트의 `advanced_rerank(query, candidates)`를 import 호출하여 재정렬하는 구조일 수 있음
- 외부 LLM 호출이 포함될 수 있으므로 `GEMINI_API_KEY`가 필요(미설정 시 실패/우회 정책은 코드 기준)

**IMPORTANT**
- `poc/`의 스크립트/로직을 호출해야 한다면, `service/pipeline/`에서만 조립
- `backend/`로 무단 이전/병합은 금지(필요 시 팀 합의/이슈로 진행)

---

## 5) Architecture

### Data Flow
```
Audio/Text → STT (Whisper/Google) → Quality Gate → Policy Gate → NLU (Gemini) → DB Search → Response
```

### Backend (`backend/`)
**API Layer**
- `api.py` — STT pipeline endpoints (`POST /stt/process`, `POST /stt/compare`, `GET /health`)
- `main.py` — Chat endpoint with LangGraph agent (`POST /api/chat`)
- `ws_stt.py` — WebSocket real-time streaming STT (`WS /ws/stt`)

**STT Module** (`backend/stt/`)
- `adapters.py` — WhisperAdapter (faster-whisper, local) and GoogleSTTAdapter (Cloud Speech v1)
- `quality_gate.py` — Validates transcription (min length, confidence threshold, nonsense pattern rejection)
- `policy_gate.py` — Routes by intent: fixed locations (화장실, 계산대), unsupported queries (배달, 환불), or product search
- `types.py` — Pydantic models
- Config: `backend/config.yaml`

**LangGraph Agent** (`backend/logic/agent_graph.py`) — 5-node cyclic state machine:
1. NLU (intent + slots)
2. Search (SQLite keyword search; fallback keyword inference if needed)
3. Ambiguity Check (clarification triggers, loop prevention)
4. Clarification question generation
5. Response formatting

**Database** (`backend/database/`)
- SQLite: `products.db` (approx. 601 items)
- `database.py` handles search/insert
- `category_matcher.py` keyword-based category matching
- `embeddings.py` CLIP-based multimodal embedding support

### Frontend (`frontend/`)
- `/` — Landing page
- `/kioskmode` — Interactive chat UI for product search

### POC Directory (`poc/`)
- Research artifacts; **read-only**

---

## 6) Testing Policy (현실적인 TDD 전환)

- 기존 구현은 이미 동작하므로, 먼저 **Characterization Tests(현상 유지/골든 케이스)**를 추가한다.
- 이후 “변경/신규 기능”부터는 가능하면 **test-first (Red → Green → Refactor)**를 적용한다.
- 외부 API(Gemini/Google STT)는 단위 테스트에서 **mock/stub** 처리한다.

목표: 성능 최적화/리팩토링 중에도 결과 품질과 분기 로직이 깨지지 않게 회귀 방지

---

## 7) Measurement & Logging (성능 개선의 표준)

- 모든 E2E 실행은 **step별 `latency_ms`**를 기록/출력해야 한다.
- 성능 개선 작업은 다음 순서를 따른다:
  1) 측정(현재 step별 latency)
  2) 가장 느린 step 1~2개를 타겟팅
  3) 변경
  4) 전/후 비교 리포트(수치 포함)

Recommended fields to log:
- `run_id`, `step`, `latency_ms`
- `provider` (e.g., gemini/stt provider)
- `fallback_used` (true/false)
- `selected_id`, `reason` (where applicable)

### 현재 병목 구간 (가설 / 측정으로 확인 필요)
- 현재 STT 제외 E2E가 약 **19초**로 관측됨
- Step 1/2/3/4에서 Gemini(LLM) API 호출이 각각 발생할 수 있어, 총 **최대 4회 호출**이 지연의 주요 요인일 가능성이 큼
- 개선 방향 후보(코드 의존성 확인 후 적용):
  - Step 2 + Step 3 병렬화 가능성 검토
  - 프롬프트/결과 캐싱(동일 질의 재사용)
  - 모델 경량화/timeout/retry 정책 정리
  - Step 4 rerank 호출 조건 축소(후보수/품질게이트 기반)

---

## 8) Environment & Secrets

### Required
- `.env` in project root (preferred) with:
```bash
GEMINI_API_KEY=...
```

### Optional / Additional .env loading (service pipeline)
- `service/pipeline/run_e2e.py` 실행 시(구현에 따라) 다음 순서로 `.env`를 자동 로드하도록 구성될 수 있음:
  1. `{PROJECT_ROOT}/.env`
  2. `{PROJECT_ROOT}/backend/.env`
- 실제 로드 여부/순서는 `service/pipeline/run_e2e.py` 코드가 소스임.

### Google Speech (STT)
This project uses Google Cloud Speech via service credentials (commonly a JSON key file).
- Configure the key file path via `backend/config.yaml` or environment variable (depending on implementation).
- Typical pattern (if supported by code/config):
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google_key.json
```

> NOTE:
> - Do not assume `GOOGLE_API_KEY` is used unless the code explicitly supports it.
> - Never commit secrets (`.env`, `google_key.json`).

---

## 9) Key Conventions
- All user-facing text and LLM responses are in Korean
- Intent types: `PRODUCT_LOCATION`, `OTHER_INQUIRY`, `UNSUPPORTED`
- Whisper defaults to "medium" model on CPU with int8 quantization; falls back to "small" on OOM
- No formal test suite exists; Characterization Tests 추가 예정 (6번 참고)
- Main branch: `dev`
---

## 10) Work Request Template (Claude Code 지시 템플릿)

작업을 요청할 때는 아래 형식을 우선 사용한다. (성공 기준이 없는 요청 금지)

```
목표: (한 줄)
성공기준: (예: run_e2e 실행 시 final_response.json 생성 + step별 latency_ms 출력)
범위: (수정 가능한 폴더/파일)
금지: (예: poc/ 수정 금지, Windows 절대경로 저장 금지, 측정 없이 최적화 금지)
명령: (실행할 커맨드들)
기대결과: (예: outputs/{run_id}/에 N개 파일 생성, total_ms <= 12000)
```

---

## 11) Merged Execution Rules (프로세스/컨테이너 난립 방지)

목표: 병합 후 통합 실행 단계에서 불필요한 프로세스/컨테이너 난립을 최소화한다.

- 원칙 A: 로컬/파일럿 단계에서는 가능한 한 **단일 런타임(또는 최소 2~3개)** 로 실행한다.
- 원칙 B: 기능(모듈) 경계는 유지하되, 병합 모드에서는 **in-process 호출(import)** 을 우선한다.
  - 필요 시 “실행 모드”에 따라 http 호출 ↔ in-process 호출을 선택하는 어댑터 계층을 둔다.
- 원칙 C: 중복 워커/스케줄러 금지
  - 동일 작업이 여러 프로세스에서 중복 실행되지 않도록 락(파일 락/redis 락 등) 또는 단일 실행 원칙을 둔다.
- 원칙 D: 포트 충돌 금지
  - FastAPI 앱을 동시에 실행해야 한다면 포트 분리(예: 8000/8001) 및 문서/스크립트에 고정한다.

---

## 12) Output Contract (final_response.json 최소 계약)

E2E 파이프라인 결과물(`final_response.json`)은 최소한 아래 필드를 포함하는 것을 권장한다.
(스키마 변경은 breaking change가 될 수 있으므로 변경 전 합의/공지)

```json
{
  "run_id": "YYYYMMDD_HHMMSS_xxxxxxxx",
  "query": "볼펜 어디있어요",
  "intent": "PRODUCT_LOCATION",
  "topk": [
    { "id": 123, "name": "...", "score": 0.93 }
  ],
  "selected_id": 123,
  "reason": "선정 근거 요약",
  "timing_ms": {
    "step0_transcript": 10,
    "step1_intent": 1200,
    "step2_keyword_extract": 900,
    "step3_keyword_expand": 800,
    "step4_search_rerank": 2500,
    "step5_final": 50,
    "total": 5460
  }
}
```

> NOTE: `timing_ms`는 성능 개선/회귀 방지를 위해 사실상 “필수”로 취급한다.

---

## 13) Golden Scenarios (현상 유지 테스트 최소 세트)

Characterization Tests(현상 유지/골든 케이스)는 아래 최소 5개를 우선 고정한다.

- 고정 위치(정책 게이트): `"화장실 어디야"`, `"계산대 어디야"`
- 상품(정상): `"건전지 어디있어요"`, `"욕실 매트 어디있어요"`
- 애매/없음(정상 처리): `"볼펜 어디있어요"` (rerank 결과 selected_id가 None이거나 후보가 없을 때도 파이프라인은 정상 완료되어야 함)
- 실패/예외: API KEY 미설정 시 Step 1/2/3/4가 어떻게 실패하는지(에러 메시지/코드) 고정

원칙:
- 외부 API(Gemini/Google STT)는 단위 테스트에서 mock/stub 처리한다.
- E2E 골든은 “로컬에서 재현 가능한 형태(리플레이 입력/캐시/샘플 output)”로 유지한다.

---

## 14) Performance Improvement Checklist (PR 필수 산출물)

성능 개선 작업은 PR에 아래를 반드시 포함한다.

- 변경 전/후: step별 `latency_ms` 표 (최소 3회 실행 평균)
- 병목 스텝 1~2개를 특정한 근거(로그/측정값)
- 품질 회귀 여부(골든 케이스 결과 유지)

---

## 15) Lightsail Deployment Notes (실수 방지)

- Linux 환경 기준 경로/권한을 가정한다.
- DB/응답에 Windows 절대경로 저장 금지.
- `.env`, credential json 파일은 커밋 금지.
- 포트/프로세스 구성은 문서화하고, 충돌이 나지 않도록 고정한다.
