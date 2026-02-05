
import sqlite3
import json
import os
import random
import time
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

# Setup
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

DB_PATH = r"c:\Users\301\pjt\Final\search\daiso-category-search\backend\database\products.db"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "poc_v2_mock_product_db.json")

# Locations simulation
LOCATIONS_POOL = [
    "1층 미용코너", "1층 악세서리 매대", "1층 계산대 앞", 
    "2층 욕실용품 A열", "2층 욕실용품 B열", "2층 청소용품 코너", "2층 세탁용품 진열대",
    "3층 주방용품 A-1", "3층 주방용품 C-2", "3층 식기 코너", "3층 밀폐용기 매대",
    "4층 취미/공구 A열", "4층 캠핑용품 존", "4층 차량용품 코너", "4층 원예용품 매대"
]

def get_location(category):
    # Simple logic to make location somewhat plausible based on category
    if "욕실" in category or "청소" in category:
        return random.choice([l for l in LOCATIONS_POOL if "2층" in l])
    elif "주방" in category:
        return random.choice([l for l in LOCATIONS_POOL if "3층" in l])
    elif "캠핑" in category or "공구" in category:
        return random.choice([l for l in LOCATIONS_POOL if "4층" in l])
    else:
        return random.choice(LOCATIONS_POOL)

def generate_description_and_keywords(name, category):
    prompt = f"""
    You are a data generator for a search engine PoC.
    Product Name: {name}
    Category: {category}

    Task 1: Generate a 'Raw Detail Page Text' (simulated HTML body text) for this product. Include 'Components', 'Material', 'Usage', and 'Target Audience'. Be creative but realistic for a Daiso product.
    Task 2: From the generated raw text, extract 'Searchable Keywords' and a 'Search Description' that would be indexed for search.

    Output Format (JSON only):
    {{
        "raw_detail_text": "...",
        "searchable_desc": "...",
        "keywords": ["tag1", "tag2", ...]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Error generating for {name}: {e}")
        return {
            "raw_detail_text": f"Error generating details for {name}",
            "searchable_desc": f"{name} - {category}",
            "keywords": []
        }

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    print("🔌 Connecting to Database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    products = cursor.execute("SELECT id, name, category_major, category_middle, price FROM products").fetchall()
    conn.close()
    
    print(f"📦 Loaded {len(products)} products.")
    
    enriched_data = []
    
    # Process batch (Let's do all of them, but with a progress bar)
    # If script fails, we can implement resume logic later, but for 600 items Flash should handle it in ~2-3 mins.
    
    print("🚀 Starting LLM Enrichment...")
    for p in tqdm(products):
        p_dict = dict(p)
        
        # 1. Location
        cat_str = f"{p_dict.get('category_major', '')} {p_dict.get('category_middle', '')}"
        p_dict['location'] = get_location(cat_str)
        
        # 2. LLM Generation
        # Cost optimization: Check if name is empty
        if not p_dict['name']: continue
        
        gen_data = generate_description_and_keywords(p_dict['name'], cat_str)
        
        p_dict.update(gen_data)
        enriched_data.append(p_dict)
        
        # Rate limit handling (simple sleep)
        time.sleep(0.1) 
        
    print(f"💾 Saving to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
    print("✅ Done!")

if __name__ == "__main__":
    main()





"""
단순히 상품명만 있는 데이터로는 "고급 검색"이나 "의도 파악"을 테스트할 수 없기 때문에, LLM을 시켜서 가상의 상세 페이지를 창조해내는 과정입니다.

1. 위치 정보 시뮬레이션 (
get_location
)
실제 매장처럼 상품 위치를 안내하기 위해 가상의 위치를 배정합니다.

python
def get_location(category):
    # 욕실용품이면 -> "2층"을 우선 배정
    if "욕실" in category:
        return random.choice([... "2층 욕실용품 A열", ...])
    # 주방용품이면 -> "3층" 배정
    elif "주방" in category:
        return random.choice([... "3층 주방용품 C-2", ...])
    # ...
원리: 카테고리 텍스트를 검사해서, 그럴듯한 층수와 매대를 랜덤하게 골라줍니다. AG(에이전트)가 나중에 이 정보를 읽고 안내하게 됩니다.
2. LLM에게 '글짓기' 시키기 (
generate_description_and_keywords
)
이 코드의 가장 중요한 부분입니다. LLM에게 두 가지 일을 동시에 시킵니다.

python
prompt = f"""
상품명: {name} (예: 변기 커버 세트)
Task 1: 'Raw 상세 페이지'를 상상해서 써줘.
(구성품, 재질, 사용법, 타겟 고객 등을 포함해서 그럴듯하게)
-> 예: "구성품에는 미끄럼 방지 매트가 포함되어 있어 안전합니다..."
Task 2: 위 텍스트를 바탕으로 '검색용 요약'과 '태그'를 추출해줘.
-> 예: 검색용 설명="변기 커버, 미끄럼 방지 매트 포함", 태그=["욕실", "안전", "세트"]
"""
핵심: 그냥 "검색 키워드 뽑아줘"라고 하면 LLM이 단어만 나열합니다. 하지만 **"상세 페이지를 먼저 써봐"**라고 하면, 그 안에 **숨겨진 니즈(안전, 미끄럼 방지)**나 구성품(매트) 같은 디테일이 자연스럽게 튀어나옵니다. 이게 바로 **"단단한 데이터"**를 만드는 비결입니다.
3. 메인 루프 (
main
)
공장을 돌리는 과정입니다.

DB 연결: products.db에서 600개 상품을 꺼내옵니다.
반복 작업 (for p in tqdm(products)):
하나씩 꺼내서 위치를 붙이고(
get_location
),
LLM에게 글짓기를 시킵니다(generate...).
저장: 모든 작업이 끝나면 poc_v2_mock_product_db.json 파일 하나로 예쁘게 저장합니다.
4. 왜 이렇게 짰나요?
현실성: 실제 커머스 검색엔진도 "상품 상세 설명(HTML)"에서 키워드를 추출해서 인덱싱합니다. 이 과정을 그대로 흉내 낸 것입니다.
검증력: "사용자가 '미끄럼 방지'라고 검색했을 때, 상품명에 없어도 상세 설명에 있으면 찾아지는가?"를 테스트하기 위함입니다.
"""