
import os
import json
import time
import google.generativeai as genai
from sentence_transformers import CrossEncoder
from tqdm import tqdm
from dotenv import load_dotenv

# Setup
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_mock_product_db.json")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_golden_test_cases.json")

# Dummy Candidates Loader (In real flow, this comes from Step 2)
def load_data():
    if not os.path.exists(DATA_PATH): return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

PRODUCTS = load_data()
PRODUCT_MAP = {p['id']: p for p in PRODUCTS}

# ===========================
# Reranking Models
# ===========================

# 1. Cross Encoder
try:
    print("🧠 Loading Cross-Encoder...")
    # Use a small, fast model
    ce_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
except Exception as e:
    print(f"Error loading CrossEncoder: {e}")
    ce_model = None

def rerank_cross_encoder(query, candidates, top_k=5):
    if not ce_model or not candidates: return candidates[:top_k]
    
    pairs = [[query, f"{c['name']} {c.get('desc','')}"] for c in candidates]
    scores = ce_model.predict(pairs)
    
    # Attach scores and sort
    scored_candidates = []
    for c, s in zip(candidates, scores):
        c_new = c.copy()
        c_new['_ce_score'] = float(s)
        scored_candidates.append(c_new)
        
    scored_candidates.sort(key=lambda x: x['_ce_score'], reverse=True)
    return scored_candidates[:top_k]

# 2. LLM Reranker (Gemini)
def rerank_llm(query, candidates, top_k=5, user_intent=None):
    if not candidates: return []
    
    candidate_text = "\n".join([f"ID {c['id']}: {c['name']} (Desc: {c.get('desc','')[:50]}..., Loc: {c.get('location','')})" for c in candidates])
    
    intent_str = f"(Intent: {json.dumps(user_intent)})" if user_intent else ""
    
    prompt = f"""
    You are an AI Search Reranker & Location Guide.
    Query: "{query}" {intent_str}

    Task 1: Rerank the following candidates by relevance to the query/intent.
    Task 2: Select the BEST one (Top-1) and provide its ID and Location.

    Candidates:
    {candidate_text}

    Output JSON Only:
    {{
        "ranked_ids": [id1, id2, ...],
        "top_match_id": id1,
        "location_guide_text": "Item is located at [Location]...",
        "reason": "..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        result = json.loads(text)
        
        # Reconstruct detailed list
        ranked_ids = result.get('ranked_ids', [])
        reranked = []
        for rid in ranked_ids:
            item = PRODUCT_MAP.get(rid)
            if item: reranked.append(item)
            
        # Append leftovers if any missing
        retrieved_ids = set(c['id'] for c in candidates)
        rank_ids_set = set(ranked_ids)
        for c in candidates:
            if c['id'] not in rank_ids_set:
                reranked.append(c)
                
        return reranked[:top_k], result # Return meta result too
    except Exception as e:
        print(f"LLM Rerank Error: {e}")
        return candidates[:top_k], {}

# ===========================
# Experiment
# ===========================
def run_experiment():
    if not os.path.exists(TEST_CASES_PATH):
        print("❌ Test cases not found.")
        return

    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    print(f"🧪 Testing AG Reranking on {len(cases)} cases...")
    
    ce_score = 0
    llm_score = 0
    location_accuracy = 0
    total = 0
    
    for case in cases:
        query = case['query']
        ground_truth = case.get('ground_truth_ids_hint', [])
        if not ground_truth: continue
        total += 1
        
        # Simulate retrieval (cheat: just pick ground truth + random noise)
        candidates = [PRODUCT_MAP[gid] for gid in ground_truth if gid in PRODUCT_MAP]
        # Add noise
        noise = [p for p in PRODUCTS if p['id'] not in ground_truth][:10]
        candidates += noise
        
        # 1. Run CE
        res_ce = rerank_cross_encoder(query, candidates, top_k=1)
        if res_ce and res_ce[0]['id'] in ground_truth:
            ce_score += 1
            
        # 2. Run LLM
        res_llm, meta = rerank_llm(query, candidates, top_k=1, user_intent=case.get('expected_intent'))
        if res_llm and res_llm[0]['id'] in ground_truth:
            llm_score += 1
            
            # Check location
            real_loc = res_llm[0]['location']
            guide_text = meta.get('location_guide_text', '')
            if real_loc in guide_text:
                location_accuracy += 1
                
        print(f"Case {total}: Q='{query}' | CE={'✅' if res_ce and res_ce[0]['id'] in ground_truth else '❌'} | LLM={'✅' if res_llm and res_llm[0]['id'] in ground_truth else '❌'}")
        
    print("\n📊 Final Results")
    print(f"Total Evaluated: {total}")
    print(f"Cross-Encoder Top-1 Acc: {ce_score}/{total} ({ce_score/total*100:.1f}%)")
    print(f"LLM (Gemini) Top-1 Acc : {llm_score}/{total} ({llm_score/total*100:.1f}%)")
    print(f"LLM Location Guide Acc : {location_accuracy}/{total} ({location_accuracy/total*100:.1f}%)")

if __name__ == "__main__":
    run_experiment()
