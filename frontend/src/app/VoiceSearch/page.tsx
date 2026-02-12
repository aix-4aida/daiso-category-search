'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AudioRecorder } from '../../utils/AudioRecorder';

// Helper to convert ArrayBuffer to Base64
function bufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

const VoiceSearch = () => {
    const router = useRouter();

    // State
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [interimText, setInterimText] = useState("");
    const [statusMessage, setStatusMessage] = useState("마이크 버튼을 눌러 말씀해주세요.");
    const [wsStatus, setWsStatus] = useState("disconnected"); // connected, disconnected, error

    // Refs
    const wsRef = useRef(null);
    const recorderRef = useRef(null);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopRecording();
        };
    }, []);

    const startRecording = async () => {
        try {
            setTranscript("");
            setInterimText("");
            setStatusMessage("연결 중...");

            // 1. WebSocket Connect
            // Use NEXT_PUBLIC_API_URL if available, else fallback
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const wsUrl = apiUrl.replace(/^http/, 'ws') + "/ws/stt";

            console.log("Connecting to WS:", wsUrl);
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("✅ WebSocket connected");
                setWsStatus("connected");
                setStatusMessage("듣고 있어요... 말씀해 보세요!");

                // Send Start Message
                ws.send(JSON.stringify({
                    type: "start",
                    meta: {
                        run_id: "web_client",
                        utterance_type: "query",
                        save_audio: false
                    }
                }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === "started") {
                    console.log("Server session started:", data.run_id);
                    setIsRecording(true);

                    // Start Audio Recording
                    startAudioCapture();
                }
                else if (data.type === "interim") {
                    setInterimText(data.text);
                }
                else if (data.type === "final") {
                    console.log("Final Result:", data);
                    setInterimText(""); // Clear interim

                    // Append only if valid
                    if (data.text) {
                        setTranscript(prev => {
                            const newText = prev + " " + data.text;
                            return newText.trim();
                        });

                        // Stop & Navigate logic
                        // If we got a final result that is not empty, stop and search
                        if (data.text.trim()) {
                            stopRecording();
                            handleSearch(data.text);
                        }
                    }
                }
                else if (data.type === "error") {
                    console.error("Server Error:", data.message);
                    setStatusMessage("오류: " + data.message);
                    stopRecording();
                }
            };

            ws.onerror = (error) => {
                console.error("WebSocket Error:", error);
                setWsStatus("error");
                setStatusMessage("서버 연결 오류");
                stopRecording();
            };

            ws.onclose = () => {
                console.log("WebSocket Disconnected");
                setWsStatus("disconnected");
                setIsRecording(false);
            };

        } catch (error) {
            console.error("Failed to start recording:", error);
            setStatusMessage("마이크 접근 실패");
        }
    };

    const startAudioCapture = async () => {
        try {
            recorderRef.current = new AudioRecorder();

            await recorderRef.current.start((pcmData) => {
                if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                    // Send Audio Chunk
                    const base64Audio = bufferToBase64(pcmData.buffer);
                    wsRef.current.send(JSON.stringify({
                        type: "audio",
                        pcm_b64: base64Audio
                    }));
                }
            });
        } catch (e) {
            console.error("Audio capture failed:", e);
            setStatusMessage("마이크 오류: " + e.message);
            stopRecording();
        }
    };

    const stopRecording = () => {
        if (recorderRef.current) {
            recorderRef.current.stop();
            recorderRef.current = null;
        }

        if (wsRef.current) {
            if (wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: "stop" }));
                wsRef.current.close();
            }
            wsRef.current = null;
        }

        setIsRecording(false);
    };

    const handleSearch = (text) => {
        const query = text.trim();
        if (!query) return;

        // Navigate to map with query
        // Using confirm/delay to let user see text? No, instant search is better.
        setTimeout(() => {
            // Remove trailing punctuation (., ?, !) common in STT results
            const cleanQuery = query.replace(/[.?!]+$/, '');
            const encodedQuery = encodeURIComponent(cleanQuery);
            router.push(`/SearchResults?q=${encodedQuery}`);
            // Note: Changed from state approach (difficult in App Router w/ router.push) 
            // to Query Param approach which is more standard.
            // Receiver page needs to check searchParams.
        }, 800);
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Header */}
            <div className="flex items-center px-4 h-14 border-b border-gray-100">
                <button onClick={() => router.back()} className="p-2 -ml-2">
                    <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                </button>
                <h1 className="text-lg font-bold ml-2">음성 검색</h1>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-8">

                {/* Visualizer / Status Icon */}
                <div className={`relative w-40 h-40 flex items-center justify-center rounded-full transition-all duration-300 ${isRecording ? 'bg-red-50 scale-105' : 'bg-gray-50'
                    }`}>
                    {isRecording && (
                        <>
                            <div className="absolute inset-0 rounded-full border-4 border-red-500 opacity-20 animate-ping"></div>
                            <div className="absolute inset-2 rounded-full border-2 border-red-300 opacity-40 animate-pulse"></div>
                        </>
                    )}
                    <button
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`z-10 w-24 h-24 rounded-full flex items-center justify-center shadow-xl transition-all transform active:scale-95 ${isRecording ? 'bg-red-500 text-white scale-110' : 'bg-[#da291c] text-white hover:bg-[#c42519]'
                            }`}
                    >
                        {isRecording ? (
                            <div className="w-8 h-8 bg-white rounded-sm shadow-sm" />
                        ) : (
                            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        )}
                    </button>
                </div>

                {/* Status Text */}
                <div className="text-center space-y-2 h-20">
                    <p className={`text-xl font-bold transition-colors ${isRecording ? 'text-red-500' : 'text-gray-800'}`}>
                        {statusMessage}
                    </p>
                    <p className="text-gray-500 text-sm">
                        {isRecording ? "말씀이 끝나면 자동으로 검색됩니다." : "버튼을 눌러 상품을 찾아보세요."}
                    </p>
                </div>

                {/* Transcript Display */}
                <div className={`w-full max-w-sm bg-gray-50 rounded-xl p-6 min-h-[140px] border border-gray-100 transition-opacity duration-300 ${(transcript || interimText) ? 'opacity-100' : 'opacity-0'
                    }`}>
                    <p className="text-xl text-gray-800 font-medium leading-relaxed break-keep text-center">
                        {transcript} <span className="text-gray-400">{interimText}</span>
                    </p>
                </div>
            </div>

            <div className="p-6 text-center">
                <p className="text-xs text-gray-300 font-mono">
                    Powered by Google STT & Whisper
                </p>
            </div>
        </div>
    );
};

export default VoiceSearch;
