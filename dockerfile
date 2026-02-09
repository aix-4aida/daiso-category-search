FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI 실행 (포트 8000번)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]