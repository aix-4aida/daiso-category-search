'use client';

import React from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, Bell, Search } from 'lucide-react'
import Layout from '../../components/Layout'
import Button from '../../components/Button'

const NoResult = () => {
    const router = useRouter()
    const searchParams = useSearchParams()
    const message = searchParams.get('message')

    return (
        <Layout className="bg-white">
            <header className="fixed top-0 left-0 p-6 z-50">
                <button onClick={() => router.back()} className="flex items-center text-gray-600 font-medium text-lg">
                    <ArrowLeft className="mr-2" /> 뒤로
                </button>
            </header>

            <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-12">
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-bold text-gray-900">죄송합니다</h1>
                    <p className="text-xl text-gray-500">{message || '해당 상품의 위치를 찾을 수 없습니다'}</p>
                </div>

                {/* Suggestion Box */}
                <div className="bg-gray-50 rounded-2xl p-8 w-full max-w-lg">
                    <div className="flex items-center mb-4 text-gray-700 font-bold text-lg">
                        <span className="mr-2">💡</span> 이렇게 검색해 보세요:
                    </div>
                    <ul className="space-y-4 text-gray-600">
                        <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></span>
                            "세탁세제 어디 있어요?"
                        </li>
                        <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></span>
                            "주방세제 위치 알려줘"
                        </li>
                        <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-3"></span>
                            "12번 매대에 뭐가 있어요?"
                        </li>
                    </ul>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4 w-full max-w-lg">
                    <Button
                        variant="secondary"
                        className="flex-1 h-14 text-lg rounded-xl bg-red-50 text-daiso-red hover:bg-red-100"
                    >
                        <Bell className="mr-2" size={20} /> 직원 호출
                    </Button>
                    <Button
                        variant="primary"
                        className="flex-1 h-14 text-lg rounded-xl"
                        onClick={() => router.push('/')}
                    >
                        <Search className="mr-2" size={20} /> 다시 검색하기
                    </Button>
                </div>
            </div>
        </Layout>
    )
}

export default NoResult
