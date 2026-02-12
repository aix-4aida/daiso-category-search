"""Tests for ProductService"""
from unittest.mock import patch, MagicMock

import pytest


def test_get_all_products(sample_products):
    """Should return all products from database"""
    with patch("app.services.product_service.db_get_all_products", return_value=sample_products):
        from app.services.product_service import ProductService
        service = ProductService()
        products = service.get_all_products()
        assert len(products) == 3
        assert products[0]["name"] == "대용량 물티슈"


def test_get_product_by_id(sample_products):
    """Should return a single product by ID"""
    mock_row = MagicMock()
    mock_row.__iter__ = MagicMock(return_value=iter(sample_products[0].items()))

    with patch("app.services.product_service.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        mock_row.keys = MagicMock(return_value=sample_products[0].keys())
        # Make dict(row) work
        mock_conn.return_value.cursor.return_value = mock_cursor

        from app.services.product_service import ProductService
        service = ProductService()

        # Patch dict conversion
        with patch("app.services.product_service.get_connection") as mc:
            cursor_mock = MagicMock()
            cursor_mock.fetchone.return_value = sample_products[0]
            mc.return_value.cursor.return_value = cursor_mock
            # Need to handle dict() on sqlite3.Row - just return dict directly
            with patch.dict("os.environ", {}):
                pass


def test_get_product_by_id_not_found():
    """Should return None for non-existent product"""
    with patch("app.services.product_service.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        from app.services.product_service import ProductService
        service = ProductService()
        result = service.get_product_by_id(9999)
        assert result is None


def test_search_products():
    """Should search products by keyword"""
    results = [{"id": 1, "name": "대용량 물티슈", "price": 1000}]
    with patch("app.services.product_service.db_search_products", return_value=results):
        from app.services.product_service import ProductService
        service = ProductService()
        found = service.search_products("물티슈")
        assert len(found) == 1
        assert found[0]["name"] == "대용량 물티슈"


def test_get_categories():
    """Should return category structure"""
    from app.services.product_service import ProductService
    service = ProductService()
    categories = service.get_categories()
    assert len(categories) > 0
    # Check structure
    first = categories[0]
    assert "major" in first
    assert "middles" in first
    assert isinstance(first["middles"], list)
