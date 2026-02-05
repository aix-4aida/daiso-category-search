from sentence_transformers import SentenceTransformer, util
import numpy as np
import inventory
import re

# Load model (can be swapped for a lighter one if needed)
# 'all-MiniLM-L6-v2' is fast and good for this.
model = SentenceTransformer('all-MiniLM-L6-v2')

# Prepare inventory embeddings
items = inventory.get_all_items()
# We construct a "searchable text" for each item: Name + Keywords + Category
item_texts = [f"{item['name']} {', '.join(item['keywords'])} {item['category']}" for item in items]
item_embeddings = model.encode(item_texts, convert_to_tensor=True)

def analyze_intent_dummy(query: str):
    """
    Mock LLM Intent Analysis.
    In a real scenario, this would call Gemini API.
    For now, we heuristically extract key terms.
    """
    # Simple rule-based extraction for prototype
    # Detect context
    context = []
    if "travel" in query.lower() or "trip" in query.lower():
        context.append("Travel")
    if "bathroom" in query.lower() or "shower" in query.lower():
        context.append("Bathroom")
    
    # Just return query as is for semantic search, heavily relying on embeddings
    return {
        "refined_query": query,
        "detected_context": context
    }

def search(query: str):
    """
    1. Analyze Intent
    2. Semantic Search
    """
    analysis = analyze_intent_dummy(query)
    refined_q = analysis["refined_query"]
    
    # Encode query
    query_embedding = model.encode(refined_q, convert_to_tensor=True)
    
    # Compute cosine similarity
    hits = util.semantic_search(query_embedding, item_embeddings, top_k=3)
    
    # hits is a list of lists (one for each query)
    top_hits = hits[0] 
    
    results = []
    for hit in top_hits:
        item = items[hit['corpus_id']]
        results.append({
            "item": item,
            "score": float(hit['score'])
        })
        
    return {
        "analysis": analysis,
        "results": results
    }

if __name__ == "__main__":
    # Test
    print(search("I need a hard mat to dry my feet in the bathroom"))
