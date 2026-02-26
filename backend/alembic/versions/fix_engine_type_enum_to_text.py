"""Fix brain_engine_runs.engine_type from enum to TEXT

The column was created as PostgreSQL enum type 'brain_engine_type'
but the SQLAlchemy model declares it as String (VARCHAR/TEXT).
PostgreSQL cannot compare an enum to a varchar directly, causing:
  operator does not exist: brain_engine_type = character varying

Also fix brain_engine_runs.status (enum brain_run_status) for consistency.
"""
from alembic import op

revision = 'fix_engine_type_enum_to_text'
down_revision = 'fix_brain_engine_runs_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Convert engine_type from enum to TEXT
    op.execute("""
        ALTER TABLE brain_engine_runs
            ALTER COLUMN engine_type TYPE TEXT USING engine_type::text;
    """)
    # Convert old status column from enum to TEXT (if it still exists)
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'brain_engine_runs' AND column_name = 'status'
            ) THEN
                ALTER TABLE brain_engine_runs
                    ALTER COLUMN status TYPE TEXT USING status::text;
            END IF;
        END $$;
    """)


def downgrade():
    # Best-effort: convert back to enum (may fail if new values were inserted)
    op.execute("""
        ALTER TABLE brain_engine_runs
            ALTER COLUMN engine_type TYPE brain_engine_type USING engine_type::brain_engine_type;
    """)
