# Complete Rebuild Prompt — BMAD Multi-Agent Business Transformation Platform

> **Purpose**: This document is a comprehensive, self-contained prompt that can be used to rebuild the entire BMAD Business Transformation Architect platform from scratch. It contains every architectural decision, database schema, API endpoint, AI prompt template, frontend component, and business rule needed to recreate the application exactly as it exists.

---

## PROJECT OVERVIEW

Build a **multi-agent AI-powered business transformation platform** that guides organizations through a structured 7-step process — from financial performance analysis to a fully prioritized feature roadmap with quarterly delivery timeline.

### What It Does

A user enters a company name and industry. The platform then:
1. **Step 1**: Ingests real financial data (or AI-generates it for private companies), scores organizational health
2. **Step 2**: Maps business processes as lean value streams, identifies bottlenecks, benchmarks against competitors
3. **Step 3**: Generates SWOT analysis and converts to actionable TOWS strategies
4. **Step 4**: Creates four-layer strategies (Business, Digital, Data, Gen AI) with cascading OKRs
5. **Step 5**: Generates prioritized digital initiatives with RICE scoring
6. **Step 6**: Breaks initiatives into delivery epics, forms teams, sets product OKRs
7. **Step 7**: Creates detailed features with acceptance criteria and quarterly roadmap

Each step has AI auto-generation with human review gates. Users can also click "Generate All Steps" for one-click end-to-end generation (~30-60 seconds).

### Key Capabilities
- 13 specialized AI agents working in sequence
- RAG (Retrieval-Augmented Generation) knowledge base for organization-specific context
- Demo mode (sample data) and Live mode (real data + RAG)
- External API integrations (Finnhub, Alpha Vantage, Jira, ServiceNow)
- File upload support (CSV, Excel, PDF, DOCX, images)
- Process diagram parsing (BPMN/XML, image vision)
- Human-in-the-loop review gates at every step

---

## TECHNOLOGY STACK

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend Framework | FastAPI | 0.115.0 |
| ASGI Server | Uvicorn | 0.30.0 |
| Database | SQLite via aiosqlite | 0.20.0 |
| AI Text Generation | OpenAI GPT-4o-mini | Latest |
| AI Vision | OpenAI GPT-4o | Latest |
| AI Embeddings | OpenAI text-embedding-3-small | Latest |
| Auth | python-jose (JWT) + bcrypt | 3.3.0 / 4.0+ |
| HTTP Client | httpx | 0.27.0 |
| HTML Parsing | BeautifulSoup4 | 4.12+ |
| PDF Parsing | PyMuPDF (fitz) | 1.24+ |
| Excel Parsing | openpyxl | 3.1+ |
| Word Parsing | python-docx | 1.0+ |
| Frontend | Vanilla JavaScript + CSS | ES6+ (no frameworks) |
| Validation | Pydantic | 2.9.0 |

