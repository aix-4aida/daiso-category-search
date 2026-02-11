
import os
import shutil
import uuid
import time
from pathlib import Path
from backend.services.stt_service import run_single_provider
from backend.services.intent_service import check_intent
from backend.services.keyword_service import extract_keyword
from backend.services.search_service import search_products
from backend.services.rerank_service import rerank_products

def run_full_pipeline(audio_file_path: str):
    """
    Run the full Daiso Search Pipeline:
    STT (Fallback) -> Intent -> Keyword -> Search -> Rerank
    """
    from backend.services.stt_service import run_stt_pipeline_with_fallback
    
    start_time = time.time()
    steps = {}
    
    # 1. STT (Google -> Whisper Fallback)
    print(f"\n--- [Step 1: STT] Start (Audio: {audio_file_path}) ---")
    stt_t0 = time.time()
    stt_result_obj = run_stt_pipeline_with_fallback(audio_file_path, attempt=1)
    stt_text = stt_result_obj.stt.text_raw
    stt_duration = time.time() - stt_t0
    print(f"--- [Step 1: STT] Result: '{stt_text}' (Provider: {stt_result_obj.provider}, Latency: {stt_duration:.2f}s) ---")
    
    steps["stt"] = {
        "text": stt_text,
        "provider": stt_result_obj.provider,
        "latency": stt_duration,
        "quality": stt_result_obj.quality_gate.status
    }

    if not stt_text:
        print("❌ [Pipeline] STT Failed: Empty text")
        return {
            "status": "error",
            "message": "음성이 인식되지 않았습니다. 다시 말씀해 주세요.",
            "steps": steps
        }

    # 2. Intent Check
    print(f"\n--- [Step 2: Intent] Classifying: '{stt_text}' ---")
    intent_res = check_intent(stt_text)
    print(f"--- [Step 2: Intent] Result: {intent_res['is_valid']} (Reason: {intent_res.get('reason')}) ---")
    steps["intent"] = intent_res
    
    if intent_res["is_valid"] == "N":
        print("⛔ [Pipeline] Filtered by Intent")
        return {
            "status": "filtered", 
            "message": "죄송합니다. 상품 검색과 관련된 질문만 답변할 수 있습니다.",
            "steps": steps
        }

    # 3. Keyword Extraction
    print(f"\n--- [Step 3: Keyword] Extracting from: '{stt_text}' ---")
    keyword_res = extract_keyword(stt_text)
    search_query = keyword_res["keyword"] or stt_text 
    print(f"--- [Step 3: Keyword] Result: '{search_query}' (Original: {keyword_res['keyword']}) ---")
    steps["keyword"] = keyword_res

    # 4. Search (Retrieval)
    print(f"\n--- [Step 4: Search] Searching for: '{search_query}' ---")
    search_t1 = time.time()
    candidates = search_products(search_query, top_k=30)
    search_duration = time.time() - search_t1
    print(f"--- [Step 4: Search] Found {len(candidates)} candidates ({search_duration:.2f}s) ---")
    
    steps["search"] = {
        "count": len(candidates),
        "top_1": candidates[0]["name"] if candidates else None,
        "latency": search_duration
    }
    
    if not candidates:
        print("❌ [Pipeline] Search Failed: No candidates")
        return {
            "status": "empty",
            "message": f"'{search_query}'에 대한 상품을 찾을 수 없습니다.",
            "steps": steps
        }

    # 5. Rerank (LLM)
    print(f"\n--- [Step 5: Rerank] Reranking {len(candidates[:10])} candidates... ---")
    rerank_t2 = time.time()
    rerank_res = rerank_products(stt_text, candidates[:10]) 
    rerank_duration = time.time() - rerank_t2
    print(f"--- [Step 5: Rerank] Result: ID {rerank_res.get('selected_id')} ({rerank_duration:.2f}s) ---")
    steps["rerank"] = rerank_res
    
    selected_id = rerank_res.get("selected_id")
    if not selected_id:
        # Fallback to Top-1 from search if rerank fails to select
        selected_id = candidates[0]["id"]
        print("⚠️ [Pipeline] Rerank failed to select ID, falling back to Search Top-1")
        
    # Find selected product details
    final_product = next((c for c in candidates if c["id"] == selected_id), None) or candidates[0]
    
    # 6. Final Response
    location = final_product.get("meta", {})
    processing_time = time.time() - start_time
    print(f"\n⏱️ [Pipeline] Total Duration: {processing_time:.2f}s")
    
    return {
        "status": "success",
        "result": {
            "product": final_product["name"],
            "id": final_product["id"],
            "location": {
                "section": location.get("section", "Unknown"),
                "floor": location.get("floor", "B1"),
                "id": location.get("id", "Unknown")
            },
            "price": final_product.get("price", "3,000원"),
            "initial": final_product.get("initial", final_product["name"][0])
        },
        "candidates": candidates[:5],
        "query": stt_text,
        "processing_time": processing_time,
        "steps": steps
    }

