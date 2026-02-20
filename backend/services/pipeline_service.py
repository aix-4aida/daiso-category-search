import os
import uuid
import time
from backend.logic.agent_graph import agent_app

def get_val(obj, key, default=None):
    if hasattr(obj, key): return getattr(obj, key)
    if isinstance(obj, dict): return obj.get(key, default)
    return default

def to_dict(p):
    if hasattr(p, "model_dump"): return p.model_dump()
    return p  # Already a dict

def format_products(products):
    """Unified formatting for products to be sent to frontend"""
    formatted = []
    for p in products:
        formatted.append({
            "id": get_val(p, "id"),
            "name": get_val(p, "name", "알 수 없는 상품"),
            "price": get_val(p, "price", 0),
            "formatted_price": f"{get_val(p, 'price', 0):,}원",
            "location": {
                "floor": get_val(p, "floor", "B1"),
                "section": get_val(p, "section", "N01"),
                "shelf_label": get_val(p, "shelf_label", "일반매대")
            },
            "image_url": get_val(p, "image_url", ""),
            "meta": {
                "category_major": get_val(p, "category_major"),
                "category_middle": get_val(p, "category_middle")
            }
        })
    return formatted

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
        return {"status": "error", "message": "음성이 인식되지 않았습니다.", "steps": steps}

    # 2. Agent Graph Workflow
    inputs = {
        "input_text": stt_text,
        "history": [],
        "clarification_count": 0,
        "request_id": str(uuid.uuid4())
    }
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    final_state = await agent_app.ainvoke(inputs, config=config)
    
    result_obj = final_state["final_response"]
    products = result_obj.products
    
    processing_time = time.time() - start_time
    
    return {
        "status": "success",
        "query": stt_text,
        "products": format_products(products),
        "message": result_obj.generated_question or f"'{stt_text}' 관련 결과를 보여드릴게요.",
        "processing_time": processing_time,
        "steps": steps
    }

async def run_text_pipeline(text: str):
    """
    Run the text-only Daiso Search Pipeline using Agent Graph.
    """
    start_time = time.time()
    steps = {}
    
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
    
    processing_time = time.time() - start_time
    
    return {
        "status": "success",
        "query": text,
        "products": format_products(products),
        "message": result_obj.generated_question or f"'{text}' 검색 결과입니다.",
        "processing_time": processing_time,
        "steps": steps
    }
