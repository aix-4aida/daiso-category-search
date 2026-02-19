import os
import json
import time
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Re-use existing modules
from backend.services_kms.simple_keyword_extractor_gemini import extract_keyword
from backend.services_kms.run_all_pipeline import run_pipeline_for_voice

load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

class SearchManager:
    def __init__(self):
        self.model = None
        self._init_model()

    def _init_model(self):
        if not API_KEY:
            print("Warning: GOOGLE_API_KEY not found. SearchManager intent check will be disabled.")
            return

        try:
            genai.configure(api_key=API_KEY)
            # Use same config as poc_flash_test.py
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 5,
                },
                system_instruction="""
너는 다이소 매장의 태블릿에 탑재된 AI 점원이다.
사용자의 발화를 분석하여, 매장 직원의 응대가 필요한지(Y), 필요 없는지(N) 판단하여 알파벳 한 글자만 출력하라.

[판단 기준]
1. Y (응대 필요):
   - 다이소 상품 찾기, 재고 확인, 상품 추천 요청
   - 매장 시설(화장실, 엘리베이터, 주차장) 및 운영 시간 문의
   - 생활 속 문제 해결을 위한 상품 탐색 (예: "욕실이 미끄러워")
2. N (응대 불필요/무시):
   - 다이소와 무관한 사적인 잡담 (인사, 농담, MBTI, 연애 상담)
   - 외부 정보 질문 (날씨, 주식, 뉴스, 연예인)
   - 타 브랜드(맥도날드, 스타벅스) 관련 질문
   - 단순한 불만 토로, 욕설, 의미 없는 혼잣말

[Few-Shot 예시]
User: "건전지 어디 있어?" -> Model: Y
User: "화장실 비번 뭐야?" -> Model: N
User: "비트코인 얼마야?" -> Model: N
User: "사랑해" -> Model: N
"""
            )
        except Exception as e:
            print(f"Error initializing SearchManager model: {e}")

    async def check_intent(self, query: str) -> str:
        """
        Returns 'Y' (Valid), 'N' (Invalid), or 'ERROR'
        """
        if not self.model:
            return "Y" # Fail open if model issue
        
        try:
            # Run in executor to avoid blocking async loop since genai is sync
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(query))
            result = response.text.strip().upper()
            
            if 'Y' in result: return 'Y'
            if 'N' in result: return 'N'
            return result
        except Exception as e:
            print(f"Intent check error: {e}")
            return "ERROR"

    async def process_search(self, query: str, input_mode: str = "text", session_id: str = None):
        """
        Unified Search Pipeline
        Returns dict with status, results, message, suggestions
        """
        start_time = time.time()
        
        # 1. Intent Check
        intent = await self.check_intent(query)
        print(f"🧠 Intent Check: '{query}' -> {intent}")
        
        if intent == 'N':
            return {
                "status": "not_supported",
                "message": "죄송합니다. 다이소 상품이나 매장 이용과 관련된 질문만 답변드릴 수 있어요.",
                "suggestions": ["건전지 어디에 있어?", "욕실 슬리퍼 찾아줘" ],
                "query": query
            }

        # 2. Keyword Extraction (Reuse existing logic)
        # Note: extract_keyword is sync, run in executor if needed, but it might be fast enough or we can wrap it
        # For now, let's assume it's sync but fast-ish (Gemini call). Better to wrap.
        loop = asyncio.get_running_loop()
        keyword_result = await loop.run_in_executor(None, lambda: extract_keyword(query))
        
        keyword = keyword_result.get("keyword", "")
        if not keyword or "error" in keyword_result:
             print(f"⚠️ Keyword extraction failed or empty: {keyword_result.get('error')}")
             # If keyword extraction failed, we can either fail or try strictly searching the query
             # Requirement says: "need_clarify" if keyword is empty
             if not keyword:
                 return {
                     "status": "need_clarify",
                     "message": "죄송합니다, 찾으시는 상품을 조금 더 구체적으로 말씀해주시겠어요?",
                     "suggestions": ["AA 건전지", "욕실 미끄럼방지 스티커", "강아지 장난감"],
                     "query": query
                 }

        print(f"🔑 Extracted Keyword: {keyword}")

        # 3. Run Pipeline (Expansion -> Retrieval -> Rerank)
        # We reuse run_pipeline_for_voice. 
        # It expects audio_path, but for text search we provide valid dummy path or handle it.
        # It handles the full pipeline including logging to files (which is fine for now).
        
        # Create a dummy audio path string if text
        dummy_audio = f"outputs/text_search_{session_id or int(time.time())}.wav"
        
        # run_pipeline_for_voice is async
        pipeline_result = await run_pipeline_for_voice(dummy_audio, query, 0.0)
        
        # 4. Parse Results
        # The pipeline returns a dict with 'results', 'keyword', 'reranked', etc.
        # But wait, run_pipeline_for_voice's return structure in main.py was manually constructed 
        # from the return of run_pipeline_for_voice function? 
        # Let's check run_all_pipeline.py's return value again.
        # It returns `results` dict with keys: stt_text, audio_path, stt_time_seconds, 
        # keyword (maybe), final_results (maybe).
        
        final_list = []
        raw_results = pipeline_result.get("final_results", [])
        
        # Logic to extract product details (copied/adapted from main.py)
        if raw_results:
            first = raw_results[0]
            # Strategies to get IDs
            retrieved = first.get("retrieved_ids", []) or first.get("retrieved_results", [])
            selected = first.get("selected_id")
            
            # Prioritize selected
            ids_to_fetch = list(retrieved)
            if selected and selected in ids_to_fetch:
                ids_to_fetch.remove(selected)
                ids_to_fetch.insert(0, selected)
            elif selected:
                ids_to_fetch.insert(0, selected)
                
            # Limit to top 5
            ids_to_fetch = ids_to_fetch[:5]
            
            # Resolve Product IDs to DB objects
            from backend.database.database import get_product_by_id
            
            for item_str in ids_to_fetch:
                try:
                    # Parse "123 (Name)" format
                    if "(" in item_str:
                        pid = item_str.split("(")[0].strip()
                    else:
                        pid = item_str.strip()
                        
                    if pid.isdigit():
                        p = get_product_by_id(int(pid))
                        if p and p['id'] not in [x['id'] for x in final_list]:
                            final_list.append(p)
                except Exception as e:
                    print(f"Error fetching product {item_str}: {e}")

        # 5. Final Status Determination
        if not final_list:
            return {
                "status": "no_result",
                "message": "검색 결과가 없습니다. 다른 키워드로 검색해보시겠어요?",
                "suggestions": ["인기 상품 보기", "홈으로 가기"],
                "query": query,
                "keyword": keyword
            }
        
        return {
            "status": "ok",
            "results": final_list,
            "keyword": keyword,
            "reranked": raw_results, # Include raw for detail views if needed
            "query": query
        }

# Global Instance
search_manager = SearchManager()
