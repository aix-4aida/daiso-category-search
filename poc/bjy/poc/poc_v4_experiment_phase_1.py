
import os
import json
import time
import random
import google.generativeai as genai
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

# Setup
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v4_mock_product_db.json")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v4_golden_test_cases.json")

# 1. Load Data
def load_data():
    if not os.path.exists(DATA_PATH): return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

PRODUCTS = load_data()
PRODUCT_MAP = {p['id']: p for p in PRODUCTS}

# 2. Intent Extraction (Phase 1 in Sequence)
INTENT_PROMPT = """
You are a 'Search Query Processor' for a Daiso product search engine.
Your goal is to extract structured intent from the user's natural language query.

Context:
- User is searching for household goods.
- Determine if the query is a "Search" intent or something else.
- Extract "Keywords" for retrieval.
- Extract "Filters" if explicitly stated (e.g., "cheap", "no plastic").

Input Query: "{query}"

Output JSON Format:
{{
    "is_search_intent": true/false,
    "keywords": ["term1", "term2"],
    "filters": {{ "category": "...", "attributes": "...", "negatives": "..." }}
}}
"""

def extract_intent(query):
    try:
        prompt = INTENT_PROMPT.replace("{query}", query)
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️ Intent Extraction Error: {e}")
        return {"keywords": query.split(), "is_search_intent": True}

# 3. Reranking (Phase 2 & 3 in Sequence)
def rerank_llm(query, intent, candidates, top_k=1):
    if not candidates: return [], {}
    
    candidate_text = "\n".join([f"ID {c['id']}: {c['name']} (Desc: {c.get('searchable_desc','')[:100]}..., Loc: {c.get('location','')})" for c in candidates])
    
    intent_str = json.dumps(intent, ensure_ascii=False)
    
    prompt = f"""
    You are an AI Search Agent.
    User Query: "{query}"
    Extracted Intent: {intent_str}

    Task:
    1. Analyze the candidates based on the user's specific request (consider filters, descriptions, negations).
    2. Select the BEST matching item (Top-1) that satisfies the user's need.
    3. If no item perfectly matches, select the closest alternative or explain why none match.

    Candidates:
    {candidate_text}

    Output JSON Only:
    {{
        "top_match_id": id,
        "reason": "Explain why this item was chosen based on the query nuances (e.g., matches description, satisfies negative constraint)."
    }}
    """
    
    try:
        start_time = time.time()
        response = model.generate_content(prompt)
        latency = time.time() - start_time
        
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        result = json.loads(text)
        result['latency'] = latency
        
        top_id = result.get('top_match_id')
        top_item = PRODUCT_MAP.get(top_id)
        
        return ([top_item] if top_item else []), result
    except Exception as e:
        print(f"  ⚠️ Rerank Error: {e}")
        return [], {}

# 4. Main Experiment Flow
def run_experiment():
    if not os.path.exists(TEST_CASES_PATH):
        print("❌ Test cases not found.")
        return

    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    print(f"🧪 Running PoC v4 Experiment on ALL {len(cases)} cases...")
    print("-" * 60)
    
    # Run all cases
    cases = cases
    
    success_count = 0
    total_valid = 0
    
    results = []

    for i, case in enumerate(cases):
        query = case['query']
        ground_truth = case.get('ground_truth_ids_hint', [])
        scenario = case.get('scenario_type', 'Unknown')
        
        print(f"\n[Case {i+1}] Query: '{query}' ({scenario})")
        
        # Step 1: Intent Extraction
        intent = extract_intent(query)
        print(f"  🧠 Intent: {intent.get('keywords')} | Filters: {intent.get('filters')}")
        
        if not ground_truth:
            # For False Positive / No Match Expected cases
            # If we simply simulate retrieval, we need to decide what to retrieve.
            # Here, we'll retrieve random items to see if the LLM correctly rejects them or finds nothing.
            candidates = random.sample(PRODUCTS, min(len(PRODUCTS), 10))
        else:
            # Step 2: Simulate Retrieval (Ground Truth + Noise)
            # Ensure Ground Truth is in candidates
            candidates = [PRODUCT_MAP[gid] for gid in ground_truth if gid in PRODUCT_MAP]
            
            # Add Noise (random items that are NOT ground truth)
            noise_candidates = [p for p in PRODUCTS if p['id'] not in ground_truth]
            noise = random.sample(noise_candidates, min(len(noise_candidates), 10))
            candidates += noise
            random.shuffle(candidates)
            
        # Step 3: LLM Reranking & Selection
        top_items, meta = rerank_llm(query, intent, candidates, top_k=1)
        
        # Evaluation
        is_correct = False
        reason = meta.get('reason', 'N/A')
        latency = meta.get('latency', 0)
        
        selected_id = top_items[0]['id'] if top_items else None
        selected_name = top_items[0]['name'] if top_items else "None"
        
        if not ground_truth:
            # Expecting None/Empty for "False Positive"
            # However, our reranker is forced to pick Top-1 usually. 
            # Ideally, the prompt should allow returning null.
            # For this PoC, let's see if it picks something irrelevant or if we consider any pick as failure.
            # If the user asks for TV and we show a trash bag, it's a failure.
            # But since we just simulated retrieval with random stuff, it's hard to judge.
            # For PoC simplicity, we count "False Positive" scenarios:
            # If reasonable rejection logic isn't improved, it might fail.
            pass 
        else:
            if selected_id in ground_truth:
                is_correct = True
                success_count += 1
            total_valid += 1

        status = "✅ PASS" if is_correct else "❌ FAIL"
        if not ground_truth: status = "❓ N/A (No GT)"
        
        print(f"  🎯 result: {status} | Selected: {selected_id} ({selected_name})")
        # print(f"  💡 Reason: {reason}")
        
        results.append({
            "query": query,
            "scenario": scenario,
            "selected_id": selected_id,
            "selected_name": selected_name,
            "ground_truth": ground_truth,
            "is_correct": is_correct,
            "reason": reason
        })

    print("-" * 60)
    print(f"📊 Final Accuracy (on cases with GT): {success_count}/{total_valid} ({success_count/total_valid*100:.1f}%)" if total_valid > 0 else "No valid GT cases")

if __name__ == "__main__":
    run_experiment()
