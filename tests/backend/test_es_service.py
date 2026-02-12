"""Tests for ESService"""
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.services.es_service import ESService, check_es_health


@pytest.fixture
def es_service():
    """Create ESService with mocked client"""
    service = ESService()
    return service


async def test_search_returns_results(es_service):
    """Should return search results from ES"""
    mock_client = MagicMock()
    mock_client.search = MagicMock(
        return_value={
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "id": 1,
                            "name": "대용량 물티슈",
                            "category_major": "뷰티/위생",
                            "category_middle": "화장지/물티슈",
                            "price": 1000,
                        },
                        "_score": 5.5,
                    },
                    {
                        "_source": {
                            "id": 2,
                            "name": "아기 물티슈",
                            "category_major": "뷰티/위생",
                            "category_middle": "화장지/물티슈",
                            "price": 1500,
                        },
                        "_score": 4.2,
                    },
                ]
            }
        }
    )
    es_service.client = mock_client

    results = await es_service.search(["물티슈"])
    assert len(results) == 2
    assert results[0]["name"] == "대용량 물티슈"
    assert results[0]["score"] == 5.5


async def test_search_returns_empty_on_no_hits(es_service):
    """Should return empty list when no hits"""
    mock_client = MagicMock()
    mock_client.search = MagicMock(
        return_value={"hits": {"hits": []}}
    )
    es_service.client = mock_client

    results = await es_service.search(["존재하지않는상품"])
    assert results == []


async def test_search_handles_error(es_service):
    """Should return empty list on error"""
    mock_client = MagicMock()
    mock_client.search = MagicMock(side_effect=Exception("Connection error"))
    es_service.client = mock_client

    results = await es_service.search(["물티슈"])
    assert results == []


async def test_create_index(es_service):
    """Should create index if not exists"""
    mock_client = MagicMock()
    mock_client.indices = MagicMock()
    mock_client.indices.exists = MagicMock(return_value=False)
    mock_client.indices.create = MagicMock()
    es_service.client = mock_client

    await es_service.create_index()
    mock_client.indices.create.assert_called_once()


async def test_bulk_index(es_service):
    """Should bulk index products"""
    mock_client = MagicMock()
    mock_client.bulk = MagicMock()
    es_service.client = mock_client

    products = [
        {"id": 1, "name": "물티슈", "category_major": "뷰티/위생", "category_middle": "화장지/물티슈", "price": 1000},
        {"id": 2, "name": "볼펜", "category_major": "문구/팬시", "category_middle": "필기구", "price": 1000},
    ]
    count = await es_service.bulk_index(products)
    assert count == 2
    mock_client.bulk.assert_called_once()


async def test_check_es_health_success():
    """Should return True when ES is reachable"""
    with patch("app.services.es_service._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.ping = MagicMock(return_value=True)
        mock_get.return_value = mock_client

        result = await check_es_health()
        assert result is True


async def test_check_es_health_failure():
    """Should return False when ES is unreachable"""
    with patch("app.services.es_service._get_client") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = await check_es_health()
        assert result is False
