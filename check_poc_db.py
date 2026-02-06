
import sqlite3

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\poc\lyg\data\products.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Check columns for each table
for table in tables:
    table_name = table[0]
    print(f"\n--- Columns in '{table_name}' ---")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(col)

conn.close()
