"""
In-process wrappers for pipeline Steps 1 / 2 / 3.

Strategy:
  - Step 2, 3: import PoC 함수 직접 호출 (sys.path 임시 추가 → finally 복원)
  - Step 1: poc_flash_test.py는 module-level exit(1) + json 미 import 이슈로
            직접 import 불가 → model/prompt/safety_settings만 참조하여 최소 wrapper
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Shared lazy Gemini initialisation (한 번만 configure)
# ---------------------------------------------------------------------------
_genai = None


def _get_genai():
    global _genai
    if _genai is None:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        genai.configure(api_key=api_key)
        _genai = genai
    return _genai


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===================================================================
# Step 1  – Intent Validation  (최소 wrapper: poc_flash_test.py 참조)
# ===================================================================
# poc/intent/poc_flash_test.py 를 직접 import 할 수 없는 이유:
#   1) module-level 에서 GOOGLE_API_KEY 없으면 exit(1) 호출
#   2) json 모듈이 __main__ 블록에서만 import → process_data() 호출 시 NameError
# 따라서 동일한 system_prompt / generation_config / safety_settings 를 사용하되
# Gemini 호출만 in-process 로 수행한다.

_intent_model = None

# --- 아래 상수는 poc/intent/poc_flash_test.py 에서 그대로 가져온 값 ---
_INTENT_SYSTEM_PROMPT = """
너는 다이소 매장의 태블릿에 탑재된 AI 점원이다.
사용자의 발화를 분석하여, 매장 직원의 응대가 필요한지(Y), 필요 없는지(N) 판단하여 알파벳 한 글자만 출력하라.

[판단 기준]
1. Y (응대 필요):
   - 다이소 상품 찾기, 재고 확인, 상품 추천 요청
   - 매장 시설(화장실, 엘리베이터, 주차장) 및 운영 시간 문의
   - 결제, 영수증 재발급, 봉투 구매, 멤버십 포인트 적립 문의
   - 생활 속 문제 해결을 위한 상품 탐색 (예: "욕실이 미끄러워")

2. N (응대 불필요/무시):
   - 다이소와 무관한 사적인 잡담 (인사, 농담, MBTI, 연애 상담)
   - 외부 정보 질문 (날씨, 주식, 비트코인, 뉴스, 연예인)
   - 타 브랜드(맥도날드, 스타벅스, 편의점) 관련 질문
   - 단순한 불만 토로, 욕설, 의미 없는 혼잣말

