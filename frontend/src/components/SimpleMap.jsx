import React, { useState } from 'react';
import { findProductLocation } from '../config/mapConfig';

const SimpleMap = ({ targetLocation, productName }) => {
    // Find target shelf based on location (from DB) or product name
    const target = findProductLocation(targetLocation || productName);

    // State to track image aspect ratios for B1 and B2
    const [ratios, setRatios] = useState({ B1: 1.4, B2: 1.4 }); // Default vertical ratio approx A4

    const handleImageLoad = (floor) => (e) => {
        const { naturalWidth, naturalHeight } = e.currentTarget;
        if (naturalWidth > 0) {
            setRatios(prev => ({
                ...prev,
                [floor]: naturalHeight / naturalWidth
            }));
        }
    };

    // Calculate path ensuring 90-degree turns
    const getPath = (floor, target) => {
        if (!target) return "";

        if (floor === "B1") {
            // Start: (50, 15) - Entrance
            // Strategy: "Clear Entrance Box & Middle Safe Passage"
            // 1. Move down to y=25 to clear the Entrance/Checkout box.
            // 2. Move right to x=65 (Gap between Season and Beauty).
            // 3. Move down to y=85 (Gap above Packaging/Below Party).

            const entranceClearY = 25; // Clear the entrance box
            const middleAisleX = 65; // Safe passage between Center and Right islands
            const bottomAisleY = 85;

            // 1. Start from Entrance
            let d = `M 50 15`;

            // 2. Move Down to clear Entrance Box
            d += ` L 50 ${entranceClearY}`;

            // 3. Move Right to Middle Aisle
            d += ` L ${middleAisleX} ${entranceClearY}`;

            // 4. Move Down Middle Aisle
            d += ` L ${middleAisleX} ${bottomAisleY}`;

            // 5. Move across Bottom Aisle to Target X
            d += ` L ${target.x} ${bottomAisleY}`;

            // 6. Move up to Target Y
            d += ` L ${target.x} ${target.y}`;

            return d;
        } else {
            // B2 Logic (Stairs at 25, 90)
            const aisleY = 80;
            if (target.y > aisleY) {
                return `M 25 90 L 25 ${target.y} L ${target.x} ${target.y}`;
            }
            return `M 25 90 L 25 ${aisleY} L ${target.x} ${aisleY} L ${target.x} ${target.y}`;
        }
    }

    const renderMapFloor = (floor, imgSrc, title, startLabel, startPos) => {
        const ratio = ratios[floor];
        const viewBoxHeight = 100 * ratio;

        // Target is valid only if it's on the current floor
        // If no target is provided, we just show the map without path (default mode)
        const isTargetOnFloor = target && target.floor === floor;
        const pathData = isTargetOnFloor ? getPath(floor, target) : "";

        return (
            <div className="flex-1 bg-white border border-gray-200 rounded-xl relative flex flex-col overflow-hidden shadow-sm h-full min-h-[300px]">
                <div className="absolute top-3 left-4 z-20 bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full shadow-sm border border-gray-100">
                    <span className="text-2xl font-black text-gray-800">{floor}</span>
                </div>

                {/* Container for Image & SVG - Centered and constrained */}
                <div className="relative w-full flex-1 flex flex-col items-center justify-center p-2">
                    <h3 className="text-lg font-bold mb-2 flex items-center absolute top-2 right-4 bg-white/90 px-2 rounded-md z-10">
                        {title}
                    </h3>
                    <div className="relative w-full h-full flex items-center justify-center rounded-lg overflow-hidden border border-gray-100 bg-gray-50">
                        <img
                            src={imgSrc}
                            alt={`${floor} Map`}
                            className="max-w-full max-h-full object-contain"
                            onLoad={handleImageLoad(floor)}
                        />
                        <svg
                            className="absolute inset-0 w-full h-full pointer-events-none"
                            viewBox={`0 0 100 ${viewBoxHeight}`}
                            preserveAspectRatio="xMidYMid meet"
                        >
                            {/* Define Markers */}
                            <defs>
                                <marker id={`arrow${floor}`} markerWidth="4" markerHeight="4" refX="2" refY="2" orient="auto" markerUnits="strokeWidth">
                                    <path d="M0,0 L0,4 L4,2 z" fill="#ef4444" />
                                </marker>
                            </defs>

                            {/* Start Point (Blue Circle) - Always Visible */}
                            <circle cx={startPos.x} cy={startPos.y} r="3" fill="white" stroke="#2563eb" strokeWidth="2" />
                            <circle cx={startPos.x} cy={startPos.y} r="1.5" fill="#2563eb" />

                            {/* Start Label */}
                            <rect x={startPos.x - 12} y={startPos.y + 4} width="24" height="6" rx="3" fill="#2563eb" opacity="0.9" />
                            <text x={startPos.x} y={startPos.y + 8} fontSize="3" textAnchor="middle" fill="white" fontWeight="bold">현재위치</text>

                            {/* Path and Destination - Only if Target is on this floor */}
                            {isTargetOnFloor && (
                                <>
                                    <path
                                        d={pathData}
                                        fill="none"
                                        stroke="#ef4444"
                                        strokeWidth="2"
                                        strokeDasharray="4 2"
                                        markerEnd={`url(#arrow${floor})`}
                                        className="animate-dash"
                                    />
                                    {/* Destination Marker (Red Circle Ripple effect) */}
                                    <circle cx={target.x} cy={target.y} r="4" fill="#ef4444" opacity="0.3">
                                        <animate attributeName="r" from="2" to="6" dur="1.5s" repeatCount="indefinite" />
                                        <animate attributeName="opacity" from="0.6" to="0" dur="1.5s" repeatCount="indefinite" />
                                    </circle>
                                    <circle cx={target.x} cy={target.y} r="2" fill="#ef4444" stroke="white" strokeWidth="1" />
                                </>
                            )}
                        </svg>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col md:flex-row gap-4 w-full h-full">
            {renderMapFloor("B1", "/map_b1.jpg", "1층 매장", "현재위치", { x: 50, y: 15 })}
            {renderMapFloor("B2", "/map_b2.jpg", "지하 매장", "계단입구", { x: 25, y: 90 })}
        </div>
    );
};

export default SimpleMap;
