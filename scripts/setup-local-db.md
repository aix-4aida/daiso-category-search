# 로컬 DB 네이티브 설치 가이드 (Windows)

## 사전 조건
- Java 11+ (현재 Java 21 설치됨 ✅)
- Node.js (PM2용, 현재 22.x 설치됨 ✅)

---

## 1. Elasticsearch 7.x 설치

### 다운로드 & 압축 해제
```powershell
# PowerShell에서 실행
cd C:\Users\pengveloper

# Elasticsearch 7.17.27 다운로드 (최신 7.x)
Invoke-WebRequest -Uri "https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.27-windows-x86_64.zip" -OutFile "elasticsearch-7.17.27.zip"

# 압축 해제
Expand-Archive -Path "elasticsearch-7.17.27.zip" -DestinationPath "C:\elasticsearch"

# 압축파일 삭제
Remove-Item "elasticsearch-7.17.27.zip"
```

### JVM 메모리 제한 설정 (필수! 512MB 환경 대비)
```powershell
# jvm.options 파일 편집
notepad C:\elasticsearch\elasticsearch-7.17.27\config\jvm.options
```

**변경할 내용 (파일 상단의 -Xms, -Xmx 값 수정):**
```
-Xms128m
-Xmx128m
```

### 보안 비활성화 (로컬 개발용)
```powershell
# elasticsearch.yml 편집
notepad C:\elasticsearch\elasticsearch-7.17.27\config\elasticsearch.yml
```

**파일 끝에 추가:**
```yaml
xpack.security.enabled: false
discovery.type: single-node
```

### 실행
```powershell
# 직접 실행
C:\elasticsearch\elasticsearch-7.17.27\bin\elasticsearch.bat

# 또는 백그라운드 실행 (PowerShell)
Start-Process -FilePath "C:\elasticsearch\elasticsearch-7.17.27\bin\elasticsearch.bat" -WindowStyle Hidden
```

### 확인
```powershell
curl http://localhost:9200
# 또는 브라우저에서 http://localhost:9200 접속
```

---

## 2. Qdrant 설치

### 다운로드
```powershell
# PowerShell에서 실행
cd C:\Users\pengveloper

# Qdrant 최신 버전 다운로드 (Windows)
Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/download/v1.13.2/qdrant-x86_64-pc-windows-msvc.zip" -OutFile "qdrant.zip"

# 압축 해제
Expand-Archive -Path "qdrant.zip" -DestinationPath "C:\qdrant"

# 압축파일 삭제
Remove-Item "qdrant.zip"
```

### 실행
```powershell
# 직접 실행
C:\qdrant\qdrant.exe

# 기본 포트: REST API = 6333, gRPC = 6334
```

### 확인
```powershell
curl http://localhost:6333
# 또는 브라우저에서 http://localhost:6333/dashboard 접속
```

---

## 3. PM2로 프로세스 관리 (선택)

```powershell
# PM2 글로벌 설치
npm install -g pm2

# Qdrant를 PM2로 관리
pm2 start C:\qdrant\qdrant.exe --name qdrant

# Backend를 PM2로 관리
pm2 start "C:\elasticsearch\elasticsearch-7.17.27\bin\elasticsearch.bat" --name elasticsearch

# 상태 확인
pm2 status

# 로그 확인
pm2 logs
```

---

## 4. 한 번에 확인하기

모든 서비스 실행 후:
```powershell
# Elasticsearch
curl http://localhost:9200
# 응답: {"name":"DESKTOP-...","cluster_name":"elasticsearch",...}

# Qdrant
curl http://localhost:6333
# 응답: {"title":"qdrant - vectorass engine","version":"1.x.x"}

# Backend (개발 모드)
cd C:\Users\pengveloper\daiso-category-search\backend
poetry run uvicorn app.main:app --reload --port 8000
# http://localhost:8000/docs 에서 Swagger UI 확인
```

---

## 환경 변수 (.env)

프로젝트 루트의 `.env` 파일에 이미 설정됨:
```
ELASTICSEARCH_URL=http://localhost:9200
QDRANT_URL=http://localhost:6333
```
