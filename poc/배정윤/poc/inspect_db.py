
import sqlite3
import os

db_path = r"c:\Users\301\pjt\Final\search\daiso-category-search\backend\database\products.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(tables)
    
    for table_name in tables:
        t = table_name[0]
        print(f"\n--- Schema for {t} ---")
        cursor.execute(f"PRAGMA table_info({t})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
    # Check count
    if tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tables[0][0]}")
        print(f"\nTotal rows in {tables[0][0]}: {cursor.fetchone()[0]}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
