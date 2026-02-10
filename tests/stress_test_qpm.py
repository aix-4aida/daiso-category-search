"""
어디다있소 - QPM (Queries Per Minute) 스트레스 테스트
Usage:
  python tests/stress_test_qpm.py --url http://localhost:8000 --qpm 60 --duration 60
"""

import asyncio
import aiohttp
import argparse
import time
import statistics
import json
from datetime import datetime


async def send_request(session, url, payload, results):
    """Send a single request and record timing."""
    start = time.perf_counter()
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            status = resp.status
            await resp.read()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            results.append({
                'status': status,
                'latency_ms': elapsed,
                'success': 200 <= status < 300
            })
    except asyncio.TimeoutError:
        elapsed = (time.perf_counter() - start) * 1000
        results.append({
            'status': 'timeout',
            'latency_ms': elapsed,
            'success': False
        })
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        results.append({
            'status': f'error: {str(e)[:50]}',
            'latency_ms': elapsed,
            'success': False
        })


async def run_stress_test(base_url, target_qpm, duration_sec):
    """Run QPM stress test."""
    search_url = f"{base_url.rstrip('/')}/search/text"
    
    # Test queries
    test_queries = [
        "샴푸", "냄비", "볼펜", "채반", "규조토 욕실 매트",
        "화장실", "수납박스", "텀블러", "마스크팩", "프라이팬",
        "USB 케이블", "포장지", "스티커", "행거", "쓰레기봉투"
    ]
    
    total_requests = int(target_qpm * (duration_sec / 60))
    interval = 60 / target_qpm  # seconds between requests
    
    print("=" * 60)
    print(f"  어디다있소 QPM Stress Test")
    print("=" * 60)
    print(f"  Target URL  : {search_url}")
    print(f"  Target QPM  : {target_qpm}")
    print(f"  Duration    : {duration_sec}s")
    print(f"  Total Reqs  : {total_requests}")
    print(f"  Interval    : {interval:.3f}s")
    print("=" * 60)
    print()
    
    results = []
    
    # Check health first
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url.rstrip('/')}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    print("✅ Health check passed")
                else:
                    print(f"⚠️ Health check returned: {resp.status}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            print("   Proceeding anyway...\n")
    
    # Run test
    async with aiohttp.ClientSession() as session:
        start_time = time.perf_counter()
        tasks = []
        
        for i in range(total_requests):
            query = test_queries[i % len(test_queries)]
            payload = {"query": query}
            
            task = asyncio.create_task(
                send_request(session, search_url, payload, results)
            )
            tasks.append(task)
            
            # Progress
            if (i + 1) % 10 == 0:
                elapsed = time.perf_counter() - start_time
                print(f"  [{i+1}/{total_requests}] sent ({elapsed:.1f}s elapsed)")
            
            # Rate limiting
            await asyncio.sleep(interval)
        
        # Wait for all remaining
        await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time
    
    # ── Analyze Results ──
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    
    latencies = [r['latency_ms'] for r in results]
    successes = [r for r in results if r['success']]
    failures = [r for r in results if not r['success']]
    
    if latencies:
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        actual_qpm = len(results) / (total_time / 60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "target_url": search_url,
                "target_qpm": target_qpm,
                "duration_sec": duration_sec,
                "total_requests": total_requests
            },
            "results": {
                "total_time_sec": round(total_time, 2),
                "actual_qpm": round(actual_qpm, 1),
                "total_requests": len(results),
                "successes": len(successes),
                "failures": len(failures),
                "success_rate": f"{len(successes)/len(results)*100:.1f}%",
                "latency_ms": {
                    "avg": round(statistics.mean(latencies), 1),
                    "min": round(min(latencies), 1),
                    "max": round(max(latencies), 1),
                    "p50": round(p50, 1),
                    "p95": round(p95, 1),
                    "p99": round(p99, 1),
                    "stdev": round(statistics.stdev(latencies), 1) if len(latencies) > 1 else 0
                }
            }
        }
        
        print(f"  Total Time    : {total_time:.2f}s")
        print(f"  Actual QPM    : {actual_qpm:.1f}")
        print(f"  Success Rate  : {len(successes)}/{len(results)} ({len(successes)/len(results)*100:.1f}%)")
        print(f"  Failures      : {len(failures)}")
        print()
        print(f"  Latency (ms):")
        print(f"    Average     : {statistics.mean(latencies):.1f}")
        print(f"    P50         : {p50:.1f}")
        print(f"    P95         : {p95:.1f}")
        print(f"    P99         : {p99:.1f}")
        print(f"    Min         : {min(latencies):.1f}")
        print(f"    Max         : {max(latencies):.1f}")
        
        # SLA check
        print()
        sla_pass = p95 < 3000
        print(f"  SLA (P95 < 3s): {'✅ PASS' if sla_pass else '❌ FAIL'}")
        
        # Save report
        report_path = f"tests/qpm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Report saved: {report_path}")
        
    else:
        print("  No results collected!")
    
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='QPM Stress Test for 어디다있소')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--qpm', type=int, default=60, help='Target queries per minute')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    
    args = parser.parse_args()
    
    asyncio.run(run_stress_test(args.url, args.qpm, args.duration))
