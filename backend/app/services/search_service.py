"""Search service - hybrid search orchestration"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.models.schemas import SearchResponse, ProductResult, MapInfo, QueryInfo
from app.services.gemini_service import GeminiService
from app.services.es_service import ESService
from app.services.qdrant_service import QdrantService
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


class SearchService:
    """Hybrid search orchestration: Gemini intent → ES + Qdrant → Gemini rerank"""

    def __init__(self) -> None:
        self.gemini = GeminiService()
        self.es = ESService()
        self.qdrant = QdrantService()
        self.product_service = ProductService()

    async def search(self, query: str) -> SearchResponse:
        """Full search pipeline"""
        # Step 1: Gemini intent analysis
        intent_result = await self.gemini.analyze_intent(query)
        keywords = intent_result.get("keywords", [query])

        # Step 2: Parallel search - ES BM25 + Qdrant vector
        es_results, qdrant_results = await asyncio.gather(
            self._search_es(keywords),
            self._search_qdrant(keywords),
            return_exceptions=True,
        )

        if isinstance(es_results, Exception):
            logger.error(f"ES search error: {es_results}")
            es_results = []
        if isinstance(qdrant_results, Exception):
            logger.error(f"Qdrant search error: {qdrant_results}")
            qdrant_results = []

        # Step 3: Merge results (RRF fusion)
        candidates = self._fuse_results(es_results, qdrant_results)

        if not candidates:
            # Fallback to SQLite LIKE search
            candidates = self._fallback_search(keywords)

        # Step 4: Gemini reranking → Top 3
        if len(candidates) > 3:
            selected_ids = await self.gemini.rerank(query, keywords, candidates)
            top_results = self._order_by_ids(candidates, selected_ids)
        else:
            top_results = candidates[:3]

        # Build response
        product_results = []
        for i, p in enumerate(top_results):
            product_results.append(
                ProductResult(
                    id=p.get("id", 0),
                    rank=i + 1,
                    name=p.get("name", ""),
                    price=p.get("price", 0),
                    image_url=f"/static/images/{p.get('image_name', '')}",
                    category_major=p.get("category_major"),
                    category_middle=p.get("category_middle"),
                    score=p.get("score", 0.0),
                )
            )

        map_info = None
        if product_results:
            first = product_results[0]
            map_info = MapInfo(
                section=first.category_major or "",
                map_image="/static/maps/store.png",
            )

        return SearchResponse(
            results=product_results,
            map_info=map_info,
            query_info=QueryInfo(
                original=query,
                intent=intent_result.get("intent", "search"),
                keywords=keywords,
            ),
        )

    async def _search_es(self, keywords: list[str]) -> list[dict]:
        """Search via Elasticsearch BM25"""
        return await self.es.search(keywords)

    async def _search_qdrant(self, keywords: list[str]) -> list[dict]:
        """Search via Qdrant vector similarity"""
        try:
            # Generate query embedding using CLIP
            from database.embeddings import get_text_embedding
            import pickle
            import numpy as np

            query_text = " ".join(keywords)
            embedding_bytes = get_text_embedding(query_text)
            embedding = pickle.loads(embedding_bytes)
            if isinstance(embedding, np.ndarray):
                vector = embedding.tolist()
            else:
                vector = list(embedding)
            return await self.qdrant.search(vector)
        except Exception as e:
            logger.error(f"Qdrant search prep failed: {e}")
            return []

    def _fuse_results(
        self, es_results: list[dict], qdrant_results: list[dict]
    ) -> list[dict]:
        """Reciprocal Rank Fusion (RRF) to merge ES and Qdrant results"""
        k = 60  # RRF constant
        scores: dict[int, float] = {}
        product_map: dict[int, dict] = {}

        for rank, item in enumerate(es_results):
            pid = item["id"]
            scores[pid] = scores.get(pid, 0) + 1.0 / (k + rank + 1)
            product_map[pid] = item

        for rank, item in enumerate(qdrant_results):
            pid = item["id"]
            scores[pid] = scores.get(pid, 0) + 1.0 / (k + rank + 1)
            if pid not in product_map:
                product_map[pid] = item

        # Sort by RRF score descending
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
        result = []
        for pid in sorted_ids:
            p = product_map[pid]
            p["score"] = scores[pid]
            result.append(p)
        return result

    def _fallback_search(self, keywords: list[str]) -> list[dict]:
        """Fallback to SQLite LIKE search"""
        all_results = []
        for kw in keywords:
            results = self.product_service.search_products(kw)
            all_results.extend(results)
        # Deduplicate
        seen = set()
        unique = []
        for r in all_results:
            if r["id"] not in seen:
                seen.add(r["id"])
                r["score"] = 0.5
                unique.append(r)
        return unique[:30]

    def _order_by_ids(
        self, candidates: list[dict], selected_ids: list[int]
    ) -> list[dict]:
        """Order candidates by selected IDs from reranking"""
        id_map = {c["id"]: c for c in candidates}
        result = []
        for pid in selected_ids:
            if pid in id_map:
                result.append(id_map[pid])
        # Fill up to 3 if reranking returned fewer
        if len(result) < 3:
            for c in candidates:
                if c["id"] not in {r["id"] for r in result}:
                    result.append(c)
                if len(result) >= 3:
                    break
        return result[:3]
