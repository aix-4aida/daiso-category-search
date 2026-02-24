/**
 * map.js
 * Waypoint-based AISLE-ONLY pathfinding & Marker labeling.
 * Updated to use new section codes (B1-A01, B2-N03, etc.)
 */

// Waypoint graph data aligned with actual floor plan coordinates
const GRAPH = {
    B1: {
        nodes: {
            // 입구 ENTRANCE ONLY — pixel(310,920) → 36%, 90%
            'b1-entrance': { x: 36, y: 90 },
            // === CORRIDOR waypoints (white walkway between sections) ===
            // Bottom horizontal corridor (포장/디지털 아래, 입구 위)
            'b1-w01': { x: 36, y: 82 },   // 입구 바로 위 복도
            'b1-w02': { x: 13, y: 82 },   // 포장 아래 복도
            'b1-w03': { x: 51, y: 82 },   // 디지털 아래 복도
            'b1-w14': { x: 70, y: 82 },   // 식품 아래 복도
            // Left vertical corridor (포장-문구 좌측)
            'b1-w04': { x: 13, y: 65 },   // 포장-문구 사이
            'b1-w05': { x: 13, y: 50 },   // 문구 위
            // Center horizontal corridors
            'b1-w06': { x: 51, y: 65 },   // 파티유아동-인테리어 사이
            'b1-w07': { x: 51, y: 50 },   // 파티유아동 위
            'b1-w08': { x: 36, y: 50 },   // 문구-캐릭터 사이
            // Center vertical corridor (시즌-건강-캐릭터 좌측)
            'b1-w09': { x: 36, y: 42 },   // 캐릭터-건강 사이
            'b1-w10': { x: 51, y: 42 },   // 캐릭터 우측
            'b1-w11': { x: 51, y: 32 },   // 건강-화장품 사이
            'b1-w12': { x: 36, y: 22 },   // 시즌 위
            'b1-w13': { x: 51, y: 22 },   // 시즌-화장품 사이
            // Right vertical corridor (화장품-패션-인테리어-식품 좌측)
            'b1-w15': { x: 70, y: 55 },   // 인테리어 위
            'b1-w16': { x: 70, y: 42 },   // 패션 앞
            'b1-w17': { x: 70, y: 22 },   // 화장품 앞
            // === Section CORRIDOR-EDGE nodes ===
            'b1-sec-season': { x: 42, y: 27 },  // 시즌
            'b1-sec-beauty': { x: 76, y: 25 },  // 화장품
            'b1-sec-health': { x: 42, y: 37 },  // 건강기능식품
            'b1-sec-character': { x: 42, y: 46 },  // 캐릭터
            'b1-sec-fashion': { x: 76, y: 46 },  // 패션
            'b1-sec-stationery': { x: 15, y: 54 },  // 문구
            'b1-sec-party': { x: 42, y: 56 },  // 파티유아동
            'b1-sec-packaging': { x: 13, y: 71 },  // 포장
            'b1-sec-digital': { x: 45, y: 74 },  // 디지털
            'b1-sec-interior': { x: 76, y: 62 },  // 인테리어
            'b1-sec-snacks': { x: 76, y: 78 },  // 식품
        },
        edges: [
            // -- Bottom corridor --
            ['b1-entrance', 'b1-w01'],
            ['b1-w01', 'b1-w02'], ['b1-w01', 'b1-w03'],
            ['b1-w03', 'b1-w14'],
            // -- Left corridor (vertical) --
            ['b1-w02', 'b1-w04'],
            ['b1-w04', 'b1-w05'],
            // -- Center horizontals --
            ['b1-w05', 'b1-w08'], ['b1-w08', 'b1-w07'],
            ['b1-w04', 'b1-w06'], ['b1-w06', 'b1-w15'],
            ['b1-w07', 'b1-w10'],
            ['b1-w03', 'b1-w06'],
            // -- Center verticals --
            ['b1-w08', 'b1-w09'],
            ['b1-w09', 'b1-w12'],
            ['b1-w10', 'b1-w11'], ['b1-w10', 'b1-w16'],
            ['b1-w11', 'b1-w13'],
            ['b1-w12', 'b1-w13'],
            ['b1-w13', 'b1-w17'],
            // -- Right corridor (vertical) --
            ['b1-w14', 'b1-w15'],
            ['b1-w15', 'b1-w16'],
            ['b1-w16', 'b1-w17'],
            // -- Section entry: corridor → section edge --
            ['b1-w12', 'b1-sec-season'], ['b1-w13', 'b1-sec-season'],
            ['b1-w17', 'b1-sec-beauty'], ['b1-w13', 'b1-sec-beauty'],
            ['b1-w09', 'b1-sec-health'], ['b1-w11', 'b1-sec-health'],
            ['b1-w08', 'b1-sec-character'], ['b1-w09', 'b1-sec-character'],
            ['b1-w16', 'b1-sec-fashion'], ['b1-w10', 'b1-sec-fashion'],
            ['b1-w05', 'b1-sec-stationery'], ['b1-w04', 'b1-sec-stationery'],
            ['b1-w07', 'b1-sec-party'], ['b1-w08', 'b1-sec-party'],
            ['b1-w02', 'b1-sec-packaging'], ['b1-w04', 'b1-sec-packaging'],
            ['b1-w01', 'b1-sec-digital'], ['b1-w03', 'b1-sec-digital'],
            ['b1-w15', 'b1-sec-interior'], ['b1-w06', 'b1-sec-interior'],
            ['b1-w14', 'b1-sec-snacks'], ['b1-w03', 'b1-sec-snacks'],
        ],
        // Section code prefix → node ID
        sectionMap: {
            'B1-A': 'b1-sec-season',
            'B1-B': 'b1-sec-beauty',
            'B1-C': 'b1-sec-health',
            'B1-D': 'b1-sec-character',
            'B1-E': 'b1-sec-fashion',
            'B1-F': 'b1-sec-stationery',
            'B1-G': 'b1-sec-party',
            'B1-H': 'b1-sec-packaging',
            'B1-I': 'b1-sec-digital',
            'B1-J': 'b1-sec-interior',
            'B1-K': 'b1-sec-snacks',
        }
    },
    B2: {
        nodes: {
            'b2-entrance': { x: 28, y: 93 },
            // Corridor waypoints
            'b2-w01': { x: 28, y: 78 },  // 여행 옆
            'b2-w02': { x: 55, y: 78 },  // 원예 옆
            'b2-w03': { x: 14, y: 58 },  // 스포츠 위
            'b2-w04': { x: 28, y: 58 },  // 반려동물 위
            'b2-w05': { x: 42, y: 58 },  // 수예 위
            'b2-w06': { x: 55, y: 58 },  // 캠핑 위
            'b2-w07': { x: 63, y: 58 },  // 캠핑-주방 사이
            'b2-w08': { x: 28, y: 48 },  // 공구 옆
            'b2-w09': { x: 55, y: 48 },  // 공구-내추럴 사이
            'b2-w10': { x: 63, y: 48 },  // 내추럴 옆
            'b2-w11': { x: 28, y: 34 },  // 일본수입 위
            'b2-w12': { x: 55, y: 34 },  // 홈패브릭-내추럴
            'b2-w13': { x: 63, y: 34 },  // 수납 옆
            'b2-w14': { x: 28, y: 22 },  // 욕실 위
            'b2-w15': { x: 55, y: 22 },  // 일본수입-수납
            'b2-w16': { x: 63, y: 22 },  // 수납 위
            'b2-w17': { x: 28, y: 10 },  // 욕실 최상단
            'b2-w18': { x: 55, y: 10 },  // 청소 위
            'b2-w19': { x: 72, y: 10 },  // 세탁 옆
            'b2-w20': { x: 85, y: 10 },  // 득템
            'b2-w21': { x: 63, y: 78 },  // 주방 아래
            'b2-w22': { x: 63, y: 16 },  // 득템 옆
            // Section center nodes
            'b2-sec-bath': { x: 38, y: 14 },
            'b2-sec-cleaning': { x: 58, y: 14 },
            'b2-sec-laundry': { x: 78, y: 12 },
            'b2-sec-goodplace': { x: 82, y: 20 },
            'b2-sec-japanese': { x: 42, y: 28 },
            'b2-sec-storage': { x: 75, y: 28 },
            'b2-sec-fabric': { x: 42, y: 40 },
            'b2-sec-natural': { x: 75, y: 42 },
            'b2-sec-tools': { x: 42, y: 53 },
            'b2-sec-sports': { x: 10, y: 67 },
            'b2-sec-pets': { x: 26, y: 67 },
            'b2-sec-handcraft': { x: 40, y: 67 },
            'b2-sec-camping': { x: 55, y: 67 },
            'b2-sec-kitchen': { x: 77, y: 67 },
            'b2-sec-travel': { x: 28, y: 85 },
            'b2-sec-gardening': { x: 52, y: 85 },
        },
        edges: [
            ['b2-entrance', 'b2-w01'],
            ['b2-w01', 'b2-w02'], ['b2-w01', 'b2-w04'],
            ['b2-w02', 'b2-w06'], ['b2-w02', 'b2-w21'],
            ['b2-w03', 'b2-w04'],
            ['b2-w04', 'b2-w05'], ['b2-w04', 'b2-w08'],
            ['b2-w05', 'b2-w06'],
            ['b2-w06', 'b2-w07'],
            ['b2-w07', 'b2-w21'], ['b2-w07', 'b2-w10'],
            ['b2-w08', 'b2-w09'], ['b2-w08', 'b2-w11'],
            ['b2-w09', 'b2-w10'],
            ['b2-w10', 'b2-w13'], ['b2-w10', 'b2-w21'],
            ['b2-w11', 'b2-w12'], ['b2-w11', 'b2-w14'],
            ['b2-w12', 'b2-w13'],
            ['b2-w13', 'b2-w16'], ['b2-w13', 'b2-w22'],
            ['b2-w14', 'b2-w15'], ['b2-w14', 'b2-w17'],
            ['b2-w15', 'b2-w16'],
            ['b2-w16', 'b2-w22'],
            ['b2-w17', 'b2-w18'],
            ['b2-w18', 'b2-w19'],
            ['b2-w19', 'b2-w20'],
            ['b2-w20', 'b2-w22'],
            ['b2-w21', 'b2-w22'],
            // Section entry connections
            ['b2-w14', 'b2-sec-bath'], ['b2-w17', 'b2-sec-bath'],
            ['b2-w15', 'b2-sec-cleaning'], ['b2-w18', 'b2-sec-cleaning'],
            ['b2-w19', 'b2-sec-laundry'], ['b2-w20', 'b2-sec-laundry'],
            ['b2-w20', 'b2-sec-goodplace'], ['b2-w22', 'b2-sec-goodplace'],
            ['b2-w11', 'b2-sec-japanese'], ['b2-w14', 'b2-sec-japanese'],
            ['b2-w13', 'b2-sec-storage'], ['b2-w16', 'b2-sec-storage'],
            ['b2-w11', 'b2-sec-fabric'], ['b2-w12', 'b2-sec-fabric'], ['b2-w08', 'b2-sec-fabric'],
            ['b2-w10', 'b2-sec-natural'], ['b2-w13', 'b2-sec-natural'], ['b2-w12', 'b2-sec-natural'],
            ['b2-w08', 'b2-sec-tools'], ['b2-w09', 'b2-sec-tools'],
            ['b2-w03', 'b2-sec-sports'], ['b2-w04', 'b2-sec-sports'],
            ['b2-w04', 'b2-sec-pets'], ['b2-w03', 'b2-sec-pets'],
            ['b2-w05', 'b2-sec-handcraft'], ['b2-w04', 'b2-sec-handcraft'],
            ['b2-w06', 'b2-sec-camping'], ['b2-w05', 'b2-sec-camping'],
            ['b2-w07', 'b2-sec-kitchen'], ['b2-w21', 'b2-sec-kitchen'], ['b2-w10', 'b2-sec-kitchen'],
            ['b2-w01', 'b2-sec-travel'], ['b2-w02', 'b2-sec-travel'],
            ['b2-w02', 'b2-sec-gardening'], ['b2-w01', 'b2-sec-gardening'],
        ],
        sectionMap: {
            'B2-A': 'b2-sec-bath',
            'B2-B': 'b2-sec-cleaning',
            'B2-C': 'b2-sec-laundry',
            'B2-D': 'b2-sec-goodplace',
            'B2-E': 'b2-sec-japanese',
            'B2-F': 'b2-sec-storage',
            'B2-G': 'b2-sec-fabric',
            'B2-H': 'b2-sec-natural',
            'B2-I': 'b2-sec-tools',
            'B2-J': 'b2-sec-sports',
            'B2-K': 'b2-sec-pets',
            'B2-L': 'b2-sec-handcraft',
            'B2-M': 'b2-sec-camping',
            'B2-N': 'b2-sec-kitchen',
            'B2-O': 'b2-sec-travel',
            'B2-P': 'b2-sec-gardening',
        }
    }
};

