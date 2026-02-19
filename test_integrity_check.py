# -*- coding: utf-8 -*-
"""Final data integrity check: SQLite + ChromaDB metadata + vector dimensions."""
import sys, os, json
sys.path.insert(0, '.')

print("=" * 60)
print("  Data Integrity Check")
print("=" * 60)

# 1. SQLite products.db
import sqlite3
conn = sqlite3.connect('backend/database/products.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM products')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM products WHERE name IS NULL OR name = ""')
null_names = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM products WHERE price IS NULL')
null_prices = c.fetchone()[0]

# Check for encoding corruption (common pattern: contains mojibake chars)
c.execute("SELECT id, name FROM products WHERE name LIKE '%???%' OR name LIKE '%ð%' LIMIT 5")
suspicious = c.fetchall()

# Spot check specific products
c.execute("SELECT id, name, category_major, floor, section FROM products WHERE id IN (579, 580, 604, 1, 100, 3503)")
spot_check = c.fetchall()
conn.close()

print(f"\n[SQLite] products.db")
print(f"  Total products: {total}")
print(f"  Null names: {null_names}")
print(f"  Null prices: {null_prices}")
print(f"  Suspicious encoding: {len(suspicious)} rows")
print(f"\n  Spot check:")
for r in spot_check:
    print(f"    ID={r[0]}, Name={r[1]}, Category={r[2]}, Floor={r[3]}, Section={r[4]}")

# 2. ChromaDB
import chromadb
client = chromadb.PersistentClient(path="backend/database/chroma_db")
coll = client.get_collection("products")
chroma_count = coll.count()

# Get random sample to check metadata
sample = coll.get(ids=["579", "580", "604", "1", "100", "3503"], include=["metadatas", "documents", "embeddings"])

print(f"\n[ChromaDB] chroma_db")
print(f"  Collection count: {chroma_count}")
print(f"  Match SQLite? {'YES' if chroma_count == total else 'NO (' + str(total) + ' vs ' + str(chroma_count) + ')'}")

print(f"\n  Metadata spot check:")
for doc_id, meta, doc, emb in zip(sample['ids'], sample['metadatas'], sample['documents'], sample['embeddings']):
    emb_dim = len(emb) if emb else 0
    has_nan = any(v != v for v in emb) if emb else False  # NaN check
    print(f"    ID={doc_id}")
    print(f"      name: {meta.get('name', '?')}")
    print(f"      category: {meta.get('category_major', '?')}")
    print(f"      doc: {doc[:40]}...")
    print(f"      embedding dim: {emb_dim}, has_NaN: {has_nan}")

# 3. Summary
print(f"\n{'=' * 60}")
issues = []
if null_names > 0: issues.append(f"{null_names} null names")
if suspicious: issues.append(f"{len(suspicious)} suspicious encoding")
if chroma_count != total: issues.append(f"count mismatch ({total} vs {chroma_count})")

if issues:
    print(f"  ISSUES FOUND: {', '.join(issues)}")
else:
    print(f"  ALL CLEAR - No data integrity issues found")
print(f"{'=' * 60}")
