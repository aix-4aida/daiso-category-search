
import os
import json
import time
import sys
import random
import google.generativeai as genai
from dotenv import load_dotenv

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
1. Intent First: Understand the user's core need.
2. Context Aware: If the query is broad, prefer the most standard/popular item.
3. Strict Negative Filtering: If a user says "NO plastic", reject plastic items.
4. Null Safety: If NO candidate matches the intent, return `null`. Do NOT force a selection.
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
        
        # Parse just to verify validity, though we only track latency here
        result = json.loads(response.text)
        result['latency'] = latency
        return result

    except Exception as e:
        # print(f"Error in rerank: {e}")
        return {"selected_id": None, "reason": f"Error: {str(e)}", "latency": 0}

def mock_qr_generation(url):
    """
    Simulates the time taken to generate a QR code.
    Client-side JS QR generation (approx 20-50ms).
    """
    # Simulate processing time
    time.sleep(0.03) # 30ms
    return f"[QR Object for {url}]"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_path = os.path.join(base_dir, 'data', 'poc_v5_golden_test_cases.json')
    product_db_path = os.path.join(base_dir, 'data', 'poc_v5_mock_product_db.json')

    print(f"Loading data from {test_cases_path}...")
    
    with open(test_cases_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    with open(product_db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    full_latencies = []
    
    print("\n=== Full Benchmark (All Cases) ===")
    print(f"Total Test Cases: {len(test_cases)}\n")

    for i, tc in enumerate(test_cases):
        query = tc['query']
        hints = tc.get('candidates_hint', [])
        
        # Prepare candidates (Mock Retrieval)
        candidates = []
        for hint in hints:
            found = False
            for p in products:
                if hint in p['name']:
                    candidates.append(p)
                    found = True
                    break 
            if not found:
                candidates.append(products[random.randint(0, len(products)-1)])
        
        while len(candidates) < 3:
             candidates.append(products[random.randint(0, len(products)-1)])

        # Measure 1) Query to Rerank
        t1_start = time.time()
        rerank_result = advanced_rerank(query, candidates)
        t1_end = time.time()
        
        rerank_duration = t1_end - t1_start
        api_latency = rerank_result.get('latency', 0) # This is purely API time

        # Measure 2) Rerank to QR
        # Assume we construct URL then gen QR
        t2_start = time.time()
        target_id = rerank_result.get('selected_id', '000')
        mock_url = f"https://example.com/mobile?id={target_id}"
        _ = mock_qr_generation(mock_url)
        t2_end = time.time()
        
        qr_gen_duration = t2_end - t2_start

        # Total
        total_duration = t2_end - t1_start
        full_latencies.append(total_duration)

        # Log
        print(f"[{i+1}/{len(test_cases)}] Query: {query}")
        print(f"  1) 쿼리입력 ~ 리랭킹 결과: {rerank_duration:.4f}초")
        print(f"  2) 리랭킹 결과 ~ QR생성: {qr_gen_duration:.4f}초 (Simulated)")
        print(f"  3) API 호출: 1번, {api_latency:.4f}초")
        print(f"  4) 총 소요 시간: {total_duration:.4f}초")
        print("-" * 40)
        
        # Rate limit safety
        time.sleep(0.5)

    if not full_latencies:
        print("No results.")
        return

    min_t = min(full_latencies)
    max_t = max(full_latencies)
    avg_t = sum(full_latencies) / len(full_latencies)

    print("\n=== 최종 결과 요약 (Query to QR) ===")
    print(f"최소 시간: {min_t:.4f}초")
    print(f"최대 시간: {max_t:.4f}초")
    print(f"평균 시간: {avg_t:.4f}초")

if __name__ == "__main__":
    main()
