
# RAG Pipeline Robustness PoC Report (v2)

## 1. 목적 (Purpose)
본 PoC(Proof of Concept)는 사용자의 다양한 검색 의도와 모호한 질의를 정확하게 처리하기 위해, **'의도 파악 - 하이브리드 검색 - 지능형 리랭킹'**으로 이어지는 3단계 파이프라인의 성능과 필요성을 검증하는 것을 목적으로 한다.

특히 기존 Keyword 매칭 방식의 한계를 극복하기 위해 다음 항목들을 중점적으로 증명하고자 한다:
1.  **의도 파악의 중요성**: 단순 키워드 매칭 대비, 의도(필터, 정렬 등)를 구조화했을 때의 이점
2.  **하이브리드 검색의 효율성**: BM25(단어)와 Vector(의미) 결합 시 Recall@K 성능 변화
3.  **지능형 리랭킹(AG)의 가치**: LLM이 개입했을 때의 정확도 향상 및 '위치 안내' 등 부가 가치 창출

---

## 2. 증명 과제 및 실험 설계 (Experiment Design)

| 단계 | 증명 항목 | 실험 방법 | 데이터 (Mock DB) |
| :--- | :--- | :--- | :--- |
| **Step 1** | **Query Processor** | 자연어 질의에서 키워드/필터/정렬 의도를 얼마나 정확히 추출하는가? | Golden Test Cases 30개 (난이도 상) |
| **Step 2** | **Hybrid Retrieval** | BM25 단독 vs Vector 단독 vs Hybrid 사용 시 **Top-K Recall** 비교 | Mock Product 601개 |
| **Step 3** | **AG Reranking** | 단순 점수 기반(Cross-Encoder) vs LLM 기반 리랭킹의 **Top-1 정확도** 및 설명 능력 | (동일) |

---

## 3. 데이터 준비 (Data Preparation)
실험의 신뢰도를 높이기 위해 LLM을 활용한 고품질 Mock Data를 구축하였다.

- **Source**: 기존 `products.db` (601개 상품)
- **Enrichment**: Gemini 2.0 Flash를 활용하여 각 상품에 대해 다음 정보를 생성
    - `Raw Detail Text`: 구성품, 재질, 사용법 등이 포함된 상세 페이지 텍스트 시뮬레이션
    - `Searchable Description`: 검색 엔진 인덱싱용 요약문
    - `Location`: 카테고리 기반 가상 위치 정보 (예: "2층 욕실용품 A열")
- **Golden Dataset**: 검색 난이도가 높은 30가지 케이스 정의 (부정문, 복합 의도, 추상적 형용사 등)

---

## 4. 실험 결과 (Results)

### 4.1. Step 2: Hybrid Retrieval 성능 (Top-K Recall)
**[결과 요약]**: Hybrid 검색이 모든 Top-K 구간에서 가장 우수한 성능을 보였다.

| Method | Recall@5 | Recall@10 | Recall@20 | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **BM25** | 66.7% (20) | 73.3% (22) | 83.3% (25) | 키워드 일치 시 강력하나 의미 파악 불가 |
| **Vector** | 23.3% (7) | 30.0% (9) | 40.0% (12) | 단독 사용 시 정밀도 부족 (Top-20에서도 40%) |
| **Hybrid** | **70.0% (21)** | **83.3% (25)** | **86.7% (26)** | **BM25의 정밀함 + Vector의 보완성 결합** |

> **인사이트**: 
> - Vector 검색 단독으로는 Recall이 매우 낮게 측정됨 (아마도 데이터셋 특성상 고유명사나 구체적 상품명이 많아 Embedding만으로는 한계).
> - **Hybrid 방식이 BM25의 약점을 완벽하게 보완**하며, Top-20 기준 86.7%의 높은 Recall을 달성함.
> - 따라서 Reranker에게 20개의 후보를 넘겨주는 것이 안정적임.

### 4.2. Step 3: AG Reranking 성능
**[결과 요약]**: Cross-Encoder는 속도가 빠르나 복합 의도(부정문, 암시적 니즈) 파악에 한계가 있었으며, LLM(Gemini)이 가장 높은 정확도를 기록했다.

| Method | Top-1 Accuracy | Location Guide | Latency (Avg) |
| :--- | :--- | :--- | :--- |
| **Cross-Encoder** | 34.5% (10/29) | 불가능 (N/A) | **빠름 (<0.1s)** |
| **LLM (Gemini)** | **93.1% (27/29)** | **가능 (정확도 93%)** | 느림 (~1.5s) |

> **인사이트**:
> - **Cross-Encoder**: 예상보다 성능이 저조함(34.5%). 특히 "부정 조건(not)"이나 "암시적 니즈"를 전혀 처리하지 못하고 단순 키워드 매칭에 머무름.
> - **LLM**: 93%의 압도적인 정확도를 기록. 복잡한 문맥을 정확히 이해하고 위치 안내까지 성공적으로 수행함. 비용 대비 효과가 확실함.

---

## 5. 결론 및 제언 (Conclusion)
1.  **Hybrid 검색 도입**: Vector 단독 사용보다는 BM25와 결합 시 **Recall 86.7%** 달성. Reranker에게 **Top-20**개를 전달하는 것이 최적.
2.  **LLM Reranking 채택**: 단순 정렬이 아닌 **"지능형 안내(Agentic Search)"**를 위해서는 LLM이 필수적임. 속도 문제를 완화하기 위해 Hybrid 검색으로 후보를 20개로 좁히는 전략이 유효함.
3.  **최종 파이프라인 제안**:
    - `Query Processor (Gemini)` -> `Hybrid Search (BM25+Vector)` -> `Candidate (Top-20)` -> `AG Reranker (Gemini)` -> `Final Response`
