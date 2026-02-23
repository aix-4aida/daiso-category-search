
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

# --- Category APIs ---

@router.get("/categories")
async def get_categories():
    """DB에서 category_major 목록을 조회합니다."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category_major, COUNT(*) as count 
            FROM products 
            WHERE category_major IS NOT NULL AND category_major != ''
            GROUP BY category_major 
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        categories = [{"name": row["category_major"], "count": row["count"]} for row in rows]
        return {"status": "success", "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category")
async def get_products_by_category(name: str, limit: int = 1000):
    """특정 category_major에 해당하는 상품을 반환합니다."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE category_major = ? ORDER BY id LIMIT ?",
            (name, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                "id": str(row["id"]),
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
        
        return {
            "status": "success",
            "query": name,
            "products": products,
            "message": f"'{name}' 카테고리 상품 {len(products)}개를 찾았습니다." if products else f"'{name}' 카테고리 상품이 없습니다.",
            "processing_time": 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    Text Search: Hybrid Search (ChromaDB Vector + BM25) + LLM Reranking (Top 3)
    """
    start_time = time.time()
    
    try:
        from backend.services.search_service import search_products
        
        # 1. 하이브리드 검색 (충분한 10개를 가져옴)
        # 이 함수가 내부적으로 fusion 기반 점수 (hybrid_score, bm25_score, vector_score)를 meta와 desc에 추가해줍니다.
        products = search_products(request.query, top_k=10, use_hybrid=True)
        
        # 2. 리랭킹 적용 (Gemini 2.0 Flash)
        if products:
            # candidates 포맷을 rerank_service가 처리할 수 있게 생성
            candidate_list = []
            for p in products:
                desc = p.get('meta', {}).get('category_major', '') or ''
                if p.get('meta', {}).get('category_middle'):
                    desc += f" > {p['meta']['category_middle']}"
                    
                candidate_list.append({
                    "id": p["id"],
                    "name": p["name"],
                    "desc": desc,
                    "meta": p.get("meta", {})
                })
                
            from backend.services.rerank_service import rerank_products
            rerank_result = rerank_products(request.query, candidate_list)
            top_ids = rerank_result.get("top_ids", [])
            
            # top_ids 순서대로 products 필터링 (최대 3개)
            reranked_products = []
            prod_map = {str(p["id"]): p for p in products}
            
            for rid in top_ids[:3]:
                if str(rid) in prod_map:
                    reranked_products.append(prod_map[str(rid)])
                    
            # 만약 rerank에서 ID를 하나도 반환하지 못했다면 기존 products 중 앞 3개로 fallback
            if not reranked_products:
                reranked_products = products[:3]
            
            # [NEW] BM25 매칭이 있는 결과와 벡터 전용 결과를 분리하여,
            # BM25 매칭 결과가 1개라도 있으면 벡터 전용(연관성 낮음) 결과를 제거
            bm25_matched = [p for p in reranked_products if float(p.get('meta', {}).get('bm25_score', '0')) > 0]
            if bm25_matched:
                removed = len(reranked_products) - len(bm25_matched)
                if removed > 0:
                    print(f"    [Post-Rerank Filter] BM25 매칭 {len(bm25_matched)}개만 유지, 벡터전용 {removed}개 제거")
                reranked_products = bm25_matched
                
            products = reranked_products
            
        processing_time = time.time() - start_time
        
        # 텍스트 검색에서도 search_scores.txt 파일 갱신
        try:
            import json
            output_path = os.path.join(str(DB_PATH.parent.parent), "search_scores.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
        except Exception as e:
            import traceback
            print(f"⚠️ Failed to write text search scores to file in search.py: {e}")
            traceback.print_exc()
            
        return {
            "status": "success",
            "query": request.query,
            "products": products,
            "message": f"'{request.query}' 검색 결과 {len(products)}개를 찾았습니다." if products else f"'{request.query}'에 대한 검색 결과가 없습니다.",
            "processing_time": processing_time,
            "steps": {"rerank_duration": rerank_result.get("latency", 0.0) if 'rerank_result' in locals() else 0.0}
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
