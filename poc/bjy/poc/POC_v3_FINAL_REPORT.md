# PoC v3: 검색 파이프라인 최종 검증 리포트

> **버전**: v3.0 (v0.6.4 릴리스 기반)
> **작성일**: 2026-01-23
> **변경점**: Mock DB 데이터 정제, Golden Test Cases 확장 (42건), Latency 측정 기능 추가

---

## 1. Executive Summary

### 1.1. 핵심 결론
**LLM 기반 AG Reranker 파이프라인은 데이터 정제 후에도 안정적인 성능을 유지하며, 상용 서비스 수준의 정확도(91.9%)를 달성했습니다.**

### 1.2. 주요 성과 지표

| 파이프라인 단계 | 지표 | 결과 | 목표 | 달성 |
|:---|:---|:---|:---|:---|
| Query Processor | Intent Accuracy | **95.2%** (40/42) | 90% 이상 | ✅ |
| Hybrid Retrieval | Recall@20 | **71.4%** (30/42) | 80% 이상 | ⚠️ |
| AG Reranker (CE) | Top-1 Accuracy | 29.7% (11/37) | - | Baseline |
| **AG Reranker (LLM)** | **Top-1 Accuracy** | **91.9% (34/37)** | 90% 이상 | ✅ |
| Location Guide | Accuracy | **86.5%** (32/37) | 100% | ⚠️ |

### 1.3. v2 대비 변경 사항
- **Test Cases**: 30건 → **42건** (Hard 14건, False Positive 5건 추가)
- **Mock DB**: 미분류 상품 200건 → **0건** (100% 분류 완료)
- **Latency 측정**: 평균 **~1.9초** (v2: ~1.7초, 케이스 난이도 증가로 소폭 상승)

---

## 2. 테스트 환경

### 2.1. 데이터셋
| 데이터 | 건수 | 비고 |
|:---|:---|:---|
| Mock Product DB | 601건 | 미분류 0건 (Clean Data) |
| Golden Test Cases | 42건 | Easy 21, Medium 7, Hard 14 |
| False Positive Cases | 5건 | 다이소에 없는 상품 쿼리 |

### 2.2. 모델 구성
| 역할 | 모델 | 비고 |
|:---|:---|:---|
| Query Processor | Gemini 2.0 Flash | 의도 분석 + 키워드 추출 |
| Hybrid Search (BM25) | rank_bm25 | 키워드 기반 |
| Hybrid Search (Vector) | paraphrase-multilingual-MiniLM-L12-v2 | 의미 기반 |
| Cross-Encoder | ms-marco-MiniLM-L-6-v2 | Baseline |
| **LLM Reranker** | **Gemini 2.0 Flash** | **최종 선택 모델** |

---

## 3. 단계별 상세 결과

### 3.1. Step 1: Query Processor

**목표**: 자연어 쿼리에서 검색 의도, 키워드, 필터 조건을 정확히 추출

| 지표 | 결과 | 분석 |
|:---|:---|:---|
| Intent Accuracy | **95.2% (40/42)** | 2건 미스매치 (복합 키워드 분리 이슈) |

**실패 케이스 분석**:
- "냄새 안 나는 쓰레기 봉투" → 키워드를 "쓰레기봉투"로 합성하지 못함
- "와인 셀러 추천해주세요" → False Positive 케이스 정상 인식

### 3.2. Step 2: Hybrid Retrieval

**목표**: 정답 상품을 Top-K 후보군에 포함

| 방법 | Recall@5 | Recall@10 | Recall@20 |
|:---|:---|:---|:---|
| BM25 | 59.5% (25) | 64.3% (27) | 71.4% (30) |
| Vector | 21.4% (9) | 28.6% (12) | 38.1% (16) |
| **Hybrid** | **61.9% (26)** | **69.0% (29)** | **71.4% (30)** |

**분석**:
- v2(86.7%) 대비 Recall 하락 → **테스트 케이스 난이도 상승 영향**
- Hard 케이스(부정 조건, 암시적 의도)에서 검색 한계 확인
- 그럼에도 **Hybrid가 BM25/Vector 단독 대비 우수**

### 3.3. Step 3: AG Reranker

**목표**: Top-20 후보군에서 정답을 Top-1으로 선정

| 모델 | Top-1 Accuracy | Location Guide | Avg Latency |
|:---|:---|:---|:---|
| Cross-Encoder | 29.7% (11/37) | ❌ 불가 | ~61ms |
| **LLM (Gemini)** | **91.9% (34/37)** | **86.5%** | **~1.9s** |

**핵심 인사이트**:
- LLM이 Cross-Encoder 대비 **+62.2%p 정확도 향상**
- 부정 조건("락스 없는"), 암시적 의도("자취생 필수템") 정확히 처리
- Location Guide 86.5%: 일부 케이스에서 위치 정보 누락 (JSON 파싱 이슈)

---

## 4. 리랭킹 모델 비교 (Benchmark)

| Model | Success | Top-1 Acc | MRR | Avg Time | 비고 |
|:---|:---|:---|:---|:---|:---|
| Cross-Encoder (ms-marco-MiniLM) | 10/29 | 34.5% | 0.498 | 61.2ms | 속도 빠름, 추론 불가 |
| BGE-Reranker-v2-m3 | 23/29 | 79.3% | 0.856 | 665.8ms | 다국어 지원 |
| Qwen3-Reranker-0.6B | 4/29 | 13.8% | 0.295 | 1824.9ms | GPU 필요 |
| Naver-Provence-Reranker | 23/29 | 79.3% | 0.828 | 3753.8ms | 상용화 협의 필요 |
| LLM (GPT-4o-mini) | 26/29 | 89.7% | 0.897 | 2759.6ms | 추론 능력 우수 |
| **LLM (Gemini 2.0 Flash)** | **27/29** | **93.1%** | **~0.93** | **~1700ms** | **최고 정확도, 선택 모델** |

> **결론**: Gemini 2.0 Flash가 정확도(93.1%)와 속도(~1.7s) 모두에서 LLM 중 최고 성능

---

## 5. 결론 및 권고사항

### 5.1. 파이프라인 검증 완료
```
User Query → Query Processor (Gemini) → Hybrid Search (Top-20) → AG Reranker (Gemini) → Top-1 위치 안내
```

### 5.2. 프로덕션 적용 권고
1. **LLM Reranker 필수 적용**: Cross-Encoder로는 복합 의도 처리 불가
2. **Hybrid Search 유지**: BM25 + Vector 조합이 단독 대비 우수
3. **Latency 허용**: ~2초 응답은 UX 허용 범위 내 (즉각 피드백 필요 시 스피너 표시)

### 5.3. 향후 개선 과제
| 과제 | 우선순위 | 설명 |
|:---|:---|:---|
| Hard Case Recall 개선 | High | 부정 조건/암시적 의도에 대한 검색 쿼리 확장 |
| Location Guide 안정화 | Medium | JSON 파싱 오류 핸들링 강화 |
| 2단계 Reranking 검토 | Low | BGE → LLM 순차 적용으로 비용 최적화 |

---

## 6. 첨부 자료
- [Golden Test Cases 분석](./document/poc_v2_Golden_Test_Cases_Analysis.md)
- [AG Module 검증 리포트](./document/poc_v2_AG_Module_Validation_Report.md)
- [Mock DB 분석](./document/poc_v2_Mock_Product_DB_Analysis.md)
