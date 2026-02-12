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
from backend.services_kms.export_db_to_tsv import export_db_to_tsv
from dotenv import load_dotenv

# Load env immediately
load_dotenv()

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


async def run_step(step_name: str, func, *args, **kwargs):
    """단일 스텝 실행 및 시간 측정 (Async)"""
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] {step_name} completed. ({elapsed:.2f}s)")
        return elapsed, True, result
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[FAILURE] {step_name} failed: {e} ({elapsed:.2f}s)")
        return elapsed, False, None


async def run_pipeline_for_voice(audio_path: str, stt_text: str, stt_elapsed: float = 0.0) -> dict:
    """
    음성 검색용 파이프라인 실행 (Async)
    """
    import json
    
    pipeline_start = time.time()
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 경로 설정
    STT_OUTPUT = str(data_dir / "stt_output.json")
    INTENT_OUTPUT = str(data_dir / "intent_output.json")
    KEYWORD_OUTPUT = str(data_dir / "extracted_keywords.json")
    EXPANSION_OUTPUT = str(data_dir / "expansion_result.json")
    CATALOG_PATH = str(project_root / "backend/services_kms/data/products_exported.tsv")
    FINAL_OUTPUT = str(data_dir / "final_reranked_results.json")
    
    # Ensure fresh data from DB
    if not export_db_to_tsv():
        print("⚠️ Warning: DB export failed. Using existing TSV if available.")
    
    step_times = []
    
    # Add STT time to step_times
    step_times.append(("STT", stt_elapsed))
    
    results = {
        "stt_text": stt_text,
        "audio_path": audio_path,
        "stt_time_seconds": stt_elapsed
    }
    
    print(f"\n🚀 Starting Voice Search Pipeline for: '{stt_text}'")
    
    # Step 1: STT 결과 저장
    stt_data = {
        "id": 1,
        "filename": Path(audio_path).name,
        "utterance": stt_text
    }
    with open(STT_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump([stt_data], f, ensure_ascii=False, indent=2)
    
    # Step 2: Intent Classification
    elapsed, success, _ = await run_step(
        "2. Intent Classification",
        check_intent,
        STT_OUTPUT, INTENT_OUTPUT
    )
    step_times.append(("Intent", elapsed))
    
    # Step 3: Keyword Extraction
    elapsed, success, _ = await run_step(
        "3. Keyword Extraction",
        extract_keywords
    )
    
    try:
        items = None
        with open(KEYWORD_OUTPUT, "r", encoding="utf-8") as f:
            items = json.load(f)
        if items and len(items) > 0:
            # Check different possible structures (it was in extraction.keyword)
            extraction = items[0].get("extraction", {})
            keyword = extraction.get("keyword", "")
            
            # Clean up slash-separated keywords (e.g. "마스크팩/시트마스크" -> "마스크팩")
            if "/" in keyword:
                keyword = keyword.split("/")[0].strip()
            results["keyword"] = keyword
    except Exception as e:
        print(f"⚠️ Error reading keyword output: {e}")
    
    step_times.append(("Keyword", elapsed))
    
    # Step 4: Keyword Expansion
    elapsed, success, _ = await run_step(
        "4. Keyword Expansion",
        expand_keywords
    )
    step_times.append(("Expansion", elapsed))
    
    # Step 5: Benchmark
    print(f"\n{'='*60}")
    print("STEP: 5. Retrieval Benchmark")
    print(f"{'='*60}\n")
    
    import subprocess
    benchmark_start = time.time()
    benchmark_out = str(data_dir / "benchmark_out")
    testcases = str(data_dir / "expansion_result.tsv")
    
    cmd = [
        sys.executable, str(base_dir / "run_benchmark.py"),
        "--vendors", str(project_root / "poc/lyg/templates/vendors.yaml"),
        "--pipelines", str(project_root / "poc/lyg/templates/pipeline.yaml"),
        "--vendor-set", "ext_qdrant_elastic",
        "--pipeline", "hybrid_fuse",
        "--catalog", CATALOG_PATH,
        "--testcases", testcases,
        "--out", benchmark_out
    ]
    
    env = os.environ.copy()
    env["CATALOG_TSV"] = CATALOG_PATH
    src_path = str(project_root / "poc/lyg/src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path

    # Subprocess는 블로킹이므로 비동기로 실행하거나, 짧으면 그냥 실행
    # 여기서는 그냥 실행 (오래 걸리면 loop.run_in_executor 사용 권장)
    try:
        subprocess.run(cmd, check=True, env=env)
        print(f"[SUCCESS] Benchmark completed. ({time.time() - benchmark_start:.2f}s)")
    except subprocess.CalledProcessError as e:
        print(f"[FAILURE] Benchmark failed: {e}")
    except Exception as e:
        print(f"[ERROR] Benchmark execution error: {e}")
    
    step_times.append(("Benchmark", time.time() - benchmark_start))
    
    # Step 6: Reranking
    latest_run = get_latest_benchmark_dir(benchmark_out)
    if latest_run:
        elapsed, success, _ = await run_step(
            "6. Advanced Reranking",
            process_benchmark_output,
            str(latest_run), CATALOG_PATH, FINAL_OUTPUT
        )
        step_times.append(("Rerank", elapsed))
        
        if Path(FINAL_OUTPUT).exists():
            with open(FINAL_OUTPUT, 'r', encoding='utf-8') as f:
                results["final_results"] = json.load(f)
    else:
        print("[SKIP] No benchmark output found for reranking.")
    
    total_time = time.time() - pipeline_start
    results["step_times"] = step_times
    results["total_time_seconds"] = total_time
    
    print(f"\nVOICE SEARCH PIPELINE COMPLETED! ({total_time:.2f}s)")
    return results


async def main_async():
    pipeline_start = time.time()
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    
    # 경로 설정
    AUDIO_INPUT = str(project_root / "data/test_audio/01_general/김민서_일반01.m4a")
    STT_OUTPUT = str(data_dir / "stt_output.json")
    INTENT_OUTPUT = str(data_dir / "intent_output.json")
    # ... (나머지 경로는 run_pipeline_for_voice와 동일하므로 생략하거나 재사용 가능하지만,
    # 편의상 직접 구현되어 있던 main 로직을 async로 변환)
    
    # 여기서는 main 함수가 CLI용 테스트이므로 run_pipeline_for_voice를 호출하는 게 깔끔함
    # 단, STT는 이미 되었다고 가정하거나 모킹해야 함.
    # 기존 main()은 stt_to_json부터 실행했음.
    
    print("Starting Daiso Category Search Pipeline (Async Direct Call)...")
    
    # STT 실행
    # 기본은 whisper이지만 필요시 google로 변경 가능
    elapsed, success, _ = await run_step(
        "1. STT", convert_stt_to_json, AUDIO_INPUT, STT_OUTPUT, provider="google" 
    )
    
    # 이후 단계는 run_pipeline_for_voice를 재사용하면 좋겠지만, 
    # run_pipeline_for_voice는 STT 이후부터 시작함.
    # 코드 중복을 피하기 위해 여기서는 run_pipeline_for_voice 호출로 대체 가능?
    # 하지만 run_pipeline_for_voice는 audio_path와 text를 인자로 받음.
    
    # STT 결과 읽기
    with open(STT_OUTPUT, 'r', encoding='utf-8') as f:
        stt_data = json.load(f)
        text = stt_data[0]['utterance']
    
    # 파이프라인 호출
    await run_pipeline_for_voice(AUDIO_INPUT, text, elapsed)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
