"""Fix brain_engine_runs schema to match SQLAlchemy model

The phase5 migration created brain_engine_runs with columns:
  id, tenant_id, engine_type, input_payload, output_payload, explainability, status, error, created_at

But the SQLAlchemy model (app.models.brain.BrainEngineRun) expects:
  id, tenant_id, engine_type, model_version, run_status, input_parameters, results,
  confidence_score, execution_time_ms, started_at, completed_at, error_message,
  retry_count, created_at, updated_at

This migration adds the missing columns and copies data from old → new where applicable.
Old columns are kept (not dropped) for safety.
"""
from alembic import op
import sqlalchemy as sa

revision = 'fix_brain_engine_runs_schema'
down_revision = 'add_followup_message_text'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns that the SQLAlchemy model expects
    op.execute("""
        -- model_version (new)
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS model_version TEXT;

        -- run_status (maps from old 'status')
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS run_status VARCHAR DEFAULT 'pending';

        -- input_parameters (maps from old 'input_payload')
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS input_parameters JSONB;

        -- results (maps from old 'output_payload')
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS results JSONB;

        -- confidence_score
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION;

        -- execution_time_ms
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS execution_time_ms INTEGER;

        -- started_at (maps from old 'created_at' as a fallback)
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ DEFAULT now();

        -- completed_at
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

        -- error_message (maps from old 'error')
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS error_message TEXT;

        -- retry_count
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

        -- updated_at
        ALTER TABLE brain_engine_runs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;
    """)

    # Copy data from old columns to new columns for existing rows
    op.execute("""
        UPDATE brain_engine_runs
        SET
            run_status       = COALESCE(run_status, status::text),
            input_parameters = COALESCE(input_parameters, input_payload),
            results          = COALESCE(results, output_payload),
            error_message    = COALESCE(error_message, error::text),
            started_at       = COALESCE(started_at, created_at)
        WHERE run_status IS NULL OR input_parameters IS NULL OR results IS NULL;
    """)


def downgrade():
    # Remove the columns we added (keep old columns intact)
    cols = [
        'model_version', 'run_status', 'input_parameters', 'results',
        'confidence_score', 'execution_time_ms', 'started_at', 'completed_at',
        'error_message', 'retry_count', 'updated_at',
    ]
    for col in cols:
        op.execute(f"ALTER TABLE brain_engine_runs DROP COLUMN IF EXISTS {col}")
