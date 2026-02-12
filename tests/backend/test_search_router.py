"""Tests for search router"""
import sys
import os
from unittest.mock import patch, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_search_endpoint(client):
    """Should return search results"""
    from app.models.schemas import SearchResponse, ProductResult, MapInfo, QueryInfo

    mock_response = SearchResponse(
        results=[
            ProductResult(
                id=1, rank=1, name="대용량 물티슈", price=1000,
                image_url="/static/images/001.jpg",
                category_major="뷰티/위생", category_middle="화장지/물티슈",
                score=0.95,
            )
        ],
        map_info=MapInfo(section="뷰티/위생"),
        query_info=QueryInfo(original="물티슈", keywords=["물티슈"]),
    )

    with patch("app.routers.search.search_service") as mock_service:
        mock_service.search = AsyncMock(return_value=mock_response)
        response = client.post("/api/search", json={"query": "물티슈 어디있어요?"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "대용량 물티슈"
        assert data["query_info"]["original"] == "물티슈"


def test_search_empty_query(client):
    """Should handle empty query"""
    from app.models.schemas import SearchResponse, QueryInfo

    mock_response = SearchResponse(
        results=[],
        query_info=QueryInfo(original="", keywords=[]),
    )

    with patch("app.routers.search.search_service") as mock_service:
        mock_service.search = AsyncMock(return_value=mock_response)
        response = client.post("/api/search", json={"query": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []


def test_search_missing_query(client):
    """Should return 422 for missing query field"""
    response = client.post("/api/search", json={})
    assert response.status_code == 422
