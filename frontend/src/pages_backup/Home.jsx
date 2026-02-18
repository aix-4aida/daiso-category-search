import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom' // Pages Router에서는 useRouter를 쓰는게 맞지만, 현재 Home.jsx는 react-router-dom을 쓰고 있음 (Next.js Pages임에도 불구하고). 기존 코드 존중하되, Next.js 라우팅(useRouter)으로 마이그레이션이 필요해보임. 하지만 일단 기존 코드 스타일 유지.
// 아, 기존 Home.jsx가 'react-router-dom'을 import하고 있었음. 이건 SPA 방식인데 Next.js에서는 'next/router' 또는 'next/navigation'을 써야 함.
// 기존 코드가 동작했다면 _app.js 등에서 설정을 했거나, import가 잘못되어 있었을 수 있음.
// 안전하게 next/router로 변경하여 구현함.

import { useRouter } from 'next/router'
import { HelpCircle, Search } from 'lucide-react'
import Layout from '../components/Layout'
import { getCategories } from '../lib/api'

const Home = () => {
    const router = useRouter()
    const [query, setQuery] = useState('')
    const [categories, setCategories] = useState([])

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
        router.push('/VoiceSearch') // Next.js routing
    }

    const handleSearch = (e) => {
        e.preventDefault()
        if (query.trim()) {
            // Use 'text' source to indicate pipeline usage
            router.push({
                pathname: '/SearchResults',
                query: { q: query, source: 'text' }
            })
        }
    }

    return (
        <Layout className="items-center justify-center p-6 relative">
            {/* Top Left Logo (Red Square) */}
            <div className="absolute top-6 left-6 w-12 h-12 bg-daiso-red rounded-md"></div>

            {/* Top Right (Optional Auth/Settings placeholder) */}
            <div className="absolute top-6 right-6 w-24 h-8 bg-gray-100 rounded-full"></div>

            <div className="w-full max-w-lg flex flex-col items-center space-y-12 mb-10">
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
                <form onSubmit={handleSearch} className="w-full relative">
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
                                onClick={() => router.push({
                                    pathname: '/SearchResults',
                                    query: { category: cat.name }
                                })}
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

export default Home
