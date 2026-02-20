# backend/stt/adapters.py
"""
STT Adapter Pattern Implementation
Whisper (faster-whisper) + Google Cloud Speech-to-Text
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .types import STTResult

# Conditional import for faster-whisper (optional dependency)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None
    WHISPER_AVAILABLE = False


class BaseAdapter(ABC):
    """Base interface for STT providers"""
    
    @abstractmethod
    def transcribe(self, audio_path: str) -> STTResult:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            STTResult with text_raw, confidence, lang, latency_ms, error
        """
        pass


class WhisperAdapter(BaseAdapter):
    """
    faster-whisper implementation with GPU acceleration
    Model: medium (default) with small fallback on OOM
    """
    
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cuda",
        compute_type: str = "float16",
        fallback_model: str = "small",
        language: str = "ko"
    ):
        if not WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper"
            )
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.fallback_model = fallback_model
        self.language = language
        self.model: Optional[WhisperModel] = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model with fallback strategy"""
        try:
            print(f"[WHISPER] Loading {self.model_size} model (device={self.device})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"[OK] {self.model_size} model loaded successfully")
        except OSError as e:
            if getattr(e, 'winerror', 0) == 1314:
                print(f"\n[CRITICAL] ?덈룄??沅뚰븳 ?ㅻ쪟 諛쒖깮 (WinError 1314)")
                print("HuggingFace 紐⑤뜽 濡쒕뱶 以??щ낵由?留곹겕 ?앹꽦???ㅽ뙣?덉뒿?덈떎.")
                print("?닿껐 諛⑸쾿:")
                print("1. ?곕???CMD/PowerShell)??'愿由ъ옄 沅뚰븳'?쇰줈 ?ㅼ떆 ?ㅽ뻾?댁＜?몄슂.")
                print("2. ?먮뒗 ?덈룄???ㅼ젙 > 媛쒖씤?뺣낫 諛?蹂댁븞 > 媛쒕컻?먯슜 > '媛쒕컻??紐⑤뱶'瑜?耳쒖＜?몄슂.\n")
                raise RuntimeError("愿由ъ옄 沅뚰븳???꾩슂?⑸땲??(WinError 1314)") from e
            raise

        except (RuntimeError, Exception) as e:
            print(f"[WARN] {self.model_size} model load failed: {e}")
            if self.fallback_model:
                print(f"[WHISPER] Falling back to {self.fallback_model} model...")
                try:
                    self.model = WhisperModel(
                        self.fallback_model,
                        device=self.device,
                        compute_type=self.compute_type
                    )
                    self.model_size = self.fallback_model
                    print(f"[OK] {self.fallback_model} model loaded successfully")
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Failed to load both {self.model_size} and {self.fallback_model}: {fallback_error}"
                    )
            else:
                raise
    
    def transcribe(self, audio_path: str) -> STTResult:
        """
        Transcribe audio using faster-whisper
        
        Returns:
            STTResult with confidence as average logprob (0-1 range, may be None)
        """
        start_time = time.time()
        
        try:
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Collect segments
            text_parts = []
            logprob_sum = 0
            segment_count = 0
            
            for segment in segments:
                text_parts.append(segment.text.strip())
                logprob_sum += segment.avg_logprob
                segment_count += 1
            
            full_text = " ".join(text_parts).strip()
            
            # Convert logprob to 0-1 confidence
            # logprob is typically -1 to 0, with 0 being most confident
            confidence = None
            if segment_count > 0:
                avg_logprob = logprob_sum / segment_count
                # Approximate conversion: exp(logprob) gives probability
                confidence = min(1.0, max(0.0, 1.0 + avg_logprob))
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return STTResult(
                text_raw=full_text if full_text else None,
                confidence=confidence,
                lang=self.language,
                latency_ms=latency_ms,
                error=None
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return STTResult(
                text_raw=None,
                confidence=None,
                lang=self.language,
                latency_ms=latency_ms,
                error=str(e)
            )


class GoogleAdapter(BaseAdapter):
    """
    Google Cloud Speech-to-Text v1 implementation
    Uses synchronous recognize for batch processing
    """
    
    def __init__(
        self,
        credentials_path: str = "google_key.json",
        language_code: str = "ko-KR",
        sample_rate_hertz: int = 16000,
        encoding: str = "LINEAR16"
    ):
        self.language_code = language_code
        self.sample_rate_hertz = sample_rate_hertz
        self.encoding = encoding
        self.credentials_path = credentials_path
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Google Speech client"""
        try:
            import os
            from google.cloud import speech
            from google.api_core.client_options import ClientOptions
            
            # 1. Try API Key from .env
            api_key = os.getenv("GOOGLE_API_KEY")
            
            # 2. Set credentials via JSON file if exists
            if self.credentials_path and Path(self.credentials_path).exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
                    Path(self.credentials_path).resolve()
                )
                self.client = speech.SpeechClient()
            elif api_key:
                # 3. Use API Key if JSON is missing but key is present
                print(f"[INFO] Using Google API Key for STT")
                client_options = ClientOptions(api_key=api_key)
                self.client = speech.SpeechClient(client_options=client_options)
            else:
                self.client = speech.SpeechClient()
            print(f"[OK] Google STT client initialized")
        except Exception as e:
            print(f"[ERROR] Google STT client init failed: {e}")
            self.client = None
    
    def transcribe(self, audio_path: str) -> STTResult:
        """
        Transcribe audio using Google Cloud Speech-to-Text
        
        Args:
            audio_path: Path to WAV file (must be LINEAR16, 16kHz, mono)
            
        Returns:
            STTResult with confidence from Google API
        """
        start_time = time.time()
        
        try:
            if not self.client:
                raise RuntimeError("Google STT client not initialized")
            
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            from google.cloud import speech
            
            # Read audio file and STRIP WAV HEADER (44 bytes)
            # Google STT (LINEAR16) expects raw PCM bytes, but pydub exports with WAV header.
            with open(audio_path, "rb") as f:
                header = f.read(44) # Read header
                audio_content = f.read() # Read remaining raw PCM data
            
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Explicitly use LINEAR16 with raw PCM data
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate_hertz,
                language_code=self.language_code,
                enable_automatic_punctuation=True,
            )
            
            # Synchronous recognize
            response = self.client.recognize(config=config, audio=audio)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract results
            if response.results:
                result = response.results[0]
                if result.alternatives:
                    alt = result.alternatives[0]
                    return STTResult(
                        text_raw=alt.transcript,
                        confidence=alt.confidence if alt.confidence > 0 else None,
                        lang=self.language_code[:2],
                        latency_ms=latency_ms,
                        error=None
                    )
            
            # No results
            return STTResult(
                text_raw=None,
                confidence=None,
                lang=self.language_code[:2],
                latency_ms=latency_ms,
                error=None
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return STTResult(
                text_raw=None,
                confidence=None,
                lang=self.language_code[:2],
                latency_ms=latency_ms,
                error=str(e)
            )


def get_adapter(provider: str, **kwargs) -> BaseAdapter:
    """
    Factory function to create STT adapter
    
    Args:
        provider: "whisper" or "google"
        **kwargs: Provider-specific configuration
        
    Returns:
        BaseAdapter instance
    """
    if provider == "whisper":
        return WhisperAdapter(**kwargs)
    elif provider == "google":
        return GoogleAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'whisper' or 'google'.")
