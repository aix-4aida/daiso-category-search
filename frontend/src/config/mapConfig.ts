/**
 * Daiso Store Map Configuration
 * 
 * This file contains zone and shelf coordinates for B1 and B2 floors.
 * Coordinates are in percentage (0-100) relative to the map image dimensions.
 * 
 * Connected to database categories from backend/database/connection.py:
 * - 욕실용품, 청소용품, 주방용품, 문구/팬시, 공구/디지털
 * - 인테리어, 수납, 뷰티/위생, 패션/잡화, 육아/안전
 */

interface ShelfLocation {
    id: string;
    floor: string;
    section: string;
    x: number;
    y: number;
}

interface FloorConfig {
    id: string;
    image: string;
    entrance: { x: number; y: number; label: string };
}

interface MapConfig {
    floors: {
        B1: FloorConfig;
        B2: FloorConfig;
    };
    shelves: Record<string, ShelfLocation>;
}

export const mapConfig: MapConfig = {
    // Floor metadata
    floors: {
        B1: {
            id: "B1",
            image: "/map_b1.jpg",
            entrance: { x: 50, y: 10, label: "B1 입구 (Main)" },
        },
        B2: {
            id: "B2",
            image: "/map_b2.jpg",
            entrance: { x: 25, y: 90, label: "B2 진입 (계단)" },
        }
    },

    // Shelves connected to database CATEGORY_LOCATIONS
    // DB categories: 욕실용품, 청소용품, 주방용품, 문구/팬시, 공구/디지털, 인테리어, 수납, 뷰티/위생, 패션/잡화, 육아/안전
    shelves: {
        // B1 Shelves (매대 13-19) - Adjusted coordinates to aisle (light gray area)
        "13": { id: "13", floor: "B1", section: "문구/팬시", x: 32, y: 75 },           // 문구/팬시 (오른쪽 통로, x=20 -> 32)
        "14": { id: "14", floor: "B1", section: "공구/디지털", x: 50, y: 80 },         // 공구/디지털 (위쪽 통로, y=85 -> 80)
        "15": { id: "15", floor: "B1", section: "인테리어", x: 66, y: 70 },            // 인테리어 (왼쪽 통로, x=80 -> 66)
        "17": { id: "17", floor: "B1", section: "뷰티/위생", x: 66, y: 30 },           // 뷰티/위생 (왼쪽 통로, x=80 -> 66)
        "18": { id: "18", floor: "B1", section: "패션/잡화", x: 66, y: 55 },           // 패션/잡화 (왼쪽 통로, x=80 -> 66)
        "19": { id: "19", floor: "B1", section: "육아/안전", x: 58, y: 70 },           // 육아/안전 (왼쪽 통로, x=60 -> 58)

        // B2 Shelves (매대 10-12, 16) - Adjusted coordinates to aisle (light gray area)
        "10": { id: "10", floor: "B2", section: "욕실용품", x: 55, y: 25 },            // 욕실용품 (아래쪽 통로, y=20 -> 25)
        "11": { id: "11", floor: "B2", section: "청소용품", x: 70, y: 25 },            // 청소용품 (아래쪽 통로, y=20 -> 25)
        "12": { id: "12", floor: "B2", section: "주방용품", x: 66, y: 60 },            // 주방용품 (왼쪽 통로, x=80 -> 66)
        "16": { id: "16", floor: "B2", section: "수납", x: 66, y: 40 },                // 수납 (왼쪽 통로, x=85 -> 66)
    }
};

// Category to Shelf Location mapping (from database CATEGORY_LOCATIONS)
const CATEGORY_TO_SHELF: Record<string, string> = {
    "욕실용품": "10",
    "청소용품": "11",
    "주방용품": "12",
    "문구/팬시": "13",
    "공구/디지털": "14",
    "인테리어": "15",
    "수납": "16",
    "뷰티/위생": "17",
    "패션/잡화": "18",
    "육아/안전": "19",
};

