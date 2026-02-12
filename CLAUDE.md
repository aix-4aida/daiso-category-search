# CLAUDE.md - 어디다있소 (Daiso Kiosk)

## 프로젝트 개요
- **이름:** 어디다있소 (Daiso Kiosk)
- **목적:** 다이소 매장 내 상품 위치 안내 및 재고 확인 키오스크 서비스
- **핵심 철학:** **"극한의 경량화"** - AWS Lightsail (1 vCPU, 512MB RAM) 환경에서 Docker 오버헤드 없이 Native 구동
- **현재 상태:** `reset01` 브랜치에서 DB 레이어만 남기고 리셋됨

## 기술 스택
### Frontend (Native Process)
- React 19 + TypeScript + Vite 7
- TailwindCSS 4 (Vite 플러그인)
- Zustand 5 (상태 관리)
- Vitest 4 + Testing Library (테스트)

### Backend (Native Process)
- Python 3.12 (requires >=3.10, <3.13)
- FastAPI + Uvicorn (ASGI)
- Poetry (패키지 매니저)
- Pytest + pytest-asyncio (테스트, asyncio_mode = "auto")

### Database & Search (Native - No Docker)
- **Elasticsearch 7.x** - BM25 검색 (JVM: `-Xms128m -Xmx128m`)
- **Qdrant** - 벡터 검색 (바이너리 실행)
- **SQLite** - 상품/카테고리/임베딩 데이터 (`backend/database/products.db`)

### AI
- Google Gemini 2.0 Flash (API)

## 프로젝트 구조
```
daiso-category-search/
├── backend/
│   ├── database/           # DB 레이어 (현재 유일한 백엔드 코드)
│   │   ├── database.py     # SQLite CRUD (products, utterances, embeddings)
│   │   ├── category_matcher.py  # 상품-카테고리 매칭
│   │   ├── crawler.py      # 상품 크롤러
│   │   ├── embeddings.py   # 임베딩 생성
│   │   ├── generate_test_data.py
│   │   ├── products.db     # SQLite DB 파일
│   │   └── images/         # 상품 이미지
│   ├── pyproject.toml
│   └── poetry.lock
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── setup-local-db.md
│   └── install-db.ps1
├── tests/                  # TDD 테스트 (아직 비어있음)
├── ui_refs/                # UI 참조 디자인
├── .env.example
├── .gitignore
└── daiso_search_guide.md   # 프로젝트 가이드 원본
```

## 개발 명령어
### Backend
```bash
cd backend
poetry install              # 의존성 설치
poetry install --with dev   # dev 의존성 포함
poetry run pytest           # 테스트 실행
poetry run pytest --cov     # 커버리지 포함
poetry run uvicorn main:app --reload  # 개발 서버
```

### Frontend
```bash
cd frontend
npm install                 # 의존성 설치
npm run dev                 # Vite 개발 서버
npm run build               # 프로덕션 빌드 (tsc -b && vite build)
npm run test                # Vitest 실행 (vitest run)
npm run test:watch          # Vitest 워치 모드
npm run lint                # ESLint
```

## 코드 컨벤션
### Python (Backend)
- **함수/변수:** `snake_case`
- **타입 힌트:** 함수 시그니처에 반드시 사용 (`def func(name: str) -> bool:`)
- **import:** 표준 라이브러리 → 서드파티 → 로컬 순서
- **독스트링:** 모듈/함수에 `"""설명"""` 형태 (영어 사용)
- **로그/피드백:** 이모지 접두사 사용 (`✅`, `❌`, `[OK]`)
- **에러 메시지:** 영어
- **SQL:** 대문자 키워드, 멀티라인 포맷

### TypeScript (Frontend)
- **React:** 함수형 컴포넌트 + TypeScript
- **모듈:** ES Modules (`"type": "module"`)

### 공통
- **커밋/주석 언어:** 한국어 가능
- **파일 인코딩:** UTF-8

## TDD 규칙 (Strict Mode)
**TDD 위반 시 PR 승인 불가**

1. 🔴 **Red:** 실패하는 테스트 먼저 작성 (구현 전)
2. 🟢 **Green:** 테스트를 통과하는 최소 구현
3. 🔵 **Refactor:** 코드 개선 (테스트 유지)

- Frontend 테스트: Vitest (`npm run test`)
- Backend 테스트: Pytest (`poetry run pytest`)
- `asyncio_mode = "auto"` 설정됨 (async 테스트 자동 감지)

## Git 규칙
- **기본 브랜치:** `dev` (PR 타겟)
- **브랜치 네이밍:** `feature/기능명`, `fix/버그명`, `chore/작업명`
- **커밋 메시지:** `Type: 설명` 형태
  - `Feat:` 새 기능
  - `Fix:` 버그 수정
  - `Chore:` 설정/환경
  - `Docs:` 문서
  - `Refactor:` 리팩토링
  - `Test:` 테스트

## 인프라 정책
- **No Docker Policy:** 모든 서비스는 OS 위 네이티브 프로세스로 구동
- **Process Manager:** PM2 (Backend, Qdrant), systemd (Elasticsearch)
- **메모리 제한:** 512MB 초과 금지, ES JVM 힙 128MB
- **Swap:** 2GB 이상 Swap 파일로 OOM 방지

## 환경변수 (.env)
`GOOGLE_API_KEY`, `ELASTIC_URL`, `ELASTIC_USERNAME`, `ELASTIC_PASSWORD`, `QDRANT_URL` 참조. `.env.example` 파일 확인.
