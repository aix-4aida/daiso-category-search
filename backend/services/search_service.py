"""
Hybrid Search Service
=====================
Uses 영근님's ivhl adapters for BM25, Vector Search, and RRF Fusion.
Supports both External (Qdrant/Elastic) and Local (In-memory) modes.
"""
import sys
import os
import pickle
import numpy as np
from pathlib import Path
import sqlite3
# 에러 해결을 위해 PROJECT_ROOT를 현재 파일 위치 기준으로 정의합니다.
# 현재 파일: backend/services/search_service.py -> 상위로 2번 가면 프로젝트 루트입니다.
PROJECT_ROOT = Path(__file__).parent.parent.parent

# ============================================================
# Import Search Infrastructure (Refactored to backend/search)
# ============================================================
# Previously imported from poc/lyg/src/ivhl
from backend.search.adapters.bm25 import LocalBM25, ElasticBM25Retriever
from backend.search.adapters.fusion import rrf_fusion, weighted_fusion
from backend.search.adapters.retrieval import BruteForceVectorRetriever, QdrantVectorRetriever

from backend.search.core.types import Document, ScoredDoc

IVHL_AVAILABLE = True
print("✅ Search adapters imported successfully (Refactored)")

# ============================================================
# Configuration
# ============================================================
BACKEND_DB_PATH = PROJECT_ROOT / "backend" / "database" / "products.db"
POC_DB_PATH = PROJECT_ROOT / "poc" / "lyg" / "data" / "products.db"

# External Server Config
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
ELASTIC_URL = os.environ.get("ELASTIC_URL", "http://localhost:9200")

print(f"🔄 Initializing Hybrid Search Engine (Qdrant: {QDRANT_URL}, Elastic: {ELASTIC_URL})...")

# ============================================================
# Load Products from Backend DB as Document objects
# ============================================================
def load_products_as_documents(db_path: Path) -> list:
    """Load products from SQLite DB into ivhl Document objects."""
    docs = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """SELECT id, name, category_major, category_middle FROM products"""
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            p_id, name, major, middle = row
            if IVHL_AVAILABLE:
                doc = Document(
                    doc_id=str(p_id),
                    title=name or "",
                    text=name or "",  # Use name as searchable text
                    meta={"major": major, "middle": middle}
                )
            else:
                # Fallback simple object
                class SimpleDoc:
                    def __init__(self, doc_id, title, text, meta):
                        self.doc_id = str(doc_id)
                        self.title = title
                        self.text = text or ""
                        self.meta = meta
                doc = SimpleDoc(p_id, name, name, {"major": major, "middle": middle})
            docs.append(doc)
        
        conn.close()
        print(f"✅ Loaded {len(docs)} products from backend DB")
    except Exception as e:
        print(f"❌ Error loading products: {e}")
    return docs

