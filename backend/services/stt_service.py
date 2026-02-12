from backend.stt import get_adapter, QualityGate, PolicyGate, get_converter as get_stt_converter
from backend.stt.types import ProviderResult
from backend.core.config import config
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize components
print("🔄 Initializing STT adapters...")

# 1. Whisper Adapter
whisper_config = config["stt"]["whisper"]
whisper_adapter = get_adapter("whisper", **whisper_config)

# 2. Google Adapter
google_config = config["stt"].get("google", {})
# Path normalized from config
google_adapter = get_adapter("google", **google_config)

# 3. Gates & Converter
quality_gate = QualityGate(**config["quality_gate"])
policy_gate = PolicyGate(
    fixed_locations=config["policy_gate"]["fixed_locations"],
    unsupported_patterns=config["policy_gate"]["unsupported_patterns"]
)
audio_converter = get_stt_converter(output_dir="outputs/normalized")

print("✅ All adapters initialized")

def run_single_provider(audio_path: str, provider: str, attempt: int = 1) -> ProviderResult:
    """Run STT pipeline for a single provider"""
    adapter = google_adapter if provider == "google" else whisper_adapter
    model = "default" if provider == "google" else config["stt"]["whisper"]["model_size"]
    
    # Convert audio
    try:
        conversion_result = audio_converter.normalize(audio_path)
        normalized_path = conversion_result["normalized_path"]
        print(f"🔄 [{provider.upper()}] Audio normalized: {audio_path} → {normalized_path}")
    except Exception as e:
        print(f"⚠️ [{provider.upper()}] Audio conversion failed, using original: {e}")
        normalized_path = audio_path
    
    # STT
    print(f"🎙️ [{provider.upper()}] Transcribing...")
    stt_result = adapter.transcribe(normalized_path)
    
    # Quality Gate
    quality_result = quality_gate.evaluate(stt_result, attempt)
    print(f"⚖️ [{provider.upper()}] Quality: {quality_result.status} (Reason: {quality_result.reason})")
    
    # Policy Gate
    policy_intent = None
    if quality_result.status == "OK" and stt_result.text_raw:
        policy_intent = policy_gate.classify(stt_result.text_raw)
    
    return ProviderResult(
        provider=provider,
        model=model,
        stt=stt_result,
        quality_gate=quality_result,
        policy_intent=policy_intent
    )

def run_stt_pipeline_with_fallback(audio_path: str, attempt: int = 1) -> ProviderResult:
    """
    STT Pipeline with Google -> Whisper fallback strategy.
    """
    # 1. Try Google STT (Primary)
    google_res = run_single_provider(audio_path, "google", attempt)
    
    if google_res.quality_gate.status == "OK":
        print(f"✅ Google STT Success: '{google_res.stt.text_raw}'")
        return google_res
    
    # 2. Try Whisper STT (Fallback) if Google fails or quality is low
    print(f"🔄 Google STT failed ({google_res.quality_gate.reason}), falling back to Whisper...")
    whisper_res = run_single_provider(audio_path, "whisper", attempt)
    
    return whisper_res

def generate_final_response(provider_result: ProviderResult) -> str:
    """Generate final response based on provider result"""
    if provider_result.quality_gate.status == "OK":
        if provider_result.policy_intent:
            if provider_result.policy_intent.intent_type == "FIXED_LOCATION":
                for loc in config["policy_gate"]["fixed_locations"]:
                    if loc["target"] == provider_result.policy_intent.location_target:
                        return loc["response"]
            elif provider_result.policy_intent.intent_type == "UNSUPPORTED":
                return config["policy_gate"]["fallback_message"]
            else:  # PRODUCT_SEARCH
                return f"[PRODUCT_SEARCH] '{provider_result.stt.text_raw}' 검색 예정"
    elif provider_result.quality_gate.status == "RETRY":
        return config["policy_gate"]["retry_message"]
    
    return "죄송합니다. 음성을 인식할 수 없었습니다."
