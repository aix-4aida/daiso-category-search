/**
 * API client for backend communication
 * - REST: /v1/search
 * - WebSocket: /ws/stt
 */

import type {
    SearchRequest,
    SearchResponse,
    ProductResult,
    STTServerMessage,
} from "@/types/search";

/**
 * API_BASE 결정:
 *  - NEXT_PUBLIC_API_URL 환경변수가 있으면 그 값 사용
 *    (로컬 dev: "http://localhost:8000", 배포: 미설정)
 *  - 없으면 "/api" (nginx 리버스 프록시 경로, 상대 경로)
 *
 * 주의: 브라우저에서 실행되므로 절대 컨테이너 내부 주소(http://backend:8000)를 쓰면 안 됨
 */
const API_BASE: string = process.env.NEXT_PUBLIC_API_URL || "/api";

function resolveWsBase(): string {
    if (typeof window === "undefined") return API_BASE.replace(/^http/, "ws");
    // 상대 경로("/api")인 경우 현재 origin 기반으로 ws URL 생성
    if (API_BASE.startsWith("/")) {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        return `${proto}//${window.location.host}${API_BASE}`;
    }
    return API_BASE.replace(/^http/, "ws");
}

const WS_BASE: string = resolveWsBase();

// ============================================================================
// REST API: Search
// ============================================================================

export async function searchProducts(
    request: SearchRequest
): Promise<SearchResponse> {
    const body = {
        query: request.query,
    };

    const res = await fetch(`${API_BASE}/search/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Search API error (${res.status}): ${errorText}`);
    }

    // Backend returns: { status, query, products: [{id,name,price,location:{floor,section,shelf_label},image_url,meta:{category_major,category_middle}}], message, processing_time }
    // Frontend expects: SearchResponse { top3: ProductResult[], is_in_scope, ... }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const raw: any = await res.json();

    // Map backend product format → frontend ProductResult format
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const products: ProductResult[] = (raw.products || []).map((p: any, idx: number) => ({
        product_id: p.id || idx,
        name: p.name || "알 수 없는 상품",
        price: p.price || 0,
        category_major: p.meta?.category_major || p.category_major || "",
        category_middle: p.meta?.category_middle || p.category_middle || "",
        location_text: p.location
            ? `${p.location.floor || "B1"}-${p.location.section || ""}-${p.location.shelf_label || ""}`
            : p.location_text || "",
        image_url: p.image_url || null,
        rank: idx + 1,
        is_top1: idx === 0,
    }));

    const mapped: SearchResponse = {
        request_id: raw.request_id || "",
        query: raw.query || request.query,
        is_in_scope: raw.status === "success" && products.length > 0,
        intent: raw.intent || null,
        top3: products,
        top1_handover: null,
        message: raw.message || null,
        needs_clarification: raw.needs_clarification || false,
        clarification_question: raw.clarification_question || null,
        clarification_options: raw.clarification_options || [],
        clarification_count: raw.clarification_count || 0,
        is_fallback: raw.is_fallback || false,
        timing_ms: raw.processing_time
            ? { total: Math.round(raw.processing_time * 1000) }
            : {},
        metadata: raw.steps || {},
        error: raw.status === "error" ? raw.message : null,
    };

    return mapped;
}

// ============================================================================
// Health Check
// ============================================================================

export async function healthCheck(): Promise<{
    status: string;
    [key: string]: unknown;
}> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
        throw new Error(`Health check failed: ${res.status}`);
    }
    return res.json();
}

// ============================================================================
// WebSocket STT Client
// ============================================================================

export interface STTCallbacks {
    onStarted?: (runId: string) => void;
    onInterim?: (text: string) => void;
    onFinal?: (text: string, confidence: number, status: string) => void;
    onError?: (message: string) => void;
    onClose?: () => void;
}

export class STTWebSocketClient {
    private ws: WebSocket | null = null;
    private audioContext: AudioContext | null = null;
    private mediaStream: MediaStream | null = null;
    private processor: ScriptProcessorNode | null = null;
    private source: MediaStreamAudioSourceNode | null = null;
    private seqCounter = 0;
    private callbacks: STTCallbacks;
    private isRecording = false;

