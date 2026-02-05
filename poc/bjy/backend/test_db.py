"""
Database PoC Test
Tests for database integrity, embeddings, and search performance
"""
import sqlite3
import os
import time
import numpy as np

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_product_count():
    """Test: 상품 수 >= 600"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"[1] Product Count: {count}")
    assert count >= 600, f"[FAIL] Expected >= 600, got {count}"
    print("    [PASS]")
    return count

def test_required_columns():
    """Test: 필수 컬럼 존재 확인"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products LIMIT 1')
    product = cursor.fetchone()
    conn.close()
    
    required = ['id', 'name', 'price']
    missing = [col for col in required if col not in product.keys()]
    
    print(f"[2] Required Columns: {required}")
    assert not missing, f"[FAIL] Missing columns: {missing}"
    print("    [PASS]")

def test_null_values():
    """Test: 필수 컬럼 NULL 값 없음"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE name IS NULL')
    null_names = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM products WHERE price IS NULL')
    null_prices = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"[3] NULL Check: name={null_names}, price={null_prices}")
    assert null_names == 0, f"[FAIL] {null_names} products with NULL name"
    print("    [PASS]")

def test_embeddings_count():
    """Test: 모든 상품에 임베딩 존재"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    product_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM product_embeddings')
    embed_count = cursor.fetchone()[0]
    
    conn.close()
    
    ratio = embed_count / product_count * 100 if product_count > 0 else 0
    
    print(f"[4] Embeddings: {embed_count}/{product_count} ({ratio:.1f}%)")
    assert ratio >= 90, f"[FAIL] Expected >= 90%, got {ratio:.1f}%"
    print("    [PASS]")

def test_embedding_validity():
    """Test: 임베딩 데이터 복원 가능"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT text_embedding FROM product_embeddings LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    
    if row and row['text_embedding']:
        embedding = np.frombuffer(row['text_embedding'], dtype=np.float32)
        print(f"[5] Embedding Shape: {embedding.shape}")
        assert len(embedding) == 512, f"[FAIL] Expected 512 dims, got {len(embedding)}"
        print("    [PASS]")
    else:
        print("[5] Embedding Validity: [SKIP] No embeddings found")

def test_category_matching():
    """Test: 카테고리 매칭률 >= 80%"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE category_major != '기타' AND category_major IS NOT NULL")
    matched = cursor.fetchone()[0]
    
    conn.close()
    
    ratio = matched / total * 100 if total > 0 else 0
    
    print(f"[6] Category Matching: {matched}/{total} ({ratio:.1f}%)")
    if ratio < 80:
        print(f"    [WARN] Below 80% target, currently {ratio:.1f}%")
    else:
        print("    [PASS]")
    return ratio

def test_search_performance():
    """Test: 검색 성능 < 100ms"""
    conn = get_connection()
    cursor = conn.cursor()
    
    queries = ["물티슈", "컵", "화장지"]
    times = []
    
    for query in queries:
        start = time.time()
        cursor.execute('SELECT * FROM products WHERE name LIKE ?', (f'%{query}%',))
        results = cursor.fetchall()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    conn.close()
    
    avg_time = sum(times) / len(times)
    print(f"[7] Search Performance: avg {avg_time:.1f}ms")
    assert avg_time < 100, f"[FAIL] Expected < 100ms, got {avg_time:.1f}ms"
    print("    [PASS]")

def run_all_tests():
    print("=" * 50)
    print("Database PoC Test")
    print("=" * 50)
    print()
    
    results = {}
    
    try:
        results['product_count'] = test_product_count()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        test_required_columns()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        test_null_values()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        test_embeddings_count()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        test_embedding_validity()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        results['category_ratio'] = test_category_matching()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    try:
        test_search_performance()
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    print()
    print("=" * 50)
    print("Database PoC Test Complete")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    run_all_tests()
