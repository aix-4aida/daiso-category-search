
import json
import os
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

MOCK_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_mock_product_db.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_golden_test_cases.json")

CONFUSION_SCENARIOS = [
    "Composition Ambiguity (Product vs Part)",
    "Negative Constraints (NOT logic)",
    "Implicit Needs (Problem solving)",
    "Category Overlap (Context ambiguity)",
    "Subjective Adjectives (Quality/Price)"
]

def load_products():
    if not os.path.exists(MOCK_DB_PATH):
        print("MOCK DB not ready yet.")
        return []
    with open(MOCK_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_golden_cases(products):
    # Sample products to give context to LLM
    product_summary = "\n".join([f"ID {p['id']}: {p['name']} ({p.get('category_middle','')})" for p in random.sample(products, min(len(products), 100))])
    
    prompt = f"""
    You are a QA Engineer for a Search Engine.
    I have a product database (sampled below):
    {product_summary}
    ... (total {len(products)} products)

    Your task is to generate exactly 30 'Golden Test Cases' to evaluate the search engine.
    
    CRITICAL REQUIREMENTS:
    1. Include queries for ALL "Confusion Scenarios":
       - Composition Ambiguity (e.g., searching for a mat, but deciding if a set containing a mat is relevant)
       - Negative Constraints (e.g., "no plastic")
       - Implicit Needs (e.g., "mold issues")
       - Category Overlap
       - Subjective Adjectives "cheap", "popular"
    2. Also include standard simple queries.
    3. For each query, identify the 'ground_truth_ids' (Top-K) from the provided list (or best guess if not all visible, but try to be accurate based on names).
    4. Define 'expected_intent' (category filters, price filters etc).

    Output JSON Format:
    [
        {{
            "query": "QUERY_STRING",
            "scenario_type": "Negative Constraints",
            "difficulty": "Hard",
            "expected_intent": {{ "keywords": ["..."], "category": "...", "filters": [...] }},
            "ground_truth_ids_hint": [10, 24, ...] (IDs that SHOULD be found)
        }},
        ...
    ]
    """
    
    print("🧠 Generating Golden Test Cases with Gemini...")
    response = model.generate_content(prompt)
    try:
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing: {e}")
        return []

def main():
    products = load_products()
    if not products:
        print("❌ Products not found. Run mock data generation first.")
        return

    cases = generate_golden_cases(products)
    
    print(f"💾 Saving {len(cases)} test cases to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
    print("✅ Done!")

if __name__ == "__main__":
    main()
