"""
Tests for backend/ws_stt.py Whisper fallback integration.
Verifies:
  - WhisperFallbackManager singleton
  - TextPostprocessor integration
  - Ring buffer always-on
  - Enhanced send_final with text_raw/text_processed
  - Config loading (fallback, postprocessing)
  - FATAL: enabled feature + missing dep → MissingDependencyError
  - disabled feature + missing dep → OK (silent)
"""
from __future__ import annotations

import threading
import importlib
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


# ---------------------------------------------------------------------------
# 1. WhisperFallbackManager singleton
# ---------------------------------------------------------------------------

class TestWhisperFallbackManager:

    def test_import_exists(self):
        from backend.ws_stt import WhisperFallbackManager
        assert WhisperFallbackManager is not None

    def test_singleton_returns_same_instance(self):
        from backend.ws_stt import WhisperFallbackManager
        WhisperFallbackManager._instance = None
        a = WhisperFallbackManager.get_instance()
        b = WhisperFallbackManager.get_instance()
        assert a is b

    def test_is_available_false_when_disabled(self):
        from backend.ws_stt import WhisperFallbackManager
        WhisperFallbackManager._instance = None
        with patch("backend.ws_stt.load_fallback_config", return_value={"enabled": False}):
            mgr = WhisperFallbackManager.get_instance()
            assert mgr.is_available() is False

    def test_transcribe_fallback_returns_dict(self):
        from backend.ws_stt import WhisperFallbackManager
        WhisperFallbackManager._instance = None
        with patch("backend.ws_stt.load_fallback_config", return_value={"enabled": False}):
            mgr = WhisperFallbackManager.get_instance()
            result = mgr.transcribe_fallback(b"\x00" * 32000)
            assert isinstance(result, dict)
            assert "text" in result or "text_raw" in result or "error" in result


# ---------------------------------------------------------------------------
# 2. Config loading
# ---------------------------------------------------------------------------

class TestConfigLoading:

    def test_load_fallback_config_returns_dict(self):
        from backend.ws_stt import load_fallback_config
        result = load_fallback_config()
        assert isinstance(result, dict)

    def test_load_postprocessing_config_returns_dict(self):
        from backend.ws_stt import load_postprocessing_config
        result = load_postprocessing_config()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 3. Postprocessor singleton
# ---------------------------------------------------------------------------

class TestPostprocessor:

    def test_get_postprocessor_importable(self):
        from backend.ws_stt import get_postprocessor
        result = get_postprocessor()
        assert result is None or hasattr(result, "postprocess")


# ---------------------------------------------------------------------------
# 4. StreamingSTTSession enhanced features
# ---------------------------------------------------------------------------

class TestStreamingSTTSession:

    def test_session_has_ring_buffer(self):
        """Ring buffer should always be active (not gated by save_audio)."""
        from backend.ws_stt import StreamingSTTSession
        ws = MagicMock()
        with patch("backend.ws_stt.load_fallback_config", return_value={"buffer_max_sec": 8}), \
             patch("backend.ws_stt.get_postprocessor", return_value=None), \
             patch("backend.ws_stt.load_postprocessing_config", return_value={}):
            session = StreamingSTTSession(ws, "fake_creds.json", meta={})
        assert hasattr(session, "full_audio_buffer")
        assert hasattr(session, "_buffer_max_bytes")
        assert session._buffer_max_bytes == 16000 * 2 * 8  # 8sec

    def test_session_has_fallback_state(self):
        """Session should track fallback state."""
        from backend.ws_stt import StreamingSTTSession
        ws = MagicMock()
        with patch("backend.ws_stt.load_fallback_config", return_value={"buffer_max_sec": 8}), \
             patch("backend.ws_stt.get_postprocessor", return_value=None), \
             patch("backend.ws_stt.load_postprocessing_config", return_value={}):
            session = StreamingSTTSession(ws, "fake_creds.json", meta={})
        assert hasattr(session, "_fallback_triggered")
        assert session._fallback_triggered is False
        assert hasattr(session, "_got_final")

    def test_send_final_accepts_text_raw_and_processed(self):
        """send_final should accept text_raw and text_processed parameters."""
        from backend.ws_stt import StreamingSTTSession
        import inspect
        sig = inspect.signature(StreamingSTTSession.send_final)
        param_names = list(sig.parameters.keys())
        assert "text_raw" in param_names
        assert "text_processed" in param_names
        assert "fallback_used" in param_names


# ---------------------------------------------------------------------------
# 5. Ring buffer always fills (not gated by save_audio)
# ---------------------------------------------------------------------------

