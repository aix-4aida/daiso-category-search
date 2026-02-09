"""
Daiso Category Search Pipeline - Refactored (직접 함수 호출 방식)
subprocess 대신 함수 직접 호출로 오버헤드 제거
"""
import os
import sys
import time
import json
import asyncio
from pathlib import Path

# Project root 설정
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 각 모듈에서 핵심 함수 import
from backend.services_kms.stt_to_json import convert_stt_to_json
from backend.services_kms.poc_flash_test import process_data as check_intent
from backend.services_kms.simple_keyword_extractor_gemini import main as extract_keywords
from backend.services_kms.expand_keywords_comparison_gemini import main as expand_keywords
from backend.services_kms.poc_v5_experiment_phase_1 import process_benchmark_output


def get_latest_benchmark_dir(base_out_dir):
    """Find the latest timestamp directory in benchmark_out"""
    p = Path(base_out_dir)
    if not p.exists():
        return None
    subdirs = [d for d in p.iterdir() if d.is_dir() and d.name[0].isdigit()]
    if not subdirs:
        return None
    return sorted(subdirs, key=lambda x: x.name, reverse=True)[0]


def run_step(step_name: str, func, *args, **kwargs):
    """단일 스텝 실행 및 시간 측정"""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    try:
        if asyncio.iscoroutinefunction(func):
            result = asyncio.run(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] {step_name} completed. ({elapsed:.2f}s)")
        return elapsed, True
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAILURE] {step_name} failed: {e} ({elapsed:.2f}s)")
        return elapsed, False


def main():
    pipeline_start = time.time()
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    
    # 경로 설정
    AUDIO_INPUT = str(project_root / "data/test_audio/01_general/김민서_일반01.m4a")
    STT_OUTPUT = str(data_dir / "stt_output.json")
    INTENT_OUTPUT = str(data_dir / "intent_output.json")
    KEYWORD_OUTPUT = str(data_dir / "extracted_keywords.json")
    EXPANSION_OUTPUT = str(data_dir / "expansion_result.json")
    CATALOG_PATH = str(project_root / "poc/lyg/data/catalog.sqlite_export.tsv")
    FINAL_OUTPUT = str(data_dir / "final_reranked_results.json")
    
    step_times = []
    
    print("Starting Daiso Category Search Pipeline (Direct Call Mode)...")
    
    # Step 1: STT
    elapsed, success = run_step(
        "1. STT (Speech to Text)",
        convert_stt_to_json,
        AUDIO_INPUT, STT_OUTPUT
    )
    step_times.append(("STT", elapsed))
    
    # Step 2: Intent Classification
    elapsed, success = run_step(
        "2. Intent Classification",
        check_intent,
        STT_OUTPUT, INTENT_OUTPUT
    )
    step_times.append(("Intent", elapsed))
    
    # Step 3: Keyword Extraction
    elapsed, success = run_step(
        "3. Keyword Extraction",
        extract_keywords
    )
    step_times.append(("Keyword", elapsed))
    
    # Step 4: Keyword Expansion (async)
    elapsed, success = run_step(
        "4. Keyword Expansion",
        expand_keywords
    )
    step_times.append(("Expansion", elapsed))
    
    # Step 5: Benchmark (외부 명령 필요 - subprocess 유지)
    print(f"\n{'='*60}")
    print("STEP: 5. Retrieval Benchmark")
    print("(subprocess - 외부 Qdrant/Elastic 연동)")
    print(f"{'='*60}\n")
    
    import subprocess
    benchmark_start = time.time()
    benchmark_out = str(data_dir / "benchmark_out")
    testcases = str(data_dir / "expansion_result.tsv")
    
    cmd = [
        sys.executable, str(base_dir / "run_benchmark.py"),
        "--vendors", "poc/data/benchmark_out/20260205_071633/configs/vendors.yaml",
        "--pipelines", "poc/data/benchmark_out/20260205_071633/configs/pipelines.yaml",
        "--vendor-set", "ext_qdrant_elastic",
        "--pipeline", "hybrid_fuse",
        "--catalog", CATALOG_PATH,
        "--testcases", testcases,
        "--out", benchmark_out
    ]
    
    try:
        subprocess.run(cmd, check=True, env={**os.environ, "CATALOG_TSV": CATALOG_PATH})
        print(f"[SUCCESS] Benchmark completed. ({time.time() - benchmark_start:.2f}s)")
    except subprocess.CalledProcessError as e:
        print(f"[FAILURE] Benchmark failed: {e}")
    step_times.append(("Benchmark", time.time() - benchmark_start))
    
    # Step 6: Reranking
    latest_run = get_latest_benchmark_dir(benchmark_out)
    if latest_run:
        elapsed, success = run_step(
            "6. Advanced Reranking",
            process_benchmark_output,
            str(latest_run), CATALOG_PATH, FINAL_OUTPUT
        )
        step_times.append(("Rerank", elapsed))
    else:
        print("[SKIP] No benchmark output found for reranking.")
    
    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETED!")
    print(f"{'='*60}")
    
    print("\nStep Timing:")
    for name, elapsed in step_times:
        print(f"  - {name}: {elapsed:.2f}s")
    
    total_time = time.time() - pipeline_start
    print(f"\n[Total Time] {total_time:.2f} seconds ({total_time/60:.1f} minutes)")


if __name__ == "__main__":
    main()
