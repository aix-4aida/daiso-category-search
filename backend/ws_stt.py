# backend/ws_stt.py
"""
WebSocket endpoint for real-time streaming STT
Uses Google Cloud Speech-to-Text v1 API with SpeechHelpers signature
STT WORKER THREAD VERSION - streaming_recognize + response iteration in same thread

v2: Whisper Fallback + TextPostprocessor
- Google Streaming 실패 시 Ring buffer PCM을 Whisper로 fallback 인식
- TextPostprocessor로 후처리 (추임새 제거, 단위 정규화)
- config.yaml 기반 설정 (fallback, postprocessing)
"""

import asyncio
import json
import time
import base64
import threading
import struct
import traceback
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Iterator, Dict
from queue import Queue, Empty
from fastapi import WebSocket, WebSocketDisconnect

# v1 API imports (graceful fallback for testing)
try:
    from google.cloud.speech_v1 import SpeechClient
    from google.cloud.speech_v1.types import (
        RecognitionConfig,
        StreamingRecognitionConfig,
        StreamingRecognizeRequest
    )
    from google.oauth2 import service_account
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    SpeechClient = None  # type: ignore[assignment,misc]
    RecognitionConfig = None  # type: ignore[assignment,misc]
    StreamingRecognitionConfig = None  # type: ignore[assignment,misc]
    StreamingRecognizeRequest = None  # type: ignore[assignment,misc]
    service_account = None  # type: ignore[assignment]
    GOOGLE_STT_AVAILABLE = False

# Whisper Fallback imports
WHISPER_ADAPTER_AVAILABLE = False
WhisperAdapter = None  # type: ignore[assignment]
for _mod_path in ("poc.lsy.stt.adapters", "poc.stt.adapters", "backend.stt.adapters"):
    try:
        import importlib
        _mod = importlib.import_module(_mod_path)
        WhisperAdapter = getattr(_mod, "WhisperAdapter")
        WHISPER_ADAPTER_AVAILABLE = True
        break
    except (ImportError, AttributeError):
        continue

# TextPostprocessor imports
POSTPROCESSOR_AVAILABLE = False
TextPostprocessor = None  # type: ignore[assignment]
for _mod_path in ("poc.lsy.stt.text_postprocessor", "poc.stt.text_postprocessor", "backend.stt.text_postprocessor"):
    try:
        _mod = importlib.import_module(_mod_path)
        TextPostprocessor = getattr(_mod, "TextPostprocessor")
        POSTPROCESSOR_AVAILABLE = True
        break
    except (ImportError, AttributeError):
        continue

# Audio preprocessor (volume normalization, denoise)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import numpy as np
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False

# Config loader
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ─── MissingDependencyError ────────────────────────────────────────────────────

class MissingDependencyError(RuntimeError):
    """Raised when an enabled feature requires a package that is not installed."""
    pass


def check_required_deps(config: Dict) -> None:
    """Validate that every *enabled* feature has its required packages installed.

    Raises MissingDependencyError with a FATAL message listing the missing package
    if an enabled feature cannot find its dependency.

    Rules:
      - stt.google.enabled=true  → google-cloud-speech must be importable
      - fallback.enabled=true    → faster-whisper (WhisperAdapter) must be importable
      - postprocessing.enabled=true → TextPostprocessor must be importable
    """
    errors: list[str] = []

    # Google STT
    google_enabled = config.get("stt", {}).get("google", {}).get("enabled", True)
    if google_enabled and not GOOGLE_STT_AVAILABLE:
        errors.append("FATAL: stt.google.enabled=true but 'google-cloud-speech' is not installed")

    # Whisper fallback
    fallback_enabled = config.get("fallback", {}).get("enabled", False)
    if fallback_enabled and not WHISPER_ADAPTER_AVAILABLE:
        errors.append("FATAL: fallback.enabled=true but 'faster-whisper' (WhisperAdapter) is not installed")

    # Postprocessor
    pp_enabled = config.get("postprocessing", {}).get("enabled", False)
    if pp_enabled and not POSTPROCESSOR_AVAILABLE:
        errors.append("FATAL: postprocessing.enabled=true but TextPostprocessor is not installed")

    if errors:
        msg = "\n".join(errors)
        print(msg)
        raise MissingDependencyError(msg)


