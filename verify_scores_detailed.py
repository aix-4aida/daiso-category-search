# -*- coding: utf-8 -*-
"""
Verify scores detailed: Top 10 Hybrid items with BM25/Vector breakdown.
"""
import sys
import os
import io
import contextlib
import re
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))
load_dotenv()

# Suppress warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from backend.services.search_service import search_products
from backend.services.rerank_service import rerank_products

queries = ["알콜솜", "키보드"]

def capture_search_logs(query):
    # Capture stdout
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        # Request Top 10
        candidates = search_products(query, top_k=10)
    
    logs = f.getvalue()
    
    # Parse logs for maps
    bm25_map = {}
    vector_map = {}
    
    for line in logs.split('\n'):
        line = line.strip()
        if line.startswith("[BM25_ALL]"):
            content = line.replace("[BM25_ALL] ", "")
            try:
                data = eval(content, {"nan": 0})
                for item in data:
                    bm25_map[str(item['id'])] = item['score']
            except:
                pass
        elif line.startswith("[VECTOR_ALL]"):
            content = line.replace("[VECTOR_ALL] ", "")
            try:
                data = eval(content, {"nan": 0})
                for item in data:
                    vector_map[str(item['id'])] = item['score']
            except:
                pass

    return candidates, bm25_map, vector_map

print(f"| Query | Rank | Product ID | Name | BM25 | Vector | Hybrid | Rerank |")
print(f"|---|---|---|---|---|---|---|---|")

for q in queries:
    candidates, bm25_map, vector_map = capture_search_logs(q)
    
    # Reranking (Pass all candidates, let LLM pick top 3)
    rerank_result = rerank_products(q, candidates)
    top_ids = [str(x) for x in rerank_result.get("top_ids", [])]
    reason = rerank_result.get("reason", "")
    
    # Output Table Rows for Top 10
    for i, item in enumerate(candidates):
        rank = i + 1
        pid = str(item['id'])
        name = item['name']
        hybrid_score = item.get('score', 0)
        
        bm25_score = bm25_map.get(pid, 0.0)
        vector_score = vector_map.get(pid, 0.0)
        
        # Format scores
        bm25_str = f"{bm25_score:.2f}" if bm25_score > 0 else "-"
        vector_str = f"{vector_score:.4f}" if vector_score > 0 else "-" # Vector scores are small
        hybrid_str = f"{hybrid_score:.4f}"
        
        # Rerank column
        if pid in top_ids:
            # Find rank in top_ids (0-based index + 1)
            r_rank = top_ids.index(pid) + 1
            rerank_str = f"✅ #{r_rank}"
        else:
            rerank_str = "-"
            
        # Clean name (remove special chars/newlines if any)
        name = name.replace("|", "/").strip()
        
        print(f"| {q} | {rank} | {pid} | {name} | {bm25_str} | {vector_str} | {hybrid_str} | {rerank_str} |")
    
    # Print Rerank Reason as a separate row or just note it
    print(f"| {q} | - | - | **Rerank Reason** | - | - | - | {reason} |")
    print("|---|---|---|---|---|---|---|---|")
