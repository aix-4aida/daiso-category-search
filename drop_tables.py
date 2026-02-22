import sqlite3

conn = sqlite3.connect('backend/database/products.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS test_utterances')
cursor.execute('DROP TABLE IF EXISTS product_embeddings')
conn.commit()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Remaining tables:', [t[0] for t in cursor.fetchall()])
conn.close()
print('Done!')
