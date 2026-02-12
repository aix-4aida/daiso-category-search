"""
STT 서비스 - 오디오 파일을 텍스트로 변환
기존 stt_to_json.py의 핵심 로직을 서비스화
Refactored to use backend/stt/config.yaml
"""
import os
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Optional

# Project root 설정
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.stt.adapters import get_adapter
from backend.stt.audio_converter import normalize_audio

from backend.stt.audio_preprocessor import AudioPreprocessor
from backend.stt.text_postprocessor import TextPostprocessor

# FFmpeg 설정
from pydub import AudioSegment
current_dir = Path(__file__).resolve().parent
local_ffmpeg = current_dir / "ffmpeg.exe"
if local_ffmpeg.exists():
    AudioSegment.converter = str(local_ffmpeg)

# ==========================================
# Config Loading
# ==========================================
def load_stt_config() -> Dict:
    """Load config.yaml from backend/stt or other locations"""
    candidate_paths = [
        # backend/stt/config.yaml (Standard)
        project_root / "backend" / "stt" / "config.yaml",
        # Relative to this file: ../../backend/stt/config.yaml
        Path(__file__).resolve().parent.parent / "stt" / "config.yaml",
        # Fallback
        project_root / "config.yaml"
    ]
    
    for config_path in candidate_paths:
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                return config
            except Exception as e:
                print(f"[WARN] Failed to load config from {config_path}: {e}")
    
    print("[WARN] No config.yaml found. Using defaults.")
    return {}

# Load config once
_STT_CONFIG = load_stt_config()

# 전처리/후처리 인스턴스 (Config 적용)
_pp_config = _STT_CONFIG.get("postprocessing", {})
audio_preprocessor = AudioPreprocessor()
text_postprocessor = TextPostprocessor(config=_pp_config)


def run_stt(audio_file_path: str, provider: str = "whisper") -> dict:
    """
    단일 오디오 파일을 STT 처리합니다. (전처리/후처리 포함)
    backend/stt/config.yaml 설정을 따릅니다.
    
    Args:
        audio_file_path: 오디오 파일 경로
        provider: STT 제공자 (기본값: whisper, config에 의해 override 가능)
        
    Returns:
        dict: {"text": str, "latency_ms": int, "confidence": float, "error": str|None}
    """
    start_time = time.time()
    
    # Config Shortcuts
    stt_cfg = _STT_CONFIG.get("stt", {})
    fallback_cfg = _STT_CONFIG.get("fallback", {})
    
    try:
        # 1. 오디오 전처리 (볼륨 정규화 등)
        # Preprocessing config
        prep_cfg = _STT_CONFIG.get("preprocessing", {})
        
        preprocessed_path, meta = audio_preprocessor.preprocess(
            audio_path=audio_file_path,
            config={
                "volume_normalize": prep_cfg.get("volume_normalize", True), 
                "target_dBFS": prep_cfg.get("target_dBFS", -20.0)
            },
            test_id=f"stt_service_{int(start_time)}",
            provider=provider
        )
        
        target_audio = preprocessed_path
        
        # 어댑터 초기화 (Google First -> Whisper Fallback scope)
        google_adapter = None
        whisper_adapter = None
        
        # Whisper Config
        whisper_cfg = stt_cfg.get("whisper", {})
        whisper_model = whisper_cfg.get("model_size", "medium")
        whisper_device = whisper_cfg.get("device", "cpu")
        whisper_compute = whisper_cfg.get("compute_type", "int8")
        
        # 1. Initialize Whisper (Always, for fallback or primary)
        try:
            whisper_adapter = get_adapter(
                "whisper", 
                model_size=whisper_model, 
                device=whisper_device, 
                compute_type=whisper_compute
            )
        except Exception as e:
            print(f"[WARN] Whisper init failed: {e}")

        # 2. Initialize Google (If requested)
        if provider == "google":
            google_cfg = stt_cfg.get("google", {})
            cred_path = google_cfg.get("credentials_path", "backend/daisoproject-sst.json")
            
            # Resolve relative credential path
            if not os.path.isabs(cred_path):
                 # Try finding it in project root or backend
                 possible_creds = [
                     project_root / cred_path,
                     project_root / "backend" / cred_path,
                     Path(cred_path)
                 ]
                 for pc in possible_creds:
                     if pc.exists():
                         cred_path = str(pc)
                         break

            try:
                google_adapter = get_adapter("google", credentials_path=cred_path)
            except Exception as e:
                print(f"[ERROR] Google init failed: {e}")

        # 오디오 정규화 (표준 포맷 변환 - 전처리 후 한 번 더 보장)
        # normalize_audio는 내부적으로 AudioConverter를 사용하며, 이미 wav라면 빠름
        norm_result = normalize_audio(target_audio)
        final_audio_path = norm_result["normalized_path"]
        
        # 2. 변환 (STT) - Fallback Logic
        stt_result = None
        final_error = None
        used_provider = provider
        
        # Try Google First
        if provider == "google" and google_adapter:
            try:
                stt_result = google_adapter.transcribe(final_audio_path)
                
                # Check for empty result (Google specific)
                if not stt_result.text_raw or not stt_result.text_raw.strip():
                    print(f"[INFO] Google returned empty result. Triggering fallback.")
                    stt_result = None # Force fallback
                else:
                    # Check post-processing inclusion for Google
                    if _pp_config.get("apply_to_google", True):
                         # Logic handles post-process at the end, raw is kept
                         pass
                         
            except Exception as e:
                print(f"[WARN] Google STT failed: {e}")
                stt_result = None
        
        # Fallback to Whisper
        if not stt_result:
            # Check if fallback is enabled
            if provider == "google" and not fallback_cfg.get("enabled", True):
                 print("[WARN] Fallback is disabled in config.")
            elif whisper_adapter:
                if provider == "google":
                    print(f"[INFO] Falling back to Whisper...")
                    used_provider = "whisper"
                
                try:
                    stt_result = whisper_adapter.transcribe(final_audio_path)
                except Exception as e:
                    final_error = str(e)
        
        if not stt_result:
            raise RuntimeError(final_error or "All STT providers failed")

        
        # 3. 텍스트 후처리 (추임새 제거, 단위 보정)
        final_text = ""
        if stt_result.text_raw:
            # Decide whether to apply postprocessing
            apply_pp = False
            if used_provider == "google" and _pp_config.get("apply_to_google", True):
                apply_pp = True
            elif used_provider == "whisper" and _pp_config.get("apply_to_fallback", True):
                apply_pp = True
            elif _pp_config.get("enabled", True): # Default fallback
                apply_pp = True
                
            if apply_pp:
                final_text = text_postprocessor.postprocess(stt_result.text_raw)
            else:
                final_text = stt_result.text_raw
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "text": final_text,
            "latency_ms": latency_ms,
            "confidence": stt_result.confidence,
            "error": stt_result.error,
            "provider": used_provider
        }
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "text": "",
            "latency_ms": latency_ms,
            "confidence": 0.0,
            "error": str(e)
        }
