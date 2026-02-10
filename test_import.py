import sys
import os
from pathlib import Path

# Setup paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "poc" / "lyg" / "src"
sys.path.append(str(src_path))

print(f"sys.path: {sys.path}")

try:
    import ivhl.core.pipeline
    print("Successfully imported ivhl.core.pipeline")
    print(f"File: {ivhl.core.pipeline.__file__}")
except ImportError as e:
    print(f"Failed to import: {e}")
except Exception as e:
    print(f"Error: {e}")
