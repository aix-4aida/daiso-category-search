"""Initialize Qdrant collection with product embeddings from SQLite."""
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.qdrant_service import QdrantService, deserialize_embedding
from database.database import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    qdrant = QdrantService()

    print("==================================================")
    print("[Qdrant Collection Initialization]")
    print("==================================================")

    # 1. Load embeddings from SQLite
    print("[1/3] Loading embeddings from SQLite...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.price, p.image_url, e.text_embedding
        FROM products p
        JOIN product_embeddings e ON p.id = e.product_id
    """)
    rows = cursor.fetchall()
    print(f"  Found {len(rows)} products with embeddings")

    if not rows:
        print("[ERROR] No embeddings found. Run embeddings.py first.")
        conn.close()
        await qdrant.close()
        return

    # 2. Create collection (skip if already exists to avoid Windows OS errors)
    print("[2/3] Creating Qdrant collection...")
    await qdrant.recreate_collection()

    # 3. Build and upload vectors
    print("[3/3] Uploading vectors to Qdrant...")
    from qdrant_client.models import PointStruct

    points = []
    skipped = 0

    for row in rows:
        p_id, p_name, p_price, p_img, p_emb = row
        try:
            vector = deserialize_embedding(p_emb)
            if isinstance(vector, list) and len(vector) == 512:
                points.append(
                    PointStruct(
                        id=p_id,
                        vector=vector,
                        payload={
                            "name": p_name,
                            "price": p_price,
                            "image_url": p_img,
                        },
                    )
                )
            else:
                logger.warning(
                    f"Product {p_id}: unexpected vector length {len(vector)}"
                )
                skipped += 1
        except Exception as e:
            logger.warning(f"Product {p_id}: deserialization failed - {e}")
            skipped += 1

    if points:
        uploaded = await qdrant.bulk_upsert(points)
        print(f"\n[OK] Uploaded {uploaded} vectors (skipped: {skipped})")
    else:
        print("\n[ERROR] No valid vectors found to upload")

    await qdrant.close()
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
