"""Fix hunter_results and hunter_runs created_at default and NOT NULL

Revision ID: fix_hunter_timestamps
Revises: add_tenantmemberships_timestamps
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_hunter_timestamps'
down_revision = 'cfacfe91159d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- hunter_results.created_at ---
    op.execute("""
        ALTER TABLE public.hunter_results
          ALTER COLUMN created_at SET DEFAULT now();
    """)
    op.execute("""
        UPDATE public.hunter_results
        SET created_at = COALESCE(created_at, updated_at, now())
        WHERE created_at IS NULL;
    """)
    op.execute("""
        ALTER TABLE public.hunter_results
          ALTER COLUMN created_at SET NOT NULL;
    """)

    # --- hunter_results.updated_at (add if not exists) ---
    op.execute("""
        ALTER TABLE public.hunter_results
          ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT now();
    """)

    # --- hunter_runs.created_at ---
    op.execute("""
        ALTER TABLE public.hunter_runs
          ALTER COLUMN created_at SET DEFAULT now();
    """)
    op.execute("""
        UPDATE public.hunter_runs
        SET created_at = COALESCE(created_at, now())
        WHERE created_at IS NULL;
    """)
    op.execute("""
        ALTER TABLE public.hunter_runs
          ALTER COLUMN created_at SET NOT NULL;
    """)

    # --- trade_signals.created_at ---
    op.execute("""
        ALTER TABLE public.trade_signals
          ALTER COLUMN created_at SET DEFAULT now();
    """)
    op.execute("""
        UPDATE public.trade_signals
        SET created_at = COALESCE(created_at, now())
        WHERE created_at IS NULL;
    """)
    op.execute("""
        ALTER TABLE public.trade_signals
          ALTER COLUMN created_at SET NOT NULL;
    """)


def downgrade() -> None:
    # Revert to nullable + no default
    for table in ['hunter_results', 'hunter_runs', 'trade_signals']:
        op.execute(f"""
            ALTER TABLE public.{table}
              ALTER COLUMN created_at DROP NOT NULL;
        """)
        op.execute(f"""
            ALTER TABLE public.{table}
              ALTER COLUMN created_at DROP DEFAULT;
        """)
    op.drop_column('hunter_results', 'updated_at')
