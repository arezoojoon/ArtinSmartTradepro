import asyncio
import httpx
import json
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
# DB_URL matches config.py default
DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/artin_trade"

EMAIL = "superadmin@artin.com"
PASSWORD = "Super@1234"

async def run_step(step_name, coro):
    print(f"\n# {step_name}")
    try:
        return await coro
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

async def verify():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        
        # 5.1 Login (Multipart Form Data)
        print("5.1 Login (must succeed and return JSON with access_token)")
        # Note: input names for OAuth2PasswordRequestForm are 'username' and 'password'
        # But user requested "email=..." and "password=..."
        # If the backend uses OAuth2PasswordRequestForm, it expects 'username'.
        # However, the user's curl command used -F "email=..." which might be accepted if the code maps it.
        # Let's check auth.py login... it uses request.form() -> data["email"]. So keys are email/password.
        
        res = await client.post("/auth/login", data={"email": EMAIL, "password": PASSWORD})
        print(res.text)
        if res.status_code != 200:
            print("Login failed.")
            return

        token_data = res.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"TOKEN_LEN={len(token)}")

        # 5.2 Create two tenants (A and B)
        print("\n5.2 Create two tenants (A and B)")
        
        # Tenant A
        res = await client.post("/tenants", json={"name": "Tenant A", "plan": "free"}, headers=headers)
        if res.status_code == 200:
            tenant_a = res.json()["id"]
        else:
            # Fallback find
            res = await client.get("/tenants", headers=headers)
            tenants = res.json()["tenants"]
            t = next((t for t in tenants if t["tenant_name"] == "Tenant A"), None)
            tenant_a = t["tenant_id"]
        
        # Tenant B
        res = await client.post("/tenants", json={"name": "Tenant B", "plan": "free"}, headers=headers)
        if res.status_code == 200:
            tenant_b = res.json()["id"]
        else:
            # Fallback find
            res = await client.get("/tenants", headers=headers)
            tenants = res.json()["tenants"]
            t = next((t for t in tenants if t["tenant_name"] == "Tenant B"), None)
            tenant_b = t["tenant_id"]

        print(f"A={tenant_a}")
        print(f"B={tenant_b}")

        # 5.3 Switch to Tenant A, create company
        print("\n5.3 Switch to Tenant A, create company, verify present")
        await client.post(f"/tenants/{tenant_a}/switch", headers=headers)
        
        # Create
        res = await client.post("/crm/companies", json={"name": "SpaceX", "domain": "spacex.com", "industry": "Aerospace"}, headers=headers)
        print(res.text) # Expect created company
        
        # List
        res = await client.get("/crm/companies", headers=headers)
        print(res.text) # Expect list with SpaceX

        # 5.4 Switch to Tenant B, verify SpaceX NOT present
        print("\n5.4 Switch to Tenant B, verify SpaceX NOT present")
        await client.post(f"/tenants/{tenant_b}/switch", headers=headers)
        
        res = await client.get("/crm/companies", headers=headers)
        print(res.text) # Expect empty list or list without SpaceX

        # 5.5 Direct DB proof
        print("\n5.5 Direct DB proof (company row tenant_id)")
        # Since 'docker exec psql' is not available in this environment, using sqlalchemy to mimic the output
        try:
            engine = create_async_engine(DB_URL)
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT name, domain, tenant_id FROM crm_companies WHERE name='SpaceX' ORDER BY created_at DESC LIMIT 5;"))
                rows = result.fetchall()
                print(" name   |   domain   |              tenant_id               ")
                print("--------+------------+--------------------------------------")
                for row in rows:
                    print(f" {row[0]:<6} | {row[1]:<10} | {row[2]}")
                print(f"({len(rows)} rows)")
        except Exception as e:
            print(f"DB Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
