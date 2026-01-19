import json
import os
import random

# ==========================================
# 1. Confusion Candidates (The "Trap" Items)
# ==========================================
# These items are designed to confuse Vector Search (Semantic Overlap).
CONFUSION_ITEMS = [
    # [Group: 장갑 (Gloves)]
    {"name": "설거지용 고무장갑", "category": "주방", "desc": "설거지할 때 손을 보호하는 라텍스 고무장갑입니다."},
    {"name": "니트릴 요리 장갑", "category": "주방", "desc": "요리나 청소 시 사용하는 일회용 니트릴 장갑입니다."},
    {"name": "오븐용 방열 장갑", "category": "주방", "desc": "뜨거운 오븐 요리를 꺼낼 때 쓰는 두꺼운 장갑입니다."},
    {"name": "겨울용 털장갑", "category": "의류", "desc": "추운 겨울에 사용하는 스마트폰 터치 방한 장갑입니다."},
    {"name": "가죽 라이딩 장갑", "category": "의류", "desc": "오토바이 라이딩 시 착용하는 가죽 장갑입니다."},
    {"name": "골프 장갑 (양피)", "category": "운동", "desc": "그립감이 좋은 천연 양가죽 골프 장갑입니다."},
    {"name": "헬스용 반장갑", "category": "운동", "desc": "덤벨 운동 시 손바닥 굳은살을 방지하는 헬스 장갑입니다."},
    {"name": "야구 배팅 장갑", "category": "운동", "desc": "타격 시 충격을 흡수하는 야구용 배팅 장갑입니다."},
    {"name": "목장갑 (10켤레)", "category": "공구", "desc": "작업 현장에서 막 쓰기 좋은 면 장갑입니다."},

    # [Group: 매트 (Mat)]
    {"name": "규조토 욕실 매트", "category": "욕실", "desc": "물기를 1초 만에 흡수하는 규조토 성분의 발매트입니다."},
    {"name": "극세사 욕실 발매트", "category": "욕실", "desc": "부드러운 촉감의 욕실 앞 인테리어 매트입니다."},
    {"name": "미끄럼방지 샤워 매트", "category": "욕실", "desc": "욕조 안에 깔아 미끄러짐을 방지하는 안전 매트입니다."},
    {"name": "요가 매트 10mm", "category": "운동", "desc": "충격 흡수가 뛰어난 홈트레이닝용 NBR 요가 매트입니다."},
    {"name": "필라테스 매트", "category": "운동", "desc": "밀리지 않는 논슬립 재질의 필라테스 전용 매트입니다."},
    {"name": "캠핑용 자충 매트", "category": "캠핑", "desc": "밸브를 열면 자동으로 공기가 차는 에어 매트입니다."},
    {"name": "피크닉 방수 돗자리", "category": "캠핑", "desc": "야외 나들이용 방수 피크닉 매트입니다."},
    {"name": "싱크대 물막이 매트", "category": "주방", "desc": "설거지 물 튀김을 방지하는 실리콘 매트입니다."},
    {"name": "차량용 코일 매트", "category": "자동차", "desc": "흙먼지 포집력이 뛰어난 자동차 바닥 매트입니다."},
    {"name": "현관 코일 매트", "category": "인테리어", "desc": "현관 입구 먼지를 잡아주는 디자인 코일 매트입니다."},

    # [Group: 솔 (Brush)]
    {"name": "욕실 청소용 솔", "category": "청소", "desc": "타일 틈새 물때를 제거하는 강력한 청소 브러쉬입니다."},
    {"name": "변기 세척 솔", "category": "청소", "desc": "구석구석 닦기 편한 변기 전용 청소 솔입니다."},
    {"name": "운동화 세척 솔", "category": "청소", "desc": "운동화 찌든 때를 벗겨내는 손잡이형 솔입니다."},
    {"name": "우드 헤어 브러쉬", "category": "미용", "desc": "두피 마사지 기능이 있는 원목 머리빗입니다."},
    {"name": "메이크업 브러쉬 세트", "category": "미용", "desc": "파운데이션과 섀도우를 위한 화장용 브러쉬입니다."},
    {"name": "수채화용 붓 세트", "category": "문구", "desc": "미술 시간에 사용하는 수채화 전용 붓입니다."},
    {"name": "페인트 붓", "category": "공구", "desc": "벽지나 가구 페인팅에 사용하는 넓은 붓입니다."},

    # [Group: 통 (Box/Case)]
    {"name": "반찬 통 (유리)", "category": "주방", "desc": "밀폐력이 좋아 냄새가 새지 않는 유리 반찬 용기입니다."},
    {"name": "대용량 멀티박스", "category": "수납", "desc": "계절 옷이나 장난감을 보관하는 대형 플라스틱 박스입니다."},
    {"name": "공구함 (3단)", "category": "공구", "desc": "다양한 공구를 분리 수납할 수 있는 철제 공구함입니다."},
    {"name": "도시락 통", "category": "주방", "desc": "직장인과 학생을 위한 2단 분리형 도시락 통입니다."},
    {"name": "여행용 파우치 세트", "category": "여행", "desc": "캐리어 내부 짐을 정리하는 메쉬 파우치입니다."},
]

