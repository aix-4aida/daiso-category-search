"""Gemini service - intent classification, keyword extraction, and reranking via Google Gemini API"""
import json
import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

CLASSIFY_PROMPT = """당신은 다이소 매장 키오스크 입력 분류기입니다.
사용자의 입력이 "상품 위치 검색"인지 판별하세요.

사용자 입력: "{query}"

아래 JSON 형식으로만 응답하세요:
{{"intent": "product_search"}} 또는 {{"intent": "not_search"}}

"not_search" 판별 기준:
- 잡담/인사: "안녕하세요", "감사합니다", "집에 가고 싶다"
- 환불/교환 요청: "환불해주세요", "교환하고 싶어요"
- 재고/입고 문의: "이거 재고 있어요?", "언제 입고돼요?"
- 지시대명사만 사용 (구체적 상품명 없음): "이거 어딨어?", "저거 찾아줘", "그거 뭐야"

"product_search" 판별 기준:
- 구체적 상품명 또는 상품 종류 언급: "물티슈 어디있어요?", "우산", "건전지 찾아줘"
- 추상적이지만 상품을 가리키는 표현: "따뜻한 거 깔고 싶어", "머리 묶을 거"
"""

EXTRACT_PROMPT = """당신은 다이소 매장 상품 검색 도우미입니다.
사용자의 질문에서 다이소 상품 검색에 적합한 키워드를 추출하세요.

사용자 입력: "{query}"

반드시 아래 JSON 형식으로만 응답하세요:
{{"keywords": ["키워드1", "키워드2", "키워드3"]}}

규칙:
- keywords는 다이소 상품명에 매칭될 수 있는 구체적 단어 1~5개
- 추상적 표현을 구체적 상품명으로 변환 (예: "따뜻한 거 깔고 싶어" → ["매트", "방석", "카펫"])
- 구어체/사투리도 이해하여 표준어 키워드로 변환"""

RERANK_PROMPT = """당신은 다이소 매장 상품 검색 결과 정렬 도우미입니다.
사용자의 검색 의도에 가장 적합한 상품 3개를 선택하고, 적합도 순으로 정렬하세요.

사용자 질문: "{query}"
추출된 키워드: {keywords}

후보 상품 목록:
{candidates}

반드시 아래 JSON 형식으로만 응답하세요:
{{"selected_ids": [가장적합한ID, 두번째ID, 세번째ID]}}

규칙:
- 정확히 3개 선택 (후보가 3개 미만이면 있는 만큼만)
- 사용자 의도에 가장 부합하는 순서로 정렬
- 상품 ID(숫자)만 포함"""


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from Gemini response"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


class GeminiService:
    """Google Gemini API service for intent classification, keyword extraction, and reranking"""

    def __init__(self) -> None:
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def classify_intent(self, query: str) -> str:
        """Classify user query as 'product_search' or 'not_search'"""
        try:
            prompt = CLASSIFY_PROMPT.format(query=query)
            response = await self.model.generate_content_async(prompt)
            text = _strip_code_fences(response.text)
            result = json.loads(text)
            intent = result.get("intent", "product_search")
            logger.info(f"[INTENT] classify_intent: query='{query}' → intent='{intent}'")
            return intent
        except Exception as e:
            logger.error(f"Gemini classify_intent failed: {e}")
            # Fallback: assume product_search (better to search than miss)
            return "product_search"

    async def extract_keywords(self, query: str) -> list[str]:
        """Extract search keywords from user query"""
        try:
            prompt = EXTRACT_PROMPT.format(query=query)
            response = await self.model.generate_content_async(prompt)
            text = _strip_code_fences(response.text)
            result = json.loads(text)
            keywords = result.get("keywords", [query])
            logger.info(f"[KEYWORDS] extract_keywords: query='{query}' → keywords={keywords}")
            return keywords
        except Exception as e:
            logger.error(f"Gemini extract_keywords failed: {e}")
            return [query]

    async def rerank(
        self, query: str, keywords: list[str], candidates: list[dict]
    ) -> list[int]:
        """Rerank candidate products and return top 3 IDs"""
        if not candidates:
            return []

        try:
            candidates_text = "\n".join(
                f"- ID:{c['id']} | {c['name']} | {c.get('category_major', '')} > {c.get('category_middle', '')} | {c.get('price', 0)}원"
                for c in candidates
            )
            prompt = RERANK_PROMPT.format(
                query=query,
                keywords=json.dumps(keywords, ensure_ascii=False),
                candidates=candidates_text,
            )
            response = await self.model.generate_content_async(prompt)
            text = _strip_code_fences(response.text)
            result = json.loads(text)
            return result.get("selected_ids", [])
        except Exception as e:
            logger.error(f"Gemini reranking failed: {e}")
            # Fallback: return first 3 candidate IDs
            return [c["id"] for c in candidates[:3]]
