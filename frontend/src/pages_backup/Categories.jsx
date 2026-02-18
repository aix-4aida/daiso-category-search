import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Layout from '../components/Layout'
import { getCategories } from '../lib/api'

const Categories = () => {
    const router = useRouter()
    const [categories, setCategories] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchCats = async () => {
            setLoading(true)
            const data = await getCategories();
            if (data && data.categories) {
                setCategories(data.categories);
            }
            setLoading(false)
        };
        fetchCats();
    }, []);

    return (
        <Layout className="bg-white">
            <header className="p-4 border-b flex items-center justify-center relative">
                <h1 className="text-xl font-bold">카테고리</h1>
            </header>

            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="flex justify-center py-10">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-daiso-red"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-4">
                        {categories.map((cat) => (
                            <button
                                key={cat.id}
                                onClick={() => router.push({
                                    pathname: '/SearchResults',
                                    query: { category: cat.name }
                                })}
                                className="aspect-[4/3] bg-gray-50 rounded-2xl flex flex-col items-center justify-center text-gray-700 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm"
                            >
                                <span className="text-lg font-bold mb-1">{cat.name}</span>
                                {/* Optional: Add icon or count here if available */}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    )
}

export default Categories
