/**
 * AudioRecorder.js
 * 
 * Records audio from the browser microphone and converts it to
 * 16kHz, 16-bit, Mono PCM format in real-time.
 * 
 * Uses AudioWorklet or ScriptProcessor (fallback) for raw audio access.
 */

export class AudioRecorder {
    constructor() {
        this.context = null;
        this.input = null;
        this.processor = null;
        this.stream = null;
        this.onAudioProcess = null; // Callback function(pcmData: Int16Array)
    }

    async start(onAudioProcess) {
        if (this.context) {
            await this.stop();
        }

        this.onAudioProcess = onAudioProcess;

        try {
            // 1. Request Microphone Access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100 // Request standard, will downsample later
                }
            });

            // 2. Create Audio Context (force 16kHz if possible, but browsers might ignore)
            // We will downsample manually to be safe.
            this.context = new (window.AudioContext || window.webkitAudioContext)();

            // 3. Create Source
            this.input = this.context.createMediaStreamSource(this.stream);

            // 4. Create Processor (ScriptProcessorNode is deprecated but widely supported for this simple use case over AudioWorklet for now)
            // Buffer size 4096 is a good balance between latency and performance
            this.processor = this.context.createScriptProcessor(4096, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (!this.onAudioProcess) return;

                const inputData = e.inputBuffer.getChannelData(0); // Float32Array (44.1kHz or 48kHz usually)
                const inputSampleRate = this.context.sampleRate;
                const targetSampleRate = 16000;

                // Downsample and convert to Int16
                const pcm16 = this.downsampleBuffer(inputData, inputSampleRate, targetSampleRate);

                if (pcm16.length > 0) {
                    this.onAudioProcess(pcm16);
                }
            };

            // 5. Connect
            this.input.connect(this.processor);
            this.processor.connect(this.context.destination); // Needed for Chrome to activate processor

            console.log(`🎤 Recording started: ${this.context.sampleRate}Hz -> 16000Hz`);
        } catch (e) {
            console.error("AudioRecorder start failed:", e);
            throw e;
        }
    }

    stop() {
        if (this.processor) {
            this.processor.disconnect();
            this.processor.onaudioprocess = null;
        }
        if (this.input) {
            this.input.disconnect();
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.context && this.context.state !== 'closed') {
            this.context.close();
        }

        this.processor = null;
        this.input = null;
        this.stream = null;
        this.context = null;
        console.log("🎤 Recording stopped");
    }

    /**
     * Simple linear interpolation downsampling and Float32 -> Int16 conversion
     */
    downsampleBuffer(buffer, sampleRate, outSampleRate) {
        if (outSampleRate === sampleRate) {
            return this.floatTo16BitPCM(buffer);
        }
        if (outSampleRate > sampleRate) {
            throw new Error("Upsampling not supported");
        }

        const sampleRateRatio = sampleRate / outSampleRate;
        const newLength = Math.round(buffer.length / sampleRateRatio);
        const result = new Int16Array(newLength);

        let offsetResult = 0;
        let offsetBuffer = 0;

        while (offsetResult < result.length) {
            const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);

            // Use simple averaging for anti-aliasing (rudimentary)
            let accum = 0, count = 0;
            for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                accum += buffer[i];
                count++;
            }

            const val = count ? accum / count : 0;

            // Float to Int16
            const s = Math.max(-1, Math.min(1, val));
            result[offsetResult] = s < 0 ? s * 0x8000 : s * 0x7FFF;

            offsetResult++;
            offsetBuffer = nextOffsetBuffer;
        }

        return result;
    }

    floatTo16BitPCM(input) {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output;
    }
}
