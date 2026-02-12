"""Pytest fixtures for backend tests"""
import sys
import os
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

# Add backend to path so 'app' and 'database' modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture
def test_client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_products():
    """Sample product data for testing"""
    return [
        {
            "id": 1,
            "rank": 1,
            "name": "대용량 물티슈",
            "price": 1000,
            "image_url": "https://example.com/1.jpg",
            "image_name": "001_대용량 물티슈.jpg",
            "image_path": "images/001_대용량 물티슈.jpg",
            "category_major": "뷰티/위생",
            "category_middle": "화장지/물티슈",
        },
        {
            "id": 2,
            "rank": 2,
            "name": "플라스틱 수납함",
            "price": 3000,
            "image_url": "https://example.com/2.jpg",
            "image_name": "002_플라스틱 수납함.jpg",
            "image_path": "images/002_플라스틱 수납함.jpg",
            "category_major": "수납/정리",
            "category_middle": "수납함",
        },
        {
            "id": 3,
            "rank": 3,
            "name": "볼펜 세트",
            "price": 1000,
            "image_url": "https://example.com/3.jpg",
            "image_name": "003_볼펜 세트.jpg",
            "image_path": "images/003_볼펜 세트.jpg",
            "category_major": "문구/팬시",
            "category_middle": "필기구",
        },
    ]


@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service"""
    mock = MagicMock()
    mock.analyze_intent = AsyncMock(
        return_value={"intent": "search", "keywords": ["물티슈"]}
    )
    mock.rerank = AsyncMock(return_value=[0, 1, 2])
    return mock


@pytest.fixture
def mock_es_service():
    """Mock Elasticsearch service"""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_qdrant_service():
    """Mock Qdrant service"""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])
    return mock
