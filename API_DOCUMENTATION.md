# 📚 Artin Smart Trade - API Documentation

> **Complete API reference for Artin Smart Trade platform**

## 📋 Table of Contents

- [🌟 Overview](#-overview)
- [🔐 Authentication](#-authentication)
- [🏢 Super Admin APIs](#-super-admin-apis)
- [🏢 Tenant Panel APIs](#-tenant-panel-apis)
- [🛠️ Toolbox APIs](#️-toolbox-apis)
- [🤝 CRM APIs](#-crm-apis)
- [📊 Data Models](#-data-models)
- [🔧 Error Handling](#-error-handling)
- [📈 Rate Limiting](#-rate-limiting)
- [🧪 Testing](#-testing)

## 🌟 Overview

Artin Smart Trade provides a comprehensive RESTful API for managing trade intelligence operations. The API follows REST principles and uses JSON for data exchange.

### 🌐 Base URLs

- **Production**: `https://api.artin-smart-trade.com`
- **Staging**: `https://staging-api.artin-smart-trade.com`
- **Development**: `http://localhost:8000`

### 📖 Interactive Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## 🔐 Authentication

### 📝 JWT Authentication

All API endpoints require JWT authentication except for public endpoints.

#### Login Request
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

#### Login Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "trade_manager",
    "tenant_id": "uuid"
  }
}
```

#### Using the Token
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 🔄 Token Refresh
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

### 🚪 Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

## 🏢 Super Admin APIs

### 📊 Revenue Dashboard

#### Get Revenue Summary
```http
GET /sys/revenue/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "mrr": 125000,
  "arr": 1500000,
  "growth_rate": 15.5,
  "churn_rate": 2.3,
  "active_subscriptions": 450,
  "period": "current_month"
}
```

#### Get Revenue Trends
```http
GET /sys/revenue/trends?period=12m
Authorization: Bearer <token>
```

### 🏥 Health Monitoring

#### Get System Health
```http
GET /sys/health
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-22T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 45
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "external_apis": {
      "comtrade": "healthy",
      "freight": "healthy",
      "fx": "healthy"
    }
  }
}
```

#### Get Connector Status
```http
GET /sys/health/connectors
Authorization: Bearer <token>
```

### 🔒 Security Operations

#### Get Security Anomalies
```http
GET /sys/security/anomalies
Authorization: Bearer <token>
```

#### Rotate API Keys
```http
POST /sys/security/rotate-keys
Authorization: Bearer <token>
```

### 🎫 Support Tickets

#### List Support Tickets
```http
GET /sys/support/tickets?status=open&priority=high
Authorization: Bearer <token>
```

#### Create Support Ticket
```http
POST /sys/support/tickets
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Login Issue",
  "description": "User unable to login",
  "priority": "medium",
  "tenant_id": "uuid"
}
```

### 💰 Cost Dashboard

#### Get Cost Summary
```http
GET /sys/costs/summary
Authorization: Bearer <token>
```

#### Get Cost Trends
```http
GET /sys/costs/trends?period=6m
Authorization: Bearer <token>
```

## 🏢 Tenant Panel APIs

### 📱 Mobile Control Tower

#### Get Mobile Dashboard
```http
GET /dashboard/mobile
Authorization: Bearer <token>
```

**Response:**
```json
{
  "liquidity": {
    "source": "Wallet API",
    "timestamp": "2024-02-22T10:30:00Z",
    "confidence": 0.95,
    "data": {
      "available_balance": 250000,
      "currency": "USD",
      "last_updated": "2024-02-22T10:25:00Z"
    }
  },
  "opportunities": {
    "source": "Hunter Engine",
    "timestamp": "2024-02-22T10:30:00Z",
    "confidence": 0.88,
    "data": {
      "new_opportunities": 15,
      "high_value_count": 3,
      "total_potential": 1250000
    }
  },
  "risks": {
    "source": "Risk Engine",
    "timestamp": "2024-02-22T10:30:00Z",
    "confidence": 0.92,
    "data": {
      "active_risks": 8,
      "high_risk_count": 2,
      "risk_score": 65.5
    }
  },
  "shocks": {
    "source": "Market Monitor",
    "timestamp": "2024-02-22T10:30:00Z",
    "confidence": 0.85,
    "data": {
      "market_shocks": 2,
      "severity": "medium",
      "affected_markets": ["EU", "Asia"]
    }
  },
  "leads": {
    "source": "Lead Engine",
    "timestamp": "2024-02-22T10:30:00Z",
    "confidence": 0.90,
    "data": {
      "new_leads": 25,
      "qualified_leads": 8,
      "conversion_potential": 32.5
    }
  }
}
```

### 📊 Main Dashboard

#### Get Pipeline Summary
```http
GET /dashboard/pipeline-summary
Authorization: Bearer <token>
```

#### Get Margin Overview
```http
GET /dashboard/margin-overview
Authorization: Bearer <token>
```

#### Get Cash Flow Trends
```http
GET /dashboard/cash-flow-trends?period=6m
Authorization: Bearer <token>
```

### 🤝 Deals & Operations

#### List Deals
```http
GET /deals?status=active&stage=negotiating
Authorization: Bearer <token>
```

#### Create Deal
```http
POST /deals
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Soybean Export Deal",
  "description": "Large soybean export to China",
  "total_value": 500000,
  "currency": "USD",
  "buyer_company_id": "uuid",
  "seller_company_id": "uuid",
  "product_type": "soybeans",
  "quantity": 1000,
  "unit": "tons",
  "expected_delivery_date": "2024-03-15"
}
```

#### Get Deal Details
```http
GET /deals/{deal_id}
Authorization: Bearer <token>
```

#### Update Deal
```http
PUT /deals/{deal_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "closed_won",
  "actual_margin_pct": 12.5,
  "closed_date": "2024-02-22"
}
```

#### Add Deal Milestone
```http
POST /deals/{deal_id}/milestones
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Contract Signed",
  "description": "Purchase contract signed by both parties",
  "due_date": "2024-02-25",
  "assigned_to": "user_uuid"
}
```

### 💳 Wallet & Billing

#### Get Wallet Balance
```http
GET /billing/wallet/balance
Authorization: Bearer <token>
```

#### Top Up Wallet
```http
POST /billing/wallet/top-up
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 10000,
  "currency": "USD",
  "payment_method_id": "pm_1234567890"
}
```

#### Get Subscription Status
```http
GET /billing/subscription
Authorization: Bearer <token>
```

#### Upgrade Subscription
```http
POST /billing/subscription/upgrade
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_plan": "enterprise",
  "billing_cycle": "annual"
}
```

#### Get Transaction History
```http
GET /billing/transactions?limit=50&offset=0
Authorization: Bearer <token>
```

### ⚙️ Advanced Settings

#### Get Custom Pipelines
```http
GET /settings/pipelines
Authorization: Bearer <token>
```

#### Create Custom Pipeline
```http
POST /settings/pipelines
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Export Pipeline",
  "description": "Custom pipeline for export deals",
  "stages": [
    {"name": "lead", "order": 1},
    {"name": "qualified", "order": 2},
    {"name": "negotiating", "order": 3},
    {"name": "closed", "order": 4}
  ]
}
```

#### Get Scoring Profiles
```http
GET /settings/scoring-profiles
Authorization: Bearer <token>
```

#### Create Alert Rule
```http
POST /settings/alert-rules
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High Value Deal Alert",
  "description": "Alert for deals over $100k",
  "conditions": {
    "total_value": {"operator": ">", "value": 100000}
  },
  "actions": [
    {"type": "notification", "recipients": ["owner", "manager"]}
  ]
}
```

## 🛠️ Toolbox APIs

### 📊 Trade Data

#### Query Trade Data
```http
POST /toolbox/trade-data/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "reporter": "USA",
  "partner": "CHN",
  "product_code": "1201",
  "year": 2023,
  "period": "annual"
}
```

#### Get HS Code Information
```http
GET /toolbox/trade-data/hs-code/1201
Authorization: Bearer <token>
```

#### Analyze Trade Trends
```http
POST /toolbox/trade-data/trends
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_code": "1201",
  "exporter": "USA",
  "importer": "CHN",
  "period": "5y"
}
```

#### Get Export Opportunities
```http
POST /toolbox/trade-data/opportunities
Authorization: Bearer <token>
Content-Type: application/json

