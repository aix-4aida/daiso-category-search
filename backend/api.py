from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .logic.nlu import analyze_text, generate_tail_question
from .logic.schemas import NLUResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/api/search", response_model=NLUResponse)
async def search_endpoint(request: SearchRequest):
    try:
        # 1. Analyze text
        nlu_result = await analyze_text(request.query)
        
        # 2. If clarification needed, generate tail question
        if nlu_result.needs_clarification and not nlu_result.generated_question:
            tail_question = await generate_tail_question(request.query, nlu_result.slots.model_dump())
            nlu_result.generated_question = tail_question
            
        return nlu_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
