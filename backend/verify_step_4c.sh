#!/usr/bin/env bash
# verify_step_4c.sh — Verify Hunter -> CRM Pipeline (IDOR + Dedup)

BASE_URL="http://localhost:8000/api/v1"
echo "--- Verifying Step 4C: Hunter Pipeline ---"

# 1. Login Tenant A (from previous step or fresh)
# We assume verify_step_4a.sh logic for login. For now, let's just get a fresh token for Tenant A.
# Actually, to make this robust, let's use the Superuser to login as Tenant A user (if exists) 
# OR just rely on superuser + tenant_id header if we were testing raw.
# But auth middleware usually requires a user linked to tenant.
# Let's borrow the login logic from verify_step_4a.sh quickly.

# --- Helper Functions ---
login() {
  local email=$1
  local password=$2
  
  # Use /auth/login as seen in verify_step_4a.sh
  RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -F "email=$email" \
    -F "password=$password")
  
  if [[ "$RESPONSE" == *"access_token"* ]]; then
      TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
      echo $TOKEN
  else
      echo ""
  fi
}

# Use superadmin credentials from verify_step_4a.sh
# Try default superadmin
TOKEN=$(login "superadmin@artin.com" "Super@1234")

# Fallback to server env credentials if default failed
if [ -z "$TOKEN" ]; then
  echo "Default login failed. Trying server credentials..."
  TOKEN=$(login "arezoom@artinwebs.org" "Arezoo123!")
fi

if [ -z "$TOKEN" ]; then
  echo "Login failed. Run generate_schema.sh first."
  exit 1
fi

echo "Token: ${TOKEN:0:10}..."

# Get Tenant A ID
# We need to know Tenant A's ID. 
# Let's fetch tenants and pick the first one as "Tenant A" and second as "Tenant B"
TENANTS_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/tenants/")
TENANT_A_ID=$(echo $TENANTS_JSON | grep -o '"id":"[^"]*"' | head -n1 | cut -d'"' -f4)
TENANT_B_ID=$(echo $TENANTS_JSON | grep -o '"id":"[^"]*"' | head -n2 | tail -n1 | cut -d'"' -f4)

echo "Tenant A: $TENANT_A_ID"
echo "Tenant B: $TENANT_B_ID"

if [ -z "$TENANT_A_ID" ] || [ -z "$TENANT_B_ID" ]; then
  echo "Need 2 tenants. Run verify_step_4a.sh first."
  exit 1
fi

# Switch to Tenant A
# We need to switch context? 
# Using the switch endpoint updates the user's active_tenant_id usually?
# Let's use the /auth/switch-tenant endpoint.
curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/switch-tenant/$TENANT_A_ID" > /dev/null
echo "Switched to Tenant A."

# 2. Simulate a Hunter Result (Fake)
# We can't easily Insert via API because Hunter runs are async.
# We will cheat and Insert a HunterResult via SQL (using docker exec) to ensure we have a controllled test case.

SQL="INSERT INTO hunter_runs (id, tenant_id, target_keyword, sources, status, created_at) VALUES ('11111111-1111-1111-1111-111111111111', '$TENANT_A_ID', 'test', '[\"manual\"]', 'completed', NOW());"
SQL+="INSERT INTO hunter_results (id, run_id, tenant_id, source, type, name, company, email, phone, website, confidence_score, is_imported) VALUES ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', '$TENANT_A_ID', 'manual', 'lead', 'Alice Target', 'Target Corp', 'alice@target.com', '+15550001', 'target.com', 0.9, false);"

# Exec SQL
docker exec -i artinsmarttrade-db-1 psql -U artin -d artin_trade -c "$SQL" > /dev/null 2>&1
echo "Inserted Mock HunterResult for Tenant A."

# 3. Test Validation: Tenant B attempts to Import Tenant A's result (IDOR)
# Switch to B
curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/switch-tenant/$TENANT_B_ID" > /dev/null
echo "Switched to Tenant B."

RESPONSE_IDOR=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"result_id": "22222222-2222-2222-2222-222222222222"}' "$BASE_URL/hunter/import-to-crm")

if [ "$RESPONSE_IDOR" == "400" ] || [ "$RESPONSE_IDOR" == "404" ] || [ "$RESPONSE_IDOR" == "403" ]; then
  echo "✅ IDOR Check Passed (Code: $RESPONSE_IDOR) - Tenant B blocked from importing A's result."
else
  echo "❌ IDOR Check FAILED (Code: $RESPONSE_IDOR) - Tenant B was able to access A's result!"
  exit 1
fi

# 4. Test Success: Tenant A imports
# Switch back to A
curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/switch-tenant/$TENANT_A_ID" > /dev/null
echo "Switched to Tenant A."

IMPORT_RESP=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"result_id": "22222222-2222-2222-2222-222222222222"}' "$BASE_URL/hunter/import-to-crm")

if echo "$IMPORT_RESP" | grep -q "contact_id"; then
  echo "✅ Valid Import Successful."
  CONTACT_ID=$(echo $IMPORT_RESP | grep -o '"contact_id":"[^"]*' | cut -d'"' -f4)
  echo "Created Contact: $CONTACT_ID"
else
  echo "❌ Import Failed: $IMPORT_RESP"
  exit 1
fi

# 5. Test Deduplication / Idempotency
# Try importing again
IMPORT_RESP_2=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"result_id": "22222222-2222-2222-2222-222222222222"}' "$BASE_URL/hunter/import-to-crm")

CONTACT_ID_2=$(echo $IMPORT_RESP_2 | grep -o '"contact_id":"[^"]*' | cut -d'"' -f4)

if [ "$CONTACT_ID" == "$CONTACT_ID_2" ]; then
  echo "✅ Deduplication/Idempotency Passed (Returned same Contact ID)."
else
  echo "❌ Dedup Failed! (New ID: $CONTACT_ID_2 vs Old: $CONTACT_ID)"
  exit 1
fi

# Cleanup
# Optional: Delete the test rows
# docker exec -i artinsmarttrade-db-1 psql -U artin -d artin_trade -c "DELETE FROM hunter_results WHERE id='22222222-2222-2222-2222-222222222222'; DELETE FROM hunter_runs WHERE id='11111111-1111-1111-1111-111111111111';"

echo "--- Step 4C Verification COMPLETE ---"
