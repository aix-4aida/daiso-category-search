"""Gemini service - intent analysis and reranking via Google Gemini API"""
import json
import logging

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

INTENT_PROMPT = """당신은 다이소 매장 상품 검색 도우미입니다.
사용자의 질문에서 검색 의도를 파악하고, 다이소에서 판매하는 상품 검색에 적합한 키워드를 추출하세요.

사용자 입력: "{query}"

반드시 아래 JSON 형식으로만 응답하세요:
{{"intent": "search", "keywords": ["키워드1", "키워드2", "키워드3"]}}

규칙:
- intent는 항상 "search"
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


class GeminiService:
    """Google Gemini API service for intent analysis and reranking"""

    def __init__(self) -> None:
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def analyze_intent(self, query: str) -> dict:
        """Analyze user query intent and extract search keywords"""
        try:
            prompt = INTENT_PROMPT.format(query=query)
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini intent analysis failed: {e}")
            # Fallback: use original query as keyword
            return {"intent": "search", "keywords": [query]}

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
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            result = json.loads(text)
            return result.get("selected_ids", [])
        except Exception as e:
            logger.error(f"Gemini reranking failed: {e}")
            # Fallback: return first 3 candidate IDs
            return [c["id"] for c in candidates[:3]]
