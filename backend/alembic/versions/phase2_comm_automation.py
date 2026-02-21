"""Phase 2: comm_* tables + automation tables + RLS policies

Revision ID: phase2_comm_automation
Revises: phase1_rbac_rls
Create Date: 2026-02-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'phase2_comm_automation'
down_revision = 'phase1_rbac_rls'
branch_labels = None
depends_on = None

NEW_RLS_TABLES = [
    "comm_channels",
    "comm_identities",
    "comm_conversations",
    "comm_messages",
    "comm_message_events",
    "automations",
    "automation_runs",
    "message_templates",
]


def upgrade():
    # ── 1. Enum types ────────────────────────────────────────────────────────
    types = [
        ('comm_channel_type', "('whatsapp','email','telegram')"),
        ('comm_provider_type', "('waha','smtp','imap')"),
        ('comm_identity_type', "('phone','email','handle')"),
        ('comm_conversation_status', "('open','pending','closed')"),
        ('comm_message_direction', "('inbound','outbound')"),
        ('comm_message_status', "('queued','sent','delivered','read','failed')"),
        ('comm_message_event_type', "('status','webhook','retry','dlq')"),
        ('automation_trigger_type', "('no_reply','stage_changed','new_lead')"),
        ('automation_run_status', "('scheduled','executed','skipped','failed')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)

    # ── 2. comm_channels ─────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE comm_channels (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id    UUID NOT NULL,
        type         comm_channel_type NOT NULL,
        provider     comm_provider_type NOT NULL,
        display_name TEXT NOT NULL,
        config       JSONB NOT NULL DEFAULT '{}',
        is_active    BOOLEAN NOT NULL DEFAULT true,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_comm_channels_tenant ON comm_channels(tenant_id);
    """)

    # ── 3. comm_identities ───────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE comm_identities (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id      UUID NOT NULL,
        channel_id     UUID NOT NULL REFERENCES comm_channels(id) ON DELETE CASCADE,
        identity_type  comm_identity_type NOT NULL,
        identity_value VARCHAR(200) NOT NULL,
        company_id     UUID REFERENCES crm_companies(id) ON DELETE SET NULL,
        contact_id     UUID REFERENCES crm_contacts(id) ON DELETE SET NULL,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_comm_identity UNIQUE (tenant_id, channel_id, identity_type, identity_value)
    );
    CREATE INDEX ix_comm_identities_tenant ON comm_identities(tenant_id);
    CREATE INDEX ix_comm_identities_value  ON comm_identities(identity_value);
    """)

    # ── 4. comm_conversations ────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE comm_conversations (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID NOT NULL,
        channel_id      UUID NOT NULL REFERENCES comm_channels(id) ON DELETE CASCADE,
        identity_id     UUID NOT NULL REFERENCES comm_identities(id) ON DELETE CASCADE,
        subject         TEXT,
        status          comm_conversation_status NOT NULL DEFAULT 'open',
        last_message_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_comm_conversation UNIQUE (tenant_id, channel_id, identity_id)
    );
    CREATE INDEX ix_comm_convs_tenant_status ON comm_conversations(tenant_id, status);
    CREATE INDEX ix_comm_convs_last_msg       ON comm_conversations(tenant_id, last_message_at DESC);
    """)

    # ── 5. comm_messages ─────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE comm_messages (
        id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id                UUID NOT NULL,
        conversation_id          UUID NOT NULL REFERENCES comm_conversations(id) ON DELETE CASCADE,
        direction                comm_message_direction NOT NULL,
        status                   comm_message_status NOT NULL DEFAULT 'queued',
        provider_message_id      VARCHAR(255),
        sender_identity_value    VARCHAR(200),
        recipient_identity_value VARCHAR(200),
        body_text                TEXT,
        media                    JSONB,
        raw_payload              JSONB,
        error                    JSONB,
        created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_comm_messages_conv_date   ON comm_messages(tenant_id, conversation_id, created_at DESC);
    CREATE INDEX ix_comm_messages_provider_id ON comm_messages(tenant_id, provider_message_id);
    """)

    # ── 6. comm_message_events ───────────────────────────────────────────────
    op.execute("""
    CREATE TABLE comm_message_events (
        id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id  UUID NOT NULL,
        message_id UUID NOT NULL REFERENCES comm_messages(id) ON DELETE CASCADE,
        event_type comm_message_event_type NOT NULL,
        event_data JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_comm_msg_events_msg   ON comm_message_events(message_id);
    CREATE INDEX ix_comm_msg_events_tenant ON comm_message_events(tenant_id, created_at DESC);
    """)

    # ── 7. automations ───────────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE automations (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id    UUID NOT NULL,
        name         VARCHAR(255) NOT NULL,
        is_active    BOOLEAN NOT NULL DEFAULT true,
        trigger_type automation_trigger_type NOT NULL,
        conditions   JSONB NOT NULL DEFAULT '{}',
        actions      JSONB NOT NULL DEFAULT '{}',
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_automations_tenant ON automations(tenant_id);
    """)

    # ── 8. automation_runs ───────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE automation_runs (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID NOT NULL,
        automation_id   UUID NOT NULL REFERENCES automations(id) ON DELETE CASCADE,
        entity_type     VARCHAR(50) NOT NULL,
        entity_id       UUID NOT NULL,
        status          automation_run_status NOT NULL DEFAULT 'scheduled',
        scheduled_for   TIMESTAMPTZ NOT NULL,
        executed_at     TIMESTAMPTZ,
        idempotency_key VARCHAR(255) NOT NULL,
        error           JSONB,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_automation_run_idem UNIQUE (tenant_id, idempotency_key)
    );
    CREATE INDEX ix_automation_runs_tenant_status  ON automation_runs(tenant_id, status);
    CREATE INDEX ix_automation_runs_scheduled       ON automation_runs(scheduled_for) WHERE status = 'scheduled';
    """)

    # ── 9. message_templates ─────────────────────────────────────────────────
    op.execute("""
    CREATE TABLE message_templates (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id    UUID NOT NULL,
        name         VARCHAR(255) NOT NULL,
        channel_type VARCHAR(50) NOT NULL DEFAULT 'whatsapp',
        language     VARCHAR(10) NOT NULL DEFAULT 'en',
        body         TEXT NOT NULL,
        variables    JSONB NOT NULL DEFAULT '[]',
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_message_templates_tenant ON message_templates(tenant_id);
    """)

    # ── 10. RLS for all new tables ───────────────────────────────────────────
    for table in NEW_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id::text = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true));
        """)

    # ── 11. Seed inbox.* permissions ─────────────────────────────────────────
    for perm in ["inbox.read", "inbox.write", "inbox.admin", "automations.read", "automations.write"]:
        op.execute(f"""
            INSERT INTO permissions (id, name)
            VALUES (gen_random_uuid(), '{perm}')
            ON CONFLICT (name) DO NOTHING;
        """)


def downgrade():
    for table in reversed(NEW_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP TABLE IF EXISTS message_templates CASCADE;")
    op.execute("DROP TABLE IF EXISTS automation_runs CASCADE;")
    op.execute("DROP TABLE IF EXISTS automations CASCADE;")
    op.execute("DROP TABLE IF EXISTS comm_message_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS comm_messages CASCADE;")
    op.execute("DROP TABLE IF EXISTS comm_conversations CASCADE;")
    op.execute("DROP TABLE IF EXISTS comm_identities CASCADE;")
    op.execute("DROP TABLE IF EXISTS comm_channels CASCADE;")

    op.execute("DROP TYPE IF EXISTS automation_run_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS automation_trigger_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_message_event_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_message_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_message_direction CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_conversation_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_identity_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_provider_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS comm_channel_type CASCADE;")
