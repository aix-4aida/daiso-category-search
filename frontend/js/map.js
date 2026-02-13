/**
 * map.js
 * Waypoint-based AISLE-ONLY pathfinding & Marker labeling.
 */

// Step 1: Waypoint graph data (Provided by user)
// Step 1: Waypoint graph data (Synced with map-pathfinding.md)
const GRAPH = {
    B1: {
        nodes: {
            'b1-entrance': { x: 50, y: 95 },
            'b1-n01': { x: 50, y: 82 },
            'b1-n02': { x: 22, y: 78 },
            'b1-n03': { x: 78, y: 78 },
            'b1-n04': { x: 10, y: 60 },
            'b1-n05': { x: 35, y: 60 },
            'b1-n06': { x: 65, y: 60 },
            'b1-n07': { x: 90, y: 60 },
            'b1-n08': { x: 20, y: 35 },
            'b1-n09': { x: 50, y: 35 },
            'b1-n10': { x: 80, y: 35 },
            'b1-n11': { x: 50, y: 10 }
        },
        edges: [
            ['b1-entrance', 'b1-n01'],
            ['b1-n01', 'b1-n02'], ['b1-n01', 'b1-n03'], ['b1-n01', 'b1-n05'],
            ['b1-n02', 'b1-n04'], ['b1-n02', 'b1-n05'],
            ['b1-n03', 'b1-n06'], ['b1-n03', 'b1-n07'],
            ['b1-n04', 'b1-n05'], ['b1-n04', 'b1-n08'],
            ['b1-n05', 'b1-n06'], ['b1-n05', 'b1-n09'],
            ['b1-n06', 'b1-n07'], ['b1-n06', 'b1-n09'],
            ['b1-n07', 'b1-n10'],
            ['b1-n08', 'b1-n09'], ['b1-n08', 'b1-n11'],
            ['b1-n09', 'b1-n10'], ['b1-n09', 'b1-n11'],
            ['b1-n10', 'b1-n11']
        ],
        categoryMap: {
            // Priority 1: Category Middle (Specific)
            '메이크업': 'b1-n02', '스킨케어': 'b1-n02', '남성케어': 'b1-n02', '헤어케어': 'b1-n02',
            '위생용품': 'b1-n08', '구강케어': 'b1-n08', '의약외품': 'b1-n08',
            '과자': 'b1-n04', '간식': 'b1-n04', '식품': 'b1-n04', '가공식품': 'b1-n04',
            '필기구': 'b1-n03', '노트': 'b1-n03', '사무용품': 'b1-n03', '미술용품': 'b1-n03',
            '파티용품': 'b1-n10', '포장용품': 'b1-n03',
            '휴대폰용품': 'b1-n07', '컴퓨터용품': 'b1-n07', '디지털': 'b1-n07',
            '양말': 'b1-n05', '속옷': 'b1-n05', '의류': 'b1-n06', '모자': 'b1-n06',
            '방향제': 'b1-n06', '인테리어소품': 'b1-n06',

            // Priority 2: Category Major (Broad)
            '뷰티': 'b1-n02', '화장품': 'b1-n02',
            '건강': 'b1-n08', '의료': 'b1-n08',
            '식품': 'b1-n04',
            '문구': 'b1-n03', '팬시': 'b1-n03', '완구': 'b1-n03',
            '전자': 'b1-n07',
            '패션': 'b1-n06', '잡화': 'b1-n06',
            '인테리어': 'b1-n06',
            '시즌': 'b1-n10',

            // Manual/Fallback
            '청소': 'b1-n05', '세탁': 'b1-n05', '욕실': 'b1-n05',
            '위생': 'b1-n08',
            '기타': 'b1-n01'
        }
    },
    B2: {
        nodes: {
            'b2-entrance': { x: 50, y: 95 },
            'b2-n01': { x: 50, y: 85 },
            'b2-n02': { x: 25, y: 85 },
            'b2-n03': { x: 75, y: 85 },
            'b2-n04': { x: 10, y: 80 },
            'b2-n05': { x: 25, y: 70 },
            'b2-n06': { x: 50, y: 70 },
            'b2-n07': { x: 75, y: 70 },
            'b2-n08': { x: 15, y: 58 },
            'b2-n09': { x: 35, y: 55 },
            'b2-n10': { x: 50, y: 55 },
            'b2-n11': { x: 65, y: 55 },
            'b2-n12': { x: 88, y: 55 },
            'b2-n13': { x: 15, y: 40 },
            'b2-n14': { x: 35, y: 38 },
            'b2-n15': { x: 50, y: 38 },
            'b2-n16': { x: 65, y: 38 },
            'b2-n17': { x: 85, y: 38 },
            'b2-n18': { x: 20, y: 20 },
            'b2-n19': { x: 50, y: 20 },
            'b2-n20': { x: 78, y: 20 },
            'b2-n21': { x: 50, y: 8 }
        },
        edges: [
            ['b2-entrance', 'b2-n01'],
            ['b2-n01', 'b2-n02'], ['b2-n01', 'b2-n03'], ['b2-n01', 'b2-n06'],
            ['b2-n02', 'b2-n04'], ['b2-n02', 'b2-n05'],
            ['b2-n03', 'b2-n07'],
            ['b2-n04', 'b2-n08'],
            ['b2-n05', 'b2-n06'], ['b2-n05', 'b2-n08'], ['b2-n05', 'b2-n09'],
            ['b2-n06', 'b2-n07'], ['b2-n06', 'b2-n10'],
            ['b2-n07', 'b2-n11'], ['b2-n07', 'b2-n12'],
            ['b2-n08', 'b2-n09'], ['b2-n08', 'b2-n13'],
            ['b2-n09', 'b2-n10'], ['b2-n09', 'b2-n14'],
            ['b2-n10', 'b2-n11'], ['b2-n10', 'b2-n15'],
            ['b2-n11', 'b2-n12'], ['b2-n11', 'b2-n16'],
            ['b2-n12', 'b2-n17'],
            ['b2-n13', 'b2-n14'], ['b2-n13', 'b2-n18'],
            ['b2-n14', 'b2-n15'], ['b2-n14', 'b2-n18'],
            ['b2-n15', 'b2-n16'], ['b2-n15', 'b2-n19'],
            ['b2-n16', 'b2-n17'], ['b2-n16', 'b2-n20'],
            ['b2-n17', 'b2-n20'],
            ['b2-n18', 'b2-n19'], ['b2-n18', 'b2-n21'],
            ['b2-n19', 'b2-n20'], ['b2-n19', 'b2-n21'],
            ['b2-n20', 'b2-n21']
        ],
        categoryMap: {
            '욕실용품': 'b2-n04', '청소용품': 'b2-n05', '세탁용품': 'b2-n08',
            '주방용품': 'b2-n07', '조리도구': 'b2-n07', '식기': 'b2-n07',
            '밀폐용기': 'b2-n07', '수납용품': 'b2-n11',
            '홈패브릭': 'b2-n11', '커튼': 'b2-n11', '침구': 'b2-n11',
            '공구': 'b2-n14', '자동차용품': 'b2-n12', '자전거용품': 'b2-n12',
            '캠핑용품': 'b2-n12', '여행용품': 'b2-n20',
            '원예용품': 'b2-n18', '반려동물용품': 'b2-n19', '애완용품': 'b2-n19',
            '수예': 'b2-n16', '취미': 'b2-n14',

            // Major and Fallback
            '욕실': 'b2-n04', '청소': 'b2-n05', '세탁': 'b2-n08',
            '주방': 'b2-n07', '수납': 'b2-n11',
            '공구': 'b2-n14', '자동차': 'b2-n12', '캠핑': 'b2-n12',
            '원예': 'b2-n18', '반려동물': 'b2-n19', '취미': 'b2-n14'
        }
    }
};

