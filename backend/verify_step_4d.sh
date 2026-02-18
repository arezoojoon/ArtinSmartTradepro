#!/usr/bin/env bash
set -euo pipefail

echo "--- Verifying Step 4D: WAHA Bot + CRM Follow-Ups ---"

# ── Config ──────────────────────────────────────────────
BASE_URL="http://localhost:8000/api/v1"
EMAIL="arezoom@artinwebs.org"
PASSWORD="Arezoo@2025@@"
DB_USER="artin"
DB_NAME="artin_trade"
DB_CONTAINER="artinsmarttrade-db-1"

psql_exec() {
  docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -tAc "$1"
}

# ── Wait for backend ───────────────────────────────────
echo "Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

# ── Login ───────────────────────────────────────────────
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/auth/login" \
  -F "email=$EMAIL" \
  -F "password=$PASSWORD")
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed."
  echo "$LOGIN_RESP"
  exit 1
fi
echo "Token: ${TOKEN:0:15}..."

# ── Get Tenants ─────────────────────────────────────────
TENANTS_RESP=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/tenants")
TENANT_A_ID=$(echo "$TENANTS_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tenants = data if isinstance(data, list) else data.get('tenants', data.get('items', []))
print(tenants[0]['id'] if tenants else '')
" 2>/dev/null || echo "")

if [ -z "$TENANT_A_ID" ]; then
  echo "❌ No tenants found. Creating test tenants..."
  TENANT_A_RESP=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"name":"Tenant D4A","plan":"professional","mode":"hybrid"}' "$BASE_URL/tenants")
  TENANT_A_ID=$(echo "$TENANT_A_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "Created Tenant A: $TENANT_A_ID"
else
  echo "Using existing Tenant A: $TENANT_A_ID"
fi

# ── Switch to Tenant A ──────────────────────────────────
SWITCH_RESP=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$BASE_URL/tenants/$TENANT_A_ID/switch")
echo "Switch response: $SWITCH_RESP"

# ═══════════════════════════════════════════════════════
# TEST 1: Follow-Up Rules CRUD
# ═══════════════════════════════════════════════════════
echo ""
echo "=== Test 1: Follow-Up Rules CRUD ==="

# 1a. Create a follow-up rule
CREATE_RULE_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"24h No-Reply","template_body":"Hi {{name}}, just following up on our conversation.","delay_minutes":1440,"max_attempts":2,"trigger_event":"no_reply","channel":"whatsapp"}' \
  "$BASE_URL/followups/rules")

if [ "$CREATE_RULE_RESP" = "200" ] || [ "$CREATE_RULE_RESP" = "201" ]; then
  echo "✅ Create Rule: $CREATE_RULE_RESP"
elif [ "$CREATE_RULE_RESP" = "403" ]; then
  echo "⚠️  Create Rule: 403 (feature gated — expected if no plan features seeded)"
else
  echo "❌ Create Rule: HTTP $CREATE_RULE_RESP"
  # Get full response for debugging
  curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"24h No-Reply","template_body":"test","delay_minutes":1440}' \
    "$BASE_URL/followups/rules"
fi

# 1b. List rules  
LIST_RULES_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/followups/rules")

if [ "$LIST_RULES_CODE" = "200" ]; then
  echo "✅ List Rules: $LIST_RULES_CODE"
elif [ "$LIST_RULES_CODE" = "403" ]; then
  echo "⚠️  List Rules: 403 (feature gated)"
else
  echo "❌ List Rules: HTTP $LIST_RULES_CODE"
fi

# 1c. List executions
LIST_EXEC_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/followups/executions")

if [ "$LIST_EXEC_CODE" = "200" ]; then
  echo "✅ List Executions: $LIST_EXEC_CODE"
elif [ "$LIST_EXEC_CODE" = "403" ]; then
  echo "⚠️  List Executions: 403 (feature gated)"
else
  echo "❌ List Executions: HTTP $LIST_EXEC_CODE"
fi

# ═══════════════════════════════════════════════════════
# TEST 2: WhatsApp Endpoint
# ═══════════════════════════════════════════════════════
echo ""
echo "=== Test 2: WhatsApp Send Endpoint ==="

WA_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipient_phone":"+15550000000","content":"test","template_name":"hello_world"}' \
  "$BASE_URL/whatsapp/send")

if [ "$WA_CODE" = "200" ]; then
  echo "✅ WhatsApp Send: $WA_CODE"
elif [ "$WA_CODE" = "402" ] || [ "$WA_CODE" = "403" ]; then
  echo "✅ WhatsApp Send: $WA_CODE (expected — insufficient credits or feature gated)"
elif [ "$WA_CODE" = "500" ]; then
  echo "❌ WhatsApp Send: 500 (server error)"
  curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"recipient_phone":"+15550000000","content":"test","template_name":"hello_world"}' \
    "$BASE_URL/whatsapp/send"
else
  echo "⚠️  WhatsApp Send: HTTP $WA_CODE"
fi

# ═══════════════════════════════════════════════════════
# TEST 3: WAHA Endpoints
# ═══════════════════════════════════════════════════════
echo ""
echo "=== Test 3: WAHA Endpoints ==="

# 3a. List deeplinks
DL_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/waha/deeplinks")

if [ "$DL_CODE" = "200" ]; then
  echo "✅ List Deeplinks: $DL_CODE"
elif [ "$DL_CODE" = "404" ]; then
  echo "❌ List Deeplinks: 404 (route not found — wiring issue)"
else
  echo "⚠️  List Deeplinks: HTTP $DL_CODE"
fi

# 3b. List sessions
SESS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/waha/sessions")

if [ "$SESS_CODE" = "200" ]; then
  echo "✅ List Sessions: $SESS_CODE"
elif [ "$SESS_CODE" = "404" ]; then
  echo "❌ List Sessions: 404 (route not found — wiring issue)"
else
  echo "⚠️  List Sessions: HTTP $SESS_CODE"
fi

# ═══════════════════════════════════════════════════════
# TEST 4: No 500s — Smoke test all 4D endpoints
# ═══════════════════════════════════════════════════════
echo ""
echo "=== Test 4: No 500 Errors (Smoke Test) ==="

FAIL_COUNT=0
for endpoint in "followups/rules" "followups/executions" "waha/deeplinks" "waha/sessions"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/$endpoint")
  if [ "$CODE" = "500" ]; then
    echo "❌ GET /$endpoint → 500"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  else
    echo "✅ GET /$endpoint → $CODE"
  fi
done

if [ "$FAIL_COUNT" -eq 0 ]; then
  echo ""
  echo "✅ No 500 errors across Step 4D endpoints."
else
  echo ""
  echo "❌ $FAIL_COUNT endpoint(s) returned 500."
fi

echo ""
echo "--- Step 4D Verification COMPLETE ---"