def run_text_pipeline(text: str):
    """
    Run the Daiso Search Pipeline from text input:
    Intent -> Keyword -> Search -> Rerank
    (Skips STT step)
    """
    start_time = time.time()
    steps = {}
    
    # 1. Intent Check
    intent_res = check_intent(text)
    print(f"🧠 [Pipeline] Intent: {intent_res}")
    steps["intent"] = intent_res
    
    if intent_res["is_valid"] == "N":
        print("⛔ [Pipeline] Filtered by Intent")
        return {
            "status": "filtered", 
            "message": "죄송합니다. 상품 검색과 관련된 질문만 답변할 수 있습니다.",
            "steps": steps
        }

    # 2. Keyword Extraction
    keyword_res = extract_keyword(text)
    search_query = keyword_res["keyword"] or text 
    print(f"🔑 [Pipeline] Keyword: '{search_query}' (Original: {keyword_res['keyword']})")
    steps["keyword"] = keyword_res

    # 3. Search (Retrieval)
    t1 = time.time()
    candidates = search_products(search_query, top_k=30)
    search_duration = time.time() - t1
    print(f"🔍 [Pipeline] Search Candidates: {len(candidates)} items ({search_duration:.2f}s)")
    if candidates:
        top_names = [c['name'] for c in candidates[:5]]
        print(f"   ➤ Top 5: {top_names}")
    
    steps["search"] = {"count": len(candidates), "top_1": candidates[0]["name"] if candidates else None, "latency": search_duration}
    
    if not candidates:
        print("❌ [Pipeline] Search Failed: No candidates")
        return {
            "status": "empty",
            "message": f"'{search_query}'에 대한 상품을 찾을 수 없습니다.",
            "steps": steps
        }

    # 4. Rerank (LLM)
    t2 = time.time()
    print("⚖️ [Pipeline] Reranking...")
    rerank_res = rerank_products(text, candidates) 
    rerank_duration = time.time() - t2
    print(f"🏆 [Pipeline] Rerank Result: {rerank_res} ({rerank_duration:.2f}s)")
    steps["rerank"] = rerank_res
    
    selected_id = rerank_res.get("selected_id")
    
    if not selected_id:
         return {
            "status": "empty",
            "message": "적절한 상품을 선택하지 못했습니다.",
            "steps": steps
        }
        
    # Find selected product details
    final_product = next((c for c in candidates if c["id"] == selected_id), None)
    
    if not final_product:
         return {"status": "error", "message": "선택된 상품 ID를 찾을 수 없습니다.", "steps": steps}

    # Construct Final Response
    location = final_product.get("meta", {})
    
    # Fallback location logic if needed
    if not location.get("section"):
         # Try to map category to section if possible
         pass
    
    processing_time = time.time() - start_time
    print(f"⏱️ [Pipeline] Total Duration: {processing_time:.2f}s")
    
    return {
        "status": "success",
        "result": {
            "product": final_product["name"],
            "id": final_product["id"],
            "location": {
                "section": location.get("section", "Unknown"),
                "floor": location.get("floor", "B1"),
                "id": location.get("id", "Unknown")
            },
            "price": final_product.get("price", "가격정보없음"),
            "initial": final_product.get("initial", "상") # Add initial if available
        },
        "candidates": candidates,
        "query": text,
        "processing_time": processing_time,
        "steps": steps
    }
