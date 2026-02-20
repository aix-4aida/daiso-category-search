"""
Search Case Logger
Writes one JSONL line per /v1/search request.

Output: backend/logs/search_cases.jsonl
Format per line:
{
    "case_id", "timestamp", "query",
    "retrieved_ids", "selected_id", "reason", "latency_ms",
    "candidates_scores": { doc_id: { bm25, dense, final } }
}

- dense score: Qdrant cosine similarity (0‑1, higher = more similar)
- bm25 score: raw Elasticsearch _score
- final score: RRF fusion  1/(rrf_k + rank)  (default rrf_k=60)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "search_cases.jsonl"


def write_search_log(entry: Dict[str, Any]) -> None:
    """Append one JSON line to the log file and echo to stdout."""
    try:
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat(timespec="milliseconds")

        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False, default=str)
        print(f"[SEARCH_LOG] {line}")

        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.error(f"Failed to write search log: {e}")