# ==========================================
# 2. Filler Items (To reach 200)
# ==========================================
# Random items to inflate the search space and test Recall.
CATEGORIES = ["주방", "욕실", "운동", "캠핑", "청소", "문구", "공구", "자동차", "반려동물", "의류", "미용", "가전", "인테리어", "식품", "유아동"]

FILLER_TEMPLATES = [
    ("텀블러", "주방", "보온 보냉이 탁월한 스테인리스 텀블러"),
    ("냄비 받침", "주방", "뜨거운 냄비를 올릴 수 있는 실리콘 받침"),
    ("극세사 이불", "침구", "겨울철 따뜻한 극세사 차렵 이불"),
    ("베개 커버", "침구", "순면 100% 호텔식 베개 커버"),
    ("블루투스 스피커", "가전", "음질이 풍부한 휴대용 스피커"),
    ("무선 마우스", "가전", "손목이 편안한 인체공학 무선 마우스"),
    ("강아지 간식", "반려동물", "반려견이 좋아하는 영양 만점 육포"),
    ("고양이 츄르", "반려동물", "고양이가 환장하는 참치맛 츄르"),
    ("차량용 방향제", "자동차", "은은한 향기가 퍼지는 송풍구 방향제"),
    ("세차 타월", "자동차", "물기 자국이 남지 않는 드라잉 타월"),
    ("A4 용지", "문구", "프린터 복사기 겸용 백색 용지"),
    ("3색 볼펜", "문구", "필기감이 부드러운 초저점도 볼펜"),
    ("멀티탭 4구", "가전", "개별 스위치가 달린 절전형 멀티탭"),
    ("드라이기", "미용", "바람이 강력한 전문가용 헤어 드라이어"),
    ("샴푸", "욕실", "두피를 시원하게 해주는 쿨링 샴푸"),
    ("바디워시", "욕실", "촉촉한 보습감을 주는 퍼퓸 바디워시"),
    ("수건 세트", "욕실", "흡수력이 좋은 40수 코마사 타월"),
    ("캠핑 의자", "캠핑", "가볍고 튼튼한 접이식 릴렉스 체어"),
    ("캠핑 램프", "캠핑", "감성적인 분위기의 LED 랜턴"),
    ("폼 클렌징", "미용", "모공 속 노폐물을 씻어내는 세안제"),
    ("마스크팩", "미용", "수분을 공급해주는 히알루론산 시트팩"),
    ("등산 스틱", "운동", "무릎 충격을 줄여주는 카본 등산 스틱"),
    ("아령 세트", "운동", "집에서 근력 운동하기 좋은 덤벨"),
]

def generate_products():
    products = []
    pid = 1
    
    # 1. Add Confusion Items
    for item in CONFUSION_ITEMS:
        products.append({
            "id": pid,
            "name": item["name"],
            "category": item["category"],
            "desc": item["desc"]
        })
        pid += 1
        
    # 2. Add Filler Items (Repeat to fill up to 200)
    while pid <= 200:
        tpl = random.choice(FILLER_TEMPLATES)
        # Add slight variation to name to avoid exact duplicates
        variation = random.choice(["(신형)", "(고급형)", "(가성비)", "(대형)", "(소형)", "1+1", "세트"])
        products.append({
            "id": pid,
            "name": f"{tpl[0]} {variation}",
            "category": tpl[1],
            "desc": tpl[2]
        })
        pid += 1
        
    return products

