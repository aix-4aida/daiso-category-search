import sys
import os
import json
import uuid
import time
import sqlite3
import requests
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Configuration
DB_PATH = PROJECT_ROOT / "backend" / "database" / "products.db"
QDRANT_URL = "http://localhost:6333"
ELASTIC_URL = "http://localhost:9200"
COLLECTION_NAME = "products"
INDEX_NAME = "products"
EMBEDDING_MODEL_NAME = "distiluse-base-multilingual-cased-v2"
UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "daiso-search")

def check_services():
    try:
        requests.get(f"{QDRANT_URL}/collections")
        print("✅ Qdrant is up")
    except:
        print("❌ Qdrant is down")
        return False
        
    try:
        requests.get(ELASTIC_URL)
        print("✅ Elasticsearch is up")
    except:
        print("❌ Elasticsearch is down")
        return False
    return True

def get_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔄 Loading model: {EMBEDDING_MODEL_NAME}")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("✅ Model loaded")
        return model
    except ImportError:
        print("❌ sentence-transformers not installed. Run: pip install sentence-transformers")
        sys.exit(1)

def load_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category_major, category_middle FROM products")
    rows = cursor.fetchall()
    products = []
    for r in rows:
        products.append({
            "id": str(r[0]),
            "name": r[1],
            "text": r[1], # Use name as text for now
            "category": f"{r[2]} > {r[3]}"
        })
    conn.close()
    print(f"✅ Loaded {len(products)} products from DB")
    return products

# --- Elastic Ops ---
def setup_elastic_index():
    headers = {"Content-Type": "application/json"}
    # Check if exists
    r = requests.head(f"{ELASTIC_URL}/{INDEX_NAME}")
    if r.status_code == 200:
        print(f"ℹ️ Elastic index '{INDEX_NAME}' already exists.")
        return

    # Create index with analyzers (Nori if available, else standard)
    # Using simple standard analyzer for now to ensure compatibility
    body = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "standard"},
                "text": {"type": "text", "analyzer": "standard"},
                "bm25_text": {"type": "text", "analyzer": "standard"},
                "category": {"type": "keyword"},
            }
        }
    }
    r = requests.put(f"{ELASTIC_URL}/{INDEX_NAME}", headers=headers, json=body)
    if r.status_code in (200, 201):
        print(f"✅ Created Elastic index '{INDEX_NAME}'")
    else:
        print(f"❌ Failed to create Elastic index: {r.text}")

def index_elastic(products):
    bulk_data = []
    for p in products:
        action = {"index": {"_index": INDEX_NAME, "_id": p["id"]}}
        # Create bm25_text by combining title and text (and category maybe)
        bm25_text = f"{p['name']} {p['category']}".strip()
        doc = {
            "doc_id": p["id"],
            "title": p["name"],
            "text": p["name"], # searching on name
            "bm25_text": bm25_text,
            "category": p["category"]
        }
        bulk_data.append(json.dumps(action))
        bulk_data.append(json.dumps(doc))
    
    # Send in chunks
    chunk_size = 500
    total_sent = 0
    headers = {"Content-Type": "application/x-ndjson"}
    
    for i in range(0, len(bulk_data), chunk_size * 2):
        chunk = bulk_data[i : i + chunk_size * 2]
        data_str = "\n".join(chunk) + "\n"
        r = requests.post(f"{ELASTIC_URL}/_bulk", headers=headers, data=data_str.encode('utf-8'))
        if r.status_code == 200:
            total_sent += len(chunk) // 2
        else:
            print(f"⚠️ Elastic bulk error: {r.text}")
            
    print(f"✅ Indexed {total_sent} docs to Elasticsearch")

# --- Qdrant Ops ---
def setup_qdrant_collection(dim=512):
    r = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
    if r.status_code == 200:
        print(f"ℹ️ Qdrant collection '{COLLECTION_NAME}' already exists.")
        return

    body = {
        "vectors": {
            "size": dim,
            "distance": "Cosine"
        }
    }
    r = requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", json=body)
    if r.status_code == 200:
        print(f"✅ Created Qdrant collection '{COLLECTION_NAME}'")
    else:
        print(f"❌ Failed to create Qdrant collection: {r.text}")

def index_qdrant(products, model):
    texts = [p["name"] for p in products]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    points = []
    for i, p in enumerate(products):
        # Create a UUID based on the string ID for Qdrant
        qid = str(uuid.uuid5(UUID_NAMESPACE, p["id"]))
        points.append({
            "id": qid,
            "vector": embeddings[i].tolist(),
            "payload": {
                "doc_id": p["id"],
                "title": p["name"],
                "text": p["name"],
                "category": p["category"]
            }
        })
    
    # Upsert
    r = requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true", json={"points": points})
    if r.status_code == 200:
        print(f"✅ Indexed {len(points)} vectors to Qdrant")
    else:
        print(f"❌ Qdrant upsert failed: {r.text}")

def main():
    if not check_services():
        return

    products = load_products()
    model = get_sentence_transformer()
    
    # Elastic
    print("\n--- Indexing Elasticsearch ---")
    setup_elastic_index()
    index_elastic(products)
    
    # Qdrant
    print("\n--- Indexing Qdrant ---")
    dim = model.get_sentence_embedding_dimension()
    setup_qdrant_collection(dim)
    index_qdrant(products, model)
    
    print("\n🎉 Indexing Complete!")

if __name__ == "__main__":
    main()
