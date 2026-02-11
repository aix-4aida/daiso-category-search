
import asyncio
from backend.services_kms.run_all_pipeline import run_pipeline_for_voice

class PipelineService:
    async def run_voice_pipeline(self, audio_path: str, text: str, stt_elapsed: float) -> dict:
        """
        Wraps the existing run_pipeline_for_voice function.
        """
        try:
            # The original function is async
            result = await run_pipeline_for_voice(audio_path, text, stt_elapsed)
            return result
        except Exception as e:
            print(f"❌ Pipeline Service Error: {e}")
            raise e

_pipeline_service = None

def get_pipeline_service():
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
