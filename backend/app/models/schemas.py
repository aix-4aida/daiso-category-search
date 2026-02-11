from typing import Optional, Literal, List
from pydantic import BaseModel, Field

# === STT & Gate Types (from stt/types.py) ===

class STTResult(BaseModel):
    """STT transcription result from any provider"""
    text_raw: Optional[str] = None
    confidence: Optional[float] = None
    lang: Optional[str] = "ko"
    latency_ms: int
    error: Optional[str] = None

class QualityGateResult(BaseModel):
    """Quality gate evaluation result"""
    status: Literal["OK", "RETRY", "FAIL"]
    is_usable: bool
    reason: Literal[
        "EMPTY_TRANSCRIPT",
        "TOO_SHORT",
        "LOW_CONFIDENCE",
        "NONSENSE_PATTERN",
        "OK"
    ]

class PolicyIntent(BaseModel):
    """Policy gate intent classification"""
    intent_type: Literal["PRODUCT_SEARCH", "FIXED_LOCATION", "UNSUPPORTED"]
    location_target: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str

# === API Response Models ===

class VoiceSearchResponse(BaseModel):
    """Response for /api/search/voice"""
    text: str
    results: List[dict] = []
    keyword: Optional[str] = None
    pipeline_status: str
    stt_time_seconds: float
    total_time_seconds: float
    error: Optional[str] = None

class PipelineResult(BaseModel):
    """Final result from the STT pipeline (original endpoint)"""
    request_id: str
    stt: STTResult
    quality_gate: QualityGateResult
    policy_intent: Optional[PolicyIntent] = None
    normalized_text: Optional[str] = None
    final_response: str
    processing_time_ms: int

class ProviderResult(BaseModel):
    """Single provider STT result"""
    provider: str
    model: str
    stt: STTResult
    quality_gate: QualityGateResult
    policy_intent: Optional[PolicyIntent] = None

class ComparisonPipelineResult(BaseModel):
    """Comparison result from both providers"""
    request_id: str
    file_name: str
    saved_path: str
    whisper: ProviderResult
    google: ProviderResult
    first_provider: str = "whisper"
    final_response: str
    processing_time_ms: int

class STTProcessResponse(BaseModel):
    """Response for /stt/process endpoint"""
    request_id: str
    stt: STTResult
    quality_gate: QualityGateResult
    policy_intent: Optional[PolicyIntent] = None
    final_response: str
    processing_time_ms: int

