import os
import sys
import subprocess
from pathlib import Path

# Setup paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "poc" / "lyg" / "src"
script_path = project_root / "backend" / "services_kms" / "run_benchmark.py"

# Setup environment
env = os.environ.copy()
env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

# Arguments
args = [
    sys.executable, str(script_path),
    "--vendors", str(project_root / "poc/lyg/templates/vendors.yaml"),
    "--pipelines", str(project_root / "poc/lyg/templates/pipeline.yaml"),
    "--vendor-set", "ext_qdrant_elastic",
    "--pipeline", "hybrid_fuse",
    "--catalog", str(project_root / "backend/services_kms/data/products_exported.tsv"),
    "--testcases", str(project_root / "backend/services_kms/data/expansion_result.tsv"),
    "--out", str(project_root / "backend/services_kms/data/benchmark_out")
]

print(f"Running command: {' '.join(args)}")
print(f"PYTHONPATH: {env['PYTHONPATH']}")

try:
    result = subprocess.run(args, env=env, check=True, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except subprocess.CalledProcessError as e:
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
    sys.exit(1)
