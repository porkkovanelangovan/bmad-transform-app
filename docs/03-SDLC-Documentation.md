# SDLC Documentation — BMAD Multi-Agent Transformation Platform

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Requirements Specification](#2-requirements-specification)
3. [System Architecture & Design](#3-system-architecture--design)
4. [Implementation Details](#4-implementation-details)
5. [Testing Strategy](#5-testing-strategy)
6. [Deployment & Operations](#6-deployment--operations)
7. [Maintenance & Support](#7-maintenance--support)
8. [Appendices](#8-appendices)

---

## 1. Project Overview

### 1.1 Product Vision

The **BMAD Business Transformation Architect** is an AI-powered multi-agent platform that guides organizations through a structured 7-step business transformation process — from financial performance analysis to a fully prioritized feature roadmap with quarterly delivery timeline.

### 1.2 Problem Statement

Organizations undertaking digital transformation face:
- Months of manual strategic analysis across disconnected tools
- Lack of data-driven prioritization for transformation initiatives
- No clear path from business strategy to engineering deliverables
- Difficulty maintaining alignment between strategy, OKRs, and execution

### 1.3 Solution

A single platform where 13 specialized AI agents collaborate to:
- Ingest real financial and operational data
- Map business processes and identify bottlenecks
- Generate SWOT analysis and strategic actions
- Create multi-layer strategies with cascading OKRs
- Prioritize digital initiatives with RICE scoring
- Break work into epics, features, and quarterly roadmaps
- Maintain human oversight through review gates at every step

### 1.4 Key Metrics

| Metric | Value |
|--------|-------|
| Time to complete full transformation plan | < 60 seconds (AI) or days (manual) |
| Cost per AI-generated plan | ~$0.03-0.05 (GPT-4o-mini) |
| Steps in transformation pipeline | 7 |
| AI agents | 13 specialized modules |
| External API integrations | 5 (Finnhub, Alpha Vantage, OpenAI, Brave Search, Jira/ServiceNow) |
| Human review gates | 7 (one per step) |

---

## 2. Requirements Specification

### 2.1 Functional Requirements

#### FR-01: User Authentication
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01.1 | Users can register with email and password | Must Have | Done |
| FR-01.2 | Users can log in and receive JWT tokens | Must Have | Done |
| FR-01.3 | Token-based session management with expiry | Must Have | Done |
| FR-01.4 | Password hashing with bcrypt | Must Have | Done |

#### FR-02: Organization Management
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-02.1 | Create organization with name, industry, competitors | Must Have | Done |
| FR-02.2 | Search for public company tickers | Should Have | Done |
| FR-02.3 | Switch between Demo and Live data modes | Should Have | Done |
| FR-02.4 | Organization data persists across sessions | Must Have | Done |

#### FR-03: Step 1 — Business Performance Dashboard
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-03.1 | Ingest financial data from Finnhub and Alpha Vantage APIs | Must Have | Done |
| FR-03.2 | Upload CSV, Excel, PDF, DOCX, JSON files for data extraction | Must Have | Done |
| FR-03.3 | Extract financial data from web URLs | Should Have | Done |
| FR-03.4 | Display business units, revenue splits, ops metrics, competitors | Must Have | Done |
| FR-03.5 | AI-powered financial health scoring (0-100) | Should Have | Done |
| FR-03.6 | AI trend analysis and forecasting | Should Have | Done |
| FR-03.7 | AI anomaly detection in KPIs | Should Have | Done |
| FR-03.8 | AI executive summary generation | Should Have | Done |
| FR-03.9 | Natural language queries over data | Nice to Have | Done |
| FR-03.10 | What-if scenario modeling | Nice to Have | Done |

#### FR-04: Step 2 — Value Stream Analysis
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-04.1 | Create and manage multiple value streams per organization | Must Have | Done |
| FR-04.2 | AI-generated process steps with timing data | Must Have | Done |
| FR-04.3 | Multi-source data gathering (8 configurable sources) | Should Have | Done |
| FR-04.4 | BPMN/XML process diagram parsing | Nice to Have | Done |
| FR-04.5 | Image-based process extraction (GPT-4o Vision) | Nice to Have | Done |
| FR-04.6 | Competitor operational benchmarking | Should Have | Done |
| FR-04.7 | Improvement lever identification (growth, efficiency, experience, effectiveness) | Must Have | Done |
| FR-04.8 | Flow efficiency and bottleneck calculation | Must Have | Done |

#### FR-05: Step 3 — SWOT/TOWS Engine
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-05.1 | AI-generated SWOT analysis from Steps 1-2 context | Must Have | Done |
| FR-05.2 | TOWS action mapping across 4 quadrants (SO, WO, ST, WT) | Must Have | Done |
| FR-05.3 | Severity and confidence ratings per entry | Should Have | Done |
| FR-05.4 | Manual SWOT entry creation and editing | Must Have | Done |

#### FR-06: Step 4 — Strategy & OKRs
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-06.1 | Four-layer strategy generation (Business, Digital, Data, Gen AI) | Must Have | Done |
| FR-06.2 | Strategic OKR creation cascaded from strategies | Must Have | Done |
| FR-06.3 | Key results with target, optimistic, and pessimistic bounds | Should Have | Done |
| FR-06.4 | Strategy approval workflow | Must Have | Done |
| FR-06.5 | User-provided strategy inputs as context | Should Have | Done |

#### FR-07: Step 5 — Digital Initiatives & RICE
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-07.1 | Initiative generation linked to approved strategies | Must Have | Done |
| FR-07.2 | RICE scoring: (Reach × Impact × Confidence) / Effort | Must Have | Done |
| FR-07.3 | Product group and digital product organization | Should Have | Done |
| FR-07.4 | RICE score manual override with rationale | Should Have | Done |
| FR-07.5 | 8-quarter roadmap phasing | Should Have | Done |

#### FR-08: Step 6 — Epics & Teams
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-08.1 | Epic generation from initiatives (2-4 per initiative) | Must Have | Done |
| FR-08.2 | AI-generated team recommendations | Should Have | Done |
| FR-08.3 | Epic-team assignment | Must Have | Done |
| FR-08.4 | Cross-epic dependency mapping | Should Have | Done |
| FR-08.5 | Product OKRs cascaded from Strategic OKRs | Must Have | Done |

#### FR-09: Step 7 — Features & Roadmap
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-09.1 | Feature generation from epics (2-5 per epic) | Must Have | Done |
| FR-09.2 | Acceptance criteria in Given/When/Then format | Should Have | Done |
| FR-09.3 | Feature priority scoring and risk assessment | Must Have | Done |
| FR-09.4 | Quarterly roadmap visualization | Must Have | Done |
| FR-09.5 | Feature dependency tracking | Should Have | Done |

#### FR-10: Orchestration & Review
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-10.1 | One-click "Generate All Steps" orchestration | Must Have | Done |
| FR-10.2 | Real-time progress tracking during generation | Must Have | Done |
| FR-10.3 | Error recovery and retry for failed steps | Should Have | Done |
| FR-10.4 | 7 review gates with approve/reject workflow | Must Have | Done |
| FR-10.5 | Reviewer name and notes for audit trail | Should Have | Done |

#### FR-11: Knowledge Base (RAG)
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-11.1 | Upload documents (PDF, DOCX, XLSX, CSV, TXT, JSON, MD) | Must Have | Done |
| FR-11.2 | Text chunking with overlap for context preservation | Must Have | Done |
| FR-11.3 | Embedding generation via OpenAI text-embedding-3-small | Must Have | Done |
| FR-11.4 | Semantic search with cosine similarity scoring | Must Have | Done |
| FR-11.5 | Keyword fallback when embeddings unavailable | Should Have | Done |
| FR-11.6 | RAG context injection into AI generation prompts | Must Have | Done |

### 2.2 Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-01 | Performance | Full 7-step AI generation | < 60 seconds |
| NFR-02 | Performance | Single API endpoint response time | < 2 seconds (non-AI) |
| NFR-03 | Availability | System uptime | 99.5% (Render free tier) |
| NFR-04 | Scalability | Concurrent users | 10-50 (single instance) |
| NFR-05 | Security | Password storage | bcrypt hashing |
| NFR-06 | Security | API authentication | JWT tokens |
| NFR-07 | Portability | Database | SQLite (dev) + PostgreSQL (prod) |
| NFR-08 | Cost | AI generation per plan | < $0.10 |
| NFR-09 | Resilience | API failure handling | Graceful degradation to templates |
| NFR-10 | Data | Demo/Live mode isolation | Demo data unaffected by Live ops |

---

## 3. System Architecture & Design

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Single-Page Application (SPA)            │    │
│  │          frontend/index.html (~4,834 lines)         │    │
│  │    Vanilla JS  ·  Custom CSS  ·  No frameworks      │    │
│  └──────────────────────┬──────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP/REST (JSON)
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│                                                             │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │              API Router Layer (12 routers)           │    │
│  │  auth · step1 · step1_ai · step2 · step3 · step4   │    │
│  │  step5 · step6 · step7 · gates · generate_all · kb  │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                          │                                   │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │              AI Agent Layer (7 modules)              │    │
│  │  openai_client · ai_dashboard · ai_swot_strategy    │    │
│  │  ai_initiatives · ai_research · ai_generate_all     │    │
│  │  rag_engine                                          │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                          │                                   │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │         Support Layer (utilities & parsers)          │    │
│  │  database.py · data_ingestion.py · process_parser   │    │
│  │  source_gatherers · url_extractor · auth.py         │    │
│  └──────────────────────┬──────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                   DATA LAYER                                │
│                                                             │
│  ┌───────────────┐    ┌───────────────┐                     │
│  │    SQLite      │    │  PostgreSQL   │                     │
│  │ (Development)  │    │ (Production)  │                     │
│  │  25+ tables    │    │  25+ tables   │                     │
│  └───────────────┘    └───────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│               EXTERNAL SERVICES                             │
│                                                             │
│  ┌──────────┐  ┌─────────────┐  ┌───────────┐              │
│  │  OpenAI  │  │   Finnhub   │  │   Alpha   │              │
│  │ GPT-4o   │  │   Ticker    │  │  Vantage  │              │
│  │ mini/4o  │  │   Search    │  │ Financials│              │
│  │ Embed    │  │   Profiles  │  │           │              │
│  └──────────┘  └─────────────┘  └───────────┘              │
│                                                             │
│  ┌──────────┐  ┌─────────────┐                              │
│  │  Brave   │  │  Jira /     │                              │
│  │  Search  │  │  ServiceNow │                              │
│  └──────────┘  └─────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | Vanilla JavaScript + CSS | ES6+ | Single-page application |
| Backend Framework | FastAPI | 0.115.0 | REST API server |
| ASGI Server | Uvicorn | 0.30.0 | HTTP server |
| Production Server | Gunicorn | 22.0.0 | Process manager |
| Database (Dev) | SQLite via aiosqlite | 0.20.0 | Local development |
| Database (Prod) | PostgreSQL via asyncpg | 0.29+ | Production persistence |
| AI Text Generation | OpenAI GPT-4o-mini | Latest | All AI agents |
| AI Vision | OpenAI GPT-4o | Latest | Process diagram parsing |
| AI Embeddings | OpenAI text-embedding-3-small | Latest | RAG knowledge base |
| Auth | python-jose + bcrypt | 3.3.0 / 4.0+ | JWT + password hashing |
| HTTP Client | httpx | 0.27.0 | External API calls |
| HTML Parsing | BeautifulSoup4 | 4.12+ | URL content extraction |
| PDF Parsing | PyMuPDF | 1.24+ | PDF text extraction |
| Excel Parsing | openpyxl | 3.1+ | Excel file reading |
| Word Parsing | python-docx | 1.0+ | DOCX text extraction |
| Hosting | Render.com | Free tier | Cloud deployment |

### 3.3 Database Design

**Entity Relationship Summary:**

```
organization (1) ──── (N) business_units
organization (1) ──── (N) revenue_splits
organization (1) ──── (N) ops_efficiency
organization (1) ──── (N) competitors
organization (1) ──── (N) org_documents ──── (N) document_chunks
organization (1) ──── (N) generation_runs

business_units (1) ── (N) value_streams
value_streams (1) ─── (N) value_stream_steps
value_streams (1) ─── (N) value_stream_metrics
value_streams (1) ─── (N) value_stream_levers
value_streams (1) ─── (N) value_stream_benchmarks

swot_entries (standalone per org)
tows_actions (standalone per org)

strategies (1) ─────── (N) strategic_okrs ──── (N) strategic_key_results
strategy_inputs (standalone per org)

product_groups (1) ── (N) digital_products
digital_products (1) ─ (N) initiatives
initiatives (1) ────── (N) epics ──── (N) features
epics (N) ─────────── (N) epic_dependencies
features (N) ────────── (N) feature_dependencies

teams (1) ──────────── (N) epics
teams (1) ──────────── (N) product_okrs ──── (N) product_key_results
teams (1) ──────────── (N) delivery_okrs ── (N) delivery_key_results

review_gates (7 per org, one per step)
```

**Key Design Decisions:**
- **No ORM**: Direct SQL queries for full control and portability
- **Dual-database**: SQLite for development simplicity, PostgreSQL for production reliability
- **Placeholder conversion**: `database.py` auto-converts `?` → `$1,$2,...` for PostgreSQL
- **JSON storage**: Complex fields (steps_completed, embedding_json) stored as JSON text
- **Soft dependencies**: Foreign keys used but cascade behavior managed in application code

### 3.4 API Design

**RESTful conventions:**
- `GET /api/step{N}/{resource}` — List resources
- `POST /api/step{N}/{resource}` — Create resource
- `PUT /api/step{N}/{resource}/{id}` — Update resource
- `DELETE /api/step{N}/{resource}/{id}` — Delete resource
- `POST /api/step{N}/auto-generate` — AI generation
- `POST /api/generate-all/start` — Orchestration

**Error handling pattern:**
```python
try:
    # Business logic
    return {"status": "success", "data": result}
except Exception as e:
    import traceback
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))
```

**AI generation pattern:**
```python
@router.post("/auto-generate")
async def auto_generate(db=Depends(get_db)):
    # 1. Gather context from upstream steps
    context = await gather_full_context(db)
    # 2. Check if OpenAI available
    if is_openai_available():
        result = await generate_with_ai(context)
    else:
        result = generate_from_templates(context)
    # 3. Insert results into database
    for item in result:
        await db.execute("INSERT INTO ...", item)
    await db.commit()
    return {"status": "success", "count": len(result)}
```

### 3.5 Security Design

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT tokens (python-jose, HS256 algorithm) |
| Password storage | bcrypt hashing with automatic salting |
| API protection | Bearer token required on all /api/* routes (except /auth/*) |
| CORS | Configurable allowed origins (default: same-origin) |
| Input validation | Pydantic models for request bodies |
| SQL injection | Parameterized queries (never string interpolation) |
| Secret management | Environment variables (never committed to repo) |
| XSS prevention | No user-generated HTML rendered without escaping |

---

## 4. Implementation Details

### 4.1 Project Structure

```
bmad-transform-app/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, routers, migrations
│   ├── database.py                # SQLite/PostgreSQL connection wrapper
│   ├── auth.py                    # JWT + bcrypt authentication
│   │
│   ├── routers/                   # API endpoint handlers
│   │   ├── auth_router.py         #   /api/auth (login, register, verify)
│   │   ├── step1_performance.py   #   /api/step1 (org, BUs, revenue, ops, competitors)
│   │   ├── step1_ai_dashboard.py  #   /api/step1/ai (10 AI capabilities)
│   │   ├── step2_value_streams.py #   /api/step2 (value streams, steps, levers)
│   │   ├── step3_swot_tows.py     #   /api/step3 (SWOT entries, TOWS actions)
│   │   ├── step4_strategy_okrs.py #   /api/step4 (strategies, OKRs, key results)
│   │   ├── step5_initiatives.py   #   /api/step5 (products, initiatives, RICE)
│   │   ├── step6_epics_teams.py   #   /api/step6 (teams, epics, dependencies)
│   │   ├── step7_features.py      #   /api/step7 (features, delivery OKRs)
│   │   ├── review_gates.py        #   /api/gates (review gate CRUD)
│   │   ├── generate_all.py        #   /api/generate-all (orchestration)
│   │   └── documents.py           #   /api/kb (knowledge base, RAG)
│   │
│   ├── ai_dashboard.py            # Step 1 AI analytics (10 capabilities)
│   ├── ai_swot_strategy.py        # Steps 3-4 SWOT, TOWS, strategies, OKRs
│   ├── ai_initiatives.py          # Steps 5-7 initiatives, epics, features
│   ├── ai_research.py             # Value stream research + competitor benchmarks
│   ├── ai_generate_all.py         # End-to-end orchestrator
│   ├── rag_engine.py              # RAG: chunking, embeddings, semantic search
│   ├── openai_client.py           # OpenAI API wrapper + template engine
│   │
│   ├── data_ingestion.py          # External API data fetching
│   ├── process_parser.py          # BPMN/image process extraction
│   ├── url_extractor.py           # Web URL content extraction
│   ├── source_gatherers.py        # Multi-source data collection
│   │
│   └── requirements.txt           # Python dependencies (18 packages)
│
├── frontend/
│   └── index.html                 # Complete SPA (~4,834 lines)
│                                  #   CSS (~900 lines)
│                                  #   HTML structure (~200 lines)
│                                  #   JavaScript (~3,700 lines, ~171 functions)
│
├── database/
│   ├── schema.sql                 # SQLite schema (531 lines, 25+ tables)
│   └── schema_postgres.sql        # PostgreSQL schema (kept in sync)
│
├── docs/
│   ├── 01-Agent-Catalog.md        # All 13 agents documented
│   ├── 02-Platform-Workflow.md    # End-to-end workflow documentation
│   └── 03-SDLC-Documentation.md  # This document
│
├── seed_test_data.sh              # Apple Inc. test data (49KB)
├── seed_ing_bank.sh               # ING Bank test data (71KB)
├── seed_telstra_health.sh         # Telstra Health test data (68KB)
├── seed_usbank.sh                 # US Bank test data (67KB)
│
├── render.yaml                    # Render.com deployment config
├── .gitignore                     # Git ignore rules
└── README.md                      # Project readme
```

### 4.2 Module Descriptions

| Module | Lines | Purpose |
|--------|-------|---------|
| `main.py` | ~800 | App setup, middleware, router registration, database migrations |
| `database.py` | ~180 | Unified SQLite/PostgreSQL wrapper with placeholder conversion |
| `auth.py` | ~120 | JWT token creation/verification, bcrypt password hashing |
| `openai_client.py` | ~600 | OpenAI API wrapper, template engine, JSON parsing |
| `ai_dashboard.py` | ~1,100 | 10 AI dashboard capabilities with caching |
| `ai_swot_strategy.py` | ~500 | SWOT/TOWS/Strategy/OKR generation |
| `ai_initiatives.py` | ~700 | Initiative/Epic/Feature generation with scoring |
| `ai_research.py` | ~300 | Value stream research + competitor benchmarking |
| `ai_generate_all.py` | ~500 | 7-step orchestrator with progress tracking |
| `rag_engine.py` | ~250 | Document chunking, embeddings, semantic search |
| `data_ingestion.py` | ~350 | Finnhub + Alpha Vantage API integration |
| `process_parser.py` | ~200 | BPMN/image parsing with GPT-4o Vision |
| `source_gatherers.py` | ~400 | 8 configurable data source gatherers |
| `url_extractor.py` | ~100 | Web content fetching and extraction |
| `frontend/index.html` | ~4,834 | Complete SPA (CSS + HTML + JS) |

### 4.3 Key Design Patterns

**1. Graceful Degradation:**
Every AI-dependent feature has a template/rule-based fallback:
```
OpenAI available?  →  Yes: AI generation with GPT-4o-mini
                   →  No:  Template-based generation (deterministic)
```

**2. Context Cascading:**
Each step aggregates all upstream data as context for AI:
```python
async def gather_full_context(db):
    org = await db.execute_fetchone("SELECT * FROM organization")
    bus = await db.execute_fetchall("SELECT * FROM business_units")
    # ... gather all upstream data
    return {"org": org, "business_units": bus, ...}
```

**3. Dual-Database Abstraction:**
```python
# database.py converts automatically:
SQLite:     "SELECT * FROM t WHERE id = ? AND name = ?"
PostgreSQL: "SELECT * FROM t WHERE id = $1 AND name = $2"
```

**4. Background Task Pattern:**
```python
# Long-running AI generation runs as background task
@router.post("/start")
async def start_generation(data: dict, db=Depends(get_db)):
    run_id = await create_run_record(db)
    asyncio.create_task(run_generation(run_id, db))  # non-blocking
    return {"run_id": run_id, "status": "running"}
```

**5. AI Result Caching:**
```python
# Hash input data → check cache → generate if miss → store result
cache_key = hashlib.md5(json.dumps(input_data).encode()).hexdigest()
cached = await db.execute_fetchone("SELECT * FROM ai_analysis_cache WHERE cache_key = ?", [cache_key])
if cached and not expired:
    return json.loads(cached["result_json"])
```

---

## 5. Testing Strategy

### 5.1 Testing Approach

The platform uses a pragmatic testing approach combining seed data scripts for integration testing with manual review gates for quality assurance.

### 5.2 Seed Data Scripts (Integration Tests)

Four comprehensive seed scripts simulate end-to-end workflows:

| Script | Company | Industry | Size |
|--------|---------|----------|------|
| `seed_test_data.sh` | Apple Inc. | Technology | 49KB |
| `seed_ing_bank.sh` | ING Bank | Financial Services | 71KB |
| `seed_telstra_health.sh` | Telstra Health | Healthcare IT | 68KB |
| `seed_usbank.sh` | US Bank | Financial Services | 67KB |

**What each script tests:**
1. Organization creation (POST /api/step1/organization)
2. Business unit creation (POST /api/step1/business-units)
3. Revenue split insertion (POST /api/step1/revenue-splits)
4. Ops metric creation (POST /api/step1/ops-efficiency)
5. Competitor creation (POST /api/step1/competitors)
6. Value stream creation with steps (POST /api/step2/value-streams)
7. SWOT entry creation (POST /api/step3/swot)
8. TOWS action creation (POST /api/step3/tows)
9. Strategy creation (POST /api/step4/strategies)
10. OKR and key result creation (POST /api/step4/strategic-okrs)
11. Product group and digital product creation (POST /api/step5/*)
12. Initiative creation with RICE scores (POST /api/step5/initiatives)
13. Team creation (POST /api/step6/teams)
14. Epic creation with dependencies (POST /api/step6/epics)
15. Feature creation (POST /api/step7/features)
16. Review gate approval (PUT /api/gates/*)

**Usage:**
```bash
# Test against local server
bash seed_test_data.sh http://localhost:8000

# Test against production
bash seed_test_data.sh https://business-transformation-architect.onrender.com
```

### 5.3 Manual Testing Checklist

#### Authentication
- [ ] Register new user with valid email/password
- [ ] Login with registered credentials
- [ ] Token persists across page refresh
- [ ] Expired token redirects to login

#### Step 1: Performance Dashboard
- [ ] Create organization with name + industry
- [ ] Search for public company ticker (e.g., "Apple")
- [ ] Fetch API data (Finnhub + Alpha Vantage)
- [ ] Upload CSV/Excel file
- [ ] Extract data from web URL
- [ ] View business units, revenue, ops, competitors
- [ ] Run AI financial analysis
- [ ] Run AI executive summary
- [ ] Run natural language query

#### Step 2: Value Streams
- [ ] Create value stream manually
- [ ] Generate value stream from template
- [ ] Pull from multiple sources
- [ ] Upload process image (GPT-4o Vision)
- [ ] View flow diagram with timing
- [ ] Generate competitor benchmarks
- [ ] Identify improvement levers

#### Steps 3-7
- [ ] Auto-generate SWOT + TOWS (Step 3)
- [ ] Auto-generate strategies + OKRs (Step 4)
- [ ] Auto-generate initiatives with RICE (Step 5)
- [ ] Auto-generate epics with team assignment (Step 6)
- [ ] Auto-generate features with acceptance criteria (Step 7)
- [ ] View quarterly roadmap (Step 7)

#### Orchestration
- [ ] "Generate All Steps" creates complete plan
- [ ] Progress overlay shows step-by-step status
- [ ] All 7 steps have data after generation
- [ ] Review gates show pending status
- [ ] Can approve each gate with reviewer name

#### Knowledge Base
- [ ] Upload document (PDF/TXT/CSV)
- [ ] View document list with chunk counts
- [ ] Semantic search returns relevant results
- [ ] Delete document removes chunks
- [ ] Toggle Demo/Live mode
- [ ] Live mode RAG enriches AI generation

### 5.4 API Testing

All API endpoints can be tested via `curl` or any HTTP client:

```bash
# Health check
curl https://business-transformation-architect.onrender.com/api/step1/organization

# Test KB upload
curl -X POST .../api/kb/upload \
  -F "file=@document.pdf" \
  -F "category=strategy" \
  -F "description=Annual strategy report"

# Test semantic search
curl -X POST .../api/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "digital transformation strategy", "limit": 5}'

# Test Generate All
curl -X POST .../api/generate-all/start \
  -H "Content-Type: application/json" \
  -d '{"org_id": 1}'

# Poll progress
curl .../api/generate-all/status/1
```

---

## 6. Deployment & Operations

### 6.1 Deployment Architecture

```
┌──────────────┐     ┌──────────────────────────────┐
│   GitHub     │────▶│        Render.com             │
│   Repository │     │                                │
│              │     │  ┌────────────────────────┐    │
│  main branch │     │  │   Web Service          │    │
│              │     │  │   Python 3.12          │    │
│              │     │  │   Uvicorn + Gunicorn   │    │
│              │     │  │   Port: $PORT          │    │
│              │     │  └───────────┬────────────┘    │
│              │     │              │                  │
│              │     │  ┌───────────▼────────────┐    │
│              │     │  │   PostgreSQL 16        │    │
│              │     │  │   (Free tier)          │    │
│              │     │  │   bta_production DB    │    │
│              │     │  └────────────────────────┘    │
│              │     │                                │
│              │     │  Environment Variables:         │
│              │     │  - DATABASE_URL (auto)          │
│              │     │  - OPENAI_API_KEY              │
│              │     │  - FINNHUB_API_KEY             │
│              │     │  - ALPHA_VANTAGE_API_KEY       │
│              │     │  - SECRET_KEY                  │
│              │     └────────────────────────────────┘
└──────────────┘
```

### 6.2 Deployment Configuration (render.yaml)

```yaml
databases:
  - name: bta-db
    plan: free
    databaseName: bta_production
    user: bta_user
    postgresMajorVersion: "16"

services:
  - type: web
    name: business-transformation-architect
    runtime: python
    plan: free
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bta-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: "3.12"
```

### 6.3 Deployment Process

```
Developer                    GitHub                     Render
────────                    ──────                     ──────
   │                           │                          │
   ├── git push main ─────────▶│                          │
   │                           │                          │
   │                           ├── Webhook trigger ──────▶│
   │                           │                          │
   │                           │       ┌──── Build ────┐  │
   │                           │       │ pip install    │  │
   │                           │       │ requirements   │  │
   │                           │       └───────────────┘  │
   │                           │                          │
   │                           │       ┌──── Deploy ───┐  │
   │                           │       │ Start uvicorn  │  │
   │                           │       │ Run migrations │  │
   │                           │       │ Serve app      │  │
   │                           │       └───────────────┘  │
   │                           │                          │
   │◀───────────── Live at URL ─────────────────────────│
```

**Manual deploy trigger:**
```bash
curl -s -X POST \
  'https://api.render.com/v1/services/srv-d6ahm9vpm1nc73dbosc0/deploys' \
  -H 'Authorization: Bearer rnd_yo0YyQ8SwyzPKMYlPCLH7OToHEXX' \
  -H 'Content-Type: application/json' \
  -d '{"clearCache":"do_not_clear"}'
```

### 6.4 Database Migration Strategy

Migrations run automatically on application startup:

```python
# main.py startup event
@app.on_event("startup")
async def startup():
    if USE_POSTGRES:
        await _migrate_postgres()   # Full schema + ALTER TABLE additions
    else:
        await _migrate_sqlite()     # Incremental column additions
```

**PostgreSQL migration pattern:**
1. Execute full `schema_postgres.sql` (all CREATE TABLE IF NOT EXISTS)
2. Run ALTER TABLE statements for any columns added since initial schema
3. Defensive: catches "column already exists" errors silently

**SQLite migration pattern:**
1. Check if tables exist (PRAGMA table_info)
2. Add missing columns incrementally
3. Rebuild tables if foreign key structure changes

### 6.5 Monitoring & Observability

| Aspect | Implementation |
|--------|---------------|
| Application logs | Render dashboard log viewer (stdout/stderr) |
| Error tracking | Python traceback output to logs |
| Health check | `GET /api/step1/organization` (returns 200 if healthy) |
| Generation tracking | `generation_runs` table with status and timestamps |
| AI cost tracking | Token counts logged per OpenAI API call |
| Uptime monitoring | Render's built-in health checks |

### 6.6 Environment Variables

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `DATABASE_URL` | Yes (prod) | Render auto-set | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Render generated | JWT signing key |
| `OPENAI_API_KEY` | Yes (for AI) | Manual | OpenAI API access |
| `FINNHUB_API_KEY` | Optional | Manual | Company ticker search |
| `ALPHA_VANTAGE_API_KEY` | Optional | Manual | Financial data |
| `BRAVE_SEARCH_API_KEY` | Optional | Manual | Web search |
| `PYTHON_VERSION` | Yes | render.yaml | Runtime version |
| `ALLOWED_ORIGINS` | Optional | Manual | CORS origins (comma-separated) |

---

## 7. Maintenance & Support

### 7.1 Adding a New Step

To add a new transformation step (e.g., Step 8):

1. **Database**: Add tables to both `schema.sql` and `schema_postgres.sql`
2. **Backend**: Create `backend/routers/step8_*.py` with CRUD + auto-generate endpoints
3. **AI module**: Add generation functions to existing AI module or create new one
4. **Frontend**: Add Step 8 section in `index.html` with:
   - Sidebar navigation item
   - Content rendering function `loadStep8()`
   - API integration functions
5. **Main.py**: Register new router + add migration statements
6. **Orchestrator**: Add Step 8 to `ai_generate_all.py` sequence
7. **Review gate**: Add Gate 8 configuration
8. **Seed scripts**: Add Step 8 data to all 4 seed scripts

### 7.2 Adding a New Data Source

To add a new external data source (e.g., Bloomberg):

1. **Source gatherer**: Add `gather_bloomberg()` function in `source_gatherers.py`
2. **Router**: Add source name to `VALID_SOURCES` and `GATHERER_MAP` in relevant step router
3. **Frontend**: Add checkbox option in pull-sources dialog
4. **Environment**: Document required API key

### 7.3 Adding a New AI Capability

To add a new AI dashboard capability:

1. **AI module**: Add function in `ai_dashboard.py` (follow existing pattern)
2. **Router**: Add endpoint in `step1_ai_dashboard.py`
3. **Frontend**: Add capability card in AI Dashboard section
4. **Caching**: Use `ai_analysis_cache` table for expensive operations

### 7.4 Schema Changes

When modifying the database schema:

1. Update `database/schema.sql` (SQLite)
2. Update `database/schema_postgres.sql` (PostgreSQL)
3. Add ALTER TABLE migration in `main.py` → `_migrate_postgres()` and `_migrate_sqlite()`
4. Test locally (SQLite) then deploy (PostgreSQL)
5. **Keep both schema files in sync**

### 7.5 Common Issues & Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 500 on org creation | FK constraints (org_documents, generation_runs) | Cascade delete dependent tables first |
| AI generation returns template data | OPENAI_API_KEY not set or expired | Check env var on Render dashboard |
| Embeddings not generated | OpenAI API unavailable | Falls back to keyword search automatically |
| Database not persisting | DATABASE_URL not set on Render | Set internal PostgreSQL connection string |
| CORS errors | Frontend origin not in ALLOWED_ORIGINS | Add origin to env var |
| Slow cold start | Render free tier spins down after 15 min | First request takes ~30 sec to wake |

### 7.6 Performance Considerations

| Area | Current State | Optimization Path |
|------|--------------|-------------------|
| AI generation | Sequential (30-60s) | Parallelize independent steps |
| Database queries | Direct SQL | Add indexes for frequent queries |
| Frontend bundle | Single 4,834-line file | Split into modules, add build step |
| Embedding storage | JSON text in SQL | Move to vector database (pgvector) |
| Caching | Per-request hash-based | Add Redis for shared caching |
| File parsing | In-memory | Stream large files |

---

## 8. Appendices

### 8.1 API Endpoint Reference

**Total: 133+ endpoints across 12 routers**

| Router | Prefix | Endpoints | Key Methods |
|--------|--------|-----------|-------------|
| Auth | `/api/auth` | 5 | register, login, verify, me, logout |
| Step 1 Performance | `/api/step1` | 15 | org CRUD, data ingestion, file upload, API fetch |
| Step 1 AI Dashboard | `/api/step1/ai` | 13 | financial analysis, trends, anomalies, NLQ, scenarios |
| Step 2 Value Streams | `/api/step2` | 15 | value stream CRUD, generation, parsing, benchmarks |
| Step 3 SWOT/TOWS | `/api/step3` | 6 | SWOT CRUD, TOWS CRUD, auto-generate |
| Step 4 Strategy | `/api/step4` | 17 | strategy CRUD, OKR CRUD, key results, data sources |
| Step 5 Initiatives | `/api/step5` | 10 | products, initiatives, RICE scoring, roadmap |
| Step 6 Epics | `/api/step6` | 13 | teams, epics, dependencies, product OKRs |
| Step 7 Features | `/api/step7` | 11 | features, delivery OKRs, dependencies, roadmap |
| Review Gates | `/api/gates` | 5 | list, get, create, approve/reject |
| Generate All | `/api/generate-all` | 4 | start, status, retry, latest |
| Knowledge Base | `/api/kb` | 7 | upload, list, search, delete, data-mode |

### 8.2 Database Tables Reference

| Table | Step | Records per Org (typical) |
|-------|------|--------------------------|
| organization | 0 | 1 |
| users | 0 | 1-5 |
| business_units | 1 | 3-6 |
| revenue_splits | 1 | 15-30 |
| ops_efficiency | 1 | 10-20 |
| competitors | 1 | 3-5 |
| value_streams | 2 | 3-5 |
| value_stream_steps | 2 | 20-40 |
| value_stream_metrics | 2 | 3-5 |
| value_stream_levers | 2 | 12-20 |
| value_stream_benchmarks | 2 | 6-15 |
| swot_entries | 3 | 12-20 |
| tows_actions | 3 | 8-16 |
| strategy_inputs | 4 | 4-5 |
| strategies | 4 | 10-16 |
| strategic_okrs | 4 | 10-20 |
| strategic_key_results | 4 | 20-40 |
| product_groups | 5 | 3-5 |
| digital_products | 5 | 6-12 |
| initiatives | 5 | 15-25 |
| teams | 6 | 4-6 |
| epics | 6 | 30-60 |
| epic_dependencies | 6 | 10-20 |
| product_okrs | 6 | 4-8 |
| product_key_results | 6 | 8-16 |
| features | 7 | 60-150 |
| feature_dependencies | 7 | 15-30 |
| delivery_okrs | 7 | 4-8 |
| delivery_key_results | 7 | 8-16 |
| review_gates | All | 7 |
| generation_runs | All | 1-5 |
| org_documents | KB | 0-20 |
| document_chunks | KB | 0-200 |
| ai_analysis_cache | 1 | 5-15 |

### 8.3 AI Model Usage

| Model | Used By | Purpose | Cost per Call |
|-------|---------|---------|---------------|
| GPT-4o-mini | All 13 agents | Text generation, analysis, synthesis | ~$0.003-0.01 |
| GPT-4o | Process Parser | Vision-based diagram extraction | ~$0.01-0.03 |
| text-embedding-3-small | RAG Engine | Document chunk embeddings | ~$0.00002 per chunk |

**Estimated cost per full transformation plan:** $0.03-0.05

### 8.4 Glossary

| Term | Definition |
|------|-----------|
| **BMAD** | Business Model Architecture Design |
| **BU** | Business Unit — organizational division |
| **RICE** | Reach, Impact, Confidence, Effort — prioritization framework |
| **OKR** | Objective and Key Result — goal-setting framework |
| **SWOT** | Strengths, Weaknesses, Opportunities, Threats — analysis framework |
| **TOWS** | Reverse SWOT matrix mapping threats/opportunities to strengths/weaknesses |
| **RAG** | Retrieval-Augmented Generation — grounding AI with document context |
| **SPA** | Single Page Application — frontend architecture |
| **JWT** | JSON Web Token — authentication mechanism |
| **HITL** | Human-In-The-Loop — human review checkpoints |
| **Flow Efficiency** | Process time / Lead time × 100% |
| **Lead Time** | Total time from start to completion (process + wait) |
| **Lever** | Improvement opportunity in a value stream |
| **Gate** | Review checkpoint requiring human approval |
| **Embedding** | Numerical vector representation of text for similarity search |
| **Chunk** | Fixed-size text segment for embedding and retrieval |
