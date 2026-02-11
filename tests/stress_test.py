"""
Production Stress Test — Simulates realistic load conditions.
Run with: python tests/stress_test.py
Requires: pip install httpx asyncio
"""
import asyncio
import time
import random
import httpx
from collections import defaultdict

BASE_URL = "http://localhost:8000/api/v1"

# Configuration
TOTAL_CONCURRENT_USERS = 50
REQUESTS_PER_USER = 10
MAX_TIMEOUT = 30.0

# Results tracking
results = defaultdict(lambda: {"success": 0, "error": 0, "latencies": []})


async def register_and_login(client: httpx.AsyncClient, user_id: int) -> dict:
    """Register a user, login, and return auth headers."""
    email = f"stress_{user_id}_{int(time.time())}@test.com"
    
    # Register
    await client.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "stress123",
        "full_name": f"Stress User {user_id}",
        "company_name": f"Stress Corp {user_id}",
    })
    
    # Login
    resp = await client.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": "stress123",
    })
    
    if resp.status_code != 200:
        return None
    
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def simulate_user_session(user_id: int):
    """Simulate a single user making multiple API calls."""
    async with httpx.AsyncClient(timeout=MAX_TIMEOUT) as client:
        headers = await register_and_login(client, user_id)
        if not headers:
            results["login"]["error"] += 1
            return

        results["login"]["success"] += 1

        # Mix of API calls
        endpoints = [
            ("GET", "/admin/stats", None, "admin_stats"),
            ("POST", "/trade/analyze/seasonal", {"product": "cocoa", "region": "europe"}, "trade_seasonal"),
            ("POST", "/brain/decide", {
                "product": "cocoa", "origin_country": "Ghana",
                "destination_country": "Germany", "quantity_kg": 1000,
                "budget_usd": 50000,
            }, "brain_decide"),
        ]

        for _ in range(REQUESTS_PER_USER):
            method, path, body, label = random.choice(endpoints)
            start = time.monotonic()
            try:
                if method == "GET":
                    resp = await client.get(f"{BASE_URL}{path}", headers=headers)
                else:
                    resp = await client.post(f"{BASE_URL}{path}", json=body, headers=headers)

                latency = time.monotonic() - start
                results[label]["latencies"].append(latency)

                if resp.status_code in (200, 403, 402):  # 403/402 are valid gates
                    results[label]["success"] += 1
                else:
                    results[label]["error"] += 1
            except Exception as e:
                results[label]["error"] += 1


async def run_stress_test():
    """Run full stress test."""
    print(f"🔥 Starting stress test: {TOTAL_CONCURRENT_USERS} users × {REQUESTS_PER_USER} requests")
    print(f"   Total requests: ~{TOTAL_CONCURRENT_USERS * REQUESTS_PER_USER}")
    print()

    start = time.monotonic()
    tasks = [simulate_user_session(i) for i in range(TOTAL_CONCURRENT_USERS)]
    await asyncio.gather(*tasks)
    total_time = time.monotonic() - start

    # Report
    print(f"\n{'=' * 60}")
    print(f"STRESS TEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Effective RPS: {sum(r['success'] + r['error'] for r in results.values()) / total_time:.1f}")
    print()

    for label, data in sorted(results.items()):
        lats = data["latencies"]
        print(f"\n📊 {label.upper()}")
        print(f"   Success: {data['success']}  |  Error: {data['error']}")
        if lats:
            lats.sort()
            p50 = lats[int(len(lats) * 0.50)]
            p95 = lats[int(len(lats) * 0.95)] if len(lats) > 20 else lats[-1]
            p99 = lats[int(len(lats) * 0.99)] if len(lats) > 100 else lats[-1]
            print(f"   P50: {p50:.3f}s  |  P95: {p95:.3f}s  |  P99: {p99:.3f}s")
            print(f"   Min: {min(lats):.3f}s  |  Max: {max(lats):.3f}s")

    # Verdict
    total_errors = sum(r["error"] for r in results.values())
    total_requests = sum(r["success"] + r["error"] for r in results.values())
    error_rate = total_errors / max(total_requests, 1) * 100

    print(f"\n{'=' * 60}")
    if error_rate > 5:
        print(f"❌ FAIL — Error rate: {error_rate:.1f}% (target: <5%)")
    elif error_rate > 1:
        print(f"⚠️  WARNING — Error rate: {error_rate:.1f}% (target: <1%)")
    else:
        print(f"✅ PASS — Error rate: {error_rate:.1f}%")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
