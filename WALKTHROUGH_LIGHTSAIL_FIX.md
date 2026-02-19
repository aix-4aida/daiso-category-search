# Walkthrough: 하이브리드 검색 파이프라인 수정

## 문제
"알콜솜" 검색 시 **관련 없는 결과** (텀블러 세척제, 수세미, 렌즈 클리너 등) 반환

## 근본 원인

| 원인 | 설명 |
|------|------|
| **ChromaDB 인덱스 stale** | 이전 corrupted 데이터로 구축된 벡터 인덱스 |
| **RRF Fusion 불균형** | BM25와 Vector에 동일 가중치 → 벡터 noise가 BM25를 압도 |
| **NLU API 키 불일치** | `GEMINI_API_KEY` 참조 → Lightsail에선 `GOOGLE_API_KEY` 사용 |

## 변경 파일

### 1. [nlu.py](file:///c:/2026/final/daiso/merged-branch-by-bjy/backend/logic/nlu.py)
- `GEMINI_API_KEY` → `GOOGLE_API_KEY`

### 2. [search_service.py](file:///c:/2026/final/daiso/merged-branch-by-bjy/backend/services/search_service.py)
- BM25 fetch 수량: `top_k * 2` → `top_k * 5` (Vector와 동일)
- Near-zero vector score 필터링 (`score > 0.1`)
- RRF에 `sparse_weight=2.0` 적용
- 단계별 디버그 로깅 (`[BM25]`, `[Vector]`, `[Fusion]`)

### 3. [fusion.py](file:///c:/2026/final/daiso/merged-branch-by-bjy/backend/search/adapters/fusion.py)
- `rrf_fusion()`에 `sparse_weight` 파라미터 추가
- BM25(sparse) 결과에 가중치 배수 적용

### 4. [agent_graph.py](file:///c:/2026/final/daiso/merged-branch-by-bjy/backend/logic/agent_graph.py)
- `search_node`: NLU slots 상세 로깅, 후보별 ID/Name/Score 출력
- `rerank_node`: LLM 선택 ID와 reason 로깅

### 5. [rebuild_chroma_index.py](file:///c:/2026/final/daiso/merged-branch-by-bjy/rebuild_chroma_index.py) (NEW)
- ChromaDB 인덱스 삭제 후 products.db 기반 재구축 스크립트

## 검증 결과

```
Query: '알콜솜'
  [BM25] Top 3: [('579', '1610.33'), ('580', '1563.24'), ('604', '1563.24')]
  [Fusion] Top 3: [('579', '0.0328'), ('580', '0.0323'), ('604', '0.0317')]
  ✅ [1] ID=579, 오죤 알콜스왑 100매입
  ✅ [2] ID=580, 우리봄 알콜 스왑 100매입
  ✅ [3] ID=604, 우리봄 알콜스왑 40매입

Query: '텀블러' → ✅ 텀블러 정리대, 보온 머그 텀블러...
Query: '볼펜'  → ✅ 소프트스트릭 볼펜 블랙...
Query: '화장솜' → ✅ 일회용 미니 화장솜...
```

## 남은 작업
- [ ] Lightsail 재배포 시 `rebuild_chroma_index.py` 실행 또는 `chroma_db/` 폴더 업로드 필요

## Lightsail 배포 트러블슈팅

### 증상
- 로컬에서는 정상이나, Lightsail 배포 후 여전히 엉뚱한 검색 결과 반환
- "알콜솜" 검색 시 "텀블러 세척제" 등 노출

### 원인
- Lightsail 배포 환경에 `QDRANT_URL` 환경변수가 설정되어 있어 `search_service.py`가 **빈 Qdrant 컨테이너**를 벡터 검색 엔진으로 우선 선택함.
- 로컬에 구워진 ChromaDB 데이터가 무시됨.

### 해결
- `backend/services/search_service.py` 수정: 로컬 `backend/database/chroma_db` 폴더가 존재하면 **무조건 ChromaDB를 우선 사용**하도록 우선순위 변경.
- Docker 이미지 v18 (`backend-v3-chroma-priority`) 재배포 완료.
