import sqlite3
import os

db_path = r"c:\2026\final\daiso\merged-branch-by-bjy\backend\database\products.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Products named '원' ---")
    cursor.execute("SELECT * FROM products WHERE name = '원'")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    print("\n--- Products containing '알코올' ---")
    cursor.execute("SELECT * FROM products WHERE name LIKE '%알코올%'")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    print("\n--- Products containing '솜' ---")
    cursor.execute("SELECT * FROM products WHERE name LIKE '%솜%'")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
