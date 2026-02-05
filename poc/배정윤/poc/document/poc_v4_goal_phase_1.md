**"검색된 후보군들 중에서 LLM이 어떻게 진짜 정답을 골라내고(Re-ranking), 고객에게 안내할 데이터(좌표/멘트)를 생성하는지"**에 대한 **백엔드 로직(지능)**을 검증

Re-ranking부터 시작하는 PoC를 위한 구체적인 실행 가이드와 코드를 정리

🎯 PoC 검증 목표
Input: (가상으로 검색된) 5~10개의 혼잡한 상품 후보 리스트.

Process (Re-ranking): LLM이 사용자 질문의 맥락("튀김 건질 때...")을 이해하고, 후보 중 가장 적합한 1개를 선택.

Output: 키오스크와 모바일이 바로 사용할 수 있는 구조화된 JSON 데이터 생성.


🛠️ 구현 가이드 (Python + Gemini API)
이 PoC는 Python 스크립트 하나로 검증 가능합니다.

1단계: Mock Input 데이터 준비 (검색 엔진 흉내)
검색 엔진(Elasticsearch/Vector DB)이 리턴했다고 가정한 "노이즈가 섞인" 데이터셋입니다.

상황: 사용자가 "기름 튀김 건져내는 망 있어?" 라고 물어봄.

후보군: (1) 채반(정답), (2) 세탁망(오답-망), (3) 튀김가루(오답-튀김), (4) 국자(유사-도구).


Python:

# mock_search_results.py

user_query = "기름 튀김 건져내는 망 어디 있어?"

# 검색 엔진이 뱉어낸 후보들 (Top-5)
candidates = [
    {
        "id": "A001",
        "name": "원형 세탁망 (중)",
        "desc": "세탁기 사용 시 옷감 보호를 위한 망",
        "location": {"zone": "Laundry", "x": 50, "y": 90}
    },
    {
        "id": "B002",
        "name": "튀김가루 1kg",
        "desc": "바삭한 튀김 요리를 위한 필수 재료",
        "location": {"zone": "Food", "x": 120, "y": 30}
    },
    {
        "id": "C003",
        "name": "스텐 건지기 (채반)",
        "desc": "국수나 튀김 요리 시 건더기를 건져낼 때 사용",
        "location": {"zone": "Kitchen_A", "x": 200, "y": 450}
    },
    {
        "id": "D004",
        "name": "플라스틱 바구니",
        "desc": "다용도 수납 바구니",
        "location": {"zone": "Storage", "x": 10, "y": 10}
    },
    {
        "id": "E005",
        "name": "스텐 국자",
        "desc": "국을 뜰 때 사용하는 조리 도구",
        "location": {"zone": "Kitchen_B", "x": 210, "y": 460}
    }
]



2단계: Re-ranking 프롬프트 설계 (핵심)
단순히 "골라줘"가 아니라, **Chain of Thought(생각의 사슬)**를 유도하여 정확도를 높이고, 출력은 반드시 JSON으로 받아야 합니다.

Python:

# rerank_logic.py
import google.generativeai as genai
import json

# Gemini API 설정 (API Key 필요)
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-1.5-pro')

def rerank_and_respond(query, candidates_list):
    prompt = f"""
    당신은 다이소 매장의 똑똑한 점원 AI입니다.
    
    [사용자 질문]
    "{query}"

    [검색된 상품 후보 리스트]
    {json.dumps(candidates_list, ensure_ascii=False)}

    [임무]
    1. 사용자 질문의 의도를 파악하고, 후보 리스트 중에서 가장 적합한 상품 **단 하나(Top-1)**를 선택하세요.
    2. 선택한 이유(reasoning)를 한 문장으로 설명하세요.
    3. 선택한 상품의 위치 정보를 바탕으로 고객에게 할 안내 멘트(tts_text)를 작성하세요.
    4. 만약 적합한 상품이 없다면 null을 반환하세요.

    [출력 형식 (JSON Only)]
    {{
        "selected_product_id": "string",
        "product_name": "string",
        "reasoning": "string",
        "location_info": {{ "zone": "string", "x": int, "y": int }},
        "tts_text": "string (고객에게 말하듯 자연스럽게)"
    }}
    """

    response = model.generate_content(prompt)
    
    # JSON 파싱 (Gemini가 마크다운 ```json ... ``` 을 붙일 경우 제거)
    text_res = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text_res)

