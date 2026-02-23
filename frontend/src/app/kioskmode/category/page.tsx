"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import BottomTabBar from "@/components/BottomTabBar";

// 카테고리 이름 → 아이콘 매핑 (DB에서 가져온 이름 기반)
const CATEGORY_ICONS: Record<string, string> = {
    "뷰티/위생": "💄",
    "주방용품": "🍳",
    "청소/욕실": "🧹",
    "수납/정리": "📦",
    "문구/팬시": "✏️",
    "인테리어/원예": "🌿",
    "공구/디지털": "🔧",
    "식품": "🍪",
    "스포츠/레저/취미": "⚽",
    "패션/잡화": "👜",
    "반려동물": "🐾",
    "유아/완구": "🧸",
    "국민득템": "🏆",
    "상품권": "🎫",
    "홈패브릭": "🛋️",
    "세탁/청소": "🧼",
    "캠핑/차량관리": "🏕️",
    "여행": "✈️",
    "수예/공예": "🧶",
};

const API_BASE: string = process.env.NEXT_PUBLIC_API_URL || "/api";

interface CategoryItem {
    name: string;
    count: number;
}

export default function CategoryPage() {
    const router = useRouter();
    const [isSearching, setIsSearching] = useState(false);
    const [categories, setCategories] = useState<CategoryItem[]>([]);
    const [isLoadingCategories, setIsLoadingCategories] = useState(true);

    // DB에서 카테고리 목록 가져오기
    useEffect(() => {
        async function fetchCategories() {
            try {
                const res = await fetch(`${API_BASE}/search/categories`);
                if (res.ok) {
                    const data = await res.json();
                    setCategories(data.categories || []);
                }
            } catch (err) {
                console.error("Failed to fetch categories:", err);
            } finally {
                setIsLoadingCategories(false);
            }
        }
        fetchCategories();
    }, []);

    const handleCategoryClick = useCallback(
        (categoryName: string) => {
            if (isSearching) return;
            router.push(`/kioskmode/category/products?name=${encodeURIComponent(categoryName)}`);
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
                {isLoadingCategories ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="w-10 h-10 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 max-w-2xl mx-auto">
                        {categories.map((cat) => (
                            <button
                                key={cat.name}
                                onClick={() => handleCategoryClick(cat.name)}
                                disabled={isSearching}
                                className={`flex flex-col items-center justify-center gap-2 bg-white rounded-2xl shadow-sm p-4 cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-300 ${isSearching
                                    ? "opacity-50 cursor-not-allowed"
                                    : "hover:shadow-md hover:scale-[1.02] active:scale-[0.98]"
                                    }`}
                            >
                                <span className="text-3xl" role="img" aria-hidden="true">
                                    {CATEGORY_ICONS[cat.name] || "📁"}
                                </span>
                                <span className="text-xs sm:text-sm font-medium text-gray-700 text-center leading-tight">
                                    {cat.name}
                                </span>
                                <span className="text-[10px] text-gray-400">
                                    {cat.count}개
                                </span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <BottomTabBar />
        </main>
    );
}
