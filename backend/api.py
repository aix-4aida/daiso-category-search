
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from unidecode import unidecode
from .logic.nlu import analyze_text, generate_tail_question, infer_product_keywords
from .database.database import search_products, get_related_products_for_context
from .logic.schemas import NLUResponse, Intent

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
    session_id: str = "default-user" # Added session_id

# Simple in-memory session store
# Structure: { session_id: [ {"role": "user", "text": "..."}, {"role": "assistant", "text": "..."} ] }
SESSIONS: Dict[str, List[Dict[str, str]]] = {}

@app.post("/api/search", response_model=NLUResponse)
async def search_endpoint(request: SearchRequest):
    print(f"[API] Search Request: {request.query} (Session: {request.session_id})")
    
    # Init session if needed
    if request.session_id not in SESSIONS:
        SESSIONS[request.session_id] = []
    
    history = SESSIONS[request.session_id]
    
    try:
        from .logic.agent_graph import agent_app
        
        initial_state = {
            "request_id": request.session_id,
            "input_text": request.query,
            "session_id": request.session_id,
            "history": history,
            "clarification_count": 0,
            "is_ambiguous": False,
            "search_candidates": [] 
        }
        
        config = {"configurable": {"thread_id": request.session_id}}
        
        print(f"[API] Invoking LangGraph (History: {len(history)} items)...")
        result_state = await agent_app.ainvoke(initial_state, config=config)
        
        final_response = result_state['final_response']
        print(f"[API] Graph Finished. Intent: {final_response.intent}")
        
        # Update SESSIONS
        history.append({"role": "user", "text": request.query})
        ai_text = final_response.generated_question or "Result found."
        history.append({"role": "assistant", "text": ai_text})
        if len(history) > 10: SESSIONS[request.session_id] = history[-10:]
        
        return final_response

    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        print(f"[API] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