# 실행
result = rerank_and_respond(user_query, candidates)
print(json.dumps(result, indent=2, ensure_ascii=False))



3단계: 예상 결과 (Output 검증)
위 코드를 실행했을 때 아래와 같이 나온다면 PoC 성공입니다.

json:
{
  "selected_product_id": "C003",
  "product_name": "스텐 건지기 (채반)",
  "reasoning": "사용자가 '튀김 건져내는 망'을 찾고 있으며, 이는 '스텐 건지기'의 설명과 기능적으로 가장 일치함. 세탁망은 용도가 다름.",
  "location_info": {
    "zone": "Kitchen_A",
    "x": 200,
    "y": 450
  },
  "tts_text": "네, 찾으시는 튀김 건지기용 채반은 주방 코너 A구역에 있습니다. 화면의 지도를 확인해 주세요."
}

📊 이 PoC에서 검증해야 할 체크리스트Re-ranking 단계만 집중해서 테스트할 때, 다음 시나리오들을 넣어보고 AI가 잘 대처하는지 확인해야 합니다.의도 매칭 능력:질문: "그.. 구멍 뚫린 바구니" $\rightarrow$ 선택: "플라스틱 바구니" vs "채반" (상황에 따라 다름, AI의 판단력 확인)함정 피하기 (Negative Test):질문: "아이폰 충전기"후보군: [세탁망, 국자, 튀김가루] (관련 없음)기대 결과: AI가 억지로 국자를 고르지 않고, "selected_product_id": null 혹은 "죄송합니다, 관련 상품이 목록에 없습니다."를 출력하는지 확인.데이터 정제 능력:검색 엔진에서 넘어온 좌표 데이터(x: 200, y: 450)가 깨지지 않고 최종 JSON까지 잘 전달되는지.

✅ 1. 포맷 검증 (Format Consistency)
동작(Operation): "넣으면 JSON이 튀어나온다." (기본)

"키오스크가 에러 없이 파싱할 수 있는가?"

LLM이 JSON 형식을 깨뜨리거나, 이상한 텍스트(예: "Here is the JSON...")를 섞어서 주면 키오스크 앱이 뻗어버립니다.

성공 기준: 100번 요청했을 때 100번 모두 완벽한 JSON 구조로 응답해야 함.


✅ 2. 논리 검증 (Reasoning Accuracy) - 여기가 핵심
지능(Intelligence): "10개 질문 중 8개 이상은 정확한 상품을 골라낸다." (목표)

"사용자 의도에 맞는 상품 ID를 골랐는가?"

Input: "튀김 건지는 거"

Candidates: [세탁망(A), 뜰채(B), 국자(C)]

LLM Output:

Case 1 (성공): {"selected_id": "B", ...} -> OK

Case 2 (실패): {"selected_id": "A", "reason": "망이라고 하셔서 세탁망을 골랐습니다."} -> Fail (JSON은 맞지만 로직이 틀림)


📊 PoC 평가표 예시 (이렇게 만드세요)
단순히 "된다/안된다"가 아니라, 엑셀에 아래처럼 10개 정도만 테스트 케이스를 만들어 돌려보세요. 이게 바로 정량적 평가입니다.
테스트 질문 (Query),후보군 (Candidates),LLM이 선택한 답,정답 여부 (O/X),비고
"""튀김 건지는 망""","[세탁망, 뜰채, 국자]",뜰채,🟢 O,정확함
"""아이폰 충전 선""","[건전지, 8핀 케이블, 멀티탭]",건전지,🔴 X,할루시네이션 발생
"""그.. 구멍 뚫린 바구니""","[채반, 냄비, 도마]",채반,🟢 O,추상적 표현 이해함
"""화장실 어디야?""","[채반, 냄비, 도마]",null,🟢 O,상품 아님 처리 성공

80점(8/10) 넘으면 다음 단계(키오스크 연동)로 넘어갈 것.