import os
import json
import numpy as np
import os
import json
import numpy as np
# import google.generativeai as genai  <-- [Mod] Lazy import로 변경
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# 로컬 환경 변수 로드 (.env 파일이 있다면)
# 1. 현재 폴더(poc) 확인
# 2. 형제 폴더(backend) 확인
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_env_path = os.path.join(current_dir, "..", "backend", ".env")

if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)
    # print(f"✅ Loaded .env from: {os.path.abspath(backend_env_path)}")
else:
    load_dotenv() # 기본값: 현재 폴더

# ==========================================
# ⚙️ 설정 (Configuration)
# ==========================================
# Test 1 사용 (Gemini) -> get_gemini_embedding 함수 내부에서 설정함

# Test 2 사용 (Local)
# 다국어(한국어 포함) 성능이 우수한 경량화 모델
LOCAL_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_local_model_instance = None # Lazy Loading

# 데이터 경로
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "products.json")


# ==========================================
# 🛠️ 유틸리티 함수 (Utilities)
# ==========================================
def load_data():
    """Dummy JSON 데이터를 로드합니다."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_gemini_embedding(text, task_type="retrieval_document"):
    """[Test 1] Gemini API를 사용 (수정전)"""
    # Lazy Import: 함수가 호출될 때만 라이브러리 로드
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY가 없습니다.")
    
    genai.configure(api_key=api_key)

    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type=task_type
    )
    return result['embedding']

def get_local_embedding(text):
    """[Test 2] Local Sentence-BERT 사용 (수정후)"""
    global _local_model_instance
    if _local_model_instance is None:
        print(f"📥 로컬 모델({LOCAL_MODEL_NAME}) 로딩 중... (최초 1회만 느림)")
        _local_model_instance = SentenceTransformer(LOCAL_MODEL_NAME)
    
    # SentenceTransformer는 바로 embedding 리스트 반환
    return _local_model_instance.encode(text).tolist()

def cosine_similarity(v1, v2):
    """두 벡터 간의 코사인 유사도를 계산합니다."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

def vector_search(query, all_products, top_k=10, threshold=0.0, use_local_model=True):
    """
    기본적인 벡터 검색 로직.
    use_local_model=True이면 로컬 모델(Test 2) 사용.
    """
    # 1. 쿼리 임베딩
    if use_local_model:
        query_vec = get_local_embedding(query)
    else:
        query_vec = get_gemini_embedding(query, task_type="retrieval_query")
    
    scored_products = []
    
    for product in all_products:
        # 캐싱 처리 (키를 분리해서 저장)
        emb_key = "embedding_local" if use_local_model else "embedding_gemini"
        
        if emb_key not in product:
            # "이름 + 설명 + 카테고리"를 합쳐서 임베딩
            text_to_embed = f"{product['name']} {product['desc']} {product['category']}"
            if use_local_model:
                product[emb_key] = get_local_embedding(text_to_embed)
            else:
                product[emb_key] = get_gemini_embedding(text_to_embed)
            
        params_vec = product[emb_key]
        score = cosine_similarity(query_vec, params_vec)
        
        if score >= threshold:
            product_with_score = product.copy()
            product_with_score["score"] = score
            # 결과 출력 시 긴 벡터 정보는 삭제
            if "embedding_local" in product_with_score: del product_with_score["embedding_local"]
            if "embedding_gemini" in product_with_score: del product_with_score["embedding_gemini"]
            
            scored_products.append(product_with_score)
    
    scored_products.sort(key=lambda x: x["score"], reverse=True)
    return scored_products[:top_k]


# ==========================================
# 🧪 실험 Run Functions
# ==========================================

