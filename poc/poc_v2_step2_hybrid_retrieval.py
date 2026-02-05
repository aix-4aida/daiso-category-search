
import os
import json
import time
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import warnings
from tqdm import tqdm

warnings.filterwarnings("ignore")

# ===========================
# Configuration
# ===========================
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_mock_product_db.json")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_golden_test_cases.json")
LOCAL_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

class SearchEngine:
    def __init__(self):
        print("🔧 Initializing Search Engine...")
        self.products = []
        self.bm25 = None
        self.vector_model = None
        self.product_embeddings = None
        self.corpus_tokenized = []
        
        self._load_data()
        self._build_indices()
        
    def _load_data(self):
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Mock DB not found at {DATA_PATH}")
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            self.products = json.load(f)
        print(f"📦 Loaded {len(self.products)} products.")

    def _build_indices(self):
        # 1. BM25 Index
        print("📝 Building BM25 Index...")
        # Tokenize simply by whitespace for this PoC (Korean specific tokenization would be better but keeping simple)
        self.corpus_tokenized = [self.tokenize(f"{p['name']} {p.get('searchable_desc','')} {p['category_middle']}") for p in self.products]
        self.bm25 = BM25Okapi(self.corpus_tokenized)
        
        # 2. Vector Index
        print(f"🧠 Loading Vector Model ({LOCAL_MODEL_NAME})...")
        self.vector_model = SentenceTransformer(LOCAL_MODEL_NAME)
        print("🧮 Encoding Product Vectors...")
        texts = [f"{p['name']} {p['category_middle']} {p.get('desc','')} {p.get('searchable_desc','')}" for p in self.products]
        self.product_embeddings = self.vector_model.encode(texts, show_progress_bar=True)
        
    def tokenize(self, text):
        return text.lower().split()

    # ===========================
    # Search Methods
    # ===========================
    
    def search_term_match(self, query, top_k=20):
        # Simple scorer: count overlapping tokens
        q_tokens = set(self.tokenize(query))
        scores = []
        for p in self.products:
            p_text = (p['name'] + " " + p.get('searchable_desc', '')).lower()
            score = sum(1 for t in q_tokens if t in p_text)
            scores.append(score)
        
        # Sort
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.products[i] for i in top_indices if scores[i] > 0]

    def search_bm25(self, query, top_k=20):
        tokenized_query = self.tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.products[i] for i in top_indices]

    def search_vector(self, query, top_k=20):
        q_vec = self.vector_model.encode([query])[0]
        scores = np.dot(self.product_embeddings, q_vec) # Assuming normalized if cosine, but Dot is fine for ranking
        # Normalization check
        # norm_doc = np.linalg.norm(self.product_embeddings, axis=1)
        # norm_query = np.linalg.norm(q_vec)
        # scores = scores / (norm_doc * norm_query)
        
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.products[i] for i in top_indices]
    
    def search_hybrid(self, query, top_k=20, alpha=0.5):
        # RRF or Weighted Sum? Let's use Weighted Sum of normalized scores for simplicity
        
        # BM25 Scores
        tokenized_query = self.tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max() # Normalize 0-1
            
        # Vector Scores
        q_vec = self.vector_model.encode([query])[0]
        vec_scores = np.dot(self.product_embeddings, q_vec)
        if vec_scores.max() > 0:
            vec_scores = vec_scores / vec_scores.max() # Normalize 0-1
        
        final_scores = (xml_score := alpha * vec_scores + (1-alpha) * bm25_scores)
        
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        return [self.products[i] for i in top_indices]

