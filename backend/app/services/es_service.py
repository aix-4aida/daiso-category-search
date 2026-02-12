"""Elasticsearch service - BM25 text search"""
import asyncio
import logging
from functools import partial

from elasticsearch import Elasticsearch

from app.config import settings

logger = logging.getLogger(__name__)

INDEX_NAME = "daiso_products"

INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "korean": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "text", "analyzer": "korean"},
            "category_major": {"type": "keyword"},
            "category_middle": {"type": "keyword"},
            "price": {"type": "integer"},
        }
    },
}


def _get_client() -> Elasticsearch:
    """Create Elasticsearch client"""
    return Elasticsearch(
        hosts=[settings.ELASTIC_URL],
        http_auth=(settings.ELASTIC_USERNAME, settings.ELASTIC_PASSWORD),
    )


async def check_es_health() -> bool:
    """Check if Elasticsearch is reachable"""
    try:
        client = _get_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, client.ping)
        client.close()
        return bool(result)
    except Exception:
        return False


class ESService:
    """Elasticsearch BM25 search service"""

    def __init__(self) -> None:
        self.client: Elasticsearch | None = None

    def _ensure_client(self) -> Elasticsearch:
        if self.client is None:
            self.client = _get_client()
        return self.client

    async def create_index(self) -> None:
        """Create the products index if it doesn't exist"""
        client = self._ensure_client()
        loop = asyncio.get_event_loop()
        exists = await loop.run_in_executor(
            None, partial(client.indices.exists, index=INDEX_NAME)
        )
        if not exists:
            await loop.run_in_executor(
                None,
                partial(client.indices.create, index=INDEX_NAME, body=INDEX_SETTINGS),
            )
            logger.info(f"Created index: {INDEX_NAME}")

    async def index_product(self, product: dict) -> None:
        """Index a single product"""
        client = self._ensure_client()
        body = {
            "id": product["id"],
            "name": product["name"],
            "category_major": product.get("category_major", ""),
            "category_middle": product.get("category_middle", ""),
            "price": product.get("price", 0),
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(client.index, index=INDEX_NAME, id=product["id"], body=body),
        )

    async def bulk_index(self, products: list[dict]) -> int:
        """Bulk index products"""
        client = self._ensure_client()
        actions = []
        for p in products:
            actions.append({"index": {"_index": INDEX_NAME, "_id": p["id"]}})
            actions.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "category_major": p.get("category_major", ""),
                    "category_middle": p.get("category_middle", ""),
                    "price": p.get("price", 0),
                }
            )
        if actions:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, partial(client.bulk, body=actions, refresh=True)
            )
        return len(products)

    async def search(self, keywords: list[str], size: int = 30) -> list[dict]:
        """BM25 search by keywords, returns top candidates"""
        client = self._ensure_client()
        query_string = " ".join(keywords)
        body = {
            "query": {
                "multi_match": {
                    "query": query_string,
                    "fields": ["name^3", "category_major", "category_middle"],
                    "type": "best_fields",
                }
            },
            "size": size,
        }
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, partial(client.search, index=INDEX_NAME, body=body)
            )
            hits = result.get("hits", {}).get("hits", [])
            return [
                {**hit["_source"], "score": hit["_score"]} for hit in hits
            ]
        except Exception as e:
            logger.error(f"ES search failed: {e}")
            return []

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
