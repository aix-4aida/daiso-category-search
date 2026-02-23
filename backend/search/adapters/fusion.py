from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from backend.search.core.types import ScoredDoc


def rrf_fusion(dense: List[ScoredDoc], sparse: List[ScoredDoc], *, rrf_k: int = 60, top_k: int = 50, sparse_weight: float = 1.0) -> List[ScoredDoc]:
    """Reciprocal Rank Fusion.

    score(doc) = sum(1/(rrf_k + rank))
    """
    scores: Dict[str, float] = {}
    extra_info: Dict[str, Dict[str, str]] = {}
    
    for rank, sd in enumerate(dense, start=1):
        scores[sd.doc_id] = scores.get(sd.doc_id, 0.0) + 1.0 / (rrf_k + rank)
        extra_info.setdefault(sd.doc_id, {})["vector_score"] = f"{sd.score:.4f}"
        
    for rank, sd in enumerate(sparse, start=1):
        scores[sd.doc_id] = scores.get(sd.doc_id, 0.0) + sparse_weight / (rrf_k + rank)
        extra_info.setdefault(sd.doc_id, {})["bm25_score"] = f"{sd.score:.4f}"
        
    merged = []
    for k, v in scores.items():
        doc_extra = extra_info.get(k, {})
        merged.append(ScoredDoc(doc_id=k, score=v, source="fused", extra=doc_extra))

    merged.sort(key=lambda x: x.score, reverse=True)
    return merged[:top_k]


def weighted_fusion(dense: List[ScoredDoc], sparse: List[ScoredDoc], *, alpha: float = 0.5, top_k: int = 50) -> List[ScoredDoc]:
    """Weighted sum after per-list min-max normalization."""

    def norm(lst: List[ScoredDoc], label: str) -> Dict[str, float]:
        if not lst:
            return {}
        mx = max(x.score for x in lst)
        mn = min(x.score for x in lst)
        if mx <= mn:
            return {x.doc_id: 0.0 for x in lst}
        return {x.doc_id: (x.score - mn) / (mx - mn) for x in lst}

    nd = norm(dense, "vector")
    ns = norm(sparse, "bm25")
    keys = set(nd.keys()) | set(ns.keys())
    scores: Dict[str, float] = {}
    extra_info: Dict[str, Dict[str, str]] = {}
    
    # Store raw scores
    for sd in dense:
        extra_info.setdefault(sd.doc_id, {})["vector_score"] = f"{sd.score:.4f}"
    for sd in sparse:
        extra_info.setdefault(sd.doc_id, {})["bm25_score"] = f"{sd.score:.4f}"
        
    for k in keys:
        scores[k] = alpha * nd.get(k, 0.0) + (1 - alpha) * ns.get(k, 0.0)
        
    merged = [ScoredDoc(doc_id=k, score=v, source="fused", extra=extra_info.get(k, {})) for k, v in scores.items()]
    merged.sort(key=lambda x: x.score, reverse=True)
    return merged[:top_k]
