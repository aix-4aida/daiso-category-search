# 프로젝트 개요
- **이름:** 어디다있소 (Daiso Kiosk)
- **목적:** 다이소 매장 내 상품 위치 안내 및 재고 확인 키오스크 서비스
- **핵심 철학:** **"극한의 경량화"** - AWS Lightsail (1 vCPU, 512MB RAM) 환경에서 Docker 오버헤드 없이 Native 구동

# 기술 스택 (Tech Stack) - All Native
## 1. Frontend (Native Process)
- **Core:** React 18+, TypeScript, Vite
- **Styling:** TailwindCSS
- **State:** Zustand
- **Run:** `npm run build` 후 FastAPI 정적 파일 서빙 또는 PM2로 Node 실행

## 2. Backend (Native Process)
- **Core:** Python 3.10+, FastAPI
- **Server:** Uvicorn (ASGI)
- **Package Manager:** Poetry (권장) 또는 pip
- **Run:** PM2를 사용하여 프로세스 관리 (`pm2 start "uvicorn main:app..."`)

## 3. Database & Search (Native Process - No Docker)
- **Search Engine:** Elasticsearch 7.x (APT 설치)
    - **CRITICAL Config:** `/etc/elasticsearch/jvm.options`에서 `-Xms128m -Xmx128m` 설정 필수 (메모리 초절약 모드)
- **Vector DB:** Qdrant (Binary 실행)
    - **Method:** 공식 Github에서 바이너리 다운로드 후 PM2로 실행

## 4. AI & Logic
- **AI:** Google Gemini 2.0 Flash (API 활용)
- **Testing:** Vitest (Front), Pytest (Back)

# 주요 파이프라인 (Logic Flow)
1. **Input:** 사용자 음성/텍스트
2. **Intent & Keyword (Gemini):** 의도 파악 및 검색 키워드 추출
3. **Hybrid Search:**
   - **BM25:** Elasticsearch (Native)
   - **Vector:** Qdrant (Native)
4. **Reranking (Gemini):** 검색 결과 30개 재정렬 (LLM 활용)
5. **Output:** Top 3 결과 및 매장 지도 표시

# 개발 방법론 (TDD - Strict Mode)
**CRITICAL: TDD 위반 시 PR 승인 불가**
1. 🔴 **Red:** 실패하는 테스트 작성 (구현 전)
2. 🟢 **Green:** 테스트를 통과하는 최소 구현
3. 🔵 **Refactor:** 코드 개선 (테스트 유지)
* Frontend: `tests/frontend/` (Vitest)
* Backend: `tests/backend/` (Pytest)

# 인프라 및 배포 전략 (Infrastructure)
**"No Docker Policy"**
- 모든 서비스(Front, Back, DB)는 OS 위에 직접 설치된 프로세스로 구동한다.
- **Process Manager:** `PM2`를 사용하여 모든 프로세스(Backend, Qdrant)를 관리하고 로그를 모니터링한다. (Elasticsearch는 `systemd` 사용)
- **Memory Management:** 512MB 한계를 넘지 않도록 모든 JVM 및 프로세스 힙 메모리를 엄격하게 제한한다.
- **Swap Memory:** 2GB 이상의 Swap 파일을 생성하여 OOM(Out of Memory) 방지 안전장치를 둔다.