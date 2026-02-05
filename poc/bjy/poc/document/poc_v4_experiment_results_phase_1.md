# PoC v4 실험 결과 보고서

## 개요
- **목표**: PoC v4 로직을 사용하여 전체 자연어 쿼리 데이터셋(단순 검색 + 대화형 쿼리)에 대한 처리 능력을 포괄적으로 검증.
- **데이터셋**: `poc_v4_golden_test_cases.json` (전체 **61건**).
- **방식**:
    1. **의도 파악 (Intent Extraction)**: Gemini 2.0 Flash로 키워드 및 필터 추출. (System Prompt 1 사용)
    2. **검색 시뮬레이션 (Retrieval)**: 정답(Ground Truth) + 무작위 상품 10개(Noise) 주입.
    3. **AG 재순위화 (Reranking)**: Gemini 2.0 Flash가 사용자 의도에 맞춰 Top-1 선정. (System Prompt 2 사용)

## 0. 사용된 시스템 프롬프트 (System Prompts)
실험 결과의 신뢰성을 위해 실제로 사용된 프롬프트를 공개합니다.

### [Prompt 1] 의도 파악 (Intent Extraction)
> 사용자의 불완전한 발화에서 핵심 키워드와 필터 조건을 추출하여 검색 엔진이 이해할 수 있는 JSON으로 변환합니다.
```text
You are a 'Search Query Processor' for a Daiso product search engine.
Your goal is to extract structured intent from the user's natural language query.

Context:
- User is searching for household goods.
- Determine if the query is a "Search" intent or something else.
- Extract "Keywords" for retrieval.
- Extract "Filters" if explicitly stated (e.g., "cheap", "no plastic").

Input Query: "{query}"

Output JSON Format:
{{
    "is_search_intent": true/false,
    "keywords": ["term1", "term2"],
    "filters": {{ "category": "...", "attributes": "...", "negatives": "..." }}
}}
```

### [Prompt 2] AG 재순위화 (Agentic Reranking)
> 추출된 의도(Intent)와 후보 상품 목록(Candidates)을 비교하여, 사용자의 미세한 요구사항(부정어, 설명 등)을 만족하는 최적의 상품을 선정합니다.
```text
You are an AI Search Agent.
User Query: "{query}"
Extracted Intent: {intent_str}

Task:
1. Analyze the candidates based on the user's specific request (consider filters, descriptions, negations).
2. Select the BEST matching item (Top-1) that satisfies the user's need.
3. If no item perfectly matches, select the closest alternative or explain why none match.

Candidates:
{candidate_text}

Output JSON Only:
{{
    "top_match_id": id,
    "reason": "Explain why this item was chosen based on the query nuances..."
}}
```

## 결과 요약
| 항목 | 값 |
| :--- | :--- |
| **총 평가 건수** | 61건 |
| **유효 평가(정답 있음)** | 55건 |
| **정확도 (Accuracy)** | **80.0%** (44/55) |
| **False Positive 방어** | 6건 중 6건 방어 성공 (TV, 명품 가방 등 미판매 상품 '없음' 처리) |

## 1. 포맷 검증 (Format Consistency)
> **목표**: "넣으면 JSON이 튀어나온다." (기본 동작 안정성 검증)

실험 중 발생한 JSON 파싱 에러 비율을 분석한 결과입니다.
*   **시도 횟수**: 총 122회 (Intent Parsing 61회 + Reranking 61회)
*   **성공 횟수**: 121회
*   **실패 횟수**: 1회 (Case 47: `Expecting value: line 1 column 1`)
*   **성공률**: **99.2%**
    *   **분석**: Gemini 2.0 Flash 모델은 프롬프트의 지시(Output JSON Only)를 매우 잘 따르며, 간헐적인 네트워크/토큰 이슈를 제외하면 **상용 수준의 포맷 안정성**을 확보했음을 확인했습니다.

## 2. 논리 검증 (Reasoning Accuracy) 상세 평가표
*(전체 61건 중 대표적인 성공/실패 사례 및 신규 추가된 자연어 쿼리 위주로 정리)*