// Keyword to category mapping for product name search
const KEYWORD_TO_CATEGORY: Record<string, string> = {
    // 욕실용품 (10번 매대)
    "샴푸": "욕실용품", "비누": "욕실용품", "욕실": "욕실용품", "목욕": "욕실용품",
    "칫솔": "욕실용품", "치약": "욕실용품", "수건": "욕실용품", "바디워시": "욕실용품",

    // 청소용품 (11번 매대)
    "청소": "청소용품", "밀대": "청소용품", "걸레": "청소용품", "스펀지": "청소용품",
    "빗자루": "청소용품", "휴지통": "청소용품", "먼지": "청소용품",

    // 주방용품 (12번 매대)
    "주방": "주방용품", "그릇": "주방용품", "냄비": "주방용품", "채반": "주방용품",
    "접시": "주방용품", "컵": "주방용품", "수저": "주방용품", "도마": "주방용품",
    "프라이팬": "주방용품", "국자": "주방용품", "밀폐용기": "주방용품",

    // 문구/팬시 (13번 매대)
    "볼펜": "문구/팬시", "펜": "문구/팬시", "문구": "문구/팬시", "노트": "문구/팬시",
    "테이프": "문구/팬시", "스티커": "문구/팬시", "가위": "문구/팬시", "풀": "문구/팬시",
    "연필": "문구/팬시", "지우개": "문구/팬시", "자": "문구/팬시",

    // 공구/디지털 (14번 매대)
    "충전기": "공구/디지털", "케이블": "공구/디지털", "공구": "공구/디지털",
    "드라이버": "공구/디지털", "디지털": "공구/디지털", "배터리": "공구/디지털",
    "이어폰": "공구/디지털", "USB": "공구/디지털",

    // 인테리어 (15번 매대)
    "인테리어": "인테리어", "조명": "인테리어", "액자": "인테리어", "꽃병": "인테리어",
    "화분": "인테리어", "시계": "인테리어", "거울": "인테리어",

    // 수납 (16번 매대)
    "수납": "수납", "바구니": "수납", "정리함": "수납", "서랍": "수납",
    "박스": "수납", "행거": "수납", "옷걸이": "수납",

    // 뷰티/위생 (17번 매대)
    "화장품": "뷰티/위생", "립스틱": "뷰티/위생", "뷰티": "뷰티/위생",
    "마스크": "뷰티/위생", "핸드크림": "뷰티/위생", "화장솜": "뷰티/위생",
    "손톱깎이": "뷰티/위생", "면봉": "뷰티/위생",

    // 패션/잡화 (18번 매대)
    "패션": "패션/잡화", "양말": "패션/잡화", "모자": "패션/잡화",
    "장갑": "패션/잡화", "머리끈": "패션/잡화", "헤어핀": "패션/잡화",

    // 육아/안전 (19번 매대)
    "유아": "육아/안전", "아기": "육아/안전", "장난감": "육아/안전",
    "파티": "육아/안전", "풍선": "육아/안전", "안전": "육아/안전",
};

/**
 * Find product location based on product name or location string
 * @param nameOrLocation - Product name or location string (e.g., "10번 매대 (욕실)")
 * @returns Shelf location object with floor, x, y coordinates
 */
export function findProductLocation(nameOrLocation: string): ShelfLocation {
    if (!nameOrLocation) return mapConfig.shelves["17"]; // Default: 뷰티/위생

    const { shelves } = mapConfig;

    // First, try to extract shelf number from location string like "10번 매대 (욕실)"
    const shelfMatch = nameOrLocation.match(/(\d+)번\s*매대/);
    if (shelfMatch && shelves[shelfMatch[1]]) {
        return shelves[shelfMatch[1]];
    }

    // Try to match category directly
    const shelfId = CATEGORY_TO_SHELF[nameOrLocation];
    if (shelfId && shelves[shelfId]) {
        return shelves[shelfId];
    }

    // Search by keywords in product name
    for (const [keyword, category] of Object.entries(KEYWORD_TO_CATEGORY)) {
        if (nameOrLocation.includes(keyword)) {
            const shelfId = CATEGORY_TO_SHELF[category];
            if (shelfId && shelves[shelfId]) {
                return shelves[shelfId];
            }
        }
    }

    return shelves["17"]; // Default: 뷰티/위생 (B1)
}

/**
 * Get shelf info by shelf ID
 * @param shelfId - Shelf ID (e.g., "10", "13")
 * @returns Shelf object or null
 */
export function getShelfById(shelfId: string): ShelfLocation | null {
    return mapConfig.shelves[shelfId] || null;
}

export default mapConfig;
