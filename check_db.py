import sqlite3
import os

db_path = "backend/database/products.db"
if not os.path.exists(db_path):
    print(f"File not found: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM products WHERE name LIKE '%물티슈%'")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} products matching '물티슈':")
        for r in rows:
            print(f" - {r[0]}")
            
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]
        print(f"Total products in DB: {total}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
