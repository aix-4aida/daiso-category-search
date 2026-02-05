
import os
import json
import time
import random
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Add current directory to path to import poc_v5_experiment_phase_1
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from poc_v5_experiment_phase_1 import advanced_rerank
except ImportError:
    # If import fails, we might need to redefine advanced_rerank here or fix path
    # But let's try assuming it works or copy-paste if needed.
    # To be safe, let's just redefine the setup and function here to be standalone
    # copying from poc_v5_experiment_phase_1.py
    
    # Setup Environment
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    
    SYSTEM_PROMPT = """
You are an expert AI Search Agent for Daiso (a variety store).
Your goal is to select the BEST matching product from a list of candidates based on a user's query.

[Principles]
1.  **Intent First**: Understand the user's core need.
2.  **Context Aware**: If the query is broad, prefer the most standard/popular item.
3.  **Strict Negative Filtering**: If a user says "NO plastic", reject plastic items.
4.  **Null Safety**: If NO candidate matches the intent, return `null`. Do NOT force a selection.
    """

    def advanced_rerank(user_query, candidates):
        if not candidates:
            return {"selected_id": None, "reason": "No candidates provided."}

        candidate_text = ""
        for c in candidates:
            name = c.get('name', 'Unknown')
            desc = c.get('desc', '') or c.get('searchable_desc', '') or "No description"
            desc = desc[:100] 
            candidate_text += f"- ID {c['id']}: {name} (Desc: {desc})\n"

        prompt = f"""
        {SYSTEM_PROMPT}

        [Current Task]
        User Query: "{user_query}"
        
        Candidates:
        {candidate_text}
        
        Output JSON:
        {{
            "selected_id": "string or null",
            "reason": "string (Korean)"
        }}
        """

        try:
            start_time = time.time()
            response = model.generate_content(prompt)
            latency = time.time() - start_time
            
            result = json.loads(response.text)
            result['latency'] = latency
            return result

        except Exception as e:
            print(f"Error in rerank: {e}")
            return {"selected_id": None, "reason": f"Error: {str(e)}", "latency": 0}

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_path = os.path.join(base_dir, 'data', 'poc_v5_golden_test_cases.json')
    product_db_path = os.path.join(base_dir, 'data', 'poc_v5_mock_product_db.json')

    print(f"Loading data from {test_cases_path} and {product_db_path}...")
    
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    with open(product_db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    # Pick random 10 cases
    sample_cases = random.sample(test_cases, 10)
    latencies = []

    print("\nStarting Benchmark (10 samples)...")
    
    for i, tc in enumerate(sample_cases):
        query = tc['query']
        hints = tc.get('candidates_hint', [])
        
        # Build candidates list
        candidates = []
        for hint in hints:
            # Find matching product in DB by name substring
            found = False
            for p in products:
                if hint in p['name']:
                    candidates.append(p)
                    found = True
                    break # Take first match
            if not found:
                # Fallback: pick random product
                candidates.append(random.choice(products))
        
        # Ensure we have at least 3 candidates
        while len(candidates) < 3:
             candidates.append(random.choice(products))
             
        # Run Rerank
        print(f"[{i+1}/10] Query: '{query}' with {len(candidates)} candidates...", end="", flush=True)
        result = advanced_rerank(query, candidates)
        lat = result.get('latency', 0)
        latencies.append(lat)
        print(f" Done. Latency: {lat:.4f}s")
        # specific to API limits, maybe sleep a bit? 
        # Gemini 2.0 Flash should be fast and high rate limit, but lets be safe
        time.sleep(0.5)

    if not latencies:
        print("No successful measurements.")
        return

    min_lat = min(latencies)
    max_lat = max(latencies)
    avg_lat = sum(latencies) / len(latencies)

    print("\n=== Benchmark Results ===")
    print(f"Samples: {len(latencies)}")
    print(f"Min Latency: {min_lat:.4f}s")
    print(f"Max Latency: {max_lat:.4f}s")
    print(f"Avg Latency: {avg_lat:.4f}s")

if __name__ == "__main__":
    main()
