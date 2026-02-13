"""
Minimal API server for integration testing.
Runs /v1/search and /health endpoints without STT dependencies.
"""
import sys
import os

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from backend.logic.integrated_search import get_pipeline

search_pipeline = get_pipeline()
print(f"Search mode: {search_pipeline.search_mode}")

app = FastAPI(title="Daiso Search - Integration Test", version="test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    store_id: str = Field(default="store_001")
    input_type: str = Field(default="text")
    query: str = Field(...)
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    clarification_count: int = 0


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "search_mode": search_pipeline.search_mode,
    }


@app.post("/v1/search")
async def search(request: SearchRequest):
    try:
        result = await search_pipeline.search(
            query=request.query,
            store_id=request.store_id,
            session_id=request.session_id,
            history=request.history or [],
            clarification_count=request.clarification_count,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
