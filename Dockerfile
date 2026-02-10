# Python 3.11 슬림 버전 사용 (가벼움)
FROM python:3.11-slim

# 작업 폴더 설정
WORKDIR /app

# 필수 패키지 설치 (curl 등)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 전체 복사
COPY backend .

# 8000번 포트 열기
EXPOSE 8000

# 서버 실행 (FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]