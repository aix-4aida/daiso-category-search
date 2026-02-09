# 🏪 Daiso Category Search - KMS Branch 참고사항

> **Branch**: `feature/kms`  
> **Last Updated**: 2026-02-09

---

## 📁 프로젝트 구조 및 의존성

### 🔧 Backend (`backend/main.py`) 실행 시 연관 파일

```
backend/
├── main.py                          # ⭐ FastAPI 메인 서버 (Entry Point)
│   ├── database/
│   │   ├── connection.py            # DB 연결 및 쿼리 함수
│   │   └── products.db              # SQLite 상품 데이터베이스 (3.4MB)
│   ├── stt/
│   │   ├── __init__.py
│   │   ├── adapters.py              # STT 어댑터 (Google, Azure 등)
│   │   ├── audio_converter.py       # 오디오 변환 유틸리티
│   │   ├── quality_gate.py          # 품질 검증
│   │   └── types.py                 # 타입 정의
│   └── services_kms/                # ⭐ KMS 파이프라인
│       ├── run_all_pipeline.py      # 통합 파이프라인 (음성→검색결과)
│       ├── stt_to_json.py           # STT 변환
│       ├── poc_flash_test.py        # Intent 분류
│       ├── simple_keyword_extractor_gemini.py    # 키워드 추출
│       ├── expand_keywords_comparison_gemini.py  # 키워드 확장
│       ├── run_benchmark.py         # 벤치마크 실행
│       ├── poc_v5_experiment_phase_1.py          # Reranking
│       └── data/                    # 파이프라인 출력 파일들
│           ├── stt_output.json
│           ├── intent_output.json
│           ├── extracted_keywords.json
│           ├── expansion_result.tsv
│           ├── benchmark_out/
│           └── final_reranked_results.json
```

---

### 🎨 Frontend (`frontend/`) 실행 시 연관 파일

```
frontend/
├── index.html                       # HTML Entry
├── package.json                     # npm 의존성
├── vite.config.js                   # Vite 설정
├── tailwind.config.js               # Tailwind CSS 설정
└── src/
    ├── main.jsx                     # React Entry Point
    ├── App.jsx                      # 라우터 설정
    ├── index.css                    # 전역 스타일
    ├── pages/
    │   ├── Home.jsx                 # 메인 페이지
    │   ├── SearchResults.jsx        # 검색 결과 + 지도 표시 ⭐
    │   ├── VoiceSearch.jsx          # 음성 검색 페이지
    │   ├── MapNavigation.jsx        # 지도 네비게이션
    │   └── NoResult.jsx             # 결과 없음 페이지
    ├── components/
    │   ├── Layout.jsx               # 공통 레이아웃
    │   ├── Header.jsx               # 헤더
    │   ├── Button.jsx               # 버튼 컴포넌트
    │   ├── Input.jsx                # 입력 컴포넌트
    │   └── ...
    ├── config/
    │   └── mapConfig.js             # 매대 좌표 설정 ⭐
    └── lib/
        └── api.js                   # Backend API 호출 함수
```

---

## 🚀 실행 방법

### Backend 실행
```bash
cd daiso-category-search
python -m backend.main
# → http://localhost:8000
```

### Frontend 실행
```bash
cd daiso-category-search/frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## ⚠️ 팀원 필수 참고사항

### 1. 환경 변수 설정 (.env)
```env
# Google Gemini API (필수)
GEMINI_API_KEY=your_gemini_api_key_here

# STT API (선택)
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### 2. KMS 파이프라인 경로 변경
> **중요**: `backend/main.py`는 이제 루트의 `run_all_pipeline.py`가 아닌  
> `backend/services_kms/run_all_pipeline.py`를 사용합니다.

```python
# backend/main.py (Line 83)
from backend.services_kms.run_all_pipeline import run_daiso_pipeline
```

### 3. 데이터 파일 위치
| 파일 | 경로 | 설명 |
|------|------|------|
| 상품 DB | `backend/database/products.db` | SQLite, ~3.4MB |
| 카탈로그 TSV | `poc/lyg/data/catalog.sqlite_export.tsv` | 벤치마크용 |
| 벤치마크 설정 | `poc/data/benchmark_out/20260205_071633/configs/` | YAML 설정 |

### 4. 지도 매대 좌표 설정
`frontend/src/config/mapConfig.js`에서 매대별 좌표를 관리합니다.
```javascript
export const SHELF_COORDINATES = {
  "문구/팬시": { x: 32, y: 50, floor: "B1" },
  "주방": { x: 55, y: 70, floor: "B1" },
  // ...
};
```

### 5. API 엔드포인트
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/search/voice` | 음성 파일 → 검색 결과 |
| GET | `/api/products/search?q=` | 텍스트 검색 |
| GET | `/api/products/category/{name}` | 카테고리별 조회 |
| GET | `/api/products/{id}` | 상품 상세 |

---

## 🔄 파이프라인 흐름

```
[음성 입력] 
    ↓
1. STT (stt_to_json.py)
    ↓
2. Intent 분류 (poc_flash_test.py)
    ↓
3. 키워드 추출 (simple_keyword_extractor_gemini.py)
    ↓
4. 키워드 확장 (expand_keywords_comparison_gemini.py)
    ↓
5. 하이브리드 검색 (run_benchmark.py)
    ↓
