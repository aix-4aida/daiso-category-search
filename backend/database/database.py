"""
Database module for Daiso Category Search
SQLite database operations
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# Database path - relative to this file's location
DB_PATH = os.path.join(os.path.dirname(__file__), 'products.db')

def get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables and ChromaDB"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            name TEXT NOT NULL,
            price INTEGER,
            category_major TEXT,
            category_middle TEXT,
            floor TEXT,
            section TEXT,
            shelf_label TEXT,
            image_url TEXT,
            image_name TEXT,
            image_path TEXT,
            description TEXT,
            reviews TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name)
        )
    ''')
    
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

    # NEW: Initialize ChromaDB if needed
    try:
        from backend.services.search_service import CHROMA_DB_PATH
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        client.get_or_create_collection(name="products")
        print(f"✅ ChromaDB initialized: {CHROMA_DB_PATH}")
    except Exception as e:
        print(f"⚠️ ChromaDB init failed: {e}")
        
    ensure_schema()

def ensure_schema():
    """Migrate database schema if needed"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(products)")
    columns = [info[1] for info in cursor.fetchall()]
    
    new_cols = {
        'description': 'TEXT',
        'reviews': 'TEXT',
        'tags': 'TEXT'
    }
    
    for col, dtype in new_cols.items():
        if col not in columns:
            print(f"📦 Adding column '{col}' to products table...")
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
            except Exception as e:
                print(f"⚠️ Failed to add column {col}: {e}")
                
    conn.commit()
    conn.close()

def insert_product(rank: int, name: str, price: int, image_url: str, 
                   image_name: str = None, image_path: str = None,
                   category_major: str = None, category_middle: str = None,
                   floor: str = None, section: str = None, shelf_label: str = None,
                   description: str = None, reviews: str = None, tags: str = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if columns exist (for migration)
        # In production, better to use migration script, but here we just try insert
        # If schema changed, we might need to alter table or recreate.
        # For now, let's assume we recreate DB or alter manually if needed.
        # Actually, let's try to add columns if not exist in init_database, but here we just update insert.
        
        cursor.execute('''
            INSERT INTO products (rank, name, price, image_url, image_name, image_path, category_major, category_middle, floor, section, shelf_label, description, reviews, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                price=excluded.price,
                image_url=excluded.image_url,
                image_name=excluded.image_name,
                image_path=excluded.image_path,
                category_major=excluded.category_major,
                category_middle=excluded.category_middle,
                floor=excluded.floor,
                section=excluded.section,
                shelf_label=excluded.shelf_label,
                description=excluded.description,
                reviews=excluded.reviews,
                tags=excluded.tags
        ''', (rank, name, price, image_url, image_name, image_path, category_major, category_middle, floor, section, shelf_label, description, reviews, tags))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Insert error: {e}")
        return False
    finally:
        conn.close()

def get_product_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_products() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY rank')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def product_exists(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM products WHERE name = ?', (name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_utterance_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM test_utterances')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def search_products(keyword: str) -> List[Dict]:
    """Search products by name (simple LIKE query)"""
    conn = get_connection()
    cursor = conn.cursor()
    # Split keyword by spaces to support multiple terms "blue pen" -> "%blue%" AND "%pen%"
    terms = keyword.split()
    query = "SELECT * FROM products WHERE " + " AND ".join(["name LIKE ?"] * len(terms))
    params = [f"%{term}%" for term in terms]
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_related_products_for_context(keyword: str, limit: int = 5) -> str:
    """
    Search products and return a formatted string for LLM context.
    Example: "- Plastic Box (1000 won)\n- Paper Box (2000 won)"
    """
    products = search_products(keyword)
    if not products:
        return ""
    
    # Take top N matching products
    context_list = []
    for p in products[:limit]:
        context_list.append(f"- {p['name']} ({p.get('price', 'N/A')}원)")
    
    return "\n".join(context_list)


def sync_to_chroma():
    """Sync products from SQLite to ChromaDB"""
    from backend.services.search_service import CHROMA_DB_PATH, get_query_embedding
    import chromadb
    
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = client.get_or_create_collection(name="products")
    
    products = get_all_products()
    print(f"🔄 Syncing {len(products)} products to ChromaDB...")
    
    ids = []
    embeddings = []
    metadatas = []
    documents = []
    
    for p in products:
        p_id = str(p['id'])
        # Simplified: always upsert for now
        emb = get_query_embedding(p['name'])
        if emb:
            ids.append(p_id)
            embeddings.append(emb)
            metadatas.append({
                "price": p.get('price', 0),
                "category_major": p.get('category_major', ""),
                "category_middle": p.get('category_middle', "")
            })
            documents.append(p['name'])
            
    if ids:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        print(f"✅ Successfully synced {len(ids)} products")

if __name__ == "__main__":
    init_database()
    sync_to_chroma()
    print(f"Products: {get_product_count()}")
