
import os
import sys
import sqlite3
# import pandas as pd  <-- Removed
from pathlib import Path
from dotenv import load_dotenv

# Setup Paths
current_dir = Path(os.getcwd())
sys.path.append(str(current_dir))

load_dotenv()

from backend.search.adapters.bm25 import LocalBM25
from backend.search.adapters.retrieval import ChromaVectorRetriever
from backend.search.adapters.fusion import rrf_fusion
from backend.search.core.types import Document, ScoredDoc
from backend.services.rerank_service import rerank_products

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("⚠️ sentence-transformers not installed. Vector search might fail.")
    SentenceTransformer = None

# Config
DB_PATH = current_dir / "backend" / "database" / "products.db"
CHROMA_PATH = current_dir / "backend" / "database" / "chroma_db"
KEYWORDS = ["건전지", "키보드"]

# 1. Load Products (Docs)
def load_docs():
    print(f"📂 Loading products from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, category_major, category_middle, description, tags FROM products")
    rows = cursor.fetchall()
    docs = []
    for r in rows:
        pid, name, price, major, middle, desc, tags = r
        # Create text for indexing
        text_content = f"{name} {major} {middle} {tags or ''}"
        docs.append(Document(
            doc_id=str(pid),
            title=name,
            text=text_content,
            meta={"price": price, "desc": desc, "major": major, "middle": middle}
        ))
    conn.close()
    print(f"✅ Loaded {len(docs)} documents.")
    return docs

# 2. Initialize Engines
def init_engines(docs):
    # BM25
    print("🔧 Initializing LocalBM25...")
    bm25 = LocalBM25(docs)
    
    # Vector
    print("🔧 Initializing ChromaDB & Embedding Model...")
    vector_retriever = None
    encoder = None
    if SentenceTransformer:
        try:
            encoder = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            vector_retriever = ChromaVectorRetriever(
                collection_name="products",
                persist_directory=str(CHROMA_PATH)
            )
            print("✅ Vector Search Ready.")
        except Exception as e:
            print(f"⚠️ Vector init failed: {e}")
    else:
        print("⚠️ Skipping Vector Search (Module missing)")
    
    return bm25, vector_retriever, encoder

def analyze(keyword, bm25, vector, encoder, docs_map):
    print(f"\n🔍 Analyzing Keyword: {keyword}")
    
    # 1. BM25
    bm25_res = bm25.query(keyword, top_k=20)
    bm25_scores = {d.doc_id: d.score for d in bm25_res}
    
    # 2. Vector
    vector_res = []
    vector_scores = {}
    if vector and encoder:
        vec = encoder.encode(keyword, convert_to_numpy=True).flatten().tolist()
        vector_res = vector.query(vec, top_k=20)
        vector_scores = {d.doc_id: d.score for d in vector_res}
        
    # 3. Fusion (RRF)
    # We re-use logic: rrf_fusion expects lists of ScoredDoc
    fused_res = rrf_fusion(vector_res, bm25_res, rrf_k=60, top_k=10)
    
    # Prepare Data for Table
    table_data = []
    candidates_for_rerank = []
    
    for rank, item in enumerate(fused_res, 1):
        doc = docs_map.get(item.doc_id)
        if not doc: continue
        
        b_score = bm25_scores.get(item.doc_id, 0.0)
        v_score = vector_scores.get(item.doc_id, 0.0)
        
        table_data.append({
            "Rank": rank,
            "ID": item.doc_id,
            "Name": doc.title,
            "Major": doc.meta.get('major'),
            "BM25": f"{b_score:.4f}",
            "Vector": f"{v_score:.4f}",
            "Total(RRF)": f"{item.score:.4f}"
        })
        
        candidates_for_rerank.append({
            "id": item.doc_id,
            "name": doc.title,
            "desc": doc.text, # Use constructed text for context
            "meta": doc.meta
        })
        
    # 4. Rerank
    print("🤖 Reranking Top 10...")
    rerank_out = rerank_products(keyword, candidates_for_rerank)
    top_ids = rerank_out.get("top_ids", [])
    reason = rerank_out.get("reason", "")
    
    # Mark Rerank Status
    final_rows = []
    for row in table_data:
        rid = row["ID"]
        if rid in top_ids:
            r_rank = top_ids.index(rid) + 1
            row["Rerank"] = f"🥇 #{r_rank}"
        else:
            row["Rerank"] = "-"
        final_rows.append(row)
        
    return final_rows, reason

def print_markdown_table(rows):
    if not rows:
        return ""
    headers = ["Rank", "Name", "Major", "BM25", "Vector", "Total(RRF)", "Rerank"]
    col_widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            val = str(row.get(h, ""))
            col_widths[h] = max(col_widths[h], len(val))
    
    # Header
    md = "| " + " | ".join(f"{h:<{col_widths[h]}}" for h in headers) + " |\n"
    # Separator
    md += "| " + " | ".join("-" * col_widths[h] for h in headers) + " |\n"
    # Rows
    for row in rows:
        md += "| " + " | ".join(f"{str(row.get(h, '')):<{col_widths[h]}}" for h in headers) + " |\n"
    return md

# Main
def main():
    docs = load_docs()
    docs_map = {d.doc_id: d for d in docs}
    bm25, vector, encoder = init_engines(docs)
    
    md_output = "# 📊 Search Quality Analysis Report\n\n"
    
    for kw in KEYWORDS:
        rows, reason = analyze(kw, bm25, vector, encoder, docs_map)
        
        md_output += f"## 🔎 Keyword: `{kw}`\n\n"
        md_output += f"**Rerank Reason:** {reason}\n\n"
        
        md_output += print_markdown_table(rows)
        md_output += "\n\n---\n\n"
        
    with open("search_quality_analysis.md", "w", encoding="utf-8") as f:
        f.write(md_output)
    
    print("\n✅ Analysis Saved to search_quality_analysis.md")

if __name__ == "__main__":
    main()