6. Reranking (poc_v5_experiment_phase_1.py)
    ↓
[검색 결과 반환] → products.db 조회 → Frontend 표시
```

---

## 📝 알려진 이슈 / TODO

- [ ] STT 필드명: `utterance` (vs `text`) 통일 필요
- [ ] 지도 좌표 미세 조정 필요 (일부 매대 경로 침범)
- [ ] `google.generativeai` → `google.genai` 마이그레이션 예정

---

## 📦 파이프라인 모듈별 설치 및 사용법

### 1. `stt_to_json.py` - 음성 → 텍스트 변환

#### 필수 프로그램 설치
```bash
# 1. FFmpeg 설치 (오디오 변환용)
# Windows: https://ffmpeg.org/download.html 에서 다운로드 후 PATH에 추가
# 또는 backend/services_kms/ 폴더에 ffmpeg.exe 직접 배치

# 2. Python 패키지 설치
pip install pydub

# 3. Google Cloud STT 인증 (선택)
# 환경변수 설정: GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

#### 사용법
```python
from backend.services_kms.stt_to_json import convert_stt_to_json

# 오디오 파일 → JSON 변환
convert_stt_to_json(
    input_dir="data/test_audio/01_general/김민서_일반01.m4a",
    output_json="backend/services_kms/data/stt_output.json"
)
```

#### 출력 형식
```json
[
  {
    "id": 1,
    "filename": "김민서_일반01.m4a",
    "utterance": "혹시 얼굴 팩 있나요?",  // ⚠️ 필드명 주의: "utterance" 사용
    "stt_meta": { "confidence": 0.95, "latency_ms": 1200 }
  }
]
```

---

### 2. `poc_v5_experiment_phase_1.py` - Gemini Reranking

#### 필수 프로그램 설치
```bash
# Python 패키지 설치
pip install google-generativeai python-dotenv

# .env 파일에 API 키 설정
echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

#### 환경 변수
```env
# 아래 둘 중 하나 설정 (GEMINI_API_KEY 우선)
GOOGLE_API_KEY=your_key
GEMINI_API_KEY=your_key
```

#### 사용법
```python
from backend.services_kms.poc_v5_experiment_phase_1 import process_benchmark_output

# 벤치마크 결과 → Reranking
process_benchmark_output(
    benchmark_dir="backend/services_kms/data/benchmark_out/20260209_053815",
    catalog_tsv="poc/lyg/data/catalog.sqlite_export.tsv",
    output_json="backend/services_kms/data/final_reranked_results.json"
)
```

#### 주의사항
> ⚠️ **Deprecated Warning**: `google.generativeai` 패키지는 더 이상 지원되지 않습니다.  
> 향후 `google.genai`로 마이그레이션 예정입니다.

---

### 3. `run_benchmark.py` - 하이브리드 검색 벤치마크

#### 필수 프로그램 설치
```bash
# 1. IVHL 패키지 설치 (프로젝트 내부 패키지)
pip install -e . # 프로젝트 루트에서 editable 설치

# 2. Python 패키지 설치
pip install pyyaml

# 3. 외부 서비스 (Vector DB)
# Qdrant: https://qdrant.tech/documentation/quick-start/
# Elasticsearch: https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html
```

#### 벤치마크 설정 파일
| 파일 | 경로 | 설명 |
|------|------|------|
| vendors.yaml | `poc/data/benchmark_out/20260205_071633/configs/vendors.yaml` | Qdrant/Elastic 연결 설정 |
| pipelines.yaml | `poc/data/benchmark_out/20260205_071633/configs/pipelines.yaml` | 파이프라인 단계 설정 |

#### 사용법 (CLI)
```bash
python backend/services_kms/run_benchmark.py \
    --vendors poc/data/benchmark_out/20260205_071633/configs/vendors.yaml \
    --pipelines poc/data/benchmark_out/20260205_071633/configs/pipelines.yaml \
    --vendor-set ext_qdrant_elastic \
    --pipeline hybrid_fuse \
    --catalog poc/lyg/data/catalog.sqlite_export.tsv \
    --testcases backend/services_kms/data/expansion_result.tsv \
    --out backend/services_kms/data/benchmark_out
```

#### 사용법 (Python)
```python
from backend.services_kms.run_benchmark import load_yaml, import_run_benchmark

# YAML 설정 로드
vendors_cfg = load_yaml("poc/data/benchmark_out/20260205_071633/configs/vendors.yaml")
pipelines_cfg = load_yaml("poc/data/benchmark_out/20260205_071633/configs/pipelines.yaml")

# 벤치마크 실행
run_benchmark = import_run_benchmark()
result = run_benchmark(vendor_set=..., pipeline=..., ...)
```

---

## 🔧 전체 의존성 요약 (requirements.txt)

```txt
# FastAPI & Backend
fastapi
uvicorn
pydantic
python-dotenv

# STT & Audio
pydub
# + FFmpeg (시스템에 설치 필요)

# AI / LLM
google-generativeai

# Search & Benchmark
pyyaml
# + ivhl (프로젝트 내부 패키지, editable 설치)
# + Qdrant, Elasticsearch (외부 서비스)

# Database
sqlite3  # 파이썬 기본 내장
```

---

## 👥 담당자

| 영역 | 담당 |
|------|------|
| KMS 파이프라인 | @kms |
| Frontend | - |
| Backend API | - |
