"""
CLIP Embedding Generator for Search-Roca
Creates text and image embeddings for multimodal search
"""
import os
import pickle
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

from database import get_connection, get_all_products

# Model configuration
MODEL_NAME = "openai/clip-vit-base-patch32"
IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')

# Global model cache
_model = None
_processor = None

def load_model():
    """Load CLIP model (cached)"""
    global _model, _processor
    if _model is None:
        print("🔄 Loading CLIP model...")
        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        print("✅ CLIP model loaded")
    return _model, _processor

def get_text_embedding(text: str) -> bytes:
    """Get text embedding as bytes"""
    model, processor = load_model()
    
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    
    # Normalize
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    
    # Convert to bytes for storage
    return pickle.dumps(text_features.numpy())

def get_image_embedding(image_path: str) -> bytes:
    """Get image embedding as bytes"""
    model, processor = load_model()
    
    if not os.path.exists(image_path):
        return None
    
    try:
        image = Image.open(image_path).convert('RGB')
        inputs = processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
        
        # Normalize
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return pickle.dumps(image_features.numpy())
    except Exception as e:
        print(f"⚠️ Image embedding failed for {image_path}: {e}")
        return None

def generate_all_embeddings():
    """Generate embeddings for all products"""
    print("=" * 50)
    print("🚀 Generating CLIP Embeddings")
    print("=" * 50)
    
    products = get_all_products()
    if not products:
        print("❌ No products found. Run crawler first.")
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for i, product in enumerate(products):
        product_id = product['id']
        name = product['name']
        image_path = product['image_path']
        
        # Check if already embedded
        cursor.execute('SELECT 1 FROM product_embeddings WHERE product_id = ?', (product_id,))
        if cursor.fetchone():
            continue
        
        print(f"[{i+1}/{len(products)}] {name[:40]}...")
        
        # Generate embeddings
        text_emb = get_text_embedding(name)
        image_emb = get_image_embedding(image_path) if image_path else None
        
        # Insert
        cursor.execute('''
            INSERT OR REPLACE INTO product_embeddings (product_id, text_embedding, image_embedding)
            VALUES (?, ?, ?)
        ''', (product_id, text_emb, image_emb))
        
        if (i + 1) % 10 == 0:
            conn.commit()
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("✅ Embeddings generated!")
    print("=" * 50)

def search_by_text(query: str, top_k: int = 5):
    """Search products by text query using CLIP"""
    model, processor = load_model()
    
    # Get query embedding
    inputs = processor(text=[query], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        query_features = model.get_text_features(**inputs)
    query_features = query_features / query_features.norm(dim=-1, keepdim=True)
    
    # Load all embeddings and compare
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.price, pe.text_embedding
        FROM products p
        JOIN product_embeddings pe ON p.id = pe.product_id
        WHERE pe.text_embedding IS NOT NULL
    ''')
    
    results = []
    for row in cursor.fetchall():
        text_emb = pickle.loads(row['text_embedding'])
        text_tensor = torch.from_numpy(text_emb)
        
        # Cosine similarity
        similarity = (query_features @ text_tensor.T).item()
        results.append({
            'id': row['id'],
            'name': row['name'],
            'price': row['price'],
            'score': similarity
        })
    
    conn.close()
    
    # Sort by similarity
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

if __name__ == "__main__":
    generate_all_embeddings()
    
    # Test search
    print("\n🔍 Test search: '물티슈'")
    results = search_by_text("물티슈")
    for r in results:
        print(f"  - {r['name']} (score: {r['score']:.3f})")
