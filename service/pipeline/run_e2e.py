"""
E2E PoC Pipeline Orchestrator.

Usage:
    python -m service.pipeline.run_e2e --text "볼펜 어디있어요"
    python -m service.pipeline.run_e2e --text "볼펜 어디있어요" --mode subprocess
    python -m service.pipeline.run_e2e --text "볼펜 어디있어요" "파란색 수건 찾아주세요"
    python -m service.pipeline.run_e2e --audio_path "data/test_audio/sample.wav"
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from service.pipeline.stt_adapter import transcribe_audio, transcribe_text
from service.pipeline.step4_search_rerank import run_step4
from service.pipeline.steps_inprocess import (
    run_step1_inprocess,
    run_step2_inprocess,
    run_step3_inprocess,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # daiso-category-search/

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")

POC_DATA_DIR = PROJECT_ROOT / "poc" / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Files that downstream PoC scripts read/write
WATCHED_FILES = [
    POC_DATA_DIR / "stt_output.json",
    POC_DATA_DIR / "intent_output.json",
    POC_DATA_DIR / "extracted_keywords.json",
    POC_DATA_DIR / "expansion_result.json",
]

# Pipeline step definitions: (step_name, script_path, expected_output)
STEPS = [
    (
        "intent",
        "poc/intent/poc_flash_test.py",
        POC_DATA_DIR / "intent_output.json",
    ),
    (
        "keyword_extract",
        "poc/kms/simple_keyword_extractor_gemini.py",
        POC_DATA_DIR / "extracted_keywords.json",
    ),
    (
        "keyword_expand",
        "poc/kms/expand_keywords_comparison_gemini.py",
        POC_DATA_DIR / "expansion_result.json",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _warn_overwrite():
    """Check watched files and print overwrite warnings."""
    for fp in WATCHED_FILES:
        if fp.exists():
            print(f"[WARN] 덮어씀: {fp.relative_to(PROJECT_ROOT)}")


def _run_step(step_name: str, script_rel: str, expected_output: Path, run_dir: Path):
    """Run a subprocess step with log capture and failure detection."""
    script_abs = str(PROJECT_ROOT / script_rel)
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  STEP: {step_name}")
    print(f"  Script: {script_rel}")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, script_abs],
        capture_output=True,
        cwd=str(PROJECT_ROOT),
    )

    # Decode stdout/stderr (Windows cp949 fallback)
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

    # Save logs
    (logs_dir / f"{step_name}.out.log").write_text(stdout, encoding="utf-8")
    (logs_dir / f"{step_name}.err.log").write_text(stderr, encoding="utf-8")

    # Failure: non-zero exit code
    if result.returncode != 0:
        print(f"[FAIL] {step_name}  - returncode={result.returncode}")
        if stderr:
            for line in stderr.strip().splitlines()[-10:]:
                print(f"  stderr> {line}")
        sys.exit(1)

    # Failure: expected output file missing
    if not expected_output.exists():
        print(f"[FAIL] {step_name}  - 기대 출력 파일 없음: {expected_output.relative_to(PROJECT_ROOT)}")
        sys.exit(1)

    print(f"[OK] {step_name}")


# ---------------------------------------------------------------------------
# Step implementations
# ---------------------------------------------------------------------------

def step0_transcript(texts: list[str] | None, audio_path: str | None, run_dir: Path) -> str:
    """Step 0: Convert input to transcript.json contract + poc/data/stt_output.json."""
    print(f"\n{'='*60}")
    print("  STEP 0: Input → transcript.json")
    print(f"{'='*60}")

    _warn_overwrite()

    if texts:
        items = transcribe_text(texts)
    else:
        items = transcribe_audio(audio_path)

    # Save to both locations
    poc_path = POC_DATA_DIR / "stt_output.json"
    poc_path.parent.mkdir(parents=True, exist_ok=True)
    _save_json(poc_path, items)

    transcript_path = run_dir / "transcript.json"
    _save_json(transcript_path, items)

    print(f"[OK] step0  - {len(items)}건 저장")
    return str(poc_path)


def step1_intent(run_dir: Path, run_id: str):
    """Step 1: Intent classification via poc/intent/poc_flash_test.py."""
    poc_stt = POC_DATA_DIR / "stt_output.json"
    if not poc_stt.exists():
        print(f"[FAIL] step1  - poc/data/stt_output.json 없음")
        sys.exit(1)

    step_name, script, expected = STEPS[0]
    _run_step(step_name, script, expected, run_dir)

    # Copy raw output to stages/
    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(expected, stages_dir / "intent_output.json")

    # Convert to nlu.json contract
    raw = _load_json(expected)
    nlu_items = []
    for item in raw:
        iv = item.get("intent_validation", {})
        is_valid = iv.get("is_valid", "N")
        nlu_items.append({
            "request_id": f"{run_id}_{item.get('id', 0)}",
            "intent": "PRODUCT_LOCATION" if is_valid == "Y" else "UNSUPPORTED",
            "slots": {
                "item": None,
                "attrs": [],
                "category_hint": None,
                "query_rewrite": None,
            },
            "expanded_keywords": [],
            "needs_clarification": False,
            "latency_ms": iv.get("latency_ms", 0),
        })
    _save_json(run_dir / "nlu.json", nlu_items)


def step2_keyword_extract(run_dir: Path):
    """Step 2: Keyword extraction via poc/kms/simple_keyword_extractor_gemini.py."""
    step_name, script, expected = STEPS[1]
    _run_step(step_name, script, expected, run_dir)

    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(expected, stages_dir / "extracted_keywords.json")
    shutil.copy2(expected, run_dir / "keywords.json")


def step3_keyword_expand(run_dir: Path):
    """Step 3: Keyword expansion via poc/kms/expand_keywords_comparison_gemini.py."""
    step_name, script, expected = STEPS[2]
    _run_step(step_name, script, expected, run_dir)

    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(expected, stages_dir / "expansion_result.json")
    shutil.copy2(expected, run_dir / "expansion.json")


def _safe_int(v):
    try:
        return int(v)
    except Exception:
        return None


def _build_item_message(search_data: dict) -> str:
    """
    Step4(search.json) 결과를 item.message에 반영하기 위한 문구 생성.
    """
    status = (search_data or {}).get("status")
    if status != "ok":
        err = ((search_data or {}).get("rerank") or {}).get("error") or "unknown"
        return f"검색/리랭킹 실패: {err}"

    retrieval = (search_data or {}).get("retrieval") or {}
    method = retrieval.get("method", "unknown")
    cand_cnt = retrieval.get("candidate_count", len((search_data or {}).get("candidates", [])))

    rerank = (search_data or {}).get("rerank") or {}
    selected_id = rerank.get("selected_id")
    top_ids = rerank.get("top_ids") or []

    # selected_id가 None이면(후보군 없거나 모델이 선택 못함)
    if selected_id in (None, "", "null"):
        return f"검색 완료(BM25/DB: {method}, 후보 {cand_cnt}개). 리랭커가 최종 상품을 선택하지 못했습니다."

    return f"검색 완료({method}, 후보 {cand_cnt}개) → 리랭킹 Top1 id={selected_id} (Top3={top_ids[:3]})"


def _resolve_query(run_dir: Path, original_texts: list[str] | None) -> str:
    """args.text 있으면 원본 사용, 없으면 nlu.json fallback."""
    # 1) 원본 텍스트 우선
    if original_texts:
        return original_texts[0]

    # 2) nlu.json fallback
    nlu_path = run_dir / "nlu.json"
    if nlu_path.exists():
        nlu_items = _load_json(nlu_path)
        for item in nlu_items:
            slots = item.get("slots", {})
            qr = slots.get("query_rewrite")
            if qr:
                return str(qr)
            it = slots.get("item")
            if it:
                return str(it)

    return ""


def step5_final_output(run_dir: Path, run_id: str, elapsed_ms: int, timing_ms: dict | None = None):
    """Step 5: Aggregate results into final_response.json."""
    print(f"\n{'='*60}")
    print("  STEP 5: Final Output")
    print(f"{'='*60}")

    # Read nlu.json for intent info
    nlu_path = run_dir / "nlu.json"
    nlu_items = _load_json(nlu_path) if nlu_path.exists() else []

    # Read expansion.json for keyword info
    expansion_path = run_dir / "expansion.json"
    expansion_items = _load_json(expansion_path) if expansion_path.exists() else []

    # Read search.json (Step 4 result)
    search_path = run_dir / "search.json"
    search_data = _load_json(search_path) if search_path.exists() else {"status": "skipped"}

    # selected 상품 찾기 (candidate에서 name/desc 매칭)
    selected_name = None
    selected_desc = None
    selected_id = None

    if isinstance(search_data, dict) and search_data.get("status") == "ok":
        selected_id = search_data.get("rerank", {}).get("selected_id")
        selected_id_int = _safe_int(selected_id)
        for c in search_data.get("candidates", []):
            if _safe_int(c.get("id")) == selected_id_int:
                selected_name = c.get("name")
                selected_desc = c.get("desc")
                break

    # Build item-level summary
    items = []
    for idx, nlu_item in enumerate(nlu_items):
        req_id = nlu_item.get("request_id", "")

        exp_item = expansion_items[idx] if idx < len(expansion_items) else {}
        expansion = exp_item.get("expansion", {}) or {}
        extraction = exp_item.get("extraction", {}) or {}

        # message를 Step4 결과 기반으로
        msg = _build_item_message(search_data)

        # item은 Step4 selected_name이 있으면 그걸 우선
        item_value = selected_name if selected_name else extraction.get("keyword", None)

        # expanded_keywords는 기존 Step3 유지 + selected_name을 맨 앞에 (원하면)
        expanded = expansion.get("expanded_keywords", []) or []
        if selected_name:
            expanded = [selected_name] + [x for x in expanded if x != selected_name]

        items.append({
            "request_id": req_id,
            "utterance": exp_item.get("utterance", ""),
            "intent": nlu_item.get("intent", "UNSUPPORTED"),
            "item": item_value,
            "expanded_keywords": expanded,
            "message": msg,
        })

    final = {
        "run_id": run_id,
        "status": "completed",
        "total_items": len(items),
        "items": items,
        "search": search_data,  # search.json 그대로 포함
        "pipeline_latency_ms": elapsed_ms,
    }
    # timing_ms 는 additive — 기존 스키마 깨뜨리지 않음
    if timing_ms:
        final["timing_ms"] = timing_ms

    _save_json(run_dir / "final_response.json", final)
    print(f"[OK] step5  - final_response.json 생성 ({len(items)}건)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="E2E PoC Pipeline Orchestrator",
    )
    parser.add_argument(
        "--text",
        nargs="+",
        help="텍스트 입력 (1개 이상). 예: --text \"볼펜 어디있어요\"",
    )
    parser.add_argument(
        "--audio_path",
        type=str,
        help="오디오 파일 경로. 예: --audio_path data/test_audio/sample.wav",
    )
    args = parser.parse_args()

    # Validate: exactly one of --text or --audio_path
    if args.text and args.audio_path:
        parser.error("--text 와 --audio_path 중 하나만 지정하세요.")
    if not args.text and not args.audio_path:
        parser.error("--text 또는 --audio_path 중 하나를 지정하세요.")

    # Generate run_id and create output directory
    run_id = f"e2e_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[Pipeline] run_id = {run_id}")
    print(f"[Pipeline] outputs → {run_dir.relative_to(PROJECT_ROOT)}\n")

    t_start = time.time()

    # Step 0: Input → transcript.json
    t0 = time.time()
    step0_transcript(args.text, args.audio_path, run_dir)
    step0_ms = int((time.time() - t0) * 1000)

    items = _load_json(run_dir / "transcript.json")

    # Step 1: Intent Classification (in-process)
    t1 = time.time()
    items = run_step1_inprocess(items, run_dir, run_id)
    step1_ms = int((time.time() - t1) * 1000)

    # Step 2: Keyword Extraction (in-process)
    t2 = time.time()
    items = run_step2_inprocess(items, run_dir)
    step2_ms = int((time.time() - t2) * 1000)

    # Step 3: Keyword Expansion (in-process)
    t3 = time.time()
    items = run_step3_inprocess(items, run_dir)
    step3_ms = int((time.time() - t3) * 1000)

    # Step 4: Search + Rerank
    query = _resolve_query(run_dir, args.text)
    t4 = time.time()
    search_result = run_step4(query, run_id)
    step4_ms = int((time.time() - t4) * 1000)

    if search_result.get("status") == "fail":
        elapsed_ms = int((time.time() - t_start) * 1000)
        print(f"\n[Pipeline] STOPPED at Step 4 (search/rerank fail)")
        print(f"  reason: {search_result.get('rerank', {}).get('error', 'unknown')}")
        print(f"  elapsed: {elapsed_ms}ms")
        sys.exit(1)

    # Step 5: Final Output
    t5 = time.time()

    # 1) Step5 직전까지 elapsed (임시)
    elapsed_before_step5 = int((time.time() - t_start) * 1000)

    # 2) timing_ms 먼저 만든다 (step5/total은 아래에서 채움)
    timing_ms = {
        "step0_transcript": step0_ms,
        "step1_intent": step1_ms,
        "step2_keyword_extract": step2_ms,
        "step3_keyword_expand": step3_ms,
        "step4_search_rerank": step4_ms,
    }

    # 3) step5 실행 (final_response.json 저장)
    step5_final_output(run_dir, run_id, elapsed_before_step5, timing_ms=timing_ms)

    # 4) step5/total 계산 (콘솔 출력용 + 필요하면 json에도 남길 수 있음)
    step5_ms = int((time.time() - t5) * 1000)
    elapsed_ms = int((time.time() - t_start) * 1000)

    timing_ms["step5_final"] = step5_ms
    timing_ms["total"] = elapsed_ms

    print(f"\n{'='*60}")
    print("  PIPELINE COMPLETED")
    print(f"  run_id: {run_id}")
    print(f"  elapsed: {elapsed_ms}ms")
    print(f"  timing : {json.dumps(timing_ms, ensure_ascii=False)}")
    print(f"  outputs: {run_dir.relative_to(PROJECT_ROOT)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
