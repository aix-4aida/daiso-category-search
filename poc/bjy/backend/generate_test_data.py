"""
Test Utterance Generator for STT Testing
Generates 3000 utterances (85% normal, 15% hard)
"""
import random
from database import get_connection, get_all_products, insert_utterance, get_utterance_count

TARGET_TOTAL = 3000
NORMAL_RATIO = 0.85  # 2550
HARD_RATIO = 0.15    # 450

# Normal utterance templates
NORMAL_TEMPLATES = [
    "{name} 있나요?",
    "{name} 어디 있어요?",
    "{name} 찾고 있어요",
    "{name} 어디서 파나요?",
    "{name} 재고 있나요?",
    "{name} 위치 알려주세요",
    "{name} 어느 코너에 있어요?",
    "혹시 {name} 있나요?",
    "{name} 어디에 있죠?",
    "{name} 팔아요?",
    "{name} 코너가 어디예요?",
    "{name} 가격이 얼마예요?",
    "{name}요",
    "{name} 주세요",
    "{name} 보여주세요",
]

# Hard utterance templates (dialect, informal, vague)
HARD_TEMPLATES = [
    # 전라도 사투리
    "{name} 어딨어요?",
    "{name} 그거 있잖여",
    "{name} 있능가?",
    # 경상도 사투리
    "{name} 어데 있노?",
    "{name} 있나 안있나?",
    "{name} 그거 어딨능교?",
    # 충청도 사투리
    "{name} 있슈?",
    "{name} 어딨슈?",
    "{name} 그거 있나유?",
    # 비정형/단답
    "저기요, {name}",
    "그거... {name} 같은 거",
    "{name}!",
    "이거 {name} 맞아요?",
    "{name} 비슷한 거",
    # 설명형
    "{name} 같은 거 찾는데요",
    "{name} 종류로 뭐 있어요?",
]

# Synonyms and variations for common products
PRODUCT_VARIATIONS = {
    "물티슈": ["물티슈", "젖은 티슈", "물휴지"],
    "휴지": ["휴지", "화장지", "두루마리"],
    "건전지": ["건전지", "배터리", "밧데리"],
    "충전기": ["충전기", "충전선", "케이블"],
    "수세미": ["수세미", "설거지 솔", "쇠수세미"],
    "장갑": ["장갑", "고무장갑", "장갑류"],
    "마스크": ["마스크", "마스크팩", "얼굴팩"],
}

def get_product_variation(name: str) -> str:
    """Get a random variation of product name"""
    for key, variations in PRODUCT_VARIATIONS.items():
        if key in name:
            return random.choice(variations)
    return name

def generate_utterances():
    """Generate 3000 test utterances"""
    print("=" * 50)
    print("🚀 Generating Test Utterances")
    print(f"🎯 Target: {TARGET_TOTAL} (Normal: {int(TARGET_TOTAL * NORMAL_RATIO)}, Hard: {int(TARGET_TOTAL * HARD_RATIO)})")
    print("=" * 50)
    
    products = get_all_products()
    if not products:
        print("❌ No products found. Run crawler first.")
        return
    
    print(f"📦 Using {len(products)} products as base")
    
    current_count = get_utterance_count()
    if current_count >= TARGET_TOTAL:
        print(f"✅ Already have {current_count} utterances. Skipping.")
        return
    
    normal_target = int(TARGET_TOTAL * NORMAL_RATIO)
    hard_target = int(TARGET_TOTAL * HARD_RATIO)
    
    normal_count = 0
    hard_count = 0
    
    # Generate normal utterances
    print("\n📝 Generating normal utterances...")
    while normal_count < normal_target:
        product = random.choice(products)
        template = random.choice(NORMAL_TEMPLATES)
        
        # Use product name or variation
        name = get_product_variation(product['name']) if random.random() > 0.7 else product['name']
        utterance = template.format(name=name)
        
        if insert_utterance(utterance, 'normal', product['id']):
            normal_count += 1
            if normal_count % 500 == 0:
                print(f"   Normal: {normal_count}/{normal_target}")
    
    # Generate hard utterances
    print("\n📝 Generating hard utterances...")
    while hard_count < hard_target:
        product = random.choice(products)
        template = random.choice(HARD_TEMPLATES)
        
        # Use shorter/informal name for hard cases
        name = product['name'].split()[0] if len(product['name'].split()) > 1 else product['name']
        if random.random() > 0.5:
            name = get_product_variation(product['name'])
        
        utterance = template.format(name=name)
        
        if insert_utterance(utterance, 'hard', product['id']):
            hard_count += 1
            if hard_count % 100 == 0:
                print(f"   Hard: {hard_count}/{hard_target}")
    
    final_count = get_utterance_count()
    print("\n" + "=" * 50)
    print(f"✅ Generated {final_count} utterances!")
    print(f"   Normal: {normal_count}")
    print(f"   Hard: {hard_count}")
    print("=" * 50)

def show_samples():
    """Show sample utterances"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n📋 Sample Normal Utterances:")
    cursor.execute('''
        SELECT u.utterance, p.name 
        FROM test_utterances u 
        JOIN products p ON u.expected_product_id = p.id 
        WHERE u.difficulty = 'normal' 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"   [{row['name'][:15]}] → \"{row['utterance']}\"")
    
    print("\n📋 Sample Hard Utterances:")
    cursor.execute('''
        SELECT u.utterance, p.name 
        FROM test_utterances u 
        JOIN products p ON u.expected_product_id = p.id 
        WHERE u.difficulty = 'hard' 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"   [{row['name'][:15]}] → \"{row['utterance']}\"")
    
    conn.close()

if __name__ == "__main__":
    generate_utterances()
    show_samples()
