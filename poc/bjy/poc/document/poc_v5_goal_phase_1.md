# PoC v5 목표: 지능형 검색 고도화 (Accuracy > 90%)

Phase 1에서 확인된 가능성을 바탕으로, **프롬프트 엔지니어링(Few-Shot + CoT)**을 강화하여 상용 수준의 정확도를 달성하는 것이 목표입니다.

## Plan: 프롬프트 엔지니어링 강화

1. **Few-Shot Prompting (예제 학습)**: LLM에게 "이럴 땐 이걸 고르는 거야"라고 정답 예시 3개를 미리 보여줍니다.
2. **CoT (Chain of Thought, 생각의 사슬)**: 바로 ID를 뱉지 말고, "왜 이게 정답이고 나머지는 오답인지" 먼저 분석하게 강제합니다.
3. **Negative Filtering (오답 방어)**: 후보군에 정답이 없으면 억지로 고르지 않고 null을 반환하는 능력을 강화합니다.

## 💻 고도화된 코드 구조 (poc_v5_reranker.py)
이 코드는 Few-Shot 예제가 포함되어 있고, **이유(Reasoning)**를 먼저 생성한 뒤 결론을 내리도록 설계되었습니다.

```python
import google.generativeai as genai
import json

# API Key 설정
# genai.configure(api_key="YOUR_API_KEY")

# 다이소 데이터 처리에 특화된 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 다이소 매장의 노련한 점원 AI입니다. 사용자의 모호한 질문을 이해하고, 검색된 상품 목록(Candidates) 중에서 가장 적합한 상품을 골라야 합니다.

[원칙]
1. 사용자의 의도(Intent)를 최우선으로 고려하세요. (예: '망'이라고 했지만 '튀김' 문맥이면 '세탁망'은 오답입니다.)
2. 상품명뿐만 아니라 '설명(desc)'과 '카테고리'를 꼼꼼히 비교하세요.
3. 후보군 중 적합한 게 없다면 과감하게 null을 반환하세요.
4. 출력은 반드시 JSON 포맷이어야 합니다.

[Few-Shot 예시]
Q: "튀김 건질 때 쓰는 거"
Candidates: [{"id":"A1", "name":"세탁망"}, {"id":"B2", "name":"스텐 채반(손잡이형)"}, {"id":"C3", "name":"튀김가루"}]
Reasoning: 사용자는 조리 도구를 찾고 있음. '세탁망'은 형태는 비슷하나 용도가 다르고, '튀김가루'는 재료임. '스텐 채반'이 튀김 건지기에 적합함.
Output: {"selected_id": "B2", "confidence": "high", "message": "튀김 건지기 용으로는 이 스텐 채반이 딱입니다."}

Q: "아이폰 충전기"
Candidates: [{"id":"D4", "name":"건전지 AA"}, {"id":"E5", "name":"C타입 케이블"}, {"id":"F6", "name":"멀티탭"}]
Reasoning: 아이폰은 8핀(라이트닝) 혹은 C타입임. 하지만 'C타입 케이블'은 아이폰 15 이상에만 해당됨. 사용자가 구체적이지 않으므로 가장 근접한 케이블을 추천하되 확신도는 낮춤.
Output: {"selected_id": "E5", "confidence": "medium", "message": "아이폰 15 이상이시면 이 C타입 케이블을 쓰시면 됩니다."}

Q: "강아지 밥그릇"
Candidates: [{"id":"G7", "name":"사람용 국그릇"}, {"id":"H8", "name":"유리컵"}]
Reasoning: '국그릇'을 대용할 순 있지만, 반려동물 전용 상품이 후보에 없음. 억지로 추천하기보다 없음을 알리는 게 나음.
Output: {"selected_id": null, "confidence": "high", "message": "죄송합니다. 현재 반려동물 용품이 검색되지 않네요."}
"""
```

## 🧪 Accuracy 90% 검증을 위한 'Golden Dataset' (poc_v5_golden_test_cases.json)
"잘 되네" 느낌만으로는 90%를 보장할 수 없습니다. **50개의 고난도 테스트셋**을 구축하여 정량적으로 검증합니다.

### 함정 문제 유형 (4가지)
1. **유형 1: 동음이의어 & 유사어 (Synonyms)**
   - Q: "배터리" -> A: "건전지" (보조배터리 X)
2. **유형 2: 용도 중심 설명 (Intent-based)**
   - Q: "여행 갈 때 샴푸 담는 통" -> A: "리필 용기" (샴푸 본품 X)
3. **유형 3: 시각적 묘사 (Visual Description)**
   - Q: "그.. 뽁뽁이" -> A: "에어캡 단열시트" (장난감 X)
4. **유형 4: 함정 카드 (Distractors)**
   - Q: "갤럭시 충전기" -> Candidates: [아이폰 케이블, 건전지] -> A: `null`

## 📊 자동 채점 스크립트 (poc_v5_eval.py)
50개를 일일이 눈으로 보지 않고 자동으로 채점하여 정확도를 산출합니다.
- **PASS 기준**: 90% 이상 (45/50개 성공)
- **실패 시**: 오답 노트를 분석하여 SYSTEM_PROMPT의 [Few-Shot 예시]에 추가하고 재도전.
