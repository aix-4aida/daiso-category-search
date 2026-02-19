'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Mic, MicOff, Keyboard } from 'lucide-react'
import Layout from '../../components/Layout'
import { AudioRecorder } from '../../utils/AudioRecorder'
import { useUnifiedSearch } from '../../hooks/useUnifiedSearch'

const VoiceSearch = () => {
    const router = useRouter()
    const { handleSearch, isLoading } = useUnifiedSearch()

    const [isRecording, setIsRecording] = useState(false)
    const [isKeyboardMode, setIsKeyboardMode] = useState(false)
    const [transcript, setTranscript] = useState('')
    const [interimText, setInterimText] = useState('')
    const [statusMessage, setStatusMessage] = useState('음성 인식을 준비하고 있습니다...')
    const autoStartedRef = useRef(false)

    const recorderRef = useRef<AudioRecorder | null>(null)
    const wsRef = useRef<WebSocket | null>(null)
    const seqRef = useRef(0)

    // Audio visualizer bars animation
    const AudioVisualizer = () => {
        const barHeights = [24, 40, 32, 48, 36, 44, 28]
        return (
            <div className="flex items-center justify-center gap-1.5 h-16">
                {barHeights.map((height, i) => (
                    <div
                        key={i}
                        className={`w-1.5 rounded-full audio-bar ${isRecording ? 'bg-daiso-red' : 'bg-gray-300'}`}
                        style={{
                            height: `${height}px`,
                            animationDelay: `${i * 0.08}s`,
                            animationPlayState: isRecording ? 'running' : 'paused'
                        }}
                    />
                ))}
            </div>
        )
    }

    const stopRecording = useCallback(() => {
        // Stop recorder
        if (recorderRef.current) {
            recorderRef.current.stop()
            recorderRef.current = null
        }

        // Send stop to WS
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'stop' }))
        }

        setIsRecording(false)
    }, [])

    const startRecording = useCallback(async () => {
        if (isKeyboardMode) return;

        setTranscript('')
        setInterimText('')
        setStatusMessage('연결 중...')
        seqRef.current = 0

        try {
            // 1. Connect WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
            const wsUrl = `${protocol}//${window.location.host}/ws/stt`
            const ws = new WebSocket(wsUrl)
            wsRef.current = ws

            ws.onopen = () => {
                console.log('🔌 WebSocket connected')
                // Send start message
                ws.send(JSON.stringify({
                    type: 'start',
                    meta: { run_id: `web_${Date.now()}`, test_id: `voice_${Date.now()}` },
                    config: {}
                }))
            }

            ws.onmessage = async (event) => {
                const msg = JSON.parse(event.data)

                if (msg.type === 'started') {
                    setStatusMessage('듣고 있습니다...')
                    setIsRecording(true)

                    // 2. Start Audio Recording
                    const recorder = new AudioRecorder()
                    recorderRef.current = recorder

                    await recorder.start((pcm16: Int16Array) => {
                        if (ws.readyState === WebSocket.OPEN) {
                            // Convert Int16Array to base64
                            const bytes = new Uint8Array(pcm16.buffer)
                            let binary = ''
                            for (let i = 0; i < bytes.length; i++) {
                                binary += String.fromCharCode(bytes[i])
                            }
                            const b64 = btoa(binary)

                            ws.send(JSON.stringify({
                                type: 'audio',
                                pcm_b64: b64,
                                seq: seqRef.current++
                            }))
                        }
                    })
                } else if (msg.type === 'interim') {
                    setInterimText(msg.text)
                } else if (msg.type === 'final') {
                    const finalText = msg.text || ''
                    setTranscript(finalText)
                    setInterimText('')

                    // Stop recording
                    if (recorderRef.current) {
                        recorderRef.current.stop()
                        recorderRef.current = null
                    }
                    setIsRecording(false)

                    if (finalText) {
                        setStatusMessage('검색 중...')
                        // Use Unified Search
                        await handleSearch(finalText, 'voice');
                    } else {
                        setStatusMessage('음성을 인식하지 못했습니다.')
                        setTimeout(() => {
                            setStatusMessage('버튼을 눌러 다시 시도해주세요')
                        }, 2000)
                    }

                    // Close WS
                    ws.close()
                    wsRef.current = null
                } else if (msg.type === 'error') {
                    console.error('STT Error:', msg.message)
                    setStatusMessage('오류가 발생했습니다. 다시 시도해주세요.')
                    stopRecording()
                }
            }

            ws.onerror = (err) => {
                console.error('WebSocket error:', err)
                setStatusMessage('연결에 실패했습니다.')
                stopRecording()
            }

            ws.onclose = () => {
                console.log('🔌 WebSocket closed')
            }

        } catch (error: any) {
            console.error('Recording start failed:', error)
            if (error.name === 'NotFoundError' || error.message?.includes('device not found')) {
                setStatusMessage('마이크가 연결되어 있지 않습니다.')
            } else if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                setStatusMessage('마이크 권한이 허용되지 않았습니다.')
            } else {
                setStatusMessage('마이크 접근에 실패했습니다.')
            }
            setIsRecording(false)
        }
    }, [handleSearch, isKeyboardMode, stopRecording])

    const handleMicClick = useCallback(() => {
        if (isRecording) {
            stopRecording()
        } else {
            startRecording()
        }
    }, [isRecording, startRecording, stopRecording])

    const toggleInputMode = () => {
        if (isRecording) stopRecording();
        setIsKeyboardMode(prev => !prev);
        if (!isKeyboardMode) {
            setStatusMessage('검색어를 입력해주세요.');
        } else {
            setStatusMessage('버튼을 눌러 상품을 찾아보세요.');
        }
    };

    const handleTextSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (transcript.trim()) {
            handleSearch(transcript, 'text');
        }
    };

    // Keep a ref to the latest startRecording so auto-start always works
    const startRecordingRef = useRef(startRecording)
    startRecordingRef.current = startRecording

    // Auto-start recording on page load (fires once on mount, only if not keyboard mode)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (!isKeyboardMode && !autoStartedRef.current) {
                startRecordingRef.current()
                autoStartedRef.current = true;
            }
        }, 500)
        return () => clearTimeout(timer)
    }, []) // Empty deps intended for mount only

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (recorderRef.current) {
                recorderRef.current.stop()
            }
            if (wsRef.current) {
                wsRef.current.close()
            }
        }
    }, [])

    return (
        <Layout className="p-6 relative">
            {/* Loading Overlay */}
            {isLoading && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-white/90 backdrop-blur-sm">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-daiso-red mb-6"></div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">상품을 찾고 있습니다</h2>
                    <p className="text-gray-500 animate-pulse">잠시만 기다려주세요...</p>
                </div>
            )}

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
                        {isKeyboardMode ? "검색" : "음성 검색"}
                    </h1>

                    {/* Status Message */}
                    <p className="text-lg text-gray-500 font-medium text-center">
                        {statusMessage}
                    </p>

                    {/* Guidance */}
                    {!isKeyboardMode && (
                        <p className="text-sm text-gray-400 text-center">
                            {isRecording ? "말씀이 끝나면 자동으로 검색됩니다." : "버튼을 눌러 상품을 찾아보세요."}
                        </p>
                    )}

                    {/* Audio Visualizer or Text Input Helper */}
                    <div className="py-4 min-h-[64px] flex items-center justify-center">
                        {!isKeyboardMode && <AudioVisualizer />}
                    </div>

                    {/* Input Area: Mic or Text Input */}
                    {isKeyboardMode ? (
                        <form onSubmit={handleTextSubmit} className="w-full">
                            <input
                                type="text"
                                value={transcript}
                                onChange={(e) => setTranscript(e.target.value)}
                                placeholder="상품명이나 증상을 입력하세요"
                                className="w-full h-16 px-6 rounded-full bg-gray-100 text-xl focus:outline-none focus:ring-2 focus:ring-daiso-red transition-shadow text-center"
                                autoFocus
                            />
                            <button
                                type="submit"
                                className="w-full mt-4 bg-daiso-red text-white py-3 rounded-xl font-bold hover:bg-red-700 transition-colors"
                            >
                                검색하기
                            </button>
                        </form>
                    ) : (
                        <button
                            onClick={handleMicClick}
                            className={`w-24 h-24 rounded-full flex items-center justify-center shadow-lg transition-all ${isRecording
                                ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                                : 'bg-daiso-red hover:bg-red-700'
                                }`}
                        >
                            {isRecording ? (
                                <MicOff size={40} color="white" />
                            ) : (
                                <Mic size={40} color="white" />
                            )}
                        </button>
                    )}

                    {/* Transcript Display (Only in Voice Mode) */}
                    {!isKeyboardMode && (
                        <div className="w-full">
                            <div className="bg-white border border-gray-200 rounded-2xl px-6 py-4 text-center shadow-sm min-h-[56px] flex items-center justify-center">
                                {transcript || interimText ? (
                                    <span className="text-gray-800 text-lg">
                                        {transcript} <span className="text-gray-400">{interimText}</span>
                                    </span>
                                ) : (
                                    <span className="text-gray-400 text-lg">
                                        음성이 여기에 표시됩니다
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Toggle Mode Button */}
                    <button
                        onClick={toggleInputMode}
                        className="flex items-center gap-2 text-gray-500 hover:text-daiso-red transition-colors mt-4 text-sm font-medium"
                    >
                        {isKeyboardMode ? (
                            <>
                                <Mic size={16} /> 음성으로 검색하기
                            </>
                        ) : (
                            <>
                                <Keyboard size={16} /> 키보드로 입력하기
                            </>
                        )}
                    </button>

                    {/* Attribution */}
                    <p className="text-xs text-gray-300 mt-4">
                        Powered by Google STT &amp; Whisper
                    </p>
                </div>
            </div>
        </Layout>
    )
}

export default VoiceSearch
