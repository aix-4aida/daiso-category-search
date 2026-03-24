
import os
import json
import time
import google.generativeai as genai
from backend.core.config import config

# Initialize Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️ GOOGLE_API_KEY not found. Reranking might fail.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={"response_mime_type": "application/json"}
)

def rerank_products(user_query: str, candidates: list) -> dict:
    """
    Reranks candidates using Gemini 2.0 Flash.
    Returns the TOP 3 best matching product IDs.
    """
    if not candidates:
        return {"top_ids": [], "reason": "No candidates provided."}

    # Prepare Candidate Text
    candidate_text = ""
    for c in candidates:
        name = c.get('name', 'Unknown')
        # Use existing meta or desc
        desc = c.get('desc', '') or c.get('meta', {}).get('major', '') or "No description"
        desc = str(desc)[:100] 
        candidate_text += f"- ID {c['id']}: {name} (Info: {desc})\n"

    # Construct Prompt
    prompt = f"""
You are an expert AI Search Agent for Daiso (a variety store).
Your goal is to rank the TOP 3 best matching products from a list of candidates based on a user's query.
You MUST always return exactly 3 product IDs in order of relevance.

[Ranking Rules]
1.  **Direct Match First**: The product whose name IS the queried item must ALWAYS rank #1, above accessories, parts, or novelty items.
    - Example: "키보드" → "USB 유선 키보드" MUST rank #1 above "키보드 초콜릿 만들기 세트".
    - Example: "커튼" → "암막 커튼 140X240cm" MUST rank #1 above "커튼 타이" or "커튼 집게".
2.  **Accessory Demotion**: Items that are accessories, parts (타이, 집게, 핀, 봉, 레일, 링), or novelty/DIY versions of the product should be ranked AFTER the actual product.
3.  **Intent First**: Understand the user's core need (e.g., "frying net" -> Kitchen, not Laundry).
4.  **2-3 Results**: Return 2 or 3 IDs. If only 2 candidates genuinely match the query, return just 2. Do NOT pad with completely unrelated items just to reach 3.

[Task]
User Query: "{user_query}"

Candidates:
{candidate_text}

Output JSON:
{{
    "top_ids": ["best_id", "second_id", "third_id"],
    "reason": "Brief Korean explanation of why these were chosen and in this order."
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
        return {"top_ids": [], "reason": f"Error: {str(e)}"}
