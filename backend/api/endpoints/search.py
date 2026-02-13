
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.services.rerank_service import rerank_products

router = APIRouter()

# --- Request/Response Schemas ---
class ProductCandidate(BaseModel):
    id: str
    name: str
    desc: Optional[str] = ""
    searchable_desc: Optional[str] = None

class RerankRequest(BaseModel):
    query: str
    candidates: List[ProductCandidate]

class RerankResponse(BaseModel):
    selected_id: Optional[str]
    reason: str
    latency: float

# --- Endpoints ---

@router.post("/rerank", response_model=RerankResponse)
async def rerank_endpoint(request: RerankRequest):
    """
    Perform LLM-based reranking on the provided candidates.
    Connects to: backend.services.rerank_service.rerank_products (Gemini 2.0 Flash)
    """
    try:
        # Pydantic models to dict list for the service
        candidates_data = [c.dict() for c in request.candidates]
        
        result = rerank_products(request.query, candidates_data)
        
        return RerankResponse(
            selected_id=result.get("selected_id"),
            reason=result.get("reason", ""),
            latency=result.get("latency", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
import shutil
import uuid
import os
from pathlib import Path
from backend.services.pipeline_service import run_full_pipeline, run_text_pipeline

@router.post("/audio")
async def search_audio(audio: UploadFile = File(...)):
    """
    Full Pipeline: Audio -> STT -> Intent -> Keyword -> Search -> Rerank -> Result
    """
    request_id = str(uuid.uuid4())[:8]
    temp_path = f"outputs/temp_{request_id}_{audio.filename}"
    Path("outputs").mkdir(exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
            
        result = await run_full_pipeline(temp_path)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        # Cleanup temp file (TEMPORARILY DISABLED FOR DEBUGGING)
        # if os.path.exists(temp_path):
        #     os.remove(temp_path)
        pass

class TextSearchRequest(BaseModel):
    query: str

@router.post("/text")
async def search_text(request: TextSearchRequest):
    """
    Text Pipeline: Intent -> Keyword -> Search -> Rerank -> Result
    """
    try:
        result = await run_text_pipeline(request.query)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
