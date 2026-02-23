"use client";

import React, { useMemo } from "react";

// ============================================================================
// GRAPH Data (Ported from map.js)
// ============================================================================

interface NodePosition {
    x: number;
    y: number;
}

interface FloorData {
    nodes: Record<string, NodePosition>;
    edges: [string, string][];
    categoryMap: Record<string, string>;
}

const GRAPH: Record<string, FloorData> = {
    B1: {
        nodes: {
            "b1-entrance": { x: 50, y: 95 },
            "b1-n01": { x: 50, y: 82 },
            "b1-n02": { x: 22, y: 78 },
            "b1-n03": { x: 78, y: 78 },
            "b1-n04": { x: 10, y: 60 },
            "b1-n05": { x: 35, y: 60 },
            "b1-n06": { x: 65, y: 60 },
            "b1-n07": { x: 90, y: 60 },
            "b1-n08": { x: 20, y: 35 },
            "b1-n09": { x: 50, y: 35 },
            "b1-n10": { x: 80, y: 35 },
            "b1-n11": { x: 50, y: 10 },
        },
        edges: [
            ["b1-entrance", "b1-n01"],
            ["b1-n01", "b1-n02"], ["b1-n01", "b1-n03"], ["b1-n01", "b1-n05"],
            ["b1-n02", "b1-n04"], ["b1-n02", "b1-n05"],
            ["b1-n03", "b1-n06"], ["b1-n03", "b1-n07"],
            ["b1-n04", "b1-n05"], ["b1-n04", "b1-n08"],
            ["b1-n05", "b1-n06"], ["b1-n05", "b1-n09"],
            ["b1-n06", "b1-n07"], ["b1-n06", "b1-n09"],
            ["b1-n07", "b1-n10"],
            ["b1-n08", "b1-n09"], ["b1-n08", "b1-n11"],
            ["b1-n09", "b1-n10"], ["b1-n09", "b1-n11"],
            ["b1-n10", "b1-n11"],
        ],
        categoryMap: {
            "메이크업": "b1-n02", "스킨케어": "b1-n02", "남성케어": "b1-n02", "헤어케어": "b1-n02",
            "위생용품": "b1-n08", "구강케어": "b1-n08", "의약외품": "b1-n08",
            "과자": "b1-n04", "간식": "b1-n04", "식품": "b1-n04", "가공식품": "b1-n04",
            "필기구": "b1-n03", "노트": "b1-n03", "사무용품": "b1-n03", "미술용품": "b1-n03",
            "파티용품": "b1-n10", "포장용품": "b1-n03",
            "휴대폰용품": "b1-n07", "컴퓨터용품": "b1-n07", "디지털": "b1-n07",
            "양말": "b1-n05", "속옷": "b1-n05", "의류": "b1-n06", "모자": "b1-n06",
            "방향제": "b1-n06", "인테리어소품": "b1-n06",
            "뷰티": "b1-n02", "화장품": "b1-n02",
            "건강": "b1-n08", "의료": "b1-n08",
            "문구": "b1-n03", "팬시": "b1-n03", "완구": "b1-n03",
            "전자": "b1-n07",
            "패션": "b1-n06", "잡화": "b1-n06",
            "인테리어": "b1-n06",
            "시즌": "b1-n10",
            "청소": "b1-n05", "세탁": "b1-n05", "욕실": "b1-n05",
            "위생": "b1-n08",
            "기타": "b1-n01",
        },
    },
    B2: {
        nodes: {
            "b2-entrance": { x: 50, y: 95 },
            "b2-n01": { x: 50, y: 85 },
            "b2-n02": { x: 25, y: 85 },
            "b2-n03": { x: 75, y: 85 },
            "b2-n04": { x: 10, y: 80 },
            "b2-n05": { x: 25, y: 70 },
            "b2-n06": { x: 50, y: 70 },
            "b2-n07": { x: 75, y: 70 },
            "b2-n08": { x: 15, y: 58 },
            "b2-n09": { x: 35, y: 55 },
            "b2-n10": { x: 50, y: 55 },
            "b2-n11": { x: 65, y: 55 },
            "b2-n12": { x: 88, y: 55 },
            "b2-n13": { x: 15, y: 40 },
            "b2-n14": { x: 35, y: 38 },
            "b2-n15": { x: 50, y: 38 },
            "b2-n16": { x: 65, y: 38 },
            "b2-n17": { x: 85, y: 38 },
            "b2-n18": { x: 20, y: 20 },
            "b2-n19": { x: 50, y: 20 },
            "b2-n20": { x: 78, y: 20 },
            "b2-n21": { x: 50, y: 8 },
        },
        edges: [
            ["b2-entrance", "b2-n01"],
            ["b2-n01", "b2-n02"], ["b2-n01", "b2-n03"], ["b2-n01", "b2-n06"],
            ["b2-n02", "b2-n04"], ["b2-n02", "b2-n05"],
            ["b2-n03", "b2-n07"],
            ["b2-n04", "b2-n08"],
            ["b2-n05", "b2-n06"], ["b2-n05", "b2-n08"], ["b2-n05", "b2-n09"],
            ["b2-n06", "b2-n07"], ["b2-n06", "b2-n10"],
            ["b2-n07", "b2-n11"], ["b2-n07", "b2-n12"],
            ["b2-n08", "b2-n09"], ["b2-n08", "b2-n13"],
            ["b2-n09", "b2-n10"], ["b2-n09", "b2-n14"],
            ["b2-n10", "b2-n11"], ["b2-n10", "b2-n15"],
            ["b2-n11", "b2-n12"], ["b2-n11", "b2-n16"],
            ["b2-n12", "b2-n17"],
            ["b2-n13", "b2-n14"], ["b2-n13", "b2-n18"],
            ["b2-n14", "b2-n15"], ["b2-n14", "b2-n18"],
            ["b2-n15", "b2-n16"], ["b2-n15", "b2-n19"],
            ["b2-n16", "b2-n17"], ["b2-n16", "b2-n20"],
            ["b2-n17", "b2-n20"],
            ["b2-n18", "b2-n19"], ["b2-n18", "b2-n21"],
            ["b2-n19", "b2-n20"], ["b2-n19", "b2-n21"],
            ["b2-n20", "b2-n21"],
        ],
        categoryMap: {
            "욕실용품": "b2-n04", "청소용품": "b2-n05", "세탁용품": "b2-n08",
            "주방용품": "b2-n07", "조리도구": "b2-n07", "식기": "b2-n07",
            "밀폐용기": "b2-n07", "수납용품": "b2-n11",
            "홈패브릭": "b2-n11", "커튼": "b2-n11", "침구": "b2-n11",
            "공구": "b2-n14", "자동차용품": "b2-n12", "자전거용품": "b2-n12",
            "캠핑용품": "b2-n12", "여행용품": "b2-n20",
            "원예용품": "b2-n18", "반려동물용품": "b2-n19", "애완용품": "b2-n19",
            "수예": "b2-n16", "취미": "b2-n14",
            "욕실": "b2-n04", "청소": "b2-n05", "세탁": "b2-n08",
            "주방": "b2-n07", "수납": "b2-n11",
            "자동차": "b2-n12", "캠핑": "b2-n12",
            "원예": "b2-n18", "반려동물": "b2-n19",
        },
    },
};

