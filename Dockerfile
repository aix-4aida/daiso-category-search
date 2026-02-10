# ===== Stage 1: Build (C 확장 컴파일용) =====
FROM python:3.10-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== Stage 2: Runtime (최소 이미지) =====
FROM python:3.10-slim

WORKDIR /app

# 런타임 의존성만 (ffmpeg for pydub, build-essential 제외)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 빌드 단계에서 설치된 패키지만 복사
COPY --from=builder /install /usr/local

COPY app/ app/
COPY backend/ backend/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
