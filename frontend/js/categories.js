/**
 * categories.js
 * Handles the styling and interaction of the Category View (Sun-young Kiosk Style).
 */

document.addEventListener('DOMContentLoaded', () => {
    initCategoryView();
});

function initCategoryView() {
    const sidebar = document.getElementById('category-sidebar');
    if (!sidebar) return;

    // Aggregated categories from map.js GRAPH data
    // (Assuming GRAPH is global)
    if (typeof GRAPH === 'undefined') {
        console.warn('GRAPH data not found. Category view may be empty.');
        return;
    }

    const categories = [
        { name: '뷰티/화장품', floor: 'B1', section: 'b1-n02', icon: '💄' },
        { name: '식품/간식', floor: 'B1', section: 'b1-n04', icon: '🍪' },
        { name: '문구/완구', floor: 'B1', section: 'b1-n03', icon: '✏️' },
        { name: '패션/잡화', floor: 'B1', section: 'b1-n06', icon: '🧢' },
        { name: '디지털/컴퓨터', floor: 'B1', section: 'b1-n07', icon: '💻' },
        { name: '욕실/청소', floor: 'B2', section: 'b2-n04', icon: '🛁' },
        { name: '세탁/수납', floor: 'B2', section: 'b2-n08', icon: '🧺' },
        { name: '주방/식기', floor: 'B2', section: 'b2-n07', icon: '🍽️' },
        { name: '공구/자동차', floor: 'B2', section: 'b2-n14', icon: '🔧' },
        { name: '취미/반려동물', floor: 'B2', section: 'b2-n19', icon: '🐕' },
        { name: '홈패브릭', floor: 'B2', section: 'b2-n11', icon: '🧶' }
    ];

    const grid = document.createElement('div');
    grid.className = 'category-grid';

    categories.forEach(cat => {
        const btn = document.createElement('div');
        btn.className = 'category-btn';
        btn.innerHTML = `
            <div class="category-icon">${cat.icon}</div>
            <div class="category-name">${cat.name}</div>
            <div class="category-floor" style="font-size:12px;color:#999;">${cat.floor}</div>
        `;
        btn.onclick = () => selectCategory(cat);
        grid.appendChild(btn);
    });

    sidebar.innerHTML = '';
    sidebar.appendChild(grid);
}

function selectCategory(cat) {
    // 1. Scroll to/Focus the correct floor map
    const mapId = cat.floor === 'B1' ? 'map-b1' : 'map-b2';
    const floorDiv = document.getElementById(cat.floor === 'B1' ? 'floor-b1' : 'floor-b2');

    // Smooth scroll to floor
    floorDiv.scrollIntoView({ behavior: 'smooth' });

    // 2. Render Map if not already (simple version)
    // We can reuse map.js logic or just highlight the node
    // For now, let's draw the map base and a pin.

    // Check if map is rendered
    const container = document.getElementById(mapId);
    if (!container.hasChildNodes()) {
        renderStaticMap(cat.floor, container);
    }

    // 3. Highlight Node
    highlightMapNode(cat.floor, cat.section);
}

function renderStaticMap(floor, container) {
    container.innerHTML = `
        <img src="images/map_${floor.toLowerCase()}.png" style="width:100%; height:auto;" onerror="this.src='https://placehold.co/600x400?text=${floor}'">
        <div class="map-overlays" id="overlay-${floor}"></div>
    `;
    container.style.position = 'relative';
}

function highlightMapNode(floor, nodeId) {
    // Remove old highlights
    document.querySelectorAll('.map-pin-highlight').forEach(el => el.remove());

    const overlay = document.getElementById(`overlay-${floor}`);
    if (!overlay) return;

    if (typeof GRAPH === 'undefined') return;

    const node = GRAPH[floor].nodes[nodeId];
    if (node) {
        const pin = document.createElement('div');
        pin.className = 'map-pin-highlight';
        pin.style.position = 'absolute';
        pin.style.left = `${node.x}%`;
        pin.style.top = `${node.y}%`;
        pin.style.transform = 'translate(-50%, -100%)';
        pin.style.fontSize = '30px'; // Big icon
        pin.innerHTML = '📍';
        pin.style.zIndex = '100';
        pin.style.filter = 'drop-shadow(0 4px 4px rgba(0,0,0,0.3))';

        // Add animation class if needed
        pin.style.animation = 'bounce 1s infinite';

        overlay.appendChild(pin);
    }
}

// Add simple bounce animation styles purely via JS injection if not in CSS
/*
const style = document.createElement('style');
style.innerHTML = `
@keyframes bounce {
  0%, 100% { transform: translate(-50%, -100%); }
  50% { transform: translate(-50%, -120%); }
}`;
document.head.appendChild(style);
*/
