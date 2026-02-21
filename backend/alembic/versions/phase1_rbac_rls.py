"""Phase 1: RBAC tables + RLS policies + seed permissions

Revision ID: phase1_rbac_rls
Revises: 
Create Date: 2026-02-21

This migration:
1. Creates RBAC tables (permissions, roles, rolepermissions, userroles)
2. Enables RLS on all tenant-owned tables
3. Seeds base permissions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = 'phase1_rbac_rls'
down_revision = 'fix_hunter_timestamps'
branch_labels = None
depends_on = None

# Seed permissions
SEED_PERMISSIONS = [
    "crm.read", "crm.write", "crm.admin",
    "users.read", "users.write", "users.manage",
    "roles.read", "roles.write",
    "hunter.read", "hunter.write",
    "brain.read", "brain.write",
    "toolbox.read", "toolbox.write",
    "whatsapp.read", "whatsapp.write",
    "campaigns.read", "campaigns.write",
    "finance.read", "finance.write",
    "billing.read", "billing.manage",
    "settings.read", "settings.write",
    "admin.access",
]

# Tables that should have RLS enabled (tenant-owned)
RLS_TABLES = [
    "tenantmemberships",
    "auditlogs",
    "crmcompanys",    # CRMCompany -> crmcompanys
    "crmcontacts",
    "crmconversations",
    "crmdeals",
    "whatsappmessages",
    "crmcampaigns",
    "crmcampaignsegments",
    "crmcampaignmessages",
    "crmfollowuprules",
    "crmfollowupexecutions",
    "crmrevenueattributions",
    "hunterruns",
    "hunterresults",
    "wallets",
    "wallettransactions",
    "botsessions",
    "botevents",
    "botdeeplinkrefs",
    "aijobs",
    "roles",
    "rolepermissions",
    "userroles",
]


def upgrade():
    # 1. Create RBAC tables (if they don't already exist)
    # permissions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR UNIQUE NOT NULL,
            description VARCHAR,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    # roles table
    op.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR NOT NULL,
            description VARCHAR,
            is_default BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_role_tenant_name UNIQUE (tenant_id, name)
        );
        CREATE INDEX IF NOT EXISTS ix_roles_tenant_id ON roles(tenant_id);
    """)

    # rolepermissions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS rolepermissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
        );
    """)

    # userroles table
    op.execute("""
        CREATE TABLE IF NOT EXISTS userroles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
        );
    """)

    # 2. Seed permissions
    for perm_name in SEED_PERMISSIONS:
        perm_id = str(uuid.uuid4())
        op.execute(f"""
            INSERT INTO permissions (id, name)
            VALUES ('{perm_id}', '{perm_name}')
            ON CONFLICT (name) DO NOTHING;
        """)

    # 3. Enable RLS on tenant-owned tables
    # First, create the GUC setting if not exists
    op.execute("""
        DO $$ BEGIN
            PERFORM set_config('app.tenant_id', '', true);
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END $$;
    """)

    for table in RLS_TABLES:
        # Safe: only enable RLS if the table actually exists
        op.execute(f"""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}') THEN
                    EXECUTE 'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY';
                    EXECUTE 'DROP POLICY IF EXISTS tenant_isolation ON {table}';
                    EXECUTE 'CREATE POLICY tenant_isolation ON {table}
                        USING (tenant_id::text = current_setting(''app.tenant_id'', true))
                        WITH CHECK (tenant_id::text = current_setting(''app.tenant_id'', true))';
                END IF;
            END $$;
        """)


def downgrade():
    # Remove RLS policies
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # Drop RBAC tables
    op.execute("DROP TABLE IF EXISTS userroles CASCADE;")
    op.execute("DROP TABLE IF EXISTS rolepermissions CASCADE;")
    op.execute("DROP TABLE IF EXISTS roles CASCADE;")
    op.execute("DROP TABLE IF EXISTS permissions CASCADE;")
