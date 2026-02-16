import asyncio
import httpx
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@example.com" 
PASSWORD = "password"

async def verify_isolation():
    print(f"--- VERIFICATION START: {BASE_URL} ---")
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Login
        print(f"\n[1] Logging in as {EMAIL}...")
        res = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if res.status_code != 200:
            print(f"FATAL: Login failed: {res.text}")
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("    -> Token acquired.")

        # 2. Create Tenant A
        print("\n[2] Creating Tenant A...")
        res = await client.post("/tenants", json={"name": "Tenant A", "plan": "free"}, headers=headers)
        if res.status_code in [200, 201]:
             tenant_a_id = res.json()["id"]
        else:
             # Fallback if exists
             res = await client.get("/tenants", headers=headers)
             tenants = res.json()["tenants"]
             tenant_a = next((t for t in tenants if t["tenant_name"] == "Tenant A"), None)
             tenant_a_id = tenant_a["tenant_id"]
        print(f"    -> Tenant A ID: {tenant_a_id}")

        # 3. Switch to Tenant A
        print(f"\n[3] Switching context to Tenant A ({tenant_a_id})...")
        res = await client.post(f"/tenants/{tenant_a_id}/switch", headers=headers)
        print(f"    -> Status: {res.status_code}, Body: {res.text}")

        # 4. Create Company in Tenant A
        print("\n[4] Creating CRM Company 'SpaceX' in Tenant A...")
        res = await client.post("/crm/companies", json={"name": "SpaceX", "domain": "spacex.com"}, headers=headers)
        print(f"    -> Status: {res.status_code}") 
        print(f"    -> Body: {res.json()}")

        # 5. Create Tenant B
        print("\n[5] Creating Tenant B...")
        res = await client.post("/tenants", json={"name": "Tenant B", "plan": "free"}, headers=headers)
        if res.status_code in [200, 201]:
             tenant_b_id = res.json()["id"]
        else:
             res = await client.get("/tenants", headers=headers)
             tenants = res.json()["tenants"]
             tenant_b = next((t for t in tenants if t["tenant_name"] == "Tenant B"), None)
             tenant_b_id = tenant_b["tenant_id"]
        print(f"    -> Tenant B ID: {tenant_b_id}")

        # 6. Switch to Tenant B
        print(f"\n[6] Switching context to Tenant B ({tenant_b_id})...")
        res = await client.post(f"/tenants/{tenant_b_id}/switch", headers=headers)
        print(f"    -> Status: {res.status_code}")

        # 7. List Companies in Tenant B
        print("\n[7] Listing CRM Companies in Tenant B (Expect EMPTY)...")
        res = await client.get("/crm/companies", headers=headers)
        print(f"    -> Status: {res.status_code}")
        print(f"    -> Body: {res.text}")
        
        companies_b = res.json()
        if any(c["name"] == "SpaceX" for c in companies_b):
            print("❌ FAIL: Isolation Broken! SpaceX found in Tenant B.")
        else:
            print("✅ PASS: Tenant B is clean.")

        # 8. Switch back to Tenant A
        print(f"\n[8] Switching back to Tenant A ({tenant_a_id})...")
        await client.post(f"/tenants/{tenant_a_id}/switch", headers=headers)

        # 9. List Companies in Tenant A
        print("\n[9] Listing CRM Companies in Tenant A (Expect 'SpaceX')...")
        res = await client.get("/crm/companies", headers=headers)
        print(f"    -> Body: {res.text}")
        
        companies_a = res.json()
        if any(c["name"] == "SpaceX" for c in companies_a):
             print("✅ PASS: Tenant A data persisted and retrieved.")
        else:
             print("❌ FAIL: Data lost in Tenant A!")

if __name__ == "__main__":
    asyncio.run(verify_isolation())
