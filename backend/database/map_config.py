"""
Map Configuration for Daiso Store Navigation
=============================================
Defines section coordinates, shelf positions, corridor waypoints,
and category-to-section mapping for B1 and B2 floors.

All coordinates are in percentage (0-100) relative to map image dimensions.
Origin (0,0) is top-left.
"""

# ============================================================
# B1 Floor - Section Definitions
# ============================================================
# Each section: code prefix, center (x,y), bounding box (x1,y1,x2,y2), shelf points
B1_SECTIONS = {
    "시즌": {
        "code": "B1-A",
        "center": (40, 24),
        "bbox": (30, 14, 52, 34),
        "shelves": [(35, 18), (45, 18), (35, 28), (45, 28)],
        "label": "시즌/Season",
    },
    "화장품": {
        "code": "B1-B",
        "center": (78, 18),
        "bbox": (62, 5, 95, 35),
        "shelves": [(67, 10), (75, 10), (85, 10), (67, 18), (75, 18), (85, 18), (67, 26), (75, 26), (85, 26)],
        "label": "화장품/Beauty",
    },
    "건강기능식품": {
        "code": "B1-C",
        "center": (42, 38),
        "bbox": (30, 34, 52, 45),
        "shelves": [(35, 37), (45, 37), (35, 42), (45, 42)],
        "label": "건강기능식품/Health",
    },
    "캐릭터": {
        "code": "B1-D",
        "center": (42, 50),
        "bbox": (30, 45, 52, 56),
        "shelves": [(35, 48), (45, 48), (35, 53), (45, 53)],
        "label": "캐릭터/Character",
    },
    "패션": {
        "code": "B1-E",
        "center": (78, 48),
        "bbox": (62, 36, 95, 58),
        "shelves": [(67, 40), (78, 40), (88, 40), (67, 48), (78, 48), (88, 48), (67, 54), (78, 54)],
        "label": "패션/Fashion",
    },
    "문구": {
        "code": "B1-F",
        "center": (14, 58),
        "bbox": (2, 50, 28, 66),
        "shelves": [(7, 53), (15, 53), (22, 53), (7, 60), (15, 60), (22, 60)],
        "label": "문구/Stationery",
    },
    "파티유아동": {
        "code": "B1-G",
        "center": (42, 62),
        "bbox": (28, 56, 52, 68),
        "shelves": [(33, 59), (42, 59), (33, 65), (42, 65)],
        "label": "파티유아동/Party·Kids",
    },
    "포장": {
        "code": "B1-H",
        "center": (10, 78),
        "bbox": (2, 70, 22, 84),
        "shelves": [(6, 73), (14, 73), (6, 80), (14, 80)],
        "label": "포장/Packaging",
    },
    "디지털": {
        "code": "B1-I",
        "center": (40, 82),
        "bbox": (28, 76, 52, 88),
        "shelves": [(32, 79), (42, 79), (32, 85), (42, 85)],
        "label": "디지털/Digital",
    },
    "인테리어소품": {
        "code": "B1-J",
        "center": (78, 68),
        "bbox": (62, 58, 95, 78),
        "shelves": [(67, 62), (78, 62), (88, 62), (67, 70), (78, 70), (88, 70)],
        "label": "인테리어소품/Interior Prop",
    },
    "식품": {
        "code": "B1-K",
        "center": (78, 86),
        "bbox": (62, 78, 95, 96),
        "shelves": [(67, 82), (78, 82), (88, 82), (67, 90), (78, 90), (88, 90)],
        "label": "식품/Snacks",
    },
}

