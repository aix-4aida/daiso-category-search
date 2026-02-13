import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { MapPin, Search, ArrowLeft, QrCode, Home } from 'lucide-react'
import Layout from '../components/Layout'
import Button from '../components/Button'
import { searchProducts, getProductsByCategory } from '../lib/api'
import { mapConfig, findProductLocation } from '../config/mapConfig'

const SimpleMap = ({ targetLocation, productName }) => {
    // Find target shelf based on location (from DB) or product name
    const target = findProductLocation(targetLocation || productName)

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

    const renderMapFloor = (floor, imgSrc, title, startLabel, startPos, startPointStr) => {
        const ratio = ratios[floor];
        const viewBoxHeight = 100 * ratio;

        // Target is valid only if it's on the current floor
        const isTargetOnFloor = target && target.floor === floor;
        const pathData = isTargetOnFloor ? getPath(floor, target) : "";

        return (
            <div className="flex-1 bg-white border border-gray-200 rounded-xl relative flex flex-col overflow-hidden shadow-sm h-full">
                <div className="absolute top-3 left-4 z-20 bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full shadow-sm border border-gray-100">
                    <span className="text-2xl font-black text-gray-800">{floor}</span>
                </div>

                {/* Container for Image & SVG - Centered and constrained */}
                <div className="relative w-full flex flex-col items-center">
                    <h3 className="text-lg font-bold mb-2 flex items-center">
                        <span className="text-blue-600 text-2xl mr-2">{floor}</span>
                        {title}
                    </h3>
                    <div className="relative w-full flex items-center justify-center bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
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
        <div className="flex gap-4 w-full h-full">
            {renderMapFloor("B1", "/map_b1.jpg", "B1", "현재위치", { x: 50, y: 15 })}
            {renderMapFloor("B2", "/map_b2.jpg", "B2", "계단입구", { x: 25, y: 90 })}
        </div>
    );
};

const SearchResults = () => {
    const router = useRouter()
    const { q: query, category, source } = router.query

    // In Next.js pages router, router.query might be empty on first render
    // Use effective query to trigger effects
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedProduct, setSelectedProduct] = useState(null)

    useEffect(() => {
        if (!router.isReady) return

        const fetchData = async () => {
            setLoading(true)
            let data = []

            // Check if this is a voice search result
            if (source === 'voice') {
                try {
                    const storedResults = localStorage.getItem('voiceSearchResults');
                    if (storedResults) {
                        data = JSON.parse(storedResults);
                        console.log("Loaded voice results:", data);
                    }
                } catch (e) {
                    console.error("Failed to load voice results:", e);
                }
            }

            // Fallback to normal search if no voice data or not voice search
            if (data.length === 0) {
                if (query) {
                    // Determine if query is JSON string (from VoiceSearch mostly) or plain text
                    let searchQuery = query
                    try {
                        // Start with basic check if it looks like JSON
                        if (typeof query === 'string' && (query.startsWith('{') || query.startsWith('['))) {
                            // Attempt to parse if needed, though usually we pass plain string now
                            // But if we passed complex object in query, we handle it
                            // For now assume query is string from VoiceSearch plain text
                        }
                    } catch (e) {
                        // specific handling if needed
                    }

                    data = await searchProducts(searchQuery)
                } else if (category) {
                    data = await getProductsByCategory(category)
                }
            }

            setResults(data)
            if (data.length > 0) setSelectedProduct(data[0])
            setLoading(false)
        }
        fetchData()
    }, [router.isReady, query, category])

    const handleProductSelect = (product) => {
        setSelectedProduct(product)
    }

    if (loading) {
        return (
            <Layout className="bg-white items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-daiso-red mx-auto mb-4"></div>
                    <div className="text-xl text-gray-600 font-medium">상품을 찾고 있습니다...</div>
                </div>
            </Layout>
        )
    }

    if (results.length === 0) {
        return (
            <Layout className="bg-white">
                <header className="p-4 border-b flex items-center">
                    <button onClick={() => router.push('/')} className="mr-4"><ArrowLeft /></button>
                    <h1 className="text-xl font-bold">검색 결과</h1>
                </header>
                <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                    <Search size={48} className="mb-4 opacity-20" />
                    <p>검색 결과가 없습니다.</p>
                </div>
            </Layout>
        )
    }

    return (
        <Layout className="bg-gray-50 h-screen overflow-hidden flex flex-col">
            {/* Header */}
            <header className="bg-white border-b px-6 py-3 flex items-center shrink-0">
                <button onClick={() => router.push('/')} className="mr-4 text-gray-600 hover:text-daiso-red transition-colors">
                    <ArrowLeft size={24} />
                </button>
                <div className="flex items-center text-2xl font-bold text-daiso-red">
                    어디다이소
                </div>
                <div className="ml-auto flex items-center gap-3">
                    <button
                        onClick={() => router.push('/')}
                        className="flex items-center gap-2 px-4 py-2 bg-daiso-red text-white rounded-lg font-medium hover:bg-red-700 transition-colors shadow-sm text-sm"
                    >
                        <Home size={16} /> 홈으로
                    </button>
                </div>
            </header>

            {/* Main Content (Split View) */}
            <div className="flex-1 flex overflow-hidden">

                {/* Left Side: Product List */}
                <div className="w-[320px] bg-white border-r flex flex-col shrink-0 z-10 shadow-lg">
                    <div className="p-4 border-b">
                        <h2 className="text-lg font-bold text-gray-800">검색 결과 {results.length}개</h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-3">
                        {results.map((product, index) => {
                            const isSelected = selectedProduct && selectedProduct.id === product.id
                            const isFirst = index === 0

                            return (
                                <div
                                    key={product.id}
                                    onClick={() => handleProductSelect(product)}
                                    className={`
                                        cursor-pointer rounded-xl transition-all duration-200 border-2 relative overflow-hidden p-3
                                        ${isSelected
                                            ? 'border-daiso-red bg-red-50 shadow-md'
                                            : 'border-gray-100 bg-white hover:border-gray-300'
                                        }
                                    `}
                                >
                                    {isFirst && <div className="absolute top-0 left-0 bg-daiso-red text-white text-[10px] font-bold px-2 py-0.5 rounded-br-lg">Best Match</div>}

                                    <div className="flex items-center">
                                        <div className="w-16 h-16 bg-gray-200 rounded-lg mr-3 shrink-0 overflow-hidden flex items-center justify-center">
                                            {product.image_url ? (
                                                <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                                            ) : (
                                                <span className="text-gray-400 text-[10px]">No Image</span>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className={`font-bold truncate text-sm ${isSelected ? 'text-daiso-red' : 'text-gray-800'}`}>
                                                {index + 1}. {product.name}
                                            </h3>
                                            <div className="flex items-center text-xs text-red-500 mb-1">
                                                <MapPin size={12} className="mr-1" />
                                                {product.location || findProductLocation(product.name)?.section}
                                            </div>
                                            <div className="font-bold text-gray-900 text-sm">
                                                {product.price?.toLocaleString()}원
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    {/* QR Code / Action Area */}
                    <div className="p-4 bg-gray-50 border-t">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="bg-white p-1.5 rounded-lg shadow-sm">
                                <QrCode size={60} />
                            </div>
                            <div className="text-xs text-gray-600">
                                <div className="font-bold mb-0.5">스마트폰으로 스캔</div>
                                <div>지도를 저장해서<br />쇼핑하세요!</div>
                            </div>
                        </div>
                        <Button className="w-full bg-yellow-400 hover:bg-yellow-500 text-black border-none font-bold rounded-lg h-10 text-sm shadow-sm">
                            카카오 보내기
                        </Button>
                    </div>
                </div>

                {/* Right Side: Map Visualization */}
                <div className="flex-1 bg-gray-100 p-4 relative flex flex-col">
                    {selectedProduct && (
                        <div className="bg-white/95 backdrop-blur-sm px-4 py-2 rounded-full shadow-md mb-3 border border-gray-200 inline-flex items-center w-fit">
                            <span className="text-gray-500 text-sm font-medium mr-2">선택된 상품:</span>
                            <span className="text-daiso-red font-bold">{selectedProduct.name}</span>
                            <span className="mx-2 text-gray-300">|</span>
                            <span className="text-gray-800 font-bold text-sm">{selectedProduct.location || findProductLocation(selectedProduct.name)?.section}</span>
                        </div>
                    )}

                    <div className="flex-1 bg-white rounded-2xl shadow-lg overflow-hidden p-4 border border-gray-200">
                        <SimpleMap
                            targetLocation={selectedProduct?.location}
                            productName={selectedProduct?.name}
                        />
                    </div>
                </div>

            </div>
        </Layout>
    )
}

export default SearchResults
