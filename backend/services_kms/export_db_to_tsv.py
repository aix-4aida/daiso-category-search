import sqlite3
import csv
import os
import sys
from pathlib import Path

# Project root setup
try:
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(project_root))
except NameError:
    project_root = Path(".").resolve()

DB_PATH = project_root / "backend/database/products.db"
OUTPUT_TSV_PATH = project_root / "backend/services_kms/data/products_exported.tsv"

def export_db_to_tsv():
    """
    Export products from SQLite DB to TSV format compatible with indexing script.
    Schema: doc_id, title, text, category
    """
    print(f"Exporting DB to TSV...")
    print(f"  - DB: {DB_PATH}")
    print(f"  - Output: {OUTPUT_TSV_PATH}")
    
    if not DB_PATH.exists():
        print(f"Error: Database file not found at {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Query products
        query = """
        SELECT id, name, category_major, category_middle 
        FROM products 
        ORDER BY id
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"  - Found {len(rows)} products.")
        
        # Ensure output directory exists
        OUTPUT_TSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_TSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            # Write header
            writer.writerow(['doc_id', 'title', 'text', 'category'])
            
            for r in rows:
                p_id, name, major, middle = r
                
                # Format fields
                doc_id = str(p_id)
                title = name or ""
                
                # Construct text field (richer context for indexing)
                # Including category info in text helps retrieval
                text_content = f"{name} {major or ''} {middle or ''}".strip()
                
                # Construct category field
                if major and middle:
                    category = f"{major} > {middle}"
                elif major:
                    category = major
                else:
                    category = ""
                    
                writer.writerow([doc_id, title, text_content, category])
                
        print(f"Export completed: {OUTPUT_TSV_PATH}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Export failed: {e}")
        return False

if __name__ == "__main__":
    export_db_to_tsv()
