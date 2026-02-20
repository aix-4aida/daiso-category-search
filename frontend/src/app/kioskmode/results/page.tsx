"use client";

import { useCallback, useEffect, useState, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { searchProducts } from "@/lib/api";
import type { ProductResult, SearchResponse } from "@/types/search";
import {
    getSearchState,
    getTopProduct,
    getRelatedProducts,
    hasResults,
    needsClarification,
    setSearchResponse,
    setQuery,
    setLoading,
    setError,
    addToHistory,
    incrementClarification,
} from "@/store/searchStore";
import BottomTabBar from "@/components/BottomTabBar";
import StoreMap from "@/components/StoreMap";

function formatPrice(price: number): string {
    return `${price.toLocaleString()}원`;
}

/* ================================================================
   LoadingScreen — Legacy-style progress circle with D logo
   Matches the deployed version's loading view
   ================================================================ */
function LoadingScreen({ query, statusText, onCancel }: { query: string; statusText: string; onCancel?: () => void }) {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setProgress((prev) => {
                const next = prev + Math.random() * 15;
                return next >= 100 ? 100 : next;
            });
        }, 200);
        return () => clearInterval(interval);
    }, []);

    const dashoffset = 565 - (565 * progress) / 100;

    return (
        <main className="flex flex-col min-h-[100dvh] bg-white items-center justify-center">
            <div style={{ textAlign: "center" }}>
                {/* Progress Circle */}
                <div style={{ position: "relative", width: 200, height: 200, margin: "0 auto" }}>
                    <svg width="200" height="200">
                        <circle cx="100" cy="100" r="90" fill="none" stroke="#f0f0f0" strokeWidth="6" />
                        <circle
                            cx="100" cy="100" r="90"
                            fill="none" stroke="#E50000" strokeWidth="6"
                            strokeLinecap="round"
                            strokeDasharray="565"
                            strokeDashoffset={dashoffset}
                            style={{ transition: "stroke-dashoffset 0.2s", transform: "rotate(-90deg)", transformOrigin: "center" }}
                        />
                    </svg>
                    <div style={{
                        position: "absolute", inset: 0,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 32, fontWeight: 800, color: "#333",
                    }}>
                        {Math.floor(progress)}%
                    </div>
                </div>

                {/* D Logo */}
                <div style={{ fontSize: 48, fontWeight: 900, color: "#E50000", marginTop: 8 }}>D</div>

                {/* Status Text */}
                <p style={{ fontSize: 18, fontWeight: 600, color: "#333", marginTop: 8 }}>{statusText}</p>

                {/* Query Tag */}
                {query && (
                    <div style={{
                        display: "inline-block", marginTop: 12,
                        padding: "6px 20px", background: "#f5f5f5",
                        borderRadius: 20, fontSize: 14, color: "#999",
                    }}>
                        &lsquo;{query}&rsquo;
                    </div>
                )}

                {/* Cancel Button */}
                {onCancel && (
                    <div style={{ marginTop: 24 }}>
                        <button
                            onClick={onCancel}
                            style={{
                                padding: "10px 24px", borderRadius: 24,
                                border: "1px solid #ddd", background: "white",
                                fontSize: 14, fontWeight: 600, color: "#666", cursor: "pointer",
                            }}
                        >
                            취소
                        </button>
                    </div>
                )}
            </div>
        </main>
    );
}

/* ================================================================
   SpeechRecognition type declarations (browser built-in API)
   ================================================================ */
interface SpeechRecognitionEvent {
    resultIndex: number;
    results: SpeechRecognitionResultList;
}
interface SpeechRecognitionErrorEvent {
    error: string;
    message?: string;
}

declare global {
    interface Window {
        webkitSpeechRecognition: new () => SpeechRecognition;
        SpeechRecognition: new () => SpeechRecognition;
    }
    interface SpeechRecognition extends EventTarget {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        start: () => void;
        stop: () => void;
        abort: () => void;
        onstart: (() => void) | null;
        onresult: ((event: SpeechRecognitionEvent) => void) | null;
        onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
        onend: (() => void) | null;
    }
}

function ResultsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const query = searchParams.get("q") || "";
    const mode = searchParams.get("mode"); // "voice" or null

    const [selectedProduct, setSelectedProduct] = useState<ProductResult | null>(null);
    const [allProducts, setAllProducts] = useState<ProductResult[]>([]);
    const [response, setResponse] = useState<SearchResponse | null>(null);
    const [isLoading, setIsLoadingLocal] = useState(false);
    const [showClarification, setShowClarification] = useState(false);

    // Voice State (browser built-in Speech API, like legacy app.js)
    const [isListening, setIsListening] = useState(false);
    const [voiceStatus, setVoiceStatus] = useState<"idle" | "listening" | "done" | "error">("idle");
    const [voiceTranscript, setVoiceTranscript] = useState("");
    const [voiceInterim, setVoiceInterim] = useState("");
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const hasStartedVoice = useRef(false);

    // ── Search Function ──────────────────────────────────────────
    const doSearch = useCallback(
        async (searchQuery: string, inputType: "text" | "voice" = "text") => {
            if (!searchQuery.trim()) return;

            setIsLoadingLocal(true);
            setIsListening(false);
            setQuery(searchQuery, inputType);
            setLoading(true);

            try {
                const state = getSearchState();
                const res = await searchProducts({
                    query: searchQuery,
                    input_type: inputType,
                    session_id: state.sessionId,
                    history: state.history,
                    clarification_count: state.clarificationCount,
                });

                setSearchResponse(res);
                setResponse(res);
                const top1 = res.top3?.find((p) => p.is_top1) || res.top3?.[0] || null;
                setAllProducts(res.top3 || []);
                setSelectedProduct(top1);

                if (res.needs_clarification) {
                    setShowClarification(true);
                }

                if (!res.is_in_scope || res.top3.length === 0) {
                    router.replace(
                        `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                    );
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "검색 오류");
                router.replace(
                    `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                );
            } finally {
                setIsLoadingLocal(false);
            }
        },
        [router]
    );

    // ── Voice: Browser Speech API (same as legacy app.js) ────────
    const startVoice = useCallback(() => {
        const SpeechRecognitionClass =
            typeof window !== "undefined"
                ? window.webkitSpeechRecognition || window.SpeechRecognition
                : null;

        if (!SpeechRecognitionClass) {
            setVoiceStatus("error");
            setVoiceTranscript("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return;
        }

        const recognition = new SpeechRecognitionClass();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "ko-KR";

        recognition.onstart = () => {
            setIsListening(true);
            setVoiceStatus("listening");
            setVoiceTranscript("");
            setVoiceInterim("");
        };

        recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interimTranscript = "";
            let finalTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            if (finalTranscript) {
                setVoiceTranscript(finalTranscript);
                setVoiceInterim("");
                setVoiceStatus("done");
                // Auto-search after voice completes (like legacy app.js)
                setTimeout(() => {
                    doSearch(finalTranscript, "voice");
                }, 500);
            } else if (interimTranscript) {
                setVoiceInterim(interimTranscript);
            }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            console.error("Speech recognition error:", event.error);
            setVoiceStatus("error");
            setVoiceTranscript(
                event.error === "not-allowed"
                    ? "마이크 접근 권한이 필요합니다."
                    : "음성 인식 오류가 발생했습니다."
            );
        };

        recognition.onend = () => {
            // If still listening (no final result yet), mark as error
            setIsListening(false);
            if (voiceStatus === "listening") {
                setVoiceStatus("error");
                setVoiceTranscript("음성이 인식되지 않았습니다.");
            }
        };

        recognitionRef.current = recognition;
        recognition.start();
    }, [doSearch, voiceStatus]);

    const retryVoice = useCallback(() => {
        recognitionRef.current?.abort();
        startVoice();
    }, [startVoice]);

    const cancelVoice = useCallback(() => {
        recognitionRef.current?.abort();
        router.back();
    }, [router]);

    // ── Initialization ──────────────────────────────────────────
    useEffect(() => {
        // Voice mode: start browser Speech API immediately
        if (mode === "voice" && !hasStartedVoice.current) {
            hasStartedVoice.current = true;
            startVoice();
            return;
        }

        // Text search mode: load from store or fetch
        if (query) {
            const state = getSearchState();

            if (hasResults() && state.query === query) {
                const top = getTopProduct();
                const related = getRelatedProducts();
                const all = top ? [top, ...related] : related;
                setAllProducts(all);
                setSelectedProduct(top || all[0] || null);
                setResponse(state.searchResponse);
                if (needsClarification()) {
                    setShowClarification(true);
                }
            } else {
                doSearch(query);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [query, mode]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            recognitionRef.current?.abort();
        };
    }, []);

    const handleBack = useCallback(() => {
        router.back();
    }, [router]);

    const handleSelectProduct = useCallback((product: ProductResult) => {
        setSelectedProduct(product);
    }, []);

    const handleClarificationOption = useCallback(
        async (option: string) => {
            setShowClarification(false);
            setIsLoadingLocal(true);
            addToHistory("user", query);
            addToHistory("assistant", response?.clarification_question || "");
            addToHistory("user", option);
            incrementClarification();

            try {
                const state = getSearchState();
                const res = await searchProducts({
                    query: option,
                    session_id: state.sessionId,
                    history: state.history,
                    clarification_count: state.clarificationCount,
                });

                setSearchResponse(res);
                setResponse(res);
                const top1 = res.top3?.find((p) => p.is_top1) || res.top3?.[0] || null;
                setAllProducts(res.top3 || []);
                setSelectedProduct(top1);
                if (res.needs_clarification) {
                    setShowClarification(true);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "검색 오류");
            } finally {
                setIsLoadingLocal(false);
            }
        },
        [query, response]
    );

    // ──────────────────────────────────────────────────────────────
    // LOADING SCREEN (Legacy Style: Progress Circle + D + 상품을 찾는 중...)
    // Shown during voice listening AND text search loading
    // ──────────────────────────────────────────────────────────────
    if (isListening || isLoading || (mode === "voice" && allProducts.length === 0 && voiceStatus !== "done" && voiceStatus !== "error")) {
        return (
            <LoadingScreen
                query={query || voiceTranscript || voiceInterim || ""}
                statusText={
                    isLoading ? "상품을 찾는 중..." :
                        voiceStatus === "listening" ? (voiceInterim ? `"${voiceInterim}" 듣는 중...` : "듣고 있어요...") :
                            "준비 중..."
                }
                onCancel={mode === "voice" && !isLoading ? cancelVoice : undefined}
            />
        );
    }

    // ──────────────────────────────────────────────────────────────
    // RESULTS VIEW (3-panel layout)
    // ──────────────────────────────────────────────────────────────
    return (
        <main className="flex flex-col min-h-[100dvh] bg-[#f5f5f7]">
            {/* Header */}
            <div className="results-header">
                <button className="back-btn" onClick={handleBack}>←</button>
                <h2 className="results-title">
                    <span className="query-highlight">&ldquo;{query || voiceTranscript}&rdquo;</span> 검색 결과 {allProducts.length}개
                </h2>
            </div>

            {/* Clarification Banner */}
            {showClarification && response?.clarification_question && (
                <div style={{ background: "#FFFDE7", borderBottom: "1px solid #FFF9C4", padding: "12px 20px" }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "#F57F17", marginBottom: 8 }}>
                        💡 {response.clarification_question}
                    </p>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {response.clarification_options.map((option, idx) => (
                            <button
                                key={idx}
                                onClick={() => handleClarificationOption(option)}
                                style={{
                                    padding: "6px 16px",
                                    borderRadius: 20,
                                    background: "white",
                                    border: "1px solid #FFF176",
                                    fontSize: 13,
                                    fontWeight: 600,
                                    color: "#F57F17",
                                    cursor: "pointer",
                                }}
                            >
                                {option}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* 3-Panel Layout */}
            <div className="results-layout">
                {/* Left: Product Cards */}
                <div className="results-left-panel">
                    {allProducts.map((product) => (
                        <div
                            key={product.product_id}
                            className={`result-card ${selectedProduct?.product_id === product.product_id ? "selected" : ""}`}
                            onClick={() => handleSelectProduct(product)}
                        >
                            <div className="result-img">
                                {product.image_url ? (
                                    <img
                                        src={product.image_url}
                                        alt={product.name}
                                        style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 10 }}
                                    />
                                ) : (
                                    <div className="result-img-text">
                                        {product.location_text?.split("-")[0] || "B1"}
                                    </div>
                                )}
                            </div>
                            <div className="result-info">
                                <div className="card-tag">{product.category_middle || product.category_major || "일반"}</div>
                                <h3 className="result-title">{product.name}</h3>
                                <div className="result-location">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                                    </svg>
                                    {product.location_text}
                                </div>
                                <div className="result-price">{formatPrice(product.price)}</div>
                            </div>
                            <div className="card-arrow">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M9 18l6-6-6-6" />
                                </svg>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Center: Map */}
                <div className="results-center-panel">
                    {selectedProduct && (
                        <StoreMap
                            productName={selectedProduct.name}
                            categoryMajor={selectedProduct.category_major}
                            categoryMiddle={selectedProduct.category_middle}
                            locationText={selectedProduct.location_text}
                        />
                    )}
                </div>

                {/* Right: QR & Actions */}
                <div className="results-right-panel">
                    <div className="qr-section">
                        <h4>스마트폰으로 스캔</h4>
                        <div className="qr-placeholder">
                            QR 코드
                        </div>
                        <button className="kakao-btn">
                            <div className="kakao-logo-bubble">TALK</div>
                            카카오로 보내기
                        </button>
                    </div>
                </div>
            </div>

            {/* Timing Debug */}
            {response?.timing_ms && (
                <div style={{ background: "#f0f0f0", padding: "8px", textAlign: "center", fontSize: 11, color: "#aaa" }}>
                    검색 소요: {response.timing_ms.total}ms
                </div>
            )}

            <BottomTabBar />
        </main>
    );
}

export default function ResultsPage() {
    return (
        <Suspense
            fallback={
                <main className="flex min-h-screen items-center justify-center bg-gray-50">
                    <div className="w-12 h-12 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
                </main>
            }
        >
            <ResultsContent />
        </Suspense>
    );
}
