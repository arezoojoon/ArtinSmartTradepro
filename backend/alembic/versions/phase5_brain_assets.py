"""Phase 5 Brain Asset Database Schema
Asset databases for arbitrage history, supplier reliability, buyer payment behavior, and seasonality matrix
"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers
revision = 'phase5_brain_assets'
down_revision = 'phase4_hunter_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Create enums
    types = [
        ('arbitrage_outcome', "('won','lost','no_go','unknown')"),
        ('brain_engine_type', "('arbitrage','risk','demand','cultural')"),
        ('brain_run_status', "('success','insufficient_data','failed')"),
    ]
    for type_name, values in types:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                    CREATE TYPE {type_name} AS ENUM {values};
                END IF;
            END $$;
        """)
    
    # Create asset_arbitrage_history table
    op.create_table('asset_arbitrage_history',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('product_key', sa.Text(), nullable=False),
        sa.Column('buy_market', sa.Text(), nullable=False),
        sa.Column('sell_market', sa.Text(), nullable=False),
        sa.Column('incoterms', sa.Text(), nullable=False),
        sa.Column('buy_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('buy_currency', sa.Text(), nullable=False),
        sa.Column('sell_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('sell_currency', sa.Text(), nullable=False),
        sa.Column('freight_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('fx_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('estimated_margin_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('realized_margin_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('outcome', sa.Enum(arbitrage_outcome, name='arbitrage_outcome'), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('data_used', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for asset_arbitrage_history
    op.create_index('idx_arbitrage_tenant_product', 'asset_arbitrage_history', ['tenant_id', 'product_key'])
    op.create_index('idx_arbitrage_tenant_markets', 'asset_arbitrage_history', ['tenant_id', 'buy_market', 'sell_market'])
    op.create_index('idx_arbitrage_created_at', 'asset_arbitrage_history', ['created_at'])
    
    # Create asset_supplier_reliability table
    op.create_table('asset_supplier_reliability',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_name', sa.Text(), nullable=False),
        sa.Column('supplier_country', sa.Text(), nullable=False),
        sa.Column('identifiers', sa.JSON(), nullable=True),
        sa.Column('on_time_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('defect_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('dispute_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_lead_time_days', sa.Integer(), nullable=True),
        sa.Column('reliability_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for asset_supplier_reliability
    op.create_index('idx_supplier_tenant_country', 'asset_supplier_reliability', ['tenant_id', 'supplier_country'])
    op.create_index('idx_supplier_tenant_name', 'asset_supplier_reliability', ['tenant_id', 'supplier_name'])
    op.create_index('idx_supplier_reliability_score', 'asset_supplier_reliability', ['reliability_score'])
    
    # Create asset_buyer_payment_behavior table
    op.create_table('asset_buyer_payment_behavior',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('buyer_country', sa.Text(), nullable=False),
        sa.Column('buyer_name', sa.Text(), nullable=True),
        sa.Column('segment', sa.Text(), nullable=True),
        sa.Column('avg_payment_delay_days', sa.Integer(), nullable=True),
        sa.Column('default_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('preferred_terms', sa.Text(), nullable=True),
        sa.Column('payment_risk_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for asset_buyer_payment_behavior
    op.create_index('idx_buyer_tenant_country', 'asset_buyer_payment_behavior', ['tenant_id', 'buyer_country'])
    op.create_index('idx_buyer_tenant_segment', 'asset_buyer_payment_behavior', ['tenant_id', 'segment'])
    op.create_index('idx_buyer_risk_score', 'asset_buyer_payment_behavior', ['payment_risk_score'])
    
    # Create asset_seasonality_matrix table
    op.create_table('asset_seasonality_matrix',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('product_key', sa.Text(), nullable=False),
        sa.Column('country', sa.Text(), nullable=False),
        sa.Column('season_key', sa.Text(), nullable=False),
        sa.Column('demand_index', sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column('price_index', sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column('volatility_index', sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column('data_used', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Unique constraint for seasonality matrix
    op.create_unique_constraint('uq_seasonality_matrix', 'asset_seasonality_matrix', 
                              ['tenant_id', 'product_key', 'country', 'season_key'])
    
    # Indexes for asset_seasonality_matrix
    op.create_index('idx_seasonality_tenant_product', 'asset_seasonality_matrix', ['tenant_id', 'product_key'])
    op.create_index('idx_seasonality_tenant_country', 'asset_seasonality_matrix', ['tenant_id', 'country'])
    op.create_index('idx_seasonality_season', 'asset_seasonality_matrix', ['season_key'])
    
    # Create brain_engine_runs table
    op.create_table('brain_engine_runs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('engine_type', sa.Enum(brain_engine_type, name='brain_engine_type'), nullable=False),
        sa.Column('input_payload', sa.JSON(), nullable=False),
        sa.Column('output_payload', sa.JSON(), nullable=True),
        sa.Column('explainability', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum(brain_run_status, name='brain_run_status'), nullable=False),
        sa.Column('error', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for brain_engine_runs
    op.create_index('idx_brain_runs_tenant_type', 'brain_engine_runs', ['tenant_id', 'engine_type'])
    op.create_index('idx_brain_runs_created_at', 'brain_engine_runs', ['created_at'])
    op.create_index('idx_brain_runs_status', 'brain_engine_runs', ['status'])
    
    # Create brain_data_sources table
    op.create_table('brain_data_sources',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for brain_data_sources
    op.create_index('idx_brain_sources_tenant', 'brain_data_sources', ['tenant_id'])
    op.create_index('idx_brain_sources_active', 'brain_data_sources', ['is_active'])
    
    # Create cultural_profiles table
    op.create_table('cultural_profiles',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('country', sa.Text(), nullable=False),
        sa.Column('negotiation_style', sa.JSON(), nullable=True),
        sa.Column('do_dont', sa.JSON(), nullable=True),
        sa.Column('typical_terms', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Indexes for cultural_profiles
    op.create_index('idx_cultural_tenant_country', 'cultural_profiles', ['tenant_id', 'country'])
    op.create_index('idx_cultural_country', 'cultural_profiles', ['country'])
    
    # Create demand_time_series table
    op.create_table('demand_time_series',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('product_key', sa.Text(), nullable=False),
        sa.Column('country', sa.Text(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('demand_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('source_name', sa.Text(), nullable=False),
        sa.Column('data_used', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Unique constraint for demand time series
    op.create_unique_constraint('uq_demand_time_series', 'demand_time_series', 
                              ['tenant_id', 'product_key', 'country', 'date'])
    
    # Indexes for demand_time_series
    op.create_index('idx_demand_tenant_product', 'demand_time_series', ['tenant_id', 'product_key'])
    op.create_index('idx_demand_tenant_country', 'demand_time_series', ['tenant_id', 'country'])
    op.create_index('idx_demand_date', 'demand_time_series', ['date'])
    
    # Enable RLS on all tables
    for table in ['asset_arbitrage_history', 'asset_supplier_reliability', 'asset_buyer_payment_behavior', 
                   'asset_seasonality_matrix', 'brain_engine_runs', 'brain_data_sources', 
                   'cultural_profiles', 'demand_time_series']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies
    # Asset tables - tenant isolation
    for table in ['asset_arbitrage_history', 'asset_supplier_reliability', 'asset_buyer_payment_behavior', 
                   'asset_seasonality_matrix', 'brain_engine_runs', 'brain_data_sources', 
                   'cultural_profiles', 'demand_time_series']:
        op.execute(f"""
        CREATE POLICY tenant_isolation_{table} ON {table}
        FOR ALL TO authenticated_users
        USING (tenant_id = app.current_tenant_id())
        WITH CHECK (tenant_id = app.current_tenant_id())
        """)
    
    # Insert default brain data sources
    op.execute("""
    INSERT INTO brain_data_sources (tenant_id, name, type, is_active, meta)
    SELECT 
        t.id,
        'manual',
        'manual_input',
        true,
        '{"description": "Manually entered data"}'::jsonb
    FROM tenants t
    WHERE t.id IS NOT NULL
    ON CONFLICT (tenant_id, name) DO NOTHING
    """)
    
    op.execute("""
    INSERT INTO brain_data_sources (tenant_id, name, type, is_active, meta)
    SELECT 
        t.id,
        'csv_import',
        'csv_upload',
        true,
        '{"description": "Data imported from CSV files"}'::jsonb
    FROM tenants t
    WHERE t.id IS NOT NULL
    ON CONFLICT (tenant_id, name) DO NOTHING
    """)

def downgrade():
    # Drop tables in reverse order
    for table in ['demand_time_series', 'cultural_profiles', 'brain_data_sources', 'brain_engine_runs',
                   'asset_seasonality_matrix', 'asset_buyer_payment_behavior', 'asset_supplier_reliability', 
                   'asset_arbitrage_history']:
        op.drop_table(table)
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS arbitrage_outcome")
    op.execute("DROP TYPE IF EXISTS brain_engine_type")
    op.execute("DROP TYPE IF EXISTS brain_run_status")
