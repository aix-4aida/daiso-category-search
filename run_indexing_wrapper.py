import sys
import os
from pathlib import Path

# Add script dir to path
script_dir = Path("c:/kms/daiso-category-search/poc/lyg/scripts")
sys.path.append(str(script_dir))

# Redirect output
sys.stdout = open("indexing_result.txt", "w", encoding="utf-8")
sys.stderr = sys.stdout

print("Starting indexing...")
try:
    import index_hybrid_from_catalog_v3
    index_hybrid_from_catalog_v3.main()
    print("Indexing completed successfully.")
except Exception as e:
    print(f"Indexing failed: {e}")
    import traceback
    traceback.print_exc()
