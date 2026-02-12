import os
import uuid
import time
from backend.logic.agent_graph import agent_app

async def run_full_pipeline(audio_file_path: str):
    """
    Run the full Daiso Search Pipeline:
    STT (Fallback) -> Agent Graph (NLU -> Search -> Response)
    """
    from backend.services.stt_service import run_stt_pipeline_with_fallback
    
    start_time = time.time()
    steps = {}
    
    # 1. STT
    print(f"--- [Pipeline] Step 1: Running STT ---")
    stt_result_obj = run_stt_pipeline_with_fallback(audio_file_path)
    stt_text = stt_result_obj.stt.text_raw
    steps["stt"] = {"text": stt_text, "provider": stt_result_obj.provider}
    print(f"--- [Pipeline] STT Result: '{stt_text}' (via {stt_result_obj.provider}) ---")

    if not stt_text:
        print(f"--- [Pipeline] ERROR: No text recognized ---")
        return {"status": "error", "message": "음성이 인식되지 않았습니다.", "steps": steps}

    # 2. Agent Graph Workflow
    print(f"--- [Pipeline] Step 2: Invoking Agent Graph ---")
    inputs = {
        "input_text": stt_text,
        "history": [],
        "clarification_count": 0,
        "request_id": str(uuid.uuid4())
    }
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    final_state = await agent_app.ainvoke(inputs, config=config)
    print(f"--- [Pipeline] Agent Graph Completed ---")
    
    result_obj = final_state["final_response"]
    products = result_obj.products
    
    # Format for frontend (matching search.js expectations)
    primary_product = products[0] if products else None
    
    formatted_result = {
        "product": primary_product.name if primary_product else "결과 없음",
        "id": primary_product.id if primary_product else None,
        "price": f"{primary_product.price:,}원" if primary_product and primary_product.price else "가격정보없음",
        "location": {
            "floor": "Unknown", 
            "id": "Unknown",
            "section": "Unknown"
        },
        "meta": {}
    }

    processing_time = time.time() - start_time
    
    return {
        "status": "success",
        "query": stt_text,
        "result": formatted_result,
        "candidates": [p.model_dump() for p in products[1:6]] if len(products) > 1 else [],
        "message": result_obj.generated_question or "상품을 찾았습니다.",
        "processing_time": processing_time,
        "steps": steps
    }

async def run_text_pipeline(text: str):
    """
    Run the text-only Daiso Search Pipeline using Agent Graph.
    """
    start_time = time.time()
    steps = {}
    
    print(f"--- [Pipeline] Invoking Agent Graph (Text) for: '{text}' ---")
    inputs = {
        "input_text": text,
        "history": [],
        "clarification_count": 0,
        "request_id": str(uuid.uuid4())
    }
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    final_state = await agent_app.ainvoke(inputs, config=config)
    
    result_obj = final_state["final_response"]
    products = result_obj.products
    
    primary_product = products[0] if products else None
    
    formatted_result = {
        "product": primary_product.name if primary_product else "결과 없음",
        "id": primary_product.id if primary_product else None,
        "price": f"{primary_product.price:,}원" if primary_product and primary_product.price else "가격정보없음",
        "location": {
            "floor": "Unknown",
            "id": "Unknown",
            "section": "Unknown"
        },
        "meta": {}
    }
    
    processing_time = time.time() - start_time
    
    return {
        "status": "success",
        "query": text,
        "result": formatted_result,
        "candidates": [p.model_dump() for p in products[1:6]] if len(products) > 1 else [],
        "message": result_obj.generated_question or "상품을 찾았습니다.",
        "processing_time": processing_time,
        "steps": steps
    }
