# 1. 가상환경 생성 (없으면)
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

# 2. 가상환경 활성화
Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# 3. 필수 라이브러리 설치
Write-Host "Installing dependencies..."
pip install selenium webdriver-manager requests

# 4. 인스펙터 실행
Write-Host "Starting Inspector..."
$env:PYTHONPATH="."
python backend/database/inspect_page.py
