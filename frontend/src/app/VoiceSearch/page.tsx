'use client';

import React, { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import Layout from '../../components/Layout'

const VoiceSearch = () => {
    const router = useRouter()
    const [isProcessing, setIsProcessing] = useState(false)
    const [transcribedText, setTranscribedText] = useState('')
    const fileInputRef = useRef<HTMLInputElement>(null)

    // Audio visualizer bars animation
    const AudioVisualizer = () => {
        const barHeights = [24, 40, 32, 48, 36, 44, 28]
        return (
            <div className="flex items-center justify-center gap-1.5 h-16">
                {barHeights.map((height, i) => (
                    <div
                        key={i}
                        className="w-1.5 bg-daiso-red rounded-full audio-bar"
                        style={{
                            height: `${height}px`,
                            animationDelay: `${i * 0.08}s`
                        }}
                    />
                ))}
            </div>
        )
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setIsProcessing(true)
        setTranscribedText('음성을 분석하고 있습니다...')
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('http://localhost:8000/api/search/voice', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Voice search failed')
            }

            const data = await response.json()
            if (data.text) {
                setTranscribedText(`"${data.text}"`)
                // Short delay to show the transcribed text
                setTimeout(() => {
                    router.push(`/SearchResults?q=${encodeURIComponent(data.text)}`)
                }, 1000)
            } else {
                setTranscribedText('')
                router.push('/NoResult?message=' + encodeURIComponent('음성을 인식하지 못했습니다.'))
            }
        } catch (error: any) {
            console.error("Voice search error:", error)
            router.push('/NoResult?message=' + encodeURIComponent(`오류가 발생했습니다: ${error.message}`))
        }
    }

    const handleConfirm = () => {
        if (transcribedText) {
            const cleanText = transcribedText.replace(/^"|"$/g, '')
            router.push(`/SearchResults?q=${encodeURIComponent(cleanText)}`)
        }
    }

    const handleCancel = () => {
        router.back()
    }

    const triggerFileUpload = () => {
        fileInputRef.current?.click()
    }

    return (
        <Layout className="p-6 relative">
            {/* Back Button */}
            <div className="absolute top-6 left-6">
                <button
                    onClick={() => router.back()}
                    className="flex items-center text-gray-600 font-medium hover:text-gray-800 transition-colors"
                >
                    <ArrowLeft className="mr-2" size={20} /> 뒤로
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col items-center justify-center">
                <div className="w-full max-w-md flex flex-col items-center space-y-8">
                    {/* Title */}
                    <h1 className="text-4xl font-bold text-gray-900">
                        듣고 있습니다...
                    </h1>

                    {/* Audio Visualizer */}
                    <div className="py-4">
                        <AudioVisualizer />
                    </div>

                    {/* Transcribed Text Display */}
                    <div className="w-full">
                        <div className="bg-white border border-gray-200 rounded-full px-6 py-4 text-center shadow-sm min-h-[56px] flex items-center justify-center">
                            {transcribedText ? (
                                <span className="text-gray-800 text-lg">{transcribedText}</span>
                            ) : (
                                <span className="text-gray-400 text-lg">
                                    녹음 파일을 업로드하세요
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Hidden file input */}
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        accept="audio/*"
                        className="hidden"
                    />

                    {/* Action Buttons */}
                    <div className="flex items-center gap-4 pt-4">
                        <button
                            onClick={handleCancel}
                            className="px-8 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                        >
                            취소
                        </button>

                        {transcribedText && !isProcessing ? (
                            <button
                                onClick={handleConfirm}
                                className="px-8 py-3 bg-daiso-red text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                            >
                                확인
                            </button>
                        ) : (
                            <button
                                onClick={triggerFileUpload}
                                disabled={isProcessing}
                                className="px-8 py-3 bg-daiso-red text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isProcessing ? '처리 중...' : '파일 선택'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    )
}

export default VoiceSearch
