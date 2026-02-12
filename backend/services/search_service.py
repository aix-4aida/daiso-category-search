"""
Hybrid Search Service (MVP Refactored)
=====================================
Uses ChromaDB for Vector Search and LocalBM25 for Sparse Search.
"""
import sys
import os
import pickle
import numpy as np
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ============================================================
# Import Search Infrastructure
# ============================================================
from backend.search.adapters.bm25 import LocalBM25, ElasticBM25Retriever
from backend.search.adapters.fusion import rrf_fusion, weighted_fusion
from backend.search.adapters.retrieval import BruteForceVectorRetriever, QdrantVectorRetriever, ChromaVectorRetriever

from backend.search.core.types import Document, ScoredDoc

IVHL_AVAILABLE = True
print("✅ Search adapters imported successfully (ChromaDB Integrated)")

# ============================================================
# Configuration
# ============================================================
BACKEND_DB_PATH = PROJECT_ROOT / "backend" / "database" / "products.db"
CHROMA_DB_PATH = PROJECT_ROOT / "backend" / "database" / "chroma_db"

# External Server Config
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
ELASTIC_URL = os.environ.get("ELASTIC_URL", "http://localhost:9200")

# ============================================================
# Load Products
# ============================================================
def load_products_as_documents(db_path: Path) -> list:
    docs = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT id, name, category_major, category_middle FROM products"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            p_id, name, major, middle = row
            docs.append(Document(
                doc_id=str(p_id),
                title=name or "",
                text=name or "",
                meta={"major": major, "middle": middle}
            ))
        conn.close()
        print(f"✅ Loaded {len(docs)} products")
    except Exception as e:
        print(f"❌ Error loading products: {e}")
    return docs

# ============================================================
# Query Embedding
# ============================================================
query_encoder = None

def get_query_embedding(query: str) -> list:
    global query_encoder
    if query_encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            query_encoder = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            print("✅ Loaded SentenceTransformer (512-dim)")
        except Exception as e:
            print(f"⚠️ Failed to load SentenceTransformer: {e}")
            return None
    
    embedding = query_encoder.encode(query, convert_to_numpy=True)
    return embedding.flatten().tolist()

# ============================================================
# Initialize Search Components
# ============================================================
docs = []
bm25_engine = None
docs_map = {}
vector_retriever = None

if BACKEND_DB_PATH.exists():
    docs = load_products_as_documents(BACKEND_DB_PATH)
    if docs:
        docs_map = {d.doc_id: d for d in docs}
        
        # 1. BM25 (Primary: Elastic if available, Fallback: Local)
        try:
            bm25_engine = ElasticBM25Retriever(docs=docs, base_url=ELASTIC_URL, index="products_idx")
            print(f"✅ ElasticBM25Retriever initialized ({ELASTIC_URL})")
        except Exception as e:
            print(f"⚠️ ElasticBM25 init failed: {e}. Falling back to LocalBM25.")
            bm25_engine = LocalBM25(docs=docs)
        
        # 2. Vector (Primary: Qdrant if available, Secondary: Chroma)
        try:
            vector_retriever = QdrantVectorRetriever(url=QDRANT_URL, collection_name="products")
            print(f"✅ QdrantVectorRetriever initialized ({QDRANT_URL})")
        except Exception as e:
            print(f"⚠️ Qdrant init failed: {e}. Attempting ChromaDB.")
            try:
                vector_retriever = ChromaVectorRetriever(
                    collection_name="products",
                    persist_directory=str(CHROMA_DB_PATH)
                )
                print(f"✅ ChromaVectorRetriever initialized at {CHROMA_DB_PATH}")
            except Exception as e2:
                print(f"⚠️ ChromaDB init failed: {e2}")

# ============================================================
# Main Search Function
# ============================================================
def search_products(query: str, top_k: int = 30, use_hybrid: bool = True, fusion_method: str = "rrf") -> list[dict]:
    if not bm25_engine:
        return []
    
    # 1. BM25
    top_k_sparse = top_k * 2 if use_hybrid else top_k
    sparse_results = bm25_engine.query(query, top_k=top_k_sparse)
    
    # 2. Hybrid
    fused_results = sparse_results
    if use_hybrid and vector_retriever:
        query_emb = get_query_embedding(query)
        if query_emb:
            try:
                dense_results = vector_retriever.query(query_emb, top_k=top_k * 2)
                if fusion_method == "rrf":
                    fused_results = rrf_fusion(dense_results, sparse_results, rrf_k=60, top_k=top_k)
                else:
                    fused_results = weighted_fusion(dense_results, sparse_results, alpha=0.5, top_k=top_k)
            except Exception as e:
                print(f"⚠️ Vector search failed: {e}")
    
    # 3. Output
    results = []
    for sd in fused_results[:top_k]:
        doc = docs_map.get(sd.doc_id)
        if doc:
            results.append({
                "id": doc.doc_id,
                "name": doc.title,
                "desc": doc.text,
                "meta": doc.meta,
                "score": sd.score
            })
    return results
