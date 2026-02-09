import React, { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload, Loader2 } from 'lucide-react'
import Layout from '../components/Layout'
import Button from '../components/Button'

const VoiceSearch = () => {
    const navigate = useNavigate()
    const [isProcessing, setIsProcessing] = useState(false)
    const fileInputRef = useRef(null)

    const handleFileUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        setIsProcessing(true)
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
                // Navigate to search results with transcribed text AND products
                navigate(`/search/results?q=${encodeURIComponent(data.text)}`, {
                    state: {
                        products: data.products,
                        query: data.text
                    }
                })
            } else {
                alert("음성을 인식하지 못했습니다.")
            }
        } catch (error) {
            console.error("Voice search error:", error)
            alert(`오류가 발생했습니다: ${error.message}`)
        } finally {
            setIsProcessing(false)
        }
    }

    const triggerFileUpload = () => {
        fileInputRef.current?.click()
    }

    return (
        <Layout className="p-6 relative">
            <div className="absolute top-6 left-6">
                <button onClick={() => navigate(-1)} className="flex items-center text-gray-600 font-medium">
                    <ArrowLeft className="mr-2" /> 뒤로
                </button>
            </div>

            <div className="flex-1 flex flex-col items-center justify-center space-y-12">
                {isProcessing ? (
                    <div className="text-center">
                        <Loader2 className="animate-spin w-16 h-16 text-daiso-red mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-gray-800">음성을 분석하고 있습니다...</h2>
                        <p className="text-gray-500 mt-2">잠시만 기다려 주세요</p>
                    </div>
                ) : (
                    <>
                        <h2 className="text-3xl font-bold text-gray-800">음성 검색</h2>
                        <p className="text-gray-500">마이크를 사용하거나 녹음 파일을 업로드하세요</p>

                        {/* Audio Visualizer Animation (Mock) */}
                        <div className="flex items-center justify-center space-x-2 h-24">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div
                                    key={i}
                                    className="w-3 bg-gray-200 rounded-full"
                                    style={{ height: '40px' }}
                                />
                            ))}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col gap-4 w-full max-w-xs">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                accept="audio/*"
                                className="hidden"
                            />

                            <Button
                                variant="primary"
                                size="lg"
                                className="w-full rounded-xl bg-daiso-red hover:bg-red-700 h-16 text-lg shadow-md"
                                onClick={triggerFileUpload}
                            >
                                <Upload className="mr-2" /> 녹음 파일 업로드
                            </Button>

                            <div className="text-center text-sm text-gray-400">
                                또는
                            </div>

                            <Button
                                variant="secondary"
                                size="lg"
                                className="w-full rounded-xl bg-gray-100 hover:bg-gray-200"
                                onClick={() => navigate(-1)}
                            >
                                취소
                            </Button>
                        </div>
                    </>
                )}
            </div>
        </Layout>
    )
}

export default VoiceSearch
