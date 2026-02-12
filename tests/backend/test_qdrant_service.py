"""Tests for QdrantService"""
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.services.qdrant_service import QdrantService, check_qdrant_health


@pytest.fixture
def qdrant_service():
    """Create QdrantService with mocked client"""
    service = QdrantService()
    return service


async def test_search_returns_results(qdrant_service):
    """Should return vector search results"""
    mock_client = AsyncMock()
    mock_point1 = MagicMock()
    mock_point1.id = 1
    mock_point1.score = 0.95
    mock_point1.payload = {"name": "대용량 물티슈", "category_major": "뷰티/위생", "price": 1000}

    mock_point2 = MagicMock()
    mock_point2.id = 2
    mock_point2.score = 0.88
    mock_point2.payload = {"name": "아기 물티슈", "category_major": "뷰티/위생", "price": 1500}

    mock_result = MagicMock()
    mock_result.points = [mock_point1, mock_point2]
    mock_client.query_points = AsyncMock(return_value=mock_result)
    qdrant_service.client = mock_client

    query_vector = [0.1] * 512
    results = await qdrant_service.search(query_vector)
    assert len(results) == 2
    assert results[0]["name"] == "대용량 물티슈"
    assert results[0]["score"] == 0.95


async def test_search_returns_empty_on_error(qdrant_service):
    """Should return empty list on error"""
    mock_client = AsyncMock()
    mock_client.query_points = AsyncMock(side_effect=Exception("Connection error"))
    qdrant_service.client = mock_client

    results = await qdrant_service.search([0.1] * 512)
    assert results == []


async def test_create_collection_when_not_exists(qdrant_service):
    """Should create collection if not exists"""
    mock_client = AsyncMock()
    mock_collections = MagicMock()
    mock_collections.collections = []
    mock_client.get_collections = AsyncMock(return_value=mock_collections)
    mock_client.create_collection = AsyncMock()
    qdrant_service.client = mock_client

    await qdrant_service.create_collection()
    mock_client.create_collection.assert_called_once()


async def test_create_collection_skip_when_exists(qdrant_service):
    """Should skip creation if collection already exists"""
    mock_client = AsyncMock()
    mock_col = MagicMock()
    mock_col.name = "daiso_products"
    mock_collections = MagicMock()
    mock_collections.collections = [mock_col]
    mock_client.get_collections = AsyncMock(return_value=mock_collections)
    qdrant_service.client = mock_client

    await qdrant_service.create_collection()
    mock_client.create_collection.assert_not_called()


async def test_check_qdrant_health_success():
    """Should return True when Qdrant is reachable"""
    with patch("app.services.qdrant_service._get_client") as mock_get:
        mock_client = AsyncMock()
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections = AsyncMock(return_value=mock_collections)
        mock_get.return_value = mock_client

        result = await check_qdrant_health()
        assert result is True


async def test_check_qdrant_health_failure():
    """Should return False when Qdrant is unreachable"""
    with patch("app.services.qdrant_service._get_client") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = await check_qdrant_health()
        assert result is False
