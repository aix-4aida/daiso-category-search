from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from backend.search.core.types import ScoredDoc


def rrf_fusion(dense: List[ScoredDoc], sparse: List[ScoredDoc], *, rrf_k: int = 60, top_k: int = 50, sparse_weight: float = 1.0) -> List[ScoredDoc]:
    """Reciprocal Rank Fusion with optional sparse (BM25) weighting.

    score(doc) = sum(weight * 1/(rrf_k + rank))
    
    Args:
        sparse_weight: multiplier for sparse (BM25) results. Set > 1.0 to
            boost keyword-matched results over semantic vector results.
    """
    scores: Dict[str, float] = {}
    # Dense (vector) results — weight 1.0
    for rank, sd in enumerate(dense, start=1):
        scores[sd.doc_id] = scores.get(sd.doc_id, 0.0) + 1.0 / (rrf_k + rank)
    # Sparse (BM25) results — boosted weight
    for rank, sd in enumerate(sparse, start=1):
        scores[sd.doc_id] = scores.get(sd.doc_id, 0.0) + sparse_weight / (rrf_k + rank)
    merged = [ScoredDoc(doc_id=k, score=v, source="fused") for k, v in scores.items()]
    merged.sort(key=lambda x: x.score, reverse=True)
    return merged[:top_k]


def weighted_fusion(dense: List[ScoredDoc], sparse: List[ScoredDoc], *, alpha: float = 0.5, top_k: int = 50) -> List[ScoredDoc]:
    """Weighted sum after per-list min-max normalization."""

    def norm(lst: List[ScoredDoc]) -> Dict[str, float]:
        if not lst:
            return {}
        mx = max(x.score for x in lst)
        mn = min(x.score for x in lst)
        if mx <= mn:
            return {x.doc_id: 0.0 for x in lst}
        return {x.doc_id: (x.score - mn) / (mx - mn) for x in lst}

    nd = norm(dense)
    ns = norm(sparse)
    keys = set(nd.keys()) | set(ns.keys())
    scores: Dict[str, float] = {}
    for k in keys:
        scores[k] = alpha * nd.get(k, 0.0) + (1 - alpha) * ns.get(k, 0.0)
    merged = [ScoredDoc(doc_id=k, score=v, source="fused") for k, v in scores.items()]
    merged.sort(key=lambda x: x.score, reverse=True)
    return merged[:top_k]
