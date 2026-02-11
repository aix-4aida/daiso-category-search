
import os
import shutil
import uuid
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, WebSocket
from typing import Optional

from backend.app.services.stt_service import get_stt_service
from backend.app.services.pipeline_service import get_pipeline_service
from backend.app.models.schemas import STTProcessResponse, VoiceSearchResponse, ComparisonPipelineResult
from backend.ws_stt import handle_streaming_stt

router = APIRouter(tags=["Voice"])

@router.post("/stt/process", response_model=STTProcessResponse)
async def process_stt(
    audio: UploadFile = File(...),
    attempt: int = Form(default=1)
):
    """Process audio through STT pipeline (STT -> Quality -> Policy)"""
    service = get_stt_service()
    
    # Save to temp
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        temp_path = tmp.name
    
    try:
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]
        
        # Run provider (Whisper)
        result = service.run_provider(temp_path, "whisper", attempt)
        final_response = service.generate_response(result)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return STTProcessResponse(
            request_id=request_id,
            stt=result.stt,
            quality_gate=result.quality_gate,
            policy_intent=result.policy_intent,
            final_response=final_response,
            processing_time_ms=processing_time_ms
        )
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@router.post("/api/search/voice", response_model=VoiceSearchResponse)
async def voice_search_api(file: UploadFile = File(...)):
    """Full Pipeline: STT -> Search -> Rerank"""
    stt_service = get_stt_service()
    pipeline_service = get_pipeline_service()
    
    request_id = str(uuid.uuid4())[:8]
    Path("outputs").mkdir(exist_ok=True)
    
    # Generate temp filename for debugging/logging
    original_filename = file.filename or f"voice_{request_id}.wav"
    temp_audio_path = f"outputs/voice_{request_id}_{original_filename}"
    
    start_total = time.time()
    
    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. STT
        stt_result = await stt_service.process_voice_search(temp_audio_path)
        text = stt_result["text"]
        
        if not text:
            return VoiceSearchResponse(
                text="", 
                pipeline_status="failed", 
                stt_time_seconds=stt_result["stt_time"], 
                total_time_seconds=time.time() - start_total,
                error="No speech detected"
            )
            
        # 2. Pipeline
        pipeline_result = await pipeline_service.run_voice_pipeline(
            temp_audio_path, 
            text, 
            stt_result["stt_time"]
        )
        
        # Extract results for response
        # (reuse logic from main.py, simplified here)
        final_json = pipeline_result.get('final_results', [])
        product_list = pipeline_result.get("final_results", []) # The pipeline seems to return structure in final_results
        
        # NOTE: pipeline_service returns raw dict from run_pipeline_for_voice
        # run_pipeline_for_voice returns dict with "final_results" key which is list of dicts
        
        # But wait, main.py had complex logic to parse IDs from strings like "123 (Name)"
        # I should probably move that parsing logic to PipelineService or keep it here.
        # Ideally Service should return clean domain objects.
        # For now, I will trust run_pipeline_for_voice returns what main.py expects, 
        # but I might need to copy the ID parsing logic if run_pipeline_for_voice doesn't do it.
        # Checking run_pipeline_for_voice in run_all_pipeline.py:
        # It reads FINAL_OUTPUT json and puts it in "final_results".
        # The JSON contains list of items.
        
        # In main.py, it iterated over `final_json[0]["retrieved_ids"]` etc.
        # This implies `final_json` is a list of query results (usually 1 query).
        
        # I'll implement the parsing logic here or in service. 
        # Let's put it here for now to match main.py behavior closely.
        
        products = []
        parsed_keyword = pipeline_result.get("keyword")
        
        if final_json and len(final_json) > 0:
            # Need to import helper to get product details? 
            # Services should be self-contained. 
            # I will use ProductService here.
            from backend.app.services.product_service import get_product_service
            p_service = get_product_service()
            
            first_result = final_json[0]
            # Logic from main.py lines 211-252
            retrieved_strs = first_result.get("retrieved_ids", []) or first_result.get("retrieved_results", [])
            item_strs = list(retrieved_strs)
            selected_val = first_result.get("selected_id")
            if selected_val:
                if selected_val in item_strs:
                    item_strs.remove(selected_val)
                item_strs.insert(0, selected_val)

            for item_str in item_strs[:10]: # Limit to 10
                 if "(" in item_str:
                     doc_id_str = item_str.split("(")[0].strip()
                 else:
                     doc_id_str = item_str.strip()
                 
                 if doc_id_str.isdigit():
                     prod = p_service.get_by_id(int(doc_id_str))
                     if prod and prod['id'] not in [p['id'] for p in products]:
                         products.append(prod)
        
        return VoiceSearchResponse(
            text=text,
            results=products,
            keyword=parsed_keyword,
            pipeline_status="completed",
            stt_time_seconds=stt_result["stt_time"],
            total_time_seconds=pipeline_result.get("total_time_seconds", 0)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return VoiceSearchResponse(
            text="",
            pipeline_status="failed",
            stt_time_seconds=0,
            total_time_seconds=time.time() - start_total,
            error=str(e)
        )

@router.websocket("/ws/stt")
async def websocket_stt_endpoint(websocket: WebSocket):
    await handle_streaming_stt(websocket)

# Legacy/Comparison endpoints if needed
