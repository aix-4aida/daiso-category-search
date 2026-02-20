"use client";

import { useCallback, useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import { findShelfByCategory, floorMaps } from "@/lib/mapData";
import BottomTabBar from "@/components/BottomTabBar";

function NavigateContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const location = searchParams.get("location") || "매장 내";
    const product = searchParams.get("product") || "";
    const productId = searchParams.get("product_id") || "";
    const price = searchParams.get("price") || "";
    const qrPayload = searchParams.get("qr") || "";
    const categoryMajor = searchParams.get("category_major") || "";
    const categoryMiddle = searchParams.get("category_middle") || "";

    // Resolve shelf location from category
    const shelf = findShelfByCategory(categoryMajor, categoryMiddle);
    const mapImage = floorMaps[shelf.floor];

    // Build mobile guide URL for QR code
    const mobileUrl = useMemo(() => {
        const origin = typeof window !== "undefined" ? window.location.origin : "";
        const mobileParams = new URLSearchParams({
            product: product,
            location: shelf.section,
            product_id: productId,
            floor: shelf.floor,
        });
        return `${origin}/mobile/map?${mobileParams.toString()}`;
    }, [product, productId, shelf.section, shelf.floor]);

    const handleBack = useCallback(() => {
        router.back();
    }, [router]);

    const handleGoHome = useCallback(() => {
        router.push("/kioskmode");
    }, [router]);

    const handleMobileGuide = useCallback(() => {
        navigator.clipboard?.writeText(mobileUrl).catch(() => {});
        alert(`모바일 안내 URL이 클립보드에 복사되었습니다.\n\n${mobileUrl}`);
    }, [mobileUrl]);

    return (
        <main className="flex min-h-[100dvh] flex-col bg-gray-50 pb-20">
            {/* Header */}
            <header className="w-full bg-white px-6 py-4 border-b border-gray-100">
                <button
                    onClick={handleBack}
                    className="flex items-center gap-1.5 text-gray-700 hover:text-gray-900 cursor-pointer transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-400 rounded-md px-2 py-1 -ml-2"
                    aria-label="뒤로 가기"
                >
                    <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        <polyline points="15 18 9 12 15 6" />
                    </svg>
                    <span className="text-sm font-medium">뒤로</span>
                </button>
            </header>

            {/* Content */}
            <div className="flex-1 px-4 sm:px-6 py-6">
                <div className="max-w-5xl mx-auto flex flex-col lg:flex-row gap-6">
                    {/* Left: Store Map */}
                    <div className="flex-1">
                        <article className="bg-white rounded-2xl shadow-sm p-6 h-full">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-bold text-gray-900">
                                    매장 지도
                                </h2>
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-blue-100 text-blue-700">
                                    {shelf.floor}
                                </span>
                            </div>

                            {/* Floor Plan with Pin */}
                            <div
                                className="relative w-full rounded-xl overflow-hidden bg-gray-100 mb-4"
                                role="img"
                                aria-label={`매장 지도 ${shelf.floor} — ${shelf.section} 위치 표시`}
                            >
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                    src={mapImage}
                                    alt={`${shelf.floor} 매장 도면`}
                                    className="w-full h-auto block"
                                />

                                {/* Pin Marker */}
                                <div
                                    className="absolute"
                                    style={{
                                        left: `${shelf.x}%`,
                                        top: `${shelf.y}%`,
                                        transform: "translate(-50%, -100%)",
                                    }}
                                >
                                    {/* Ping animation (outer ring) */}
                                    <span
                                        className="absolute inline-flex h-8 w-8 rounded-full bg-red-400 opacity-75 animate-ping"
                                        style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}
                                    />
                                    {/* Pin icon */}
                                    <svg
                                        width="32"
                                        height="40"
                                        viewBox="0 0 24 30"
                                        className="relative z-10 drop-shadow-lg"
                                    >
                                        <path
                                            d="M12 0C5.4 0 0 5.4 0 12c0 9 12 18 12 18s12-9 12-18C24 5.4 18.6 0 12 0z"
                                            fill="#EF4444"
                                        />
                                        <circle cx="12" cy="11" r="4.5" fill="white" />
                                    </svg>
                                </div>
                            </div>

                            {/* Legend */}
                            <div className="flex items-center justify-center gap-6">
                                <div className="flex items-center gap-2">
                                    <span
                                        className="w-3 h-3 rounded-full bg-red-500 inline-block"
                                        aria-hidden="true"
                                    />
                                    <span className="text-sm text-gray-600">
                                        {shelf.section}
                                    </span>
                                </div>
                            </div>
                        </article>
                    </div>

                    {/* Right: Navigation Info */}
                    <div className="lg:w-80">
                        <div className="bg-white rounded-2xl shadow-sm p-6 flex flex-col items-center">
                            {/* Location Title */}
                            <div className="flex items-center gap-2 mb-2">
                                <svg
                                    width="24"
                                    height="24"
                                    viewBox="0 0 24 24"
                                    fill="#EF4444"
                                    aria-hidden="true"
                                >
                                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                                </svg>
                                <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                                    {shelf.section}
                                </h2>
                            </div>

                            {/* Floor badge */}
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 mb-3">
                                {shelf.floor} / {shelf.id}
                            </span>

                            {/* Product Name */}
                            {product && (
                                <p className="text-sm text-gray-500 mb-1 text-center">
                                    {product}
                                </p>
                            )}

                            {/* Price */}
                            {price && (
                                <p className="text-lg font-bold text-red-600 mb-4">
                                    ₩{Number(price).toLocaleString()}
                                </p>
                            )}

                            {/* QR Code */}
                            <div
                                className="bg-white rounded-xl p-4 mb-4"
                                role="img"
                                aria-label="QR 코드 - 스마트폰으로 스캔하여 지도 안내 받기"
                            >
                                <QRCodeSVG
                                    value={mobileUrl}
                                    size={192}
                                    level="M"
                                    bgColor="#ffffff"
                                    fgColor="#111111"
                                />
                            </div>

                            {/* QR Info Text */}
                            <div className="bg-red-50 rounded-lg px-4 py-3 mb-6 w-full">
                                <p className="text-xs sm:text-sm text-red-600 text-center leading-relaxed">
                                    <svg
                                        width="14"
                                        height="14"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        className="inline-block mr-1 -mt-0.5"
                                        aria-hidden="true"
                                    >
                                        <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
                                        <line x1="12" y1="18" x2="12.01" y2="18" />
                                    </svg>
                                    QR 코드를 스캔하면 스마트폰으로 지도를 보며 이동할 수 있어요!
                                </p>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-3 w-full">
                                <button
                                    onClick={handleGoHome}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 border-gray-300 text-gray-700 font-medium cursor-pointer transition-all duration-200 hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
                                >
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        aria-hidden="true"
                                    >
                                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                                        <polyline points="9 22 9 12 15 12 15 22" />
                                    </svg>
                                    처음으로
                                </button>
                                <button
                                    onClick={handleMobileGuide}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-red-600 text-white font-medium cursor-pointer transition-all duration-200 hover:bg-red-700 active:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2"
                                >
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        aria-hidden="true"
                                    >
                                        <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
                                        <line x1="12" y1="18" x2="12.01" y2="18" />
                                    </svg>
                                    모바일로 안내받기
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <BottomTabBar />
        </main>
    );
}

export default function NavigatePage() {
    return (
        <Suspense
            fallback={
                <main className="flex min-h-screen items-center justify-center bg-gray-50">
                    <div className="w-12 h-12 border-4 border-red-400 border-t-transparent rounded-full animate-spin" />
                </main>
            }
        >
            <NavigateContent />
        </Suspense>
    );
}
