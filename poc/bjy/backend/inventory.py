# Mock inventory for Daiso products with coordinate mapping
# Coordinates based on store map (20x20 grid, 1 unit ≈ 1 meter)

# Map configuration
MAP_CONFIG = {
    "width": 20,           # Map width in units
    "height": 20,          # Map height in units
    "scale": 1.0,          # 1 unit = 1 meter (approximate)
    "kiosk": {             # Kiosk/Start position (현위치)
        "x": 10,
        "y": 2,
        "desc": "Entrance / Kiosk"
    }
}

# Category zone centers (for reference)
CATEGORY_ZONES = {
    "bathroom": {"x": 2, "y": 14, "name": "욕실용품"},
    "cleaning": {"x": 2, "y": 12, "name": "청소용품"},
    "kitchen": {"x": 8, "y": 16, "name": "주방용품"},
    "electronics": {"x": 8, "y": 14, "name": "전자/렌지용품"},
    "food": {"x": 16, "y": 14, "name": "식품"},
    "event": {"x": 10, "y": 12, "name": "이벤트존"},
    "camping": {"x": 4, "y": 10, "name": "캠핑"},
    "travel": {"x": 6, "y": 8, "name": "여행"},
    "kids": {"x": 14, "y": 8, "name": "아동/패션"},
    "cashier": {"x": 10, "y": 2, "name": "계산대"}
}

INVENTORY_DB = [
    {
        "id": 1,
        "name": "Diatomaceous Earth Bath Mat (Hard)",
        "category": "Bathroom",
        "keywords": ["hard mat", "bathroom", "water absorption", "dry", "stone mat", "규조토", "발매트"],
        "description": "A hard, quick-drying bath mat made of diatomaceous earth.",
        "location": {"x": 2, "y": 14, "desc": "욕실용품 코너"}
    },
    {
        "id": 2,
        "name": "Soft Microfiber Bath Mat",
        "category": "Bathroom",
        "keywords": ["soft mat", "bathroom", "fluffy", "washable", "극세사", "매트"],
        "description": "Soft and fluffy microfiber bath mat.",
        "location": {"x": 3, "y": 14, "desc": "욕실용품 코너"}
    },
    {
        "id": 3,
        "name": "AA Batteries (10pcs)",
        "category": "Electronics",
        "keywords": ["battery", "aa", "power", "energy", "dry cell", "건전지", "배터리"],
        "description": "Pack of 10 alkaline AA batteries.",
        "location": {"x": 8, "y": 14, "desc": "전자용품 코너"}
    },
    {
        "id": 4,
        "name": "Travel Toiletry Set",
        "category": "Travel",
        "keywords": ["shampoo", "conditioner", "rinse", "travel", "small", "bottle", "kit", "여행용", "샴푸"],
        "description": "Compact shampoo and rinse set for traveling.",
        "location": {"x": 6, "y": 8, "desc": "여행용품 코너"}
    },
    {
        "id": 5,
        "name": "iPhone Lightning Cable (2m)",
        "category": "Electronics",
        "keywords": ["cable", "iphone", "lightning", "charging", "long cable", "2m", "충전기", "케이블"],
        "description": "2 meter long charging cable for iPhone.",
        "location": {"x": 9, "y": 14, "desc": "전자용품 코너"}
    },
    {
        "id": 6,
        "name": "Camping Lantern LED",
        "category": "Camping",
        "keywords": ["lantern", "camping", "light", "LED", "outdoor", "랜턴", "캠핑"],
        "description": "Portable LED lantern for camping.",
        "location": {"x": 4, "y": 10, "desc": "캠핑용품 코너"}
    },
    {
        "id": 7,
        "name": "Kids Stationery Set",
        "category": "Kids",
        "keywords": ["stationery", "pencil", "eraser", "kids", "school", "문구", "학용품"],
        "description": "Colorful stationery set for children.",
        "location": {"x": 14, "y": 8, "desc": "아동/패션 코너"}
    },
    {
        "id": 8,
        "name": "Snack Mix Pack",
        "category": "Food",
        "keywords": ["snack", "food", "candy", "mix", "과자", "간식"],
        "description": "Assorted snack mix pack.",
        "location": {"x": 16, "y": 14, "desc": "식품 코너"}
    }
]

def get_all_items():
    return INVENTORY_DB

def get_map_config():
    return MAP_CONFIG
