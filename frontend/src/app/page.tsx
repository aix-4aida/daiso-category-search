'use client';

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { HelpCircle, Search } from 'lucide-react'
import Layout from '../components/Layout'
import { getCategories } from '../lib/api'
import { useUnifiedSearch } from '../hooks/useUnifiedSearch'

export default function Home() {
    const router = useRouter()
    const [query, setQuery] = useState('')
    const [categories, setCategories] = useState<{ id: string, name: string }[]>([])

    // Load categories from API on mount
    useEffect(() => {
        const fetchCats = async () => {
            const data = await getCategories();
            if (data && data.categories) {
                setCategories(data.categories);
            }
        };
        fetchCats();
    }, []);

    const handleVoiceClick = () => {
        router.push('/VoiceSearch')
    }

    const { handleSearch, isLoading } = useUnifiedSearch();

    const onSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (query.trim()) {
            handleSearch(query, 'text');
        }
    }

    return (
        <Layout className="items-center justify-center p-6 relative">
            {/* Top Left Logo (Red Square) */}
            <div className="absolute top-6 left-6 w-12 h-12 bg-daiso-red rounded-md"></div>

            {/* Top Right placeholder */}
            <div className="absolute top-6 right-6 w-24 h-8 bg-gray-100 rounded-full"></div>

            <div className="w-full max-w-lg flex flex-col items-center space-y-10 pt-16">
                {/* Title Section */}
                <div className="text-center space-y-4">
                    <h1 className="text-5xl font-bold text-daiso-red tracking-tight">어디다있소?</h1>
                    <p className="text-xl text-gray-500 font-medium">찾으시는 상품을 말씀해주세요</p>
                </div>

                {/* Big Voice Button */}
                <button
                    onClick={handleVoiceClick}
                    className="w-40 h-40 bg-daiso-red rounded-full flex items-center justify-center shadow-lg hover:bg-red-700 transition-transform hover:scale-105 active:scale-95"
                >
                    <HelpCircle size={64} color="white" strokeWidth={1.5} />
                </button>

                {/* Search Input (New Feature) */}
                <form onSubmit={onSearch} className="w-full relative">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="텍스트로 검색하려면 입력하세요..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="w-full h-14 pl-12 pr-6 rounded-full bg-gray-100 text-lg focus:outline-none focus:ring-2 focus:ring-daiso-red transition-shadow"
                        />
                    </div>
                </form>

                {/* Dynamic Categories */}
                <div className="w-full">
                    <h3 className="text-sm text-gray-400 font-medium mb-3 ml-1">추천 카테고리</h3>
                    <div className="grid grid-cols-5 gap-2 w-full">
                        {/* Show first 5 categories only on Home */}
                        {categories.slice(0, 5).map((cat) => (
                            <button
                                key={cat.id}
                                onClick={() => router.push(`/SearchResults?category=${encodeURIComponent(cat.name)}`)}
                                className="aspect-square bg-red-50 rounded-2xl flex flex-col items-center justify-center text-gray-700 hover:bg-red-100 transition-colors p-1"
                            >
                                <span className="text-xs font-bold text-center break-keep leading-tight">{cat.name}</span>
                            </button>
                        ))}
                    </div>
                    {categories.length === 0 && (
                        <div className="text-center text-gray-300 text-xs py-4">카테고리 로딩 중...</div>
                    )}
                </div>
            </div>
        </Layout>
    )
}
