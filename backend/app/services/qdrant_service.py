"""Qdrant service - vector similarity search."""
import logging
import pickle

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "daiso_products_v5"
VECTOR_DIM = 512


def _get_client() -> AsyncQdrantClient:
    """Create Qdrant async client."""
    return AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
        check_compatibility=False,
    )


async def check_qdrant_health() -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = _get_client()
        await client.get_collections()
        await client.close()
        return True
    except Exception:
        return False


class QdrantService:
    """Qdrant vector search service."""

    def __init__(self) -> None:
        self.client: AsyncQdrantClient | None = None

    async def _ensure_client(self) -> AsyncQdrantClient:
        if self.client is None:
            self.client = _get_client()
        return self.client

    async def create_collection(self) -> None:
        """Create the products collection if it does not exist."""
        client = await self._ensure_client()
        collections = await client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION_NAME not in names:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_DIM, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created collection: {COLLECTION_NAME}")

    async def recreate_collection(self) -> None:
        """Create collection only if missing. Skip deletion to avoid Windows OS Error 5."""
        client = await self._ensure_client()

        collections = await client.get_collections()
        existing_names = [c.name for c in collections.collections]

        if COLLECTION_NAME in existing_names:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists. Reusing it.")
            return

        try:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_DIM, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def upsert_point(
        self, product_id: int, vector: list[float], payload: dict
    ) -> None:
        """Upsert a single point."""
        client = await self._ensure_client()
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(id=product_id, vector=vector, payload=payload)
            ],
        )

    async def bulk_upsert(self, points: list[PointStruct]) -> int:
        """Bulk upsert points in batches of 100."""
        client = await self._ensure_client()
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await client.upsert(
                collection_name=COLLECTION_NAME, points=batch
            )
        return len(points)

    async def search(
        self, query_vector: list[float], limit: int = 30
    ) -> list[dict]:
        """Vector similarity search."""
        client = await self._ensure_client()
        try:
            results = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=limit,
            )
            return [
                {**point.payload, "id": point.id, "score": point.score}
                for point in results.points
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None


def deserialize_embedding(blob: bytes) -> list[float]:
    """Deserialize a pickled numpy array from SQLite BLOB to a flat list of floats."""
    import numpy as np

    arr = pickle.loads(blob)
    if isinstance(arr, np.ndarray):
        return arr.flatten().tolist()
    # Fallback for legacy nested-list data
    result = list(arr)
    while isinstance(result, list) and len(result) == 1 and isinstance(result[0], list):
        result = result[0]
    return result