def run_grid_search(products, mode="local"):
    """
    mode='gemini' -> Test 1 (수정전)
    mode='local'  -> Test 2 (수정후)
    """
    is_local = (mode == "local")
    title = "[Test 2] 수정후: Local Model" if is_local else "[Test 1] 수정전: Gemini API"
    
    print("\n" + "="*60)
    print(f"🧪 {title} - Grid Search")
    print("="*60)
    
    query = "욕실매트"
    
    # ✅ Ground Truth (정답지) - 엄격 기준
    ground_truth_ids = {1, 5, 9}
    
    print(f"🔎 검색어: '{query}'")
    print(f"🎯 정답셋(Ground Truth): ID {list(ground_truth_ids)}")
    
    k_candidates = [3, 5, 7, 10]
    thr_candidates = [0.40, 0.50, 0.60, 0.70] if is_local else [0.60, 0.70, 0.80] 
    # 로컬 모델은 점수 분포가 다를 수 있어 범위를 조금 낮춤
    
    best_score = 0
    best_params = {}
    
    print(f"\n{'K':<4} | {'Thr':<6} | {'Found':<5} | {'Prec(정확)':<10} | {'Rec(재현)':<10} | {'F1-Score':<10} | {'판정'}")
    print("-" * 80)
    
    for k in k_candidates:
        for thr in thr_candidates:
            # 검색 수행
            results = vector_search(query, products, top_k=k, threshold=thr, use_local_model=is_local)
            
            retrieved_ids = set([item['id'] for item in results])
            
            # Metric 계산
            if len(retrieved_ids) == 0:
                precision = 0.0
            else:
                precision = len(retrieved_ids.intersection(ground_truth_ids)) / len(retrieved_ids)
                
            if len(ground_truth_ids) == 0:
                recall = 0.0
            else:
                recall = len(retrieved_ids.intersection(ground_truth_ids)) / len(ground_truth_ids)
            
            if (precision + recall) == 0:
                f1_score = 0.0
            else:
                f1_score = 2 * (precision * recall) / (precision + recall)
            
            verdict = ""
            if f1_score >= 0.8: verdict = "🏆 Excellent"
            elif f1_score >= 0.6: verdict = "✅ Good"
            else: verdict = "❌ Fail"
            
            if f1_score > best_score:
                best_score = f1_score
                best_params = {"k": k, "thr": thr}
            
            print(f"{k:<4} | {thr:<6} | {len(results):<5} | {precision:.3f}      | {recall:.3f}      | {f1_score:.3f}      | {verdict}")

    print("-" * 80)
    print(f"\n🎉 [{mode} 모드 결과] Best F1: {best_score:.3f}")
    if best_params:
        print(f"👉 Recommended: Top-K={best_params['k']}, Threshold={best_params['thr']}")
    
    # [DEBUG] 상세 랭킹 확인 (Why?)
    print("\n🕵️ [DEBUG] Ranking Check")
    full_results = vector_search(query, products, top_k=len(products), threshold=0.0, use_local_model=is_local)
    
    print(f"🔎 정답 상품 순위:")
    for rank, item in enumerate(full_results):
        if item['id'] in ground_truth_ids:
            print(f" - #{rank+1}위: [{item['score']:.4f}] {item['name']}")
            
    print(f"\n🔎 Top 5 오답(Noise) 확인:")
    count = 0
    for rank, item in enumerate(full_results):
        if item['id'] not in ground_truth_ids:
            print(f" - #{rank+1}위: [{item['score']:.4f}] {item['name']} ({item['category']})")
            count += 1
            if count >= 5: break


# ==========================================
# 🔮 Future Steps (Issue 2, 3)
# 현재 Sprint 1에서는 Issue 1(Retrieval)에 집중하고 있습니다.
# 아래 함수들은 Issue 1이 해결된 후(Next Sprint), 순차적으로 활성화하여 실험할 예정입니다.
# ==========================================

def experiment_llm_reranking(products):
    """
    [Issue 2] LLM Re-ranking
    1차 검색(Retrieval) 결과에서 문맥적으로 맞지 않는 상품을 LLM이 2차 검수하는 로직.
    """
    print("\n" + "="*80)
    print("🧪 [Test 3] LLM Re-ranking (Issue 2)")
    print("목표: Top-7 안에 들어온 정답(#4, #5, #7)을 #1, #2, #3으로 끌어올리기")
    print("="*80)

    # 1. 1차 검색 (Retrieval) - Local Model, K=7
    query = "욕실매트"
    print(f"1️⃣ 1차 검색 수행 (Query: '{query}', Model: Local, K=7)...")
    candidates = vector_search(query, products, top_k=7, threshold=0.0, use_local_model=True)
    
    print("\n[Before Re-ranking] 1차 검색 결과:")
    for i, item in enumerate(candidates):
        print(f" - Rank {i+1}: {item['name']} (Score: {item['score']:.4f})")

    # 2. LLM에게 Re-ranking 요청
    print("\n2️⃣ Gemini에게 Re-ranking 요청 중...")
    
    # Lazy Import & Config
    import google.generativeai as genai
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY가 없어서 Skip합니다.")
        return
    genai.configure(api_key=api_key)
    
    # Prompt 구성
    candidate_text = ""
    for i, item in enumerate(candidates):
        candidate_text += f"ID {item['id']}: {item['name']} (설명: {item['desc']})\n"
        
    prompt = f"""
    당신은 쇼핑몰 검색 품질 관리자입니다.
    사용자가 "{query}"라고 검색했습니다.
    다음은 1차 검색 결과 후보들입니다.
    
    [후보 목록]
    {candidate_text}
    
    [지시사항]
    1. 사용자의 검색 의도("{query}")에 가장 적합한 순서대로 상품을 재정렬하세요.
    2. "욕실에 바닥에 깔아 사용하는 매트"가 가장 높은 점수를 받아야 합니다.
    3. 이름에 '매트'가 없거나 용도가 다른 경우(선반, 칫솔꽂이 등)는 하위권으로 내리십시오.
    4. 결과는 JSON 형식으로 다음 포맷에 맞춰 출력하세요. 설명은 필요 없습니다.
    [
        {{"id": 상품ID, "rank": 1, "reason": "선정이유"}},
        ...
    ]
    """
    
    try:
        # gemini-2.0-flash (Verified Available)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        # JSON 파싱 (간단한 처리)
        import re
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            rerank_results = json.loads(json_match.group(0))
            
            print("\n🎉 [After Re-ranking] 최종 결과:")
            for item in rerank_results:
                # 원래 상품 정보 매핑
                original_prod = next((p for p in candidates if p['id'] == item['id']), None)
                if original_prod:
                    mark = "✅" if item['id'] in {1, 5, 9} else "  "
                    print(f" - {mark} Rank {item['rank']}: {original_prod['name']} (Reason: {item.get('reason', '')})")
                    
        else:
            print(f"❌ JSON 파싱 실패. 응답 원본:\n{response.text}")
            
    except Exception as e:
        print(f"❌ Re-ranking 중 에러 발생: {e}")

