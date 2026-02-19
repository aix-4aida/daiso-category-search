"""
ChromaDB Vector Index Rebuild Script
=====================================
Deletes the existing stale ChromaDB index and rebuilds it
from the current products.db data using SentenceTransformer embeddings.

Usage:
    cd c:\2026\final\daiso\merged-branch-by-bjy
    .venv\Scripts\python.exe rebuild_chroma_index.py
"""
import sys
import os
import shutil
import sqlite3
import time

sys.path.insert(0, '.')

# Paths
DB_PATH = os.path.join("backend", "database", "products.db")
CHROMA_DB_PATH = os.path.join("backend", "database", "chroma_db")

COLLECTION_NAME = "products"
MODEL_NAME = "distiluse-base-multilingual-cased-v2"
BATCH_SIZE = 100


def main():
    # 1. Delete existing ChromaDB index
    if os.path.exists(CHROMA_DB_PATH):
        print(f"🗑️  Deleting existing ChromaDB at: {CHROMA_DB_PATH}")
        shutil.rmtree(CHROMA_DB_PATH)
    else:
        print(f"ℹ️  No existing ChromaDB found at: {CHROMA_DB_PATH}")

    # 2. Load products from SQLite
    print(f"📦 Loading products from: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, category_major, category_middle FROM products")
    rows = cursor.fetchall()
    conn.close()
    print(f"   → {len(rows)} products loaded")

    if not rows:
        print("❌ No products found! Aborting.")
        return

    # 3. Load SentenceTransformer
    print(f"🧠 Loading SentenceTransformer model: {MODEL_NAME}")
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(MODEL_NAME)
    print(f"   → Model loaded (embedding dim: {encoder.get_sentence_embedding_dimension()})")

    # 4. Create ChromaDB collection
    print(f"🔧 Creating new ChromaDB collection: {COLLECTION_NAME}")
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # 5. Generate embeddings and add to ChromaDB in batches
    total = len(rows)
    start_time = time.time()

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch = rows[batch_start:batch_end]

        ids = [str(r[0]) for r in batch]
        # Combine name + category for richer embeddings
        texts = []
        metadatas = []
        for r in batch:
            p_id, name, price, major, middle = r
            text = f"{name or ''} {major or ''} {middle or ''}".strip()
            texts.append(text)
            metadatas.append({
                "name": name or "",
                "price": price or 0,
                "category_major": major or "",
                "category_middle": middle or ""
            })

        # Encode
        embeddings = encoder.encode(texts, convert_to_numpy=True).tolist()

        # Add to ChromaDB
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        elapsed = time.time() - start_time
        pct = batch_end / total * 100
        print(f"   [{batch_end}/{total}] {pct:.0f}% ({elapsed:.1f}s elapsed)")

    total_time = time.time() - start_time
    print(f"\n✅ ChromaDB rebuilt successfully!")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Documents: {collection.count()}")
    print(f"   Path: {CHROMA_DB_PATH}")
    print(f"   Time: {total_time:.1f}s")

    # 6. Quick validation: test query
    print(f"\n🔍 Validation: searching '알콜솜'...")
    query_emb = encoder.encode("알콜솜", convert_to_numpy=True).tolist()
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=5,
        include=["metadatas", "distances", "documents"]
    )
    
    print(f"   Top 5 results:")
    for i, (doc_id, doc, meta, dist) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        score = 1.0 - dist if dist <= 1.0 else 0.0
        print(f"   {i+1}. ID={doc_id}, Score={score:.4f}, Name={meta.get('name', '?')}")


if __name__ == "__main__":
    main()
