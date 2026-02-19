import sqlite3
import json

db_path = r"c:\2026\final\daiso\merged-branch-by-bjy\backend\database\products.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    print("--- Schema ---")
    cursor.execute("PRAGMA table_info(products)")
    schema = cursor.fetchall()
    for col in schema:
        print(col)
        
    print("\n--- Sample Data (First 3) ---")
    cursor.execute("SELECT * FROM products LIMIT 3")
    rows = cursor.fetchall()
    print(json.dumps(rows, indent=2, ensure_ascii=False))

    print("\n--- Products named '원' ---")
    cursor.execute("SELECT * FROM products WHERE name = '원'")
    rows = cursor.fetchall()
    print(f"Count: {len(rows)}")
    if rows:
        print(json.dumps(rows[:3], indent=2, ensure_ascii=False))
        
    print("\n--- Products containing '알코올' ---")
    cursor.execute("SELECT * FROM products WHERE name LIKE '%알코올%'")
    rows = cursor.fetchall()
    print(f"Count: {len(rows)}")
    if rows:
        print(json.dumps(rows[:3], indent=2, ensure_ascii=False))

    conn.close()
except Exception as e:
    print(f"Error: {e}")
