# Project Setup Guide

## 1. 가상환경 생성 및 활성화

### 가상환경 생성 (최초 1회)
```bash
python -m venv venv
```

### 가상환경 활성화
**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
venv\Scripts\activate
```

*활성화 시 터미널 프롬프트 앞에 `(venv)`가 표시되어야 합니다.*

## 2. 라이브러리 설치

가상환경이 활성화된 상태에서 아래 명령어를 실행하세요.
```bash
pip install -r requirements.txt
```

## 3. 실행 방법

```bash
uvicorn app.main:app --reload
```
