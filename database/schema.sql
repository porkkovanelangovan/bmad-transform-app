-- ============================================================
-- Business Transformation Architect - SQLite Schema
-- ============================================================
-- Referential Integrity Chain:
--   Initiative -> Product -> Epic -> Feature
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- Users (Authentication)
-- ============================================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Organization Setup
-- ============================================================

CREATE TABLE organization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ticker TEXT,
    industry TEXT NOT NULL,
    sub_industry TEXT,
    market_cap REAL,
    country TEXT,
    currency TEXT,
    competitor_1_name TEXT,
    competitor_2_name TEXT,
    ai_executive_summary TEXT,
    ai_health_score REAL,
    ai_summary_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 1: Business Performance Dashboard
-- ============================================================

CREATE TABLE business_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE revenue_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    dimension TEXT NOT NULL CHECK (dimension IN ('product', 'region', 'segment')),
    dimension_value TEXT NOT NULL,
    revenue REAL NOT NULL DEFAULT 0,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ops_efficiency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    target_value REAL,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ticker TEXT,
    market_share REAL,
    revenue REAL,
    profit_margin REAL,
    operating_margin REAL,
    return_on_equity REAL,
    return_on_assets REAL,
    pe_ratio REAL,
    eps REAL,
    market_cap_value REAL,
    strengths TEXT,
    weaknesses TEXT,
    data_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 2: Value Stream Analysis
-- ============================================================

CREATE TABLE value_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE value_stream_levers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    lever_type TEXT NOT NULL CHECK (lever_type IN ('growth', 'efficiency', 'experience', 'effectiveness')),
    opportunity TEXT NOT NULL,
    current_state TEXT,
    target_state TEXT,
    impact_estimate TEXT CHECK (impact_estimate IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE value_stream_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    step_order INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    description TEXT,
    step_type TEXT NOT NULL DEFAULT 'process' CHECK (step_type IN ('trigger', 'process', 'decision', 'delivery')),
    process_time_hours REAL DEFAULT 0,
    wait_time_hours REAL DEFAULT 0,
    lead_time_hours REAL DEFAULT 0,
    resources TEXT,
    is_bottleneck INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE value_stream_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_stream_id INTEGER NOT NULL UNIQUE REFERENCES value_streams(id),
    total_lead_time_hours REAL DEFAULT 0,
    total_process_time_hours REAL DEFAULT 0,
    total_wait_time_hours REAL DEFAULT 0,
    flow_efficiency REAL DEFAULT 0,
    bottleneck_step TEXT,
    bottleneck_reason TEXT,
    data_source TEXT DEFAULT 'manual' CHECK (data_source IN ('ai_generated', 'template', 'uploaded', 'manual', 'visual_upload', 'url_extraction')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE value_stream_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    competitor_name TEXT NOT NULL,
    total_lead_time_hours REAL,
    total_process_time_hours REAL,
    flow_efficiency REAL,
    bottleneck_step TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 3: SWOT to TOWS Action Engine
-- ============================================================

CREATE TABLE swot_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    category TEXT NOT NULL CHECK (category IN ('strength', 'weakness', 'opportunity', 'threat')),
    description TEXT NOT NULL,
    data_source TEXT,
    severity TEXT DEFAULT 'medium',
    confidence TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tows_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_type TEXT NOT NULL CHECK (strategy_type IN ('SO', 'WO', 'ST', 'WT')),
    swot_entry_1_id INTEGER NOT NULL REFERENCES swot_entries(id),
    swot_entry_2_id INTEGER NOT NULL REFERENCES swot_entries(id),
    action_description TEXT NOT NULL,
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    impact_score INTEGER DEFAULT 5,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 4: Four-Layer Strategy & Strategic OKRs
-- ============================================================

CREATE TABLE strategy_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_type TEXT NOT NULL CHECK (input_type IN (
        'business_strategy', 'digital_strategy', 'data_strategy', 'gen_ai_strategy',
        'competitor_strategy', 'ongoing_initiatives', 'document_reference'
    )),
    title TEXT,
    content TEXT NOT NULL,
    file_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer TEXT NOT NULL CHECK (layer IN ('business', 'digital', 'data', 'gen_ai')),
    name TEXT NOT NULL,
    description TEXT,
    tows_action_id INTEGER REFERENCES tows_actions(id),
    approved INTEGER DEFAULT 0,
    risk_level TEXT DEFAULT 'medium',
    risks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE strategic_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    objective TEXT NOT NULL,
    time_horizon TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE strategic_key_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value REAL DEFAULT 0,
    target_value REAL NOT NULL,
    target_optimistic REAL,
    target_pessimistic REAL,
    unit TEXT,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 5: Digital Initiatives & RICE Prioritization
-- ============================================================

CREATE TABLE product_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE digital_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_group_id INTEGER NOT NULL REFERENCES product_groups(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    strategy_id INTEGER REFERENCES strategies(id),
    name TEXT NOT NULL,
    description TEXT,
    -- RICE scoring
    reach INTEGER NOT NULL DEFAULT 1,
    impact REAL NOT NULL DEFAULT 1 CHECK (impact IN (0.25, 0.5, 1, 2, 3)),
    confidence REAL NOT NULL DEFAULT 1 CHECK (confidence IN (0.5, 0.8, 1.0)),
    effort INTEGER NOT NULL DEFAULT 1,
    rice_score REAL GENERATED ALWAYS AS ((reach * impact * confidence * 1.0) / effort) STORED,
    -- Manual override
    rice_override REAL,
    rice_override_reason TEXT,
    -- Extended metadata
    value_score INTEGER DEFAULT 3,
    size_score INTEGER DEFAULT 3,
    impacted_segments TEXT,
    dependencies TEXT,
    risks TEXT,
    roadmap_phase TEXT,
    status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'in_progress', 'completed', 'deferred')),
    ai_generated INTEGER DEFAULT 0,
    ai_rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Step 6: Epic & Team Collaboration + Product OKRs
-- ============================================================

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategic_okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    ai_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_key_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value REAL DEFAULT 0,
    target_value REAL NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    priority_score REAL DEFAULT 0,
    risk_level TEXT DEFAULT 'medium',
    risks TEXT,
    dependencies_text TEXT,
    roadmap_phase TEXT,
    ai_generated INTEGER DEFAULT 0,
    estimated_effort_days REAL,
    ai_rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE epic_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_id INTEGER NOT NULL REFERENCES epics(id),
    depends_on_epic_id INTEGER NOT NULL REFERENCES epics(id),
    dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
    notes TEXT,
    CHECK (epic_id != depends_on_epic_id)
);

