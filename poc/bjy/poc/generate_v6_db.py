
import json

# Load v5 DB (Mocking reading the file I just saw)
# In reality I would read the full file, but for PoC simple generation script is better.
# I will create a script that TAKES v5 file and OUTPUTS v6 file.

import json
import random

# Mapping Rules: Category/Keyword -> New Shelf ID
# B1 Shelves: A01 (Stationery), B01 (Season), C01 (Beauty), D01 (Health), E01 (Character), F01 (Fashion), G01 (Party), H01 (Interior), I01 (Packaging), J01 (Digital), K01 (Snacks)
# B2 Shelves: BA01 (Bath), CL01 (Cleaning), LA01 (Laundry), GP01 (Good Place), JA01 (Japanese), ST01 (Storage), HF01 (Home Fabric), NC01 (Natural), TO01 (Tools), SP01 (Sports), PE01 (Pets), HC01 (Handcraft), CA01 (Camping), KI01 (Kitchen), TR01 (Travel), GA01 (Gardening)

def get_shelf_id(product):
    cat_major = product.get("category_major", "")
    cat_middle = product.get("category_middle", "")
    name = product.get("name", "")
    keywords = product.get("keywords", [])
    combined_text = (name + " " + cat_major + " " + cat_middle + " " + " ".join(keywords)).lower()

    # --- B2 Mapping ---
    if "욕실" in combined_text or "비누" in combined_text or "샴푸" in combined_text: return "BA01"
    if "청소" in combined_text or "세제" in combined_text or "쓰레기" in combined_text: return "CL01"
    if "세탁" in combined_text or "빨래" in combined_text: return "LA01"
    if "수납" in combined_text or "바구니" in combined_text or "정리" in combined_text: return "ST01"
    if "주방" in combined_text or "그릇" in combined_text or "수세미" in combined_text or "컵" in combined_text: return "KI01" 
    if "공구" in combined_text or "건전지" in combined_text: return "TO01" # Battery -> Tools/Digital overlap. Let's put Battery in Digital J01 (B1) or Tools (B2)? Map says "Tools" on B2. "Digital" on B1. Batteries usually near checkout or Digital. I'll put in J01 (B1) for Digital, TO01 for generic tools.
    if "건전지" in combined_text: return "J01" # Digital B1
    if "캠핑" in combined_text: return "CA01"
    if "반려" in combined_text or "강아지" in combined_text or "고양이" in combined_text or "사료" in combined_text: return "PE01"
    if "스포츠" in combined_text or "운동" in combined_text: return "SP01"
    if "원예" in combined_text or "화분" in combined_text: return "GA01"
    if "여행" in combined_text: return "TR01"
    if "일본" in combined_text: return "JA01"
    if "수예" in combined_text or "뜨개" in combined_text: return "HC01"
    if "패브릭" in combined_text or "쿠션" in combined_text or "방석" in combined_text: return "HF01"

    # --- B1 Mapping ---
    if "문구" in combined_text or "노트" in combined_text or "펜" in combined_text: return "A01"
    if "시즌" in combined_text or "크리스마스" in combined_text: return "B01"
    if "뷰티" in combined_text or "화장품" in combined_text or "마스크" in combined_text or "스킨" in combined_text or "미용" in combined_text: return "C01"
    if "건강" in combined_text or "비타민" in combined_text: return "D01"
    if "캐릭터" in combined_text or "인형" in combined_text: return "E01" # Doll -> Character
    if "패션" in combined_text or "옷" in combined_text or "양말" in combined_text or "머리끈" in combined_text: return "F01"
    if "파티" in combined_text: return "G01"
    if "인테리어" in combined_text or "조명" in combined_text or "액자" in combined_text: return "H01"
    if "포장" in combined_text or "쇼핑백" in combined_text: return "I01"
    if "디지털" in combined_text or "충전기" in combined_text or "케이블" in combined_text: return "J01"
    if "식품" in combined_text or "과자" in combined_text or "음료" in combined_text or "커피" in combined_text: return "K01"

    # Default fallback
    return "C01" # Beauty as default

# Read Source
with open("c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v5_mock_product_db.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Update
updated_products = []
for p in products:
    new_shelf = get_shelf_id(p)
    
    # Floor determination
    floor = "B1"
    if len(new_shelf) == 4: # e.g. BA01
        floor = "B2"
    elif new_shelf in ["A01", "A02", "B01", "C01", "D01", "E01", "F01", "G01", "H01", "I01", "J01", "K01"]:
        floor = "B1"

    # Update location field to be human readable but strictly structured
    # Format: "B2_BA01" or just let map data handle it.
    # User requirement: "Store shelf number in DB".
    p["location"] = new_shelf # Store ID in location field? Or create new field?
    # Keeping 'location' as the ID allows easy lookup.
    # The display text "B2 Bath" is derived from map data.
    p["shelf_id"] = new_shelf # Add specific field
    p["floor"] = floor 
    
    updated_products.append(p)

# Write Target
with open("c:/Users/301/pjt/Final/search/search-roca/poc/data/poc_v6_mock_product_db.json", "w", encoding="utf-8") as f:
    json.dump(updated_products, f, ensure_ascii=False, indent=2)

print(f"Generated poc_v6_mock_product_db.json with {len(updated_products)} items.")
