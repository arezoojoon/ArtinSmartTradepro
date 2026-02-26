"""Add Smart Logistics tables: shipments, packages, events, carriers

Creates the core logistics tracking infrastructure for AI-powered
shipment management with Vision document extraction.
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_logistics_tables'
down_revision = 'fix_engine_type_enum_to_text'
branch_labels = None
depends_on = None


def upgrade():
    # Carriers
    op.execute("""
    CREATE TABLE IF NOT EXISTS logistics_carriers (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID NOT NULL REFERENCES tenants(id),
        name            TEXT NOT NULL,
        contact_name    TEXT,
        contact_phone   TEXT,
        contact_email   TEXT,
        api_endpoint    TEXT,
        capabilities    JSONB DEFAULT '{}',
        is_active       BOOLEAN DEFAULT true,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at      TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_carriers_tenant ON logistics_carriers (tenant_id);
    """)

    # Shipments
    op.execute("""
    CREATE TABLE IF NOT EXISTS logistics_shipments (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id           UUID NOT NULL REFERENCES tenants(id),
        shipment_number     TEXT NOT NULL,
        order_id            TEXT,
        origin              JSONB DEFAULT '{}',
        destination         JSONB DEFAULT '{}',
        status              TEXT NOT NULL DEFAULT 'created',
        carrier_id          UUID REFERENCES logistics_carriers(id),
        goods_description   TEXT,
        total_weight_kg     DOUBLE PRECISION,
        total_packages      INTEGER DEFAULT 0,
        incoterms           TEXT,
        estimated_delivery  TIMESTAMPTZ,
        actual_delivery     TIMESTAMPTZ,
        pickup_at           TIMESTAMPTZ,
        pod_image_url       TEXT,
        pod_signature_url   TEXT,
        pod_recipient_name  TEXT,
        ai_extracted        BOOLEAN DEFAULT false,
        ai_confidence       DOUBLE PRECISION,
        source_document_url TEXT,
        customer_phone      TEXT,
        customer_name       TEXT,
        notification_sent   BOOLEAN DEFAULT false,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at          TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_shipments_tenant ON logistics_shipments (tenant_id);
    CREATE INDEX IF NOT EXISTS idx_shipments_status ON logistics_shipments (status);
    CREATE INDEX IF NOT EXISTS idx_shipments_number ON logistics_shipments (shipment_number);
    """)

    # Packages
    op.execute("""
    CREATE TABLE IF NOT EXISTS logistics_packages (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        shipment_id     UUID NOT NULL REFERENCES logistics_shipments(id) ON DELETE CASCADE,
        barcode         TEXT,
        weight_kg       DOUBLE PRECISION,
        dimensions      TEXT,
        contents        TEXT,
        metadata_json   JSONB DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_packages_shipment ON logistics_packages (shipment_id);
    """)

    # Events / Timeline
    op.execute("""
    CREATE TABLE IF NOT EXISTS logistics_events (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        shipment_id     UUID NOT NULL REFERENCES logistics_shipments(id) ON DELETE CASCADE,
        package_id      UUID REFERENCES logistics_packages(id),
        event_type      TEXT NOT NULL,
        actor           TEXT,
        payload         JSONB DEFAULT '{}',
        latitude        DOUBLE PRECISION,
        longitude       DOUBLE PRECISION,
        location_name   TEXT,
        speed_kmh       DOUBLE PRECISION,
        eta             TIMESTAMPTZ,
        notes           TEXT,
        timestamp       TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_events_shipment ON logistics_events (shipment_id);
    CREATE INDEX IF NOT EXISTS idx_events_type ON logistics_events (event_type);
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON logistics_events (timestamp);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS logistics_events CASCADE")
    op.execute("DROP TABLE IF EXISTS logistics_packages CASCADE")
    op.execute("DROP TABLE IF EXISTS logistics_shipments CASCADE")
    op.execute("DROP TABLE IF EXISTS logistics_carriers CASCADE")
