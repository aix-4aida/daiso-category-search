
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath("."))

from backend.services.keyword_service import extract_keyword
from backend.services.search_service import search_products
from backend.services.rerank_service import rerank_products

def test_pipeline(query):
    print(f"\n--- Testing Query: '{query}' ---")
    
    # 1. Keyword Extraction
    print("1. Extracting Keyword...")
    kw_res = extract_keyword(query)
    keyword = kw_res.get("keyword")
    print(f"   Keyword: '{keyword}'")
    print(f"   Reasoning: {kw_res.get('reasoning')}")
    
    # 2. Search
    print("2. Searching Products...")
    candidates = search_products(keyword or query, top_k=5)
    print(f"   Found {len(candidates)} candidates.")
    for i, c in enumerate(candidates):
        print(f"   [{i}] {c['name']} (ID: {c['id']})")
        
    # 3. Rerank
    if candidates:
        print("3. Reranking...")
        rerank_res = rerank_products(query, candidates)
        print(f"   Selected ID: {rerank_res.get('selected_id')}")
        print(f"   Reason: {rerank_res.get('reason')}")
        
        selected_id = rerank_res.get("selected_id")
        if selected_id:
            final = next((c for c in candidates if c['id'] == selected_id), None)
            if final:
                print(f"   Final Product: {final['name']}")
    else:
        print("   No candidates for reranking.")

if __name__ == "__main__":
    test_pipeline("물티슈")
    # Also test what happens with noise or specific terms that might lead to '냄비'
    test_pipeline("냄비")
    test_pipeline("그거 닦는거")
