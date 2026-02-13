"""Tests for SearchService - hybrid search orchestration"""
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture
def search_service():
    """Create SearchService with all dependencies mocked"""
    with patch("app.services.search_service.GeminiService") as MockGemini, \
         patch("app.services.search_service.ESService") as MockES, \
         patch("app.services.search_service.QdrantService") as MockQdrant, \
         patch("app.services.search_service.ProductService") as MockProduct:

        from app.services.search_service import SearchService
        service = SearchService()

        # Setup default mocks for 2-step intent pipeline
        service.gemini.classify_intent = AsyncMock(return_value="product_search")
        service.gemini.extract_keywords = AsyncMock(return_value=["물티슈"])
        service.gemini.rerank = AsyncMock(return_value=[1, 2, 3])

        service.es.search = AsyncMock(return_value=[
            {"id": 1, "name": "대용량 물티슈", "price": 1000, "category_major": "뷰티/위생",
             "category_middle": "화장지/물티슈", "image_name": "001_대용량 물티슈.jpg", "score": 5.0},
            {"id": 2, "name": "아기 물티슈", "price": 1500, "category_major": "뷰티/위생",
             "category_middle": "화장지/물티슈", "image_name": "002_아기 물티슈.jpg", "score": 4.0},
        ])

        service.qdrant.search = AsyncMock(return_value=[
            {"id": 1, "name": "대용량 물티슈", "price": 1000, "category_major": "뷰티/위생",
             "category_middle": "화장지/물티슈", "image_name": "001_대용량 물티슈.jpg", "score": 0.95},
            {"id": 3, "name": "물티슈 캡", "price": 1000, "category_major": "뷰티/위생",
             "category_middle": "화장지/물티슈", "image_name": "003_물티슈 캡.jpg", "score": 0.88},
        ])

        service.product_service.search_products = MagicMock(return_value=[])

        return service


async def test_search_full_pipeline(search_service):
    """Should execute the full search pipeline and return results"""
    search_service._search_qdrant = AsyncMock(return_value=[
        {"id": 1, "name": "대용량 물티슈", "price": 1000, "category_major": "뷰티/위생",
         "category_middle": "화장지/물티슈", "image_name": "001_대용량 물티슈.jpg", "score": 0.95},
        {"id": 3, "name": "물티슈 캡", "price": 1000, "category_major": "뷰티/위생",
         "category_middle": "화장지/물티슈", "image_name": "003_물티슈 캡.jpg", "score": 0.88},
    ])

    result = await search_service.search("물티슈 어디있어요?")

    assert result.query_info.original == "물티슈 어디있어요?"
    assert result.query_info.keywords == ["물티슈"]
    assert len(result.results) <= 3
    search_service.gemini.classify_intent.assert_called_once_with("물티슈 어디있어요?")
    search_service.gemini.extract_keywords.assert_called_once_with("물티슈 어디있어요?")


async def test_search_not_search_intent(search_service):
    """Should return early with message for non-search queries"""
    search_service.gemini.classify_intent = AsyncMock(return_value="not_search")

    result = await search_service.search("안녕하세요")

    assert result.results == []
    assert result.query_info.intent == "not_search"
    assert result.message is not None
    assert "상품" in result.message
    # Should NOT call extract_keywords or search
    search_service.gemini.extract_keywords.assert_not_called()


async def test_search_returns_map_info(search_service):
    """Should include map info in response"""
    search_service._search_qdrant = AsyncMock(return_value=[])

    result = await search_service.search("물티슈")
    if result.results:
        assert result.map_info is not None
        assert result.map_info.section != ""


async def test_map_info_includes_navigation_data(search_service):
    """Should include waypoints, destination, and counter in map info"""
    search_service._search_qdrant = AsyncMock(return_value=[])

    result = await search_service.search("물티슈")
    if result.results:
        mi = result.map_info
        assert mi is not None
        assert mi.counter_number is not None
        assert mi.destination is not None
        assert mi.start is not None
        assert len(mi.waypoints) >= 3
        assert mi.section_description != ""


async def test_product_result_includes_location_data(search_service):
    """Each product result should include location fields"""
    search_service._search_qdrant = AsyncMock(return_value=[])

    result = await search_service.search("물티슈")
    if result.results:
        p = result.results[0]
        assert p.counter_number is not None
        assert p.destination_x is not None
        assert p.destination_y is not None
        assert p.location_floor is not None
        assert p.location_description is not None


async def test_rrf_fusion(search_service):
    """Should merge ES and Qdrant results via RRF"""
    es_results = [
        {"id": 1, "name": "A", "score": 5.0},
        {"id": 2, "name": "B", "score": 4.0},
    ]
    qdrant_results = [
        {"id": 2, "name": "B", "score": 0.9},
        {"id": 3, "name": "C", "score": 0.8},
    ]

    fused = search_service._fuse_results(es_results, qdrant_results)

    # ID 2 should have highest RRF score (appears in both)
    assert fused[0]["id"] == 2
    assert len(fused) == 3


async def test_order_by_ids(search_service):
    """Should reorder candidates by selected IDs"""
    candidates = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
    ]

    result = search_service._order_by_ids(candidates, [3, 1, 2])
    assert result[0]["id"] == 3
    assert result[1]["id"] == 1
    assert result[2]["id"] == 2


async def test_fallback_search_when_no_results(search_service):
    """Should fallback to SQLite search when ES/Qdrant return nothing"""
    search_service.gemini.classify_intent = AsyncMock(return_value="product_search")
    search_service.gemini.extract_keywords = AsyncMock(return_value=["볼펜"])
    search_service._search_es = AsyncMock(return_value=[])
    search_service._search_qdrant = AsyncMock(return_value=[])
    search_service.product_service.search_products = MagicMock(return_value=[
        {"id": 10, "name": "볼펜 세트", "price": 1000, "image_name": "010_볼펜 세트.jpg",
         "category_major": "문구/팬시", "category_middle": "필기구"},
    ])

    result = await search_service.search("볼펜 찾아주세요")
    assert len(result.results) >= 1
    assert result.results[0].name == "볼펜 세트"
