import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { MapPin, Search, ArrowLeft, QrCode, Home } from 'lucide-react'
import Layout from '../components/Layout'
import Button from '../components/Button'
import SimpleMap from '../components/SimpleMap'
import { searchProducts, getProductsByCategory, processTextSearch } from '../lib/api'
import { mapConfig, findProductLocation } from '../config/mapConfig'

const SearchResults = () => {
    const router = useRouter()
    const { q: query, category, source } = router.query

    // In Next.js pages router, router.query might be empty on first render
    // Use effective query to trigger effects
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedProduct, setSelectedProduct] = useState(null)
    const [pipelineKeyword, setPipelineKeyword] = useState(null)

    useEffect(() => {
        if (!router.isReady) return

        const fetchData = async () => {
            setLoading(true)
            let data = []

            // 1. Voice Search Results (Loaded from LocalStorage)
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
            // 2. Text Search (Pipeline) - New Feature
            else if (source === 'text' && query) {
                try {
                    console.log("Processing text search pipeline:", query);
                    const resp = await processTextSearch(query);
                    if (resp.results) {
                        data = resp.results;
                        setPipelineKeyword(resp.keyword);
                    }
                } catch (e) {
                    console.error("Text pipeline failed:", e);
                    // Fallback to simple SQL search
                    data = await searchProducts(query);
                }
            }
            // 3. Normal Search (SQL LIKE) or Category
            else {
                if (query) {
                    data = await searchProducts(query)
                } else if (category) {
                    data = await getProductsByCategory(category)
                }
            }

            setResults(data)
            if (data.length > 0) setSelectedProduct(data[0])
            setLoading(false)
        }
        fetchData()
    }, [router.isReady, query, category, source])

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