// Step 2: BFS implementation
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
    if (!start || !end) return [];
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
    // Return empty if no path found (prevents straight line)
    return [];
}

// Step 3: Determine arrival node (Category Priority)
function getArrivalNodeId(floor, product) {
    const data = GRAPH[floor];
    if (!data) return `${floor.toLowerCase()}-entrance`; // Fail-safe

    const major = product.meta?.category_major || "";
    const middle = product.meta?.category_middle || "";

    // 1. Try Category Middle (Best match)
    const middleNode = data.categoryMap[middle];
    if (middleNode) {
        console.log(`[Map] Mapped Middle Check: ${middle} -> ${middleNode}`);
        return middleNode;
    }

    // 2. Try Category Major (Fallback 1)
    const majorNode = data.categoryMap[major];
    if (majorNode) {
        console.log(`[Map] Mapped Major Check: ${major} -> ${majorNode}`);
        return majorNode;
    }

    // 3. Fallback to N01 (Fallback 2)
    console.warn(`[Map] No mapping for [${middle} / ${major}]. Defaulting to N01.`);
    return `${floor.toLowerCase()}-n01`;
}

// Step 4: Render Map & Marker
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

    // If BFS failed, path is empty. Show fallback message or just markers.
    const isPathFound = path.length > 0;
    const distance = isPathFound ? (path.length - 1) * 5 : 0;
    const distanceText = isPathFound ? `약 <strong>${distance}m</strong>` : "경로 탐색 불가";

    panel.innerHTML = `
        <div class="result-map-wrapper">
            <div class="result-map-header">
                <div class="floor-title-large">${floor}</div>
            </div>
            
            <div class="map-legend-overlay">
                <div class="legend-item"><span class="dot blue"></span> 추천 경로</div>
                <div class="legend-item"><span class="dot red"></span> 상품 위치</div>
            </div>

            <div class="map-image-container">
                <img src="images/map_${floor.toLowerCase()}.png" class="map-base-img" onerror="this.src='https://placehold.co/600x400?text=Map+${floor}'">
                <svg class="map-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
                    ${isPathFound ? drawRouteSVG(floor, path) : ''}
                    ${renderMarkerSVG(floor, endNodeId, product.name)}
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
        stroke-width="3" 
        stroke-dasharray="8,4" 
        stroke-linecap="round" 
        stroke-linejoin="round" />
  `;
}

