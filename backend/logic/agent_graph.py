
import asyncio
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.logic.nlu import analyze_text, generate_tail_question, infer_product_keywords
from backend.services.search_service import search_products
from backend.logic.schemas import NLUResponse, Intent, NLUSlots, Product

# --- 1. Graph State Definition ---
class GraphState(TypedDict):
    request_id: str
    input_text: str             # Normalized user input
    session_id: str             # (Added for context handling)
    history: List[Dict]         # Conversation History
    
    intent: Intent              # PRODUCT_LOCATION / OTHER / UNSUPPORTED
    slots: Dict[str, Any]       # {item, attrs, query_rewrite...}
    
    search_candidates: List[Dict] # DB Search Results
    
    is_ambiguous: bool          # Ambiguity Check Result
    clarification_count: int    # Limit max 1 turn
    
    final_response: NLUResponse # Structured Object for API

# --- 2. Nodes ---

async def nlu_node(state: GraphState):
    """Node 1: Parse User Input"""
    print(f"--- [Node: NLU] Analyzing: {state['input_text']} ---")
    history = state.get("history", [])
    nlu_result = await analyze_text(state['input_text'], history=history)
    
    return {
        "intent": nlu_result.intent,
        "slots": nlu_result.slots.model_dump(),
        "final_response": nlu_result 
    }

async def search_node(state: GraphState):
    """Node 2: Search DB (Hybrid Top-5)"""
    if state["intent"] != Intent.PRODUCT_LOCATION:
        return {"search_candidates": []}
        
    slots = state["slots"]
    item = slots.get("item") or ""
    query_rewrite = slots.get("query_rewrite") or ""
    query = item or query_rewrite
    print(f"--- [Node: Search] Hybrid Querying (Top-5) ---")
    print(f"    NLU slots.item='{item}', query_rewrite='{query_rewrite}'")
    print(f"    Final query: '{query}'")
    
    candidates = []
    if query:
        candidates = search_products(query, top_k=5)
    
    if not candidates and query:
         print(f"    -> 0 results. attempting keyword inference...")
         keywords = await infer_product_keywords(state['input_text'])
         print(f"    -> Inferred keywords: {keywords}")
         for kw in keywords:
             candidates.extend(search_products(kw, top_k=5))
             if candidates: break
             
    print(f"    -> Found {len(candidates)} raw candidates")
    if candidates:
        for i, c in enumerate(candidates[:5]):
            print(f"       [{i+1}] ID={c.get('id')}, Name={c.get('name')}, Score={c.get('score', 0):.4f}")
    return {"search_candidates": candidates}

async def rerank_node(state: GraphState):
    """Node 2.5: LLM Reranking (Top-5 -> Top-3)"""
    candidates = state["search_candidates"]
    if not candidates:
        return {"search_candidates": []}
    
    print(f"--- [Node: Rerank] Ranking Top-{len(candidates)} to Top-3 ---")
    print(f"    Input query: '{state['input_text']}'")
    print(f"    Candidates: {[c.get('name','?') for c in candidates]}")
    from backend.services.rerank_service import rerank_products
    
    try:
        rerank_result = rerank_products(state["input_text"], candidates)
        top_ids = rerank_result.get("top_ids", [])
        reason = rerank_result.get("reason", "")
        print(f"    LLM selected IDs: {top_ids}")
        print(f"    Reason: {reason}")
        
        # Sort and filter candidates based on LLM's top_ids
        reranked = []
        cand_map = {str(c['id']): c for c in candidates}
        
        for rid in top_ids[:3]: 
            clean_id = str(rid).replace("ID", "").replace("id", "").strip()
            if clean_id in cand_map:
                reranked.append(cand_map[clean_id])
        
        # Fallback if rerank failed to find IDs
        if not reranked and candidates:
            print(f"    ⚠️ Rerank returned no matching IDs, using raw top 3")
            reranked = candidates[:3]
                
        print(f"    -> Reranked to {len(reranked)} results: {[r.get('name','?') for r in reranked]}")
        return {"search_candidates": reranked}
    except Exception as e:
        print(f"⚠️ Rerank failed: {e}. Using raw top 3.")
        return {"search_candidates": candidates[:3]}

async def ambiguity_check_node(state: GraphState):
    """Node 3: Check Context/Ambiguity"""
    candidates = state["search_candidates"]
    intent = state["intent"]
    is_ambiguous = False
    
    if intent == Intent.UNSUPPORTED or intent == Intent.OTHER_INQUIRY:
        is_ambiguous = False
    elif not candidates:
        is_ambiguous = True
    elif state["final_response"].needs_clarification:
        is_ambiguous = True
        
    history = state.get("history", [])
    if history and history[-1]["role"] == "assistant":
        last_msg = history[-1]["text"]
        if "?" in last_msg or "어떤" in last_msg or "입니까" in last_msg:
             print("--- [Node: Ambiguity] Loop Detected. Forcing Answer. ---")
             is_ambiguous = False
        
    print(f"--- [Node: Ambiguity] Is Ambiguous? {is_ambiguous} ---")
    return {"is_ambiguous": is_ambiguous}

async def clarification_node(state: GraphState):
    """Node 4: Generate Tail Question"""
    print(f"--- [Node: Clarification] Generating Question ---")
    candidates = state["search_candidates"]
    slots = state["slots"]
    from backend.database.category_matcher import get_drill_down_context
    db_context = get_drill_down_context(candidates)

    question = await generate_tail_question(state["input_text"], slots, db_context=db_context)
    
    resp = state["final_response"]
    resp.needs_clarification = True
    resp.generated_question = question
    resp.products = candidates
    
    return {
        "final_response": resp,
        "clarification_count": state["clarification_count"] + 1
    }

async def response_node(state: GraphState):
    """Node 5: Finalize Answer"""
    print(f"--- [Node: Response] Finalizing ---")
    resp = state["final_response"]
    
    # Explicitly validate and convert to Product models to avoid Pydantic serialization errors
    candidates = state["search_candidates"]
    try:
        product_objects = [Product(**c) for c in candidates]
        resp.products = product_objects
    except Exception as e:
        print(f"⚠️ Product validation failed: {e}")
        # Fallback: try to pass as is, though it might fail serialization
        resp.products = candidates # type: ignore

    if state["intent"] == Intent.UNSUPPORTED:
        resp.generated_question = "죄송합니다. 상품 찾기 외의 질문은 아직 답변하기 어렵습니다."
        resp.needs_clarification = True
    elif not resp.generated_question:
        query = state['input_text']
        count = len(resp.products)
        resp.generated_question = f"요청하신 '{query}' 관련 상품 {count}개를 찾았습니다."
        
    return {"final_response": resp}

# --- 3. Edges ---
def route_after_ambiguity(state: GraphState):
    if state["is_ambiguous"] and state["clarification_count"] < 1:
        return "clarification"
    return "final_response"

# --- 4. Graph Construction ---
workflow = StateGraph(GraphState)
workflow.add_node("nlu", nlu_node)
workflow.add_node("search", search_node)
workflow.add_node("rerank", rerank_node)
workflow.add_node("ambiguity_check", ambiguity_check_node)
workflow.add_node("clarification", clarification_node)
workflow.add_node("final_response", response_node)

workflow.set_entry_point("nlu")
workflow.add_edge("nlu", "search")
workflow.add_edge("search", "rerank")
workflow.add_edge("rerank", "ambiguity_check")
workflow.add_conditional_edges("ambiguity_check", route_after_ambiguity, {"clarification": "clarification", "final_response": "final_response"})
workflow.add_edge("clarification", END)
workflow.add_edge("final_response", END)

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
