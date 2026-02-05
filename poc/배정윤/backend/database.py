"""
Database module for Search-Roca
SQLite for now, PostgreSQL ready for later
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

def get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            name TEXT NOT NULL,
            price INTEGER,
            image_url TEXT,
            image_name TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name)
        )
    ''')
    
    # Test utterances table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_utterances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utterance TEXT NOT NULL,
            difficulty TEXT CHECK(difficulty IN ('normal', 'hard')),
            expected_product_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expected_product_id) REFERENCES products(id)
        )
    ''')
    
    # Product embeddings table (for CLIP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_embeddings (
            product_id INTEGER PRIMARY KEY,
            text_embedding BLOB,
            image_embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def insert_product(rank: int, name: str, price: int, image_url: str, 
                   image_name: str = None, image_path: str = None) -> bool:
    """Insert product, skip if duplicate"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO products (rank, name, price, image_url, image_name, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (rank, name, price, image_url, image_name, image_path))
        conn.commit()
        inserted = cursor.rowcount > 0
        return inserted
    except Exception as e:
        print(f"❌ Insert error: {e}")
        return False
    finally:
        conn.close()

def get_product_count() -> int:
    """Get total number of products"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_products() -> List[Dict]:
    """Get all products"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY rank')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def product_exists(name: str) -> bool:
    """Check if product already exists"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM products WHERE name = ?', (name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def insert_utterance(utterance: str, difficulty: str, product_id: int) -> bool:
    """Insert test utterance"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO test_utterances (utterance, difficulty, expected_product_id)
            VALUES (?, ?, ?)
        ''', (utterance, difficulty, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Insert utterance error: {e}")
        return False
    finally:
        conn.close()

def get_utterance_count() -> int:
    """Get total number of test utterances"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM test_utterances')
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == "__main__":
    init_database()
    print(f"Products: {get_product_count()}")
    print(f"Utterances: {get_utterance_count()}")
