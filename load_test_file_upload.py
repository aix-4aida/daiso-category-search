import os
import time
import requests
import concurrent.futures
import argparse
from pathlib import Path

# ==========================================
# 설정 (Configuration)
# ==========================================
DEFAULT_SERVER_URL = "http://54.180.246.142:8000"  # 테스트할 서버 주소
ENDPOINT = "/api/search/voice"
DEFAULT_AUDIO_FILE = "data/test_audio/01_general/김민서_일반01.m4a"  # 테스트용 오디오 파일 경로 (프로젝트 루트 기준)
CONCURRENT_USERS = 10  # 동시에 접속할 가상 유저 수
TOTAL_REQUESTS = 50   # 총 날릴 요청 수

def send_request(url, file_path, request_id):
    """
    단일 요청을 전송하고 응답 시간을 측정하는 함수
    """
    start_time = time.time()
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'audio/m4a')}
            response = requests.post(url, files=files, timeout=60) # 타임아웃 60초
            
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            # 성공 여부 판단 (text가 있거나 results가 있으면 성공)
            success = bool(data.get("text") or data.get("results"))
            return {
                "id": request_id,
                "status": "SUCCESS" if success else "FAIL_LOGIC",
                "code": response.status_code,
                "time": elapsed,
                "error": None
            }
        else:
            return {
                "id": request_id,
                "status": "FAIL_HTTP",
                "code": response.status_code,
                "time": elapsed,
                "error": response.text[:100]
            }
            
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "id": request_id,
            "status": "ERROR",
            "code": 0,
            "time": elapsed,
            "error": str(e)
        }

def run_load_test(server_url, audio_file, users, total_reqs):
    print(f"\n🚀 Load Test Started")
    print(f"Target: {server_url}{ENDPOINT}")
    print(f"Audio File: {audio_file}")
    print(f"Concurrent Users: {users}")
    print(f"Total Requests: {total_reqs}")
    print("-" * 50)

    if not os.path.exists(audio_file):
        print(f"❌ Error: Audio file not found at {audio_file}")
        return

    url = f"{server_url}{ENDPOINT}"
    results = []
    start_time = time.time()

    # ThreadPoolExecutor를 사용하여 동시 요청 시뮬레이션
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as executor:
        futures = [executor.submit(send_request, url, audio_file, i) for i in range(total_reqs)]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            results.append(res)
            print(f"[{i+1}/{total_reqs}] {res['status']} ({res['time']:.2f}s) - {res['error'] or ''}")

    total_duration = time.time() - start_time
    
    # 결과 분석
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    fail_count = len(results) - success_count
    avg_slatency = sum(r['time'] for r in results) / len(results) if results else 0
    max_latency = max(r['time'] for r in results) if results else 0
    min_latency = min(r['time'] for r in results) if results else 0
    
    print("-" * 50)
    print(f"📊 Test Summary")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Requests: {total_reqs} (Success: {success_count}, Fail: {fail_count})")
    print(f"Average Latency: {avg_slatency:.2f}s")
    print(f"Min/Max Latency: {min_latency:.2f}s / {max_latency:.2f}s")
    print(f"Throughput: {total_reqs / total_duration:.2f} req/s")
    print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Load Tester for Voice Search API")
    parser.add_argument("--url", default=DEFAULT_SERVER_URL, help="Server Base URL")
    parser.add_argument("--file", default=DEFAULT_AUDIO_FILE, help="Path to audio file")
    parser.add_argument("--users", type=int, default=CONCURRENT_USERS, help="Concurrent users")
    parser.add_argument("--requests", type=int, default=TOTAL_REQUESTS, help="Total requests to send")
    
    args = parser.parse_args()
    
    run_load_test(args.url, args.file, args.users, args.requests)
