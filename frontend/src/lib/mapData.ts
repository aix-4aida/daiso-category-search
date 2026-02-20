/**
 * Store floor plan data — shelf coordinates and category-to-shelf mapping.
 * Ported from poc/bjy/poc/frontend/phase_2/poc_v6_map_data.js
 */

export interface ShelfInfo {
    id: string;
    floor: "B1" | "B2";
    section: string;
    x: number; // % from left
    y: number; // % from top
}

// ─── Shelf Coordinates (x, y as %) ─────────────────────────────────────────

const shelves: Record<string, ShelfInfo> = {
    // B1
    A01: { id: "A01", floor: "B1", section: "문구", x: 20, y: 72 },
    A02: { id: "A02", floor: "B1", section: "문구", x: 20, y: 80 },
    B01: { id: "B01", floor: "B1", section: "시즌", x: 60, y: 35 },
    C01: { id: "C01", floor: "B1", section: "화장품", x: 80, y: 30 },
    D01: { id: "D01", floor: "B1", section: "건강기능식품", x: 60, y: 50 },
    E01: { id: "E01", floor: "B1", section: "캐릭터", x: 60, y: 60 },
    F01: { id: "F01", floor: "B1", section: "패션", x: 80, y: 60 },
    G01: { id: "G01", floor: "B1", section: "파티/유아동", x: 60, y: 75 },
    H01: { id: "H01", floor: "B1", section: "인테리어 소품", x: 80, y: 75 },
    I01: { id: "I01", floor: "B1", section: "포장", x: 15, y: 85 },
    J01: { id: "J01", floor: "B1", section: "디지털", x: 50, y: 85 },
    K01: { id: "K01", floor: "B1", section: "식품", x: 85, y: 85 },
    // B2
    BA01: { id: "BA01", floor: "B2", section: "욕실", x: 55, y: 20 },
    CL01: { id: "CL01", floor: "B2", section: "청소", x: 70, y: 20 },
    LA01: { id: "LA01", floor: "B2", section: "세탁", x: 90, y: 15 },
    GP01: { id: "GP01", floor: "B2", section: "득템", x: 92, y: 25 },
    JA01: { id: "JA01", floor: "B2", section: "일본수입", x: 55, y: 35 },
    HF01: { id: "HF01", floor: "B2", section: "홈패브릭", x: 55, y: 45 },
    TO01: { id: "TO01", floor: "B2", section: "공구", x: 55, y: 55 },
    ST01: { id: "ST01", floor: "B2", section: "수납", x: 85, y: 40 },
    NC01: { id: "NC01", floor: "B2", section: "내추럴코너", x: 85, y: 55 },
    KI01: { id: "KI01", floor: "B2", section: "주방", x: 80, y: 60 },
    SP01: { id: "SP01", floor: "B2", section: "스포츠", x: 15, y: 72 },
    PE01: { id: "PE01", floor: "B2", section: "반려동물", x: 30, y: 70 },
    HC01: { id: "HC01", floor: "B2", section: "수예", x: 45, y: 70 },
    CA01: { id: "CA01", floor: "B2", section: "캠핑/차량관리", x: 60, y: 70 },
    TR01: { id: "TR01", floor: "B2", section: "여행", x: 40, y: 85 },
    GA01: { id: "GA01", floor: "B2", section: "원예", x: 65, y: 85 },
};

// ─── Category → Shelf Mapping ──────────────────────────────────────────────
// category_middle gives more precision when available

const middleToShelf: Record<string, string> = {
    // 뷰티/위생
    "스킨케어": "C01",
    "메이크업": "C01",
    "네일용품": "C01",
    "미용소품": "C01",
    "맨케어": "C01",
    "화장지/물티슈": "C01",
    "헤어/바디": "BA01",
    // 주방용품
    "식기/그릇": "KI01",
    "잔/컵/물병": "KI01",
    "밀폐/보관용기": "KI01",
    "수저/커트러리": "KI01",
    "주방잡화": "KI01",
    "조리도구": "KI01",
    "팬/냄비": "KI01",
    "일회용품": "KI01",
    // 청소/욕실
    "욕실용품": "BA01",
    "청소도구": "CL01",
    "세탁용품": "LA01",
    "방향/탈취": "NC01",
    // 수납/정리
    "수납함": "ST01",
    "옷걸이/행거": "ST01",
    "정리용품": "ST01",
    "진공백": "ST01",
    // 문구/팬시
    "필기구": "A01",
    "노트/메모": "A02",
    "사무용품": "A01",
    "학용품": "A01",
    // 인테리어/원예
    "인테리어소품": "H01",
    "원예용품": "GA01",
    "조명": "H01",
    // 공구/디지털
    "공구": "TO01",
    "전기용품": "J01",
    "건전지": "J01",
    // 식품
    "과자/스낵": "K01",
    "음료": "K01",
    "조미료": "K01",
    // 스포츠/레저/취미
    "운동용품": "SP01",
    "캠핑/레저": "CA01",
    "자동차용품": "CA01",
    // 패션/잡화
    "양말/스타킹": "F01",
    "슬리퍼": "F01",
    "가방/파우치": "F01",
    "우산/장갑": "F01",
    // 반려동물
    "강아지용품": "PE01",
    "고양이용품": "PE01",
    "반려동물공통": "PE01",
    // 유아/완구
    "완구": "G01",
    "유아용품": "G01",
};

const majorToShelf: Record<string, string> = {
    "뷰티/위생": "C01",
    "주방용품": "KI01",
    "청소/욕실": "CL01",
    "수납/정리": "ST01",
    "문구/팬시": "A01",
    "인테리어/원예": "H01",
    "공구/디지털": "J01",
    "식품": "K01",
    "스포츠/레저/취미": "SP01",
    "패션/잡화": "F01",
    "반려동물": "PE01",
    "유아/완구": "G01",
};

// ─── Floor Map Images ──────────────────────────────────────────────────────

export const floorMaps: Record<string, string> = {
    B1: "/images/map_b1.jpg",
    B2: "/images/map_b2.jpg",
};

// ─── Lookup Function ───────────────────────────────────────────────────────

const DEFAULT_SHELF = shelves["C01"];

export function findShelfByCategory(
    categoryMajor?: string,
    categoryMiddle?: string,
): ShelfInfo {
    // Try middle category first (more precise)
    if (categoryMiddle && middleToShelf[categoryMiddle]) {
        const shelfId = middleToShelf[categoryMiddle];
        return shelves[shelfId] ?? DEFAULT_SHELF;
    }

    // Fall back to major category
    if (categoryMajor && majorToShelf[categoryMajor]) {
        const shelfId = majorToShelf[categoryMajor];
        return shelves[shelfId] ?? DEFAULT_SHELF;
    }

    return DEFAULT_SHELF;
}
