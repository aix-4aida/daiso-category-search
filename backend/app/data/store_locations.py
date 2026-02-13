"""Store location data - middle category to physical store location mapping

Based on actual Daiso store floor plan:
- B1: 화장품, 시즌, 건강기능식품, 캐릭터, 문구, 패션, 파티·유아동,
      인테리어소품, 포장, 디지털, 식품
- B2: 욕실, 청소, 세탁, 일본수입, 수납, 홈패브릭, 내추럴코너, 공구,
      스포츠, 반려동물, 수예, 캠핑·차량관리, 주방, 여행, 원예
"""
from dataclasses import dataclass


@dataclass
class StoreLocation:
    counter_number: int
    floor: str
    section_description: str
    x: float
    y: float


# Kiosk position: B1 출입구 (top center of B1 map)
KIOSK_POSITION: dict[str, float] = {"x": 0.45, "y": 0.05}

# Main aisle Y coordinate for B1 waypoint routing (horizontal corridor)
B1_MAIN_AISLE_Y: float = 0.15
# Main aisle Y coordinate for B2 waypoint routing
B2_MAIN_AISLE_Y: float = 0.15

# Middle category (중분류) → store location mapping
MIDDLE_CATEGORY_LOCATIONS: dict[str, StoreLocation] = {
    # ===== B1 (지하1층) =====

    # 뷰티/위생 → B1 화장품(Beauty) 코너 (우측 상단)
    "스킨케어": StoreLocation(1, "B1", "화장품 코너", 0.82, 0.18),
    "메이크업": StoreLocation(2, "B1", "화장품 코너", 0.82, 0.22),
    "네일용품": StoreLocation(3, "B1", "화장품 코너", 0.82, 0.26),
    "미용소품": StoreLocation(4, "B1", "화장품 코너", 0.82, 0.14),
    "맨케어": StoreLocation(5, "B1", "화장품 코너", 0.82, 0.30),
    "헤어/바디": StoreLocation(6, "B1", "화장품 코너", 0.82, 0.20),
    "화장지/물티슈": StoreLocation(7, "B1", "화장품 코너", 0.82, 0.24),

    # 문구/팬시 → B1 문구(Stationery) 코너 (좌측 중간)
    "필기구": StoreLocation(8, "B1", "문구 코너", 0.12, 0.52),
    "노트/메모": StoreLocation(9, "B1", "문구 코너", 0.12, 0.56),
    "사무용품": StoreLocation(10, "B1", "문구 코너", 0.12, 0.48),
    "학용품": StoreLocation(11, "B1", "문구 코너", 0.12, 0.60),

    # 식품 → B1 식품(Snacks) 코너 (우측 최하단)
    "과자/스낵": StoreLocation(12, "B1", "식품 코너", 0.82, 0.86),
    "음료": StoreLocation(13, "B1", "식품 코너", 0.82, 0.90),
    "조미료": StoreLocation(14, "B1", "식품 코너", 0.82, 0.82),

    # 패션/잡화 → B1 패션(Fashion) 코너 (우측 중간)
    "양말/스타킹": StoreLocation(15, "B1", "패션 코너", 0.82, 0.48),
    "슬리퍼": StoreLocation(16, "B1", "패션 코너", 0.82, 0.52),
    "가방/파우치": StoreLocation(17, "B1", "패션 코너", 0.82, 0.44),
    "우산/장갑": StoreLocation(18, "B1", "패션 코너", 0.82, 0.56),

    # 인테리어/원예 → B1 인테리어소품(Interior Prop) (우측 하단)
    "인테리어소품": StoreLocation(19, "B1", "인테리어 소품 코너", 0.82, 0.68),
    "조명": StoreLocation(20, "B1", "인테리어 소품 코너", 0.82, 0.72),

    # 공구/디지털 → B1 디지털(Digital) 코너 (중앙 하단)
    "전기용품": StoreLocation(21, "B1", "디지털 코너", 0.45, 0.78),
    "건전지": StoreLocation(22, "B1", "디지털 코너", 0.45, 0.82),

    # 유아/완구 → B1 파티·유아동(Party·Kids) (중앙)
    "완구": StoreLocation(23, "B1", "파티·유아동 코너", 0.45, 0.58),
    "유아용품": StoreLocation(24, "B1", "파티·유아동 코너", 0.45, 0.62),

    # B1 포장(Packaging) (좌측 하단)
    # - 매핑할 중분류가 직접적으로 없으므로 일회용품을 여기에 배치
    "일회용품": StoreLocation(25, "B1", "포장 코너", 0.12, 0.75),

    # ===== B2 (지하2층) =====

    # 청소/욕실 → B2 욕실(Bath), 청소(Cleaning), 세탁(Laundry)
    "욕실용품": StoreLocation(26, "B2", "욕실 코너", 0.30, 0.08),
    "청소도구": StoreLocation(27, "B2", "청소 코너", 0.50, 0.08),
    "세탁용품": StoreLocation(28, "B2", "세탁 코너", 0.82, 0.05),
    "방향/탈취": StoreLocation(29, "B2", "욕실 코너", 0.30, 0.14),

    # 수납/정리 → B2 수납(Storage)
    "수납함": StoreLocation(30, "B2", "수납 코너", 0.82, 0.28),
    "옷걸이/행거": StoreLocation(31, "B2", "수납 코너", 0.82, 0.32),
    "정리용품": StoreLocation(32, "B2", "수납 코너", 0.82, 0.24),
    "진공백": StoreLocation(33, "B2", "수납 코너", 0.82, 0.36),

    # 주방용품 → B2 주방(Kitchen) (우측 하단)
    "식기/그릇": StoreLocation(34, "B2", "주방 코너", 0.82, 0.72),
    "잔/컵/물병": StoreLocation(35, "B2", "주방 코너", 0.82, 0.76),
    "밀폐/보관용기": StoreLocation(36, "B2", "주방 코너", 0.82, 0.68),
    "수저/커트러리": StoreLocation(37, "B2", "주방 코너", 0.82, 0.80),
    "주방잡화": StoreLocation(38, "B2", "주방 코너", 0.82, 0.74),
    "조리도구": StoreLocation(39, "B2", "주방 코너", 0.82, 0.70),
    "팬/냄비": StoreLocation(40, "B2", "주방 코너", 0.82, 0.78),

    # 공구 → B2 공구(Tools) (중앙 하부)
    "공구": StoreLocation(41, "B2", "공구 코너", 0.40, 0.55),

    # 스포츠/레저/취미 → B2 스포츠(Sports), 캠핑·차량관리
    "운동용품": StoreLocation(42, "B2", "스포츠 코너", 0.08, 0.68),
    "캠핑/레저": StoreLocation(43, "B2", "캠핑·차량관리 코너", 0.50, 0.68),
    "자동차용품": StoreLocation(44, "B2", "캠핑·차량관리 코너", 0.50, 0.72),

    # 반려동물 → B2 반려동물(Pets) (좌측 하단)
    "강아지용품": StoreLocation(45, "B2", "반려동물 코너", 0.22, 0.68),
    "고양이용품": StoreLocation(46, "B2", "반려동물 코너", 0.22, 0.72),
    "반려동물공통": StoreLocation(47, "B2", "반려동물 코너", 0.22, 0.64),

    # 인테리어/원예 → B2 원예(Gardening) (하단 중앙)
    "원예용품": StoreLocation(48, "B2", "원예 코너", 0.48, 0.88),
}


def get_location(category_middle: str | None) -> StoreLocation | None:
    """Get store location for a middle category"""
    if category_middle is None:
        return None
    return MIDDLE_CATEGORY_LOCATIONS.get(category_middle)


def build_waypoints(
    dest_x: float, dest_y: float, floor: str = "B1"
) -> list[dict[str, float]]:
    """Build navigation waypoints from kiosk to destination.

    Route: kiosk → main aisle → horizontal move → destination
    For B2, the path assumes stairs/escalator at top center,
    so the starting point mirrors the kiosk position.
    """
    kx = KIOSK_POSITION["x"]
    ky = KIOSK_POSITION["y"]
    aisle_y = B1_MAIN_AISLE_Y if floor == "B1" else B2_MAIN_AISLE_Y

    # If destination is above the aisle, go directly
    if dest_y <= aisle_y:
        points: list[dict[str, float]] = [
            {"x": kx, "y": ky},
            {"x": dest_x, "y": ky},
            {"x": dest_x, "y": dest_y},
        ]
    else:
        points = [
            {"x": kx, "y": ky},
            {"x": kx, "y": aisle_y},
            {"x": dest_x, "y": aisle_y},
            {"x": dest_x, "y": dest_y},
        ]
    return points