{
  "exporter": "USA",
  "product_categories": ["agriculture", "machinery"],
  "target_markets": ["CHN", "JPN", "DEU"]
}
```

#### Get Popular Routes
```http
GET /toolbox/trade-data/popular-routes?limit=20
Authorization: Bearer <token>
```

### 🚢 Freight Rates

#### Get Freight Rates
```http
POST /toolbox/freight-rates/rates
Authorization: Bearer <token>
Content-Type: application/json

{
  "origin_port": "USLAX",
  "destination_port": "CNSHA",
  "container_type": "40HC",
  "service_type": "FCL"
}
```

#### Optimize Route
```http
POST /toolbox/freight-rates/optimize
Authorization: Bearer <token>
Content-Type: application/json

{
  "origin_port": "USLAX",
  "destination_port": "CNSHA",
  "container_type": "40HC",
  "constraints": {
    "max_cost": 5000,
    "max_transit_time": 30
  }
}
```

#### Get Port Information
```http
GET /toolbox/freight-rates/ports/USLAX
Authorization: Bearer <token>
```

#### Get Popular Freight Routes
```http
GET /toolbox/freight-rates/popular-routes
Authorization: Bearer <token>
```

### 💱 FX Center

#### Get FX Rate
```http
POST /toolbox/fx-center/rate
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_currency": "USD",
  "quote_currency": "EUR",
  "amount": 10000
}
```

#### Get Multiple Rates
```http
POST /toolbox/fx-center/multiple-rates
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_currency": "USD",
  "quote_currencies": ["EUR", "GBP", "JPY", "CNY"]
}
```

#### Analyze Volatility
```http
GET /toolbox/fx-center/volatility/USD/EUR?period_days=30
Authorization: Bearer <token>
```

#### Get Hedge Recommendations
```http
POST /toolbox/fx-center/hedge-recommendations
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_currency": "USD",
  "quote_currency": "EUR",
  "exposure_amount": 100000,
  "timeframe_months": 3
}
```

#### Get Historical Rates
```http
POST /toolbox/fx-center/historical-rates
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_currency": "USD",
  "quote_currency": "EUR",
  "start_date": "2024-01-01",
  "end_date": "2024-02-22"
}
```

### 📈 BI Analytics

#### Calculate Metric
```http
POST /toolbox/bi-analytics/metrics/total_deals_value
Authorization: Bearer <token>
Content-Type: application/json

