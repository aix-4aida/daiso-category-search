"use client";

import { useState, useCallback, useEffect, useRef } from "react";
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

/* ================================================================
   SpeechRecognition type declarations
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

export default function KioskHome() {
    const router = useRouter();
    const [query, setQueryLocal] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    // Voice State
    const [isListening, setIsListening] = useState(false);
    const [voiceLabel, setVoiceLabel] = useState("어떤 상품의 위치를 알고 싶으세요?");
    const recognitionRef = useRef<SpeechRecognition | null>(null);

    // Carousel State
    const [currentSlide, setCurrentSlide] = useState(0);
    const totalSlides = 2;

    // ── Carousel Logic ──────────────────────────────────────────
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % totalSlides);
        }, 5000);
        return () => clearInterval(interval);
    }, [totalSlides]);

    const goToSlide = (index: number) => {
        setCurrentSlide(index);
    };

    // ── Search Logic (text + voice 공통) ─────────────────────────
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

                if (!response.is_in_scope || response.error || response.top3.length === 0) {
                    router.push(
                        `/kioskmode/not-found-result?q=${encodeURIComponent(searchQuery)}`
                    );
                } else {
                    router.push(
                        `/kioskmode/results?q=${encodeURIComponent(searchQuery)}&mode=${inputType}`
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

    // ── Voice: 홈 페이지에서 먼저 음성 인식 (legacy app.js와 동일) ──
    const handleVoiceSearch = useCallback(() => {
        if (isListening) {
            // 이미 듣고 있으면 중지
            recognitionRef.current?.abort();
            setIsListening(false);
            setVoiceLabel("어떤 상품의 위치를 알고 싶으세요?");
            return;
        }

        const SpeechRecognitionClass =
            typeof window !== "undefined"
                ? window.webkitSpeechRecognition || window.SpeechRecognition
                : null;

        if (!SpeechRecognitionClass) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return;
        }

        resetSearch();

        const recognition = new SpeechRecognitionClass();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "ko-KR";

        recognition.onstart = () => {
            setIsListening(true);
            setVoiceLabel("듣고 있어요...");
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
                setVoiceLabel(finalTranscript);
                setIsListening(false);
                // 음성 인식 완료 → 검색 실행 (backend main.py 호출)
                setTimeout(() => {
                    performSearch(finalTranscript, "voice");
                }, 500);
            } else if (interimTranscript) {
                setVoiceLabel(interimTranscript);
            }
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            console.error("Speech recognition error:", event.error);
            setIsListening(false);
            setVoiceLabel(
                event.error === "not-allowed"
                    ? "마이크 접근 권한이 필요합니다."
                    : "음성 인식 오류가 발생했습니다. 다시 시도해 주세요."
            );
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;
        recognition.start();
    }, [isListening, performSearch]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            recognitionRef.current?.abort();
        };
    }, []);

    const showHelp = () => {
        alert('목소리나 텍스트로 상품을 검색해 보세요.\n검색 결과에서 상품을 누르면 위치를 안내해 드립니다.');
    };

    return (
        <main className="flex flex-col min-h-[100dvh] bg-white">
            {/* ── Header (Legacy Style) ── */}
            <header className="header">
                <div className="header-logo">
                    <div className="logo-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="4" y="4" width="7" height="7" fill="white" />
                            <rect x="13" y="4" width="7" height="7" fill="white" />
                            <rect x="4" y="13" width="7" height="7" fill="white" />
                            <rect x="13" y="13" width="7" height="7" fill="transparent" stroke="white" strokeWidth="2" />
                        </svg>
                    </div>
                    <img
                        src="/images/logo.png.png"
                        alt="어디다있소"
                        style={{ height: '36px', objectFit: 'contain' }}
                    />
                </div>
                <div className="header-right">
                    <div className="lang-toggle">
                        <span className="active">KOR</span> / <span>ENG</span>
                    </div>
                    <button className="help-btn" onClick={showHelp}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9 9a3 3 0 015.12-2.13A3 3 0 0113 12.5V14" />
                            <circle cx="12" cy="18" r="0.5" fill="currentColor" />
                        </svg>
                        도움말
                    </button>
                </div>
            </header>

            {/* ── Main Content ── */}
            <div className="main-content overflow-y-auto">
                {/* Carousel Section */}
                <section className="carousel-section">
                    <div
                        className="carousel-track"
                        id="carousel-track"
                        style={{ transform: `translateX(-${currentSlide * 100}%)` }}
                    >
                        {/* Slide 1 */}
                        <div className="carousel-slide">
                            <div className="banner-card">
                                <div className="banner-text">
                                    <h2>오늘의 추천 상품</h2>
                                    <p>다이소는 특별한 추천 상품</p>
                                </div>
                                <div className="banner-products">
                                    {[
                                        { cat: "13세일", price: "3,900원" },
                                        { cat: "13세일", price: "2,900원" },
                                        { cat: "15개입", price: "3,000원" },
                                        { cat: "23세일", price: "3,000원" },
                                    ].map((item, i) => (
                                        <div className="product-thumb" key={i}>
                                            <div style={{ width: '100%', height: '100px', background: '#f5f5f5', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', color: '#999' }}>
                                                상품이미지
                                            </div>
                                            <div className="price-tag">
                                                <span className="category">{item.cat}</span>
                                                <span className="price">{item.price}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        {/* Slide 2 */}
                        <div className="carousel-slide">
                            <div className="banner-card" style={{ background: 'linear-gradient(135deg, #ffe8ec 0%, #ffd1d9 100%)' }}>
                                <div className="banner-text">
                                    <h2>SPRING PROMOTION</h2>
                                    <p>New Arrivals &amp; Special Offers</p>
                                    <p style={{ fontSize: '20px', fontWeight: 700, marginTop: '12px' }}>Visit Us Today!</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="carousel-dots">
                        <div className={`dot ${currentSlide === 0 ? 'active' : ''}`} onClick={() => goToSlide(0)} />
                        <div className={`dot ${currentSlide === 1 ? 'active' : ''}`} onClick={() => goToSlide(1)} />
                    </div>
                </section>

                {/* Voice Search Section */}
                <section className="voice-section">
                    <button
                        className={`mic-button ${isListening ? 'active' : ''}`}
                        id="mic-btn"
                        onClick={handleVoiceSearch}
                        disabled={isSearching}
                    >
                        <div className="mic-ripple" />
                        <div className="mic-ripple" />
                        <div className="mic-ripple" />
                        <svg viewBox="0 0 24 24">
                            <path d="M12 1a4 4 0 00-4 4v6a4 4 0 008 0V5a4 4 0 00-4-4z" />
                            <path d="M19 10v1a7 7 0 01-14 0v-1M12 18.5v3M8 21.5h8" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button>
                    <p className="voice-label">{voiceLabel}</p>
                </section>

                {/* Search Bar */}
                <div className="search-bar">
                    <input
                        type="text"
                        id="search-input"
                        placeholder="어떤 상품의 위치를 알고 싶으세요?"
                        value={query}
                        onChange={(e) => setQueryLocal(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                        autoComplete="off"
                        disabled={isSearching}
                    />
                    <svg
                        className="search-icon"
                        viewBox="0 0 24 24"
                        onClick={handleSearch}
                    >
                        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                </div>
            </div>

            {/* ── Bottom Tab Bar ── */}
            <BottomTabBar />
        </main>
    );
}

