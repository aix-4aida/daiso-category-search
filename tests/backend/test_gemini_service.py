"""Tests for GeminiService"""
import sys
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture
def gemini_service():
    """Create GeminiService with mocked genai"""
    with patch("app.services.gemini_service.genai"):
        with patch("app.services.gemini_service.settings") as mock_settings:
            mock_settings.GOOGLE_API_KEY = "test-key"
            from app.services.gemini_service import GeminiService
            service = GeminiService()
            return service


async def test_analyze_intent_basic(gemini_service):
    """Should extract keywords from a simple query"""
    mock_response = MagicMock()
    mock_response.text = '{"intent": "search", "keywords": ["물티슈"]}'
    gemini_service.model.generate_content_async = AsyncMock(return_value=mock_response)

    result = await gemini_service.analyze_intent("물티슈 어디있어요?")
    assert result["intent"] == "search"
    assert "물티슈" in result["keywords"]


async def test_analyze_intent_abstract_query(gemini_service):
    """Should convert abstract expressions to concrete keywords"""
    mock_response = MagicMock()
    mock_response.text = '{"intent": "search", "keywords": ["매트", "방석", "카펫"]}'
    gemini_service.model.generate_content_async = AsyncMock(return_value=mock_response)

    result = await gemini_service.analyze_intent("따뜻한 거 깔고 싶어")
    assert result["intent"] == "search"
    assert len(result["keywords"]) >= 1


async def test_analyze_intent_with_code_fences(gemini_service):
    """Should handle response wrapped in markdown code fences"""
    mock_response = MagicMock()
    mock_response.text = '```json\n{"intent": "search", "keywords": ["볼펜"]}\n```'
    gemini_service.model.generate_content_async = AsyncMock(return_value=mock_response)

    result = await gemini_service.analyze_intent("볼펜 찾아주세요")
    assert result["keywords"] == ["볼펜"]


async def test_analyze_intent_fallback_on_error(gemini_service):
    """Should fallback to original query on API error"""
    gemini_service.model.generate_content_async = AsyncMock(
        side_effect=Exception("API error")
    )

    result = await gemini_service.analyze_intent("테스트 쿼리")
    assert result["intent"] == "search"
    assert result["keywords"] == ["테스트 쿼리"]


async def test_rerank_basic(gemini_service):
    """Should return selected product IDs"""
    mock_response = MagicMock()
    mock_response.text = '{"selected_ids": [3, 1, 5]}'
    gemini_service.model.generate_content_async = AsyncMock(return_value=mock_response)

    candidates = [
        {"id": 1, "name": "물티슈", "category_major": "뷰티/위생", "price": 1000},
        {"id": 3, "name": "대형 물티슈", "category_major": "뷰티/위생", "price": 2000},
        {"id": 5, "name": "아기 물티슈", "category_major": "뷰티/위생", "price": 1500},
    ]

    result = await gemini_service.rerank("물티슈", ["물티슈"], candidates)
    assert result == [3, 1, 5]


async def test_rerank_empty_candidates(gemini_service):
    """Should return empty list for empty candidates"""
    result = await gemini_service.rerank("물티슈", ["물티슈"], [])
    assert result == []


async def test_rerank_fallback_on_error(gemini_service):
    """Should fallback to first 3 IDs on API error"""
    gemini_service.model.generate_content_async = AsyncMock(
        side_effect=Exception("API error")
    )

    candidates = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
        {"id": 4, "name": "D"},
    ]

    result = await gemini_service.rerank("test", ["test"], candidates)
    assert result == [1, 2, 3]
