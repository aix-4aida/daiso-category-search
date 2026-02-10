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
│   ├── services_kms/                # ⭐ KMS 파이프라인
│       ├── run_all_pipeline.py      # 통합 파이프라인 (음성→검색결과)
│       ├── export_db_to_tsv.py      # DB → TSV 변환 (벤치마크용) ✅
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

---

## 🛠 설치 및 환경 설정 (필수)

### 1. Python 패키지 설치
이 프로젝트는 Python 3.10+ 환경을 권장합니다.

```bash
# 1. 기본 의존성 설치
pip install -r requirements.txt

# 2. IVHL (검색 라이브러리) 설치 ⭐ 중요
# (루트 디렉토리에서 실행)
pip install -e poc/lyg
```

### 2. 외부 프로그램 설치
- **FFmpeg**: 오디오 변환(`stt_to_json.py`)을 위해 필수입니다.
  - [다운로드 링크](https://ffmpeg.org/download.html)
  - 설치 후 `bin` 폴더 경로를 시스템 환경변수 `Path`에 추가해야 합니다.
  - **확인**: 터미널에서 `ffmpeg -version` 입력 시 버전 정보가 출력되어야 합니다.

### 3. Docker 서비스 실행 (DB)
Qdrant(벡터DB)와 Elasticsearch(검색엔진)를 실행합니다.

```bash
docker-compose up -d
```

### 4. 환경 변수 확인 (.env)
루트 디렉토리의 `.env` 파일에 아래 내용이 있는지 확인하세요.

```env
GEMINI_API_KEY=...
QDRANT_URL=http://localhost:6333
ELASTIC_URL=http://localhost:9200
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

# Search Engine (필수) ✅
QDRANT_URL=http://localhost:6333
ELASTIC_URL=http://localhost:9200

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
| 카탈로그 TSV | `backend/services_kms/data/products_exported.tsv` | ✅ DB에서 자동 추출됨 |
| 벤치마크 설정 | `poc/lyg/templates/pipeline.yaml` | ✅ 검색 파이프라인 설정 |
| 공급자 설정 | `poc/lyg/templates/vendors.yaml` | ✅ DB 연결/인증 설정 |

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

### 6. PYTHONPATH 설정 (중요) ✅
`run_benchmark.py` 실행 시 `ivhl` 패키지(소스 코드)를 찾을 수 있도록 `PYTHONPATH` 설정이 필요합니다.
`backend/services_kms/run_all_pipeline.py`에서는 자동으로 설정되지만, 수동 실행 시에는 아래와 같이 실행해야 합니다.

```powershell
# Windows PowerShell
$env:PYTHONPATH="poc/lyg/src"; python backend/services_kms/run_benchmark.py ...
```

---

## 🔄 파이프라인 흐름

```
[음성 입력] 
    ↓
0. DB 동기화 (export_db_to_tsv.py) : products.db → tsv ✅
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
    "utterance": "혹시 얼굴 팩 있나요?",
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

# ✅ 출력 형식 (Updated)
# - retrieved_results: Top 5 (ID + 상품명)
# - selected_id: ID + 상품명
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
#### 사용법 (CLI) ✅ PYTHONPATH 설정 필수
```bash
# Windows: $env:PYTHONPATH="poc/lyg/src" 선행 필요
python backend/services_kms/run_benchmark.py \
    --vendors poc/lyg/templates/vendors.yaml \
    --pipelines poc/lyg/templates/pipeline.yaml \
    --vendor-set ext_qdrant_elastic \
    --pipeline hybrid_fuse \
    --catalog backend/services_kms/data/products_exported.tsv \
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


---

## 🚀 배포 (Deployment) - 2026.02.10 업데이트

### 1. 배포 환경 (AWS Lightsail)
*   **OS**: Ubuntu 22.04 / 24.04
*   **권장 사양**: **최소 4GB RAM ($20/월) 이상**
    *   🚨 **중요**: 512MB RAM 인스턴스 사용 시 Elasticsearch와 Python 컨테이너가 **OOM (Out Of Memory) Kill**로 인해 강제 종료됨 (`Exited (137)` 에러). 정상 구동 불가능.
*   **방화벽(Networking) 설정**:
    *   `3000` (Frontend 웹 접근)
    *   `8000` (Backend API)
    *   `6333` (Qdrant 벡터DB)

### 4. 2GB 램에서 빌드 멈춤 현상 (필수)
Lightsail 2GB 인스턴스는 메모리가 부족하여 빌드 중 멈출 수 있습니다. **Swap 메모리 설정**이 필수입니다.

```bash
# 1. 스왑 파일 생성 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 영구 설정 (재부팅해도 유지)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 5. `ContainerConfig` 에러 (컨테이너 깨짐)
빌드 실패 후 `ContainerConfig` 에러가 나면 컨테이너를 지우고 다시 실행하세요.
```bash
docker rm -f daiso-category-search_backend_1
docker-compose up -d
```

### 2. 주요 설정 파일
*   **Frontend Dockerfile** (`frontend/Dockerfile`):
    *   Next.js `output: 'standalone'` 모드 적용 (이미지 경량화)
*   **Docker Compose** (`docker-compose.yml`):
    *   Frontend, Backend, Qdrant, Elasticsearch 4개 컨테이너 오케스트레이션
*   **GitHub Actions** (`.github/workflows/deploy.yml`):
    *   `feature/kms` 브랜치 푸시 시 자동 빌드 -> Docker Hub 푸시 -> Lightsail 배포

### 3. 트러블슈팅 가이드 (Troubleshooting)

#### **Q1. Git Push 실패 (File too large)**
*   **현상**: `ffmpeg.exe`나 `.wav` 파일 용량이 100MB를 초과하여 푸시 거부.
*   **해결**: `.gitignore`에 추가하고 `git rm --cached`로 추적 해제 후 커밋.

#### **Q2. Next.js 빌드 실패 (Build Error)**
*   **현상**: `useSearchParams()` 사용 페이지에서 빌드 에러 발생.
*   **해결**: 해당 훅을 사용하는 컴포넌트를 반드시 `<Suspense>`로 감싸야 함 (`MapNavigation`, `SearchResults`, `NoResult` 페이지 수정 완료).

#### **Q3. 서버 배포 실패 (Invalid tag format)**
*   **현상**: Docker ID에 이메일(`@`)이 포함되어 이미지 태그 생성 실패.
*   **해결**: 이메일이 아닌 **Docker ID (`minssss`)** 사용.

#### **Q4. 사이트 접속 불가 (Connection Refused)**
*   **현상**: 배포 성공 메시지가 떴으나 사이트 접속 안 됨. `docker ps -a` 확인 시 `Exited (137)` 상태.
*   **해결**: **메모리 부족**이 원인. 인스턴스 스냅샷 생성 후 **4GB 램 이상 플랜으로 업그레이드** 필요.

### 4. 수동 배포 및 복구 명령어 (SSH)
서버에서 자동 배포가 꼬였을 때 사용하는 긴급 복구 명령어입니다.

```bash
# 1. 프로젝트 코드 다운로드 (Clone)
git clone -b feature/kms https://github.com/aix-4aida/daiso-category-search.git

# 2. 폴더로 이동
cd daiso-category-search

# 3. Docker 설치 및 권한 부여 (비밀번호 물어보면 그냥 엔터 치거나 사용자 비번 입력)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER

# 4. (중요) 터미널 껏다 켜기
exit

# 5. 최신 코드 강제 동기화 (충돌 해결)
git fetch origin
git reset --hard origin/feature/kms

# 6. Docker ID 환경변수 설정 (필수!)
export DOCKER_USERNAME=minssss

# 7. 이미지 갱신 및 재시작
docker-compose pull
docker-compose up -d

# 8. 생존 여부 확인
docker ps -a 
# (STATUS가 'Up' 이어야 함. 'Exited'면 사양 업그레이드 필요)
```
