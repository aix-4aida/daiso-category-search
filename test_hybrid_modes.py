"""
Hybrid Search Mode Test
Tests BM25-only, Dense-only, and Hybrid RRF modes individually.
"""
import sys
import os

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

from backend.search.config import HybridSearchConfig
from backend.search.hybrid import HybridSearchService


def main():
    config = HybridSearchConfig.from_env()
    svc = HybridSearchService(config)

    # Health check
    health = svc.health_check()
    print("=" * 70)
    print("Hybrid Search Mode Test")
    print("=" * 70)
    print(f"\nHealth: {health}")
    assert health["elasticsearch"], "Elasticsearch not healthy"
    assert health["qdrant"], "Qdrant not healthy"
    print("All services healthy!\n")

    queries = ["욕실 매트", "건전지", "볼펜"]
    modes = ["bm25_only", "dense_only", "hybrid"]

    for query in queries:
        print(f"\n{'='*70}")
        print(f"Query: '{query}'")
        print(f"{'='*70}")

        for mode in modes:
            result = svc.search(query, top_k=5, mode=mode)
            print(f"\n  [{mode.upper()}] {len(result.docs)} results | timing={result.timing_ms}")
            for i, doc in enumerate(result.docs[:3], 1):
                print(f"    {i}. [{doc.source}] {doc.title} (score={doc.score:.4f}) cat={doc.category}")

    print(f"\n{'='*70}")
    print("All hybrid search mode tests passed!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
