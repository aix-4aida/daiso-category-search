# Python 3.12 slim version for smaller image size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed (e.g. for audio processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run commands
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]