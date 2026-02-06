
import sqlite3
import pickle
import numpy as np
import os

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\backend\database\products.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name, embedding FROM products WHERE embedding IS NOT NULL LIMIT 1;")
row = cursor.fetchone()

if row:
    name, emb_blob = row
    try:
        # Try unpickling
        embedding = pickle.loads(emb_blob)
        print(f"Product: {name}")
        print(f"Type: {type(embedding)}")
        if isinstance(embedding, np.ndarray):
            print(f"Shape: {embedding.shape}")
        elif isinstance(embedding, list):
            print(f"Length: {len(embedding)}")
        else:
             print(f"Content: {embedding}")
    except Exception as e:
        print(f"Error unpickling: {e}")
        # Try raw numpy load if it's bytes
        try:
             import io
             embedding = np.load(io.BytesIO(emb_blob), allow_pickle=True)
             print(f"Shape (via np.load): {embedding.shape}")
        except Exception as e2:
             print(f"Error np.load: {e2}")

else:
    print("No embeddings found in DB.")

conn.close()
