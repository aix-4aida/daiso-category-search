# Daiso Category Search (AI Powered)

이 프로젝트는 다이소 상품 검색을 위한 AI 기반 애플리케이션입니다.
Gemini 1.5 Flash (또는 Gemini 2.0 Flash) 모델을 사용하여 사용자의 자연어 쿼리를 이해하고, 의도를 분석하거나 필요한 경우 꼬리 질문을 생성합니다.

## 프로젝트 구조

```
daiso-category-search/
├── backend/                # FastAPI 백엔드
│   ├── logic/              # NLU 및 핵심 로직
│   │   ├── nlu.py          # Gemini API 연동
│   │   ├── prompts.py      # 프롬프트 템플릿
│   │   └── schemas.py      # 데이터 스키마
│   ├── api.py              # API 엔드포인트
│   └── experiments/        # 검증 스크립트
├── frontend/               # Next.js 프론트엔드
│   └── src/app/page.tsx    # 채팅 UI
└── requirements.txt        # Python 의존성
```

## 시작하기

### 1. 환경 설정

`.env` 파일을 루트 디렉토리에 생성하고 Gemini API Key를 입력하세요.
```
GEMINI_API_KEY=your_api_key_here
```

### 2. 백엔드 실행

```bash
# 가상환경 활성화 후
pip install -r requirements.txt
uvicorn backend.api:app --reload --port 8000
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### 4. 사용 방법

브라우저에서 `http://localhost:3000`으로 접속하여 검색어를 입력합니다.
- **검색**: "파란색 볼펜 찾아줘"
- **대화**: AI가 의도가 불분명할 경우 꼬리 질문을 합니다.
