import os
import json
import time
import google.generativeai as genai
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Setup Environment
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Model Configuration
# Using Gemini 2.0 Flash for speed and reasoning capability
# Set response_mime_type to application/json for strict structured output
model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={"response_mime_type": "application/json"}
)

# --- SYSTEM PROMPT (The "Brain" of PoC v5) ---
SYSTEM_PROMPT = """
You are an expert AI Search Agent for Daiso (a variety store).
Your goal is to select the BEST matching product from a list of candidates based on a user's query.

[Principles]
1.  **Intent First**: Understand the user's core need. (e.g., "net for frying" -> Kitchen tool, NOT laundry net).
2.  **Context Aware**: If the query is broad (e.g., "detergent"), prefer the most standard/popular item unless context implies otherwise.
3.  **Strict Negative Filtering**: If a user says "NO plastic", reject plastic items.
4.  **Null Safety**: If NO candidate matches the intent, return `null`. Do NOT force a selection.

[Few-Shot Examples]

**Example 1: Specific Function**
User Query: "튀김 건질 때 쓰는 거"
Candidates:
- ID A1: "세탁망 (원형)" - 세탁기용 망
- ID B2: "스텐 채반 (손잡이형)" - 튀김/면 요리용
- ID C3: "튀김가루 1kg" - 식재료
Reasoning: User needs a tool to scoop fried food. A1 is for laundry (wrong category). C3 is an ingredient (wrong category). B2 is the correct tool.
Output: {"selected_id": "B2", "reason": "사용자가 조리 도구를 찾고 있으며, 스텐 채반이 튀김 건지기에 가장 적합합니다."}

**Example 2: Distractor / Trap**
User Query: "아이폰 충전기"
Candidates:
- ID D1: "건전지 AA 2개입"
- ID D2: "갤럭시 C타입 케이블" - 삼성 호환
- ID D3: "멀티탭 3구"
Reasoning: User specifically asked for "iPhone". D2 is for Galaxy (C-type might work for iPhone 15, but usually implies Lightning or 'iPhone' compatible). D1 and D3 are irrelevant. Since no explicit iPhone cable is here, better to act safe or reject if strictly incompatible. However, C-type is standard now. Let's look for explicit match. If none, return null.
Output: {"selected_id": null, "reason": "후보군에 아이폰 전용 충전기나 케이블이 없습니다."}

**Example 3: Visual Description**
User Query: "그.. 뽁뽁이.. 겨울에 창문에 붙이는거"
Candidates:
- ID E1: "단열 시트 (에어캡)"
- ID E2: "장난감 뽁뽁이"
- ID E3: "투명 테이프"
Reasoning: "뽁뽁이" is a slang for bubble wrap. Context "winter/window" confirms it's for insulation. E1 is the exact product.
Output: {"selected_id": "E1", "reason": "'뽁뽁이'는 에어캡의 은어이며, 겨울철 창문에 붙인다는 문맥으로 보아 단열 시트가 정답입니다."}

**Example 4: Broken English / Phonetic**
User Query: "Jongee Tape"
Candidates:
- ID F1: "박스 테이프 (투명)"
- ID F2: "마스킹 테이프 (종이)"
Reasoning: "Jongee" sounds like "Jong-i" (Paper) in Korean. User wants Paper Tape. F2 is the correct match.
Output: {"selected_id": "F2", "reason": "'Jongee'는 '종이'의 발음 표기이며, 종이 테이프인 마스킹 테이프가 적합합니다."}
"""

def advanced_rerank(user_query, candidates):
    """
    Reranks candidates using Gemini 2.0 Flash with CoT.
    Returns a dict with 'selected_id' and 'reason'.
    """
    if not candidates:
        return {"selected_id": None, "reason": "No candidates provided."}

    # Prepare Candidate Text
    candidate_text = ""
    for c in candidates:
        # Use clean fields if available, otherwise raw
        name = c.get('name', 'Unknown')
        desc = c.get('desc', '') or c.get('searchable_desc', '') or "No description"
        # Cut desc length to save tokens but keep essence
        desc = desc[:100] 
        candidate_text += f"- ID {c['id']}: {name} (Desc: {desc})\n"

    # Construct Full Prompt
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
        return {"selected_id": None, "reason": f"Error: {str(e)}"}

