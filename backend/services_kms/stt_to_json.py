import os
import json
import sys
import time
from pathlib import Path

# Add project root to sys.path
# backend/services_kms/stt_to_json.py -> parent -> services_kms -> parent -> backend -> parent -> root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

print(f"[DEBUG] Project Root: {project_root}")
print(f"[DEBUG] sys.path added: {project_root}")

# Import STT adapter from backend/stt
try:
    from backend.stt.adapters import get_adapter
    from backend.stt.audio_converter import normalize_audio
    print("[DEBUG] Imported backend.stt successfully")
except ImportError as e:
    print(f"[DEBUG] Import failed: {e}")
    # Try alternate path if needed, but project_root should work
    sys.path.append(str(project_root / 'backend'))
    from stt.adapters import get_adapter
    from stt.audio_converter import normalize_audio

# Force pydub to use local ffmpeg if available
from pydub import AudioSegment
current_dir = Path(__file__).resolve().parent  # Script's own directory
local_ffmpeg = os.path.join(current_dir, "ffmpeg.exe")
if os.path.exists(local_ffmpeg):
    AudioSegment.converter = local_ffmpeg
    print(f"[Config] Using local ffmpeg: {local_ffmpeg}")

def convert_stt_to_json(input_dir: str, output_json: str, provider: str = "whisper"):
    """
    Reads audio files, transcribes them, and saves to JSON.
    """
    input_path = Path(input_dir)
    output_path = Path(output_json)
    
    if not input_path.exists():
        print(f"Error: Input '{input_dir}' does not exist.")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Initializing STT Adapters (Provider: {provider.upper()})...")
    google_adapter = None
    whisper_adapter = None
    
    # 1. Initialize Whisper (Always, for fallback or primary)
    try:
        # Using default settings as in original code
        whisper_adapter = get_adapter("whisper", model_size="medium", device="cpu", compute_type="int8")
        print(" [OK] Whisper Adapter initialized")
    except Exception as e:
        print(f" [WARN] Whisper Adapter failed to load: {e}")

    # 2. Initialize Google (If requested)
    if provider == "google":
        try:
            google_adapter = get_adapter("google", credentials_path="backend/daisoproject-sst.json")
            print(" [OK] Google Adapter initialized")
        except Exception as e:
            print(f" [ERROR] Google Adapter failed to load: {e}")
            print("  -> Continuing with Whisper only if available.")

    results = []
    audio_extensions = {".wav", ".mp3", ".m4a", ".flac"}
    
    # ... (input validation logging kept same)
    print(f"[DEBUG] Validating Input Path: {input_path}")
    print(f"[DEBUG] Absolute Path: {input_path.resolve()}")
    print(f"[DEBUG] Exists: {input_path.exists()}")
    print(f"[DEBUG] Is File: {input_path.is_file()}")

    if input_path.is_file():
        files = [input_path]
    else:
        # Directory: Recursive search
        files = [f for f in input_path.rglob("*") if f.suffix.lower() in audio_extensions]
    
    print(f"[DEBUG] Found files: {len(files)}")
    
    if not files:
        print(f"No audio files found in '{input_dir}'.")
        return

    print(f"Found {len(files)} audio files. Starting transcription...")

    print(f"Found {len(files)} audio files. Starting transcription...")

    # Use stt_service.run_stt (Centralized Logic with Config)
    from backend.services_kms.stt_service import run_stt

    for i, file_path in enumerate(files, 1):
        print(f"Processing [{i}/{len(files)}]: {file_path.name}")
        
        try:
            # Call run_stt (Handles Preprocessing -> Adapter (Google/Whisper) -> Fallback -> Postprocessing)
            # provider arg is passed from convert_stt_to_json
            result_dict = run_stt(str(file_path), provider=provider)
            
            # Map result to output format
            final_utterance = result_dict.get("text", "")
            
            item = {
                "id": i,
                "filename": file_path.name,
                "utterance": final_utterance,
                "stt_meta": {
                    "confidence": result_dict.get("confidence", 0.0),
                    "latency_ms": result_dict.get("latency_ms", 0),
                    "error": result_dict.get("error"),
                    "provider": result_dict.get("provider", "unknown")
                }
            }
            results.append(item)
            print(f"  - Utterance: {item['utterance']}")
            if result_dict.get("error"):
                 print(f"  Ref: Error: {result_dict.get('error')}")

        except Exception as e:
            print(f"  - Failed to process {file_path.name}: {e}")
            results.append({
                "id": i,
                "filename": file_path.name,
                "utterance": "",
                "error": str(e)
            })

    # Save to JSON
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSuccessfully saved {len(results)} items to '{output_json}'")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    # Use project root for paths (2 levels up from backend/services_kms)
    project_root = Path(__file__).resolve().parent.parent.parent
    
    INPUT_AUDIO_DIR = str(project_root / "data/test_audio/02_short/김민서_단답01.m4a")
    OUTPUT_JSON_FILE = str(project_root / "backend/services_kms/data/stt_output.json")
    
    if not os.path.exists(INPUT_AUDIO_DIR):
        print(f"Directory not found: {INPUT_AUDIO_DIR}")
        print("Please ensure your audio files are in this folder.")
    else:
        convert_stt_to_json(INPUT_AUDIO_DIR, OUTPUT_JSON_FILE)
