"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { searchProducts } from "@/lib/api";
import {
    setQuery,
    setSearchResponse,
    setLoading,
    setError,
    resetSearch,
    getSearchState,
} from "@/store/searchStore";
import BottomTabBar from "@/components/BottomTabBar";

export default function KioskHome() {
    const router = useRouter();
    const [query, setQueryLocal] = useState("");
    const [isSearching, setIsSearching] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // ── Existing logic (unchanged) ──────────────────────────────

    const performSearch = useCallback(
        async (searchQuery: string, inputType: "text" | "voice" = "text") => {
            if (!searchQuery.trim()) return;

            setIsSearching(true);
            setQuery(searchQuery, inputType);
            setLoading(true);

            try {
                const state = getSearchState();
                const response = await searchProducts({
                    query: searchQuery,
                    input_type: inputType,
                    session_id: state.sessionId,
                    history: state.history,
                    clarification_count: state.clarificationCount,
                });

                setSearchResponse(response);

                if (!response.is_in_scope || response.error) {
                    router.push(
                        `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                    );
                } else if (response.top3.length === 0) {
                    router.push(
                        `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                    );
                } else {
                    router.push(
                        `/kioskmode/results?q=${encodeURIComponent(searchQuery)}`
                    );
                }
            } catch (err) {
                const errorMsg =
                    err instanceof Error ? err.message : "검색 중 오류가 발생했습니다.";
                setError(errorMsg);
                router.push(
                    `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                );
            } finally {
                setIsSearching(false);
            }
        },
        [router]
    );

    const handleSearch = useCallback(() => {
        performSearch(query);
    }, [query, performSearch]);

    const handleVoiceSearch = useCallback(() => {
        resetSearch();
        router.push("/kioskmode/listening");
    }, [router]);

    // ── UI (reskinned to match first.png) ───────────────────────

    return (
        <main className="flex flex-col min-h-[100dvh] bg-gray-50">
            {/* ── Header ── */}
            <header className="flex items-center justify-between px-5 py-3 bg-white">
                <div className="flex items-center gap-2">
                    <div
                        className="w-8 h-8 bg-red-600 rounded flex items-center justify-center"
                        role="img"
                        aria-label="다이소 로고"
                    >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="white" aria-hidden="true">
                            <rect x="4" y="4" width="7" height="7" rx="1" />
                            <rect x="13" y="4" width="7" height="7" rx="1" />
                            <rect x="4" y="13" width="7" height="7" rx="1" />
                            <rect x="13" y="13" width="7" height="7" rx="1" />
                        </svg>
                    </div>
                    <span className="text-lg font-extrabold text-red-600 tracking-tight">
                        어디다있소
                    </span>
                </div>
            </header>

            {/* ── Search Bar ── */}
            <div className="px-5 py-3 bg-white border-b border-gray-100">
                <div className="flex items-center gap-2.5 max-w-2xl mx-auto">
                    {/* Mic button */}
                    <button
                        onClick={handleVoiceSearch}
                        disabled={isSearching}
                        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-300 ${
                            isSearching
                                ? "bg-gray-400 cursor-not-allowed"
                                : "bg-red-500 hover:bg-red-600 active:scale-95 cursor-pointer"
                        }`}
                        aria-label="음성으로 검색하기"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="white" aria-hidden="true">
                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                        </svg>
                    </button>

                    {/* Search input */}
                    <div className="flex-1 flex items-center bg-gray-100 rounded-full px-4 py-2.5">
                        <label htmlFor="search-input" className="sr-only">상품명 검색</label>
                        <input
                            id="search-input"
                            ref={inputRef}
                            type="text"
                            className="flex-1 bg-transparent outline-none text-sm text-gray-800 placeholder-gray-400"
                            placeholder="찾으시는 상품을 말씀해주세요"
                            value={query}
                            onChange={(e) => setQueryLocal(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            onFocus={(e) => e.target.scrollIntoView({ behavior: "smooth", block: "center" })}
                            autoComplete="off"
                            disabled={isSearching}
                        />
                        {isSearching ? (
                            <div className="ml-2 w-5 h-5 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <button
                                onClick={handleSearch}
                                className="ml-2 text-gray-400 hover:text-gray-600 cursor-pointer focus:outline-none"
                                aria-label="검색"
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                    <circle cx="11" cy="11" r="8" />
                                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Main Content ── */}
            <div className="flex-1 flex flex-col items-center justify-center px-5 pb-24">
                {/* Promotion Banner */}
                <div className="w-full max-w-2xl mx-auto mt-6">
                    <div className="relative w-full rounded-2xl overflow-hidden shadow-lg bg-gradient-to-br from-pink-400 via-red-400 to-pink-500 aspect-[2.5/1] flex items-center justify-center">
                        {/* Decorative elements */}
                        <div className="absolute inset-0 opacity-20">
                            <div className="absolute top-4 left-6 w-16 h-16 rounded-full bg-white" />
                            <div className="absolute top-8 left-20 w-10 h-10 rounded-full bg-white" />
                            <div className="absolute bottom-6 right-10 w-20 h-20 rounded-full bg-white" />
                            <div className="absolute top-6 right-24 w-8 h-8 rounded-full bg-white" />
                            <div className="absolute bottom-4 left-32 w-12 h-12 rounded-full bg-white" />
                        </div>
                        <div className="relative text-center text-white px-6">
                            <p className="text-2xl sm:text-3xl font-extrabold tracking-wide drop-shadow">
                                SPRING PROMOTION
                            </p>
                            <p className="text-xs sm:text-sm mt-1 opacity-90 drop-shadow">
                                New Arrivals &amp; Special Offers
                            </p>
                            <p className="text-sm sm:text-base font-bold mt-1 drop-shadow">
                                Visit Us Today!
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Bottom Tab Bar ── */}
            <BottomTabBar />
        </main>
    );
}