# ============================================================
# Load Embeddings from POC DB (Fallback only)
# ============================================================
def load_embeddings(db_path: Path) -> dict:
    """Returns dict: {doc_id: embedding_as_list}"""
    embeddings = {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_id, text_embedding FROM product_embeddings WHERE text_embedding IS NOT NULL")
        rows = cursor.fetchall()
        
        for row in rows:
            product_id, emb_blob = row
            try:
                emb = pickle.loads(emb_blob)
                if isinstance(emb, np.ndarray):
                    # Convert to list for ivhl compatibility
                    embeddings[str(product_id)] = emb.flatten().tolist()
            except:
                pass
        
        conn.close()
        print(f"✅ Loaded {len(embeddings)} embeddings from POC DB")
    except Exception as e:
        print(f"❌ Error loading embeddings: {e}")
    return embeddings

# ============================================================
# Query Embedding (using SentenceTransformer)
# ============================================================
query_encoder = None

def get_query_embedding(query: str) -> list:
    """Generate embedding for query using SentenceTransformer."""
    global query_encoder
    if query_encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use 512-dim multilingual model (matches DB embeddings)
            query_encoder = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            print("✅ Loaded SentenceTransformer model for query embedding (512-dim)")
        except Exception as e:
            print(f"⚠️ Failed to load SentenceTransformer: {e}")
            return None
    
    embedding = query_encoder.encode(query, convert_to_numpy=True)
    return embedding.flatten().tolist()  # Return as list for ivhl

# ============================================================
# Initialize Search Components
# ============================================================
docs = []
bm25_engine = None
docs_map = {}
embeddings = {}
vector_retriever = None

# Load products
if BACKEND_DB_PATH.exists():
    docs = load_products_as_documents(BACKEND_DB_PATH)
    if docs:
        docs_map = {d.doc_id: d for d in docs}
        
        # Initialize Retrievers
        if IVHL_AVAILABLE:
            # 1. Elastic BM25 (Primary)
            try:
                bm25_engine = ElasticBM25Retriever(
                    docs=docs,
                    base_url=ELASTIC_URL,
                    index="products"
                )
                print(f"✅ ElasticBM25Retriever initialized ({ELASTIC_URL})")
            except Exception as e:
                print(f"⚠️ ElasticBM25Retriever init failed: {e}. Falling back to LocalBM25.")
                bm25_engine = LocalBM25(docs=docs)

            # 2. Qdrant Vector (Primary)
            try:
                vector_retriever = QdrantVectorRetriever(
                    url=QDRANT_URL,
                    collection="products"
                )
                print(f"✅ QdrantVectorRetriever initialized ({QDRANT_URL})")
            except Exception as e:
                print(f"⚠️ QdrantVectorRetriever init failed: {e}. Checking local embeddings...")
                # Fallback to local BruteForce if Qdrant fails
                if POC_DB_PATH.exists():
                    embeddings = load_embeddings(POC_DB_PATH)
                    if embeddings:
                        vector_retriever = BruteForceVectorRetriever(docs=docs, doc_vecs=embeddings)
                        print("✅ BruteForceVectorRetriever initialized (ivhl fallback)")
                    else:
                        print("⚠️ No local embeddings found.")
                        vector_retriever = None
        else:
            print("⚠️ ivhl adapter not available. Using LocalBM25.")
            bm25_engine = LocalBM25(docs=docs)
else:
    print(f"⚠️ Backend DB not found at {BACKEND_DB_PATH}")


print(f"✅ Hybrid Search Engine ready: {len(docs)} products")

# ============================================================
# Fallback: Custom Vector Search (when ivhl not available)
# ============================================================
def _cosine_similarity_fallback(a, b) -> float:
    """Fallback cosine similarity."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def _rrf_fusion_fallback(bm25_doc_ids: list, vector_results: list, k: int = 60) -> list:
    """Fallback RRF fusion."""
    scores = {}
    
    # BM25 contribution
    for rank, doc_id in enumerate(bm25_doc_ids):
        if doc_id not in scores:
            scores[doc_id] = 0.0
        scores[doc_id] += 1.0 / (k + rank + 1)
    
    # Vector contribution
    for rank, (doc_id, _) in enumerate(vector_results):
        if doc_id not in scores:
            scores[doc_id] = 0.0
        scores[doc_id] += 1.0 / (k + rank + 1)
    
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in sorted_items]

def _fallback_vector_search(query_emb, embeddings_dict: dict, top_k: int) -> list:
    """Fallback vector search without ivhl."""
    scores = []
    for doc_id, doc_emb in embeddings_dict.items():
        score = _cosine_similarity_fallback(query_emb, np.array(doc_emb))
        scores.append((doc_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]

# ============================================================
# Main Search Function
# ============================================================
def search_products(query: str, top_k: int = 30, use_hybrid: bool = True, fusion_method: str = "rrf") -> list[dict]:
    """
    Search products using Hybrid Search (BM25 + Vector) with ivhl adapters.
    - Primary: uses ivhl external retrievers (Elastic/Qdrant)
    - Secondary: uses ivhl local retrievers (LocalBM25/BruteForce)
    - Fallback: uses custom implementation when ivhl not available
    
    Args:
        query: Search query string
        top_k: Number of results to return
        use_hybrid: If True, use hybrid search. If False, use BM25 only.
        fusion_method: "rrf" or "weighted"
    
    Returns:
        List of dicts: {'id', 'name', 'desc', 'meta'}
    """
    if not bm25_engine:
        return []
    
    # 1. BM25 Search (Sparse)
    try:
        top_k_bm25 = top_k * 2 if use_hybrid else top_k
        sparse_results = bm25_engine.query(query, top_k=top_k_bm25)
    except Exception as e:
        print(f"⚠️ BM25 search failed: {e}")
        sparse_results = []
    
    # 2. Vector Search (Dense) if hybrid enabled
    fused_results = sparse_results
    
    if use_hybrid and IVHL_AVAILABLE:
        query_emb = get_query_embedding(query)
        if query_emb is not None:
            top_k_dense = top_k * 2
            
            if vector_retriever:
                # === Primary/Secondary: Use ivhl adapters ===
                try:
                    dense_results = vector_retriever.query(query_emb, top_k=top_k_dense)
                    
                    if fusion_method == "rrf":
                        fused_results = rrf_fusion(dense_results, sparse_results, rrf_k=60, top_k=top_k)
                    else:
                        fused_results = weighted_fusion(dense_results, sparse_results, alpha=0.5, top_k=top_k)
                except Exception as e:
                    print(f"⚠️ Vector search failed: {e}")
            elif embeddings:
                 # === Fallback: Custom implementation (if ivhl loaded but no retriever?) ===
                 # Usually BruteForceVectorRetriever handles this if intialized
                 # But if even that failed, use custom fallback
                 print("⚠️ Using fallback hybrid search (ivhl loaded but vector retriever missing)")
                 query_emb_np = np.array(query_emb)
                 vector_results = _fallback_vector_search(query_emb_np, embeddings, top_k_dense)
                 bm25_doc_ids = [sd.doc_id for sd in sparse_results]
                 fused_doc_ids = _rrf_fusion_fallback(bm25_doc_ids, vector_results, k=60)
                 # Map back to mock ScoredDoc for consistency? 
                 # Or just rebuild list of dicts directly from doc_ids
                 results = []
                 for doc_id in fused_doc_ids[:top_k]:
                    doc = docs_map.get(doc_id)
                    if doc:
                        results.append({
                            "id": doc.doc_id,
                            "name": doc.title,
                            "desc": doc.text,
                            "meta": doc.meta
                        })
                 return results
    
    # 3. Build output for ivhl results
    results = []
    for sd in fused_results[:top_k]:
        doc = docs_map.get(sd.doc_id)
        if doc:
            results.append({
                "id": doc.doc_id,
                "name": doc.title,
                "desc": doc.text,
                "meta": doc.meta
            })
    
    return results
