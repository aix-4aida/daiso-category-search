import sys
import os
import sqlite3

# Add project root to sys.path
sys.path.append(os.getcwd())

DB_PATH = os.path.join(os.getcwd(), 'backend', 'database', 'products.db')

def verify_db():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM products WHERE description IS NOT NULL OR tags IS NOT NULL ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} products")
        
        for row in rows:
            print("-" * 30)
            print(f"Name: {row['name']}")
            print(f"Price: {row['price']}")
            
            # Check new columns
            desc = row['description']
            reviews = row['reviews']
            tags = row['tags']
            
            print(f"Description: {desc[:50]}..." if desc else "Description: None")
            print(f"Reviews: {reviews[:50]}..." if reviews else "Reviews: None")
            print(f"Tags: {tags}")
            
    except Exception as e:
        print(f"Error reading DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_db()
