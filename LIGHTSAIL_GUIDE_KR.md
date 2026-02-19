# 🚀 AWS Lightsail 배포 가이드 (Korean)

이 문서는 **Daiso Category Search** 애플리케이션을 AWS Lightsail 컨테이너 서비스(Container Services)에 배포하기 위한 가이드입니다.

## ✅ 필수 확인 사항 (상황 요약)

1.  **통신 방식**: AWS Lightsail 컨테이너 서비스의 같은 배포(Deployment) 안에 있는 컨테이너들은 `localhost`를 통해 서로 통신합니다.
    *   **Docker Compose (로컬 개발)**: `http://backend:8000` 사용
    *   **AWS Lightsail (운영 배포)**: `http://localhost:8000` 사용
2.  **설정 파일 분리**: 위 차이점을 해결하기 위해 배포용 설정 파일(`nginx.lightsail.conf`, `Dockerfile.frontend.lightsail`)을 별도로 생성했습니다.
3.  **외부 Elasticsearch**: Backend 컨테이너에서 외부 Elasticsearch로 연결하기 위해 환경 변수(`ELASTIC_URL`)를 설정해야 합니다.

---

## 1. Docker 이미지 빌드 (로컬 머신)

Lightsail에 올리기 전에 로컬에서 이미지를 빌드합니다.

**중요**: 모든 명령어는 **프로젝트의 최상위 루트 디렉토리** (`C:\2026\final\daiso\merged-branch-by-bjy`)에서 실행해야 합니다. (`backend` 폴더 안이 아닙니다!)

**필수**: Docker 빌드 전에 `.env` 파일이 있어야 합니다.
```powershell
# PowerShell
Copy-Item .env.example .env
```
(내용은 비워둬도 Lightsail 콘솔에서 환경 변수를 설정하므로 괜찮습니다. 파일 존재 여부만 중요합니다.)

### 1-1. Backend 빌드
Backend는 기존 `Dockerfile`을 그대로 사용합니다.

```bash
docker build -t daiso-backend .
```

### 1-2. Frontend 빌드 (**중요**)
Lightsail용 설정(`localhost` 프록시)이 적용된 전용 Dockerfile을 사용합니다.

```bash
docker build -f Dockerfile.frontend.lightsail -t daiso-frontend .
```

---

## 2. 이미지를 AWS Lightsail로 푸시 (Push)

AWS CLI 및 Lightsail Control Plugin이 설치되어 있어야 합니다.

1.  **로그인**: 셸에서 AWS에 로그인합니다 (필요한 경우).
2.  **푸시 명령어**:
    *   `<Service-Name>`: Lightsail에서 생성한 컨테이너 서비스 이름 (예: `daiso-service`)
    *   `<Local-Image>`: 위에서 빌드한 이미지 태그 (`daiso-backend`, `daiso-frontend`)
    *   `<Release-Image>`: Lightsail에 등록할 이름 (예: `backend-v1`, `frontend-v1`)

```bash
# Backend 푸시
aws lightsail push-container-image --service-name <Service-Name> --label backend-v1 --image daiso-backend

# Frontend 푸시
aws lightsail push-container-image --service-name daiso-search-service --label frontend-v1 --image daiso-frontend

# Qdrant 푸시 (먼저 이미지를 받아야 합니다!)
docker pull qdrant/qdrant:latest
aws lightsail push-container-image --service-name daiso-search-service --label qdrant-v1 --image qdrant/qdrant:latest

# Elasticsearch 푸시 (선택 사항 - 메모리 주의!)
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.9
aws lightsail push-container-image --service-name daiso-search-service --label elastic-v1 --image docker.elastic.co/elasticsearch/elasticsearch:7.17.9
```

*푸시가 완료되면 터미널에 `Image: :<Service-Name>.backend-v1.X` 형태의 이미지 주소가 출력됩니다. 이 주소를 복사해두세요.*

---

## 3. Lightsail 컨테이너 서비스 설정 (Deployments 탭)

AWS Lightsail 콘솔에서 **[Create your first deployment]** 또는 **[Modify your current deployment]**를 클릭합니다.

