import requests
import uuid
import sys
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

def log(msg, success=True):
    color = Color.GREEN if success else Color.RED
    mark = "✅" if success else "❌"
    print(f"{color}{mark} {msg}{Color.RESET}")

def register_user(email, password):
    # 1. Register
    reg_data = {
        "email": email,
        "password": password,
        "full_name": "Test User",
        "company_name": f"Company {uuid.uuid4()}",
        "phone": "+1234567890"
    }
    resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    if resp.status_code not in [200, 201]:
        return None, f"Registration failed: {resp.text}"
    
    # 2. Login
    login_data = {"username": email, "password": password}
    resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if resp.status_code != 200:
        return None, f"Login failed: {resp.text}"
        
    return resp.json()["access_token"], None

def run_smoke_test():
    print("🚀 Starting Final Release Gate Verification...\n")

    # 1. Health Check
    try:
        resp = requests.get(HEALTH_URL)
        if resp.status_code == 200:
            log("Health Check Passed")
        else:
            log(f"Health Check Failed: {resp.status_code}", False)
            sys.exit(1)
    except Exception as e:
        log(f"Health Check Failed: {e}", False)
        sys.exit(1)

    # 2. Tenant Isolation Test (Section D)
    print("\n🔒 Testing Tenant Isolation (Section D)...")
    
    # User A
    email_a = f"tenant_a_{uuid.uuid4()}@example.com"
    token_a, err = register_user(email_a, "password123")
    if err:
        log(f"User A Setup Failed: {err}", False)
        return
    log(f"Registered Tenant A: {email_a}")

    # User B
    email_b = f"tenant_b_{uuid.uuid4()}@example.com"
    token_b, err = register_user(email_b, "password123")
    if err:
        log(f"User B Setup Failed: {err}", False)
        return
    log(f"Registered Tenant B: {email_b}")

    # A creates data
    headers_a = {"Authorization": f"Bearer {token_a}"}
    contact_data = {"first_name": "Secret", "last_name": "Contact", "email": "secret@a.com"}
    resp = requests.post(f"{BASE_URL}/crm/contacts", json=contact_data, headers=headers_a)
    if resp.status_code != 200:
        log(f"Tenant A failed to create contact: {resp.text}", False)
        return
    contact_id = resp.json()["id"]
    log(f"Tenant A created contact {contact_id}")

    # B tries to read data
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp = requests.get(f"{BASE_URL}/crm/contacts/{contact_id}", headers=headers_b)
    
    if resp.status_code == 404:
        log("Tenant Isolation PASSED: Tenant B got 404 accessing Tenant A's data")
    elif resp.status_code == 200:
        log("Tenant Isolation FAILED: Tenant B can see Tenant A's data!", False)
    elif resp.status_code == 403:
        log("Tenant Isolation WARNING: Got 403 instead of 404 (Security Verification)", False)
    else:
        log(f"Tenant Isolation ERROR: Unexpected status {resp.status_code}", False)

    # 3. Plan Enforcement (Section B)
    print("\n🛡️ Testing Plan Enforcement (Section B)...")
    # Basic user trying Pro feature (Hunter)
    resp = requests.post(
        f"{BASE_URL}/hunter/start", 
        json={"query": "test", "limit": 10}, 
        headers=headers_a
    )
    if resp.status_code == 403:
         log("Plan Enforcement PASSED: Basic user blocked from Hunter (403)")
    elif resp.status_code == 402:
         log("Plan Enforcement PASSED: Basic user blocked from Hunter (402 Payment Required)")
    else:
         log(f"Plan Enforcement FAILED: Basic user got {resp.status_code} for Pro feature", False)

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    run_smoke_test()
