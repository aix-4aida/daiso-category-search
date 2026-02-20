
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
import time
import sqlite3
from pathlib import Path

# SQLite DB path
DB_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "products.db"

def search_products_db(query: str, limit: int = 10):
    """Search products in SQLite using improved Korean-aware matching."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Split query into keywords
    keywords = query.strip().split()
    
    if not keywords:
        conn.close()
        return []
    
    # Generate substrings for compound Korean words
    # e.g., "마스크팩" → ["마스크팩", "마스크", "스크팩", "크팩"]
    all_patterns = set()
    for kw in keywords:
        all_patterns.add(kw)
        # Generate substrings of length >= 2 characters
        if len(kw) >= 3:
            for i in range(len(kw)):
                for j in range(i + 2, len(kw) + 1):
                    sub = kw[i:j]
                    if len(sub) >= 2:
                        all_patterns.add(sub)
    
    # Build WHERE clause: any pattern matches any field (OR logic)
    conditions = []
    params = []
    for pat in all_patterns:
        pattern = f"%{pat}%"
        conditions.append(
            "(name LIKE ? OR category_major LIKE ? OR category_middle LIKE ? "
            "OR tags LIKE ? OR description LIKE ?)"
        )
        params.extend([pattern] * 5)
    
    where_clause = " OR ".join(conditions)
    
    # Order by relevance: exact name match first, then longest matching substrings in name
    order_parts = []
    order_params = []
    # Sort patterns by length descending (e.g. len 4 before len 3 before len 2)
    for pat in sorted(all_patterns, key=len, reverse=True):
        order_parts.append("(CASE WHEN name LIKE ? THEN 0 ELSE 1 END)")
        order_params.append(f"%{pat}%")
    order_clause = ", ".join(order_parts) if order_parts else "name"
    
    sql = f"SELECT * FROM products WHERE {where_clause} ORDER BY {order_clause} LIMIT ?"
    params.extend(order_params)
    params.append(limit)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "name": row["name"],
            "price": row["price"] or 0,
            "location": {
                "floor": row["floor"] or "B1",
                "section": row["section"] or "",
                "shelf_label": row["shelf_label"] or ""
            },
            "image_url": row["image_url"] or "",
            "meta": {
                "category_major": row["category_major"] or "",
                "category_middle": row["category_middle"] or ""
            }
        })
    
    return results

# --- Pipelines (kept for audio, but text now uses SQLite) ---

try:
    from backend.services.pipeline_service import run_full_pipeline
except ImportError:
    async def run_full_pipeline(path):
        return {"status": "error", "message": "Pipeline not available"}

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
        pass

class TextSearchRequest(BaseModel):
    query: str

@router.post("/text")
async def search_text(request: TextSearchRequest):
    """
    Text Search: Direct SQLite query on products.db
    """
    start_time = time.time()
    
    try:
        products = search_products_db(request.query)
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "query": request.query,
            "products": products,
            "message": f"'{request.query}' 검색 결과 {len(products)}개를 찾았습니다." if products else f"'{request.query}'에 대한 검색 결과가 없습니다.",
            "processing_time": processing_time,
            "steps": {}
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