# ============================================================
# B2 Floor - Section Definitions
# ============================================================
B2_SECTIONS = {
    "욕실": {
        "code": "B2-A",
        "center": (38, 10),
        "bbox": (28, 3, 50, 18),
        "shelves": [(33, 7), (43, 7), (33, 14), (43, 14)],
        "label": "욕실/Bath",
    },
    "청소": {
        "code": "B2-B",
        "center": (58, 10),
        "bbox": (50, 3, 68, 18),
        "shelves": [(53, 7), (63, 7), (53, 14)],
        "label": "청소/Cleaning",
    },
    "세탁": {
        "code": "B2-C",
        "center": (82, 7),
        "bbox": (72, 3, 95, 13),
        "shelves": [(77, 7), (87, 7)],
        "label": "세탁/Laundry",
    },
    "득템": {
        "code": "B2-D",
        "center": (85, 17),
        "bbox": (75, 13, 95, 22),
        "shelves": [(80, 17), (90, 17)],
        "label": "득템/Good Place",
    },
    "일본수입": {
        "code": "B2-E",
        "center": (42, 26),
        "bbox": (28, 20, 55, 33),
        "shelves": [(33, 23), (45, 23), (33, 30), (45, 30)],
        "label": "일본수입/Japanese Imported",
    },
    "수납": {
        "code": "B2-F",
        "center": (78, 28),
        "bbox": (65, 22, 95, 35),
        "shelves": [(70, 25), (82, 25), (70, 32), (82, 32)],
        "label": "수납/Storage",
    },
    "홈패브릭": {
        "code": "B2-G",
        "center": (42, 40),
        "bbox": (28, 34, 55, 47),
        "shelves": [(33, 37), (45, 37), (33, 44), (45, 44)],
        "label": "홈패브릭/Home Fabric",
    },
    "내추럴코너": {
        "code": "B2-H",
        "center": (78, 42),
        "bbox": (65, 35, 95, 50),
        "shelves": [(70, 38), (82, 38), (70, 45), (82, 45)],
        "label": "내추럴코너/Natural Corner",
    },
    "공구": {
        "code": "B2-I",
        "center": (42, 53),
        "bbox": (28, 48, 55, 58),
        "shelves": [(35, 52), (48, 52)],
        "label": "공구/Tools",
    },
    "스포츠": {
        "code": "B2-J",
        "center": (8, 67),
        "bbox": (2, 60, 18, 75),
        "shelves": [(6, 64), (13, 64), (6, 71), (13, 71)],
        "label": "스포츠/Sports",
    },
    "반려동물": {
        "code": "B2-K",
        "center": (26, 67),
        "bbox": (18, 60, 35, 75),
        "shelves": [(22, 64), (30, 64), (22, 71), (30, 71)],
        "label": "반려동물/Pets",
    },
    "수예": {
        "code": "B2-L",
        "center": (40, 67),
        "bbox": (35, 60, 48, 75),
        "shelves": [(38, 64), (44, 64), (38, 71)],
        "label": "수예/Handcraft",
    },
    "캠핑차량관리": {
        "code": "B2-M",
        "center": (55, 67),
        "bbox": (48, 60, 63, 75),
        "shelves": [(50, 64), (58, 64), (50, 71)],
        "label": "캠핑차량관리/Camping·Car Care",
    },
    "주방": {
        "code": "B2-N",
        "center": (80, 67),
        "bbox": (65, 58, 95, 78),
        "shelves": [(70, 62), (82, 62), (70, 68), (82, 68), (70, 74), (82, 74)],
        "label": "주방/Kitchen",
    },
    "여행": {
        "code": "B2-O",
        "center": (28, 85),
        "bbox": (18, 80, 40, 92),
        "shelves": [(24, 84), (34, 84)],
        "label": "여행/Travel",
    },
    "원예": {
        "code": "B2-P",
        "center": (52, 87),
        "bbox": (40, 82, 62, 95),
        "shelves": [(45, 86), (55, 86)],
        "label": "원예/Gardening",
    },
}

# ============================================================
# Entrance / Current Position
# ============================================================
B1_ENTRANCE = (33, 94)   # 입구 ENTRANCE ONLY
B2_ENTRANCE = (28, 96)   # B2 계단 입구

# ============================================================
# Corridor Waypoints (white paths only)
# ============================================================
# These define the walkable corridor graph.
# Format: list of (x, y) nodes. Edges connect waypoints that share
# a corridor segment. The pathfinder uses these as an adjacency graph.