{
  "filters": {
    "status": ["closed_won"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-02-22"
    }
  }
}
```

#### Generate Dashboard
```http
POST /toolbox/bi-analytics/dashboard
Authorization: Bearer <token>
Content-Type: application/json

{
  "dashboard_type": "executive_overview",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-02-22"
  }
}
```

#### Generate Report
```http
POST /toolbox/bi-analytics/report
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "monthly",
  "format_type": "json",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

#### Get Available Metrics
```http
GET /toolbox/bi-analytics/metrics
Authorization: Bearer <token>
```

#### Get Dashboard Templates
```http
GET /toolbox/bi-analytics/dashboard-templates
Authorization: Bearer <token>
```

## 🤝 CRM APIs

### 👁️ Vision/Voice Processing

#### Process Document
```http
POST /crm/vision-voice/process-document
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>
document_type_hint: business_card
```

#### Process Audio
```http
POST /crm/vision-voice/process-audio
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <audio_file>
language_hint: en
```

#### Create CRM Record from Document
```http
POST /crm/vision-voice/create-crm-record
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>
document_type_hint: business_card
```

#### Get Processing History
```http
GET /crm/vision-voice/processing-history?limit=20
Authorization: Bearer <token>
```

#### Get Supported Document Types
```http
GET /crm/vision-voice/document-types
Authorization: Bearer <token>
```

### 🧪 Campaign A/B Testing

#### Create A/B Test
```http
POST /crm/campaign-ab/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "campaign_name": "Welcome Email Test",
  "variant_a": {
    "name": "Control",
    "subject": "Welcome to Artin Smart Trade",
    "content": "Original content..."
  },
  "variant_b": {
    "name": "Test",
    "subject": "Transform Your Trade Operations",
    "content": "Test content..."
  },
  "test_duration_days": 14,
  "target_audience": {
    "segment": "new_users"
  }
}
```

#### Start A/B Test
```http
POST /crm/campaign-ab/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "test_id": "ab_test_20240222_143022",
  "sample_size": 2000
}
```

#### Record Campaign Event
```http
POST /crm/campaign-ab/record-event
Authorization: Bearer <token>
Content-Type: application/json

{
  "test_id": "ab_test_20240222_143022",
  "variant_id": "ab_test_20240222_143022_A",
  "event_type": "opened",
  "contact_id": "contact_uuid"
}
```

#### Get Test Results
```http
GET /crm/campaign-ab/results/{test_id}
Authorization: Bearer <token>
```

#### Get Campaign Recommendations
```http
GET /crm/campaign-ab/recommendations/{test_id}
Authorization: Bearer <token>
```

#### Get Test Templates
```http
GET /crm/campaign-ab/test-templates
Authorization: Bearer <token>
```

### 🔄 Pipeline Automation

