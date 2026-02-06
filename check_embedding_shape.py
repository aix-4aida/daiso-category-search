
import sqlite3
import pickle
import numpy as np

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\poc\lyg\data\products.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT product_id, text_embedding FROM product_embeddings WHERE text_embedding IS NOT NULL LIMIT 1;")
row = cursor.fetchone()

if row:
    product_id, emb_blob = row
    try:
        embedding = pickle.loads(emb_blob)
        print(f"Product ID: {product_id}")
        print(f"Type: {type(embedding)}")
        if isinstance(embedding, np.ndarray):
            print(f"Shape: {embedding.shape}")
            print(f"Dtype: {embedding.dtype}")
        elif isinstance(embedding, list):
            print(f"Length: {len(embedding)}")
    except Exception as e:
        print(f"Error unpickling: {e}")
else:
    print("No embeddings found in product_embeddings table.")

conn.close()
