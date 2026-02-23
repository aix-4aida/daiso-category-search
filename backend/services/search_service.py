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
# Korean Synonym / Alternate Spelling Map
# ============================================================
SYNONYM_MAP = {
    "알코올": ["알콜", "알코올"],
    "알콜": ["알코올", "알콜"],
    "솜": ["스왑", "솜"],
    "핸드폰": ["휴대폰", "스마트폰"],
    "휴대폰": ["핸드폰", "스마트폰"],
    "볼펜": ["볼 펜", "펜"],
    "가위": ["시저"],
    "물티슈": ["물 티슈", "웨트 티슈"],
    "이어폰": ["이어 폰", "이어셋"],
    "충전기": ["충전 기", "차저"],
}

def expand_query_with_synonyms(query: str) -> list:
    """Expand a query into multiple variants using synonym map."""
    variants = [query]
    for word, synonyms in SYNONYM_MAP.items():
        if word in query:
            for syn in synonyms:
                variant = query.replace(word, syn)
                if variant != query and variant not in variants:
                    variants.append(variant)
    return variants

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
        query = "SELECT id, name, price, category_major, category_middle, floor, section, shelf_label, image_url FROM products"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            p_id, name, price, major, middle, floor, section, shelf_label, image_url = row
            docs.append(Document(
                doc_id=str(p_id),
                title=name or "",
                text=name or "",
                meta={
                    "price": price, 
                    "major": major, 
                    "middle": middle,
                    "floor": floor,
                    "section": section,
                    "shelf_label": shelf_label,
                    "image_url": image_url
                }
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
            elastic = ElasticBM25Retriever(docs=docs, base_url=ELASTIC_URL, index="products_idx")
            if elastic.check_connection():
                bm25_engine = elastic
                print(f"✅ ElasticBM25Retriever initialized ({ELASTIC_URL})")
            else:
                raise ConnectionError("ElasticSearch not reachable")
        except Exception as e:
            print(f"⚠️ ElasticBM25 init failed: {e}. Falling back to LocalBM25.")
            bm25_engine = LocalBM25(docs=docs)
        
        # 2. Vector (Primary: ChromaDB if exists locally, Secondary: Qdrant)
        # We prioritize ChromaDB here because we are baking the index into the Docker image.
        try:
            if CHROMA_DB_PATH.exists() and any(CHROMA_DB_PATH.iterdir()):
                print(f"📂 Found local ChromaDB at {CHROMA_DB_PATH}. Using it.")
                vector_retriever = ChromaVectorRetriever(
                    collection_name="products",
                    persist_directory=str(CHROMA_DB_PATH)
                )
                print(f"✅ ChromaVectorRetriever initialized at {CHROMA_DB_PATH}")
            else:
                raise FileNotFoundError("ChromaDB path not found or empty")
        except Exception as e_chroma:
            print(f"⚠️ ChromaDB init skipped/failed: {e_chroma}. Attempting Qdrant.")
            try:
                qdrant = QdrantVectorRetriever(url=QDRANT_URL, collection_name="products")
                if qdrant.check_connection():
                    vector_retriever = qdrant
                    print(f"✅ QdrantVectorRetriever initialized ({QDRANT_URL})")
                else:
                    raise ConnectionError("Qdrant not reachable")
            except Exception as e_qdrant:
                print(f"⚠️ Qdrant init failed: {e_qdrant}")

# ============================================================
# Main Search Function
# ============================================================
def search_products(query: str, top_k: int = 3, use_hybrid: bool = True, fusion_method: str = "rrf") -> list[dict]:
    if not bm25_engine:
        return []
    
    top_k_fetch = top_k * 5
    
    # 1. BM25 with synonym expansion
    query_variants = expand_query_with_synonyms(query)
    print(f"    [Synonyms] Variants: {query_variants}")
    
    all_sparse = []
    seen_ids = set()
    for variant in query_variants:
        results = bm25_engine.query(variant, top_k=top_k_fetch)
        for r in results:
            if r.doc_id not in seen_ids:
                all_sparse.append(r)
                seen_ids.add(r.doc_id)
    
    # Sort by score descending, take top
    all_sparse.sort(key=lambda x: x.score, reverse=True)
    sparse_results = all_sparse[:top_k_fetch]
    
    bm25_top = [(sr.doc_id, f"{sr.score:.2f}") for sr in sparse_results[:3]]
    print(f"    [BM25] Top 3: {bm25_top}")
    
    # 2. Hybrid
    fused_results = sparse_results
    if use_hybrid and vector_retriever:
        query_emb = get_query_embedding(query)
        if query_emb:
            try:
                dense_results = vector_retriever.query(query_emb, top_k=top_k_fetch)
                
                # Filter out low scores
                valid_dense = [d for d in dense_results if d.score > 0.3]
                print(f"    [Vector] Total={len(dense_results)}, Valid(score>0.3)={len(valid_dense)}")
                
                if valid_dense:
                    if fusion_method == "rrf":
                        fused_results = rrf_fusion(valid_dense, sparse_results, rrf_k=60, top_k=top_k_fetch, sparse_weight=2.0)
                    else:
                        fused_results = weighted_fusion(valid_dense, sparse_results, alpha=0.5, top_k=top_k_fetch)
                    fused_top = [(fr.doc_id, f"{fr.score:.4f}") for fr in fused_results[:3]]
                    print(f"    [Fusion] Top 3: {fused_top}")
                else:
                    print(f"    [Vector] All scores below 0.3 → BM25-only mode")
            except Exception as e:
                print(f"⚠️ Vector search failed: {e}")
    
    # 3. Output - only include results with meaningful scores
    results = []
    for sd in fused_results:
        if sd.score <= 0.0:
            continue
        doc = docs_map.get(sd.doc_id)
        if doc:
            results.append({
                "id": doc.doc_id,
                "name": doc.title,
                "desc": doc.text,
                "price": doc.meta.get("price", 0),
                "meta": doc.meta,
                "score": sd.score
            })
            if len(results) >= top_k:
                break
    
    # 4. Score gap filter: drop outliers with score < 30% of top score
    if results:
        top_score = results[0]["score"]
        threshold = top_score * 0.3
        filtered = [r for r in results if r["score"] >= threshold]
        dropped = len(results) - len(filtered)
        if dropped > 0:
            print(f"    [ScoreGap] Dropped {dropped} outliers (threshold={threshold:.4f}, top={top_score:.4f})")
            for r in results:
                if r["score"] < threshold:
                    print(f"      ❌ Dropped: {r['name']} (score={r['score']:.4f})")
        results = filtered
    
    return results

