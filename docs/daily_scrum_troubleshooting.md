# Daily Scrum Log - Troubleshooting & Resolutions

이 문서는 프로젝트 진행 중 발생한 주요 이슈(Trouble)와 해결 과정(Shooting)을 날짜별로 요약한 기록입니다. Daily Scrum 및 주간 보고 시 참고 자료로 활용할 수 있습니다.

## 2026-02-19 (Today)
### 1. DB 이미지 경로 불일치 이슈
- **발생 문제 (Trouble)**: 
  - `merged-branch-by-bjy` 브랜치에서 Pull 받은 `products.db`의 `image_path` 컬럼이 이전 작업 환경(`C:\2026\final\...`)의 절대 경로로 고정되어 있음.
  - 이로 인해 현재 로컬 환경에서 이미지를 불러오지 못하는 문제 발생.
- **해결 (Shooting)**:
  - `verify_current_db.py`로 문제 확인 (총 5,085개 경로 불일치).
  - `fix_db_paths.py` 스크립트를 제작하여 DB 내 모든 이미지 경로를 현재 프로젝트 루트(`C:\Users\301\pjt\Final\search\daiso-category-search\...`) 기준으로 일괄 변환(Update) 처리.
  - 변환 후 샘플 데이터를 조회하여 정상 경로 반영 확인 완료.

### 2. 저장소 동기화 (Sync)
- **발생 문제 (Trouble)**: 
  - Saida Organization 원격 저장소의 최신 변경 사항(`merged-branch-by-bjy`)이 로컬에 반영되지 않음.
- **해결 (Shooting)**:
  - Git Remote 및 Branch 상태 점검 후 `git pull origin merged-branch-by-bjy` 수행.
  - 대용량 이미지 파일 및 점검 스크립트(`inspect_*.py`) 동기화 완료.

---

## 2026-02-13
### 1. 로컬 배포 시뮬레이션 환경 구축
- **발생 문제 (Trouble)**: 
  - 로컬 개발 환경(`npm run dev`)과 실제 배포 환경(Nginx Proxy)의 API 경로 처리 방식이 달라(`localhost:8000` vs `/api/`), 배포 시 404 에러 발생 가능성 존재.
- **해결 (Shooting)**:
  - `docker-compose.prod.yml`을 작성하여 로컬에서도 Nginx를 통한 리버스 프록시 환경을 모사.
  - `app.js` 코드를 수정하여 배포 환경에서는 상대 경로(`/api/search`)를 사용하도록 분기 처리 로직 검증.

---

## 2026-02-11
### 1. STT(음성 인식) 안정성 문제
- **발생 문제 (Trouble)**: 
  - 단일 STT 엔진 사용 시 외부 API 장애나 네트워크 이슈로 인해 음성 검색 기능 전체가 마비될 위험 존재.
- **해결 (Shooting)**:
  - **Fallback Logic 구현**: Google STT를 우선 시도하고, 실패 시 로컬 또는 대체 Whisper 모델로 자동 전환되는 로직을 `stt_service.py`에 구현.
  - 파이프라인 통합 테스트를 통해 Failover 동작 검증 완료.

---

## 2026-02-05
### 1. 프롬프트 버전 파편화 및 파일 유실
- **발생 문제 (Trouble)**: 
  - `search-roca` 리포지토리의 핵심 벤치마크 스크립트가 유실되고, `daiso-category-search`에는 더 이상 쓰지 않는 `poc_v2` 프롬프트들이 혼재되어 혼란 가중.
- **해결 (Shooting)**:
  - 유실된 `generate_v6_db.py` 및 벤치마크 스크립트 복구.
  - 불필요한 `poc_v2` 프롬프트 삭제 및 최신 `poc_v5` 시스템 프롬프트를 명시적으로 파일화하여 버전 관리 체계 정립.

---

