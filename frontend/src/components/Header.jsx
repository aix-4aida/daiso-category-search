import React from 'react'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const Header = ({ title, showBack = true }) => {
    const navigate = useNavigate()

    return (
        <header className="fixed top-0 left-0 right-0 h-16 bg-white flex items-center px-4 z-50">
            {showBack && (
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                >
                    <ArrowLeft size={24} />
                    <span className="sr-only">뒤로가기</span>
                </button>
            )}
            {title && (
                <h1 className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-lg font-medium text-gray-800">
                    {title}
                </h1>
            )}
        </header>
    )
}

export default Header
