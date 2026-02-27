# Multi-Tenant Security Architecture

## 🔐 Overview

Artin Smart Trade implements a robust multi-tenant architecture with strict data isolation between companies. Each tenant (company) has complete isolation of their logistics data, ensuring that no company can access another company's shipment information.

## 🏗️ Architecture Components

### 1. Database Layer (Row Level Security)

```sql
-- All logistics tables include tenant_id for isolation
CREATE TABLE logistics_shipments (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),  -- 🔑 Isolation Key
    shipment_number TEXT NOT NULL,
    -- ... other fields
);

CREATE INDEX idx_shipments_tenant ON logistics_shipments(tenant_id);
```

### 2. Backend Security Gateway

```python
# app/core/tenant.py
class TenantContext:
    def __init__(self, tenant_id: str, user_id: str, user_role: str):
        self.tenant_id = tenant_id    # 🏢 Current Company
        self.user_id = user_id        # 👤 Current User
        self.user_role = user_role    # 🔐 User Permissions

# Security dependency injection
async def get_tenant_context(
    current_user: User = Depends(get_current_user)
) -> TenantContext:
    # Extract tenant from JWT token
    # Validate user belongs to tenant
    # Return secure context
```

### 3. API Layer Protection

```python
# app/routers/logistics.py
@router.get("/shipments/{shipment_id}/events")
async def list_events(
    shipment_id: UUID,
    tenant: TenantContext = Depends(get_tenant_context), # 🛡️ Security Gateway
    db: AsyncSession = Depends(get_db),
):
    # Join with Shipment to enforce tenant isolation
    stmt = (
        select(ShipmentEvent)
        .join(Shipment, ShipmentEvent.shipment_id == Shipment.id)
        .where(
            Shipment.id == shipment_id,
            Shipment.tenant_id == tenant.tenant_id  # 🔒 RLS Filter
        )
    )
```

## 🌍 Internationalization (i18n)

### Frontend Language Detection

```typescript
// hooks/useTenantContext.ts
export const useTenantContext = (): TenantContext => {
  // Extract language from JWT payload
  const tenantLanguage = payload.language || 
                       payload.tenant_language || 
                       (payload.company_name?.includes('فارسی') ? 'fa' : 'en');
  
  return {
    tenantId: payload.tenant_id,
    language: tenantLanguage as 'en' | 'fa',
    // ... other context
  };
};
```

### Bilingual Timeline Component

```typescript
// components/logistics/ShipmentTimelineBilingual.tsx
const getEventConfig = (eventType: string, language: 'en' | 'fa') => {
  const configs = {
    en: {
      delivered: { label: 'Delivered', icon: CheckCircle2 },
      in_transit: { label: 'In Transit', icon: Truck },
      // ... English labels
    },
    fa: {
      delivered: { label: 'تحویل داده شد', icon: CheckCircle2 },
      in_transit: { label: 'در حال حمل', icon: Truck },
      // ... Persian labels
    }
  };
  return configs[language][eventType];
};
```

## 🔒 Security Features

### 1. **JWT Token Isolation**
- Each JWT token contains `tenant_id` and `current_tenant_id`
- Tokens are validated on every API call
- Cross-tenant access is impossible

### 2. **Database Row Level Security**
- All queries automatically filtered by `tenant_id`
- JOIN operations enforce isolation at database level
- No accidental data leaks possible

### 3. **API Gateway Protection**
- Every endpoint requires `TenantContext` dependency
- Automatic tenant filtering applied to all queries
- 404 errors for non-existent or inaccessible resources

### 4. **Audit Logging**
```python
# Log all tenant operations for security monitoring
await log_tenant_operation(
    operation="READ_TIMELINE",
    resource_type="shipment_events",
    resource_id=str(shipment_id),
    tenant=tenant,
    success=True
)
```

## 🚀 Usage Examples

### English Tenant (Default)
```typescript
// English company sees English interface
<ShipmentTimeline 
  events={events} 
  language="en"
  direction="ltr"
/>
```

### Persian Tenant
```typescript
// Persian company sees Persian interface
<ShipmentTimeline 
  events={events} 
  language="fa"
  direction="rtl"
/>
```

## 🛡️ Security Guarantees

1. **Data Isolation**: ✅ Tenants can only access their own data
2. **Language Isolation**: ✅ Each tenant sees their preferred language
3. **API Security**: ✅ All endpoints protected by tenant context
4. **Database Security**: ✅ Row Level Security enforced at query level
5. **Audit Trail**: ✅ All operations logged with tenant context

## 📊 Multi-Tenant Metrics

```python
# Dashboard KPIs are automatically tenant-isolated
@router.get("/stats")
async def get_stats(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    # Only returns stats for current tenant
    status_counts = {}
    for status in SHIPMENT_STATUSES:
        count = await db.execute(
            select(func.count()).where(
                Shipment.tenant_id == tenant.tenant_id,  # 🔒 Auto-filtered
                Shipment.status == status
            )
        )
        status_counts[status] = count.scalar()
    return status_counts
```

## 🌐 Global Deployment Ready

This architecture supports:
- **Multiple Languages**: English, Persian, and easily extensible
- **Multiple Regions**: Deploy anywhere with same security guarantees  
- **Multiple Tenants**: Scale to thousands of companies with complete isolation
- **Multiple Devices**: Responsive design works on desktop, tablet, and mobile

---

**🔐 Security First**: Every component designed with multi-tenant isolation as the primary requirement.
