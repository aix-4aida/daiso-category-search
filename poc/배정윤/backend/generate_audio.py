"""
CosyVoice TTS - Natural Korean Audio Generator
Uses FunAudioLLM/CosyVoice for high-quality Korean TTS
"""
import os
import sys
import time
import random

# Check if CosyVoice is installed
try:
    from cosyvoice.cli.cosyvoice import CosyVoice
    from cosyvoice.utils.file_utils import load_wav
except ImportError:
    print("""
❌ CosyVoice가 설치되지 않았습니다!

📋 설치 방법:
1. CosyVoice 클론:
   git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
   cd CosyVoice
   
2. 환경 설정:
   conda create -n cosyvoice python=3.10
   conda activate cosyvoice
   pip install -r requirements.txt
   
3. 모델 다운로드 (약 4GB):
   # ModelScope에서 자동 다운로드됨

4. 이 스크립트를 CosyVoice 폴더로 복사 후 실행
    """)
    sys.exit(1)

import torchaudio
from database import get_connection, get_all_products

# Output directory
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio')

# Korean voice presets
KOREAN_VOICES = [
    "Korean Female 1",
    "Korean Male 1", 
]

def init_cosyvoice():
    """Initialize CosyVoice model"""
    print("🔄 Loading CosyVoice model... (첫 실행시 모델 다운로드)")
    # 한국어 지원 모델 로드
    cosyvoice = CosyVoice('CosyVoice-300M-SFT')
    print("✅ CosyVoice loaded!")
    return cosyvoice

def generate_audio(cosyvoice, text: str, filename: str, voice_idx: int = 0) -> bool:
    """Generate audio using CosyVoice"""
    try:
        filepath = os.path.join(AUDIO_DIR, filename)
        
        # Skip if exists
        if os.path.exists(filepath):
            return True
        
        # Generate speech (Korean)
        output = cosyvoice.inference_sft(
            text,
            speaker_id=voice_idx % 2,  # Alternate between voices
            stream=False
        )
        
        # Save audio
        for i, audio_data in enumerate(output):
            torchaudio.save(filepath, audio_data['tts_speech'], 22050)
            break  # Only take first output
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating: {e}")
        return False

def generate_all_audio(limit: int = None):
    """Generate audio for all test utterances"""
    print("=" * 50)
    print("🎙️ CosyVoice Korean TTS Generator")
    print("=" * 50)
    
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Initialize model
    cosyvoice = init_cosyvoice()
    
    # Get utterances from database
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT id, utterance, difficulty FROM test_utterances'
    if limit:
        query += f' LIMIT {limit}'
    
    cursor.execute(query)
    utterances = cursor.fetchall()
    conn.close()
    
    if not utterances:
        print("❌ No utterances found. Run generate_test_data.py first.")
        return
    
    print(f"📋 Generating {len(utterances)} audio files...")
    print("-" * 50)
    
    success = 0
    fail = 0
    start_time = time.time()
    
    for i, row in enumerate(utterances):
        utt_id = row['id']
        text = row['utterance']
        difficulty = row['difficulty']
        
        # Voice selection (random for diversity)
        voice_idx = random.randint(0, 1)
        
        filename = f"{utt_id:05d}_{difficulty}.wav"
        
        print(f"[{i+1}/{len(utterances)}] {text[:30]}...", end='')
        
        if generate_audio(cosyvoice, text, filename, voice_idx):
            success += 1
            print(" ✅")
        else:
            fail += 1
            print(" ❌")
        
        # Progress update
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (len(utterances) - i - 1) / rate
            print(f"\n📊 Progress: {i+1}/{len(utterances)} | Speed: {rate:.1f}/sec | ETA: {remaining/60:.1f}min\n")
    
    print("\n" + "=" * 50)
    print(f"🎉 Complete! Success: {success}, Failed: {fail}")
    print(f"📁 Saved to: {AUDIO_DIR}")
    print("=" * 50)

def test_single():
    """Test with a single utterance"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    cosyvoice = init_cosyvoice()
    
    test_texts = [
        "안녕하세요, 물티슈 있나요?",
        "여행용 샴푸 어디 있어요?",
        "그거 어딨능교?",  # 사투리
    ]
    
    for i, text in enumerate(test_texts):
        print(f"Generating: {text}")
        filename = f"test_{i+1}.wav"
        if generate_audio(cosyvoice, text, filename, i):
            print(f"  → {AUDIO_DIR}/{filename} ✅")
        else:
            print(f"  → Failed ❌")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_single()
    elif len(sys.argv) > 1 and sys.argv[1] == '--limit':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        generate_all_audio(limit=limit)
    else:
        generate_all_audio()
