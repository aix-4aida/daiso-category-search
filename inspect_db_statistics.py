import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

DB_PATH = os.path.join(os.getcwd(), 'backend', 'database', 'products.db')

def inspect_db_stats():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"🔍 Database Analysis: {DB_PATH}\n")
    print("="*40)

    # 1. Table Counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    total_products = 0
    
    print(f"📊 Tables Found: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        print(f"   - {table}: {count:,} rows")
        if table == 'products':
            total_products = count

    print("\n" + "="*40)
    
    # 2. Product Data Quality (if products table exists)
    if 'products' in tables:
        print(f"🧠 Product Data Quality Analysis (Total: {total_products:,})")
        
        # Check for missing crucial fields
        checks = {
            "Missing Description": "description IS NULL OR description = ''",
            "Missing Reviews": "reviews IS NULL OR reviews = ''",
            "Missing Tags": "tags IS NULL OR tags = ''",
            "Missing Image URL": "image_url IS NULL OR image_url = ''",
            "Missing Category": "category_major IS NULL",
            "Zero Price": "price = 0"
        }
        
        for label, condition in checks.items():
            cursor.execute(f"SELECT COUNT(*) as count FROM products WHERE {condition}")
            fail_count = cursor.fetchone()['count']
            success_count = total_products - fail_count
            percent = (fail_count / total_products * 100) if total_products > 0 else 0
            
            status = "✅" if fail_count == 0 else "⚠️" if percent < 10 else "❌"
            print(f"   {status} {label}: {fail_count:,} ({percent:.1f}%)")

        # 3. Category Distribution (Top 10)
        print("\n🏆 Top 10 Major Categories:")
        cursor.execute("SELECT category_major, COUNT(*) as c FROM products GROUP BY category_major ORDER BY c DESC LIMIT 10")
        for row in cursor.fetchall():
            cat = row['category_major'] or "Unknown"
            print(f"   - {cat}: {row['c']:,}")

    conn.close()

if __name__ == "__main__":
    inspect_db_stats()