## 2026-01-29
### 1. AR 카메라 초기화 실패
- **발생 문제 (Trouble)**: 
  - 모바일 웹 환경에서 AR 네비게이션 진입 시 카메라 권한을 획득하지 못하거나 검은 화면이 뜨는 현상 발생.
- **해결 (Shooting)**:
  - 브라우저 캐시 문제 및 HTTPS(또는 localhost) 컨텍스트에서의 권한 요청 로직 재점검.
  - 디버깅 툴을 통해 카메라 스트림 초기화 시점을 조정하여 해결.

### 2. Git Merge 충돌
- **발생 문제 (Trouble)**: 
  - 기능 병합 과정에서 대규모 충돌 발생으로 코드 무결성 위협.
- **해결 (Shooting)**:
  - 무리한 충돌 해결 대신 Merge를 Abort(중단)하고, 로컬 저장소를 Upstream과 동기화(Sync)한 후 순차적으로 변경 사항을 재반영하는 안전한 방식으로 선회.

---

## 2026-01-27
### 1. 검색 정확도 미달 (PoC v5)
- **발생 문제 (Trouble)**: 
  - 특정 복합 의도 검색어에 대해 LLM이 엉뚱한 카테고리를 추천하는 케이스 발견.
- **해결 (Shooting)**:
  - **CoT(Chain-of-Thought) 도입**: 시스템 프롬프트에 "생각하는 과정" 예시를 추가하여 추론 능력 향상.
  - **Golden Dataset 확장**: 실패 케이스를 테스트 데이터셋에 추가하여 회귀 테스트(Regression Test) 환경 구축.

---

## 2026-01-23
### 1. AG Module 검증 전략 수립
- **발생 문제 (Trouble)**:
  - Re-ranking 모듈의 정확한 효용성을 수치적으로 증명하기 어렵고, 한국어에 최적화된 모델 선정에 대한 근거가 부족함.
- **해결 (Shooting)**:
  - 기존 문서를 `poc_v2_AG_Module_Validation_Report.md`로 고도화하여 검증 목적, 실험 계획, 결과 분석 체계를 확립.
  - Re-ranking 수행 전후의 정확도 차이를 비교 분석하는 실험 설계를 통해 모듈 도입의 타당성 확보.

---

## 2026-01-21
### 1. Git Ignore 설정 누락
- **발생 문제 (Trouble)**:
  - `idea-exploit` 등 불필요한 폴더가 버전 관리에 포함되어 저장소 용량을 차지하고 보안상 노출될 우려가 있음.
- **해결 (Shooting)**:
  - `.gitignore` 파일을 업데이트하여 해당 폴더를 추적 대상에서 명시적으로 제외(Untracked).
  - 커밋 메시지에 한글 설명을 보강하여 변경 의도를 명확히 기록.

---

## 2026-01-20
### 1. RAG 검색 품질 저하
- **발생 문제 (Trouble)**:
  - 키워드 검색 시 의도와 다른 문서가 추출되거나(Low Precision), 필요한 문서가 누락되는(Low Recall) 문제 발생.
- **해결 (Shooting)**:
  - `RAG_System_experiment_keyword.py`를 통해 Top-K 값(10, 30, 50)에 따른 성능 변화를 시뮬레이션.
  - 실험 결과에 기반하여 검색 정확도와 재현율 간의 균형점(Optimal Top-K)을 도출하고 리포트에 반영.

---

## 2026-01-19
### 1. PoC 코드 통합 난항
- **발생 문제 (Trouble)**:
  - `search-roca`에서 개발된 RAG Robustness PoC 코드를 `daiso-category-search` 메인 프로젝트로 이관하는 과정에서 의존성 충돌 우려.
- **해결 (Shooting)**:
  - 별도의 기능 브랜치(`feat/rag-robustness-poc`)를 생성하여 선 통합 후 `dev` 브랜치로 병합하는 전략 채택.
  - `requirements.txt`와 `CHANGELOG.md`를 함께 업데이트하여 통합 버전(`v0.3.1` 등) 관리 체계 유지.