// BFS shortest path
function buildAdjList(floorData) {
    const adj = {};
    Object.keys(floorData.nodes).forEach(n => adj[n] = []);
    floorData.edges.forEach(([a, b]) => {
        if (!floorData.nodes[a] || !floorData.nodes[b]) return;
        adj[a].push(b);
        adj[b].push(a);
    });
    return adj;
}

function bfs(adj, start, end) {
    if (!start || !end || start === end) return [start];
    const queue = [[start]];
    const visited = new Set([start]);
    while (queue.length > 0) {
        const path = queue.shift();
        const node = path[path.length - 1];
        if (node === end) return path;
        for (const neighbor of (adj[node] || [])) {
            if (!visited.has(neighbor)) {
                visited.add(neighbor);
                queue.push([...path, neighbor]);
            }
        }
    }
    return [];
}

// Get target node from product's section code
function getArrivalNodeId(floor, product) {
    const data = GRAPH[floor];
    if (!data) return `${floor.toLowerCase()}-entrance`;

    // Use the new section code (e.g. "B1-B03")
    const section = (product.location?.section || "").toUpperCase();

    if (section && section.length >= 4) {
        // Extract prefix: "B1-B03" → "B1-B"
        const prefix = section.substring(0, 4);
        const nodeId = data.sectionMap[prefix];
        if (nodeId) {
            console.log(`[Map] Section ${section} → prefix ${prefix} → node ${nodeId}`);
            return nodeId;
        }
    }

    // Fallback: try category-based mapping
    const major = product.meta?.category_major || "";
    const categoryFallback = {
        '시즌/시리즈': 'b1-sec-season', '뷰티/위생': 'b1-sec-beauty',
        '문구/팬시': 'b1-sec-stationery', '식품': 'b1-sec-snacks',
        '패션/잡화': 'b1-sec-fashion', '공구/디지털': 'b1-sec-digital',
        '유아/완구': 'b1-sec-party',
        '청소/욕실': 'b2-sec-bath', '주방용품': 'b2-sec-kitchen',
        '반려동물': 'b2-sec-pets', '수납/정리': 'b2-sec-storage',
        '스포츠/레저/취미': 'b2-sec-sports', '인테리어/원예': 'b2-sec-natural',
        '국민득템': 'b2-sec-goodplace',
    };
    const fallbackNode = categoryFallback[major];
    if (fallbackNode && data.nodes[fallbackNode]) {
        console.log(`[Map] Fallback: ${major} → ${fallbackNode}`);
        return fallbackNode;
    }

    console.warn(`[Map] No mapping for section=${section}, major=${major}. Defaulting to entrance.`);
    return `${floor.toLowerCase()}-entrance`;
}