[Few-Shot 예시]
User: "건전지 어디 있어?" -> Model: Y
User: "포인트 적립 되나요?" -> Model: Y
User: "화장실 비번 뭐야?" -> Model: Y
User: "비트코인 얼마야?" -> Model: N
User: "맥도날드 가격 알려줘" -> Model: N
User: "나랑 결혼할래?" -> Model: N
User: "사랑해" -> Model: N
"""

_INTENT_GEN_CONFIG = {
    "temperature": 0.0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 5,
}


def _get_intent_model():
    global _intent_model
    if _intent_model is None:
        genai = _get_genai()
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        _intent_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=_INTENT_GEN_CONFIG,
            system_instruction=_INTENT_SYSTEM_PROMPT,
        )
        _intent_model._safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    return _intent_model


def run_step1_inprocess(items: list[dict], run_dir: Path, run_id: str) -> list[dict]:
    """Step 1: Intent validation (in-process).

    Returns items with ``intent_validation`` field added.
    Writes ``run_dir/nlu.json``.
    """
    print(f"\n{'=' * 60}")
    print("  STEP 1 (in-process): Intent Validation")
    print(f"{'=' * 60}")

    model = _get_intent_model()
    safety = model._safety

    processed: list[dict] = []
    nlu_items: list[dict] = []

    for i, item in enumerate(items):
        utterance = item.get("utterance", "")
        if not utterance:
            item["intent_validation"] = {"is_valid": "N", "latency_ms": 0}
            processed.append(item)
            continue

        start = time.time()
        prediction = "ERROR"
        try:
            response = model.generate_content(utterance, safety_settings=safety)
            raw = response.text.strip().upper()
            if "Y" in raw:
                prediction = "Y"
            elif "N" in raw:
                prediction = "N"
            else:
                prediction = raw
        except Exception as e:
            print(f"  [Step1] Error: {e}")
            prediction = "ERROR"

        latency_ms = int((time.time() - start) * 1000)
        item["intent_validation"] = {"is_valid": prediction, "latency_ms": latency_ms}
        processed.append(item)

        print(f"  [{i + 1}/{len(items)}] {utterance} → {prediction} ({latency_ms}ms)")

        # nlu.json 계약
        nlu_items.append(
            {
                "request_id": f"{run_id}_{item.get('id', i + 1)}",
                "intent": "PRODUCT_LOCATION" if prediction == "Y" else "UNSUPPORTED",
                "slots": {"item": None, "attrs": [], "category_hint": None, "query_rewrite": None},
                "expanded_keywords": [],
                "needs_clarification": False,
                "latency_ms": latency_ms,
            }
        )

    _save_json(run_dir / "nlu.json", nlu_items)
    print(f"[OK] step1 (in-process)")
    return processed


# ===================================================================
# Step 2  – Keyword Extraction  (PoC import)
# ===================================================================
# poc/kms/simple_keyword_extractor_gemini.py 의 extract_keyword(query) 를
# 직접 import하여 호출한다.
# module-level 에서 genai.configure + model 생성이 실행되므로,
# import 전에 env var 가 설정되어 있어야 한다 (run_e2e.py 에서 load_dotenv 완료).

_extract_keyword_fn = None


def _get_extract_keyword():
    """Lazy import of poc extract_keyword function."""
    global _extract_keyword_fn
    if _extract_keyword_fn is not None:
        return _extract_keyword_fn

    # env var 보장 (poc_flash_test 는 GOOGLE_API_KEY, extractor 는 GEMINI_API_KEY 우선)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        os.environ.setdefault("GEMINI_API_KEY", gemini_key)
        os.environ.setdefault("GOOGLE_API_KEY", gemini_key)

    poc_kms = str(PROJECT_ROOT / "poc" / "kms")
    added = poc_kms not in sys.path
    if added:
        sys.path.insert(0, poc_kms)
    try:
        from simple_keyword_extractor_gemini import extract_keyword  # type: ignore

        _extract_keyword_fn = extract_keyword
        return extract_keyword
    finally:
        if added:
            try:
                sys.path.remove(poc_kms)
            except ValueError:
                pass


def run_step2_inprocess(items: list[dict], run_dir: Path) -> list[dict]:
    """Step 2: Keyword extraction (in-process, PoC import).

    Returns items with ``extraction`` field added.
    Writes ``run_dir/keywords.json``.
    """
    print(f"\n{'=' * 60}")
    print("  STEP 2 (in-process): Keyword Extraction")
    print(f"{'=' * 60}")

    extract_keyword = _get_extract_keyword()

    for i, item in enumerate(items):
        utterance = item.get("utterance", "").strip()
        if not utterance:
            item["extraction"] = {"error": "Empty utterance"}
            continue

        result = extract_keyword(utterance)
        item["extraction"] = result

        kw = result.get("keyword", result.get("error", "?"))
        print(f"  [{i + 1}/{len(items)}] {utterance} → {kw}")

    _save_json(run_dir / "keywords.json", items)
    print(f"[OK] step2 (in-process)")
    return items


# ===================================================================
# Step 3  – Keyword Expansion  (PoC import)
# ===================================================================
# poc/kms/nlu.py 의 expand_search_keywords (async) 를 직접 import.
# backend/logic/nlu.py 에서 이미 동일 경로로 import 하므로 검증됨.

_expand_fn = None


def _get_expand_fn():
    """Lazy import of poc.kms.nlu.expand_search_keywords."""
    global _expand_fn
    if _expand_fn is not None:
        return _expand_fn

    pr = str(PROJECT_ROOT)
    added = pr not in sys.path
    if added:
        sys.path.insert(0, pr)
    try:
        from poc.kms.nlu import expand_search_keywords  # type: ignore

        _expand_fn = expand_search_keywords
        return expand_search_keywords
    finally:
        if added:
            try:
                sys.path.remove(pr)
            except ValueError:
                pass


def run_step3_inprocess(items: list[dict], run_dir: Path) -> list[dict]:
    """Step 3: Keyword expansion (in-process, PoC import).

    Returns items with ``expansion`` field added.
    Writes ``run_dir/expansion.json``.
    """
    print(f"\n{'=' * 60}")
    print("  STEP 3 (in-process): Keyword Expansion")
    print(f"{'=' * 60}")

    expand_fn = _get_expand_fn()

    async def _expand_one(keyword: str) -> tuple[list[str], dict]:
        return await expand_fn(keyword, return_usage=True)

    for i, item in enumerate(items):
        extraction = item.get("extraction", {})
        kw = extraction.get("keyword", "")

        if not kw or "error" in extraction:
            item["expansion"] = {"error": "No valid keyword from extraction"}
            continue

        func_start = time.time()
        try:
            expanded_list, usage = asyncio.run(_expand_one(kw))
            func_end = time.time()
            total_time = func_end - func_start
            api_time = usage.get("latency_seconds", total_time)
            processing_time = max(0, total_time - api_time)

            item["expansion"] = {
                "expanded_keywords": expanded_list,
                "meta": {
                    "total_time_seconds": total_time,
                    "api_latency_seconds": api_time,
                    "processing_overhead_seconds": processing_time,
                    "total_tokens": usage.get("total_tokens", 0),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
            }
            print(f"  [{i + 1}/{len(items)}] '{kw}' → {len(expanded_list)} items")
        except Exception as e:
            print(f"  [{i + 1}/{len(items)}] Error expanding '{kw}': {e}")
            item["expansion"] = {"error": str(e)}

    _save_json(run_dir / "expansion.json", items)
    print(f"[OK] step3 (in-process)")
    return items
