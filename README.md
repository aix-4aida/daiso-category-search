# Daiso Category Search (Search-Roca)

다이소 물품 찾기 및 매장 내비게이션 서비스의 통합 저장소입니다.  
FastAPI 백엔드와 키오스크/모바일 프론트엔드로 구성되어 있습니다.

## 📁 디렉토리 구조

```
daiso-category-search/
├── app/                  # FastAPI 백엔드 메인
├── backend/              # 검색/STT 로직 및 인프라
│   ├── services/         # Fallback 처리가 강화된 검색 서비스
│   └── stt/              # 최적화된 STT 파이프라인 (FFmpeg 기반)
├── frontend/             # 이미지 기반 지도가 적용된 프론트엔드
├── docs/                 # 프로젝트 가이드 및 디자인 문서 (신규)
└── test/                 # 스트레스 테스트 스크립트
```

## ✨ 주요 기능 및 특징
- **강력한 검색 안정성**: 백엔드 엔진 장애 시 즉각적으로 로컬 DB 검색으로 전환 (Zero Downtime).
- **실감 지형 가이드**: 매장 실사 평면도 위에 상품 위치를 정밀하게 표시하는 이미지 기반 맵 시스템.
- **실전형 음성 검색**: 브라우저 마이크를 통한 실시간 음성 인식 및 검색 연동.
- **클라우드 최적화**: AWS Lightsail(Micro) 사양에 맞춘 FFmpeg 탑재 및 경량 AI 모델링.

## 🚀 실행 방법

### 1. 가상환경 설정 (권장)
프로젝트 실행 전 격리된 가상환경을 사용하는 것을 권장합니다.

**Case A: venv (Python 내장)**
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows PowerShell)
.\venv\Scripts\activate

# 활성화 (Mac/Linux)
source venv/bin/activate
```

**Case B: Conda**
```bash
# 가상환경 생성 (Python 3.12)
conda create -n daiso-search python=3.12

# 활성화
conda activate daiso-search
```

### 2. 패키지 설치 및 환경 설정
**Python (Backend)**
필요한 패키지를 설치합니다. (`requirements.txt`에 FastAPI 등 모든 의존성이 포함되어 있습니다)
```bash
pip install -r requirements.txt
```
API 키 설정을 위해 `.env` 파일을 생성하세요.
```bash
copy .env.example .env
# .env 파일 내 GOOGLE_API_KEY 등을 입력
```

**Node.js (Frontend - Optional)**
프론트엔드(`frontend/kiosk` 등)를 단독으로 테스트하고 싶을 때 사용합니다.
```bash
npm install
npm run lite
# -> 브라우저가 자동으로 실행되며 Kiosk 화면이 열립니다. (bs-config.json)
```

**External Search Server (Hybrid Search)** (Optional but recommended)
Docker 기반의 Qdrant(Vector DB)와 Elasticsearch(BM25)를 사용하려면:
1. Docker Desktop 설치 및 실행
2. 컨테이너 실행:
   ```bash
   docker-compose up -d
   ```
3. 데이터 인덱싱 (최초 1회):
   ```bash
   python index_to_external.py
   ```


### 3. 모바일 연결 가이드 (QR 코드)
1. **PC 터미널**: `ipconfig` (Windows) 또는 `ifconfig` (Mac/Linux)를 입력하여 **내 PC의 IP 주소**를 확인합니다. (예: `192.168.0.x`)
2. **Kiosk 화면 설정**: 상단 노란색 **[설정]** 박스의 `1. Ngrok URL` 칸에 `http://<IP주소>:3000`을 입력하고 **[설정 저장]**을 누릅니다.
   - 예: `http://192.168.0.142:3000`
3. **QR 스캔**: 상품을 검색하고 생성된 QR 코드를 핸드폰으로 스캔합니다.
4. **모바일 접속**: 핸드폰 브라우저에서 지도 및 AR 화면이 정상적으로 열리는지 확인합니다.

### 3. 서버 실행
프로젝트 루트 경로에서 다음 명령어를 실행합니다.
```bash
python app/main.py
```
또는
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 접속
- **키오스크**: [http://localhost:8000/frontend/kiosk/index.html](http://localhost:8000/frontend/kiosk/index.html)
- **모바일**: QR코드 스캔 시 `/frontend/mobile/index.html`로 자동 연결됩니다.

## 🛠️ 개발 가이드
- **백엔드**: `app/main.py`에서 API 엔드포인트를 관리합니다. `backend/services/pipeline_service.py`가 핵심 검색 로직을 수행합니다.
- **프론트엔드**: `frontend/` 폴더 내의 HTML/JS를 수정합니다. `assets/map_data.js`에서 지도/상품 데이터를 관리합니다.
