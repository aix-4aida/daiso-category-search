"""Tests for products router"""
import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_products():
    return [
        {
            "id": 1, "rank": 1, "name": "대용량 물티슈", "price": 1000,
            "image_url": "https://example.com/1.jpg", "image_name": "001.jpg",
            "category_major": "뷰티/위생", "category_middle": "화장지/물티슈",
        },
        {
            "id": 2, "rank": 2, "name": "볼펜 세트", "price": 1000,
            "image_url": "https://example.com/2.jpg", "image_name": "002.jpg",
            "category_major": "문구/팬시", "category_middle": "필기구",
        },
    ]


def test_get_products(client, mock_products):
    """Should return paginated product list"""
    with patch("app.routers.products.service") as mock_service:
        mock_service.get_all_products.return_value = mock_products
        response = client.get("/api/products")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "대용량 물티슈"


def test_get_products_pagination(client, mock_products):
    """Should support skip and limit"""
    with patch("app.routers.products.service") as mock_service:
        mock_service.get_all_products.return_value = mock_products
        response = client.get("/api/products?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "볼펜 세트"


def test_get_product_by_id(client, mock_products):
    """Should return single product"""
    with patch("app.routers.products.service") as mock_service:
        mock_service.get_product_by_id.return_value = mock_products[0]
        response = client.get("/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "대용량 물티슈"


def test_get_product_not_found(client):
    """Should return 404 for missing product"""
    with patch("app.routers.products.service") as mock_service:
        mock_service.get_product_by_id.return_value = None
        response = client.get("/api/products/9999")
        assert response.status_code == 404


def test_get_categories(client):
    """Should return categories"""
    with patch("app.routers.products.service") as mock_service:
        mock_service.get_categories.return_value = [
            {"major": "뷰티/위생", "middles": ["스킨케어", "화장지/물티슈"]},
        ]
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["major"] == "뷰티/위생"
