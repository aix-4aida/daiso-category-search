
from backend.stt import get_adapter, QualityGate, PolicyGate, AudioConverter
from backend.stt.types import ProviderResult
from backend.core.config import config
import os

# Initialize components (Module-level singleton pattern for simplicity in this refactor)
# In a larger app, use Dependency Injection
print("🔄 Initializing STT adapters...")

whisper_adapter = get_adapter(
    "whisper",
    **config["stt"]["whisper"]
)

google_config = config["stt"].get("google", {})
google_config["credentials_path"] = "backend/daisoproject-sst.json"
google_adapter = get_adapter("google", **google_config)

quality_gate = QualityGate(**config["quality_gate"])

policy_gate = PolicyGate(
    fixed_locations=config["policy_gate"]["fixed_locations"],
    unsupported_patterns=config["policy_gate"]["unsupported_patterns"]
)

audio_converter = AudioConverter(output_dir="outputs/normalized")

print("✅ All adapters initialized")

def run_single_provider(audio_path: str, provider: str, attempt: int = 1) -> ProviderResult:
    """Run STT pipeline for a single provider"""
    adapter = whisper_adapter if provider == "whisper" else google_adapter
    model = config["stt"]["whisper"]["model_size"] if provider == "whisper" else "default"
    
    # Convert audio
    try:
        conversion_result = audio_converter.normalize(audio_path)
        normalized_path = conversion_result["normalized_path"]
        print(f"🔄 Audio normalized: {audio_path} → {normalized_path}")
    except Exception as e:
        print(f"⚠️ Audio conversion failed, using original: {e}")
        normalized_path = audio_path
    
    # STT
    stt_result = adapter.transcribe(normalized_path)
    
    # Quality Gate
    quality_result = quality_gate.evaluate(stt_result, attempt)
    
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
