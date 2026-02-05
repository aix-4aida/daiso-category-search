"use client";

import { useState } from 'react';
import QRCode from 'react-qr-code';

// Kiosk position (matches backend MAP_CONFIG)
const KIOSK_POSITION = { x: 10, y: 2 };

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [qrValue, setQrValue] = useState('');
    const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
    const [showSettings, setShowSettings] = useState(false);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query) return;
        setLoading(true);
        setResult(null);
        setQrValue('');

        try {
            const res = await fetch(`${backendUrl}/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            const data = await res.json();

            if (data.results && data.results.length > 0) {
                setResult(data.results[0].item);
            }
        } catch (err) {
            console.error(err);
            alert('Search failed. Check backend URL in settings.');
        } finally {
            setLoading(false);
        }
    };

    const generateQR = () => {
        if (!result) return;

        // Target product coordinates
        const targetX = result.location.x;
        const targetY = result.location.y;

        // User starts at kiosk position
        const userX = KIOSK_POSITION.x;
        const userY = KIOSK_POSITION.y;

        const protocol = window.location.protocol;
        const host = window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : '';

        // Include user position (ux, uy) and target position (tx, ty)
        const url = `${protocol}//${host}${port}/ar?tx=${targetX}&ty=${targetY}&ux=${userX}&uy=${userY}&name=${encodeURIComponent(result.name)}`;

        setQrValue(url);
    };

    // Voice recognition handler
    const handleVoiceInput = () => {
        // Check for SpeechRecognition support
        const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;

        if (!SpeechRecognition) {
            alert("❌ 이 브라우저는 음성인식을 지원하지 않습니다.\n\nChrome 또는 Edge를 사용해주세요.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'ko-KR';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.continuous = false;

        recognition.onstart = () => {
            console.log("Voice recognition started");
            setQuery("🎤 말씀하세요...");
        };

        recognition.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            console.log("Recognized:", transcript);
            setQuery(transcript);
        };

        recognition.onerror = (event: any) => {
            console.error("Speech error:", event.error);
            if (event.error === 'not-allowed') {
                setQuery("❌ 마이크 권한 거부됨");
                alert("마이크 권한을 허용해주세요.\n\n브라우저 주소창 왼쪽의 🔒 아이콘 클릭 → 마이크 허용");
            } else if (event.error === 'no-speech') {
                setQuery("🔇 음성이 감지되지 않았습니다");
            } else {
                setQuery(`❌ 오류: ${event.error}`);
            }
        };

        recognition.onend = () => {
            console.log("Voice recognition ended");
        };

        try {
            recognition.start();
        } catch (e) {
            console.error("Failed to start recognition:", e);
            setQuery("❌ 음성인식 시작 실패");
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8 flex flex-col items-center relative">
            {/* Settings Toggle */}
            <div className="absolute top-4 right-4 z-50">
                <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="text-gray-400 text-2xl hover:text-gray-600"
                >
                    ⚙️
                </button>
                {showSettings && (
                    <div className="absolute right-0 mt-2 bg-white p-4 shadow-xl rounded-lg border w-72 text-left">
                        <label className="text-xs font-bold text-gray-700 block mb-1">Backend API URL</label>
                        <input
                            type="text"
                            value={backendUrl}
                            onChange={(e) => setBackendUrl(e.target.value)}
                            className="w-full text-xs border p-2 rounded text-black bg-gray-50"
                            placeholder="http://localhost:8000"
                        />
                        <p className="text-[10px] text-gray-400 mt-2">
                            For tunnel: Use public Backend URL
                        </p>
                    </div>
                )}
            </div>

            <h1 className="text-3xl font-bold mb-8 text-black">What are you looking for?</h1>

            <form onSubmit={handleSearch} className="w-full max-w-2xl flex gap-4">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g. '여행용 샴푸' or 'bathroom mat'"
                    className="flex-1 p-4 rounded-xl text-xl border border-gray-300 text-black shadow-sm focus:ring-2 focus:ring-blue-500"
                />
                <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-8 py-4 rounded-xl text-xl font-bold hover:bg-blue-700 transition-colors"
                >
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </form>

            {/* Voice Input Button */}
            <button
                type="button"
                onClick={handleVoiceInput}
                className="mt-4 flex items-center gap-2 text-gray-500 hover:text-blue-500 transition-colors"
            >
                <span className="text-2xl">🎤</span>
                <span className="text-lg">Touch to Speak</span>
            </button>

            {result && (
                <div className="mt-12 bg-white p-8 rounded-2xl shadow-xl w-full max-w-2xl flex flex-col items-center animate-fade-in">
                    <h2 className="text-2xl font-bold text-gray-800">{result.name}</h2>
                    <p className="text-gray-500 mt-2">{result.category}</p>
                    <div className="my-6 bg-gray-100 p-4 rounded-lg w-full text-center">
                        <p className="text-lg font-semibold text-blue-600">{result.location.desc}</p>
                        <p className="text-sm text-gray-400 mt-1">
                            Map Position: ({result.location.x}, {result.location.y})
                        </p>
                    </div>

                    {!qrValue ? (
                        <button
                            onClick={generateQR}
                            className="bg-green-500 text-white px-6 py-3 rounded-lg text-lg font-bold hover:bg-green-600 transition-colors shadow-lg"
                        >
                            📱 Get AR Directions
                        </button>
                    ) : (
                        <div className="flex flex-col items-center">
                            <p className="mb-4 font-bold text-gray-700">Scan with your phone!</p>
                            <div className="p-3 bg-white rounded-lg shadow-lg border-4 border-blue-500">
                                <QRCode value={qrValue} size={200} />
                            </div>
                            <p className="mt-3 text-sm text-gray-500">
                                Distance: ~{Math.round(Math.sqrt(Math.pow(result.location.x - KIOSK_POSITION.x, 2) + Math.pow(result.location.y - KIOSK_POSITION.y, 2)))}m
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
