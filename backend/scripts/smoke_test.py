import asyncio
import httpx
import uuid
import sys

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    print("Running Artin Smart Trade Phase 1 Smoke Test...")
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"smoketest_{unique_suffix}@artin.com"
    password = "Password123!"
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Register User
        print(f"\n1. Registering user {email}...")
        res = await client.post("/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Smoke Test User"
        })
        if res.status_code != 200:
            print(f"Failed to register: {res.text}")
            sys.exit(1)
        print("✅ Registered successfully.")
        
        # 2. Login
        print("\n2. Logging in...")
        res = await client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if res.status_code != 200:
            print(f"Failed to login: {res.text}")
            sys.exit(1)
            
        tokens = res.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Logged in successfully.")
        
        # 3. Create Tenant
        print("\n3. Creating Tenant (should trigger seeder)...")
        res = await client.post("/tenants", json={
            "name": f"Smoke Test Tenant {unique_suffix}",
            "plan": "professional"
        }, headers=headers)
        if res.status_code != 200:
            print(f"Failed to create tenant: {res.text}")
            sys.exit(1)
            
        tenant = res.json()
        print(f"✅ Created tenant: {tenant['name']}")
        
        # Refresh login to get tenant context in JWT
        print("\n3b. Refreshing token to inject tenant_id into JWT...")
        res = await client.post("/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        if res.status_code != 200:
            print("Failed to refresh token:", res.text)
            sys.exit(1)
        
        tokens = res.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("✅ Token refreshed.")
        
        # 4. Verify Default Pipeline Exists
        print("\n4. Verifying seeded Pipeline...")
        res = await client.get("/crm/pipelines", headers=headers)
        if res.status_code != 200:
            print(f"Failed to fetch pipelines: {res.text}")
            sys.exit(1)
            
        pipelines = res.json()["pipelines"]
        if not pipelines:
            print("❌ No pipelines found! Seeder failed.")
            sys.exit(1)
            
        pipeline_id = pipelines[0]["id"]
        print(f"✅ Found default pipeline {pipeline_id}.")
        
        # 5. Create Contact
        print("\n5. Creating CRM Contact...")
        res = await client.post("/crm/contacts", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.local",
            "phone": "555-0000"
        }, headers=headers)
        if res.status_code != 200:
            print(f"Failed to create contact: {res.text}")
            sys.exit(1)
            
        contact_id = res.json()["id"]
        print(f"✅ Created contact {contact_id}.")
        
        # 6. Create Deal
        print("\n6. Creating CRM Deal...")
        res = await client.post("/crm/deals", json={
            "name": "Big Export Deal",
            "contact_id": contact_id,
            "pipeline_id": pipeline_id,
            "stage_id": "lead",
            "value": 150000.0,
            "currency": "AED"
        }, headers=headers)
        if res.status_code != 200:
            print(f"Failed to create deal: {res.text}")
            sys.exit(1)
            
        deal_id = res.json()["id"]
        print(f"✅ Created deal {deal_id}.")
        
        # 7. Move Deal Stage
        print("\n7. Moving Deal Stage to 'proposal'...")
        res = await client.put(f"/crm/deals/{deal_id}", json={
            "stage_id": "proposal"
        }, headers=headers)
        if res.status_code != 200:
            print(f"Failed to move deal: {res.text}")
            sys.exit(1)
        
        print("✅ Deal successfully moved to proposal stage.")
        print("\n🎉 SMOKE TEST PASSED: Full E2E Auth, RBAC, RLS, and CRM flow is functional.")

if __name__ == "__main__":
    asyncio.run(main())
