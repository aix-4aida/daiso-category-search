
import os
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from backend.core.config import config
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.0-flash"

generation_config = {
    "temperature": 0.0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 5,
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

SYSTEM_PROMPT = """
너는 다이소 매장의 태블릿에 탑재된 AI 점원이다.
사용자의 발화를 분석하여, 매장 직원의 응대가 필요한지(Y), 필요 없는지(N) 판단하여 알파벳 한 글자만 출력하라.

[판단 기준]
1. Y (응대 필요):
   - 다이소 상품 찾기, 재고 확인, 상품 추천 요청
   - 매장 시설(화장실, 엘리베이터, 주차장) 및 운영 시간 문의
   - 결제, 영수증 재발급, 봉투 구매, 멤버십 포인트 적립 문의
   - 생활 속 문제 해결을 위한 상품 탐색 (예: "욕실이 미끄러워")

2. N (응대 불필요/무시):
   - 다이소와 무관한 사적인 잡담 (인사, 농담, MBTI, 연애 상담)
   - 외부 정보 질문 (날씨, 주식, 비트코인, 뉴스, 연예인)
   - 타 브랜드(맥도날드, 스타벅스, 편의점) 관련 질문
   - 단순한 불만 토로, 욕설, 의미 없는 혼잣말

[Few-Shot 예시]
User: "건전지 어디 있어?" -> Model: Y
User: "포인트 적립 되나요?" -> Model: Y
User: "화장실 비번 뭐야?" -> Model: Y
User: "비트코인 얼마야?" -> Model: N
User: "맥도날드 가격 알려줘" -> Model: N
User: "나랑 결혼할래?" -> Model: N
User: "사랑해" -> Model: N
"""

# Initialize model lazily or at module level
try:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    print(f"Error initializing Intent Model: {e}")
    model = None

def check_intent(utterance: str) -> dict:
    """
    Check if the user utterance requires a response (Y/N).
    Returns dict with 'is_valid' (Y/N/ERROR) and 'latency_ms'.
    """
    if not utterance:
        return {"is_valid": "N", "latency_ms": 0}
        
    start_time = time.time()
    prediction = "ERROR"

    try:
        if model:
            response = model.generate_content(utterance, safety_settings=safety_settings)
            raw_text = response.text.strip().upper()

            if 'Y' in raw_text:
                prediction = 'Y'
            elif 'N' in raw_text:
                prediction = 'N'
            else:
                prediction = raw_text # Fallback or specific code
        else:
            prediction = "ERROR_MODEL_INIT"

    except Exception as e:
        print(f"Intent Check Error: {e}")
        prediction = "ERROR"

    duration_ms = int((time.time() - start_time) * 1000)
    
    return {
        "is_valid": prediction,
        "latency_ms": duration_ms
    }
