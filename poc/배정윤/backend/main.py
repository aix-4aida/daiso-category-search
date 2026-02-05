from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
# will import search engine later

app = FastAPI(title="Search-Roca API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify generic localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchQuery(BaseModel):
    query: str
    context: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "Search-Roca Backend Running"}

import search_engine

@app.post("/api/search")
def search_items(payload: SearchQuery):
    try:
        results = search_engine.search(payload.query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