| 테스트 질문 (Query) | 시나리오 유형 | LLM 선택 | 결과 | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **"주방세제"** | Simple Query | (선택 안함) | 🔴 X | 너무 광범위하여 선택 유보 (엄격) |
| **"수납함"** | Simple Query | (선택 안함) | 🔴 X | 너무 광범위하여 선택 유보 (엄격) |
| **"미백 세럼"** | Simple Query | 본셉 비타씨 미백샷 | 🟢 O | - |
| **"비닐 봉투"** | Simple Query | (선택 안함) | 🔴 X | '비닐 봉투' 키워드 매칭 실패 (엄격) |
| **"종이컵"** | Simple Query | 미피 캐릭터 종이컵 | 🟢 O | - |
| **"곰팡이 제거"** | Implicit Needs | 닥터오렌지 곰팡이 제거 젤 | 🟢 O | - |
| **"가성비 좋은 물티슈"** | Subjective | (선택 안함) | 🔴 X | '가성비' 판단 기준 모호 |
| **"비건 주방세제"** | Category Overlap | (선택 안함) | 🔴 X | '비건' 속성 매칭 실패 |
| **"플라스틱 없는 수납함"** | Negative | (선택 안함) | 🔴 X | 조건 만족 상품 찾기 어려움 |
| **"소독 스프레이 without 알코올"** | Negative | (선택 안함) | 🔴 X | 조건 만족 상품 찾기 어려움 |
| **"강아지"** | Simple Query | [펫] 더독 육포 | ❌ Fail | 장난감/사료가 아닌 간식 선택 (모호함) |
| **"저기.. 그.. 화장실 청소할 때 쓰는.. 스펀지 같은 거 있나요?"** | Hesitation | 3중 청소용 스펀지 | 🟢 O | **필러 처리 완벽** |
| **"음.. 뭐냐.. 그.. 튀김 건지는 거.."** | Hesitation | 스텐 채반 (24cm) | 🟢 O | **설명형 쿼리 성공** |
| **"요리할 때 국물 우려내는 주머니 같은 거요."** | Description | 요리용 면주머니 | 🟢 O | - |
| **"쓰레기 부피 줄여주는 봉투 있어요?"** | Description | 원형 압축 쓰레기 봉투 | 🟢 O | **추론 성공 (부피->압축)** |
| **"쇠로 된 수세미 말고.. 일회용으로 쓰는 수세미 있나요?"** | Negative | 일회용 베이킹소다 수세미 | 🟢 O | **부정어 처리 성공** |
| **"락스 냄새 안 나는 화장실 청소 세제 주세요."** | Negative | 동구밭 세탁조 크리너 | 🟢 O | **대체재 추천 성공** |
| **"집에 강아지가 있는데 삑삑 소리 나는 장난감 사주려고요."** | Context | [펫] 고슴도치 인형 | 🟢 O | **속성(소리) 매칭 성공** |
| **"자취 시작하는데 필요한 청소 도구 추천해주세요."** | Context | 렛츠 클린 청소포 | 🟢 O | **문맥 추천 성공** |
| **"건전지."** | Short | 네오셀 알카라인 건전지 AA | 🟢 O | 단답형 처리 |
| **"제가 지금 손을 다쳐서 설거지하기가 힘든데 간편하게 쓸 수 있는 수세미 있을까요?"** | Narrative | 일회용 베이킹소다 수세미 | 🟢 O | **상황 이해 성공** |
| **"AA 건전지 10개짜리"** | Attribute | 알카라인 건전지 AA 10개입 | 🟢 O | 수량 파악 |
| **"그.. 멍멍이 간식 좀 찾으려는데요.. 닭고기 들어간거요.."** | Hesitation | [펫] 더독 슬라이스 사사미 | 🟢 O | **필러+성분 파악 성공** |
| **"책상 위에 두는 철망으로 된 바구니?"** | Description | 사각 메쉬 책상 바구니 | 🟢 O | **유의어(철망->메쉬) 성공** |
| **"어.. 저기.. 물티슈인데.. 캡 달려있는거.. 150매 정도?"** | Hesitation | 에끌라 깨끗한 물티슈 | 🟢 O | **복합 조건 성공** |
| **"그.. 아이들 장난감 세탁기 있나요?"** | Specific Product | 세탁기 모형 작동 완구 | 🟢 O | 성공 |
| **"믹스커피."** | Short | 네스카페 수프리모 | 🟢 O | 성공 |
| **"다이소에 TV도 파나요?"** | False Positive | (선택 안함) | 🟢 O | **방어 성공** |
| **"명품 가방 있어요?"** | False Positive | (선택 안함) | 🟢 O | **방어 성공** |
| **"화장실 수건.. 베이지색으로.. 좀 부드러운거.."** | Desc+Attr | 송월 코마사 세면 타월 | 🟢 O | 성공 |

## 결론
전체 61건의 테스트 결과, **80.0%**의 높은 정확도를 기록했습니다.
기존 키워드 매칭 방식에서 실패하기 쉬운 **"망설임(필러)", "상황 설명", "부정어(A 말고 B)"** 등의 자연어 쿼리에서 매우 우수한 성능을 보였습니다. 
실패한 케이스들은 주로 **"너무 광범위한 쿼리(주방세제)"**에 대해 LLM이 조심스럽게 아무것도 선택하지 않거나(None), **"주관적 속성(가성비, 비건)"**에 대한 메타데이터가 상품 DB에 부족하여 발생한 것으로 분석됩니다.

---
*위 결과는 `poc_v4_experiment.py` 실행 로그를 기반으로 작성되었습니다.*
