"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchProducts } from "@/lib/api";
import {
    setQuery,
    setSearchResponse,
    setLoading,
    setError,
    getSearchState,
} from "@/store/searchStore";
import BottomTabBar from "@/components/BottomTabBar";

const CATEGORIES = [
    { label: "뷰티/위생", icon: "💄" },
    { label: "주방용품", icon: "🍳" },
    { label: "청소/욕실", icon: "🧹" },
    { label: "수납/정리", icon: "📦" },
    { label: "문구/팬시", icon: "✏️" },
    { label: "인테리어/원예", icon: "🌿" },
    { label: "공구/디지털", icon: "🔧" },
    { label: "식품", icon: "🍪" },
    { label: "스포츠/레저/취미", icon: "⚽" },
    { label: "패션/잡화", icon: "👜" },
    { label: "반려동물", icon: "🐾" },
    { label: "유아/완구", icon: "🧸" },
] as const;

export default function CategoryPage() {
    const router = useRouter();
    const [isSearching, setIsSearching] = useState(false);

    const handleCategoryClick = useCallback(
        async (category: string) => {
            if (isSearching) return;

            const searchQuery = `${category} 상품 찾아줘`;
            setIsSearching(true);
            setQuery(searchQuery, "text");
            setLoading(true);

            try {
                const state = getSearchState();
                const response = await searchProducts({
                    query: searchQuery,
                    input_type: "text",
                    session_id: state.sessionId,
                    history: state.history,
                    clarification_count: state.clarificationCount,
                });

                setSearchResponse(response);

                if (!response.is_in_scope || response.error || response.top3.length === 0) {
                    router.push(`/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`);
                } else {
                    router.push(`/kioskmode/results?q=${encodeURIComponent(searchQuery)}`);
                }
            } catch (err) {
                const errorMsg = err instanceof Error ? err.message : "검색 중 오류가 발생했습니다.";
                setError(errorMsg);
                router.push(`/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`);
            } finally {
                setIsSearching(false);
            }
        },
        [router, isSearching]
    );

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
                    카테고리
                </span>
            </header>

            {/* Category Grid */}
            <div className="flex-1 px-5 py-5 pb-24">
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 max-w-2xl mx-auto">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat.label}
                            onClick={() => handleCategoryClick(cat.label)}
                            disabled={isSearching}
                            className={`flex flex-col items-center justify-center gap-2 bg-white rounded-2xl shadow-sm p-4 cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-300 ${
                                isSearching
                                    ? "opacity-50 cursor-not-allowed"
                                    : "hover:shadow-md hover:scale-[1.02] active:scale-[0.98]"
                            }`}
                        >
                            <span className="text-3xl" role="img" aria-hidden="true">
                                {cat.icon}
                            </span>
                            <span className="text-xs sm:text-sm font-medium text-gray-700 text-center leading-tight">
                                {cat.label}
                            </span>
                        </button>
                    ))}
                </div>
            </div>

            <BottomTabBar />
        </main>
    );
}
