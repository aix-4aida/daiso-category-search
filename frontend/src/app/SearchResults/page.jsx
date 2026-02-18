'use client';

import React, { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { MapPin, Search, ArrowLeft, QrCode, Home } from 'lucide-react'
import Layout from '../../components/Layout'
import Button from '../../components/Button'
import SimpleMap from '../../components/SimpleMap'
import { searchProducts, getProductsByCategory, processTextSearch } from '../../lib/api'

const SearchResultsPage = () => {
    const router = useRouter()
    const searchParams = useSearchParams()

    // Get params safely
    const query = searchParams.get('q')
    const category = searchParams.get('category')
    const source = searchParams.get('source')

    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedProduct, setSelectedProduct] = useState(null)
    const [pipelineKeyword, setPipelineKeyword] = useState(null)

    useEffect(() => {
        // App Router useEffect runs on client, params are available
        const fetchData = async () => {
            setLoading(true)
            let data = []

            // 1. Voice Search Results
            if (source === 'voice') {
                try {
                    const storedResults = localStorage.getItem('voiceSearchResults');
                    if (storedResults) {
                        data = JSON.parse(storedResults);
                    }
                } catch (e) {
                    console.error("Failed to load voice results:", e);
                }
            }
            // 2. Text Search (Pipeline)
            else if (source === 'text' && query) {
                try {
                    const resp = await processTextSearch(query);
                    if (resp.results) {
                        data = resp.results;
                        setPipelineKeyword(resp.keyword);
                    }
                } catch (e) {
                    console.error("Text pipeline failed:", e);
                    data = await searchProducts(query);
                }
            }
            // 3. Normal Search
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
    }, [query, category, source])

    const handleProductSelect = (product) => {
        setSelectedProduct(product)
    }

    return (
        <Layout className="bg-gray-50 h-screen flex flex-col overflow-hidden">
            {/* Header */}
            <header className="bg-white px-6 py-4 flex items-center justify-between shadow-sm shrink-0 z-10">
                <button
                    onClick={() => router.back()}
                    className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full"
                >
                    <ArrowLeft size={24} />
                </button>
                <h1 className="text-lg font-bold text-gray-800 truncate max-w-[200px]">
                    {pipelineKeyword ? `"${pipelineKeyword}" 검색결과` :
                        query ? `"${query}" 검색결과` :
                            category ? category : '검색 결과'}
                </h1>
                <div className="w-10"></div> {/* Spacer for centering */}
            </header>

            <div className="flex-1 flex overflow-hidden relative">
                {/* Left Panel: Product List */}
                <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col z-20 shadow-lg">
                    <div className="p-4 border-b bg-gray-50">
                        <p className="text-sm text-gray-500">
                            총 <span className="font-bold text-daiso-red">{results.length}</span>개의 상품을 찾았습니다
                        </p>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {loading ? (
                            <div className="flex justify-center py-10">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-daiso-red"></div>
                            </div>
                        ) : results.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                                <Search size={48} className="mb-4 opacity-20" />
                                <p>검색 결과가 없습니다</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-100">
                                {results.map((product) => (
                                    <div
                                        key={product.id}
                                        onClick={() => handleProductSelect(product)}
                                        className={`p-4 cursor-pointer transition-colors hover:bg-red-50 relative ${selectedProduct?.id === product.id ? 'bg-red-50 border-l-4 border-daiso-red' : ''
                                            }`}
                                    >
                                        <div className="flex gap-3">
                                            {/* Thumbnail */}
                                            <div className="w-16 h-16 bg-gray-200 rounded-lg shrink-0 overflow-hidden">
                                                {product.image_url ? (
                                                    <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">No Img</div>
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className={`font-medium text-sm mb-1 truncate ${selectedProduct?.id === product.id ? 'text-daiso-red' : 'text-gray-800'
                                                    }`}>
                                                    {product.name}
                                                </h3>
                                                <p className="text-xs text-gray-500 mb-1">
                                                    {product.category_major} {'>'} {product.category_middle}
                                                </p>
                                                <p className="text-sm font-bold">
                                                    {product.price?.toLocaleString()}원
                                                </p>
                                            </div>
                                        </div>
                                        {/* Location Badge */}
                                        <div className="mt-2 inline-flex items-center px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-600">
                                            <MapPin size={12} className="mr-1" />
                                            {product.location || '위치 정보 없음'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Map & Details */}
                <div className="flex-1 bg-gray-50 p-6 flex flex-col overflow-y-auto">
                    {selectedProduct ? (
                        <div className="flex flex-col h-full space-y-6">
                            {/* Map View */}
                            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-1 flex-1 min-h-[400px]">
                                <SimpleMap
                                    targetLocation={selectedProduct.location || selectedProduct.name}
                                    productName={selectedProduct.name}
                                />
                            </div>

                            {/* Action Bar */}
                            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 flex items-center justify-between shrink-0">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800 mb-1">{selectedProduct.name}</h2>
                                    <p className="text-gray-500">
                                        {selectedProduct.location ? `${selectedProduct.location} 구역에 있습니다` : '직원에게 문의해주세요'}
                                    </p>
                                </div>
                                <div className="flex gap-3">
                                    <Button variant="secondary" onClick={() => router.push('/')}>
                                        <Home size={20} className="mr-2" />
                                        홈으로
                                    </Button>
                                    <Button onClick={() => alert('모바일 안내를 시작합니다')}>
                                        <QrCode size={20} className="mr-2" />
                                        모바일로 안내받기
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                            <MapPin size={64} className="mb-4 opacity-20" />
                            <p className="text-lg">상품을 선택하면 위치를 확인할 수 있습니다</p>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    )
}

export default SearchResultsPage
