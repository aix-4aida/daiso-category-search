"use client";

import { useState } from "react";
import BottomTabBar from "@/components/BottomTabBar";

const FLOORS = [
    { id: "B1" as const, label: "B1", image: "/images/map_b1.jpg" },
    { id: "B2" as const, label: "B2", image: "/images/map_b2.jpg" },
];

export default function StoreMapPage() {
    const [activeFloor, setActiveFloor] = useState<"B1" | "B2">("B1");
    const current = FLOORS.find((f) => f.id === activeFloor)!;

    return (
        <main className="flex flex-col min-h-[100dvh] bg-gray-50">
            {/* Header */}
            <header className="flex items-center gap-2 px-5 py-3 bg-white border-b border-gray-100">
                <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center" role="img" aria-label="다이소 로고">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="white" aria-hidden="true">
                        <rect x="4" y="4" width="7" height="7" rx="1" />
                        <rect x="13" y="4" width="7" height="7" rx="1" />
                        <rect x="4" y="13" width="7" height="7" rx="1" />
                        <rect x="13" y="13" width="7" height="7" rx="1" />
                    </svg>
                </div>
                <span className="text-lg font-extrabold text-red-600 tracking-tight">
                    매장 배치도
                </span>
            </header>

            {/* Content — 2-column */}
            <div className="flex-1 flex px-5 py-5 pb-24 gap-4 max-w-5xl mx-auto w-full overflow-hidden">
                {/* Left: Map image */}
                <div className="flex-1 bg-white rounded-2xl shadow-sm overflow-hidden flex items-center justify-center"
                    style={{ maxHeight: "calc(100dvh - 56px - 64px - 40px)" }}
                >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={current.image}
                        alt={`${current.label} 매장 배치도`}
                        className="w-full h-full block"
                        style={{ objectFit: "contain" }}
                    />
                </div>

                {/* Right: Floor selector */}
                <div className="flex flex-col gap-3" style={{ width: 180 }}>
                    {FLOORS.map((floor) => {
                        const isActive = activeFloor === floor.id;
                        return (
                            <button
                                key={floor.id}
                                onClick={() => setActiveFloor(floor.id)}
                                className={`w-full py-4 rounded-xl text-lg font-bold cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-300 ${
                                    isActive
                                        ? "bg-red-500 text-white shadow-md border-2 border-red-600"
                                        : "bg-white text-gray-600 border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                                }`}
                                aria-pressed={isActive}
                            >
                                {floor.label}
                            </button>
                        );
                    })}
                </div>
            </div>

            <BottomTabBar />
        </main>
    );
}
