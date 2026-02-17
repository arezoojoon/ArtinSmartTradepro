#!/bin/bash
set -e

# 0) Environment sanity
echo "--- Environment ---"
pwd
# docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "Docker ps failed"
# docker logs --tail 80 artin_api || echo "Docker logs failed"

# 1) Authentication
echo "--- Login ---"
RES=$(curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -F "email=superadmin@artin.com" \
  -F "password=Super@1234")

# Check if response contains access_token
if [[ "$RES" != *"access_token"* ]]; then
  echo "LOGIN FAILED. Response:"
  echo "$RES"
  exit 1
fi

TOKEN=$(echo "$RES" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "TOKEN_LEN=${#TOKEN}"

# 2) Create Tenants
echo "--- Create Tenants ---"
TENANT_A_JSON=$(curl -sS -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tenant A","plan":"professional"}')
echo "Tenant A Response: $TENANT_A_JSON"
TENANT_A=$(echo $TENANT_A_JSON | python3 -c "import sys,json; print(json.load(sys.stdin).get('id') or '')")

TENANT_B_JSON=$(curl -sS -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tenant B","plan":"professional"}')
echo "Tenant B Response: $TENANT_B_JSON"
TENANT_B=$(echo $TENANT_B_JSON | python3 -c "import sys,json; print(json.load(sys.stdin).get('id') or '')")

echo "A=$TENANT_A"
echo "B=$TENANT_B"

# 3) Switch to Tenant A & Create Company
echo "--- Context A ---"
curl -sS -X POST "http://localhost:8000/api/v1/tenants/$TENANT_A/switch" \
  -H "Authorization: Bearer $TOKEN"
  
curl -sS -X POST "http://localhost:8000/api/v1/crm/companies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"SpaceX","domain":"spacex.com","industry":"Aerospace"}'

echo "List A:"
curl -sS "http://localhost:8000/api/v1/crm/companies" \
  -H "Authorization: Bearer $TOKEN"

# 4) Switch to Tenant B
echo "--- Context B ---"
curl -sS -X POST "http://localhost:8000/api/v1/tenants/$TENANT_B/switch" \
  -H "Authorization: Bearer $TOKEN"

echo "List B:"
curl -sS "http://localhost:8000/api/v1/crm/companies" \
  -H "Authorization: Bearer $TOKEN"