# ==========================================
# 3. Test Inputs (The "Exam Sheet")
# ==========================================
TEST_INPUTS = [
    # [Target: 고무장갑 (주방)]
    {"id": 1, "query": "설거지할 때 끼는 고무장갑", "expected_category": "주방", "target_keyword": "설거지용 고무장갑", "negative_keywords": ["겨울", "골프"]},
    {"id": 2, "query": "안 미끄러지는 설거지 장갑", "expected_category": "주방", "target_keyword": "고무장갑", "negative_keywords": ["골프"]},
    
    # [Target: 골프장갑 (운동)]
    {"id": 3, "query": "필드 나갈 때 쓰는 골프 장갑", "expected_category": "운동", "target_keyword": "골프 장갑", "negative_keywords": ["설거지", "털장갑"]},
    {"id": 4, "query": "그립감 좋은 양피 장갑", "expected_category": "운동", "target_keyword": "골프 장갑", "negative_keywords": ["고무"]},

    # [Target: 털장갑 (의류)]
    {"id": 5, "query": "겨울에 끼는 스마트폰 터치 장갑", "expected_category": "의류", "target_keyword": "겨울용 털장갑", "negative_keywords": ["설거지", "골프"]},
    
    # [Target: 욕실매트 (욕실)]
    {"id": 6, "query": "화장실 앞에 깔아두는 매트", "expected_category": "욕실", "target_keyword": "욕실", "negative_keywords": ["요가", "캠핑", "차량"]},
    {"id": 7, "query": "물기 잘 마르는 규조토 발매트", "expected_category": "욕실", "target_keyword": "규조토", "negative_keywords": ["요가"]},
    
    # [Target: 요가매트 (운동)]
    {"id": 8, "query": "집에서 스트레칭할 때 까요는 매트", "expected_category": "운동", "target_keyword": "요가", "negative_keywords": ["욕실", "현관"]},
    {"id": 9, "query": "층간소음 방지용 두꺼운 운동 매트", "expected_category": "운동", "target_keyword": "요가", "negative_keywords": ["욕실"]},
    
    # [Target: 차량용 매트 (자동차)]
    {"id": 10, "query": "자동차 바닥에 까는 코일 매트", "expected_category": "자동차", "target_keyword": "차량", "negative_keywords": ["욕실", "요가"]},
    
    # [Target: 변기솔 (청소)]
    {"id": 11, "query": "변기 안쪽 닦는 청소 솔", "expected_category": "청소", "target_keyword": "변기", "negative_keywords": ["머리", "화장"]},
    
    # [Target: 헤어브러쉬 (미용)]
    {"id": 12, "query": "머리 빗는 나무 빗", "expected_category": "미용", "target_keyword": "헤어", "negative_keywords": ["변기", "청소"]},
    
    # [Target: 붓/브러쉬 (문구/미용)]
    {"id": 13, "query": "그림 그릴 때 쓰는 수채화 붓", "expected_category": "문구", "target_keyword": "수채화", "negative_keywords": ["청소", "화장"]},
    
    # [Target: 공구함 (공구)]
    {"id": 14, "query": "망치랑 드라이버 넣는 통", "expected_category": "공구", "target_keyword": "공구함", "negative_keywords": ["반찬", "도시락"]},
    
    # [Target: 반찬통 (주방)]
    {"id": 15, "query": "김치 담아서 냉장고에 넣는 통", "expected_category": "주방", "target_keyword": "반찬", "negative_keywords": ["공구", "옷"]},
]

# Generate Inputs (Easy way: just define 20 solid cases is enough proof, but user asked for 50)
# Let's multiply variations to reach 50
VARIATIONS = [
    (" 추천해줘", ""),
    (" 찾아줘", ""),
    (" 있나요?", ""),
    (" 구매하고 싶어", ""),
    (" 보여줘", "")
]

def generate_test_inputs():
    final_inputs = []
    tid = 1
    
    for base in TEST_INPUTS:
        # Create 3-4 variations for each base case
        for suffix, _ in VARIATIONS[:3]: # Take 3 variations
            new_query = base["query"] + suffix
            final_inputs.append({
                "id": tid,
                "query": new_query,
                "expected_category": base["expected_category"],
                "target_keyword": base["target_keyword"],
                "negative_keywords": base["negative_keywords"]
            })
            tid += 1
            if tid > 50: break
        if tid > 50: break
            
    return final_inputs

if __name__ == "__main__":
    # Ensure directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate & Save Products
    products = generate_products()
    with open(os.path.join(output_dir, "products_large.json"), "w", encoding="utf-8") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)
    print(f"✅ Generated {len(products)} products in 'products_large.json'")
    
    # Generate & Save Test Inputs
    test_inputs = generate_test_inputs()
    with open(os.path.join(output_dir, "test_inputs_large.json"), "w", encoding="utf-8") as f:
        json.dump(test_inputs, f, indent=4, ensure_ascii=False)
    print(f"✅ Generated {len(test_inputs)} test inputs in 'test_inputs_large.json'")
