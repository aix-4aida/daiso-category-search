import sqlite3
import os

db_plural = "backend/database/products.db"
db_singular = "backend/database/product.db"

def check_db(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    print(f"\n--- Checking {path} ---")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    try:
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        if 'products' in tables:
            # Check schema
            cursor.execute("PRAGMA table_info(products);")
            columns = cursor.fetchall()
            print("Columns in 'products' table:")
            for c in columns:
                print(f" - {c[1]} ({c[2]})")
            
            # Check for 물티슈
            cursor.execute("SELECT name, category_major, category_middle FROM products WHERE name LIKE '%물티슈%' LIMIT 5")
            rows = cursor.fetchall()
            print(f"Products matching '물티슈':")
            for r in rows:
                print(f" - {r}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

check_db(db_plural)
check_db(db_singular)
