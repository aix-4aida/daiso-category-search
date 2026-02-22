
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

[Principles]
1.  **Intent First**: Understand the user's core need (e.g., "frying net" -> Kitchen, not Laundry).
2.  **Context Aware**: Prefer standard/popular items for broad queries.
3.  **Strict Filtering**: Only include items that reasonably match the intent.
4.  **Null Safety**: If a candidate is irrelevant, omit it from the top list.

[Task]
User Query: "{user_query}"

Candidates:
{candidate_text}

Output JSON:
{{
    "top_ids": ["1", "2", "3"],
    "reason": "Brief Korean explanation of why these were chosen."
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