-- ============================================================
-- Step 7: Feature Backlog & Roadmap + Delivery OKRs
-- ============================================================

CREATE TABLE delivery_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    ai_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE delivery_key_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_okr_id INTEGER NOT NULL REFERENCES delivery_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value REAL DEFAULT 0,
    target_value REAL NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    priority_score REAL DEFAULT 0,
    risk_level TEXT DEFAULT 'medium',
    risks TEXT,
    dependencies_text TEXT,
    roadmap_phase TEXT,
    ai_generated INTEGER DEFAULT 0,
    ai_rationale TEXT,
    acceptance_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- HITL Review Gates
-- ============================================================

CREATE TABLE review_gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
-- Step 1: Data Ingestion Hub
-- ============================================================

CREATE TABLE step1_data_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    label TEXT,
    url_type TEXT DEFAULT 'external',
    last_fetched_at TIMESTAMP,
    last_result_json TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- AI Dashboard Tables
-- ============================================================

CREATE TABLE ai_analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    result_json TEXT NOT NULL,
    ai_model TEXT DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE ai_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    scenario_type TEXT NOT NULL CHECK (scenario_type IN ('revenue_change', 'market_entry', 'cost_change', 'custom')),
    parameters_json TEXT NOT NULL,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE nlq_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    data_tables_queried TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feature_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL REFERENCES features(id),
    depends_on_feature_id INTEGER NOT NULL REFERENCES features(id),
    dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
    notes TEXT,
    CHECK (feature_id != depends_on_feature_id)
);

-- ============================================================
-- Generate All: Orchestrator Runs
-- ============================================================

CREATE TABLE generation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER NOT NULL REFERENCES organization(id),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'partial')),
    current_step INTEGER DEFAULT 0,
    steps_completed TEXT DEFAULT '[]',
    steps_failed TEXT DEFAULT '[]',
    message TEXT,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================
-- Indexes for performance
-- ============================================================

CREATE INDEX idx_value_stream_steps_vs ON value_stream_steps(value_stream_id, step_order);
CREATE INDEX idx_value_stream_benchmarks_vs ON value_stream_benchmarks(value_stream_id);
CREATE INDEX idx_revenue_splits_period ON revenue_splits(period);
CREATE INDEX idx_initiatives_rice ON initiatives(rice_score DESC);
CREATE INDEX idx_initiatives_status ON initiatives(status);
CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_features_status ON features(status);
CREATE INDEX idx_features_epic ON features(epic_id);
CREATE INDEX idx_review_gates_step ON review_gates(step_number, gate_number);
CREATE INDEX idx_users_email ON users(email);
