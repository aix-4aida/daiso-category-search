"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";

// ============================================================
// 설정
// ============================================================
const WS_URL = "ws://127.0.0.1:8010/ws/stt";
const TARGET_SAMPLE_RATE = 16000;

// ============================================================
// 타입
// ============================================================
type SessionState = "idle" | "connecting" | "recording" | "finalizing";

interface FinalResult {
    text: string;
    textRaw: string;
    textProcessed: string;
    status: string;
    confidence: number;
    latencyMs: number;
    fallbackUsed: boolean;
    fallbackProvider: string;
}

// ============================================================
// 유틸: 리샘플링 (48kHz → 16kHz 등)
// ============================================================
function resample(input: Float32Array, fromRate: number, toRate: number): Float32Array {
    if (fromRate === toRate) return input;
    const ratio = fromRate / toRate;
    const outputLength = Math.round(input.length / ratio);
    const output = new Float32Array(outputLength);
    for (let i = 0; i < outputLength; i++) {
        const srcIndex = i * ratio;
        const srcIndexFloor = Math.floor(srcIndex);
        const frac = srcIndex - srcIndexFloor;
        const a = input[srcIndexFloor] || 0;
        const b = input[Math.min(srcIndexFloor + 1, input.length - 1)] || 0;
        output[i] = a + frac * (b - a); // 선형 보간
    }
    return output;
}

