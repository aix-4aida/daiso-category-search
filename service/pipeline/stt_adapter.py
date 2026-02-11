"""
STT Adapter — 텍스트/오디오 입력을 stt_output.json 호환 형식으로 변환.
"""


def transcribe_text(texts: list[str]) -> list[dict]:
    """텍스트 입력을 stt_output.json 호환 형식으로 변환.

    Returns:
        list of dicts compatible with poc/data/stt_output.json schema.
    """
    results = []
    for i, text in enumerate(texts, 1):
        results.append({
            "id": i,
            "filename": "text_input",
            "utterance": text,
            "stt_meta": {
                "confidence": 1.0,
                "latency_ms": 0,
                "error": None,
            },
        })
    return results


def transcribe_audio(audio_path: str) -> list[dict]:
    """TODO: 실제 STT 연동 (Whisper / Google Cloud Speech).

    이번 단계에서는 미구현. 다음 단계에서 backend.stt.adapters 를 연동할 예정.
    """
    raise NotImplementedError("audio STT는 다음 단계에서 구현 예정")
