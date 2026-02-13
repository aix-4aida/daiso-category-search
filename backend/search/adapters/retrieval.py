from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import requests

from backend.search.core.types import Document, ScoredDoc


class VectorRetriever(Protocol):
    def query(self, qvec: List[float], *, top_k: int) -> List[ScoredDoc]:
        ...


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    denom = na * nb
    if denom == 0.0:
        return 0.0
    return float(s / denom)


@dataclass
class BruteForceVectorRetriever:
    """
    Local dense retriever for debugging / baseline.
    Uses doc_id as key.
    """
    docs: List[Document]
    doc_vecs: Dict[str, List[float]]

    def query(self, qvec: List[float], *, top_k: int) -> List[ScoredDoc]:
        scored: List[ScoredDoc] = []
        for d in self.docs:
            v = self.doc_vecs.get(d.doc_id)
            if v is None:
                continue
            score = _cosine(qvec, v)
            scored.append(ScoredDoc(doc_id=d.doc_id, score=score, source="dense"))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[: int(top_k)]


@dataclass
class QdrantVectorRetriever:
    """
    Qdrant vector retriever using REST API.
    """
    url: str                      # ex) http://localhost:6333
    collection_name: str
    timeout_s: int = 5

    def check_connection(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            url = f"{self.url.rstrip('/')}/"
            r = requests.get(url, timeout=self.timeout_s)
            return r.status_code == 200
        except Exception:
            return False

    def query(self, qvec: List[float], *, top_k: int) -> List[ScoredDoc]:
        endpoint = f"{self.url.rstrip('/')}/collections/{self.collection_name}/points/search"
        body = {
            "vector": qvec,
            "limit": int(top_k),
            "with_payload": True
        }
        
        try:
            r = requests.post(endpoint, json=body, timeout=self.timeout_s)
            if r.status_code != 200:
                print(f"⚠️ Qdrant search failed: {r.status_code} {r.text}")
                return []
            
            data = r.json()
            hits = data.get("result", [])
            
            out: List[ScoredDoc] = []
            for rank, h in enumerate(hits, start=1):
                doc_id = str(h.get("id") or "")
                score = float(h.get("score") or 0.0)
                if doc_id:
                    out.append(ScoredDoc(doc_id=doc_id, score=score, source="dense"))
            return out
        except Exception as e:
            print(f"❌ Qdrant query error: {e}")
            return []

@dataclass
class ChromaVectorRetriever:
    """
    ChromaDB vector retriever.
    """
    collection_name: str
    persist_directory: Optional[str] = None
    _client: Any = None
    _collection: Any = None

    def __post_init__(self):
        import chromadb
        if self.persist_directory:
            self._client = chromadb.PersistentClient(path=self.persist_directory)
        else:
            self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(name=self.collection_name)

    def query(self, qvec: List[float], *, top_k: int) -> List[ScoredDoc]:
        results = self._collection.query(
            query_embeddings=[qvec],
            n_results=int(top_k),
            include=["metadatas", "distances"]
        )
        
        out: List[ScoredDoc] = []
        # Chroma returns results in nested lists
        if results['ids']:
            ids = results['ids'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{} for _ in ids]
            distances = results['distances'][0] if results['distances'] else [0.0 for _ in ids]
            
            for doc_id, meta, dist in zip(ids, metadatas, distances):
                # Chroma distance is often L2 or cosine distance. 
                # ScoredDoc usually expects similarity (higher is better). 
                # For simplicity, we just pass distance if not clarified, but usually similarity = 1 - distance
                score = 1.0 - dist if dist <= 1.0 else 0.0
                out.append(ScoredDoc(doc_id=doc_id, score=score, source="dense"))
        
        return out
