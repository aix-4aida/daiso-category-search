/**
 * 어디다있소 - Map Rendering (map.js)
 * Renders B1/B2 floor maps with category highlighting and route display
 */

// ── Floor Layout Data ──
const FLOOR_B1 = [
    { id: 'B01', name: '시즌', en: 'Season', row: 1, col: 1 },
    { id: 'C01', name: '화장품', en: 'Beauty', row: 1, col: 2 },
    { id: 'D01', name: '건강기능식품', en: 'Health', row: 1, col: 3 },
    { id: 'E01', name: '캐릭터', en: 'Character', row: 2, col: 2 },
    { id: 'F01', name: '패션', en: 'Fashion', row: 2, col: 3 },
    { id: 'G01', name: '파티·유아동', en: 'Party/Kids', row: 2, col: 4 },
    { id: 'H01', name: '인테리어소품', en: 'Interior', row: 3, col: 2 },
    { id: 'I01', name: '포장', en: 'Packaging', row: 3, col: 1 },
    { id: 'J01', name: '디지털', en: 'Digital', row: 4, col: 1 },
    { id: 'K01', name: '식품', en: 'Snacks', row: 4, col: 2 },
    { id: 'ENTRANCE', name: '출입구', en: 'Entrance', row: 4, col: 3, special: true },
    { id: 'CHECKOUT', name: '계산대', en: 'Self-Checkout', row: 1, col: 4, special: true }
];

const FLOOR_B2 = [
    { id: 'BA01', name: '욕실', en: 'Bath', row: 1, col: 1 },
    { id: 'CL01', name: '청소', en: 'Cleaning', row: 1, col: 2 },
    { id: 'LA01', name: '세탁', en: 'Laundry', row: 1, col: 3 },
    { id: 'GP01', name: '득템', en: 'Good Place', row: 1, col: 4 },
    { id: 'JA01', name: '일본수입', en: 'Japanese', row: 2, col: 1 },
    { id: 'HF01', name: '홈패브릭', en: 'Home Fabric', row: 2, col: 2 },
    { id: 'ST01', name: '수납정리', en: 'Storage', row: 2, col: 3 },
    { id: 'NC01', name: '내추럴코너', en: 'Natural', row: 2, col: 4 },
    { id: 'TO01', name: '공구', en: 'Tools', row: 3, col: 1 },
    { id: 'SP01', name: '스포츠', en: 'Sports', row: 3, col: 2 },
    { id: 'HC01', name: '수예', en: 'Handcraft', row: 3, col: 3 },
    { id: 'CA01', name: '캠핑', en: 'Camping', row: 3, col: 4 },
    { id: 'K01', name: '주방', en: 'Kitchen', row: 4, col: 4 },
    { id: 'TR01', name: '여행', en: 'Travel', row: 4, col: 1 },
    { id: 'GA01', name: '원예', en: 'Gardening', row: 4, col: 2 },
    { id: 'A02', name: '문구', en: 'Stationery', row: 4, col: 3 }
];

// ── Category Definitions ──
const CATEGORIES = [
    { name: '전체', icon: '전', filter: null },
    { name: '뷰티', icon: '뷰', filter: ['C01'] },
    { name: '주방', icon: '주', filter: ['K01'] },
    { name: '욕실', icon: '욕', filter: ['BA01'] },
    { name: '문구', icon: '문', filter: ['A02'] },
    { name: '수납정리', icon: '수', filter: ['ST01'] },
    { name: '식품', icon: '식', filter: ['K01'] },
    { name: '인테리어', icon: '인', filter: ['H01', 'HF01'] },
    { name: '애견', icon: '펫', filter: ['SP01'] }
];

let activeCategory = '전체';

// ── Render Category Map ──
function renderCategoryMap() {
    renderFloorGrid('map-b1', FLOOR_B1);
    renderFloorGrid('map-b2', FLOOR_B2);
    renderCategorySidebar();
}

