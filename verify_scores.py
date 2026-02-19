# -*- coding: utf-8 -*-
"""
Verify scores for BM25, Vector, Hybrid, and Reranking.
Captures stdout from search_service to get intermediate scores.
"""
import sys
import os
import io
import contextlib
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
        candidates = search_products(query, top_k=5)
    
    logs = f.getvalue()
    
    # Parse logs for scores
    bm25_scores = []
    vector_scores = []
    fusion_scores = []
    
    for line in logs.split('\n'):
        line = line.strip()
        if line.startswith("[BM25] Top 3:"):
            # Format: [('id', 'score'), ...]
            content = line.replace("[BM25] Top 3: ", "")
            bm25_scores = eval(content)
        elif line.startswith("[Vector] Top 3 with scores:"): # Might need to adjust search_service logging to match this or parse what exists
            pass 
        elif "[Vector]" in line and "Top 3" in line:
             # Search service format might be: [Vector] Top 3: [('id', 'score')...]
             pass
        elif line.startswith("[Fusion] Top 3:"):
            content = line.replace("[Fusion] Top 3: ", "")
            fusion_scores = eval(content)

    return candidates, logs, bm25_scores, fusion_scores

print(f"| Query | Stage | Rank | Product ID | Name | Score/Reason |")
print(f"|---|---|---|---|---|---|")

for q in queries:
    # 1. Retrieval & Fusion
    candidates, logs, bm25_data, fusion_data = capture_search_logs(q)
    
    # Extract Raw Vector Scores from logs (search_service doesn't print structured vector scores in Top 3 format cleanly in previous view, let's parse raw lines if possible or relies on candidates)
    # Actually search_service currently prints:
    # [BM25] Top 3: [('id', 'score'), ...]
    # [Fusion] Top 3: [('id', 'score'), ...]
    # [Vector] ... valid items count ...
    
    # Let's just use the fusion results as "Hybrid" scores.
    # For BM25/Vector breakdown, I might need to read the log lines more carefully or just report what I can.
    # The user wants specific comparison.
    
    # 2. Reranking
    rerank_result = rerank_products(q, candidates)
    top_ids = rerank_result.get("top_ids", [])
    reason = rerank_result.get("reason", "")
    
    # --- OUTPUT ---
    # Show BM25 Top 3
    if bm25_data:
        for i, (pid, score) in enumerate(bm25_data):
            # Find name from candidates if present, else lookup (not efficient but okay)
            name = next((c['name'] for c in candidates if str(c['id']) == str(pid)), "Unknown (Filtered?)")
            print(f"| {q} | BM25 | {i+1} | {pid} | {name} | {score} |")
            
    # Show Fusion Top 3
    if fusion_data:
        for i, (pid, score) in enumerate(fusion_data):
             name = next((c['name'] for c in candidates if str(c['id']) == str(pid)), "Unknown")
             print(f"| {q} | Hybrid | {i+1} | {pid} | {name} | {score} |")
             
    # Show Rerank Results
    if top_ids:
        print(f"| {q} | Rerank | - | {top_ids} | - | {reason} |")
    else:
        print(f"| {q} | Rerank | - | None | - | {reason} |")
        
    print("|---|---|---|---|---|---|")
