# 1. 가상환경 생성 (없으면)
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

# 2. 가상환경 활성화
Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# 3. 필수 라이브러리 설치 (크롤러용)
Write-Host "Installing dependencies (selenium, webdriver-manager)..."
pip install selenium webdriver-manager requests numpy chromadb

# 4. 크롤러 실행
Write-Host "Starting Crawler..."
$env:PYTHONPATH="."
python backend/database/crawler_full.py
