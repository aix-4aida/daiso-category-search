"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import BottomTabBar from "@/components/BottomTabBar";

const API_BASE: string = process.env.NEXT_PUBLIC_API_URL || "/api";

interface Product {
    id: string;
    name: string;
    price: number;
    image_url: string;
    location: {
        floor: string;
        section: string;
        shelf_label: string;
    };
    meta: {
        category_major: string;
        category_middle: string;
    };
}

function formatPrice(price: number): string {
    return `${price.toLocaleString()}원`;
}

const ITEMS_PER_PAGE = 10;

function CategoryProductsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const category = searchParams.get("name") || "";

    const [products, setProducts] = useState<Product[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [currentPage, setCurrentPage] = useState(1);

    useEffect(() => {
        if (!category) return;

        async function fetchProducts() {
            setIsLoading(true);
            try {
                const res = await fetch(`${API_BASE}/search/category?name=${encodeURIComponent(category)}`);
                if (res.ok) {
                    const data = await res.json();
                    setProducts(data.products || []);
                    if (data.products?.length > 0) {
                        setSelectedProduct(data.products[0]);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch category products:", err);
            } finally {
                setIsLoading(false);
            }
        }
        fetchProducts();
    }, [category]);

    const totalPages = Math.ceil(products.length / ITEMS_PER_PAGE);
    const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
    const currentProducts = products.slice(startIdx, startIdx + ITEMS_PER_PAGE);

    const handleBack = useCallback(() => {
        router.back();
    }, [router]);

    const handleSelectProduct = useCallback((product: Product) => {
        setSelectedProduct(product);
    }, []);

    const handlePageChange = useCallback((page: number) => {
        setCurrentPage(page);
        setSelectedProduct(products[(page - 1) * ITEMS_PER_PAGE] || null);
    }, [products]);

    if (isLoading) {
        return (
            <main className="flex flex-col min-h-[100dvh] bg-white items-center justify-center">
                <div className="w-12 h-12 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
                <p style={{ marginTop: 12, fontSize: 14, color: "#999" }}>
                    {category} 상품을 불러오는 중...
                </p>
            </main>
        );
    }

    // 층별 지도
    const selectedFloor = selectedProduct?.location?.floor?.toUpperCase() || "B1";
    const mapSrc = selectedFloor.includes("B2") ? "/images/map_b2.jpg" : "/images/map_b1.jpg";

    // 페이지 번호 목록 (현재 페이지 주변 5개)
    const getPageNumbers = () => {
        const pages: number[] = [];
        let start = Math.max(1, currentPage - 2);
        let end = Math.min(totalPages, start + 4);
        if (end - start < 4) start = Math.max(1, end - 4);
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    };

    return (
        <main className="flex flex-col min-h-[100dvh] bg-[#f5f5f7]">
            {/* Header */}
            <div className="results-header">
                <button className="back-btn" onClick={handleBack}>←</button>
                <h2 className="results-title">
                    <span className="query-highlight">{category}</span> 전체 상품 {products.length}개
                </h2>
            </div>

            {/* 3-Panel Layout */}
            <div className="results-layout">
                {/* Left: Product Cards + Pagination */}
                <div className="results-left-panel" style={{ display: "flex", flexDirection: "column", maxHeight: "calc(100dvh - 140px)", overflow: "hidden" }}>
                    {/* Scrollable product list */}
                    <div style={{ flex: 1, overflowY: "auto" }}>
                        {currentProducts.map((product) => (
                            <div
                                key={product.id}
                                className={`result-card ${selectedProduct?.id === product.id ? "selected" : ""}`}
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
                                            {product.location?.floor || "B1"}
                                        </div>
                                    )}
                                </div>
                                <div className="result-info">
                                    <div className="card-tag">{product.meta?.category_middle || product.meta?.category_major || "일반"}</div>
                                    <h3 className="result-title">{product.name}</h3>
                                    <div className="result-location">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                                        </svg>
                                        {product.location?.floor || "B1"}-{product.location?.section || ""} {product.location?.shelf_label || ""}
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

                    {/* Pagination - fixed at bottom */}
                    {totalPages > 1 && (
                        <div style={{
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            gap: 4,
                            padding: "10px 8px",
                            flexWrap: "wrap",
                            borderTop: "1px solid #e5e5e5",
                            background: "#fff",
                            flexShrink: 0,
                        }}>
                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                style={{
                                    padding: "6px 10px",
                                    border: "1px solid #ddd",
                                    borderRadius: 6,
                                    background: currentPage === 1 ? "#f0f0f0" : "#fff",
                                    color: currentPage === 1 ? "#bbb" : "#333",
                                    cursor: currentPage === 1 ? "not-allowed" : "pointer",
                                    fontSize: 13,
                                    fontWeight: 600,
                                }}
                            >
                                ◀ 이전
                            </button>

                            {getPageNumbers().map((page) => (
                                <button
                                    key={page}
                                    onClick={() => handlePageChange(page)}
                                    style={{
                                        padding: "6px 10px",
                                        border: page === currentPage ? "2px solid #E50000" : "1px solid #ddd",
                                        borderRadius: 6,
                                        background: page === currentPage ? "#E50000" : "#fff",
                                        color: page === currentPage ? "#fff" : "#333",
                                        cursor: "pointer",
                                        fontSize: 13,
                                        fontWeight: page === currentPage ? 700 : 400,
                                        minWidth: 36,
                                    }}
                                >
                                    {page}
                                </button>
                            ))}

                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                style={{
                                    padding: "6px 10px",
                                    border: "1px solid #ddd",
                                    borderRadius: 6,
                                    background: currentPage === totalPages ? "#f0f0f0" : "#fff",
                                    color: currentPage === totalPages ? "#bbb" : "#333",
                                    cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                                    fontSize: 13,
                                    fontWeight: 600,
                                }}
                            >
                                다음 ▶
                            </button>

                            <div style={{ width: "100%", textAlign: "center", fontSize: 11, color: "#999", marginTop: 4 }}>
                                {currentPage} / {totalPages} 페이지 ({startIdx + 1}~{Math.min(startIdx + ITEMS_PER_PAGE, products.length)} / {products.length}개)
                            </div>
                        </div>
                    )}
                </div>

                {/* Center: Map */}
                <div className="results-center-panel">
                    {selectedProduct && (
                        <div className="store-map-container">
                            <div className="store-map-header">
                                <span className="store-map-floor-label">{selectedFloor}</span>
                                <div style={{ fontSize: 13, color: "#666", marginLeft: 8 }}>
                                    {selectedProduct.name}
                                </div>
                            </div>
                            <div className="store-map-svg-wrapper">
                                <img
                                    src={mapSrc}
                                    alt={`${selectedFloor} 층 매장 지도`}
                                    style={{
                                        width: "100%",
                                        height: "100%",
                                        objectFit: "contain",
                                        borderRadius: 8,
                                    }}
                                />
                            </div>
                            <div className="store-map-footer">
                                위치: <strong>{selectedProduct.location?.shelf_label || selectedProduct.location?.section || "매장 내"}</strong>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Product Detail */}
                <div className="results-right-panel">
                    {selectedProduct && (
                        <div className="qr-section">
                            <h4>{selectedProduct.name}</h4>
                            <div style={{ marginTop: 8, fontSize: 20, fontWeight: 800, color: "#E50000" }}>
                                {formatPrice(selectedProduct.price)}
                            </div>
                            <div style={{ marginTop: 12, fontSize: 13, color: "#666" }}>
                                <div>📂 {selectedProduct.meta?.category_major || ""}</div>
                                {selectedProduct.meta?.category_middle && (
                                    <div> └ {selectedProduct.meta.category_middle}</div>
                                )}
                                <div style={{ marginTop: 8 }}>
                                    📍 {selectedProduct.location?.floor || "B1"} / {selectedProduct.location?.shelf_label || "매장 내"}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <BottomTabBar />
        </main>
    );
}

export default function CategoryProductsPage() {
    return (
        <Suspense
            fallback={
                <main className="flex min-h-screen items-center justify-center bg-gray-50">
                    <div className="w-12 h-12 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
                </main>
            }
        >
            <CategoryProductsContent />
        </Suspense>
    );
}
