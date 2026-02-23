"""Check local DB sections for keyboard products."""
import sqlite3
conn = sqlite3.connect("backend/database/products.db")
c = conn.cursor()
c.execute("SELECT id, name, floor, section, shelf_label FROM products WHERE name LIKE '%키보드%'")
rows = c.fetchall()
print("Local DB check:")
for r in rows:
    print(f"  ID={r[0]} name={r[1]} floor={r[2]} section={r[3]} label={r[4]}")
conn.close()
