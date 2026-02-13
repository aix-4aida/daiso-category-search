
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.services.search_service import search_products, bm25_engine, vector_retriever, get_query_embedding

def debug():
    query = "물티슈"
    print(f"🔍 Debugging search for: '{query}'")
    
    # 1. Check BM25
    if bm25_engine:
        sparse = bm25_engine.query(query, top_k=10)
        print(f"📊 BM25 Results ({len(sparse)}):")
        for sd in sparse[:5]:
            from backend.services.search_service import docs_map
            doc = docs_map.get(sd.doc_id)
            if doc:
                print(f"  - {doc.title} (Score: {sd.score:.4f})")
            else:
                print(f"  - [ZOMBIE ID] {sd.doc_id} (Score: {sd.score:.4f})")
    
    # 2. Check Vector
    if vector_retriever:
        emb = get_query_embedding(query)
        dense = vector_retriever.query(emb, top_k=10)
        print(f"📊 Vector Results ({len(dense)}):")
        for sd in dense[:10]:
            from backend.services.search_service import docs_map
            doc = docs_map.get(sd.doc_id)
            if doc:
                print(f"  - {doc.title} (Score: {sd.score:.4f})")
            else:
                print(f"  - [ZOMBIE ID] {sd.doc_id} (Score: {sd.score:.4f})")
            
    # 3. Check Hybrid
    hybrid = search_products(query, top_k=3)
    print(f"📊 Hybrid Results ({len(hybrid)}):")
    for r in hybrid:
        print(f"  - {r['name']} (Score: {r['score']:.4f})")

if __name__ == "__main__":
    debug()
