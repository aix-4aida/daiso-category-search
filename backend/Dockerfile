FROM python:3.10-slim

# System deps: ffmpeg for audio processing, curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (lightweight, no torch)
COPY requirements-deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY poc/ ./poc/

# Ensure outputs directory exists
RUN mkdir -p outputs/normalized outputs/streaming_audio

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
