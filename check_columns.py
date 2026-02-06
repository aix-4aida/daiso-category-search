
import sqlite3

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\backend\database\products.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(products);")
columns = cursor.fetchall()
print("Columns in 'products' table:")
for col in columns:
    print(col)

conn.close()
