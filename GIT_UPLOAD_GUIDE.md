# 🚀 Git 업로드 파일 목록 (feature/kms 브랜치)

> **Target Branch**: `feature/kms`  
> **Repository**: https://github.com/aix-4aida/daiso-category-search  
> **Updated**: 2026-02-09

---

## ✅ 업로드해야 할 파일 목록

### 1. Backend 파이프라인 (KMS) - 핵심!
```
backend/services_kms/
├── run_all_pipeline.py          # ⭐ 통합 파이프라인 (수정됨)
├── stt_to_json.py               # STT 변환
├── poc_flash_test.py            # Intent 분류 (수정됨 - json import 제거)
├── simple_keyword_extractor_gemini.py   # 키워드 추출
├── expand_keywords_comparison_gemini.py # 키워드 확장
├── run_benchmark.py             # 벤치마크 실행
└── poc_v5_experiment_phase_1.py # Reranking
```

### 2. Backend API 서버
```
backend/
├── main.py                      # ⭐ FastAPI 서버 (대폭 수정됨 - STT 파이프라인)
├── config.yaml                  # 설정 파일
├── ws_stt.py                    # WebSocket STT 핸들러
├── stt/
│   ├── __init__.py
│   ├── adapters.py              # STT 어댑터
│   ├── audio_converter.py
│   ├── quality_gate.py
│   ├── policy_gate.py
│   └── types.py
└── database/
    ├── connection.py            # DB 연결
    └── products.db              # ⚠️ 용량 큼 (3.4MB) - Git LFS 고려
```

### 3. Frontend (Next.js로 변경됨!)
```
frontend/
├── package.json                 # ⭐ VITE → NEXT.JS 변경됨!
├── src/
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── SearchResults.jsx    # 지도 내비게이션 포함
│   │   ├── VoiceSearch.jsx
│   │   └── ...
│   ├── components/
│   ├── config/
│   │   └── mapConfig.js         # 매대 좌표
│   └── ...
└── tailwind.config.js
```

### 4. 루트 레벨 파일
```
./
├── run_all_pipeline.py          # ⭐ 파이프라인 (수정됨 - subprocess 방식)
├── KMS_README.md                # 📋 팀원용 문서 (새로 생성)
├── .env                         # ⚠️ Git에 올리지 마세요! (.gitignore에 추가)
└── requirements.txt             # Python 의존성
```

### 5. PoC 디렉토리
```
poc/
├── intent/
│   └── poc_flash_test.py        # (수정됨 - json import 제거)
├── kms/
│   ├── simple_keyword_extractor_gemini.py
│   └── expand_keywords_comparison_gemini.py
├── kdg/
│   └── poc_v5_experiment_phase_1.py
├── lyg/
│   ├── scripts/run_benchmark.py
│   └── data/catalog.sqlite_export.tsv
└── data/
    └── benchmark_out/           # 벤치마크 설정 (configs/*.yaml)
```

---

## ⚠️ Git에 올리지 말아야 할 파일들

```gitignore
# 환경 설정 (민감 정보)
.env
*.json (API 키 포함 가능성)
daisoproject-sst.json           # Google 인증 파일

# 빌드 결과물
__pycache__/
node_modules/
.next/
venv/

# 데이터 파일 (용량/민감)
*.db                            # Git LFS 사용 또는 제외
backend/services_kms/data/      # 파이프라인 출력 파일들
outputs/                        # 임시 오디오 파일

# IDE
.idea/
.vscode/
```

---

## 📋 Git 커밋 가이드

### 1. 변경 파일 확인
```bash
git status
git diff --name-only
```

### 2. 스테이징
```bash
# 핵심 파일만 선택적으로 추가
git add backend/services_kms/*.py
git add backend/main.py
git add backend/stt/
git add frontend/package.json
git add frontend/src/
git add run_all_pipeline.py
git add KMS_README.md

# 또는 한번에 (주의: .gitignore 확인 필요)
git add -A
```

### 3. 커밋 메시지 예시
```bash
git commit -m "feat(kms): 통합 파이프라인 및 Next.js 프론트엔드 마이그레이션

- backend/main.py: STT 파이프라인 API 추가 (/stt/compare, /ws/stt)
- backend/services_kms/: KMS 전용 파이프라인 모듈
- frontend: Vite → Next.js 마이그레이션
- run_all_pipeline.py: subprocess 방식으로 리팩토링
- KMS_README.md: 팀원용 설치/사용 가이드 추가
"
```

### 4. 푸시
```bash
git push origin feature/kms
```

---

## 🔄 주요 변경사항 요약

| 변경 전 | 변경 후 | 영향 |
|---------|---------|------|
| `run_all_pipeline.py` (async/direct import) | subprocess 방식 | 모듈 독립성 향상 |
| `backend/main.py` (간단한 API) | STT 파이프라인 완전 통합 | 음성 검색 기능 강화 |
| Frontend (Vite + React) | Next.js 14 | 프레임워크 변경! |
| 없음 | `backend/services_kms/` | KMS 전용 파이프라인 |
| 없음 | `KMS_README.md` | 팀원 온보딩 문서 |

---

## 👥 팀원 알림 사항

1. **프론트엔드 변경**: `npm install` 다시 실행 필요 (Next.js 의존성)
2. **환경 변수**: `.env` 파일에 `GEMINI_API_KEY` 필수
3. **STT 기능**: FFmpeg 설치 필요
4. **DB**: `products.db` 파일이 커서 Git LFS 사용 권장