#### Create Automation Rule
```http
POST /crm/pipeline-automation/rules
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High Value Deal Alert",
  "description": "Alert when deal value exceeds $100k",
  "trigger_type": "value_threshold",
  "trigger_conditions": {
    "value_threshold": 100000,
    "conditions": [
      {"field": "total_value", "operator": ">", "value": 100000}
    ]
  },
  "actions": [
    {
      "type": "notification",
      "parameters": {
        "message": "High value deal detected: {deal_title}",
        "recipients": ["deal_owner", "sales_manager"]
      }
    }
  ],
  "is_active": true,
  "priority": 1
}
```

#### Trigger Automation
```http
POST /crm/pipeline-automation/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "event_type": "stage_change",
  "deal_id": "deal_uuid",
  "data": {
    "from_stage": "qualified",
    "to_stage": "proposal"
  }
}
```

#### Get Automation Rules
```http
GET /crm/pipeline-automation/rules?is_active=true
Authorization: Bearer <token>
```

#### Get Automation History
```http
GET /crm/pipeline-automation/history?limit=50
Authorization: Bearer <token>
```

#### Get Trigger Types
```http
GET /crm/pipeline-automation/trigger-types
Authorization: Bearer <token>
```

#### Get Action Types
```http
GET /crm/pipeline-automation/action-types
Authorization: Bearer <token>
```

## 📊 Data Models

### 🏢 Tenant Model
```json
{
  "id": "uuid",
  "name": "Acme Trading Corp",
  "domain": "acme-trading.com",
  "plan": "enterprise",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-02-22T10:30:00Z"
}
```

### 👤 User Model
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "trade_manager",
  "tenant_id": "uuid",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-02-22T09:15:00Z"
}
```

### 🤝 Deal Model
```json
{
  "id": "uuid",
  "title": "Soybean Export Deal",
  "description": "Large soybean export to China",
  "total_value": 500000,
  "currency": "USD",
  "status": "negotiating",
  "buyer_company_id": "uuid",
  "seller_company_id": "uuid",
  "assigned_to": "uuid",
  "created_at": "2024-02-01T00:00:00Z",
  "updated_at": "2024-02-22T10:30:00Z"
}
```

### 💰 Wallet Model
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "balance": 250000,
  "currency": "USD",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-02-22T10:30:00Z"
}
```

## 🔧 Error Handling

### 📋 Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2024-02-22T10:30:00Z",
    "request_id": "req_1234567890"
  }
}
```

### 🚨 Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### 🔍 Validation Errors
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "Invalid email format"
        },
        {
          "field": "total_value",
          "message": "Value must be greater than 0"
        }
      ]
    }
  }
}
```

## 📈 Rate Limiting

### 🚦 Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1645545600
```

### 📊 Rate Limits by Plan

| Plan | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|-------------|
| Starter | 100 | 5,000 | 50,000 |
| Professional | 500 | 25,000 | 250,000 |
| Enterprise | 2,000 | 100,000 | 1,000,000 |

### 🔄 Rate Limit Response
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": "1 hour",
      "retry_after": 3600
    }
  }
}
```

## 🧪 Testing

### 🧪 API Testing Examples

#### Using curl
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Get deals
curl -X GET http://localhost:8000/deals \
  -H "Authorization: Bearer <token>"

# Create deal
curl -X POST http://localhost:8000/deals \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Deal", "total_value": 100000}'
```

#### Using Python
```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = response.json()['access_token']

# Get deals
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/deals', headers=headers)
deals = response.json()
```

#### Using JavaScript
```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const { access_token } = await loginResponse.json();

// Get deals
const dealsResponse = await fetch('http://localhost:8000/deals', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const deals = await dealsResponse.json();
```

### 🧪 Postman Collection

A comprehensive Postman collection is available at:
`/docs/postman-collection.json`

### 🧪 OpenAPI Specification

The complete OpenAPI specification is available at:
`/openapi.json`

---

## 🎯 API Quick Start

1. **Get your API keys** from the dashboard
2. **Authenticate** using the login endpoint
3. **Use the token** for all subsequent requests
4. **Monitor rate limits** using response headers
5. **Handle errors** gracefully using the standard error format

## 📞 API Support

- **Documentation**: [docs.artin-smart-trade.com](https://docs.artin-smart-trade.com)
- **API Status**: [status.artin-smart-trade.com](https://status.artin-smart-trade.com)
- **Support**: api-support@artin-smart-trade.com
- **Issues**: [GitHub Issues](https://github.com/your-org/artin-smart-trade/issues)

---

*Built with ❤️ by the Artin Smart Trade Team*