// ============================================================================
// BFS Pathfinding
// ============================================================================

function buildAdjList(floorData: FloorData): Record<string, string[]> {
    const adj: Record<string, string[]> = {};
    Object.keys(floorData.nodes).forEach((n) => (adj[n] = []));
    floorData.edges.forEach(([a, b]) => {
        if (!floorData.nodes[a] || !floorData.nodes[b]) return;
        adj[a].push(b);
        adj[b].push(a);
    });
    return adj;
}

function bfs(adj: Record<string, string[]>, start: string, end: string): string[] {
    if (!start || !end) return [];
    const queue: string[][] = [[start]];
    const visited = new Set([start]);

    while (queue.length > 0) {
        const path = queue.shift()!;
        const node = path[path.length - 1];
        if (node === end) return path;

        for (const neighbor of adj[node] || []) {
            if (!visited.has(neighbor)) {
                visited.add(neighbor);
                queue.push([...path, neighbor]);
            }
        }
    }
    return [];
}

function getArrivalNodeId(floor: string, categoryMajor: string, categoryMiddle: string): string {
    const data = GRAPH[floor];
    if (!data) return `${floor.toLowerCase()}-entrance`;

    // 1. Try Category Middle
    if (categoryMiddle && data.categoryMap[categoryMiddle]) {
        return data.categoryMap[categoryMiddle];
    }
    // 2. Try Category Major
    if (categoryMajor && data.categoryMap[categoryMajor]) {
        return data.categoryMap[categoryMajor];
    }
    // 3. Fallback
    return `${floor.toLowerCase()}-n01`;
}