function renderMarkerSVG(floor, targetNodeId, productName) {
    const floorData = GRAPH[floor];
    const target = floorData.nodes[targetNodeId];
    const start = floorData.nodes[`${floor.toLowerCase()}-entrance`];

    if (!target) return ""; // Should not happen if logic is correct

    // Truncate product name (max 10 chars)
    const displayTitle = productName.length > 10 ? productName.substring(0, 10) + "..." : productName;

    return `
        <!-- Start Marker (Current Position) -->
        <g class="start-marker">
            <circle cx="${start.x}" cy="${start.y}" r="2" fill="#2962FF" stroke="white" stroke-width="0.5" />
            <circle cx="${start.x}" cy="${start.y}" r="4" fill="#2962FF" fill-opacity="0.2">
                <animate attributeName="r" from="2" to="6" dur="2s" repeatCount="indefinite" />
                <animate attributeName="fill-opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite" />
            </circle>
            <!-- Label for Start -->
            <rect x="${start.x - 10}" y="${start.y - 12}" width="20" height="6" rx="1.5" fill="white" stroke="#2962FF" stroke-width="0.3" filter="drop-shadow(0px 1px 1px rgba(0,0,0,0.2))"/>
            <text x="${start.x}" y="${start.y - 8}" font-size="3.5" text-anchor="middle" fill="black" font-weight="bold" font-family="sans-serif">현재 위치</text>
        </g>

        <!-- Target Marker (Product Location) -->
        <g class="target-marker">
            <!-- Ping animation for target -->
            <circle cx="${target.x}" cy="${target.y}" r="3" fill="#E50000" fill-opacity="0.3">
                <animate attributeName="r" from="3" to="10" dur="1.5s" repeatCount="indefinite" />
                <animate attributeName="fill-opacity" from="0.3" to="0" dur="1.5s" repeatCount="indefinite" />
            </circle>
            
            <!-- Pin Icon -->
            <path d="M${target.x} ${target.y} L${target.x - 4} ${target.y - 12} A4.5 4.5 0 1 1 ${target.x + 4} ${target.y - 12} Z" fill="#E50000" stroke="white" stroke-width="0.5" />
            <circle cx="${target.x}" cy="${target.y - 12}" r="2" fill="white" />

            <!-- Label for Target -->
            <rect x="${target.x - 18}" y="${target.y - 24}" width="36" height="7" rx="1.5" fill="white" stroke="#E50000" stroke-width="0.3" filter="drop-shadow(0px 1px 1px rgba(0,0,0,0.2))"/>
            <text x="${target.x}" y="${target.y - 19.5}" font-size="4" text-anchor="middle" fill="black" font-weight="bold" font-family="sans-serif">${displayTitle}</text>
        </g>
    `;
}