// Render Map & Path
function renderResultMap(product) {
    const panel = document.getElementById('map-panel');
    const floor = (product.location?.floor || "B1").toUpperCase();
    const floorData = GRAPH[floor];

    if (!floorData) {
        panel.innerHTML = `<div class="no-results">지도 데이터를 불러올 수 없습니다. (${floor})</div>`;
        return;
    }

    const startNodeId = `${floor.toLowerCase()}-entrance`;
    const endNodeId = getArrivalNodeId(floor, product);

    const adj = buildAdjList(floorData);
    const path = bfs(adj, startNodeId, endNodeId);

    const isPathFound = path.length > 1;
    const distance = isPathFound ? (path.length - 1) * 3 : 0;
    const distanceText = isPathFound ? `약 <strong>${distance}m</strong>` : "경로 탐색 불가";
    const sectionLabel = product.location?.shelf_label || product.meta?.category_major || "";

    panel.innerHTML = `
        <div class="result-map-wrapper">
            <div class="result-map-header">
                <div class="floor-title-large">${floor}</div>
            </div>
            
            <div class="map-legend-overlay">
                <div class="legend-item"><span class="dot red"></span> 추천 경로</div>
                <div class="legend-item"><span class="dot red" style="opacity:0.5"></span> 상품 위치</div>
            </div>

            <div class="map-image-container">
                <img src="images/map_${floor.toLowerCase()}.png" class="map-base-img" onerror="this.src='https://placehold.co/600x400?text=Map+${floor}'">
                <svg class="map-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
                    ${isPathFound ? drawRouteSVG(floor, path) : ''}
                    ${renderMarkerSVG(floor, startNodeId, endNodeId, product.name, sectionLabel)}
                </svg>
            </div>
            <div class="map-footer" style="margin-top:12px; font-size:14px; color:#666; text-align:center;">
                현재 위치: <strong>정문 입구</strong> &nbsp; | &nbsp; 이동 거리: ${distanceText}
            </div>
        </div>
    `;
}

