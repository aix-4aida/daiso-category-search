# AWS Lightsail 배포 가이드 (FE + BE)

## 아키텍처 개요

```
사용자 브라우저  →  Lightsail FE (Nginx, Port 80)  →  Lightsail BE (FastAPI, Port 8000)
                                                          ↓
                                                    Google Gemini API
```

---

## 사전 준비

1. **AWS CLI 설치**: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html
2. **AWS Lightsail 플러그인 설치**:
   ```bash
   aws lightsail install-plugin
   ```
3. **Docker 설치**: https://docs.docker.com/get-docker/
4. **.env 파일 준비**: `GOOGLE_API_KEY` 등 환경변수 설정

---

## BE (Backend) 배포

### Step 1: Docker 이미지 빌드
```bash
cd daiso-category-search

# 백엔드 이미지 빌드
docker build -t daiso-backend:latest .

# 로컬 테스트
docker run -p 8000:8000 --env-file .env daiso-backend:latest
# → http://localhost:8000/health 확인
```

### Step 2: Lightsail 컨테이너 서비스 생성
```bash
# 서비스 생성 (Micro: 1 vCPU, 512MB / $7/월)
aws lightsail create-container-service \
  --service-name daiso-backend \
  --power micro \
  --scale 1
```

### Step 3: 이미지 푸시
```bash
aws lightsail push-container-image \
  --service-name daiso-backend \
  --label backend \
  --image daiso-backend:latest
```

### Step 4: 배포 설정
`deployment.json` 파일 생성:
```json
{
  "containers": {
    "backend": {
      "image": ":daiso-backend.backend.latest",
      "environment": {
        "GOOGLE_API_KEY": "<your-key>"
      },
      "ports": {
        "8000": "HTTP"
      }
    }
  },
  "publicEndpoint": {
    "containerName": "backend",
    "containerPort": 8000,
    "healthCheck": {
      "path": "/health",
      "intervalSeconds": 30,
      "timeoutSeconds": 5
    }
  }
}
```

```bash
aws lightsail create-container-service-deployment \
  --service-name daiso-backend \
  --cli-input-json file://deployment.json
```

### Step 5: URL 확인
```bash
aws lightsail get-container-services --service-name daiso-backend
# → url 필드에서 Public URL 확인
# 예: https://daiso-backend.xxxxx.lightsailcontainer.com
```

---

## FE (Frontend) 배포

### Step 1: Docker 이미지 빌드
```bash
# frontend-v3 내의 JS에서 API URL 설정
# js/app.js 의 API_BASE 를 BE Public URL로 변경

# 프론트엔드 이미지 빌드
docker build -f Dockerfile.frontend -t daiso-frontend:latest .

# 로컬 테스트
docker run -p 3000:80 daiso-frontend:latest
# → http://localhost:3000 확인
```

### Step 2: Lightsail 서비스 생성 & 배포
```bash
# 서비스 생성 (Nano: $3.5/월 — 정적 파일이므로 최소 사양)
aws lightsail create-container-service \
  --service-name daiso-frontend \
  --power nano \
  --scale 1

# 이미지 푸시
aws lightsail push-container-image \
  --service-name daiso-frontend \
  --label frontend \
  --image daiso-frontend:latest
```

FE 배포 설정 (`deployment-fe.json`):
```json
{
  "containers": {
    "frontend": {
      "image": ":daiso-frontend.frontend.latest",
      "ports": {
        "80": "HTTP"
      }
    }
  },
  "publicEndpoint": {
    "containerName": "frontend",
    "containerPort": 80,
    "healthCheck": {
      "path": "/",
      "intervalSeconds": 30
    }
  }
}
```

```bash
aws lightsail create-container-service-deployment \
  --service-name daiso-frontend \
  --cli-input-json file://deployment-fe.json
```

---

## CORS 설정

BE (`backend/main.py`)에서 FE URL을 명시적으로 추가:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://daiso-frontend.xxxxx.lightsailcontainer.com",  # FE URL
        "*"
    ],
    ...
)
```

---

## E2E 테스트 체크리스트

### 1. BE 단독 확인
- [ ] `GET /health` → `{"status": "healthy"}` 반환
- [ ] `GET /` → 서비스 정보 반환
- [ ] `POST /search/text` → 검색 결과 반환

### 2. FE 확인
- [ ] 메인 페이지 (`/`) 로딩 → 어디다있소 로고 표시
- [ ] 검색창 입력 → 로딩 → 결과 표시
- [ ] 마이크 버튼 → 에니메이션 동작
- [ ] 카테고리 지도 탭 → B1/B2 지도 표시
- [ ] 모바일 지도/AR 페이지 접속

### 3. FE ↔ BE 연동
- [ ] FE에서 검색 → BE API 호출 → 결과 화면 표시
- [ ] CORS 에러 없음 (브라우저 콘솔 확인)

### 4. QPM 테스트
```bash
python tests/stress_test_qpm.py \
  --url https://daiso-backend.xxxxx.lightsailcontainer.com \
  --qpm 30 \
  --duration 60
```
- [ ] P95 < 3,000ms
- [ ] 성공률 > 99%

---

## 비용 예상

| 서비스 | 사양 | 월 비용 |
|--------|------|--------|
| BE Container | Micro (1 vCPU, 512MB) | $7 |
| FE Container | Nano (256MB) | $3.5 |
| **합계** | | **$10.5** |

> 💡 테스트 후 사용하지 않으면 서비스를 삭제하여 비용 절약:
> ```bash
> aws lightsail delete-container-service --service-name daiso-backend
> aws lightsail delete-container-service --service-name daiso-frontend
> ```
