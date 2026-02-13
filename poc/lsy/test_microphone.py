#!/usr/bin/env python3
"""
🎤 실시간 마이크 STT 테스트 스크립트
- PyAudio로 마이크 캡처 (16kHz mono PCM16)
- WebSocket으로 서버에 실시간 전송
- Interim/Final 결과를 콘솔에 표시
- Enter 키로 종료

사용법:
  1. 서버 시작: python -m uvicorn poc.lsy.api:app --host 127.0.0.1 --port 8010
  2. 이 스크립트 실행: python test_microphone.py
  3. 마이크에 말하면 실시간 STT 결과 표시
  4. Enter 키를 누르면 종료

필요한 패키지:
  pip install pyaudio websockets
"""

import asyncio
import json
import base64
import threading
import time
import sys

try:
    import pyaudio
except ImportError:
    print("❌ pyaudio가 설치되지 않았습니다.")
    print("   pip install pyaudio")
    print("   (Windows에서 설치 실패 시: pip install pipwin && pipwin install pyaudio)")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("❌ websockets가 설치되지 않았습니다.")
    print("   pip install websockets")
    sys.exit(1)


# ============================================================
# 설정
# ============================================================
WS_URL = "ws://127.0.0.1:8010/ws/stt"
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 100  # 100ms 단위로 전송
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)  # 1600 samples
FORMAT = pyaudio.paInt16


# ============================================================
# 전역 상태
# ============================================================
stop_flag = threading.Event()


def wait_for_enter():
    """Enter 키 입력 대기 (별도 스레드에서 실행)"""
    input()
    stop_flag.set()


async def run_microphone_stt():
    """메인 실시간 STT 루프"""
    
    print("=" * 60)
    print("🎤 실시간 마이크 STT 테스트")
    print("=" * 60)
    print(f"  서버: {WS_URL}")
    print(f"  샘플레이트: {SAMPLE_RATE}Hz")
    print(f"  프레임 크기: {CHUNK_DURATION_MS}ms ({CHUNK_SIZE} samples)")
    print()
    print("  📢 마이크에 말하면 실시간으로 인식됩니다.")
    print("  ⏎  Enter 키를 누르면 종료됩니다.")
    print("=" * 60)
    print()
    
    # 1. PyAudio 초기화
    pa = pyaudio.PyAudio()
    
    # 마이크 정보 출력
    default_input = pa.get_default_input_device_info()
    print(f"🎙️  마이크: {default_input['name']}")
    print()
    
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    # 2. Enter 키 감지 스레드 시작
    enter_thread = threading.Thread(target=wait_for_enter, daemon=True)
    enter_thread.start()
    
    # 3. WebSocket 연결
    try:
        async with websockets.connect(WS_URL, max_size=10**7) as ws:
            print("🔌 WebSocket 연결됨")
            
            # Start 메시지 전송
            start_msg = {
                "type": "start",
                "meta": {
                    "run_id": "mic_test",
                    "test_id": f"mic_{int(time.time())}",
                    "utterance_type": "realtime_mic",
                    "spoken_text": "실시간 마이크 테스트",
                    "save_audio": False
                }
            }
            await ws.send(json.dumps(start_msg))
            
            # Started 응답 대기
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            resp = json.loads(response)
            
            if resp.get("type") != "started":
                print(f"❌ 시작 실패: {resp}")
                return
            
            print("✅ STT 세션 시작됨")
            print()
            print("─" * 60)
            print("💬 인식 결과:")
            print("─" * 60)
            
            # 4. 오디오 전송 + 결과 수신 동시 실행
            send_task = asyncio.create_task(send_audio(ws, stream))
            recv_task = asyncio.create_task(receive_results(ws))
            
            # 둘 중 하나가 끝날 때까지 대기
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 나머지 태스크 취소
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Stop 메시지 전송
            try:
                await ws.send(json.dumps({"type": "stop", "reason": "manual"}))
                print("\n\n🛑 Stop 전송")
                
                # Final 결과 대기 (최대 10초)
                try:
                    while True:
                        response = await asyncio.wait_for(ws.recv(), timeout=10)
                        resp = json.loads(response)
                        if resp.get("type") == "final":
                            print_final_result(resp)
                            break
                        elif resp.get("type") == "interim":
                            # 마지막 interim 무시
                            pass
                except asyncio.TimeoutError:
                    print("  ⏰ Final 결과 대기 시간 초과")
            except Exception:
                pass
                
    except websockets.exceptions.ConnectionClosed:
        print("\n🔌 WebSocket 연결 종료")
    except ConnectionRefusedError:
        print(f"\n❌ 서버에 연결할 수 없습니다: {WS_URL}")
        print("   서버가 실행 중인지 확인하세요:")
        print("   python -m uvicorn poc.lsy.api:app --host 127.0.0.1 --port 8010")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        # 정리
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print("\n✅ 마이크 테스트 종료")


async def send_audio(ws, stream):
    """마이크에서 오디오를 읽어 WebSocket으로 전송"""
    seq = 0
    
    try:
        while not stop_flag.is_set():
            # PyAudio에서 오디오 읽기 (blocking)
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: stream.read(CHUNK_SIZE, exception_on_overflow=False)
            )
            
            # Base64 인코딩 후 전송 (기존 서버 프로토콜에 맞춤)
            pcm_b64 = base64.b64encode(audio_data).decode("utf-8")
            
            msg = {
                "type": "audio",
                "pcm_b64": pcm_b64,
                "seq": seq
            }
            
            await ws.send(json.dumps(msg))
            seq += 1
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        if not stop_flag.is_set():
            print(f"\n❌ 오디오 전송 오류: {e}")


async def receive_results(ws):
    """서버로부터 STT 결과를 수신하여 표시"""
    interim_count = 0
    
    try:
        while not stop_flag.is_set():
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=0.5)
                resp = json.loads(response)
                
                if resp.get("type") == "interim":
                    interim_count += 1
                    text = resp.get("text", "")
                    # 같은 줄에서 계속 업데이트 (실시간 느낌)
                    print(f"\r  💬 {text}                    ", end="", flush=True)
                    
                elif resp.get("type") == "final":
                    print_final_result(resp)
                    break  # Final 결과 받으면 종료
                    
                elif resp.get("type") == "error":
                    print(f"\n  ❌ 에러: {resp.get('message', '')}")
                    
            except asyncio.TimeoutError:
                continue
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        if not stop_flag.is_set():
            print(f"\n❌ 결과 수신 오류: {e}")


def print_final_result(resp):
    """최종 결과 출력"""
    text = resp.get("text", "")
    status = resp.get("status", "?")
    meta = resp.get("meta", {})
    text_raw = meta.get("text_raw", text)
    text_processed = meta.get("text_processed", text)
    confidence = meta.get("confidence", 0)
    latency = meta.get("latency_ms", 0)
    fallback = meta.get("fallback_used", False)
    
    print(f"\n")
    print("─" * 60)
    print("📊 최종 결과")
    print("─" * 60)
    print(f"  원본 (raw):     {text_raw}")
    print(f"  후처리 (proc):  {text_processed}")
    print(f"  상태:           {status}")
    print(f"  신뢰도:         {confidence}")
    print(f"  지연시간:       {latency}ms")
    print(f"  Fallback:       {'사용' if fallback else '미사용'}")
    print("─" * 60)


if __name__ == "__main__":
    print()
    print("🚀 실시간 마이크 STT 테스트를 시작합니다...")
    print()
    
    try:
        asyncio.run(run_microphone_stt())
    except KeyboardInterrupt:
        print("\n\n⚠️ Ctrl+C로 종료됨")
