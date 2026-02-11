
import time
import shutil
import uuid
import os
from pathlib import Path
from typing import Optional, Dict

from backend.stt import get_adapter, QualityGate, PolicyGate, AudioConverter
from backend.stt.types import STTResult, ProviderResult
from backend.app.core.config import get_settings
from backend.app.models.schemas import ComparisonPipelineResult, ProviderResult as SchemaProviderResult

class STTService:
    def __init__(self):
        self.settings = get_settings()
        self.whisper_adapter = None
        self.google_adapter = None
        self.quality_gate = None
        self.policy_gate = None
        self.audio_converter = AudioConverter(output_dir="outputs/normalized")
        
        self.initialize_components()

    def initialize_components(self):
        print("🔄 Initializing STT Service components...")
        config = self.settings.config
        
        # Whisper
        self.whisper_adapter = get_adapter(
            "whisper",
            **config["stt"]["whisper"]
        )
        
        # Google
        google_config = config["stt"].get("google", {})
        # Adjust credentials path relative to project root if needed
        # Assuming backend/daisoproject-sst.json exists
        creds_path = Path("backend/daisoproject-sst.json")
        if creds_path.exists():
             google_config["credentials_path"] = str(creds_path)
        self.google_adapter = get_adapter("google", **google_config)
        
        # Gates
        self.quality_gate = QualityGate(**config["quality_gate"])
        self.policy_gate = PolicyGate(
            fixed_locations=config["policy_gate"]["fixed_locations"],
            unsupported_patterns=config["policy_gate"]["unsupported_patterns"]
        )
        print("✅ STT Service components initialized")

    def normalize_audio(self, audio_path: str) -> str:
        try:
            result = self.audio_converter.normalize(audio_path)
            return result["normalized_path"]
        except Exception as e:
            print(f"⚠️ Audio normalization failed: {e}")
            return audio_path

    def run_provider(self, audio_path: str, provider: str, attempt: int = 1) -> SchemaProviderResult:
        adapter = self.whisper_adapter if provider == "whisper" else self.google_adapter
        model_name = self.settings.stt_config.get("whisper", {}).get("model_size", "default") if provider == "whisper" else "default"
        
        # Normalize
        normalized_path = self.normalize_audio(audio_path)
        
        # Transcribe
        stt_result = adapter.transcribe(normalized_path)
        
        # Quality Gate
        quality_result = self.quality_gate.evaluate(stt_result, attempt)
        
        # Policy Gate
        policy_intent = None
        if quality_result.status == "OK" and stt_result.text_raw:
            policy_intent = self.policy_gate.classify(stt_result.text_raw)
            
        return SchemaProviderResult(
            provider=provider,
            model=model_name,
            stt=stt_result.dict(),
            quality_gate=quality_result.dict(),
            policy_intent=policy_intent.dict() if policy_intent else None
        )

    def generate_response(self, result: SchemaProviderResult) -> str:
        pg_config = self.settings.policy_gate_config
        
        if result.quality_gate.status == "OK":
            if result.policy_intent:
                if result.policy_intent.intent_type == "FIXED_LOCATION":
                    for loc in pg_config.get("fixed_locations", []):
                        if loc["target"] == result.policy_intent.location_target:
                            return loc["response"]
                elif result.policy_intent.intent_type == "UNSUPPORTED":
                    return pg_config.get("fallback_message", "지원하지 않는 요청입니다.")
                else:  # PRODUCT_SEARCH
                    return f"[PRODUCT_SEARCH] '{result.stt.text_raw}' 검색 예정"
        elif result.quality_gate.status == "RETRY":
            return pg_config.get("retry_message", "다시 말씀해 주세요.")
            
        return "죄송합니다. 음성을 인식할 수 없었습니다."

    async def process_voice_search(self, file_path: str) -> dict:
        """
        Executes just the STT part for voice search.
        The actual pipeline (Search/Rerank) is handled by PipelineService.
        """
        start_time = time.time()
        result = self.run_provider(file_path, "whisper", 1)
        elapsed = time.time() - start_time
        
        return {
            "text": result.stt.text_raw,
            "stt_time": elapsed,
            "error": result.stt.error
        }

# Global instance
_stt_service = None

def get_stt_service():
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
