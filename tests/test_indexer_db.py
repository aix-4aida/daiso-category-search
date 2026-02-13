"""
Tests for read_products_db() and index_catalog(source="db").

TDD Red: These tests must FAIL before implementation.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

import pytest


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_db(tmp_path):
    """Create a minimal products.db with known data."""
    db_path = str(tmp_path / "products.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            name TEXT NOT NULL,
            price INTEGER,
            image_url TEXT,
            image_name TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category_major TEXT,
            category_middle TEXT,
            UNIQUE(name)
        )
    """)
    cur.executemany(
        "INSERT INTO products (id, rank, name, price, category_major, category_middle) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, 1, "메디필 멜라논엑스 기미크림 30 ml", 5000, "뷰티/위생", "스킨케어"),
            (2, 2, "템포롤화장지(24 m)", 500, "뷰티/위생", "화장지/물티슈"),
            (3, 3, "동구밭 더 간편한 세탁조 크리너 10개입", 1000, "청소/욕실", "세탁용품"),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def empty_db(tmp_path):
    """Create an empty products table."""
    db_path = str(tmp_path / "empty.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            category_major TEXT, category_middle TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestReadProductsDb:
    """read_products_db() should return (rows, headers) like read_catalog()."""

    def test_returns_tuple_of_rows_and_headers(self, sample_db):
        from backend.search.indexer import read_products_db

        rows, headers = read_products_db(sample_db)
        assert isinstance(rows, list)
        assert isinstance(headers, list)

    def test_headers_contain_required_columns(self, sample_db):
        from backend.search.indexer import read_products_db

        rows, headers = read_products_db(sample_db)
        for col in ("doc_id", "title", "text", "category"):
            assert col in headers, f"Missing required column: {col}"

    def test_row_count_matches_db(self, sample_db):
        from backend.search.indexer import read_products_db

        rows, headers = read_products_db(sample_db)
        assert len(rows) == 3

    def test_doc_id_format(self, sample_db):
        """doc_id should be P-{id} to match catalog convention."""
        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(sample_db)
        doc_ids = [r["doc_id"] for r in rows]
        assert doc_ids == ["P-1", "P-2", "P-3"]

    def test_title_is_product_name(self, sample_db):
        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(sample_db)
        assert rows[0]["title"] == "메디필 멜라논엑스 기미크림 30 ml"

    def test_text_is_product_name(self, sample_db):
        """text field = name (products.db has no separate description)."""
        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(sample_db)
        assert rows[0]["text"] == "메디필 멜라논엑스 기미크림 30 ml"

    def test_category_combines_major_and_middle(self, sample_db):
        """category = 'category_major > category_middle'."""
        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(sample_db)
        assert rows[0]["category"] == "뷰티/위생 > 스킨케어"
        assert rows[2]["category"] == "청소/욕실 > 세탁용품"

    def test_empty_db_returns_empty_list(self, empty_db):
        from backend.search.indexer import read_products_db

        rows, headers = read_products_db(empty_db)
        assert rows == []
        assert "doc_id" in headers

    def test_missing_file_raises(self):
        from backend.search.indexer import read_products_db

        with pytest.raises(FileNotFoundError):
            read_products_db("/nonexistent/path.db")

    def test_rows_are_dicts(self, sample_db):
        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(sample_db)
        assert all(isinstance(r, dict) for r in rows)

    def test_null_category_fallback(self, tmp_path):
        """If category_major/middle is NULL, category should be empty string."""
        db_path = str(tmp_path / "null_cat.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                category_major TEXT, category_middle TEXT
            )
        """)
        cur.execute("INSERT INTO products (id, name) VALUES (1, '테스트 상품')")
        conn.commit()
        conn.close()

        from backend.search.indexer import read_products_db

        rows, _ = read_products_db(db_path)
        assert rows[0]["category"] == ""


# ---------------------------------------------------------------------------
# Image & Price mapping tests
# ---------------------------------------------------------------------------

class TestImageAndPriceMapping:
    """read_products_db() should include image_url and price in rows."""

    @pytest.fixture
    def db_with_images(self, tmp_path):
        """Create products.db with image and price data."""
        db_path = str(tmp_path / "img_products.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank INTEGER,
                name TEXT NOT NULL,
                price INTEGER,
                image_url TEXT,
                image_name TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category_major TEXT,
                category_middle TEXT,
                UNIQUE(name)
            )
        """)
        cur.executemany(
            "INSERT INTO products (id, rank, name, price, image_url, image_name, category_major, category_middle) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 1, "메디필 멜라논엑스 기미크림 30 ml", 5000,
                 "https://cdn.daisomall.co.kr/images/prod1.jpg", "001_메디필.jpg",
                 "뷰티/위생", "스킨케어"),
                (2, 2, "템포롤화장지(24 m)", 500,
                 "https://cdn.daisomall.co.kr/images/prod2.jpg", "002_템포롤.jpg",
                 "뷰티/위생", "화장지/물티슈"),
                (3, 3, "동구밭 세탁조 크리너", 1000,
                 None, None,
                 "청소/욕실", "세탁용품"),
            ],
        )
        conn.commit()
        conn.close()
        return db_path

    def test_headers_contain_image_url(self, db_with_images):
        """headers should include image_url."""
        from backend.search.indexer import read_products_db
        _, headers = read_products_db(db_with_images)
        assert "image_url" in headers

    def test_headers_contain_price(self, db_with_images):
        """headers should include price."""
        from backend.search.indexer import read_products_db
        _, headers = read_products_db(db_with_images)
        assert "price" in headers

    def test_row_has_image_url(self, db_with_images):
        """Each row dict should have image_url key."""
        from backend.search.indexer import read_products_db
        rows, _ = read_products_db(db_with_images)
        assert "image_url" in rows[0]
        assert rows[0]["image_url"] == "https://cdn.daisomall.co.kr/images/prod1.jpg"

    def test_row_has_price(self, db_with_images):
        """Each row dict should have price key."""
        from backend.search.indexer import read_products_db
        rows, _ = read_products_db(db_with_images)
        assert "price" in rows[0]
        assert rows[0]["price"] == 5000

    def test_null_image_url_returns_empty_string(self, db_with_images):
        """If image_url is NULL in DB, row should have empty string."""
        from backend.search.indexer import read_products_db
        rows, _ = read_products_db(db_with_images)
        assert rows[2]["image_url"] == ""

    def test_null_price_returns_zero(self, tmp_path):
        """If price is NULL in DB, row should have 0."""
        db_path = str(tmp_path / "no_price.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                price INTEGER, image_url TEXT,
                category_major TEXT, category_middle TEXT
            )
        """)
        cur.execute("INSERT INTO products (id, name) VALUES (1, '가격없는 상품')")
        conn.commit()
        conn.close()

        from backend.search.indexer import read_products_db
        rows, _ = read_products_db(db_path)
        assert rows[0]["price"] == 0

    def test_existing_tests_still_pass_with_new_fields(self, db_with_images):
        """doc_id, title, text, category should still be correct."""
        from backend.search.indexer import read_products_db
        rows, headers = read_products_db(db_with_images)
        # Original fields still work
        assert rows[0]["doc_id"] == "P-1"
        assert rows[0]["title"] == "메디필 멜라논엑스 기미크림 30 ml"
        assert rows[0]["text"] == "메디필 멜라논엑스 기미크림 30 ml"
        assert rows[0]["category"] == "뷰티/위생 > 스킨케어"
        # New fields
        assert rows[0]["image_url"] == "https://cdn.daisomall.co.kr/images/prod1.jpg"
        assert rows[0]["price"] == 5000


class TestIndexCatalogSourceDb:
    """index_catalog() should support source='db' to read from products.db."""

    def test_dry_run_with_source_db(self, sample_db):
        """dry_run + source='db' should read from SQLite and report counts."""
        from backend.search.indexer import index_catalog

        result = index_catalog(
            source="db",
            db_path=sample_db,
            dry_run=True,
        )
        assert result["status"] == "dry_run"
        assert result["total"] == 3
        assert result["valid"] == 3

    def test_source_db_reads_from_sqlite_not_tsv(self, sample_db):
        """When source='db', read_products_db is called, not read_catalog."""
        from backend.search.indexer import index_catalog

        with patch("backend.search.indexer.read_products_db") as mock_read_db, \
             patch("backend.search.indexer.read_catalog") as mock_read_tsv:
            mock_read_db.return_value = (
                [
                    {"doc_id": "P-1", "title": "t", "text": "t", "category": "c"},
                ],
                ["doc_id", "title", "text", "category"],
            )
            index_catalog(source="db", db_path=sample_db, dry_run=True)
            mock_read_db.assert_called_once_with(sample_db)
            mock_read_tsv.assert_not_called()

    def test_source_tsv_still_works(self, tmp_path):
        """Default source='tsv' should still use read_catalog."""
        from backend.search.indexer import index_catalog

        tsv_path = str(tmp_path / "test.tsv")
        with open(tsv_path, "w", encoding="utf-8") as f:
            f.write("doc_id\ttitle\ttext\tcategory\n")
            f.write("P-1\t제품1\t설명1\t카테고리1\n")

        result = index_catalog(
            catalog_path=tsv_path,
            source="tsv",
            dry_run=True,
        )
        assert result["status"] == "dry_run"
        assert result["total"] == 1