// ============================================================================
// StoreMap Component
// ============================================================================

interface StoreMapProps {
    productName: string;
    categoryMajor: string;
    categoryMiddle: string;
    locationText: string; // e.g. "B1-N01" or "B2 > 주방용품"
}

function extractFloor(locationText: string): string {
    const upper = locationText.toUpperCase();
    if (upper.includes("B2")) return "B2";
    return "B1";
}

export default function StoreMap({
    productName,
    categoryMajor,
    categoryMiddle,
    locationText,
}: StoreMapProps) {
    const floor = extractFloor(locationText);

    const { path, startNode, endNode, distance, floorData } = useMemo(() => {
        const fd = GRAPH[floor];
        if (!fd) return { path: [] as string[], startNode: null, endNode: null, distance: 0, floorData: null };

        const startId = `${floor.toLowerCase()}-entrance`;
        const endId = getArrivalNodeId(floor, categoryMajor, categoryMiddle);
        const adj = buildAdjList(fd);
        const p = bfs(adj, startId, endId);
        const dist = p.length > 0 ? (p.length - 1) * 5 : 0;

        return {
            path: p,
            startNode: fd.nodes[startId],
            endNode: fd.nodes[endId],
            distance: dist,
            floorData: fd,
        };
    }, [floor, categoryMajor, categoryMiddle]);

    if (!floorData) {
        return (
            <div style={{ padding: 20, textAlign: "center", color: "#999" }}>
                지도 데이터를 불러올 수 없습니다.
            </div>
        );
    }

    const displayTitle = productName.length > 10 ? productName.substring(0, 10) + "..." : productName;

    // Build SVG polyline points
    const routePoints = path
        .map((id) => {
            const n = floorData.nodes[id];
            return n ? `${n.x},${n.y}` : "";
        })
        .filter(Boolean)
        .join(" ");

    return (
        <div className="store-map-container">
            {/* Floor Label */}
            <div className="store-map-header">
                <span className="store-map-floor-label">{floor}</span>
                <div className="store-map-legend">
                    <span className="legend-dot blue" /> 추천 경로
                    <span className="legend-dot red" /> 상품 위치
                </div>
            </div>

            {/* Floor Map Image */}
            <div className="store-map-svg-wrapper">
                <img
                    src={floor === "B2" ? "/images/map_b2.jpg" : "/images/map_b1.jpg"}
                    alt={`${floor} 층 매장 지도`}
                    style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        borderRadius: 8,
                    }}
                />
            </div>

            {/* Footer */}
            <div className="store-map-footer">
                현재 위치: <strong>정문 입구</strong> &nbsp;|&nbsp; 이동 거리: {path.length > 0 ? <strong>약 {distance}m</strong> : "경로 탐색 불가"}
            </div>
        </div>
    );
}
