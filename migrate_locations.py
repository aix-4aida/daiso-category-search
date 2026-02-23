"""
Migrate products.db to use proper map section codes.
====================================================
Updates floor, section, and shelf_label for all products based
on their category_major, using the mapping in map_config.py.
"""
import sqlite3
import random
from pathlib import Path

# Import map config
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.database.map_config import (
    CATEGORY_TO_SECTION, B1_SECTIONS, B2_SECTIONS
)

DB_PATH = Path(__file__).resolve().parent / "backend" / "database" / "products.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all products
    c.execute("SELECT id, category_major FROM products")
    rows = c.fetchall()
    
    updated = 0
    unmapped = set()
    
    for pid, cat_major in rows:
        if cat_major in CATEGORY_TO_SECTION:
            floor, section_name = CATEGORY_TO_SECTION[cat_major]
            sections = B1_SECTIONS if floor == "B1" else B2_SECTIONS
            
            if section_name in sections:
                sec_info = sections[section_name]
                code_prefix = sec_info["code"]
                num_shelves = len(sec_info["shelves"])
                
                # Distribute products across shelves in this section
                shelf_idx = (pid % num_shelves) + 1
                section_code = f"{code_prefix}{shelf_idx:02d}"
                shelf_label = sec_info["label"]
                
                c.execute(
                    "UPDATE products SET floor=?, section=?, shelf_label=? WHERE id=?",
                    (floor, section_code, shelf_label, pid)
                )
                updated += 1
            else:
                unmapped.add(cat_major)
        else:
            unmapped.add(cat_major)
    
    conn.commit()
    
    # Verify
    c.execute("SELECT floor, section, COUNT(*) FROM products GROUP BY floor, section ORDER BY floor, section")
    groups = c.fetchall()
    
    print(f"\n{'='*50}")
    print(f"  Migration Complete: {updated} products updated")
    print(f"{'='*50}")
    
    if unmapped:
        print(f"  ⚠️ Unmapped categories: {unmapped}")
    
    print(f"\n  {'Floor':5s} | {'Section':10s} | {'Count':>5s}")
    print(f"  {'─'*5} | {'─'*10} | {'─'*5}")
    for floor, section, cnt in groups:
        print(f"  {floor:5s} | {section:10s} | {cnt:5d}")
    
    conn.close()
    print(f"\n  ✅ Done!")

if __name__ == "__main__":
    migrate()