### requirements.txt
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
gunicorn==22.0.0
aiosqlite==0.20.0
httpx==0.27.0
pydantic==2.9.0
python-jose[cryptography]==3.3.0
bcrypt>=4.0.0
python-dotenv==1.0.1
python-multipart==0.0.12
openai>=1.12.0
asyncpg>=0.29.0
email-validator==2.1.0
beautifulsoup4>=4.12.0
PyMuPDF>=1.24.0
openpyxl>=3.1.0
python-docx>=1.0.0
```

### Environment Variables
```
SECRET_KEY=dev-secret-key-change-in-production    # JWT signing key
OPENAI_API_KEY=sk-...                              # OpenAI API (required for AI features)
FINNHUB_API_KEY=...                                # Finnhub financial API (optional)
ALPHA_VANTAGE_API_KEY=...                          # Alpha Vantage financial API (optional)
BRAVE_SEARCH_API_KEY=...                           # Web search (optional)
JIRA_BASE_URL=https://...atlassian.net             # Jira integration (optional)
JIRA_EMAIL=...                                     # Jira auth email
JIRA_API_TOKEN=...                                 # Jira API token
SERVICENOW_INSTANCE=...                            # ServiceNow instance name (optional)
SERVICENOW_USERNAME=...                            # ServiceNow auth
SERVICENOW_PASSWORD=...                            # ServiceNow auth
ALLOWED_ORIGINS=http://localhost:8000               # CORS origins (comma-separated)
DATABASE_URL=                                      # PostgreSQL connection (leave empty for SQLite)
```

---

## PROJECT STRUCTURE

```
bmad-transform-app/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, 12 routers, migrations
│   ├── database.py                # SQLite/PostgreSQL dual-database wrapper
│   ├── auth.py                    # JWT tokens + bcrypt password hashing
│   │
│   ├── routers/                   # API endpoint handlers (12 files)
│   │   ├── auth_router.py         #   /api/auth — register, login, verify
│   │   ├── step1_performance.py   #   /api/step1 — org, BUs, revenue, ops, competitors, file upload, API ingestion
│   │   ├── step1_ai_dashboard.py  #   /api/step1/ai — 13 AI analytics endpoints
│   │   ├── step2_value_streams.py #   /api/step2 — value streams, steps, levers, benchmarks, multi-source pull
│   │   ├── step3_swot_tows.py     #   /api/step3 — SWOT CRUD, TOWS CRUD, auto-generate
│   │   ├── step4_strategy_okrs.py #   /api/step4 — strategy inputs, 4-layer strategies, OKRs, key results
│   │   ├── step5_initiatives.py   #   /api/step5 — product groups, products, initiatives, RICE, roadmap
│   │   ├── step6_epics_teams.py   #   /api/step6 — teams, epics, dependencies, product OKRs, roadmap
│   │   ├── step7_features.py      #   /api/step7 — features, delivery OKRs, dependencies, roadmap
│   │   ├── review_gates.py        #   /api/gates — 7 review gates with approve/reject
│   │   ├── generate_all.py        #   /api/generate-all — orchestrator start/status/retry
│   │   └── documents.py           #   /api/kb — knowledge base upload, search, data-mode toggle
│   │
│   ├── ai_dashboard.py            # Step 1 AI analytics (10 capabilities + context gathering + caching)
│   ├── ai_swot_strategy.py        # Steps 3-4: SWOT, TOWS, strategies, OKRs generation
│   ├── ai_initiatives.py          # Steps 5-7: initiatives, epics, features, team recommendations
│   ├── ai_research.py             # Value stream research + competitor benchmarking
│   ├── ai_generate_all.py         # 7-step orchestrator with progress tracking
│   ├── rag_engine.py              # RAG: chunking, embeddings, cosine similarity, semantic search
│   ├── openai_client.py           # Template engine (deterministic value stream generation, no API needed)
│   │
│   ├── data_ingestion.py          # Finnhub + Alpha Vantage API integration
│   ├── connectors.py              # Jira + ServiceNow API connectors
│   ├── process_parser.py          # BPMN/XML parsing + GPT-4o Vision image extraction
│   ├── url_extractor.py           # Web URL content fetching + AI extraction
│   └── source_gatherers.py        # 8 configurable data source gatherer functions
│
├── frontend/
│   └── index.html                 # Complete SPA (~4,800+ lines: CSS + HTML + JS)
│
├── database/
│   └── schema.sql                 # SQLite schema (25+ tables with indexes)
│
└── seed_test_data.sh              # Test data seeding script (curl-based)
```

---

## DATABASE SCHEMA (SQLite)

### Authentication & Organization

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization (
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
    data_mode TEXT DEFAULT 'demo' CHECK (data_mode IN ('demo', 'live')),
    ai_executive_summary TEXT,
    ai_health_score REAL,
    ai_summary_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step 1: Business Performance Dashboard

```sql
CREATE TABLE IF NOT EXISTS business_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revenue_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    dimension TEXT NOT NULL CHECK (dimension IN ('product', 'region', 'segment')),
    dimension_value TEXT NOT NULL,
    revenue REAL NOT NULL DEFAULT 0,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops_efficiency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    target_value REAL,
    period TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitors (
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

CREATE TABLE IF NOT EXISTS step1_data_urls (
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
```

### Step 2: Value Stream Analysis

```sql
CREATE TABLE IF NOT EXISTS value_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS value_stream_steps (
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

CREATE TABLE IF NOT EXISTS value_stream_metrics (
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

CREATE TABLE IF NOT EXISTS value_stream_benchmarks (
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

CREATE TABLE IF NOT EXISTS value_stream_levers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_stream_id INTEGER NOT NULL REFERENCES value_streams(id),
    lever_type TEXT NOT NULL CHECK (lever_type IN ('growth', 'efficiency', 'experience', 'effectiveness')),
    opportunity TEXT NOT NULL,
    current_state TEXT,
    target_state TEXT,
    impact_estimate TEXT CHECK (impact_estimate IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step 3: SWOT/TOWS

```sql
CREATE TABLE IF NOT EXISTS swot_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_unit_id INTEGER NOT NULL REFERENCES business_units(id),
    category TEXT NOT NULL CHECK (category IN ('strength', 'weakness', 'opportunity', 'threat')),
    description TEXT NOT NULL,
    data_source TEXT,
    severity TEXT DEFAULT 'medium',
    confidence TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tows_actions (
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
```

### Step 4: Strategy & OKRs

```sql
CREATE TABLE IF NOT EXISTS strategy_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_type TEXT NOT NULL CHECK (input_type IN ('business_strategy', 'digital_strategy', 'data_strategy', 'gen_ai_strategy', 'competitor_strategy', 'ongoing_initiatives', 'document_reference')),
    title TEXT,
    content TEXT NOT NULL,
    file_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategies (
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

CREATE TABLE IF NOT EXISTS strategic_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    objective TEXT NOT NULL,
    time_horizon TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategic_key_results (
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
```

### Step 5: Initiatives & RICE

```sql
CREATE TABLE IF NOT EXISTS product_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS digital_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_group_id INTEGER NOT NULL REFERENCES product_groups(id),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    strategy_id INTEGER REFERENCES strategies(id),
    name TEXT NOT NULL,
    description TEXT,
    reach INTEGER NOT NULL DEFAULT 1,
    impact REAL NOT NULL DEFAULT 1 CHECK (impact IN (0.25, 0.5, 1, 2, 3)),
    confidence REAL NOT NULL DEFAULT 1 CHECK (confidence IN (0.5, 0.8, 1.0)),
    effort INTEGER NOT NULL DEFAULT 1,
    rice_score REAL GENERATED ALWAYS AS ((reach * impact * confidence * 1.0) / effort) STORED,
    rice_override REAL,
    rice_override_reason TEXT,
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
```

### Step 6: Epics & Teams

```sql
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategic_okr_id INTEGER NOT NULL REFERENCES strategic_okrs(id),
    digital_product_id INTEGER NOT NULL REFERENCES digital_products(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    ai_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_key_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value REAL DEFAULT 0,
    target_value REAL NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS epics (
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

CREATE TABLE IF NOT EXISTS epic_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_id INTEGER NOT NULL REFERENCES epics(id),
    depends_on_epic_id INTEGER NOT NULL REFERENCES epics(id),
    dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
    notes TEXT,
    CHECK (epic_id != depends_on_epic_id)
);
```

### Step 7: Features & Delivery OKRs

```sql
CREATE TABLE IF NOT EXISTS delivery_okrs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_okr_id INTEGER NOT NULL REFERENCES product_okrs(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    objective TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'achieved', 'at_risk')),
    ai_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delivery_key_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_okr_id INTEGER NOT NULL REFERENCES delivery_okrs(id),
    key_result TEXT NOT NULL,
    metric TEXT,
    current_value REAL DEFAULT 0,
    target_value REAL NOT NULL,
    unit TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
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

CREATE TABLE IF NOT EXISTS feature_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL REFERENCES features(id),
    depends_on_feature_id INTEGER NOT NULL REFERENCES features(id),
    dependency_type TEXT DEFAULT 'blocks' CHECK (dependency_type IN ('blocks', 'relates_to')),
    notes TEXT,
    CHECK (feature_id != depends_on_feature_id)
);
```

### Review Gates, Orchestration, AI Cache, RAG

```sql
CREATE TABLE IF NOT EXISTS review_gates (
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

CREATE TABLE IF NOT EXISTS generation_runs (
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

CREATE TABLE IF NOT EXISTS ai_analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    result_json TEXT NOT NULL,
    ai_model TEXT DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    scenario_type TEXT NOT NULL CHECK (scenario_type IN ('revenue_change', 'market_entry', 'cost_change', 'custom')),
    parameters_json TEXT NOT NULL,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nlq_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    data_tables_queried TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS org_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER NOT NULL REFERENCES organization(id),
    filename TEXT NOT NULL,
    file_type TEXT,
    content_text TEXT,
    doc_category TEXT DEFAULT 'general' CHECK (doc_category IN ('general', 'financial', 'strategy', 'operations', 'value_stream', 'competitor', 'technology', 'market')),
    upload_source TEXT DEFAULT 'manual' CHECK (upload_source IN ('manual', 'step1_upload', 'step2_upload', 'url_fetch', 'api_ingest')),
    step_number INTEGER,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES org_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_json TEXT,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_org_documents_org ON org_documents(org_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc ON document_chunks(document_id);
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
```

---

## BACKEND IMPLEMENTATION

### 1. main.py — Application Setup

**Responsibilities:**
- Create FastAPI app (title: "Business Transformation Architect", version: "1.0.0")
- Configure CORS middleware with `ALLOWED_ORIGINS` from env (default: `http://localhost:8000`)
- Mount `frontend/` directory as static files at root `/`
- Register 12 routers with `/api/` prefix
- On startup: initialize database, run migrations (execute schema.sql, then ALTER TABLE for any missing columns)
- Add no-cache middleware for `/` and `*.html` responses

**Router Registration:**
```
/api/auth          → auth_router
/api/step1         → step1_performance
/api/step1         → step1_ai_dashboard (same prefix, different routes)
/api/step2         → step2_value_streams
/api/step3         → step3_swot_tows
/api/step4         → step4_strategy_okrs
/api/step5         → step5_initiatives
/api/step6         → step6_epics_teams
/api/step7         → step7_features
/api/gates         → review_gates
/api/generate-all  → generate_all
/api/kb            → documents
```

### 2. database.py — Unified Database Wrapper

**Key Design: Dual-database support with a single interface**

```python
class SQLiteRow:
    """Makes aiosqlite rows dict-accessible via row["column_name"]"""
    # Wraps aiosqlite.Row with __getitem__, get, items, keys, values

class CursorResult:
    """Holds lastrowid from INSERT operations"""
    # Attribute: lastrowid (int | None)

class DBConnection:
    """Unified interface for SQLite and PostgreSQL"""
    # Methods:
    # - execute_fetchall(query, params) → list[dict]
    # - execute_fetchone(query, params) → dict | None
    # - execute(query, params) → CursorResult
    # - executescript(script) — run multi-statement SQL
    # - commit() — SQLite only
    # - close()
```

**Critical Feature — Placeholder Conversion:**
- SQLite uses `?` placeholders
- PostgreSQL uses `$1, $2, ...` positional placeholders
- `database.py` auto-converts `?` → `$N` using regex on every query
- This allows ALL SQL queries to be written with `?` and work on both databases

**Connection:**
- SQLite: `aiosqlite.connect("../database/bmad_transform.db")` per request
- PostgreSQL (if `DATABASE_URL` set): asyncpg connection pool (min=2, max=10)
- FastAPI dependency: `async def get_db() -> DBConnection`

### 3. auth.py — JWT Authentication

```python
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Functions:
hash_password(password: str) → str         # bcrypt.hashpw with gensalt
verify_password(plain, hashed) → bool      # bcrypt.checkpw
create_access_token(data: dict) → str      # jwt.encode with exp claim (+24h)
get_current_user(token) → dict             # Verify JWT, query users table
get_optional_user(request) → dict | None   # Non-raising version for optional auth
```

### 4. data_ingestion.py — Financial API Integration

**Finnhub API** (finnhub.io):
- `search_ticker(company_name)` — Search with multiple query variations (abbreviations, corporate suffixes), filter to US exchanges
- `fetch_company_profile(ticker)` — Company metadata (industry, market cap, country)
- `fetch_peers(ticker)` — Competitor ticker discovery (top 8)
- `fetch_finnhub_metrics(ticker)` — 25+ financial metrics (margins, ROE, ROA, PE, EPS, beta, dividends, 5-year annual data)

**Alpha Vantage API** (alphavantage.co):
- `fetch_company_overview(ticker)` — Revenue, margins, PE ratio, analyst target
- `fetch_financials(ticker)` — Income statement (5 years of annual reports)

**Key Business Rule:** Finnhub is PRIMARY source (60 calls/min), Alpha Vantage is SUPPLEMENT (25 calls/day). Metrics from Finnhub take priority; Alpha Vantage fills gaps.

### 5. openai_client.py — Template Engine (No API Required)

**Purpose:** Deterministic value stream generation using built-in industry templates. Does NOT call OpenAI despite the filename.

**10+ Templates:** loan processing, claims management, account opening, payment processing, software development, incident management, customer onboarding, patient intake, order fulfillment, production manufacturing

**Each Template Contains:**
- 6-10 process steps with: step_name, step_type (trigger/process/decision/delivery), process_time_hours, wait_time_hours, resources, is_bottleneck, notes
- Bottleneck reason explanation

**Functions:**
- `generate_value_stream(segment_name, industry, org_name, competitors)` → steps + metrics + competitor benchmarks
- `_find_template(segment_name)` — Fuzzy match segment to template (exact → partial → keyword → default)
- `_generate_benchmarks(...)` — Creates competitor benchmarks with ±15-30% variance (seeded randomization)

**Metrics Calculation:**
- `total_lead_time = sum(process_time + wait_time)` for all steps
- `flow_efficiency = (total_process_time / total_lead_time) × 100`
- Bottleneck = explicitly marked step OR highest lead time step

### 6. AI Modules

#### 6a. ai_research.py — Value Stream Synthesis & Competitor Benchmarking

**`research_value_stream(segment_name, industry, org_name, org_context, competitor_data, sources_context, rag_context)`**
- Model: GPT-4o-mini, Temperature: 0.7, Max Tokens: 3000
- System prompt: "You are a lean/six sigma expert specializing in value stream mapping..."
- Returns: `{steps: [...], overall_metrics: {...}, competitor_benchmarks: [...]}`
- Each benchmark includes: automation_level, technology_stack, key_differentiator
- Validation: auto-calculate metrics if missing from AI response

**`research_competitor_benchmarks(segment_name, industry, org_name, competitors, org_value_stream_data, rag_context)`**
- Model: GPT-4o-mini, Temperature: 0.7, Max Tokens: 3000
- System prompt: "You are an operations research expert specializing in competitive benchmarking..."
- Returns: `{benchmarks: [...], industry_best_practices: [...]}`
- Each benchmark includes: digital_maturity, process_innovations, estimated_cost_per_transaction

**`is_openai_available()`** — Returns True only if OPENAI_API_KEY env var set AND openai package importable

#### 6b. ai_dashboard.py — 10 AI Dashboard Capabilities

All functions use GPT-4o-mini at Temperature 0.7.

| # | Function | Max Tokens | Returns |
|---|----------|-----------|---------|
| 1 | `ai_financial_analysis()` | 3000 | SWOT with metric references, data_quality_score 0-100 |
| 2 | `ai_discover_competitors()` | 3000 | 4-8 new competitors with threat_score 1-10, relevance (direct/indirect/emerging) |
| 3 | `ai_trend_analysis()` | 3000 | Revenue direction, CAGR, YoY growth rates, 1-3 period forecasts |
| 4 | `ai_anomaly_detection()` | 3000 | Anomalies with severity, data quality issues, benchmark deviations |
| 5 | `ai_executive_summary()` | 4000 | 3 paragraphs (performance, competitive, outlook), key findings, strategic implications |
| 6 | `ai_data_enrichment_suggestions()` | 3000 | Missing metrics, suggested BUs, revenue dimensions, completeness score 0-100 |
| 7 | `ai_transformation_health()` | 5000 | Overall score 0-100, per-step scores, readiness level, critical gaps, gate recommendations |
| 8 | `ai_natural_language_query()` | 3000 | Direct answer, supporting data, confidence, follow-up questions |
| 9 | `ai_whatif_scenario()` | 4000 | Financial/competitive/operational impact, risks, opportunities, downstream effects |
| 10 | `ai_generate_report()` | 5000 | Audience-specific report (c_suite/technical/board), 4-6 sections with markdown |

**Context Gathering:** `gather_dashboard_context(db)` collects ALL data across 7 steps (org, ops, revenue, competitors, BUs, value streams, SWOT, strategies, initiatives, epics, features, gates).

**Caching:** Results cached in `ai_analysis_cache` table with MD5 hash key and 24-hour expiry. Functions 1, 3, 4, 5, 7 use caching.

**RAG Integration:** In live mode, includes `build_rag_context()` with query "{org_name} {industry}...", top_k=6.

#### 6c. ai_swot_strategy.py — SWOT/TOWS/Strategy Generation

**`gather_full_context(db, business_unit_id)`** — Collects: org, financials, revenue, competitors, value streams with metrics/benchmarks, high-impact levers, existing SWOT/TOWS, strategy inputs, external sources (web search, benchmarks, Finnhub, Jira, ServiceNow), RAG context.

**`generate_ai_swot(context)`**
- Returns 4-8 entries per category (S/W/O/T) with severity, confidence, data_source
- Rule: Must reference actual data points

**`generate_ai_tows(swot_entries, context)`**
- Returns 12-20 actions across 4 quadrants (SO/WO/ST/WT)
- Each: impact_score 1-10, priority (critical/high/medium/low)
- SO = offensive/growth, WO = address weaknesses, ST = defend, WT = survival

**`generate_ai_strategies(context, tows_actions)`**
- Returns strategies across 4 layers with OKRs and key results
- Each strategy has: risk_level, risks, tows_alignment
- Key results have: current_value, target_value, target_optimistic, target_pessimistic, unit, rationale
- Targets must be derived from ACTUAL DATA (current metrics, benchmarks, competitor data)

**Rule-based Fallback:** If OpenAI unavailable, generates strategies from financial analysis and value stream gaps with hardcoded targets based on actual metrics.

#### 6d. ai_initiatives.py — Initiatives, Epics, Features

**`generate_ai_initiatives(context)`**
- Returns 1-2 initiatives per strategic OKR
- RICE scoring: Reach (1-10), Impact (0.25/0.5/1/2/3), Confidence (0.5/0.8/1.0), Effort (1-10)
- Formula: `RICE = (Reach × Impact × Confidence) / Effort`
- Roadmap phase: quick_win (high impact + low effort), strategic, long_term

**`generate_ai_epics(initiatives, context)`**
- Returns 2-5 epics per initiative (variable, NOT fixed 3)
- Each: value_score/size_score/effort_score (1-5), estimated_effort_days (1-365), risk_level
- Cross-layer dependencies: gen_ai → data → digital → business
- Also returns: product_okrs, cross_epic_dependencies

**`generate_ai_features(epics, context)`**
- Returns 2-5 features per epic (variable, NOT fixed 3)
- Descriptions in "As a [role], I want [X] so that [Y]" format
- Acceptance criteria in Given/When/Then format
- Also returns: delivery_okrs, feature_dependencies

**`recommend_team_assignments(epics, teams)`**
- Temperature: 0.3 (deterministic)
- Matches epics to teams based on capability keywords

**Rule-based Fallback Templates:**
- Epics per layer: business (Market Analysis, Revenue Optimization, Customer Program), digital (Platform Build, Process Automation, Integration & API), data (Data Pipeline, Dashboard & Analytics, Data Quality & Governance), gen_ai (AI Model Development, AI Workflow Automation, AI Governance & Training)
- Features per layer: business (Research & Discovery, Implementation & Rollout, Monitoring & Optimization), digital (Architecture & Design, Core Development, Testing & Deployment), etc.

#### 6e. ai_generate_all.py — 7-Step Orchestrator

**`generate_all_steps(run_id, org_id, db)`** — Main orchestrator, runs as asyncio background task.

**Step Execution Sequence:**
1. **Step 1**: Try API ingestion (Finnhub/Alpha Vantage) → fallback to AI generation → fallback to templates
2. **Step 2**: AI determines 3-4 value stream names → generates each via pull_from_sources
3. **Step 3**: Calls existing auto_generate() from step3 router
4. **Step 4**: Calls existing auto_generate() from step4 router, then auto-approves all strategies
5. **Step 5**: Calls existing auto_generate() from step5 router
6. **Step 6**: Creates teams first (AI or default), then calls auto_generate() from step6 router
7. **Step 7**: Calls existing auto_generate() from step7 router
8. **Review Gates**: Creates 7 gates (all status: pending)

**Progress Tracking:** Updates `generation_runs` table with current_step, steps_completed (JSON array), steps_failed (JSON array), message, error_message.

**Error Recovery:** Each step in try-except. On failure: adds to steps_failed, continues. Final status: completed (7/7) / partial (some) / failed (0/7).

**Default Teams (if AI unavailable):** Platform Engineering (10), Data & Analytics (8), Product Development (8), Business Operations (6), Customer Experience (6)

#### 6f. rag_engine.py — Knowledge Base & Semantic Search

**`chunk_text(text, chunk_size=400, overlap=80)`**
- Word-based chunking with 80-word overlap (stride = 320)
- Returns list of text chunks

**`generate_embeddings(texts)`**
- Model: OpenAI text-embedding-3-small
- Batch processing: 20 texts per batch
- Returns: list of 1536-dimension float vectors

**`cosine_similarity(a, b)`**
- Formula: `dot(a,b) / (norm(a) × norm(b))`
- Returns 0.0 if either norm is 0

**`store_document(db, org_id, filename, file_type, content_text, doc_category, upload_source, step_number)`**
- Truncates text to 50,000 chars
- Inserts into org_documents
- Chunks text → generates embeddings → stores chunks with embedding_json
- Returns document_id (cursor.lastrowid)

**`retrieve_relevant_chunks(db, query, org_id, top_k=10, doc_category=None)`**
- Generates query embedding → compares cosine similarity to all stored embeddings
- Returns top_k results sorted by similarity descending
- Falls back to keyword search if embedding generation fails

**`build_rag_context(db, query, org_id, top_k=8, doc_category=None)`**
- Retrieves chunks → formats with source headers → joins with separator
- Format: `[Source: filename | Type: category | Relevance: 0.85]`

**`is_live_mode(db)`** — Returns True if organization.data_mode == 'live'

### 7. source_gatherers.py — 8 Data Source Functions

| # | Function | Returns |
|---|----------|---------|
| 1 | `gather_app_data(db)` | Existing org records and value streams from database |
| 2 | `gather_erp_simulation(segment, industry)` | Simulated ERP/CRM data with departments, SLA targets, volumes |
| 3 | `gather_industry_benchmarks(segment, industry)` | Best-in-class/average/laggard benchmarks + industry KPIs |
| 4 | `gather_finnhub_data(org_name, industry, competitors)` | Real competitor profiles and financials from Finnhub |
| 5 | `gather_web_search(segment, industry)` | Web search results (2 queries × 3 results) |
| 6 | `gather_competitor_operations(db, segment, industry, org_name, competitors)` | AI competitor benchmarks + best practices |
| 7 | `gather_jira(segment, industry)` | Jira workflow data (if configured) |
| 8 | `gather_servicenow(segment, industry)` | ServiceNow lifecycle data (if configured) |

All functions fail gracefully, returning empty dicts if unavailable.

### 8. process_parser.py — BPMN & Vision Parsing

- `parse_bpmn(xml_bytes)` — Parses BPMN/XML process diagrams. Maps startEvent→trigger, endEvent→delivery, *Gateway→decision, *Task→process. BFS traversal for step ordering.
- `parse_process_image(file_bytes, content_type)` — GPT-4o Vision (detail="high") extracts process steps from screenshots/diagrams
- PDF: Renders first page as image for Vision, falls back to text extraction from 5 pages

### 9. url_extractor.py — Web Content Extraction

- Fetches URL with httpx (30s timeout, follow redirects)
- BeautifulSoup removes script/style/nav/footer, extracts p/li/td/th/h1-h6 text
- Truncates to 8,000 chars
- GPT-4o-mini (Temperature: 0.1) extracts structured process steps
- Returns: steps[], source_url, confidence (high/medium/low)

### 10. connectors.py — Jira & ServiceNow

**Jira:** HTTP Basic Auth, fetches projects → issues (last 50) → statuses. Calculates avg cycle time from resolved issues. Maps status categories to step_types.

**ServiceNow:** Basic Auth, fetches sys_choice (states) → records (last 50). Calculates avg resolution time. Maps standard incident states to step_types.

---

## API ENDPOINTS — COMPLETE REFERENCE

### Authentication (/api/auth)
| Method | Path | Purpose |
|--------|------|---------|
| POST | /register | Register (email, password≥8 chars, name) → returns user |
| POST | /login | Login → returns JWT token |
| GET | /me | Get current user from token |

### Step 1: Performance Dashboard (/api/step1)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /organization | Get latest org record |
| POST | /organization | Create org (cascade deletes existing data first) |
| GET | /business-units | List all BUs |
| POST | /business-units | Create BU |
| DELETE | /business-units/{id} | Delete BU |
| GET | /revenue-splits | List revenue splits (JOIN business_units) |
| POST | /revenue-splits | Create revenue split |
| GET | /ops-efficiency | List ops metrics (JOIN business_units) |
| POST | /ops-efficiency | Create ops metric |
| GET | /competitors | List competitors |
| POST | /competitors | Create competitor |
| GET | /search-companies?q= | Autocomplete ticker search via Finnhub |
| POST | /ingest | Full API data ingestion (Finnhub + Alpha Vantage + peers + competitors) |
| POST | /upload | Upload file (CSV/Excel/PDF/DOCX/Image) with auto-detection |
| GET | /urls | List saved data URLs |
| POST | /urls | Save data URL |
| DELETE | /urls/{id} | Delete data URL |
| POST | /urls/{id}/fetch | Fetch & extract from single URL |
| POST | /urls/fetch-all | Fetch all saved URLs |
| POST | /refresh-all | Refresh from ALL sources (APIs + URLs + web + Jira + ServiceNow) |
| GET | /analysis | Full analysis with auto-SWOT generation |
| POST | /analysis/save-swot | Save auto-generated SWOT to Step 3 |
| POST | /reset-data | Delete ALL data across steps 1-7 |

### Step 1: AI Dashboard (/api/step1/ai)
| Method | Path | Purpose |
|--------|------|---------|
| POST | /ai/financial-analysis | AI financial SWOT (cached) |
| POST | /ai/discover-competitors | AI competitor discovery |
| POST | /ai/discover-competitors/save | Save discovered competitors to DB |
| GET | /ai/trend-analysis | Revenue trend analysis (cached) |
| GET | /ai/anomaly-detection | Data anomaly detection (cached) |
| POST | /ai/executive-summary | Executive summary (cached, stored in org) |
| GET | /ai/enrichment-suggestions | Missing data recommendations |
| GET | /ai/transformation-health | 7-step health scoring (cached) |
| POST | /ai/query | Natural language query |
| POST | /ai/scenario | What-if scenario modeling |
| GET | /ai/scenarios | List saved scenarios |
| POST | /ai/generate-report | Generate report (c_suite/technical/board) |
| GET | /ai/query-history | List past NLQ queries |

### Step 2: Value Streams (/api/step2)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /value-streams | List value streams |
| POST | /value-streams | Create value stream |
| DELETE | /value-streams/{id} | Delete (cascade steps, metrics, benchmarks, levers) |
| GET | /value-streams/{id}/detail | Full detail with steps, metrics, benchmarks |
| POST | /value-streams/{id}/steps | Add process step |
| PUT | /value-streams/{id}/steps/{sid} | Update step (auto-recalculate lead_time) |
| DELETE | /value-streams/{id}/steps/{sid} | Delete step |
| POST | /value-streams/{id}/recalculate | Recalculate metrics from steps |
| POST | /value-streams/{id}/competitor-benchmarks | AI generate competitor benchmarks |
| GET | /levers | List improvement levers |
| POST | /levers | Create lever |
| POST | /generate | Generate from templates |
| POST | /pull-sources | Multi-source AI generation (8 sources) |
| POST | /upload | Upload CSV/JSON value stream data |
| POST | /upload-visual | Upload image/PDF/BPMN for vision extraction |
| POST | /pull-from-url | Extract process from web URL |

### Step 3: SWOT/TOWS (/api/step3)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /swot | List SWOT entries |
| POST | /swot | Create SWOT entry |
| DELETE | /swot/{id} | Delete (cascade TOWS actions) |
| GET | /tows | List TOWS actions (JOIN SWOT entries) |
| POST | /tows | Create TOWS action |
| POST | /auto-generate | AI or rule-based SWOT + TOWS generation |

### Step 4: Strategy & OKRs (/api/step4)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /inputs | List strategy inputs |
| POST | /inputs | Create/upsert strategy input (singleton per type) |
| DELETE | /inputs/{id} | Delete input |
| GET | /data-sources | Check available data for generation |
| GET | /strategies | List strategies |
| POST | /strategies | Create strategy |
| PUT | /strategies/{id} | Update strategy (name, description, approved, risk) |
| DELETE | /strategies/{id} | Delete (cascade OKRs, key results, nullify initiatives) |
| GET | /strategies-full | Nested: strategies → OKRs → key results |
| GET | /okrs | List strategic OKRs |
| POST | /okrs | Create OKR |
| PUT | /okrs/{id} | Update OKR |
| DELETE | /okrs/{id} | Delete (cascade key results) |
| GET | /okrs/{id}/key-results | List key results for OKR |
| POST | /okrs/{id}/key-results | Create key result |
| DELETE | /okrs/{oid}/key-results/{kid} | Delete key result |
| POST | /approve-all | Approve all strategies + update gate |
| POST | /auto-generate | AI or rule-based strategy + OKR generation |

### Step 5: Initiatives (/api/step5)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /product-groups | List product groups |
| POST | /product-groups | Create product group |
| GET | /digital-products | List digital products |
| POST | /digital-products | Create digital product |
| GET | /initiatives | List initiatives (ORDER BY RICE score DESC) |
| GET | /initiatives-full | Nested: initiatives → strategic OKRs → key results |
| POST | /initiatives | Create initiative (auto-calculates rice_score) |
| PUT | /initiatives/{id} | Update initiative fields |
| POST | /auto-generate | AI or rule-based initiative generation from approved strategies |
| GET | /roadmap | 8-quarter roadmap (2 years) |

### Step 6: Epics & Teams (/api/step6)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /teams | List teams |
| POST | /teams | Create team |
| GET | /product-okrs | List product OKRs |
| POST | /product-okrs | Create product OKR |
| GET | /epics | List epics (ORDER BY priority_score DESC) |
| GET | /epics-full | Nested: epics → initiative → strategy → product → dependencies |
| POST | /epics | Create epic (auto-calculates priority_score) |
| PUT | /epics/{id} | Update epic (auto-recalculate priority_score) |
| DELETE | /epics/{id} | Delete (cascade features, dependencies) |
| GET | /dependencies | List epic dependencies |
| POST | /dependencies | Create dependency |
| DELETE | /dependencies/{id} | Delete dependency |
| GET | /summary | Counts: initiatives, epics, product_okrs, teams, dependencies |
| POST | /auto-generate | AI or rule-based epic generation with team creation |
| GET | /roadmap | 4-quarter roadmap (1 year) |

### Step 7: Features (/api/step7)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /delivery-okrs | List delivery OKRs |
| POST | /delivery-okrs | Create delivery OKR |
| GET | /features | List features (ORDER BY priority_score DESC) |
| GET | /features-full | Nested: features → epic → initiative → strategy → product → team |
| POST | /features | Create feature (auto-calculates priority_score) |
| PUT | /features/{id} | Update feature (auto-recalculate priority_score) |
| DELETE | /features/{id} | Delete feature |
| GET | /feature-dependencies | List feature dependencies |
| POST | /feature-dependencies | Create dependency |
| DELETE | /feature-dependencies/{id} | Delete dependency |
| GET | /summary | Counts: epics, features, delivery_okrs, teams |
| POST | /auto-generate | AI or rule-based feature generation |
| GET | /roadmap | 4-quarter roadmap (1 year) |

### Review Gates (/api/gates)
| Method | Path | Purpose |
|--------|------|---------|
| GET | / | List all review gates |
| GET | /step/{n} | Get gates for step n |
| POST | / | Create gate |
| PUT | /{id} | Update gate (approve/reject with reviewer + notes) |
| GET | /progress | Per-step approval counts |

### Generate All (/api/generate-all)
| Method | Path | Purpose |
|--------|------|---------|
| POST | /start | Start 7-step generation (async background task) |
| GET | /status/{run_id} | Poll generation progress |
| POST | /retry/{run_id} | Retry from failed step |
| GET | /latest | Get most recent generation run |

### Knowledge Base (/api/kb)
| Method | Path | Purpose |
|--------|------|---------|
| GET | /data-mode | Get demo/live mode |
| POST | /data-mode | Toggle demo/live mode |
| POST | /upload | Upload document (PDF/DOCX/XLSX/CSV/TXT/JSON/MD) |
| GET | /list | List documents with chunk counts |
| DELETE | /{doc_id} | Delete document + chunks |
| POST | /search | Semantic search (cosine similarity) |
| GET | /stats | KB stats (documents, chunks, embedded, mode, openai_available) |

---

## FRONTEND IMPLEMENTATION

### Architecture
- **Single HTML file** (~4,800+ lines containing CSS + HTML + JS)
- **No frameworks** — vanilla JavaScript, custom CSS
- **Dark theme** with slate/navy color palette
- **Single-page navigation** — all steps render dynamically into one content area

### Color System
```css
--bg-primary: #0f172a;        /* Dark navy background */
--bg-sidebar: #1e293b;        /* Sidebar and cards */
--text-primary: #e2e8f0;      /* Light gray text */
--text-secondary: #94a3b8;    /* Medium gray text */
--accent: #0ea5e9;            /* Sky blue accent */
--success: #065f46 bg / #6ee7b7 text;  /* Green */
--warning: #713f12 bg / #fbbf24 text;  /* Amber */
--danger: #7f1d1d bg / #fca5a5 text;   /* Red */
--ai: #581c87 bg / #c4b5fd text;       /* Purple for AI badges */
```

### Layout Structure
```
┌──────────────────────────────────────────────────┐
│  SIDEBAR (280px)          │  MAIN CONTENT AREA   │
│  ┌──────────────────┐     │  ┌──────────────────┐│
│  │ App Title         │     │  │  Dynamic content ││
│  │ Step 1-7 nav items│     │  │  rendered by     ││
│  │ (with gate badges)│     │  │  loadStep{N}()   ││
│  │ ─────────────────│     │  │                  ││
│  │ KB Knowledge Base │     │  │  Phase tabs      ││
│  │ Data Mode Badge   │     │  │  Data tables     ││
│  │ ─────────────────│     │  │  Forms           ││
│  │ User info + Logout│     │  │  Charts          ││
│  └──────────────────┘     │  │  AI sections     ││
│                            │  │  Review gates    ││
│                            │  └──────────────────┘│
└──────────────────────────────────────────────────┘
```

### JavaScript State
```javascript
const API = '/api';
let currentStep = 1;
let authToken = localStorage.getItem('bta_token');
let currentUser = null;
let step1Phase = 'data';    // 'setup' | 'data' | 'analysis' | 'ai'
let currentDataMode = 'demo';
let _genPollTimer = null;
let _currentRunId = null;
```

### Core Navigation
```javascript
showStep(n)          // Navigate to step 1-7, calls loadStep{N}()
loadStep1()          // Loads Step 1 with 4 sub-phases
loadStep2() - 7()    // Each step has phase tabs and CRUD forms
```

### Step 1 Sub-Phases
- **setup**: Organization creation form with company autocomplete (Finnhub search)
- **data**: Data ingestion hub — file upload (CSV/Excel/PDF/DOCX/Image), URL extraction, API connectors, saved URLs
- **analysis**: Financial metrics dashboard — revenue splits, ops metrics, competitor tables, charts
- **ai**: AI Dashboard — 10 collapsible capability sections (financial analysis, trends, anomalies, executive summary, competitor discovery, enrichment, health, NLQ, scenarios, reports)

### Key UI Components

**Autocomplete Widget:**
- `onOrgNameInput(val)` triggers Finnhub search after 300ms debounce
- Arrow keys navigate, Enter selects
- Shows company name + ticker symbol

**Value Stream Flow Diagram:**
- Horizontal flow with step boxes connected by arrows
- Step types styled: trigger (dashed green), process (solid), decision (rotated diamond), delivery (dashed blue)
- Bottleneck steps highlighted orange
- Metrics bar below showing lead time, process time, flow efficiency

**SWOT Grid:**
- 2×2 CSS grid with color-coded quadrants (green/red/blue/amber)
- Severity and confidence badges per entry

**RICE Score Badges:**
- rice-high (≥5): green
- rice-mid (≥2): amber
- rice-low (<2): red

**Quarterly Roadmap:**
- Horizontal scroll container with quarter columns
- Cards color-coded by strategy layer
- Phase badges: QW (Quick Win), ST (Strategic), LT (Long-Term)
- Step 5: 8 quarters (2 years), Steps 6-7: 4 quarters (1 year)

**Strategy Layer Colors:**
- Business: Green border/badge
- Digital: Blue border/badge
- Data: Orange border/badge
- Gen AI: Purple border/badge

**Generate All Modal:**
- Full-screen overlay with step progress list
- Each step shows: icon (pending/running/done/failed), name, status message
- Polls `/api/generate-all/status/{run_id}` every 2 seconds
- On complete: transforms into Review Wizard with approve buttons

**Knowledge Base Modal:**
- Stats cards (documents, chunks, embedded, mode)
- Upload area with category dropdown
- Document list with delete buttons
- Semantic search with results showing similarity scores
- Data mode toggle switch (Demo ↔ Live)

**Toast Notifications:**
- Fixed bottom-right position
- Auto-dismiss after 2.5 seconds
- Green success styling

**Inline Editing:**
- Click table cell → transforms to input/select
- Enter saves, Escape cancels
- Calls PUT endpoint to update

**Collapsible Cards:**
- Click header to expand/collapse body
- Used for AI sections in Step 1

### Gate Configuration
```javascript
const gateConfig = {
    1: [{n:1, name:'Review dashboard metrics'}, {n:2, name:'Approve performance baseline'}],
    2: [{n:1, name:'Refine opportunity levers'}],
    3: [{n:1, name:'Validate SWOT entries'}, {n:2, name:'Approve TOWS strategies'}],
    4: [{n:1, name:'Review strategies'}, {n:2, name:'Approve Strategic OKRs'}],
    5: [{n:1, name:'RICE manual override complete'}, {n:2, name:'Approve initiative list'}],
    6: [{n:1, name:'Review team dependencies'}, {n:2, name:'Approve Product OKRs'}],
    7: [{n:1, name:'Review Delivery OKRs'}, {n:2, name:'Approve final roadmap'}],
};
```

---

## CRITICAL BUSINESS RULES

### Scoring Formulas
| Formula | Calculation | Valid Values |
|---------|-------------|--------------|
| RICE Score | (Reach × Impact × Confidence) / Effort | R: 1-10, I: {0.25,0.5,1,2,3}, C: {0.5,0.8,1.0}, E: 1-10 |
| Priority Score | (Value × Size) / Effort | All: 1-5 |
| Flow Efficiency | (process_time / lead_time) × 100 | Percentage |
| Lead Time | process_time + wait_time | Hours |

### Key Constraints
1. **RICE Impact** must be one of: 0.25, 0.5, 1, 2, 3 — no other values
2. **RICE Confidence** must be one of: 0.5, 0.8, 1.0 — no other values
3. **Strategy layers**: business, digital, data, gen_ai — all four required
4. **Strategy auto-approval**: Step 4 strategies auto-approved (SET approved=1) during Generate All for Step 5 consumption
5. **Epic/Feature counts**: 2-5 per parent (variable, NOT fixed 3)
6. **Cross-layer dependencies**: gen_ai → data → digital → business
7. **OKR Cascade**: Strategic OKRs → Product OKRs → Delivery OKRs
8. **RAG only in Live mode**: Demo mode uses no RAG context in AI prompts
9. **AI analysis caching**: 24-hour expiry, MD5 hash of input data as cache key
10. **Organization reset cascade**: Must delete org_documents, document_chunks, generation_runs before deleting organization (FK constraints)

### Data Flow Between Steps
```
Step 1 (BUs, revenue, ops, competitors)
  → Step 2 (value streams, process steps, bottlenecks)
    → Step 3 (SWOT entries, TOWS actions)
      → Step 4 (strategies [approved], OKRs, key results)
        → Step 5 (product groups, products, RICE initiatives)
          → Step 6 (teams, epics, product OKRs, dependencies)
            → Step 7 (features, delivery OKRs, quarterly roadmap)
```

### AI Fallback Pattern
Every AI-powered feature has a deterministic fallback:
```
is_openai_available()?
  → Yes: Call GPT-4o-mini with structured JSON prompt
  → No:  Use template/rule-based generation (works without any API key)
```

---

## RUNNING THE APPLICATION

### Local Development
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access at: http://localhost:8000

### Database
- SQLite file created automatically at `database/bmad_transform.db`
- Schema applied on first startup via `schema.sql`
- No separate migration step needed

### Testing with Seed Data
```bash
bash seed_test_data.sh http://localhost:8000
```
This creates a complete Apple Inc. dataset across all 7 steps via curl API calls.

---

## IMPLEMENTATION ORDER

Build in this sequence (each phase depends on the previous):

### Phase 1: Foundation
1. `database/schema.sql` — Complete database schema
2. `backend/database.py` — SQLite connection wrapper
3. `backend/auth.py` — JWT + bcrypt authentication
4. `backend/main.py` — FastAPI app skeleton with CORS, static files, startup
5. `backend/routers/auth_router.py` — Register/login/me
6. `frontend/index.html` — Login screen + basic layout + navigation shell

### Phase 2: Step 1 — Performance Dashboard
7. `backend/data_ingestion.py` — Finnhub + Alpha Vantage API calls
8. `backend/routers/step1_performance.py` — Org setup, CRUD, file upload, API ingestion
9. `backend/ai_dashboard.py` — 10 AI capabilities + context gathering + caching
10. `backend/routers/step1_ai_dashboard.py` — AI dashboard endpoints
11. Frontend: Step 1 phases (setup, data, analysis, AI)

### Phase 3: Step 2 — Value Streams
12. `backend/openai_client.py` — Template engine (10+ industry templates)
13. `backend/source_gatherers.py` — 8 data source gatherers
14. `backend/connectors.py` — Jira + ServiceNow connectors
15. `backend/process_parser.py` — BPMN/Vision parsing
16. `backend/url_extractor.py` — Web content extraction
17. `backend/ai_research.py` — Value stream synthesis + competitor benchmarks
18. `backend/routers/step2_value_streams.py` — Value stream CRUD, multi-source pull, visual upload
19. Frontend: Step 2 (input methods, edit view, flow diagram, benchmarks)

### Phase 4: Steps 3-4 — SWOT, Strategy & OKRs
20. `backend/ai_swot_strategy.py` — SWOT/TOWS/Strategy/OKR generation
21. `backend/routers/step3_swot_tows.py` — SWOT/TOWS CRUD + auto-generate
22. `backend/routers/step4_strategy_okrs.py` — Strategy inputs, strategies, OKRs, key results
23. Frontend: Step 3 (SWOT grid, TOWS matrix) + Step 4 (inputs, generation, review)

### Phase 5: Steps 5-7 — Initiatives, Epics, Features
24. `backend/ai_initiatives.py` — Initiatives/Epics/Features + RICE + team recommendations
25. `backend/routers/step5_initiatives.py` — Product groups, products, initiatives, roadmap
26. `backend/routers/step6_epics_teams.py` — Teams, epics, dependencies, product OKRs
27. `backend/routers/step7_features.py` — Features, delivery OKRs, dependencies, roadmap
28. Frontend: Steps 5-7 (RICE table, quarterly roadmaps, feature backlog)

### Phase 6: Review Gates & Orchestration
29. `backend/routers/review_gates.py` — Gate CRUD + approval workflow
30. `backend/ai_generate_all.py` — 7-step orchestrator
31. `backend/routers/generate_all.py` — Start/status/retry endpoints
32. Frontend: Review gates, Generate All modal, progress polling

### Phase 7: Knowledge Base (RAG)
33. `backend/rag_engine.py` — Chunking, embeddings, similarity search, context building
34. `backend/routers/documents.py` — KB upload, list, search, delete, data-mode toggle
35. Frontend: KB modal, data mode badge, document management

### Phase 8: Polish & Testing
36. Create seed data script (curl-based API calls)
37. End-to-end testing across all steps
38. Cross-browser testing
39. Error handling review

---

> **This prompt contains everything needed to rebuild the entire BMAD Business Transformation Architect platform. Every table, endpoint, AI prompt, UI component, business rule, and scoring formula is documented above. Build each phase sequentially, testing as you go.**
