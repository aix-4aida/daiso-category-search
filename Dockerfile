# ── Stage 1: Build ──
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements (lightweight version for Lightsail)
COPY requirements-lightsail.txt requirements.txt

# Install CPU-only PyTorch FIRST (avoids pulling ~2GB CUDA version)
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu

# Then install the rest (sentence-transformers will reuse the CPU torch)
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.10-slim

# Install runtime dependencies (ffmpeg for audio conversion)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY backend/ ./backend/
COPY .env .env

# Copy frontend for static serving
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
