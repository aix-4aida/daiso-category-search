/**
 * categories.js
 * Category Map View — Dual-floor layout with SVG section labels & category filter.
 * Matches the section codes used in map.js GRAPH data.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCategoryView();
});

// B1 section data with pixel-accurate positions (% of 863x1024 image)
const B1_SECTIONS = [
    { code: 'B01', name: '시즌', en: 'Season', x: 53, y: 33, color: '#FFCDD2', cat: '시즌' },
    { code: 'C01', name: '화장품', en: 'Beauty', x: 83, y: 30, color: '#F8BBD0', cat: '뷰티' },
    { code: 'D01', name: '건강기능식품', en: 'Health', x: 54.4, y: 46, color: '#C8E6C9', cat: '건강' },
    { code: 'E01', name: '캐릭터', en: 'Character', x: 55, y: 59, color: '#FFF9C4', cat: '캐릭터' },
    { code: 'F01', name: '패션', en: 'Fashion', x: 83, y: 61, color: '#D1C4E9', cat: '패션' },
    { code: 'A02', name: '문구', en: 'Stationery', x: 23, y: 67, color: '#BBDEFB', cat: '문구' },
    { code: 'G01', name: '파티·유아동', en: 'Party/Kids', x: 49, y: 70, color: '#FFE0B2', cat: '파티' },
    { code: 'I01', name: '포장', en: 'Packaging', x: 17, y: 90, color: '#CFD8DC', cat: '포장' },
    { code: 'J01', name: '디지털', en: 'Digital', x: 53, y: 86, color: '#B3E5FC', cat: '디지털' },
    { code: 'H01', name: '인테리어소품', en: 'Interior Prop', x: 83, y: 79, color: '#C8E6C9', cat: '인테리어' },
    { code: 'K01', name: '식품', en: 'Snacks', x: 83, y: 92, color: '#FFCCBC', cat: '식품' },
];

// B2 section data
const B2_SECTIONS = [
    { code: 'BA01', name: '욕실', en: 'Bath', x: 53, y: 13, color: '#B2EBF2', cat: '욕실' },
    { code: 'CL01', name: '청소', en: 'Cleaning', x: 69, y: 13, color: '#DCEDC8', cat: '청소' },
    { code: 'LA01', name: '세탁', en: 'Laundry', x: 86, y: 8, color: '#E1BEE7', cat: '세탁' },
    { code: 'GP01', name: '득템', en: 'Good Place', x: 88, y: 20, color: '#FFF176', cat: '득템' },
    { code: 'JA01', name: '일본수입', en: 'Japanese', x: 54, y: 28, color: '#FFCDD2', cat: '일본수입' },
    { code: 'ST01', name: '수납', en: 'Storage', x: 83, y: 29, color: '#CFD8DC', cat: '수납' },
    { code: 'HF01', name: '홈패브릭', en: 'Home Fabric', x: 54, y: 40, color: '#D7CCC8', cat: '홈패브릭' },
    { code: 'NC01', name: '내추럴코너', en: 'Natural', x: 83, y: 40, color: '#AED581', cat: '자연' },
    { code: 'TO01', name: '공구', en: 'Tools', x: 54, y: 52, color: '#90A4AE', cat: '공구' },
    { code: 'KI01', name: '주방', en: 'Kitchen', x: 82, y: 75, color: '#FFE082', cat: '주방' },
    { code: 'SP01', name: '스포츠', en: 'Sports', x: 14, y: 78, color: '#80CBC4', cat: '스포츠' },
    { code: 'PE01', name: '반려동물', en: 'Pets', x: 28, y: 72, color: '#FFAB91', cat: '애견' },
    { code: 'HC01', name: '수예', en: 'Handcraft', x: 40, y: 72, color: '#CE93D8', cat: '수예' },
    { code: 'CA01', name: '캠핑', en: 'Camping', x: 54, y: 69, color: '#66BB6A', cat: '캠핑' },
    { code: 'TR01', name: '여행', en: 'Travel', x: 41, y: 86, color: '#4FC3F7', cat: '여행' },
    { code: 'GA01', name: '원예', en: 'Gardening', x: 62, y: 92, color: '#81C784', cat: '원예' },
];

// Category icon mapping (from GitHub reference page.tsx)
const CATEGORY_ICONS = {
    "뷰티/위생": "💄",
    "주방용품": "🍳",
    "청소/욕실": "🧹",
    "수납/정리": "📦",
    "문구/팬시": "✏️",
    "인테리어/원예": "🌿",
    "공구/디지털": "🔧",
    "식품": "🍪",
    "스포츠/레저/취미": "⚽",
    "패션/잡화": "👜",
    "반려동물": "🐾",
    "유아/완구": "🧸",
    "국민득템": "🏆",
    "상품권": "🎫",
    "홈패브릭": "🛋️",
    "세탁/청소": "🧼",
    "캠핑/차량관리": "🏕️",
    "여행": "✈️",
    "수예/공예": "🧶",
};

// [REMOVED] CATEGORY_FILTER_MAP is no longer used for strict 1:1 mapping.
// Buttons now match category (cat) values exactly.


async function initCategoryView() {
    const sidebar = document.getElementById('category-sidebar');
    if (!sidebar) return;

    // Attach click listeners to the hardcoded buttons
    const filterButtons = sidebar.querySelectorAll('.cat-filter-btn');
    filterButtons.forEach(btn => {
        btn.onclick = () => {
            const catName = btn.getAttribute('data-cat') || btn.innerText.trim();
            filterCategory(catName, btn);
        };
    });

    // Render both floor maps
    renderFloorMap('b1', B1_SECTIONS);
    renderFloorMap('b2', B2_SECTIONS);
}


function renderFloorMap(floorId, sections) {
    const container = document.getElementById(`map-${floorId}`);
    if (!container) return;

    const floor = floorId.toUpperCase();
    container.innerHTML = `
        <div class="category-map-wrap">
            <svg class="cat-map-svg" viewBox="0 0 863 1024">
                <!-- 배경 지도 이미지를 SVG 내부로 통합 -->
                <image href="images/map_${floorId}.png" x="0" y="0" width="863" height="1024"></image>
                
                <!-- 기존 0-100 좌표계를 863x1024 시스템으로 변환 -->
                <g transform="scale(8.63, 10.24)">
                    ${sections.map(s => renderSectionSVG(s)).join('')}
                </g>
            </svg>
        </div>
    `;
}

function renderSectionSVG(sec) {
    // Semi-transparent colored rectangle behind the text
    const w = Math.max(sec.name.length * 4.5, 14);
    const h = 8;

    // Original label group (now hidden with opacity: 0)
    const originalLabel = `
        <g class="section-label" data-cat="${sec.cat}" data-code="${sec.code}" style="opacity: 0;">
            <rect x="${sec.x - w / 2}" y="${sec.y - h / 2}" width="${w}" height="${h}" rx="1.5"
                fill="${sec.color}" fill-opacity="0.65" stroke="rgba(0,0,0,0.1)" stroke-width="0.3"/>
            <text x="${sec.x}" y="${sec.y - 0.5}" text-anchor="middle" font-size="2.8"
                font-weight="700" fill="#333" font-family="'SUIT Variable',sans-serif">${sec.code} ${sec.name}</text>
            <text x="${sec.x}" y="${sec.y + 3}" text-anchor="middle" font-size="2"
                fill="#666" font-family="'SUIT Variable',sans-serif">${sec.en}</text>
        </g>
    `;

    // New pin icon group (initially hidden)
    const pinIcon = `
        <g class="map-pin-group" data-cat="${sec.cat}" data-code="${sec.code}" 
           transform="translate(${sec.x}, ${sec.y}) scale(0.4)" style="display: none;">
            <!-- Ripple layers -->
            <circle class="pin-ripple" cx="0" cy="0" r="0" fill="none" stroke="#FF0000" stroke-width="2" />
            <circle class="pin-ripple" cx="0" cy="0" r="0" fill="none" stroke="#FF0000" stroke-width="2" />
            <circle class="pin-ripple" cx="0" cy="0" r="0" fill="none" stroke="#FF0000" stroke-width="2" />
            
            <path class="pin-path" fill="#FF0000" d="M0 -20C-3.87 -20 -7 -16.87 -7 -13c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5s-1.12 2.5-2.5 2.5z"
                  style="transform-origin: 0px 0px;"/>
        </g>
    `;

    return originalLabel + pinIcon;
}

let currentFilter = null;

function filterCategory(catName, btn) {
    // 1. Hide all pins and deactivate all buttons
    document.querySelectorAll('.map-pin-group').forEach(p => {
        p.style.display = 'none';
    });
    document.querySelectorAll('.cat-filter-btn').forEach(b => b.classList.remove('active'));

    // 2. Activate clicked button
    btn.classList.add('active');

    // 3. Show matching pins (if not "전체")
    if (catName !== '전체') {
        document.querySelectorAll('.map-pin-group').forEach(p => {
            if (p.dataset.cat === catName) { // Strict exact matching
                p.style.display = 'block';
                p.style.opacity = '1';
            }
        });
    }
}

// Entrance + self-checkout markers
const MARKERS = {
    B1: [
        { x: 36, y: 90, label: '입구', type: 'entrance' },
        { x: 48, y: 12, label: '출입구', type: 'exit' },
    ],
    B2: [
        { x: 28, y: 95, label: '입구', type: 'entrance' },
        { x: 55, y: 95, label: '본관', type: 'exit' },
    ]
};
