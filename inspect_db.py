
import sqlite3
import os

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\backend\database\products.db"

if not os.path.exists(DB_PATH):
    print(f"Error: DB not found at {DB_PATH}")
    # Try looking in current dir relative to script
    DB_PATH = os.path.join(os.getcwd(), "backend", "database", "products.db")
    if not os.path.exists(DB_PATH):
        print(f"Error: DB also not found at {DB_PATH}")
        exit(1)

print(f"Connecting to {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Get Schema for each table
for table in tables:
    table_name = table[0]
    print(f"\n--- Schema for {table_name} ---")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(col)

    # Preview data
    print(f"\n--- Preview Data (Top 3) for {table_name} ---")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

conn.close()
