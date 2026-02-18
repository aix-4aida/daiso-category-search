import sqlite3
import os

db_path = 'backend/database/products.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
    
    # Check distinct values if category_major exists
    col_names = [col[1] for col in columns]
    if 'category_major' in col_names:
        cursor.execute("SELECT DISTINCT category_major FROM products")
        majors = cursor.fetchall()
        print("Majors:", [m[0] for m in majors])
    else:
        print("category_major column not found")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
