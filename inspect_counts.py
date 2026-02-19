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
    
    cursor.execute("SELECT count(*) as cnt FROM products")
    cnt = cursor.fetchone()['cnt']
    print(f"Total Products: {cnt}")
    
    print("\n--- First 10 Products ---")
    cursor.execute("SELECT id, name, price FROM products LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['name']}, Price: {row['price']}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
