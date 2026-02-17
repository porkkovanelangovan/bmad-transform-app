-- ============================================================
-- Business Transformation Architect - PostgreSQL Schema
-- ============================================================
-- Referential Integrity Chain:
--   Initiative -> Product -> Epic -> Feature
-- ============================================================

-- ============================================================
-- Users (Authentication)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Organization Setup
-- ============================================================

CREATE TABLE IF NOT EXISTS organization (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    ticker TEXT,
    industry TEXT NOT NULL,
    sub_industry TEXT,
    market_cap DOUBLE PRECISION,
    country TEXT,
    currency TEXT,
    competitor_1_name TEXT,
    competitor_2_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 1: Business Performance Dashboard
-- ============================================================

CREATE TABLE IF NOT EXISTS business_units (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revenue_splits (
    id SERIAL PRIMARY KEY,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    dimension TEXT NOT NULL CHECK (dimension IN ('product', 'region', 'segment')),
    dimension_value TEXT NOT NULL,
    revenue DOUBLE PRECISION NOT NULL DEFAULT 0,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops_efficiency (
    id SERIAL PRIMARY KEY,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    target_value DOUBLE PRECISION,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    ticker TEXT,
    market_share DOUBLE PRECISION,
    revenue DOUBLE PRECISION,
    profit_margin DOUBLE PRECISION,
    operating_margin DOUBLE PRECISION,
    return_on_equity DOUBLE PRECISION,
    return_on_assets DOUBLE PRECISION,
    pe_ratio DOUBLE PRECISION,
    eps DOUBLE PRECISION,
    market_cap_value DOUBLE PRECISION,
    strengths TEXT,
    weaknesses TEXT,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 2: Value Stream Analysis
-- ============================================================

CREATE TABLE IF NOT EXISTS value_streams (
    id SERIAL PRIMARY KEY,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS value_stream_levers (
    id SERIAL PRIMARY KEY,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    lever_type TEXT NOT NULL CHECK (lever_type IN ('growth', 'efficiency', 'experience', 'effectiveness')),
    opportunity TEXT NOT NULL,
    current_state TEXT,
    target_state TEXT,
    impact_estimate TEXT CHECK (impact_estimate IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS value_stream_steps (
    id SERIAL PRIMARY KEY,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    step_order INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    description TEXT,
    step_type TEXT NOT NULL DEFAULT 'process' CHECK (step_type IN ('trigger', 'process', 'decision', 'delivery')),
    process_time_hours DOUBLE PRECISION DEFAULT 0,
    wait_time_hours DOUBLE PRECISION DEFAULT 0,
    lead_time_hours DOUBLE PRECISION DEFAULT 0,
    resources TEXT,
    is_bottleneck INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS value_stream_metrics (
    id SERIAL PRIMARY KEY,
    value_stream_id INTEGER NOT NULL UNIQUE REFERENCES value_streams(id),
    total_lead_time_hours DOUBLE PRECISION DEFAULT 0,
    total_process_time_hours DOUBLE PRECISION DEFAULT 0,
    total_wait_time_hours DOUBLE PRECISION DEFAULT 0,
    flow_efficiency DOUBLE PRECISION DEFAULT 0,
    bottleneck_step TEXT,
    bottleneck_reason TEXT,
    data_source TEXT DEFAULT 'manual' CHECK (data_source IN ('ai_generated', 'template', 'uploaded', 'manual')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS value_stream_benchmarks (
    id SERIAL PRIMARY KEY,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    competitor_name TEXT NOT NULL,
    total_lead_time_hours DOUBLE PRECISION,
    total_process_time_hours DOUBLE PRECISION,
    flow_efficiency DOUBLE PRECISION,
    bottleneck_step TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 3: SWOT to TOWS Action Engine
-- ============================================================

CREATE TABLE IF NOT EXISTS swot_entries (
    id SERIAL PRIMARY KEY,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    category TEXT NOT NULL CHECK (category IN ('strength', 'weakness', 'opportunity', 'threat')),
    description TEXT NOT NULL,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tows_actions (
    id SERIAL PRIMARY KEY,
    strategy_type TEXT NOT NULL CHECK (strategy_type IN ('SO', 'WO', 'ST', 'WT')),
    swot_entry_1_id INTEGER NOT NULL REFERENCES swot_entries(id),
    swot_entry_2_id INTEGER NOT NULL REFERENCES swot_entries(id),
    action_description TEXT NOT NULL,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 4: Four-Layer Strategy & Strategic OKRs
-- ============================================================

CREATE TABLE IF NOT EXISTS strategy_inputs (
    id SERIAL PRIMARY KEY,
    input_type TEXT NOT NULL CHECK (input_type IN (
        'business_strategy', 'digital_strategy', 'data_strategy', 'gen_ai_strategy',
        'competitor_strategy', 'ongoing_initiatives', 'document_reference'
    )),
    title TEXT,
    content TEXT NOT NULL,
    file_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    layer TEXT NOT NULL CHECK (layer IN ('business', 'digital', 'data', 'gen_ai')),
    name TEXT NOT NULL,
    description TEXT,
    tows_action_id INTEGER REFERENCES tows_actions(id),
    approved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategic_okrs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    objective TEXT NOT NULL,
    time_horizon TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategic_key_results (
    id SERIAL PRIMARY KEY,
    okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value DOUBLE PRECISION DEFAULT 0,
    target_value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 5: Digital Initiatives & RICE Prioritization
-- ============================================================

CREATE TABLE IF NOT EXISTS product_groups (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS digital_products (
    id SERIAL PRIMARY KEY,
    product_group_id INTEGER NOT NULL REFERENCES product_groups(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS initiatives (
    id SERIAL PRIMARY KEY,
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    strategy_id INTEGER REFERENCES strategies(id),
    name TEXT NOT NULL,
    description TEXT,
    -- RICE scoring
    reach INTEGER NOT NULL DEFAULT 1,
    impact DOUBLE PRECISION NOT NULL DEFAULT 1 CHECK (impact IN (0.25, 0.5, 1, 2, 3)),
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1 CHECK (confidence IN (0.5, 0.8, 1.0)),
    effort INTEGER NOT NULL DEFAULT 1,
    rice_score DOUBLE PRECISION GENERATED ALWAYS AS ((reach * impact * confidence * 1.0) / effort) STORED,
    -- Manual override
    rice_override DOUBLE PRECISION,
    rice_override_reason TEXT,
    -- Extended metadata
    value_score INTEGER DEFAULT 3,
    size_score INTEGER DEFAULT 3,
    impacted_segments TEXT,
    dependencies TEXT,
    risks TEXT,
    roadmap_phase TEXT,
    status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'in_progress', 'completed', 'deferred')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 6: Epic & Team Collaboration + Product OKRs
-- ============================================================

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_okrs (
    id SERIAL PRIMARY KEY,
    strategic_okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_key_results (
    id SERIAL PRIMARY KEY,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value DOUBLE PRECISION DEFAULT 0,
    target_value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS epics (
    id SERIAL PRIMARY KEY,
    initiative_id INTEGER NOT NULL REFERENCES initiatives(id),
    team_id INTEGER REFERENCES teams(id),
    product_okr_id INTEGER REFERENCES product_okrs(id),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'backlog' CHECK (status IN ('backlog', 'in_progress', 'done', 'blocked')),
    start_date TEXT,
    target_date TEXT,
    value_score INTEGER DEFAULT 3,
    size_score INTEGER DEFAULT 3,
    effort_score INTEGER DEFAULT 3,
    priority_score DOUBLE PRECISION DEFAULT 0,
    risk_level TEXT DEFAULT 'medium',
    risks TEXT,
    dependencies_text TEXT,
    roadmap_phase TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS epic_dependencies (
    id SERIAL PRIMARY KEY,
    epic_id INTEGER NOT NULL REFERENCES epics(id),
    depends_on_epic_id INTEGER NOT NULL REFERENCES epics(id),
    dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
    notes TEXT,
    CHECK (epic_id != depends_on_epic_id)
);

-- ============================================================
-- Step 7: Feature Backlog & Roadmap + Delivery OKRs
-- ============================================================

CREATE TABLE IF NOT EXISTS delivery_okrs (
    id SERIAL PRIMARY KEY,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delivery_key_results (
    id SERIAL PRIMARY KEY,
    delivery_okr_id INTEGER NOT NULL REFERENCES delivery_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value DOUBLE PRECISION DEFAULT 0,
    target_value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    epic_id INTEGER NOT NULL REFERENCES epics(id),
    delivery_okr_id INTEGER REFERENCES delivery_okrs(id),
    name TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'backlog' CHECK (status IN ('backlog', 'ready', 'in_progress', 'done')),
    estimated_effort INTEGER,
    start_date TEXT,
    target_date TEXT,
    completion_date TEXT,
    value_score INTEGER DEFAULT 3,
    size_score INTEGER DEFAULT 3,
    effort_score INTEGER DEFAULT 3,
    priority_score DOUBLE PRECISION DEFAULT 0,
    risk_level TEXT DEFAULT 'medium',
    risks TEXT,
    dependencies_text TEXT,
    roadmap_phase TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- HITL Review Gates
-- ============================================================

CREATE TABLE IF NOT EXISTS review_gates (
    id SERIAL PRIMARY KEY,
    step_number INTEGER NOT NULL CHECK (step_number BETWEEN 1 AND 7),
    gate_number INTEGER NOT NULL,
    gate_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'revision_needed')),
    reviewer TEXT,
    review_notes TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes for performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_value_stream_steps_vs ON value_stream_steps(value_stream_id, step_order);
CREATE INDEX IF NOT EXISTS idx_value_stream_benchmarks_vs ON value_stream_benchmarks(value_stream_id);
CREATE INDEX IF NOT EXISTS idx_revenue_splits_period ON revenue_splits(period);
CREATE INDEX IF NOT EXISTS idx_initiatives_rice ON initiatives(rice_score DESC);
CREATE INDEX IF NOT EXISTS idx_initiatives_status ON initiatives(status);
CREATE INDEX IF NOT EXISTS idx_epics_status ON epics(status);
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_features_epic ON features(epic_id);
CREATE INDEX IF NOT EXISTS idx_review_gates_step ON review_gates(step_number, gate_number);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
