import React, { useState } from 'react'
import { useRouter } from 'next/router'
import { HelpCircle, Search } from 'lucide-react'
import Layout from '../components/Layout'
import Button from '../components/Button'

const CATEGORIES = [
    { id: '위생', name: '의약품' },
    { id: '문구', name: '문구' },
    { id: '주방', name: '주방' },
    { id: '청소', name: '생활' },
    { id: '잡화', name: '잡화' },
]

const Home = () => {
    const router = useRouter()
    const [query, setQuery] = useState('')

    const handleVoiceClick = () => {
        router.push('/VoiceSearch')
    }

    const handleSearch = (e) => {
        e.preventDefault()
        if (query.trim()) {
            router.push(`/SearchResults?q=${encodeURIComponent(query)}`)
        }
    }

    return (
        <Layout className="items-center justify-center p-6 relative">
            {/* Top Left Logo (Red Square) */}
            <div className="absolute top-6 left-6 w-12 h-12 bg-daiso-red rounded-md"></div>

            {/* Top Right (Optional Auth/Settings placeholder) */}
            <div className="absolute top-6 right-6 w-24 h-8 bg-gray-100 rounded-full"></div>

            <div className="w-full max-w-lg flex flex-col items-center space-y-12">
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

                {/* Search Input */}
                <form onSubmit={handleSearch} className="w-full relative">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                        <input
                            type="text"
                            placeholder="상품명을 입력하세요..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="w-full h-14 pl-12 pr-6 rounded-full bg-gray-100 text-lg focus:outline-none focus:ring-2 focus:ring-daiso-red transition-shadow"
                        />
                    </div>
                </form>

                {/* Categories */}
                <div className="flex justify-between w-full gap-2">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat.id}
                            onClick={() => router.push(`/SearchResults?category=${cat.id}`)}
                            className="flex-1 aspect-square bg-red-50 rounded-2xl flex flex-col items-center justify-center text-gray-700 hover:bg-red-100 transition-colors"
                        >
                            <span className="text-sm font-medium">{cat.name}</span>
                        </button>
                    ))}
                </div>
            </div>
        </Layout>
    )
}

export default Home
