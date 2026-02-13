'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Mic, MicOff } from 'lucide-react'
import Layout from '../../components/Layout'
import { AudioRecorder } from '../../utils/AudioRecorder'

const VoiceSearch = () => {
    const router = useRouter()
    const [isRecording, setIsRecording] = useState(false)
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
        setTranscript('')
        setInterimText('')
        setStatusMessage('연결 중...')
        seqRef.current = 0

        try {
            // 1. Connect WebSocket
            const hostname = window.location.hostname
            const wsUrl = `ws://${hostname}:8000/ws/stt`
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

                        // Send text to pipeline
                        try {
                            const pipelineResp = await fetch(`http://${window.location.hostname}:8000/api/search/process_text`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: finalText })
                            })
                            const data = await pipelineResp.json()

                            // Store data for VoiceResults page
                            const queryText = data.keyword || finalText
                            if (data.keyword) {
                                localStorage.setItem('voiceSearchKeyword', data.keyword)
                            }
                            if (data.results && data.results.length > 0) {
                                localStorage.setItem('voiceSearchResults', JSON.stringify(data.results))
                            }
                            if (data.reranked && data.reranked.length > 0) {
                                localStorage.setItem('voiceRerankedResults', JSON.stringify(data.reranked))
                            }

                            // Navigate to VoiceResults (Top 3 selection page)
                            router.push(`/VoiceResults?q=${encodeURIComponent(queryText)}`)
                        } catch (pipeErr) {
                            console.error('Pipeline error:', pipeErr)
                            router.push(`/SearchResults?q=${encodeURIComponent(finalText)}`)
                        }
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

        } catch (error) {
            console.error('Recording start failed:', error)
            setStatusMessage('마이크 접근에 실패했습니다.')
            setIsRecording(false)
        }
    }, [router, stopRecording])

    const handleMicClick = useCallback(() => {
        if (isRecording) {
            stopRecording()
        } else {
            startRecording()
        }
    }, [isRecording, startRecording, stopRecording])

    // Keep a ref to the latest startRecording so auto-start always works
    const startRecordingRef = useRef(startRecording)
    startRecordingRef.current = startRecording

    // Auto-start recording on page load (fires once on mount, no deps issue)
    useEffect(() => {
        const timer = setTimeout(() => {
            startRecordingRef.current()
        }, 500)
        return () => clearTimeout(timer)
    }, [])

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
                        음성 검색
                    </h1>

                    {/* Status Message */}
                    <p className="text-lg text-gray-500 font-medium text-center">
                        {statusMessage}
                    </p>

                    {/* Guidance */}
                    <p className="text-sm text-gray-400 text-center">
                        {isRecording ? "말씀이 끝나면 자동으로 검색됩니다." : "버튼을 눌러 상품을 찾아보세요."}
                    </p>

                    {/* Audio Visualizer */}
                    <div className="py-4">
                        <AudioVisualizer />
                    </div>

                    {/* Mic Button */}
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

                    {/* Transcript Display */}
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