이제 **Backend**, **Frontend**, **Qdrant**, **Elasticsearch** 총 4개의 컨테이너를 설정합니다.

### 3-1. 컨테이너 1: Backend 추가
*   **이미지 선택**: 방금 푸시한 Backend 이미지 선택
*   **컨테이너 이름**: `backend` (중요하지 않지만 식별용)
*   **포트 구성**: `8000` (HTTP, TCP)
*   **환경 변수 (Environment Variables)**:
    *   `ELASTIC_URL`:
        *   컨테이너 추가한 경우: `http://localhost:9200`
        *   외부 서버 사용 시: `http://<외부-주소>:9200` (또는 HTTPS 주소)
    *   `QDRANT_URL`: `http://localhost:6333` (Qdrant도 같이 띄운다면 localhost, 외부는 해당 주소)
    *   `DISABLE_WHISPER`: `true` (메모리 절약을 위해 권장)
    *   `GOOGLE_API_KEY`: `(필요시 입력)`
    *   `OPENAI_API_KEY`: `(필요시 입력)`

### 3-2. 컨테이너 2: Qdrant 추가 (선택 사항)
*   **이미지 선택**: `qdrant/qdrant:latest` (Docker Hub 이미지 직접 입력)
*   **컨테이너 이름**: `qdrant`
*   **포트 구성**: `6333` (HTTP, TCP)
*   **환경 변수**: 별도 설정 없음
*   **시작 명령**: 비워둠

### 3-3. 컨테이너 3: Elasticsearch 추가 (**새로 추가됨**) 
*   **이미지 선택**: 방금 푸시한 `elastic-v1` 이미지 선택
*   **컨테이너 이름**: `elasticsearch`
*   **포트 구성**: `9200` (HTTP, TCP)
*   **환경 변수**:
    *   `discovery.type`: `single-node` (필수)
    *   `xpack.security.enabled`: `false` (보안 비활성화)
    *   `ES_JAVA_OPTS`: `-Xms512m -Xmx512m` (메모리 제한 필수)
*   **시작 명령**: 비워둠

### 3-4. 컨테이너 4: Frontend 추가
*   **이미지 선택**: 방금 푸시한 Frontend 이미지 선택 (`frontend-v1` 라벨이 붙은 것)
*   **컨테이너 이름**: `frontend`
*   **포트 구성**: `80` (HTTP, TCP)
*   **퍼블릭 엔드포인트**: **[체크]** (이 컨테이너를 통해 접속합니다)

### 3-4. Backend 환경 변수 수정
Qdrant 컨테이너를 추가했다면, Backend 컨테이너의 환경 변수를 확인하세요.
*   `QDRANT_URL`: `http://localhost:6333` (컨테이너끼리는 localhost 통신)

### 3-5. 기타
*   **시작 명령 (Launch Command)**: 비워둠 (Dockerfile의 CMD 사용)
*   **상태 확인 (Health Check)**: 기본값 유지

---

## 4. 배포 및 확인

1.  **[저장 및 배포]** 버튼을 클릭합니다.
2.  배포가 `Active(활성)` 상태가 될 때까지 기다립니다 (몇 분 소요).
3.  상단의 **퍼블릭 도메인** 주소로 접속합니다.
4.  웹페이지가 뜨고 검색 기능이 작동하는지 확인합니다.

---

## ❓ 문제 해결 (Troubleshooting)

*   **502 Bad Gateway**: 백엔드가 아직 실행 중이거나 죽었을 수 있습니다. 로그를 확인하세요.
*   **API 호출 실패 (404/500)**:
    *   브라우저 개발자 도구(F12) > Network 탭 확인.
    *   Frontend가 `/api/...`로 요청을 보내는지 확인.
    *   Lightsail 로그에서 Nginx가 `upstream sent no valid header` 등의 에러를 뱉는지 확인. (Backend 연결 문제)
*   **Elasticsearch 연결 오류**: Backend 로그에서 확인. 보안 그룹(방화벽)에서 Lightsail IP가 허용되어 있는지 확인해야 할 수도 있습니다.
