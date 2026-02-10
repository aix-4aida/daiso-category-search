/**
 * 어디다있소 - Map Rendering (map.js)
 * Renders Image-based B1/B2 floor maps with coordinate pins
 */

// ── Floor & Shelf Coordinate Data ──
const MAP_DATA = {
    floors: {
        "B1": { map: "images/map_b1.png", label: "B1 Floor (Main)" },
        "B2": { map: "images/map_b2.png", label: "B2 Floor (Sub)" }
    },
    shelves: {
        // B1 Shelves
        "A01": { floor: "B1", x: 20, y: 72, name: "문구" },
        "A02": { floor: "B1", x: 20, y: 80, name: "문구" },
        "B01": { floor: "B1", x: 60, y: 35, name: "시즌" },
        "D01": { floor: "B1", x: 60, y: 50, name: "건강" },
        "E01": { floor: "B1", x: 60, y: 60, name: "캐릭터" },
        "G01": { floor: "B1", x: 60, y: 75, name: "파티/유아동" },
        "C01": { floor: "B1", x: 80, y: 30, name: "화장품" },
        "F01": { floor: "B1", x: 80, y: 60, name: "패션" },
        "H01": { floor: "B1", x: 80, y: 75, name: "인테리어" },
        "K01": { floor: "B1", x: 85, y: 85, name: "식품" },
        "I01": { floor: "B1", x: 15, y: 85, name: "포장" },
        "J01": { floor: "B1", x: 50, y: 85, name: "디지털" },
        // B2 Shelves
        "BA01": { floor: "B2", x: 55, y: 20, name: "욕실" },
        "JA01": { floor: "B2", x: 55, y: 35, name: "일본수입" },
        "HF01": { floor: "B2", x: 55, y: 45, name: "홈패브릭" },
        "TO01": { floor: "B2", x: 55, y: 55, name: "공구" },
        "CL01": { floor: "B2", x: 70, y: 20, name: "청소" },
        "LA01": { floor: "B2", x: 90, y: 15, name: "세탁" },
        "GP01": { floor: "B2", x: 92, y: 25, name: "득템" },
        "ST01": { floor: "B2", x: 85, y: 40, name: "수납" },
        "NC01": { floor: "B2", x: 85, y: 55, name: "내추럴" },
        "SP01": { floor: "B2", x: 15, y: 72, name: "스포츠" },
        "KI01": { floor: "B2", x: 80, y: 60, name: "주방" },
        "PE01": { floor: "B2", x: 30, y: 70, name: "반려동물" },
        "HC01": { floor: "B2", x: 45, y: 70, name: "수예" },
        "CA01": { floor: "B2", x: 60, y: 70, name: "캠핑" },
        "TR01": { floor: "B2", x: 40, y: 85, name: "여행" },
        "GA01": { floor: "B2", x: 65, y: 85, name: "원예" }
    },
    entrances: {
        "B1": { x: 50, y: 15 },
        "B2": { x: 25, y: 90 }
    }
};

const CATEGORIES = [
    { name: '전체', icon: '전', filter: null },
    { name: '뷰티', icon: '뷰', filter: ['C01'] },
    { name: '주방', icon: '주', filter: ['KI01'] },
    { name: '욕실', icon: '욕', filter: ['BA01'] },
    { name: '문구', icon: '문', filter: ['A01', 'A02'] },
    { name: '수납정리', icon: '수', filter: ['ST01'] },
    { name: '식품', icon: '식', filter: ['K01'] },
    { name: '인테리어', icon: '인', filter: ['H01', 'HF01'] },
    { name: '애견', icon: '펫', filter: ['PE01'] }
];

let activeCategory = '전체';

// ── Main Render Entry ──
function renderCategoryMap() {
    renderFloorImage('map-b1', 'B1');
    renderFloorImage('map-b2', 'B2');
    renderCategorySidebar();
}

/**
 * Renders floor image and overlays markers
 */
function renderFloorImage(containerId, floorKey) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const floor = MAP_DATA.floors[floorKey];
    const entrance = MAP_DATA.entrances[floorKey];

    // Clear previous
    container.innerHTML = '';
    container.className = 'map-image-container'; // Specialized CSS class

    // Create Map Image
    const mapImg = document.createElement('img');
    mapImg.src = floor.map;
    mapImg.className = 'map-base-img';
    container.appendChild(mapImg);

    // Filtered Shelves
    const categoryFilter = CATEGORIES.find(c => c.name === activeCategory)?.filter;

    Object.entries(MAP_DATA.shelves).forEach(([id, shelf]) => {
        if (shelf.floor !== floorKey) return;

        const isHighlighted = activeCategory === '전체' || (categoryFilter && categoryFilter.includes(id));

        const pin = document.createElement('div');
        pin.className = `map-pin ${isHighlighted ? 'active' : 'dimmed'}`;
        pin.style.left = `${shelf.x}%`;
        pin.style.top = `${shelf.y}%`;
        pin.innerHTML = `<span class="pin-label">${shelf.name}</span>`;
        container.appendChild(pin);
    });

    // Entrance
    if (entrance) {
        const entPin = document.createElement('div');
        entPin.className = 'map-pin entrance';
        entPin.style.left = `${entrance.x}%`;
        entPin.style.top = `${entrance.y}%`;
        entPin.innerHTML = `<span class="pin-label">입구</span>`;
        container.appendChild(entPin);
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

/**
 * Renders the result map (found product)
 */
function renderResultMap(result) {
    const panel = document.getElementById('map-panel');
    if (!panel) return;

    const floor = result.floor || 'B1';
    const targetId = result.id?.split('-')[1] || result.id; // Support 'B1-A01' format
    const shelf = MAP_DATA.shelves[targetId] || MAP_DATA.shelves[result.id] || null;

    panel.innerHTML = `
    <div class="result-map-wrapper">
      <div class="result-map-header">
        <h2 class="floor-title-large">${floor}</h2>
        <div class="map-legend">
          <span class="legend-item"><span class="dot blue"></span> 현재위치</span>
          <span class="legend-item"><span class="dot red"></span> 상품위치</span>
        </div>
      </div>
      <div class="map-image-container highlight-view" id="result-map-container"></div>
    </div>
  `;

    const container = document.getElementById('result-map-container');
    const floorInfo = MAP_DATA.floors[floor];

    // Base Image
    const img = document.createElement('img');
    img.src = floorInfo.map;
    img.className = 'map-base-img';
    container.appendChild(img);

    // All Shelves (Dimmed)
    Object.entries(MAP_DATA.shelves).forEach(([id, s]) => {
        if (s.floor !== floor) return;
        const pin = document.createElement('div');
        pin.className = 'map-pin dimmed';
        pin.style.left = `${s.x}%`;
        pin.style.top = `${s.y}%`;
        container.appendChild(pin);
    });

    // Target Pin (Highlighted)
    if (shelf) {
        const pin = document.createElement('div');
        pin.className = 'map-pin target-pin active pulse';
        pin.style.left = `${shelf.x}%`;
        pin.style.top = `${shelf.y}%`;
        pin.innerHTML = `
            <div class="target-marker"></div>
            <div class="pin-popup">${result.product || shelf.name}</div>
        `;
        container.appendChild(pin);
    }

    // Entrance (Current Position Marker)
    const entrance = MAP_DATA.entrances[floor];
    if (entrance) {
        const curPin = document.createElement('div');
        curPin.className = 'map-pin current-position';
        curPin.style.left = `${entrance.x}%`;
        curPin.style.top = `${entrance.y}%`;
        container.appendChild(curPin);
    }
}