// ============================================================
// 유틸: Float32 → Int16 PCM → Base64
// ============================================================
function float32ToInt16(float32: Float32Array): Int16Array {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
        const s = Math.max(-1, Math.min(1, float32[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return int16;
}

function int16ToBase64(int16: Int16Array): string {
    const bytes = new Uint8Array(int16.buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

// ============================================================
// RMS 계산 (음량 바 표시용)
// ============================================================
function computeRMS(float32: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < float32.length; i++) {
        sum += float32[i] * float32[i];
    }
    return Math.sqrt(sum / float32.length);
}

// ============================================================
// 메인 컴포넌트
// ============================================================
export default function SttTestPage() {
    // State
    const [state, setState] = useState<SessionState>("idle");
    const [interimText, setInterimText] = useState("");
    const [finalResults, setFinalResults] = useState<FinalResult[]>([]);
    const [rmsLevel, setRmsLevel] = useState(0);
    const [error, setError] = useState("");
    const [log, setLog] = useState<string[]>([]);
    const [actualSampleRate, setActualSampleRate] = useState<number | null>(null);

    // Refs
    const wsRef = useRef<WebSocket | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const workletRef = useRef<AudioWorkletNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const seqRef = useRef(0);
    const sampleRateRef = useRef(TARGET_SAMPLE_RATE);
    // 오디오 프레임 버퍼 (작은 프레임을 모아서 100ms 단위로 전송)
    const audioBufferRef = useRef<Float32Array[]>([]);
    const bufferSamplesRef = useRef(0);

    // 로그 추가
    const addLog = useCallback((msg: string) => {
        const ts = new Date().toLocaleTimeString("ko-KR");
        setLog((prev) => [...prev.slice(-50), `[${ts}] ${msg}`]);
    }, []);

    // ============================================================
    // 오디오 프레임 전송 (버퍼링 후 100ms 단위)
    // ============================================================
    const flushAudioBuffer = useCallback(() => {
        const chunks = audioBufferRef.current;
        if (chunks.length === 0) return;

        // 모든 청크 합치기
        const totalLen = chunks.reduce((s, c) => s + c.length, 0);
        const merged = new Float32Array(totalLen);
        let offset = 0;
        for (const c of chunks) {
            merged.set(c, offset);
            offset += c.length;
        }
        audioBufferRef.current = [];
        bufferSamplesRef.current = 0;

        // 리샘플링 (브라우저 샘플레이트 → 16kHz)
        const resampled = resample(merged, sampleRateRef.current, TARGET_SAMPLE_RATE);

        // Float32 → Int16 → Base64
        const int16 = float32ToInt16(resampled);
        const b64 = int16ToBase64(int16);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({
                    type: "audio",
                    pcm_b64: b64,
                    seq: seqRef.current++,
                })
            );
        }
    }, []);

    // ============================================================
    // START
    // ============================================================
    const handleStart = useCallback(async () => {
        setError("");
        setInterimText("");
        setState("connecting");
        seqRef.current = 0;
        audioBufferRef.current = [];
        bufferSamplesRef.current = 0;
        addLog("🔌 서버 연결 중...");

        try {
            // 1. WebSocket 연결
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onclose = () => {
                addLog("🔌 WebSocket 종료");
                cleanup();
                setState("idle");
            };

            ws.onerror = () => {
                setError("서버 연결 실패. 서버가 실행 중인지 확인하세요.");
                addLog("❌ WebSocket 에러");
                cleanup();
                setState("idle");
            };

            // 연결 대기
            await new Promise<void>((resolve, reject) => {
                ws.onopen = () => resolve();
                ws.onerror = () => reject(new Error("WebSocket 연결 실패"));
                setTimeout(() => reject(new Error("연결 시간 초과")), 5000);
            });

            addLog("✅ WebSocket 연결됨");

            // 2. 메시지 핸들러
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "started") {
                        addLog("✅ STT 세션 시작됨");
                    } else if (data.type === "interim") {
                        setInterimText(data.text || "");
                    } else if (data.type === "final") {
                        const meta = data.meta || {};
                        const result: FinalResult = {
                            text: data.text || "",
                            textRaw: meta.text_raw || data.text || "",
                            textProcessed: meta.text_processed || data.text || "",
                            status: data.status || "OK",
                            confidence: meta.confidence || 0,
                            latencyMs: meta.latency_ms || 0,
                            fallbackUsed: meta.fallback_used || false,
                            fallbackProvider: meta.fallback_provider || "",
                        };
                        setFinalResults((prev) => [...prev, result]);
                        setInterimText("");
                        addLog(`📊 최종: "${result.textProcessed}" (${result.status})`);
                        setState("idle");
                        cleanup();
                    } else if (data.type === "error") {
                        setError(data.message || "서버 오류");
                        addLog(`❌ 서버 에러: ${data.message}`);
                    } else if (data.type === "auto_stop") {
                        addLog(`🛑 자동 종료: ${data.reason}`);
                        setState("finalizing");
                    }
                } catch {
                    // ignore parse errors
                }
            };

            // 3. Start 메시지 전송
            ws.send(
                JSON.stringify({
                    type: "start",
                    meta: {
                        run_id: "browser_test",
                        test_id: `browser_${Date.now()}`,
                        utterance_type: "realtime_browser",
                        spoken_text: "브라우저 실시간 테스트",
                        save_audio: false,
                    },
                })
            );

            // 4. 마이크 접근
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: false,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });
            streamRef.current = mediaStream;

            // 5. AudioContext (브라우저 기본 샘플레이트 사용 → 리샘플링으로 처리)
            const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
            const audioCtx = new AudioCtx();
            audioCtxRef.current = audioCtx;

            const browserRate = audioCtx.sampleRate;
            sampleRateRef.current = browserRate;
            setActualSampleRate(browserRate);

            if (browserRate !== TARGET_SAMPLE_RATE) {
                addLog(`⚠️ 브라우저 샘플레이트: ${browserRate}Hz → ${TARGET_SAMPLE_RATE}Hz로 리샘플링`);
            } else {
                addLog(`✅ 샘플레이트: ${browserRate}Hz (일치)`);
            }

            // 100ms 분량의 샘플 수 (브라우저 샘플레이트 기준)
            const samplesPerFlush = Math.round(browserRate * 0.1); // 100ms

            // 6. AudioWorklet (Blob URL)
            const workletCode = `
        class PCMProcessor extends AudioWorkletProcessor {
          process(inputs) {
            const ch = inputs[0]?.[0];
            if (ch && ch.length > 0) {
              this.port.postMessage(new Float32Array(ch));
            }
            return true;
          }
        }
        registerProcessor("pcm-processor", PCMProcessor);
      `;
            const blob = new Blob([workletCode], { type: "application/javascript" });
            const url = URL.createObjectURL(blob);
            await audioCtx.audioWorklet.addModule(url);

            const source = audioCtx.createMediaStreamSource(mediaStream);
            sourceRef.current = source;

            const worklet = new AudioWorkletNode(audioCtx, "pcm-processor");
            workletRef.current = worklet;

            // PCM 수신 → 버퍼에 쌓기 → 100ms마다 전송
            worklet.port.onmessage = (e) => {
                const float32: Float32Array = e.data;

                // RMS (음량 표시)
                setRmsLevel(computeRMS(float32));

                // 버퍼에 쌓기
                audioBufferRef.current.push(float32);
                bufferSamplesRef.current += float32.length;

                // 100ms 분량 쌓이면 전송
                if (bufferSamplesRef.current >= samplesPerFlush) {
                    flushAudioBuffer();
                }
            };

            source.connect(worklet);

            setState("recording");
            addLog("🎤 녹음 시작 - 말씀하세요!");
        } catch (err: any) {
            setError(err.message || "마이크 접근 실패");
            addLog(`❌ 시작 실패: ${err.message}`);
            cleanup();
            setState("idle");
        }
    }, [addLog, flushAudioBuffer]);

    // ============================================================
    // STOP
    // ============================================================
    const handleStop = useCallback(() => {
        addLog("🛑 수동 종료");
        setState("finalizing");

        // 남은 버퍼 전송
        flushAudioBuffer();

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({ type: "stop", reason: "manual" })
            );
        }

        // 마이크/오디오 정리 (WS는 final 받고 닫힘)
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (workletRef.current) {
            workletRef.current.disconnect();
            workletRef.current = null;
        }
        if (audioCtxRef.current) {
            audioCtxRef.current.close();
            audioCtxRef.current = null;
        }
        setRmsLevel(0);
    }, [addLog, flushAudioBuffer]);

    // ============================================================
    // Cleanup
    // ============================================================
    const cleanup = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (workletRef.current) {
            workletRef.current.disconnect();
            workletRef.current = null;
        }
        if (audioCtxRef.current) {
            audioCtxRef.current.close();
            audioCtxRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setRmsLevel(0);
    }, []);

    // Unmount 시 정리
    useEffect(() => {
        return () => cleanup();
    }, [cleanup]);

    // ============================================================
    // UI
    // ============================================================
    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-2xl mx-auto">
                {/* 헤더 */}
                <h1 className="text-3xl font-bold text-center mb-2">
                    🎤 실시간 STT 테스트
                </h1>
                <p className="text-gray-400 text-center mb-8 text-sm">
                    Google Streaming STT + 단위 정규화 후처리
                </p>

                {/* 에러 */}
                {error && (
                    <div className="bg-red-900/50 border border-red-500 rounded-lg p-3 mb-4 text-sm">
                        ❌ {error}
                    </div>
                )}

                {/* 상태 표시 */}
                <div className="flex items-center justify-center gap-3 mb-6">
                    <div
                        className={`w-3 h-3 rounded-full ${state === "idle"
                                ? "bg-gray-500"
                                : state === "connecting"
                                    ? "bg-yellow-400 animate-pulse"
                                    : state === "recording"
                                        ? "bg-red-500 animate-pulse"
                                        : "bg-blue-400 animate-pulse"
                            }`}
                    />
                    <span className="text-sm text-gray-300">
                        {state === "idle" && "대기 중"}
                        {state === "connecting" && "연결 중..."}
                        {state === "recording" && "녹음 중 — 말씀하세요"}
                        {state === "finalizing" && "처리 중..."}
                    </span>
                    {actualSampleRate && state === "recording" && (
                        <span className="text-xs text-gray-600">
                            ({actualSampleRate}Hz → {TARGET_SAMPLE_RATE}Hz)
                        </span>
                    )}
                </div>

                {/* 음량 바 */}
                {state === "recording" && (
                    <div className="mb-6">
                        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-green-500 transition-all duration-100 rounded-full"
                                style={{ width: `${Math.min(rmsLevel * 500, 100)}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* 버튼 */}
                <div className="flex justify-center mb-8">
                    {state === "idle" ? (
                        <button
                            onClick={handleStart}
                            className="px-8 py-4 bg-blue-600 hover:bg-blue-500 rounded-xl text-lg font-semibold transition-colors shadow-lg shadow-blue-600/25"
                        >
                            🎤 음성 인식 시작
                        </button>
                    ) : state === "recording" ? (
                        <button
                            onClick={handleStop}
                            className="px-8 py-4 bg-red-600 hover:bg-red-500 rounded-xl text-lg font-semibold transition-colors shadow-lg shadow-red-600/25"
                        >
                            ⏹ 중지
                        </button>
                    ) : (
                        <button
                            disabled
                            className="px-8 py-4 bg-gray-700 rounded-xl text-lg font-semibold opacity-50 cursor-not-allowed"
                        >
                            {state === "connecting" ? "연결 중..." : "처리 중..."}
                        </button>
                    )}
                </div>

                {/* Interim 텍스트 */}
                {interimText && (
                    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-4">
                        <div className="text-xs text-gray-500 mb-1">💬 실시간 인식</div>
                        <div className="text-xl text-yellow-300">{interimText}</div>
                    </div>
                )}

                {/* 최종 결과 목록 */}
                {finalResults.length > 0 && (
                    <div className="space-y-3 mb-8">
                        <h2 className="text-sm text-gray-500 font-semibold">📊 인식 결과</h2>
                        {finalResults.map((r, i) => (
                            <div
                                key={i}
                                className="bg-gray-900 border border-gray-700 rounded-lg p-4"
                            >
                                <div className="text-lg font-semibold mb-2 text-green-400">
                                    {r.textProcessed || r.text || "(인식 결과 없음)"}
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                                    <div>원본: {r.textRaw}</div>
                                    <div>후처리: {r.textProcessed}</div>
                                    <div>상태: {r.status}</div>
                                    <div>신뢰도: {(r.confidence * 100).toFixed(1)}%</div>
                                    <div>지연: {r.latencyMs}ms</div>
                                    <div>
                                        Fallback: {r.fallbackUsed ? r.fallbackProvider : "미사용"}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* 결과 초기화 */}
                {finalResults.length > 0 && state === "idle" && (
                    <div className="flex justify-center mb-8">
                        <button
                            onClick={() => setFinalResults([])}
                            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-400 transition-colors"
                        >
                            🗑 결과 초기화
                        </button>
                    </div>
                )}

                {/* 로그 */}
                <details className="mt-4" open>
                    <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-400">
                        📋 디버그 로그 ({log.length})
                    </summary>
                    <div className="mt-2 bg-gray-900 border border-gray-800 rounded-lg p-3 max-h-48 overflow-y-auto text-xs text-gray-500 font-mono">
                        {log.map((l, i) => (
                            <div key={i}>{l}</div>
                        ))}
                    </div>
                </details>

                {/* 도움말 */}
                <div className="mt-8 text-xs text-gray-600 text-center space-y-1">
                    <p>서버: {WS_URL}</p>
                    <p>
                        서버 시작: python -m uvicorn poc.lsy.api:app --host 127.0.0.1 --port
                        8010
                    </p>
                </div>
            </div>
        </div>
    );
}
