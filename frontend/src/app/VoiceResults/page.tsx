'use client';

import React, { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, Star, Package, Home } from 'lucide-react'
import Layout from '../../components/Layout'

const getBaseUrl = () => {
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        return `http://${hostname}:8000/api`;
    }
    return 'http://localhost:8000/api';
};

const VoiceResults = () => {
    const router = useRouter()
    const searchParams = useSearchParams()
    const queryParam = searchParams?.get('q') || ''

    const [selectedItem, setSelectedItem] = useState<any>(null)
    const [otherItems, setOtherItems] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [query, setQuery] = useState(queryParam)

    useEffect(() => {
        const loadRerankedResults = async () => {
            setLoading(true)
            try {
                const storedReranked = localStorage.getItem('voiceRerankedResults')
                const storedKeyword = localStorage.getItem('voiceSearchKeyword')

                if (storedKeyword) setQuery(storedKeyword)

                if (!storedReranked) {
                    router.replace(`/SearchResults?q=${encodeURIComponent(storedKeyword || queryParam)}&source=voice`)
                    return
                }

                const reranked = JSON.parse(storedReranked)
                if (!reranked || reranked.length === 0) {
                    router.replace(`/SearchResults?q=${encodeURIComponent(storedKeyword || queryParam)}&source=voice`)
                    return
                }

                const first = reranked[0]
                const selectedIdStr = first.selected_id || ''
                const retrievedIds = first.retrieved_ids || []
                const reason = first.reason || ''

                const parseId = (str: string) => {
                    if (!str) return null
                    const match = str.match(/^(\d+)/)
                    return match ? parseInt(match[1]) : null
                }

                const parseName = (str: string) => {
                    if (!str) return ''
                    const match = str.match(/\((.+)\)/)
                    return match ? match[1] : str
                }

                const fetchProduct = async (id: number) => {
                    try {
                        const resp = await fetch(`${getBaseUrl()}/products/${id}`)
                        if (resp.ok) return await resp.json()
                    } catch (e) {
                        console.error(`Failed to fetch product ${id}:`, e)
                    }
                    return null
                }

                // Fetch selected product
                const selectedId = parseId(selectedIdStr)
                let selectedProduct = null
                if (selectedId) {
                    selectedProduct = await fetchProduct(selectedId)
                }

                const selected = {
                    id: selectedId,
                    name: selectedProduct?.name || parseName(selectedIdStr),
                    price: selectedProduct?.price || 0,
                    location: selectedProduct?.location || '',
                    image_url: selectedProduct?.image_url || '',
                    reason: reason,
                    product: selectedProduct
                }

                // Fetch other products
                const others: any[] = []
                for (const idStr of retrievedIds) {
                    if (idStr === selectedIdStr) continue
                    const pid = parseId(idStr)
                    if (!pid) continue

                    const product = await fetchProduct(pid)
                    others.push({
                        id: pid,
                        name: product?.name || parseName(idStr),
                        price: product?.price || 0,
                        location: product?.location || '',
                        image_url: product?.image_url || '',
                        product: product
                    })

                    if (others.length >= 2) break
                }

                setSelectedItem(selected)
                setOtherItems(others)
            } catch (e) {
                console.error('Error loading reranked results:', e)
            } finally {
                setLoading(false)
            }
        }

        loadRerankedResults()
    }, [])

    const handleProductClick = (item: any) => {
        const productName = item.product?.name || item.name
        if (item.product) {
            localStorage.setItem('voiceSearchResults', JSON.stringify([item.product]))
        }
        router.push(`/SearchResults?q=${encodeURIComponent(productName)}&source=voice`)
    }

    if (loading) {
        return (
            <Layout className="items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-daiso-red mx-auto mb-4"></div>
                    <div className="text-xl text-gray-600 font-medium">AI가 최적의 상품을 찾고 있습니다...</div>
                </div>
            </Layout>
        )
    }

    if (!selectedItem) {
        return (
            <Layout className="items-center justify-center">
                <div className="text-center text-gray-500">
                    <p>결과가 없습니다.</p>
                    <button onClick={() => router.push('/')} className="mt-4 px-6 py-2 bg-daiso-red text-white rounded-lg">
                        홈으로
                    </button>
                </div>
            </Layout>
        )
    }

    return (
        <Layout className="bg-gray-50 p-6 relative">
            {/* Back Button */}
            <div className="absolute top-6 left-6 z-10">
                <button
                    onClick={() => router.back()}
                    className="flex items-center text-gray-600 font-medium hover:text-gray-800 transition-colors"
                >
                    <ArrowLeft className="mr-2" size={20} /> 뒤로
                </button>
            </div>

            {/* Home Button */}
            <div className="absolute top-6 right-6 z-10">
                <button
                    onClick={() => router.push('/')}
                    className="flex items-center gap-2 px-4 py-2 bg-daiso-red text-white rounded-lg font-medium hover:bg-red-700 transition-colors shadow-sm"
                >
                    <Home size={18} /> 홈으로
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col items-center justify-center">
                <div className="w-full max-w-2xl flex flex-col items-center space-y-6">
                    {/* Title */}
                    <div className="text-center space-y-2 pt-8">
                        <h1 className="text-3xl font-bold text-gray-900">이 상품을 찾으시나요?</h1>
                        <p className="text-gray-500">&quot;{query}&quot; 검색 결과입니다. 원하시는 상품을 선택해주세요.</p>
                    </div>

                    {/* Best Match - Large Card */}
                    <div
                        onClick={() => handleProductClick(selectedItem)}
                        className="w-full bg-white border-2 border-daiso-red rounded-2xl p-6 shadow-lg cursor-pointer hover:shadow-xl transition-all hover:scale-[1.01] relative overflow-hidden"
                    >
                        <div className="absolute top-0 left-0 bg-daiso-red text-white text-xs font-bold px-4 py-1.5 rounded-br-xl flex items-center gap-1">
                            <Star size={14} fill="white" /> Best Match
                        </div>

                        <div className="flex items-center pt-4">
                            <div className="w-32 h-32 bg-gray-100 rounded-xl mr-6 shrink-0 overflow-hidden flex items-center justify-center">
                                {selectedItem.image_url ? (
                                    <img src={selectedItem.image_url} alt={selectedItem.name} className="w-full h-full object-cover" />
                                ) : (
                                    <Package size={48} className="text-gray-300" />
                                )}
                            </div>
                            <div className="flex-1">
                                <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedItem.name}</h2>
                                {selectedItem.price > 0 && (
                                    <p className="text-xl font-bold text-daiso-red mb-2">{selectedItem.price.toLocaleString()}원</p>
                                )}
                                {selectedItem.location && (
                                    <p className="text-sm text-gray-500 mb-2">📍 {selectedItem.location}</p>
                                )}

                            </div>
                        </div>
                    </div>

                    {/* Other Candidates - Half Size */}
                    {otherItems.length > 0 && (
                        <div className="w-full grid grid-cols-2 gap-4">
                            {otherItems.map((item: any, index: number) => (
                                <div
                                    key={item.id || index}
                                    onClick={() => handleProductClick(item)}
                                    className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md hover:border-gray-400 transition-all hover:scale-[1.02]"
                                >
                                    <div className="w-full h-20 bg-gray-100 rounded-lg mb-3 overflow-hidden flex items-center justify-center">
                                        {item.image_url ? (
                                            <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                                        ) : (
                                            <Package size={32} className="text-gray-300" />
                                        )}
                                    </div>
                                    <h3 className="text-sm font-bold text-gray-800 truncate mb-1">{item.name}</h3>
                                    {item.price > 0 && (
                                        <p className="text-sm font-bold text-gray-600">{item.price.toLocaleString()}원</p>
                                    )}
                                    {item.location && (
                                        <p className="text-xs text-gray-400 mt-1">📍 {item.location}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Skip Button */}
                    <button
                        onClick={() => router.push(`/SearchResults?q=${encodeURIComponent(query)}&source=voice`)}
                        className="text-gray-400 text-sm hover:text-gray-600 transition-colors underline mt-2"
                    >
                        원하는 상품이 없나요? 전체 검색결과 보기
                    </button>
                </div>
            </div>
        </Layout>
    )
}

export default VoiceResults
