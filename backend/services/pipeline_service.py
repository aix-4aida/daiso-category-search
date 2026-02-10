
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
    STT -> Intent -> Keyword -> Search -> Rerank
    """
    start_time = time.time()
    steps = {}
    
    # 1. STT
    t0 = time.time()
    print(f"🎤 [Pipeline] STT Processing: {audio_file_path}")
    stt_result_obj = run_single_provider(audio_file_path, "whisper")
    stt_text = stt_result_obj.stt.text_raw
    stt_duration = time.time() - t0
    print(f"📝 [Pipeline] STT Result: '{stt_text}' ({stt_duration:.2f}s)")
    steps["stt"] = {"text": stt_text, "latency": stt_duration} 
    
    if not stt_text:
        print("❌ [Pipeline] STT Failed: Empty text")
        return {"status": "error", "message": "음성이 인식되지 않았습니다.", "steps": steps}

    # 2. Intent Check
    intent_res = check_intent(stt_text)
    print(f"🧠 [Pipeline] Intent: {intent_res}")
    steps["intent"] = intent_res
    
    if intent_res["is_valid"] == "N":
        print("⛔ [Pipeline] Filtered by Intent")
        return {
            "status": "filtered", 
            "message": "죄송합니다. 상품 검색과 관련된 질문만 답변할 수 있습니다.",
            "steps": steps
        }

    # 3. Keyword Extraction
    keyword_res = extract_keyword(stt_text)
    search_query = keyword_res["keyword"] or stt_text 
    print(f"🔑 [Pipeline] Keyword: '{search_query}' (Original: {keyword_res['keyword']})")
    steps["keyword"] = keyword_res

    # 4. Search (Retrieval)
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

    # 5. Rerank (LLM)
    t2 = time.time()
    print("⚖️ [Pipeline] Reranking...")
    rerank_res = rerank_products(stt_text, candidates) 
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

    # Construct Final Response (Mocking Location for now if not in meta)
    # Meta example: {'section': 'A1', 'floor': 'B1'} (Depends on catalog data)
    location = final_product.get("meta", {})
    
    # Fallback location logic (Remove hardcoded fake data)
    # If section is missing, try to use category info or return Unknown
    if not location.get("section"):
         # Try to map category to section if possible, otherwise Unknown
         # location["section"] = location.get("major", "위치 정보 없음")
         pass
    
    processing_time = time.time() - start_time
    print(f"⏱️ [Pipeline] Total Duration: {processing_time:.2f}s (STT: {stt_duration:.2f}s, Search: {search_duration:.2f}s, Rerank: {rerank_duration:.2f}s)")
    
    # 2. 최종적으로 Front에게 주는 JSON 응답    
    return {
        "status": "success",
        "result": {
            "product": final_product["name"],
            "id": final_product["id"],
            "location": {
                "section": location.get("section", "Unknown"),
                "floor": location.get("floor", "B1"),
                "id": location.get("id", "Unknown")
            }
        },
        "candidates": candidates, # Hybrid/BM25 Search Results
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