function renderFloorGrid(containerId, floorData) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    // Create 4x4 grid
    for (let row = 1; row <= 4; row++) {
        for (let col = 1; col <= 4; col++) {
            const cell = floorData.find(c => c.row === row && c.col === col);

            const div = document.createElement('div');
            div.className = 'map-cell';

            if (cell) {
                const isHighlighted = activeCategory === '전체' ||
                    (CATEGORIES.find(c => c.name === activeCategory)?.filter || []).includes(cell.id);

                if (isHighlighted && activeCategory !== '전체') {
                    div.classList.add('highlight');
                }

                if (cell.special) {
                    div.style.background = '#f0f0f0';
                    div.style.fontWeight = '700';
                }

                div.innerHTML = `
          <span class="cell-id">${cell.id}</span>
          <span class="cell-name">${cell.name}</span>
          <span style="font-size:9px;color:#999;">${cell.en}</span>
        `;
            }

            container.appendChild(div);
        }
    }
}

function renderCategorySidebar() {
    const sidebar = document.getElementById('category-sidebar');
    if (!sidebar) return;

    sidebar.innerHTML = '';

    CATEGORIES.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = `category-btn ${cat.name === activeCategory ? 'active' : ''}`;
        btn.onclick = () => {
            activeCategory = cat.name;
            renderCategoryMap();
        };
        btn.innerHTML = `<span class="cat-icon">${cat.icon}</span> ${cat.name}`;
        sidebar.appendChild(btn);
    });
}

// ── Render Result Map (with route) ──
function renderResultMap(result) {
    const panel = document.getElementById('map-panel');
    if (!panel) return;

    // Determine which floor
    const floor = result.floor || 'B1';
    const floorData = floor === 'B2' ? FLOOR_B2 : FLOOR_B1;
    const targetId = result.location?.split('-')[1] || result.location;

    panel.innerHTML = `
    <div style="width:100%;max-width:600px;padding:20px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2 style="font-size:48px;font-weight:800;color:#E50000;opacity:0.3;">${floor}</h2>
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="display:inline-flex;align-items:center;gap:4px;">
            <span style="width:12px;height:12px;background:#2962FF;border-radius:50%;display:inline-block;"></span>
            <span style="font-size:12px;color:#888;">현재위치</span>
          </span>
          <span style="display:inline-flex;align-items:center;gap:4px;">
            <span style="width:12px;height:12px;background:#E50000;border-radius:50%;display:inline-block;"></span>
            <span style="font-size:12px;color:#888;">상품위치</span>
          </span>
        </div>
      </div>
      <div class="map-grid" id="result-map-grid"></div>
    </div>
  `;

    const grid = document.getElementById('result-map-grid');

    for (let row = 1; row <= 4; row++) {
        for (let col = 1; col <= 4; col++) {
            const cell = floorData.find(c => c.row === row && c.col === col);

            const div = document.createElement('div');
            div.className = 'map-cell';

            if (cell) {
                const isTarget = cell.id === targetId;
                const isEntrance = cell.id === 'ENTRANCE';

                if (isTarget) {
                    div.classList.add('highlight');
                    div.innerHTML = `
            <div class="pin"></div>
            <span class="cell-id">${cell.id}</span>
            <span class="cell-name" style="color:#E50000;font-weight:700;">${cell.name}</span>
          `;
                } else if (isEntrance) {
                    div.style.background = '#e3f2fd';
                    div.innerHTML = `
            <span style="width:12px;height:12px;background:#2962FF;border-radius:50%;display:inline-block;margin-bottom:4px;"></span>
            <span class="cell-name">${cell.name}</span>
          `;
                } else {
                    div.innerHTML = `
            <span class="cell-id">${cell.id}</span>
            <span class="cell-name">${cell.name}</span>
          `;
                }
            }

            grid.appendChild(div);
        }
    }
}
