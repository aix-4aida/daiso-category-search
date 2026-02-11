import sys
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from backend.services.pipeline_service import run_full_pipeline
from backend.stt.types import ProviderResult, STTResult, QualityGateResult

class TestSearchPipelineFix(unittest.TestCase):
    
    @patch("backend.services.stt_service.run_single_provider")
    @patch("backend.services.pipeline_service.check_intent")
    @patch("backend.services.pipeline_service.extract_keyword")
    @patch("backend.services.pipeline_service.search_products")
    @patch("backend.services.pipeline_service.rerank_products")
    def test_stt_fallback_google_to_whisper(self, mock_rerank, mock_search, mock_keyword, mock_intent, mock_stt):
        """
        Scenario: Google STT fails, Whisper STT succeeds.
        Verify: Pipeline continues with Whisper result.
        """
        # 1. Mock Google Failure
        google_fail = ProviderResult(
            provider="google",
            model="default",
            stt=STTResult(text_raw=None, confidence=0.0, latency_ms=100),
            quality_gate=QualityGateResult(status="FAIL", is_usable=False, reason="EMPTY_TRANSCRIPT")
        )
        
        # 2. Mock Whisper Success
        whisper_success = ProviderResult(
            provider="whisper",
            model="tiny",
            stt=STTResult(text_raw="물티슈 있어요?", confidence=0.9, latency_ms=500),
            quality_gate=QualityGateResult(status="OK", is_usable=True, reason="OK")
        )
        
        # Side effect: first call Google fail, second call Whisper success
        mock_stt.side_effect = [google_fail, whisper_success]
        
        # Mock other steps
        mock_intent.return_value = {"is_valid": "Y", "reason": "Search query"}
        mock_keyword.return_value = {"keyword": "물티슈", "reasoning": "Extracted"}
        mock_search.return_value = [{"id": "1", "name": "에끌라 물티슈", "meta": {"section": "C01", "floor": "B1"}}]
        mock_rerank.return_value = {"selected_id": "1", "reason": "Best match"}
        
        # Run
        result = run_full_pipeline("dummy_audio.wav")
        
        # Assertions
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"]["product"], "에끌라 물티슈")
        self.assertEqual(result["steps"]["stt"]["provider"], "whisper")
        print("\n✅ Test Passed: Successfully fell back to Whisper when Google failed.")

    @patch("backend.services.stt_service.run_single_provider")
    def test_stt_google_success(self, mock_stt):
        """
        Scenario: Google STT succeeds.
        Verify: Whisper is NOT called.
        """
        google_success = ProviderResult(
            provider="google",
            model="default",
            stt=STTResult(text_raw="물티슈", confidence=0.95, latency_ms=200),
            quality_gate=QualityGateResult(status="OK", is_usable=True, reason="OK")
        )
        
        mock_stt.return_value = google_success
        
        # We need to mock other imports in the pipeline if we don't want them to run
        with patch("backend.services.pipeline_service.check_intent") as mock_intent, \
             patch("backend.services.pipeline_service.extract_keyword") as mock_keyword, \
             patch("backend.services.pipeline_service.search_products") as mock_search, \
             patch("backend.services.pipeline_service.rerank_products") as mock_rerank:
            
            mock_intent.return_value = {"is_valid": "Y"}
            mock_keyword.return_value = {"keyword": "물티슈"}
            mock_search.return_value = [{"id": "1", "name": "물티슈"}]
            mock_rerank.return_value = {"selected_id": "1"}
            
            result = run_full_pipeline("dummy_audio.wav")
            
            self.assertEqual(mock_stt.call_count, 1)
            self.assertEqual(result["steps"]["stt"]["provider"], "google")
            print("✅ Test Passed: Used Google STT and skipped Whisper.")

if __name__ == "__main__":
    unittest.main()
