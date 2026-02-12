"""Tests for health router"""
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


def test_health_check(client):
    """Should return health status"""
    with patch("app.services.es_service.check_es_health", return_value=True), \
         patch("app.services.qdrant_service.check_qdrant_health", return_value=True), \
         patch("database.database.get_product_count", return_value=100):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["services"]["database"] is True
        assert data["services"]["elasticsearch"] is True
        assert data["services"]["qdrant"] is True


def test_health_check_degraded(client):
    """Should return degraded status when DB is down"""
    with patch("app.services.es_service.check_es_health", return_value=False), \
         patch("app.services.qdrant_service.check_qdrant_health", return_value=False), \
         patch("database.database.get_product_count", side_effect=Exception("DB error")):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] is False
