
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
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key: genai.configure(api_key=api_key)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "products_large.json")
TEST_INPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "rag_test_keywords.json")

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

def load_prompt(filename):
    path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def classify_intent(query, categories):
    """[Issue 3] Intent Classifier (Loaded from prompts/intent_rules_prompt.txt)"""
    if not api_key: return "Error"
    
    cat_list_str = ", ".join(categories)
    try:
        prompt_template = load_prompt("intent_rules_prompt.txt")
        prompt = prompt_template.replace("{query}", query).replace("{cat_list_str}", cat_list_str)
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        pred = response.text.strip()
        # Cleanup
        for c in categories:
            if c in pred: return c
        return pred
    except Exception as e:
        print(f"Intent Error: {e}")
        return "Error"

def vector_search(query, products, top_k=10):
    """[Issue 1] Vector Search"""
    q_vec = get_embedding(query)
    
    scored = []
    for p in products:
        # Cache embeddings if not present (simple in-memory cache for this run)
        if "emb" not in p:
            # Enrich context: name + desc + category
            text = f"{p['name']} {p['desc']} {p['category']}" 
            p["emb"] = get_embedding(text)
        
        score = cosine_similarity(q_vec, p["emb"])
        scored.append({**p, "score": float(score)}) # flatten
        
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def rerank_results(query, candidates):
    """[Issue 2] LLM Reranker (Loaded from prompts/rerank_prompt.txt)"""
    if not api_key: return []
    
    cand_text = "\n".join([f"ID {c['id']}: {c['name']} ({c['desc']})" for c in candidates])
    
    try:
        prompt_template = load_prompt("rerank_prompt.txt")
        # Use simple replace to avoid f-string complexity with json braces in txt
        prompt = prompt_template.replace("{query}", query).replace("{candidate_text}", cand_text)
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        import re
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"Rerank Error: {e}")
    return []

def run_simulation():
    print("📦 Loading Data...")
    products = load_json(DATA_PATH)
    test_inputs = load_json(TEST_INPUT_PATH)
    all_categories = list(set(p['category'] for p in products))
    print(f"✅ Loaded {len(products)} products, {len(test_inputs)} validation keywords.")
    
    # Test Loop for different K parameters
    k_candidates = [10, 30, 50]
    
    for k_val in k_candidates:
        print(f"\n" + "="*80)
        print(f"🧪 [Test 6] Running Simulation with Top-K={k_val} ...")
        print("="*80)
        
        stats = {
            "intent_correct": 0,
            "retrieval_success": 0, 
            "rerank_success": 0,    
            "total": len(test_inputs)
        }
    
        print(f"{'Keyword':<15} | {'Intent':<6} | {'Ret.(K=' + str(k_val) + ')':<10} | {'Rerank(Top1)':<10}")
        print("-" * 80)
        
        for case in test_inputs:
            query = case['keyword'] 
            expected_cat = case['expected_category']
            target_kw = case['target_keyword']
            
            # 1. Intent Classification
            pred_cat = classify_intent(query, all_categories)
            intent_ok = (pred_cat == expected_cat)
            if intent_ok: stats["intent_correct"] += 1
            
            # 2. Retrieval (K_VAL affected)
            if intent_ok:
                scope = [p for p in products if p['category'] == pred_cat]
            else:
                scope = products
                
            retrieved = vector_search(query, scope, top_k=k_val)
            
            # Check Retrieval Recall
            hit_retrieval = any(target_kw in r['name'] for r in retrieved)
            if hit_retrieval: stats["retrieval_success"] += 1
            
            # 3. Reranking (Candidate pool size increased by K)
            reranked_meta = rerank_results(query, retrieved)
            
            top1_item = None
            if reranked_meta:
                top1_id = reranked_meta[0]['id']
                top1_item = next((r for r in retrieved if r['id'] == top1_id), None)
            else:
                top1_item = retrieved[0] if retrieved else None
                
            hit_rerank = (top1_item and target_kw in top1_item['name'])
            if hit_rerank: stats["rerank_success"] += 1
            
            # Log Failures Only (to reduce noise)
            if not (intent_ok and hit_retrieval and hit_rerank):
                log_intent = "✅" if intent_ok else f"❌({pred_cat})"
                log_ret = "✅" if hit_retrieval else "❌"
                log_rank = "✅" if hit_rerank else f"❌({top1_item['name'][:5] + '..' if top1_item else 'None'})"
                print(f"{query[:15]:<15} | {log_intent:<6} | {log_ret:<10} | {log_rank:<10}")
            
        print("-" * 80)
        print(f"📊 Score (K={k_val}, N={stats['total']})")
        print(f"1. Intent Accuracy: {stats['intent_correct']}/{stats['total']} ({stats['intent_correct']/stats['total']*100:.1f}%)")
        print(f"2. Retrieval Recall: {stats['retrieval_success']}/{stats['total']} ({stats['retrieval_success']/stats['total']*100:.1f}%)")
        print(f"3. Rerank Precision: {stats['rerank_success']}/{stats['total']} ({stats['rerank_success']/stats['total']*100:.1f}%)")


if __name__ == "__main__":
    run_simulation()