# ===========================
# Experiment Runner
# ===========================
def run_experiment():
    if not os.path.exists(TEST_CASES_PATH):
        print("❌ Test cases not found.")
        return
        
    engine = SearchEngine()
    
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    print("\n🧪 Starting Top-K Sensitivity Test (K=[5, 10, 20])...")
    
    k_list = [5, 10, 20]
    methods = ["BM25", "Vector", "Hybrid"]
    
    results = {m: {k: {"recall": 0} for k in k_list} for m in methods}
    total_cases = len(cases)
    
    for case in tqdm(cases):
        query = case['query']
        ground_truth = set(case.get('ground_truth_ids_hint', []))
        if not ground_truth: continue # Skip if no truth defined
        
        # Run Searches
        res_bm25 = engine.search_bm25(query, top_k=20)
        res_vec = engine.search_vector(query, top_k=20)
        res_hybrid = engine.search_hybrid(query, top_k=20)
        
        res_dict = {"BM25": res_bm25, "Vector": res_vec, "Hybrid": res_hybrid}
        
        for method, items in res_dict.items():
            retrieved_ids = [p['id'] for p in items]
            
            for k in k_list:
                # Check if ANY ground truth is in Top-K (Hit Rate / Recall@K logic)
                # Actually, strictly Recall is (Relevant Items Retrieved / Total Relevant).
                # Here we check "Intersection Count"
                top_k_ids = set(retrieved_ids[:k])
                intersection = top_k_ids.intersection(ground_truth)
                if intersection:
                    results[method][k]["recall"] += 1 # Increment "Hit" count for now
    
    print("\n📊 Results (Hit Rate @ K)")
    print(f"{'Method':<10} | {'@5':<10} | {'@10':<10} | {'@20':<10}")
    print("-" * 50)
    for m in methods:
        row = f"{m:<10}"
        for k in k_list:
            hit_count = results[m][k]["recall"]
            rate = (hit_count / total_cases) * 100
            row += f" | {rate:.1f}% ({hit_count})"
        print(row)

if __name__ == "__main__":
    run_experiment()



"""
검색 엔진의 핵심(Retrieval) 성능을 검증하는 실험실입니다.

Step 1에서 의도를 파악하고 나면, 실제로 수많은 상품 중에서 **"어떤 알고리즘으로 찾아야 정답이 나올까?"**를 경쟁시키는 코드입니다.

핵심 기능 설명
SearchEngine
 클래스 (검색 엔진 본체):
인덱싱 (준비 단계):
BM25: 상품명과 설명을 단어 단위로 쪼개서 통계적 점수(희소성)를 미리 계산해둡니다.
Vector: SentenceTransformer 모델을 써서 모든 상품을 384차원의 숫자(벡터)로 변환해둡니다.
검색 메서드 3종 세트:
search_term_match
: 단순히 단어가 포함됐는지 개수를 셉니다. (가장 기초적)
search_bm25
: 키워드의 중요도(빈도)를 따져서 찾습니다. (단어 매칭의 진화형)
search_vector
: 단어가 달라도 의미가 비슷하면 찾습니다. (예: "물기 제거" <-> "건조")
search_hybrid
 (하이브리드 검색):
BM25 점수 + 벡터 점수를 반반(0.5:0.5 또는 조절 가능) 섞어서 최종 순위를 매깁니다.
단어가 정확히 일치하는 것도 찾고, 의미가 통하는 것도 찾기 위한 **"필승 전략"**입니다.
run_experiment
 (Top-K 실험기):
목적: "몇 개를 가져와야 안전할까?"를 테스트합니다.
Step 0에서 만든 정답지(golden_test_cases)를 사용하여, BM25, Vector, Hybrid 방식 각각에 대해 질문을 던집니다.
Top-5, 10, 20개씩 끊어서 가져왔을 때, 그 안에 진짜 정답이 들어있는지(Hit Rate/Recall)를 표로 출력합니다.
이 코드가 중요한 이유
**"왜 Hybrid를 써야 하나요?"**라는 질문에 데이터로 답할 수 있게 해줍니다.
"Reranking 모델한테 몇 개를 넘겨줘야 하죠?" (5개? 20개?)라는 질문에 대해, "20개를 넘겨주면 정답 포함률이 95%지만 속도가 느리고, 10개면 90%입니다"라고 트레이드오프를 결정할 수 있는 근거를 줍니다.
결국, 돈(LLM 비용/시간)을 쓰기 전에 가장 효율적으로 후보를 추려내는 최적의 설정을 찾는 코드입니다.
"""