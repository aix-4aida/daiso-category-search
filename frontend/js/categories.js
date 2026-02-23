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
    { code: 'B01', name: '시즌', en: 'Season', x: 49, y: 27, color: '#FFCDD2', cat: '시즌' },
    { code: 'C01', name: '화장품', en: 'Beauty', x: 83, y: 25, color: '#F8BBD0', cat: '뷰티' },
    { code: 'D01', name: '건강기능식품', en: 'Health', x: 49, y: 37, color: '#C8E6C9', cat: '건강' },
    { code: 'E01', name: '캐릭터', en: 'Character', x: 49, y: 46, color: '#FFF9C4', cat: '캐릭터' },
    { code: 'F01', name: '패션', en: 'Fashion', x: 83, y: 46, color: '#D1C4E9', cat: '패션' },
    { code: 'A02', name: '문구', en: 'Stationery', x: 15, y: 54, color: '#BBDEFB', cat: '문구' },
    { code: 'G01', name: '파티·유아동', en: 'Party/Kids', x: 49, y: 56, color: '#FFE0B2', cat: '파티' },
    { code: 'I01', name: '포장', en: 'Packaging', x: 13, y: 71, color: '#CFD8DC', cat: '포장' },
    { code: 'J01', name: '디지털', en: 'Digital', x: 45, y: 74, color: '#B3E5FC', cat: '디지털' },
    { code: 'H01', name: '인테리어소품', en: 'Interior Prop', x: 83, y: 62, color: '#C8E6C9', cat: '인테리어' },
    { code: 'K01', name: '식품', en: 'Snacks', x: 83, y: 78, color: '#FFCCBC', cat: '식품' },
];

// B2 section data
const B2_SECTIONS = [
    { code: 'BA01', name: '욕실', en: 'Bath', x: 25, y: 18, color: '#B2EBF2', cat: '욕실' },
    { code: 'CL01', name: '청소', en: 'Cleaning', x: 47, y: 18, color: '#DCEDC8', cat: '청소' },
    { code: 'LA01', name: '세탁', en: 'Laundry', x: 72, y: 13, color: '#E1BEE7', cat: '수납정리' },
    { code: 'GP01', name: '득템', en: 'Good Place', x: 72, y: 22, color: '#FFF176', cat: '득템' },
    { code: 'JA01', name: '일본수입', en: 'Japanese', x: 25, y: 32, color: '#FFCDD2', cat: '일본수입' },
    { code: 'ST01', name: '수납', en: 'Storage', x: 72, y: 35, color: '#CFD8DC', cat: '수납정리' },
    { code: 'HF01', name: '홈패브릭', en: 'Home Fabric', x: 25, y: 48, color: '#D7CCC8', cat: '인테리어' },
    { code: 'NC01', name: '내추럴코너', en: 'Natural', x: 72, y: 48, color: '#AED581', cat: '자연' },
    { code: 'TO01', name: '공구', en: 'Tools', x: 25, y: 55, color: '#90A4AE', cat: '공구' },
    { code: 'KI01', name: '주방', en: 'Kitchen', x: 72, y: 55, color: '#FFE082', cat: '주방' },
    { code: 'SP01', name: '스포츠', en: 'Sports', x: 16, y: 72, color: '#80CBC4', cat: '스포츠' },
    { code: 'PE01', name: '반려동물', en: 'Pets', x: 28, y: 72, color: '#FFAB91', cat: '애견' },
    { code: 'HC01', name: '수예', en: 'Handcraft', x: 40, y: 72, color: '#CE93D8', cat: '수예' },
    { code: 'CA01', name: '캠핑', en: 'Camping', x: 52, y: 72, color: '#66BB6A', cat: '캠핑' },
    { code: 'TR01', name: '여행', en: 'Travel', x: 28, y: 88, color: '#4FC3F7', cat: '여행' },
    { code: 'GA01', name: '원예', en: 'Gardening', x: 52, y: 88, color: '#81C784', cat: '원예' },
];

// Category filter buttons
const CATEGORIES = [
    { name: '전체', icon: '🏬', filter: null },
    { name: '뷰티', icon: '💄', filter: ['뷰티', '화장품'] },
    { name: '주방', icon: '🍽️', filter: ['주방'] },
    { name: '욕실', icon: '🛁', filter: ['욕실', '청소'] },
    { name: '문구', icon: '✏️', filter: ['문구'] },
    { name: '수납정리', icon: '🧺', filter: ['수납정리'] },
    { name: '식품', icon: '🍪', filter: ['식품'] },
    { name: '인테리어', icon: '🏠', filter: ['인테리어'] },
    { name: '애견', icon: '🐕', filter: ['애견'] },
];

function initCategoryView() {
    const sidebar = document.getElementById('category-sidebar');
    if (!sidebar) return;

    // Render category filter buttons
    sidebar.innerHTML = CATEGORIES.map((cat, i) => `
        <button class="cat-filter-btn ${i === 0 ? 'active' : ''}" onclick="filterCategory('${cat.name}', this)">
            <span class="cat-filter-icon">${cat.icon}</span>
            <span class="cat-filter-name">${cat.name}</span>
        </button>
    `).join('');

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
            <img src="images/map_${floorId}.png" class="cat-map-img"
                 onerror="this.src='https://placehold.co/430x510?text=${floor}'">
            <svg class="cat-map-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                ${sections.map(s => renderSectionSVG(s)).join('')}
            </svg>
        </div>
    `;
}

function renderSectionSVG(sec) {
    // Semi-transparent colored rectangle behind the text
    const w = Math.max(sec.name.length * 4.5, 14);
    const h = 8;
    return `
        <g class="section-label" data-cat="${sec.cat}" data-code="${sec.code}">
            <rect x="${sec.x - w / 2}" y="${sec.y - h / 2}" width="${w}" height="${h}" rx="1.5"
                fill="${sec.color}" fill-opacity="0.65" stroke="rgba(0,0,0,0.1)" stroke-width="0.3"/>
            <text x="${sec.x}" y="${sec.y - 0.5}" text-anchor="middle" font-size="2.8"
                font-weight="700" fill="#333" font-family="'SUIT Variable',sans-serif">${sec.code} ${sec.name}</text>
            <text x="${sec.x}" y="${sec.y + 3}" text-anchor="middle" font-size="2"
                fill="#666" font-family="'SUIT Variable',sans-serif">${sec.en}</text>
        </g>
    `;
}

let currentFilter = null;

function filterCategory(catName, btn) {
    // Update active button
    document.querySelectorAll('.cat-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const cat = CATEGORIES.find(c => c.name === catName);
    currentFilter = cat?.filter || null;

    // Highlight matching sections
    document.querySelectorAll('.section-label').forEach(g => {
        const secCat = g.dataset.cat;
        if (!currentFilter) {
            // 전체: show all
            g.style.opacity = '1';
            g.querySelector('rect').setAttribute('fill-opacity', '0.65');
        } else if (currentFilter.some(f => secCat.includes(f))) {
            g.style.opacity = '1';
            g.querySelector('rect').setAttribute('fill-opacity', '0.85');
            g.querySelector('rect').setAttribute('stroke', '#E50000');
            g.querySelector('rect').setAttribute('stroke-width', '0.6');
        } else {
            g.style.opacity = '0.25';
            g.querySelector('rect').setAttribute('fill-opacity', '0.3');
            g.querySelector('rect').setAttribute('stroke', 'rgba(0,0,0,0.1)');
            g.querySelector('rect').setAttribute('stroke-width', '0.3');
        }
    });
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
