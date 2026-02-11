"""
Step 4: SQLite Product Search + Gemini CoT Rerank.

- Search: backend/database/products.db (AND LIKE -> OR LIKE fallback)
- Rerank: poc/kdg/poc_v5_experiment_phase_1.advanced_rerank (Gemini 2.0 Flash)
"""

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "backend" / "database" / "products.db"
TOP_K = 50

STOPWORDS = [
    "어디", "있어요", "있나요", "어디에", "에서", "주세요",
    "찾아", "찾아줘", "찾아주세요", "좀", "요", "은", "는",
]


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _clean_query(query: str) -> list[str]:
    """Remove stopwords, return tokens with len >= 1."""
    text = query
    for sw in STOPWORDS:
        text = text.replace(sw, " ")
    tokens = [t for t in text.split() if len(t) >= 1]
    return tokens


def _search_products(query: str) -> list[dict]:
    """Search products.db: AND LIKE first, fallback to OR LIKE."""
    tokens = _clean_query(query)
    if not tokens:
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # 1st: AND LIKE
        where_and = " AND ".join(["name LIKE ?"] * len(tokens))
        params = [f"%{t}%" for t in tokens]
        sql = f"SELECT id, name, category_major, category_middle FROM products WHERE {where_and} ORDER BY id LIMIT {TOP_K}"
        cur.execute(sql, params)
        rows = cur.fetchall()

        # 2nd: OR LIKE fallback
        if not rows:
            where_or = " OR ".join(["name LIKE ?"] * len(tokens))
            sql = f"SELECT id, name, category_major, category_middle FROM products WHERE {where_or} ORDER BY id LIMIT {TOP_K}"
            cur.execute(sql, params)
            rows = cur.fetchall()

        candidates = []
        for r in rows:
            major = r["category_major"] or ""
            middle = r["category_middle"] or ""
            candidates.append({
                "id": r["id"],
                "name": r["name"],
                "desc": f"{major} {middle}".strip(),
            })
        return candidates
    finally:
        conn.close()


def _rerank(query: str, candidates: list[dict]):
    """Call advanced_rerank from poc/kdg. Returns result dict or raises."""
    kdg_path = str(PROJECT_ROOT / "poc" / "kdg")
    added = False
    if kdg_path not in sys.path:
        sys.path.insert(0, kdg_path)
        added = True

    try:
        from poc_v5_experiment_phase_1 import advanced_rerank

        result = advanced_rerank(query, candidates)

        if not isinstance(result, dict):
            raise ValueError(f"advanced_rerank returned non-dict: {type(result)}")
        if "selected_id" not in result:
            raise ValueError(f"advanced_rerank result missing 'selected_id': {result}")

        return result
    finally:
        if added:
            try:
                sys.path.remove(kdg_path)
            except ValueError:
                pass


def run_step4(query: str, run_id: str) -> dict:
    """Step 4: SQLite Search + Gemini Rerank.

    Returns search_result dict (also saved to outputs/{run_id}/search.json).
    """
    print(f"\n{'='*60}")
    print("  STEP 4: Search + Rerank")
    print(f"{'='*60}")

    t_start = time.time()
    run_dir = PROJECT_ROOT / "outputs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    search_json_path = run_dir / "search.json"

    # --- A. SQLite Search ---
    try:
        candidates = _search_products(query)
    except Exception as e:
        elapsed = int((time.time() - t_start) * 1000)
        fail_result = {
            "status": "fail",
            "query": query,
            "retrieval": {"method": "sqlite_like", "top_k": TOP_K, "candidate_count": 0},
            "candidates_preview": [],
            "rerank": {"provider": "gemini", "error": f"DB search failed: {e}"},
            "latency_ms": elapsed,
        }
        _save_json(search_json_path, fail_result)
        print(f"[FAIL] step4 - DB search error: {e}")
        return fail_result

    candidate_count = len(candidates)
    top_ids = [c["id"] for c in candidates[:5]]
    print(f"  Search: {candidate_count} candidates for '{query}' (tokens: {_clean_query(query)})")

    # --- B. API Key Check (before importing reranker module) ---
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        elapsed = int((time.time() - t_start) * 1000)
        fail_result = {
            "status": "fail",
            "query": query,
            "retrieval": {"method": "sqlite_like", "top_k": TOP_K, "candidate_count": candidate_count},
            "candidates_preview": candidates[:3],
            "rerank": {"provider": "gemini", "error": "Missing GEMINI_API_KEY/GOOGLE_API_KEY"},
            "latency_ms": elapsed,
        }
        _save_json(search_json_path, fail_result)
        print("[FAIL] step4 - GEMINI_API_KEY/GOOGLE_API_KEY not set")
        return fail_result

    # --- C. Rerank ---
    try:
        rerank_result = _rerank(query, candidates)
    except Exception as e:
        elapsed = int((time.time() - t_start) * 1000)
        fail_result = {
            "status": "fail",
            "query": query,
            "retrieval": {"method": "sqlite_like", "top_k": TOP_K, "candidate_count": candidate_count},
            "candidates_preview": candidates[:3],
            "rerank": {"provider": "gemini", "error": str(e)},
            "latency_ms": elapsed,
        }
        _save_json(search_json_path, fail_result)
        print(f"[FAIL] step4 - Rerank error: {e}")
        return fail_result

    # --- D. Success ---
    elapsed = int((time.time() - t_start) * 1000)
    selected_id = rerank_result.get("selected_id")

    ok_result = {
        "status": "ok",
        "query": query,
        "retrieval": {"method": "sqlite_like", "top_k": TOP_K, "candidate_count": candidate_count},
        "candidates": candidates,
        "rerank": {
            "provider": "gemini",
            "selected_id": selected_id,
            "top_ids": top_ids,
            "reason": rerank_result.get("reason", ""),
        },
        "latency_ms": elapsed,
    }
    _save_json(search_json_path, ok_result)
    print(f"[OK] step4 - selected_id={selected_id}, {candidate_count} candidates, {elapsed}ms")
    return ok_result
