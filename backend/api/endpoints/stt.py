
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.stt_service import run_single_provider, generate_final_response
from backend.stt.types import PipelineResult, ComparisonPipelineResult
import shutil
import uuid
import time
from pathlib import Path

router = APIRouter()

@router.post("/compare", response_model=ComparisonPipelineResult)
async def compare_audio(
    audio: UploadFile = File(...),
    attempt: int = 1
):
    """
    Process audio through both Whisper and Google STT for comparison
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file
    Path("outputs").mkdir(exist_ok=True)
    original_filename = audio.filename or f"recording_{request_id}.wav"
    temp_audio_path = f"outputs/temp_{request_id}_{original_filename}"
    
    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Run both providers
        whisper_result = run_single_provider(temp_audio_path, "whisper", attempt)
        google_result = run_single_provider(temp_audio_path, "google", attempt)
        
        # Generate final response
        final_response = generate_final_response(whisper_result)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ComparisonPipelineResult(
            request_id=request_id,
            file_name=original_filename,
            saved_path=temp_audio_path,
            whisper=whisper_result,
            google=google_result,
            primary_provider="whisper",
            final_response=final_response,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process", response_model=PipelineResult)
async def process_audio(
    audio: UploadFile = File(...),
    attempt: int = 1
):
    """
    Process audio through Whisper STT pipeline (original endpoint)
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    Path("outputs").mkdir(exist_ok=True)
    temp_audio_path = f"outputs/temp_{request_id}.wav"
    
    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Run single provider (Whisper)
        result = run_single_provider(temp_audio_path, "whisper", attempt)
        
        # Generate Response logic reused here (simplified)
        final_response = generate_final_response(result)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return PipelineResult(
            request_id=request_id,
            stt=result.stt,
            quality_gate=result.quality_gate,
            policy_intent=result.policy_intent,
            normalized_text=result.stt.text_raw,
            final_response=final_response,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