# For quick testing
# if __name__ == "__main__":
#     test_query = "싱크대 거름망"
#     test_candidates = [
#         {"id": "100", "name": "싱크대 거름망 (스텐)", "desc": "배수구 찌꺼기 거름"},
#         {"id": "101", "name": "거름망 트랩", "desc": "냄새 차단"},
#         {"id": "102", "name": "수세미", "desc": "설거지용"}
#     ]
#     print(advanced_rerank(test_query, test_candidates))

def load_catalog(catalog_path):
    """Loads catalog TSV into a dict {doc_id: {id, name, desc}}"""
    products = {}
    if not os.path.exists(catalog_path):
        print(f"Warning: Catalog file not found: {catalog_path}")
        return products
        
    with open(catalog_path, 'r', encoding='utf-8') as f:
        # Skip header if exists (starts with # or id)
        for line in f:
            if line.startswith("#") or line.lower().startswith("doc_id") or line.lower().startswith("id"):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                doc_id = parts[0]
                title = parts[1]
                text = parts[2]
                # desc is text
                products[doc_id] = {"id": doc_id, "name": title, "desc": text}
    return products

def process_benchmark_output(run_dir, catalog_path, output_file):
    run_path = Path(run_dir)
    detail_path = run_path / "detail.jsonl"
    
    if not detail_path.exists():
        print(f"Error: detail.jsonl not found in {run_dir}")
        return

    print(f"Loading catalog from {catalog_path}...")
    catalog = load_catalog(catalog_path)
    
    print(f"Processing benchmark results from {detail_path}...")
    
    results = []
    
    with open(detail_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            row = json.loads(line)
            
            # detail.jsonl has nested structure: {"type": "case", "payload": {...}}
            # We need to extract the payload for case entries
            if row.get("type") != "case":
                continue
            
            case = row.get("payload", {})
            if "case_id" not in case: continue
            
            query = case.get("intent_text", "") or case.get("raw_text", "")
            
            # Get candidates from retrieval phase
            # run_benchmark outputs 'predicted_doc_ids' (Top N)
            # User request: Limit to Top 3
            top_ids = case.get("predicted_doc_ids", [])[:3]
            
            candidates = []
            retrieved_display = [] # To show ID + Name
            
            for doc_id in top_ids:
                if doc_id in catalog:
                    item = catalog[doc_id]
                    candidates.append(item)
                    retrieved_display.append(f"{doc_id} ({item['name']})")
                else:
                    candidates.append({"id": doc_id, "name": "Unknown", "desc": ""})
                    retrieved_display.append(f"{doc_id} (Unknown)")
            
            print(f"Reranking Query: '{query}' ({len(candidates)} candidates)...")
            
            # Call KDG Reranker
            rerank_result = advanced_rerank(query, candidates)
            
            # Add selected item name for clarity
            sel_id = rerank_result.get("selected_id")
            sel_name = ""
            if sel_id and sel_id in catalog:
                sel_name = f" ({catalog[sel_id]['name']})"
            
            output_item = {
                "case_id": case.get("case_id"),
                "query": query,
                "retrieved_ids": retrieved_display,
                "selected_id": f"{sel_id}{sel_name}" if sel_id else None,
                "reason": rerank_result.get("reason"),
                "latency_ms": rerank_result.get("latency", 0) * 1000
            }
            results.append(output_item)
            
            print(f"  -> Selected: {output_item['selected_id']}")

    # Save Results
    base_dir = os.path.dirname(output_file)
    if base_dir and not os.path.exists(base_dir):
        os.makedirs(base_dir)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"\nReranking Complete. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # Optional logic: If no args, run quick test. If args, run pipeline mode.
    # But since user specifically wants to use this file in pipeline, we prioritize that.
    
    parser.add_argument("--run-dir", help="Directory containing benchmark detail.jsonl")
    parser.add_argument("--catalog", help="Path to catalog TSV")
    parser.add_argument("--out", help="Output JSON file path")
    
    args = parser.parse_args()
    
    if args.run_dir and args.catalog and args.out:
        process_benchmark_output(args.run_dir, args.catalog, args.out)
    else:
        # Fallback to quick test
        test_query = "싱크대 거름망"
        test_candidates = [
            {"id": "100", "name": "싱크대 거름망 (스텐)", "desc": "배수구 찌꺼기 거름"},
            {"id": "101", "name": "거름망 트랩", "desc": "냄새 차단"},
            {"id": "102", "name": "수세미", "desc": "설거지용"}
        ]
        print(advanced_rerank(test_query, test_candidates))