    constructor(callbacks: STTCallbacks) {
        this.callbacks = callbacks;
    }

    /**
     * Start STT session: connect WebSocket + start microphone capture
     */
    async start(): Promise<void> {
        // 1. Connect WebSocket
        this.ws = new WebSocket(`${WS_BASE}/ws/stt`);
        this.seqCounter = 0;

        this.ws.onmessage = (event) => {
            try {
                const msg: STTServerMessage = JSON.parse(event.data);
                this.handleMessage(msg);
            } catch {
                console.error("Failed to parse STT message:", event.data);
            }
        };

        this.ws.onerror = (event) => {
            console.error("WebSocket error:", event);
            this.callbacks.onError?.("WebSocket 연결 오류가 발생했습니다.");
        };

        this.ws.onclose = () => {
            this.isRecording = false;
            this.callbacks.onClose?.();
        };

        // Wait for connection
        await new Promise<void>((resolve, reject) => {
            if (!this.ws) return reject(new Error("No WebSocket"));
            this.ws.onopen = () => resolve();
            setTimeout(() => reject(new Error("WebSocket connection timeout")), 5000);
        });

        // 2. Send start message
        this.ws.send(
            JSON.stringify({
                type: "start",
                config: { sample_rate: 16000, language: "ko-KR" },
                meta: {
                    run_id: `web_${Date.now()}`,
                    test_id: `session_${Date.now()}`,
                },
            })
        );

        // 3. Start microphone capture
        await this.startMicrophone();
    }

    /**
     * Start capturing microphone audio and sending to WebSocket
     */
    private async startMicrophone(): Promise<void> {
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                },
            });

            this.audioContext = new AudioContext({ sampleRate: 16000 });
            this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Use ScriptProcessorNode for PCM capture (4096 samples per buffer)
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.isRecording = true;

            this.processor.onaudioprocess = (event) => {
                if (!this.isRecording || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    return;
                }

                const inputData = event.inputBuffer.getChannelData(0);

                // Convert Float32 to Int16 PCM
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
                }

                // Convert to base64
                const bytes = new Uint8Array(pcm16.buffer);
                let binary = "";
                for (let i = 0; i < bytes.length; i++) {
                    binary += String.fromCharCode(bytes[i]);
                }
                const pcmB64 = btoa(binary);

                // Send audio chunk
                this.ws!.send(
                    JSON.stringify({
                        type: "audio",
                        pcm_b64: pcmB64,
                        seq: this.seqCounter++,
                    })
                );
            };

            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
        } catch (err) {
            console.error("Microphone access error:", err);
            this.callbacks.onError?.("마이크 접근 권한이 필요합니다.");
            throw err;
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    private handleMessage(msg: STTServerMessage): void {
        switch (msg.type) {
            case "started":
                this.callbacks.onStarted?.(msg.run_id);
                break;
            case "interim":
                this.callbacks.onInterim?.(msg.text);
                break;
            case "final":
                this.callbacks.onFinal?.(
                    msg.text,
                    msg.meta?.confidence ?? 0,
                    msg.status
                );
                // Auto-stop after final result
                this.stop();
                break;
            case "error":
                this.callbacks.onError?.(msg.message);
                break;
        }
    }

    /**
     * Stop STT session: stop microphone + close WebSocket
     */
    stop(): void {
        this.isRecording = false;

        // Stop microphone
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }
        if (this.audioContext) {
            this.audioContext.close().catch(() => { });
            this.audioContext = null;
        }
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach((track) => track.stop());
            this.mediaStream = null;
        }

        // Send stop message and close WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify({ type: "stop" }));
            } catch {
                // ignore
            }
            this.ws.close();
        }
        this.ws = null;
    }

    /**
     * Check if currently recording
     */
    get recording(): boolean {
        return this.isRecording;
    }
}