class TestRingBufferAlwaysActive:

    def test_audio_generator_fills_buffer_without_save_audio(self):
        """Even without save_audio=True, ring buffer should accumulate."""
        from backend.ws_stt import StreamingSTTSession
        ws = MagicMock()
        with patch("backend.ws_stt.load_fallback_config", return_value={"buffer_max_sec": 8}), \
             patch("backend.ws_stt.get_postprocessor", return_value=None), \
             patch("backend.ws_stt.load_postprocessing_config", return_value={}):
            session = StreamingSTTSession(ws, "fake_creds.json", meta={"save_audio": False})

        chunk = b"\x01\x02" * 1600  # 3200 bytes = 100ms
        session.audio_queue.put(chunk)
        session.audio_queue.put(None)  # poison pill

        gen = session._audio_generator()
        next(gen)
        assert len(session.full_audio_buffer) == 3200


# ---------------------------------------------------------------------------
# 6. MissingDependencyError — enabled=true + missing dep → FATAL
# ---------------------------------------------------------------------------

class TestMissingDependencyError:

    def test_error_class_exists(self):
        from backend.ws_stt import MissingDependencyError
        assert issubclass(MissingDependencyError, RuntimeError)

    def test_check_deps_raises_when_google_stt_enabled_but_missing(self):
        """stt.google enabled + google-cloud-speech missing → MissingDependencyError."""
        from backend.ws_stt import check_required_deps, MissingDependencyError

        config = {
            "stt": {"google": {"enabled": True}},
            "fallback": {"enabled": False},
            "postprocessing": {"enabled": False},
        }
        with patch("backend.ws_stt.GOOGLE_STT_AVAILABLE", False):
            with pytest.raises(MissingDependencyError, match="google-cloud-speech"):
                check_required_deps(config)

    def test_check_deps_raises_when_fallback_enabled_but_whisper_missing(self):
        """fallback.enabled=true + faster-whisper missing → MissingDependencyError."""
        from backend.ws_stt import check_required_deps, MissingDependencyError

        config = {
            "stt": {"google": {"enabled": True}},
            "fallback": {"enabled": True},
            "postprocessing": {"enabled": False},
        }
        with patch("backend.ws_stt.GOOGLE_STT_AVAILABLE", True), \
             patch("backend.ws_stt.WHISPER_ADAPTER_AVAILABLE", False):
            with pytest.raises(MissingDependencyError, match="faster-whisper"):
                check_required_deps(config)

    def test_check_deps_ok_when_disabled_and_missing(self):
        """All features disabled → no error even if deps missing."""
        from backend.ws_stt import check_required_deps

        config = {
            "stt": {"google": {"enabled": False}},
            "fallback": {"enabled": False},
            "postprocessing": {"enabled": False},
        }
        with patch("backend.ws_stt.GOOGLE_STT_AVAILABLE", False), \
             patch("backend.ws_stt.WHISPER_ADAPTER_AVAILABLE", False):
            # Should NOT raise
            check_required_deps(config)

    def test_check_deps_ok_when_enabled_and_available(self):
        """All features enabled + deps present → no error."""
        from backend.ws_stt import check_required_deps

        config = {
            "stt": {"google": {"enabled": True}},
            "fallback": {"enabled": True},
            "postprocessing": {"enabled": True},
        }
        with patch("backend.ws_stt.GOOGLE_STT_AVAILABLE", True), \
             patch("backend.ws_stt.WHISPER_ADAPTER_AVAILABLE", True), \
             patch("backend.ws_stt.POSTPROCESSOR_AVAILABLE", True):
            check_required_deps(config)


# ---------------------------------------------------------------------------
# 7. WS error response on missing dep (initialize should send MISSING_DEP)
# ---------------------------------------------------------------------------

class TestWSMissingDepResponse:

    @pytest.mark.asyncio
    async def test_initialize_sends_missing_dep_when_google_unavailable(self):
        """initialize() should send {type:error, code:MISSING_DEP} and return False."""
        from backend.ws_stt import StreamingSTTSession

        ws = AsyncMock()
        with patch("backend.ws_stt.load_fallback_config", return_value={"buffer_max_sec": 8}), \
             patch("backend.ws_stt.get_postprocessor", return_value=None), \
             patch("backend.ws_stt.load_postprocessing_config", return_value={}), \
             patch("backend.ws_stt.GOOGLE_STT_AVAILABLE", False):
            session = StreamingSTTSession(ws, "fake_creds.json", meta={})
            result = await session.initialize()

        assert result is False
        ws.send_json.assert_called_once()
        msg = ws.send_json.call_args[0][0]
        assert msg["type"] == "error"
        assert msg["code"] == "MISSING_DEP"
        assert "google-cloud-speech" in msg["message"]