def classify_intent(query, categories):
    """
    [Intent Classifier]
    사용자의 검색어(Query)를 보고 가장 적절한 카테고리를 예측합니다.
    """
    # Lazy Import & Config
    import google.generativeai as genai
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    
    cat_list_str = ", ".join(categories)
    
    prompt = f"""
    당신은 쇼핑몰 검색 시스템의 의도 분류기(Intent Classifier)입니다.
    사용자의 검색어: "{query}"
    
    [가능한 카테고리 목록]
    {cat_list_str}
    
    [지시사항]
    1. 검색어와 가장 관련성 높은 카테고리를 하나만 선택하세요.
    2. 답변은 카테고리 명칭만 정확히 출력하세요. (설명 금지)
    3. 목록에 없는 경우 가장 가까운 것을 선택하거나, 모르면 '기타'라고 하세요.
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        predicted_category = response.text.strip()
        
        # 후처리: 이상한 문장 부호 제거나 매칭 확인
        for cat in categories:
            if cat in predicted_category:
                return cat
        return predicted_category
        
    except Exception as e:
        print(f"❌ Intent Classification Error: {e}")
        return None

def experiment_category_filter(products):
    """
    [Issue 3] Dynamic Category Filter
    Static한 "욕실" 필터가 아닌, 검색어에 따라 동적으로 카테고리를 판단하고 필터링합니다.
    """
    print("\n" + "="*80)
    print("🧪 [Test 4] Dynamic Category Filtering (Issue 3)")
    print("목표: 어떤 검색어(욕실/운동/캠핑)가 들어와도, 그에 맞는 카테고리만 필터링하는가?")
    print("="*80)
    
    # 1. 전체 카테고리 스키마 추출
    all_categories = set(p['category'] for p in products)
    print(f"📋 감지된 카테고리 목록: {all_categories}")
    
    # 2. 다중 테스트 케이스
    test_queries = [
        "욕실매트",         # Exp: 욕실
        "홈트레이닝 매트",    # Exp: 운동
        "야외 돗자리"        # Exp: 캠핑 or 자동차
    ]
    
    for query in test_queries:
        print(f"\n🔍 [Query]: '{query}'")
        
        # (1) 의도 분류
        predicted = classify_intent(query, all_categories)
        if not predicted:
            print("⚠️ 분류 실패 (API Error)")
            continue
            
        print(f"👉 AI 판단 카테고리: '{predicted}'")
        
        # (2) 필터링
        filtered_products = [p for p in products if p['category'] == predicted]
        print(f"👉 필터링 결과: {len(products)}개 -> {len(filtered_products)}개")
        
        if not filtered_products:
            print("❌ 해당 카테고리 상품 없음.")
            continue

        # (3) 검색 수행 (Local Model)
        results = vector_search(query, filtered_products, top_k=3, threshold=0.0, use_local_model=True)
        
        print("🔎 Top-3 검색 결과:")
        for i, item in enumerate(results):
            print(f" - #{i+1}: {item['name']} (Category: {item['category']}, Score: {item['score']:.4f})")


# ==========================================
# 🚀 메인 실행부
# ==========================================
if __name__ == "__main__":
    print("📦 데이터 로딩 중...")
    products = load_data()
    print(f"✅ {len(products)}개 상품 로드 완료.")
    
    """
    Test1: 수정전, Gemini API(text-embedding-004) 사용하여 임베딩.
    Test2: 수정후, Local Model(MiniLM) 사용하여 임베딩.
    """
    # run_grid_search(products, mode="gemini")
    
    print("\n" + "="*80)
    print("Test2:")
    print("수정후 (Local Model 사용)")
    print("="*80)
    
    run_grid_search(products, mode="local")
    
    # Issue 2 Active
    experiment_llm_reranking(products)
    
    # Issue 3 Active
    experiment_category_filter(products)