# ─── Session configuration ────────────────────────────────────────────────────

MAX_SESSION_DURATION_SEC = 30
SILENCE_TIMEOUT_SEC = 3.0
SAMPLE_RATE = 16000
LANGUAGE_CODE = "ko-KR"

# Ring buffer default (config에서 override)
DEFAULT_BUFFER_MAX_SEC = 8

# Logging configuration
CSV_LOG_PATH = Path("outputs/streaming_poc_results.csv")
AUDIO_SAVE_DIR = Path("outputs/streaming_audio")
AUDIO_SAVE_ENABLED = False  # Feature flag (controlled by metadata)

# CSV Header (v2: fallback columns 추가)
CSV_HEADER = [
    "timestamp", "run_id", "test_id", "utterance_type", "spoken_text_ref",
    "text_raw", "text_processed", "final_transcript",
    "confidence", "status", "failure_reason",
    "first_interim_latency_ms", "final_latency_ms", "duration_sec",
    "chunk_count", "audio_path",
    "fallback_used", "fallback_provider", "fallback_latency_ms",
    "fallback_reason"
]

# Thread lock for CSV writing
csv_lock = threading.Lock()


# ─── Config Loading ───────────────────────────────────────────────────────────

def _find_config_yaml() -> Optional[Path]:
    """Search for config.yaml in common locations."""
    candidates = [
        Path(__file__).resolve().parent / "config.yaml",       # backend/config.yaml
        Path("backend") / "config.yaml",
        Path("config.yaml"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_fallback_config() -> Dict:
    """Load fallback section from config.yaml. Returns {} if not found."""
    if not YAML_AVAILABLE:
        return {"enabled": False}
    path = _find_config_yaml()
    if not path:
        return {"enabled": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("fallback", {"enabled": False})
    except Exception:
        return {"enabled": False}


def load_postprocessing_config() -> Dict:
    """Load postprocessing section from config.yaml. Returns {} if not found."""
    if not YAML_AVAILABLE:
        return {}
    path = _find_config_yaml()
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("postprocessing", {})
    except Exception:
        return {}


# ─── Singleton Postprocessor ──────────────────────────────────────────────────

_postprocessor_instance: Optional[object] = None


def get_postprocessor():
    """Return singleton TextPostprocessor (or None if unavailable)."""
    global _postprocessor_instance
    if _postprocessor_instance is not None:
        return _postprocessor_instance
    if not POSTPROCESSOR_AVAILABLE:
        return None
    try:
        pp_config = load_postprocessing_config()
        if not pp_config.get("enabled", True):
            return None
        _postprocessor_instance = TextPostprocessor(config=pp_config)
        return _postprocessor_instance
    except Exception:
        return None


# ─── CSV Logging ──────────────────────────────────────────────────────────────

def append_to_csv_log(row_data: Dict):
    """Thread-safe CSV append"""
    try:
        is_new = not CSV_LOG_PATH.exists()
        CSV_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with csv_lock:
            with open(CSV_LOG_PATH, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
                if is_new:
                    writer.writeheader()
                safe_row = {k: row_data.get(k, "") for k in CSV_HEADER}
                writer.writerow(safe_row)
    except Exception as e:
        print(f"CSV Log Error: {e}")


# ============================================================
# WhisperFallbackManager: process singleton, lazy load
# ============================================================

class WhisperFallbackManager:
    """
    Process-level singleton Whisper model.
    - Loaded lazily on first fallback request.
    - Thread-safe via Lock.
    """
    _instance: Optional['WhisperFallbackManager'] = None
    _init_lock = threading.Lock()
    _transcribe_lock = threading.Lock()

    def __init__(self):
        self.model = None
        self._loaded = False
        self._fallback_config = load_fallback_config()

    @classmethod
    def get_instance(cls) -> 'WhisperFallbackManager':
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _ensure_loaded(self):
        if self._loaded:
            return
        with self._init_lock:
            if self._loaded:
                return
            whisper_cfg = self._fallback_config.get("whisper", {})
            if not WHISPER_ADAPTER_AVAILABLE:
                self._loaded = True
                return
            try:
                self.model = WhisperAdapter(
                    model_size=whisper_cfg.get("model_size", "small"),
                    device=whisper_cfg.get("device", "cpu"),
                    compute_type=whisper_cfg.get("compute_type", "int8"),
                    fallback_model=whisper_cfg.get("fallback_model", "small"),
                    language=whisper_cfg.get("language", "ko"),
                )
            except Exception as e:
                print(f"Whisper fallback model load failed: {e}")
                self.model = None
            self._loaded = True

    def is_available(self) -> bool:
        if not self._fallback_config.get("enabled", False):
            return False
        if not WHISPER_ADAPTER_AVAILABLE:
            return False
        self._ensure_loaded()
        return self.model is not None

    def transcribe_fallback(self, pcm_bytes: bytes) -> Dict:
        """
        Run Whisper fallback on PCM bytes.
        Returns {"text_raw": str, "text_processed": str, "confidence": float,
                 "latency_ms": int, "error": str|None}
        """
        self._ensure_loaded()
        if not self.model:
            return {"text_raw": "", "text_processed": "", "confidence": 0.0,
                    "latency_ms": 0, "error": "Whisper model not loaded"}

        preprocess_cfg = self._fallback_config.get("preprocess", {})

        # Preprocess: volume normalize + denoise
        processed_bytes = pcm_bytes
        if PYDUB_AVAILABLE:
            try:
                processed_bytes = self._preprocess_pcm(pcm_bytes, preprocess_cfg)
            except Exception:
                pass

        with self._transcribe_lock:
            result = self.model.transcribe_bytes(processed_bytes, sample_rate=SAMPLE_RATE)

        text_raw = result.text_raw or ""

        # Postprocess
        text_processed = text_raw
        pp_config = load_postprocessing_config()
        if text_raw and pp_config.get("apply_to_fallback", True):
            pp = get_postprocessor()
            if pp:
                try:
                    text_processed = pp.postprocess(text_raw)
                except Exception:
                    pass

        return {
            "text_raw": text_raw,
            "text_processed": text_processed,
            "confidence": result.confidence or 0.0,
            "latency_ms": result.latency_ms,
            "error": result.error,
        }

    def _preprocess_pcm(self, pcm_bytes: bytes, config: Dict) -> bytes:
        """Volume normalize + denoise on raw PCM bytes (no temp files)."""
        audio = AudioSegment(
            data=pcm_bytes, sample_width=2, frame_rate=SAMPLE_RATE, channels=1,
        )
        if config.get("volume_normalize", True):
            target = config.get("target_dBFS", -20.0)
            change = target - audio.dBFS
            change = max(-30, min(30, change))
            audio = audio.apply_gain(change)
        if config.get("denoise", True) and NOISEREDUCE_AVAILABLE:
            samples = np.array(audio.get_array_of_samples())
            reduced = nr.reduce_noise(
                y=samples.astype(np.float32), sr=SAMPLE_RATE,
                prop_decrease=0.8, stationary=True,
            )
            audio = audio._spawn(reduced.astype(np.int16).tobytes())
        return audio.raw_data


# ============================================================
# StreamingSTTSession: Google Streaming + Whisper Fallback
# ============================================================

class StreamingSTTSession:
    """
    Streaming STT session:
    - WS thread: receives audio -> queue.put()
    - STT worker thread: streaming_recognize + response iteration
    - Fallback: SILENCE stop without final -> Whisper recognition
    """

    def __init__(self, websocket: WebSocket, credentials_path: str, meta: dict = None):
        self.websocket = websocket
        self.credentials_path = credentials_path
        self.meta = meta or {}
        self.run_id = self.meta.get("run_id", "default_run")
        self.test_id = self.meta.get("test_id", f"test_{int(time.time())}")
        self.save_audio = self.meta.get("save_audio", False)

        self.client = None

        # Timing
        self.start_ts: Optional[float] = None
        self.first_interim_ts: Optional[float] = None
        self.final_ts: Optional[float] = None
        self.last_audio_ts: Optional[float] = None

        # State
        self.is_running = False
        self.stop_event = threading.Event()
        self.audio_queue: Queue = Queue()
        self.result_queue: Queue = Queue()
        self.chunk_count = 0
        self.response_count = 0

        # Ring buffer: ALWAYS active (for fallback, not gated by save_audio)
        self.full_audio_buffer = bytearray()
        fb_cfg = load_fallback_config()
        buffer_sec = fb_cfg.get("buffer_max_sec", DEFAULT_BUFFER_MAX_SEC)
        self._buffer_max_bytes = SAMPLE_RATE * 2 * buffer_sec

        # Postprocessor reference (singleton)
        self._postprocessor = get_postprocessor()
        self._pp_config = load_postprocessing_config()

        # Fallback state
        self._fallback_triggered = False
        self._got_final = False
        self._fallback_result: Optional[Dict] = None
        self.force_fallback = self.meta.get("force_fallback", False)

        # Thread reference
        self.worker_thread = None

    async def initialize(self):
        """Initialize Google STT client."""
        if not GOOGLE_STT_AVAILABLE:
            msg = "FATAL: google-cloud-speech is not installed"
            print(msg)
            await self.send_message({
                "type": "error",
                "code": "MISSING_DEP",
                "message": msg,
            })
            return False
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = SpeechClient(credentials=credentials)
            return True
        except Exception as e:
            traceback.print_exc()
            await self.send_error(str(e))
            return False

    async def send_message(self, msg: dict):
        try:
            await self.websocket.send_json(msg)
        except Exception:
            pass

    async def send_error(self, msg: str):
        await self.send_message({"type": "error", "message": msg})

    async def send_interim(self, text: str):
        if self.first_interim_ts is None:
            self.first_interim_ts = time.time()
        await self.send_message({"type": "interim", "text": text, "is_final": False})

    async def send_final(
        self,
        text_raw: str = "",
        text_processed: str = "",
        confidence: float = 0.0,
        status: str = "OK",
        failure_reason: str = "",
        fallback_used: bool = False,
        fallback_provider: str = "",
        fallback_latency_ms: int = 0,
        fallback_reason: str = "",
        # backward compat: accept 'text' kwarg, map to text_raw
        text: str = "",
    ):
        # backward compat
        if text and not text_raw:
            text_raw = text

        self.final_ts = time.time()
        final_text = text_processed if text_processed else text_raw

        duration_sec = (self.final_ts - self.start_ts) if self.start_ts else 0
        final_latency_ms = int(duration_sec * 1000)
        first_interim_latency = (
            int((self.first_interim_ts - self.start_ts) * 1000)
            if self.first_interim_ts and self.start_ts else None
        )

        meta = {
            "confidence": round(confidence, 4),
            "latency_ms": final_latency_ms,
            "first_interim_ms": first_interim_latency,
            "duration_sec": round(duration_sec, 2),
            "text_raw": text_raw,
            "text_processed": text_processed,
            "fallback_used": fallback_used,
            "fallback_provider": fallback_provider,
            "fallback_latency_ms": fallback_latency_ms,
            "fallback_reason": fallback_reason,
        }

        await self.send_message({
            "type": "final", "text": final_text, "is_final": True,
            "status": status, "meta": meta,
        })

        # Save Audio if enabled
        audio_path_str = ""
        if self.save_audio or AUDIO_SAVE_ENABLED:
            try:
                AUDIO_SAVE_DIR.mkdir(parents=True, exist_ok=True)
                filename = f"{self.run_id}_{self.test_id}.wav"
                filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
                save_path = AUDIO_SAVE_DIR / filename
                with open(save_path, "wb") as f:
                    f.write(struct.pack('<4sI4s', b'RIFF', 36 + len(self.full_audio_buffer), b'WAVE'))
                    f.write(struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16))
                    f.write(struct.pack('<4sI', b'data', len(self.full_audio_buffer)))
                    f.write(self.full_audio_buffer)
                audio_path_str = str(save_path)
            except Exception:
                pass

        # Log to CSV
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "test_id": self.test_id,
            "utterance_type": self.meta.get("utterance_type", ""),
            "spoken_text_ref": self.meta.get("spoken_text", ""),
            "text_raw": text_raw,
            "text_processed": text_processed,
            "final_transcript": final_text,
            "confidence": round(confidence, 4),
            "status": status,
            "failure_reason": failure_reason,
            "first_interim_latency_ms": first_interim_latency if first_interim_latency else "",
            "final_latency_ms": final_latency_ms,
            "duration_sec": round(duration_sec, 2),
            "chunk_count": self.chunk_count,
            "audio_path": audio_path_str,
            "fallback_used": fallback_used,
            "fallback_provider": fallback_provider,
            "fallback_latency_ms": fallback_latency_ms,
            "fallback_reason": fallback_reason,
        }
        append_to_csv_log(log_data)

    def _audio_generator(self) -> Iterator:
        """Queue-based audio generator (runs in STT worker thread)."""
        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.2)
                if chunk is None:
                    break
                self.chunk_count += 1

                # Ring buffer: ALWAYS accumulate (for fallback)
                self.full_audio_buffer.extend(chunk)
                if len(self.full_audio_buffer) > self._buffer_max_bytes:
                    overflow = len(self.full_audio_buffer) - self._buffer_max_bytes
                    del self.full_audio_buffer[:overflow]

                if GOOGLE_STT_AVAILABLE and StreamingRecognizeRequest is not None:
                    yield StreamingRecognizeRequest(audio_content=chunk)
                else:
                    yield chunk

            except Empty:
                if self.stop_event.is_set():
                    break
                continue

    def _stt_worker_thread(self):
        """STT worker: streaming_recognize + response iteration."""
        try:
            recognition_config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLE_RATE,
                language_code=LANGUAGE_CODE,
                enable_automatic_punctuation=True,
            )
            streaming_config = StreamingRecognitionConfig(
                config=recognition_config,
                interim_results=True,
                single_utterance=True,
            )
            responses = self.client.streaming_recognize(
                config=streaming_config,
                requests=self._audio_generator(),
            )

            for response in responses:
                self.response_count += 1
                for result in response.results:
                    if not result.alternatives:
                        continue
                    alt = result.alternatives[0]
                    text = alt.transcript
                    conf = getattr(alt, 'confidence', 0.0)

                    if result.is_final:
                        self._got_final = True
                        if self.force_fallback:
                            self.result_queue.put({
                                "type": "final", "text": "", "confidence": 0.0,
                                "status": "FORCE_FALLBACK",
                                "reason": "force_fallback enabled",
                                "needs_fallback": True,
                                "google_text": text, "google_confidence": conf,
                            })
                        else:
                            self.result_queue.put({
                                "type": "final", "text": text, "confidence": conf,
                            })
                        self.stop_event.set()
                        return
                    else:
                        self.result_queue.put({"type": "interim", "text": text})

            # Response loop ended without final
            status = "NO_SPEECH" if self.chunk_count == 0 else "TOO_SHORT"
            self.result_queue.put({
                "type": "final", "text": "", "confidence": 0.0,
                "status": status, "reason": "No final result",
                "needs_fallback": True,
            })

        except Exception as e:
            traceback.print_exc()
            self.result_queue.put({
                "type": "error", "message": str(e), "needs_fallback": True,
            })

    def _run_whisper_fallback(self) -> Dict:
        """Run Whisper fallback on ring buffer content."""
        manager = WhisperFallbackManager.get_instance()
        if not manager.is_available():
            return {"text_raw": "", "text_processed": "", "confidence": 0.0,
                    "latency_ms": 0, "provider": "whisper",
                    "error": "Fallback not available"}

        buffer_bytes = bytes(self.full_audio_buffer)
        if len(buffer_bytes) < 3200:  # min 100ms
            return {"text_raw": "", "text_processed": "", "confidence": 0.0,
                    "latency_ms": 0, "provider": "whisper",
                    "error": "Buffer too short"}

        result = manager.transcribe_fallback(buffer_bytes)
        result["provider"] = "whisper"
        return result

    async def process_audio(self, pcm_b64: str, seq: int):
        """Called from WS thread - puts audio into queue for worker."""
        try:
            audio = base64.b64decode(pcm_b64)
            self.audio_queue.put(audio)
            self.last_audio_ts = time.time()
        except Exception:
            pass

    async def start(self):
        self.is_running = True
        self.start_ts = time.time()
        self.stop_event.clear()

        self.worker_thread = threading.Thread(target=self._stt_worker_thread, daemon=True)
        self.worker_thread.start()

        asyncio.create_task(self._process_results())
        asyncio.create_task(self._monitor_session())

    async def _process_results(self):
        """Process results from STT worker, trigger fallback if needed, send to WS."""
        while self.is_running:
            try:
                r = self.result_queue.get_nowait()

                if r["type"] == "interim":
                    await self.send_interim(r["text"])

                elif r["type"] == "final":
                    text_raw = r["text"]
                    confidence = r.get("confidence", 0.0)
                    status = r.get("status", "OK")
                    reason = r.get("reason", "")
                    needs_fallback = r.get("needs_fallback", False)

                    fallback_used = False
                    fallback_provider = ""
                    fallback_latency_ms = 0
                    fallback_reason = ""
                    fb_result = {}

                    # Fallback trigger
                    if (
                        needs_fallback
                        and (not text_raw or text_raw.strip() == "")
                        and not self._fallback_triggered
                        and len(self.full_audio_buffer) > 3200
                    ):
                        self._fallback_triggered = True
                        if self.force_fallback:
                            fallback_reason = "FORCE"
                        else:
                            fallback_reason = "SILENCE_NO_FINAL"

                        fb_result = await asyncio.get_event_loop().run_in_executor(
                            None, self._run_whisper_fallback,
                        )

                        if fb_result.get("text_raw") or fb_result.get("text_processed"):
                            text_raw = fb_result.get("text_raw", "")
                            confidence = fb_result.get("confidence", 0.0)
                            status = "FALLBACK_OK"
                            reason = ""
                            fallback_used = True
                            fallback_provider = fb_result.get("provider", "whisper")
                            fallback_latency_ms = fb_result.get("latency_ms", 0)
                        else:
                            status = "FALLBACK_FAIL"
                            reason = fb_result.get("error", "Fallback returned empty")
                            fallback_used = True
                            fallback_provider = "whisper"
                            fallback_latency_ms = fb_result.get("latency_ms", 0)

                    # Postprocess
                    text_processed = text_raw
                    if fallback_used:
                        text_processed = fb_result.get("text_processed", text_raw)
                    elif text_raw and self._pp_config.get("apply_to_google", True):
                        pp = get_postprocessor()
                        if pp:
                            try:
                                text_processed = pp.postprocess(text_raw)
                            except Exception:
                                pass

                    await self.send_final(
                        text_raw=text_raw, text_processed=text_processed,
                        confidence=confidence,
                        status=status, failure_reason=reason,
                        fallback_used=fallback_used,
                        fallback_provider=fallback_provider,
                        fallback_latency_ms=fallback_latency_ms,
                        fallback_reason=fallback_reason,
                    )
                    self.is_running = False
                    self.stop_event.set()

                elif r["type"] == "error":
                    needs_fallback = r.get("needs_fallback", False)
                    error_msg = r["message"]

                    fallback_used = False
                    fallback_provider = ""
                    fallback_latency_ms = 0
                    fallback_reason = ""
                    text_raw = ""
                    text_processed = ""
                    status = "FAIL"
                    fb_result = {}

                    if (
                        needs_fallback
                        and not self._fallback_triggered
                        and len(self.full_audio_buffer) > 3200
                    ):
                        self._fallback_triggered = True
                        fallback_reason = "GOOGLE_ERROR"

                        fb_result = await asyncio.get_event_loop().run_in_executor(
                            None, self._run_whisper_fallback,
                        )

                        if fb_result.get("text_raw") or fb_result.get("text_processed"):
                            text_raw = fb_result.get("text_raw", "")
                            text_processed = fb_result.get("text_processed", text_raw)
                            status = "FALLBACK_OK"
                            error_msg = ""
                            fallback_used = True
                            fallback_provider = fb_result.get("provider", "whisper")
                            fallback_latency_ms = fb_result.get("latency_ms", 0)
                        else:
                            fallback_used = True
                            fallback_provider = "whisper"
                            fallback_latency_ms = fb_result.get("latency_ms", 0)
                            status = "FALLBACK_FAIL"

                    if not fallback_used:
                        await self.send_error(error_msg)

                    await self.send_final(
                        text_raw=text_raw, text_processed=text_processed,
                        status=status, failure_reason=error_msg,
                        fallback_used=fallback_used,
                        fallback_provider=fallback_provider,
                        fallback_latency_ms=fallback_latency_ms,
                        fallback_reason=fallback_reason,
                    )
                    self.is_running = False
                    self.stop_event.set()

            except Empty:
                await asyncio.sleep(0.05)

    async def _monitor_session(self):
        """Monitor for timeout conditions."""
        while self.is_running and not self.stop_event.is_set():
            await asyncio.sleep(0.1)
            now = time.time()
            if self.start_ts and (now - self.start_ts) >= MAX_SESSION_DURATION_SEC:
                await self.stop("TIMEOUT")
                return
            if self.last_audio_ts and (now - self.last_audio_ts) >= SILENCE_TIMEOUT_SEC:
                await self.stop("SILENCE")
                return

    async def stop(self, reason: str = "USER_STOP"):
        if self.stop_event.is_set():
            return
        self.stop_event.set()

        # Inject ~500ms silence to help STT finalize
        silence_frame = b'\x00' * 16000
        self.audio_queue.put(silence_frame)
        self.audio_queue.put(None)  # Poison pill

        if self.worker_thread and self.worker_thread.is_alive():
            await asyncio.get_event_loop().run_in_executor(
                None, self.worker_thread.join, 2.0,
            )

        for _ in range(10):
            if not self.is_running:
                break
            await asyncio.sleep(0.1)
        self.is_running = False


# ============================================================
# WebSocket Handler
# ============================================================

async def handle_streaming_stt(websocket: WebSocket, credentials_path: str = None):
    await websocket.accept()

    session = None

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "start":
                meta = msg.get("meta", {})

                if not credentials_path:
                    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if not credentials_path:
                    credentials_path = "backend/daisoproject-sst.json"

                session = StreamingSTTSession(websocket, credentials_path, meta=meta)
                if await session.initialize():
                    await session.start()
                    await websocket.send_json({"type": "started", "run_id": session.run_id})
                else:
                    await websocket.send_json({"type": "error", "message": "Init failed"})

            elif msg["type"] == "audio" and session:
                await session.process_audio(msg.get("pcm_b64", ""), msg.get("seq", 0))

            elif msg["type"] == "stop" and session:
                await session.stop("USER_STOP")
                session = None

    except WebSocketDisconnect:
        if session:
            await session.stop("DISCONNECT")
    except RuntimeError as e:
        if "WebSocket is not connected" in str(e):
            if session:
                await session.stop("DISCONNECT")
        else:
            traceback.print_exc()
            if session:
                await session.stop("ERROR")
    except Exception:
        traceback.print_exc()
        if session:
            await session.stop("ERROR")