function drawRouteSVG(floor, path) {
    const floorData = GRAPH[floor];
    let points = "";
    path.forEach(id => {
        const n = floorData.nodes[id];
        if (n) points += `${n.x},${n.y} `;
    });

    return `
    <polyline points="${points.trim()}" 
        fill="none" 
        stroke="#2962FF" 
        stroke-width="2" 
        stroke-dasharray="4,3" 
        stroke-linecap="round" 
        stroke-linejoin="round"
        opacity="0.85">
        <animate attributeName="stroke-dashoffset" from="14" to="0" dur="1s" repeatCount="indefinite" />
    </polyline>
    `;
}

function renderMarkerSVG(floor, startNodeId, targetNodeId, productName, sectionLabel) {
    const floorData = GRAPH[floor];
    const target = floorData.nodes[targetNodeId];
    const start = floorData.nodes[startNodeId];

    if (!target || !start) return "";

    const displayTitle = (sectionLabel || productName || "").length > 10
        ? (sectionLabel || productName).substring(0, 10) + "..."
        : (sectionLabel || productName);

    return `
        <!-- Start Marker (Current Position) -->
        <g class="start-marker">
            <circle cx="${start.x}" cy="${start.y}" r="2.5" fill="#2962FF" stroke="white" stroke-width="0.8" />
            <circle cx="${start.x}" cy="${start.y}" r="5" fill="#2962FF" fill-opacity="0.15">
                <animate attributeName="r" from="3" to="7" dur="2s" repeatCount="indefinite" />
                <animate attributeName="fill-opacity" from="0.4" to="0" dur="2s" repeatCount="indefinite" />
            </circle>
            <rect x="${start.x - 10}" y="${start.y - 12}" width="20" height="6" rx="2" fill="white" stroke="#2962FF" stroke-width="0.4" filter="drop-shadow(0px 1px 2px rgba(0,0,0,0.15))"/>
            <text x="${start.x}" y="${start.y - 7.5}" font-size="3.2" text-anchor="middle" fill="#2962FF" font-weight="bold" font-family="'Noto Sans KR', sans-serif">현재 위치</text>
        </g>

        <!-- Target Marker (Product Location) -->
        <g class="target-marker">
            <!-- Soft pulse ring -->
            <circle cx="${target.x}" cy="${target.y}" r="4" fill="#E50000" fill-opacity="0.12">
                <animate attributeName="r" from="4" to="10" dur="1.8s" repeatCount="indefinite" />
                <animate attributeName="fill-opacity" from="0.2" to="0" dur="1.8s" repeatCount="indefinite" />
            </circle>
            <!-- Clean circular marker -->
            <circle cx="${target.x}" cy="${target.y}" r="4" fill="#E50000" stroke="white" stroke-width="1.2" filter="drop-shadow(0px 1px 3px rgba(229,0,0,0.4))" />
            <circle cx="${target.x}" cy="${target.y}" r="1.5" fill="white" />
            <!-- Label badge -->
            <rect x="${target.x - 15}" y="${target.y - 12}" width="30" height="6" rx="3" fill="#E50000" filter="drop-shadow(0px 1px 2px rgba(0,0,0,0.2))"/>
            <text x="${target.x}" y="${target.y - 8}" font-size="3" text-anchor="middle" fill="white" font-weight="bold" font-family="'Noto Sans KR', sans-serif">${displayTitle}</text>
        </g>
    `;
}
