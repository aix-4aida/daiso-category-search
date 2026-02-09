"""
STT 서비스 - 오디오 파일을 텍스트로 변환
기존 stt_to_json.py의 핵심 로직을 서비스화
"""
import os
import sys
import time
from pathlib import Path

# Project root 설정
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.stt.adapters import get_adapter
from backend.stt.audio_converter import normalize_audio

# FFmpeg 설정
from pydub import AudioSegment
current_dir = Path(__file__).resolve().parent
local_ffmpeg = current_dir / "ffmpeg.exe"
if local_ffmpeg.exists():
    AudioSegment.converter = str(local_ffmpeg)


def run_stt(audio_file_path: str, provider: str = "whisper") -> dict:
    """
    단일 오디오 파일을 STT 처리합니다.
    
    Args:
        audio_file_path: 오디오 파일 경로
        provider: STT 제공자 (기본값: whisper)
        
    Returns:
        dict: {"text": str, "latency_ms": int, "confidence": float, "error": str|None}
    """
    start_time = time.time()
    
    try:
        # 어댑터 초기화
        adapter = get_adapter(provider, model_size="medium", device="cpu", compute_type="int8")
        
        # 오디오 정규화
        norm_result = normalize_audio(audio_file_path)
        target_audio = norm_result["normalized_path"]
        
        # 변환
        stt_result = adapter.transcribe(target_audio)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "text": stt_result.text_raw if not stt_result.error else "",
            "latency_ms": latency_ms,
            "confidence": stt_result.confidence,
            "error": stt_result.error
        }
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "text": "",
            "latency_ms": latency_ms,
            "confidence": 0.0,
            "error": str(e)
        }