B1_WAYPOINTS = [
    # Entrance area
    (33, 94),   # 0: 입구
    (33, 85),   # 1: 입구 바로 위 (디지털 옆)
    (25, 85),   # 2: 포장 앞
    (55, 85),   # 3: 디지털-식품 사이
    # Middle corridor (horizontal)
    (25, 68),   # 4: 포장-문구 사이
    (25, 58),   # 5: 문구 앞
    (55, 68),   # 6: 파티유아동-인테리어 사이
    (55, 58),   # 7: 파티유아동 위
    # Center vertical corridor
    (28, 48),   # 8: 문구-캐릭터 사이
    (28, 36),   # 9: 캐릭터-건강 사이
    (55, 48),   # 10: 캐릭터-패션 사이
    (55, 36),   # 11: 건강기능식품-화장품 사이
    # Upper corridor
    (28, 14),   # 12: 시즌 위쪽
    (55, 14),   # 13: 시즌-화장품 사이
    (55, 5),    # 14: 출입구 영역
    # Right side corridor
    (60, 85),   # 15: 식품 옆
    (60, 58),   # 16: 인테리어소품 옆
    (60, 36),   # 17: 패션 옆
    (60, 14),   # 18: 화장품 옆
]

# Edges (bidirectional): pairs of waypoint indices
B1_EDGES = [
    (0, 1),    # 입구 → 디지털 옆
    (1, 2),    # 디지털 옆 → 포장 앞
    (1, 3),    # 디지털 옆 → 식품 쪽
    (2, 4),    # 포장 앞 → 포장-문구 사이
    (4, 5),    # 포장-문구 사이 → 문구 앞
    (4, 6),    # 포장-문구 → 파티유아동 사이 (수평)
    (3, 15),   # 디지털-식품 → 식품 옆
    (3, 6),    # 디지털-식품 → 파티유아동-인테리어 사이
    (5, 8),    # 문구앞 → 캐릭터 사이
    (6, 7),    # 파티유아동-인테리어 → 파티유아동 위
    (6, 16),   # 파티유아동-인테리어 → 인테리어소품 옆
    (7, 10),   # 파티유아동 위 → 캐릭터-패션
    (8, 9),    # 문구-캐릭터 → 캐릭터-건강
    (8, 10),   # 문구-캐릭터 → 캐릭터-패션 (횡단)
    (9, 11),   # 캐릭터-건강 → 건강-화장품 (횡단)
    (9, 12),   # 캐릭터-건강 → 시즌 위
    (10, 11),  # 캐릭터-패션 → 건강-화장품
    (10, 17),  # 캐릭터-패션 → 패션 옆
    (11, 13),  # 건강-화장품 → 시즌-화장품
    (12, 13),  # 시즌위 → 시즌-화장품
    (13, 14),  # 시즌-화장품 → 출입구
    (13, 18),  # 시즌-화장품 → 화장품 옆
    (15, 16),  # 식품옆 → 인테리어소품 옆
    (16, 17),  # 인테리어소품 → 패션 옆
    (17, 18),  # 패션옆 → 화장품옆
]

B2_WAYPOINTS = [
    # Entrance (stairs area from B1)
    (28, 96),   # 0: B2 입구
    (28, 78),   # 1: 여행 옆
    (55, 78),   # 2: 원예 옆
    # Lower corridor
    (14, 58),   # 3: 스포츠 위
    (28, 58),   # 4: 반려동물 위
    (42, 58),   # 5: 수예 위
    (55, 58),   # 6: 캠핑 위
    (63, 58),   # 7: 캠핑-주방 사이
    # Middle corridor
    (28, 48),   # 8: 공구 옆
    (55, 48),   # 9: 공구-내추럴 사이
    (63, 48),   # 10: 내추럴 옆
    # Upper-middle corridor
    (28, 34),   # 11: 일본수입 위
    (55, 34),   # 12: 홈패브릭-내추럴
    (63, 34),   # 13: 수납 옆
    # Upper corridor
    (28, 20),   # 14: 욕실 위
    (55, 20),   # 15: 일본수입-수납
    (63, 20),   # 16: 수납 위
    # Top corridor
    (28, 3),    # 17: 욕실-청소 위
    (55, 3),    # 18: 청소 위
    (72, 3),    # 19: 세탁 옆
    (90, 3),    # 20: 세탁-득템
    # Right corridor
    (63, 78),   # 21: 주방 아래
    (63, 14),   # 22: 득템 옆
]

