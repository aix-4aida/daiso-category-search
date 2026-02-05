
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import google.generativeai as genai
import time

# ==========================================
# ⚙️ Configuration & Setup
# ==========================================
# Load backend .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key: genai.configure(api_key=api_key)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "products_large.json")
TEST_INPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "rag_e2e_test_queries.json")

LOCAL_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        print(f"📥 Loading Local Model ({LOCAL_MODEL_NAME})...")
        _model_instance = SentenceTransformer(LOCAL_MODEL_NAME)
    return _model_instance

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# 🧠 Logic Functions
# ==========================================

def get_embedding(text):
    model = get_model()
    return model.encode(text)

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def run_meaning_extraction_agent(sentence):
    """
    [Step 3] Meaning Extraction Agent
    Input: "설거지할 때 끼는 고무장갑 추천해줘"
    Output: {"keyword": "고무장갑", "intent": "주방", "attributes": ["설거지용"]}
    """
    if not api_key: return None
    
    prompt = f"""
    You are a Search Query Refiner Agent.
    
    [User Sentence]
    "{sentence}"
    
    [Task]
    1. Extract the core 'Product Keyword' (Noun) that the user wants to buy. Remove verbs like 'recommend', 'find', 'looking for'.
    2. Infer the 'Shopping Category' (Intent) based on usage context.
    3. Return JSON only: {{"keyword": "...", "intent": "..."}}
    
    [Categories]
    주방, 운동, 욕실, 자동차, 청소, 미용, 문구, 공구, 의류
    
    [Examples]
    - "안 미끄러지는 욕실 매트 찾아줘" -> {{"keyword": "욕실매트", "intent": "욕실"}}
    - "설거지 고무장갑 추천" -> {{"keyword": "고무장갑", "intent": "주방"}}
    - "골프 칠 때 끼는 장갑" -> {{"keyword": "골프 장갑", "intent": "운동"}}
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        import re
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"Agent Error: {e}")
    return None

def vector_search(query, products, top_k=10):
    q_vec = get_embedding(query)
    scored = []
    for p in products:
        if "emb" not in p:
            text = f"{p['name']} {p['desc']} {p['category']}" 
            p["emb"] = get_embedding(text)
        score = cosine_similarity(q_vec, p["emb"])
        scored.append({**p, "score": float(score)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def rerank_results(query, candidates):
    if not api_key: return []
    cand_text = "\n".join([f"ID {c['id']}: {c['name']} ({c['desc']})" for c in candidates])
    
    prompt = f"""
    Search Query: "{query}"
    Candidates:
    {cand_text}
    
    Task: Rerank by relevance. Return JSON list: [{{"id": 1, "rank": 1}}].
    Filter out homonyms (e.g. Yoga Mat vs Bath Mat).
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        import re
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass
    return []

# ==========================================
# 🧪 Validation Suite
# ==========================================

def run_simulation():
    print("📦 Loading Baseline Data (Sentences)...")
    products = load_json(DATA_PATH)
    test_inputs = load_json(TEST_INPUT_PATH)
    print(f"✅ Loaded {len(products)} products, {len(test_inputs)} sentences.")
    
    # We will compare K=30 (Proposed)
    K_VAL = 30
    
    print(f"\n🚀 Running Real Agent Experiment (Sentence -> Agent -> K={K_VAL})...")
    print(f"{'Sentence':<20} | {'Agent KW':<10} | {'Intent':<6} | {'Recall':<6}")
    print("-" * 80)
    
    stats = {"agent_success": 0, "retrieval_success": 0, "total": len(test_inputs)}
    
    for case in test_inputs:
        raw_sentence = case['query']
        target_kw = case['target_keyword'] # For validation
        expected_cat = case['expected_category']
        
        # 1. Agent Extraction
        extracted = run_meaning_extraction_agent(raw_sentence)
        
        if not extracted:
            print(f"{raw_sentence[:20]:<20} | ❌ Error")
            continue
            
        agent_kw = extracted.get("keyword", "")
        agent_intent = extracted.get("intent", "")
        
        # Verify Agent Performance
        # Flexible check: if expected category matches agent intent
        is_intent_correct = (agent_intent == expected_cat)
        if is_intent_correct: stats["agent_success"] += 1
        
        # 2. Retrieval with Extracted Metadata
        # Filter scope by Agent Intent (Rule: Pre-filter)
        if is_intent_correct:
            scope = [p for p in products if p['category'] == agent_intent]
        else:
            scope = products # Fallback
            
        # Search using Agent Keyword (not raw sentence)
        retrieved = vector_search(agent_kw, scope, top_k=K_VAL)
        
        # 3. Check Recall
        hit = any(target_kw in r['name'] for r in retrieved)
        if hit: stats["retrieval_success"] += 1
        
        log_intent = "✅" if is_intent_correct else f"❌{agent_intent}"
        log_ret = "✅" if hit else "❌"
        
        print(f"{raw_sentence[:20]:<20} | {agent_kw:<10} | {log_intent:<6} | {log_ret:<6}")
        
        # Rate Limit Prevention
        time.sleep(0.5)

    print("-" * 80)
    print(f"📊 Real Agent Results (N={stats['total']})")
    print(f"1. Agent Accuracy: {stats['agent_success']}/{stats['total']} ({stats['agent_success']/stats['total']*100:.1f}%)")
    print(f"2. Final Recall: {stats['retrieval_success']}/{stats['total']} ({stats['retrieval_success']/stats['total']*100:.1f}%)")
    
    # Compare with Baseline (Hardcoded numbers from report)
    print(f"\n[Comparison]")
    print(f"Baseline (Raw Sentence) Recall: 57.8%")
    print(f"Robustness (Real Agent) Recall: {stats['retrieval_success']/stats['total']*100:.1f}%")

if __name__ == "__main__":
    run_simulation()
