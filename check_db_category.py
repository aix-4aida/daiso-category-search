import sqlite3
import os

db_path = 'backend/database/products.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Checking '네오셀 알카라인 건전지' ---")
cursor.execute("SELECT id, name, category_major, category_middle FROM products WHERE name LIKE '%네오셀%'")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n--- Checking Distinct Major Categories ---")
cursor.execute("SELECT DISTINCT category_major FROM products LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
