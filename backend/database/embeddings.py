"""Generate CLIP text embeddings and store them in SQLite as pickled BLOBs."""
import sqlite3
import pickle
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from database import get_connection

MODEL_NAME = "openai/clip-vit-base-patch32"


def generate_embeddings() -> None:
    """Generate 512-dim CLIP text embeddings for all products."""
    print(f"Loading model: {MODEL_NAME}")
    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()

    print(f"Generating embeddings for {len(products)} products")

    for p_id, p_name in products:
        inputs = processor(text=[p_name], return_tensors="pt", padding=True)
        with torch.no_grad():
            # transformers 5.x returns BaseModelOutputWithPooling
            # The 512-dim vector is in .pooler_output (shape: [batch, 512])
            result = model.get_text_features(**inputs)
            if hasattr(result, "pooler_output"):
                pooled = result.pooler_output[0]
            else:
                pooled = result[0]
            # L2-normalize and convert to 1-D float32 numpy array
            vector = pooled / pooled.norm(p=2, dim=-1, keepdim=True)
            vector_np = vector.numpy().astype(np.float32).flatten()

        # Wrap with sqlite3.Binary so SQLite stores it as a true BLOB
        blob = sqlite3.Binary(pickle.dumps(vector_np))

        cursor.execute(
            "INSERT OR REPLACE INTO product_embeddings "
            "(product_id, text_embedding) VALUES (?, ?)",
            (p_id, blob),
        )

        if p_id % 50 == 0:
            print(f"  Processed {p_id} products")
            conn.commit()

    conn.commit()
    conn.close()
    print("[OK] Embedding generation completed successfully")


if __name__ == "__main__":
    generate_embeddings()