B2_EDGES = [
    (0, 1),
    (1, 2),    # 입구 → 원예 옆
    (1, 4),    # 입구 → 반려동물 위
    (2, 6),    # 원예옆 → 캠핑 위
    (2, 21),   # 원예옆 → 주방 아래
    (3, 4),    # 스포츠 → 반려동물
    (4, 5),    # 반려동물 → 수예
    (4, 8),    # 반려동물 → 공구 옆
    (5, 6),    # 수예 → 캠핑
    (6, 7),    # 캠핑 → 캠핑-주방
    (7, 21),   # 캠핑-주방 → 주방 아래
    (7, 10),   # 캠핑-주방 → 내추럴 옆
    (8, 9),    # 공구옆 → 공구-내추럴
    (8, 11),   # 공구옆 → 일본수입 위
    (9, 10),   # 공구-내추럴 → 내추럴 옆
    (10, 13),  # 내추럴옆 → 수납 옆
    (10, 21),  # 내추럴옆 → 주방 아래
    (11, 12),  # 일본수입 → 홈패브릭-내추럴
    (11, 14),  # 일본수입 → 욕실 위
    (12, 13),  # 홈패브릭-내추럴 → 수납옆
    (13, 16),  # 수납옆 → 수납 위
    (13, 22),  # 수납옆 → 득템 옆
    (14, 15),  # 욕실위 → 일본수입-수납
    (14, 17),  # 욕실위 → 욕실 최상단
    (15, 16),  # 일본수입-수납 → 수납 위
    (16, 22),  # 수납 위 → 득템 옆
    (17, 18),  # 욕실 최상단 → 청소 위
    (18, 19),  # 청소 위 → 세탁 옆
    (19, 20),  # 세탁 옆 → 득템
    (20, 22),  # 득템 → 득템 옆 (하단)
    (21, 22),  # 주방 아래 → 득템 옆
]

# ============================================================
# Category Major → Map Section Mapping
# ============================================================
CATEGORY_TO_SECTION = {
    # B1 sections
    "시즌/시리즈": ("B1", "시즌"),
    "뷰티/위생": ("B1", "화장품"),
    "문구/팬시": ("B1", "문구"),
    "식품": ("B1", "식품"),
    "패션/잡화": ("B1", "패션"),
    "공구/디지털": ("B1", "디지털"),
    "국민득템": ("B2", "득템"),
    # B2 sections
    "청소/욕실": ("B2", "욕실"),       # Primary: 욕실+청소
    "주방용품": ("B2", "주방"),
    "반려동물": ("B2", "반려동물"),
    "수납/정리": ("B2", "수납"),
    "스포츠/레저/취미": ("B2", "스포츠"),
    "유아/완구": ("B1", "파티유아동"),
    "인테리어/원예": ("B2", "내추럴코너"),
    "상품권": ("B1", "시즌"),          # Fallback
}

# ============================================================
# Helper: find closest waypoint to a section
# ============================================================
def _dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

def get_section_entry_waypoint(floor, section_name):
    """Return the index of the closest corridor waypoint to a section's center."""
    sections = B1_SECTIONS if floor == "B1" else B2_SECTIONS
    waypoints = B1_WAYPOINTS if floor == "B1" else B2_WAYPOINTS
    
    if section_name not in sections:
        return 0
    
    center = sections[section_name]["center"]
    closest_idx = 0
    closest_dist = float('inf')
    for i, wp in enumerate(waypoints):
        d = _dist(center, wp)
        if d < closest_dist:
            closest_dist = d
            closest_idx = i
    return closest_idx

def get_all_sections():
    """Return a merged dict of all sections across floors."""
    result = {}
    for name, info in B1_SECTIONS.items():
        result[info["code"]] = {"floor": "B1", "name": name, **info}
    for name, info in B2_SECTIONS.items():
        result[info["code"]] = {"floor": "B2", "name": name, **info}
    return result
