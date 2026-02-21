# Platform Workflow — BMAD Multi-Agent Transformation Platform

## How the Platform Works

The BMAD Business Transformation Architect guides organizations through a **7-step strategic transformation process**. Each step builds on the outputs of previous steps, creating a cascading pipeline from raw business data to a fully prioritized feature roadmap.

Users can either:
- **Step-by-step**: Work through each step manually, using AI assistance as needed
- **Generate All**: One-click end-to-end AI generation of all 7 steps, then review and refine

---

## End-to-End Workflow Diagram

```
                          ┌─────────────────────────┐
                          │     USER ENTRY POINT     │
                          │  Login / Register        │
                          └───────────┬─────────────┘
                                      │
                          ┌───────────▼─────────────┐
                          │    ORGANIZATION SETUP    │
                          │  Company Name + Industry │
                          │  + Competitor Names      │
                          └───────────┬─────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     │                │                 │
              ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
              │  Knowledge  │  │  Generate   │  │  Step-by-   │
              │  Base Upload│  │  All Steps  │  │  Step Mode  │
              │  (Optional) │  │  (One-Click)│  │  (Manual)   │
              └──────┬──────┘  └─────┬──────┘  └──────┬──────┘
                     │               │                 │
                     └───────────────┼─────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                TRANSFORMATION PIPELINE              │
          │                                                     │
          │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
          │  │ STEP 1   │───▶│ STEP 2   │───▶│ STEP 3   │      │
          │  │ Perform. │    │ Value    │    │ SWOT /   │      │
          │  │ Dashboard│    │ Streams  │    │ TOWS     │      │
          │  └──────────┘    └──────────┘    └──────────┘      │
          │       │               │               │             │
          │       ▼               ▼               ▼             │
          │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
          │  │ Gate 1   │    │ Gate 2   │    │ Gate 3   │      │
          │  │ Review   │    │ Review   │    │ Review   │      │
          │  └──────────┘    └──────────┘    └──────────┘      │
          │                                       │             │
          │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
          │  │ STEP 4   │───▶│ STEP 5   │───▶│ STEP 6   │      │
          │  │ Strategy │    │ Digital  │    │ Epics &  │      │
          │  │ & OKRs   │    │ Initiat. │    │ Teams    │      │
          │  └──────────┘    └──────────┘    └──────────┘      │
          │       │               │               │             │
          │       ▼               ▼               ▼             │
          │  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
          │  │ Gate 4   │    │ Gate 5   │    │ Gate 6   │      │
          │  │ Review   │    │ Review   │    │ Review   │      │
          │  └──────────┘    └──────────┘    └──────────┘      │
          │                                       │             │
          │                                  ┌──────────┐      │
          │                                  │ STEP 7   │      │
          │                                  │ Features │      │
          │                                  │ & Roadmap│      │
          │                                  └──────────┘      │
          │                                       │             │
          │                                  ┌──────────┐      │
          │                                  │ Gate 7   │      │
          │                                  │ Review   │      │
          │                                  └──────────┘      │
          └─────────────────────────────────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  TRANSFORMATION     │
                          │  PLAN COMPLETE      │
                          │  (All 7 Gates       │
                          │   Approved)         │
                          └─────────────────────┘
```

---

## Step-by-Step Workflow Detail

### Step 0: Authentication & Organization Setup

**What happens:**
1. User registers or logs in (JWT token-based authentication)
2. User creates an organization profile: company name, industry, competitor names
3. System checks if the company is publicly traded (for API data availability)
4. User optionally switches from Demo mode to Live mode and uploads Knowledge Base documents

**Data created:**
- `organization` record (name, industry, ticker, data_mode)
- Optional: `org_documents` + `document_chunks` (for RAG)

**Frontend flow:**
```
Login Screen → Org Setup Form → Submit → Phase transitions to Data Ingestion
```

---

### Step 1: Business Performance Dashboard

**Purpose:** Establish the organization's current financial and operational baseline.

**Workflow:**

```
Organization Created
    │
    ├─ Phase 1: Data Ingestion Hub
    │   ├─ API Ingestion (Public companies)
    │   │   ├─ Finnhub: Ticker search → Company profile → Peer discovery
    │   │   └─ Alpha Vantage: Revenue, margins, profitability ratios
    │   │
    │   ├─ File Upload (Any company)
    │   │   ├─ CSV/Excel → Auto-detect table type (BUs, revenue, ops, competitors)
    │   │   ├─ PDF/DOCX → Text extraction → AI parsing
    │   │   └─ Images → GPT-4o Vision OCR → structured data
    │   │
    │   ├─ URL Extraction
    │   │   ├─ Fetch web page → BeautifulSoup parsing
    │   │   └─ AI extracts financial data from text
    │   │
    │   └─ Manual Entry
    │       └─ Add business units, revenue splits, ops metrics, competitors directly
    │
    ├─ Phase 2: Data Analysis
    │   ├─ Business unit breakdown with metrics
    │   ├─ Revenue splits by product/region/segment (multi-year)
    │   ├─ Operational efficiency KPIs (margins, ROE, ROA, EPS)
    │   └─ Competitor comparison tables
    │
    └─ Phase 3: AI Dashboard (10 capabilities)
        ├─ Financial Health Scoring (0-100 score with breakdown)
        ├─ AI Competitor Discovery (find similar companies)
        ├─ Trend Analysis (revenue growth/decline forecasting)
        ├─ Anomaly Detection (statistical outliers in KPIs)
        ├─ Executive Summary (comprehensive health report)
        ├─ Data Enrichment Suggestions (missing data recommendations)
        ├─ Transformation Readiness Score (digital readiness assessment)
        ├─ Natural Language Queries (ask questions about data)
        ├─ What-If Scenarios (revenue/cost change modeling)
        └─ Report Generation (downloadable markdown report)
```

**Data produced:** `business_units`, `revenue_splits`, `ops_efficiency`, `competitors`
**Gate 1:** Review dashboard metrics, approve performance baseline

---

### Step 2: Value Stream Analysis

**Purpose:** Map current business processes, identify bottlenecks, and benchmark against competitors.

**Workflow:**

```
Step 1 Data Available
    │
    ├─ Create Value Streams (3-4 per organization)
    │   ├─ AI auto-determine industry-relevant segments
    │   │   e.g., Banking: "Loan Processing", "Account Opening", "Claims"
    │   └─ Or manually name segments
    │
    ├─ For each Value Stream:
    │   │
    │   ├─ Data Gathering (8 configurable sources)
    │   │   ├─ app_data: Existing org records
    │   │   ├─ erp_simulation: Simulated ERP/CRM data
    │   │   ├─ industry_benchmarks: Standard KPIs
    │   │   ├─ finnhub: Competitor financial data
    │   │   ├─ web_search: Live market research
    │   │   ├─ openai_research: AI synthesis of all sources
    │   │   ├─ competitor_operations: AI competitor benchmarking
    │   │   ├─ jira / servicenow: (if configured)
    │   │   └─ RAG context injection (Live mode only)
    │   │
    │   ├─ Process Mapping
    │   │   ├─ 6-10 process steps with types (trigger/process/decision/delivery)
    │   │   ├─ Process time and wait time per step (hours)
    │   │   └─ Bottleneck identification
    │   │
    │   ├─ Metrics Calculation
    │   │   ├─ Total lead time = sum of (process_time + wait_time)
    │   │   ├─ Total process time = sum of process_time only
    │   │   ├─ Total wait time = sum of wait_time only
    │   │   └─ Flow efficiency = process_time / lead_time × 100%
    │   │
    │   ├─ Improvement Levers (4 categories)
    │   │   ├─ Growth: Revenue expansion opportunities
    │   │   ├─ Efficiency: Cost reduction and automation
    │   │   ├─ Experience: Customer satisfaction improvements
    │   │   └─ Effectiveness: Quality and accuracy gains
    │   │
    │   └─ Competitor Benchmarks
    │       ├─ Process comparisons (lead time, automation level)
    │       ├─ Technology stack analysis
    │       └─ Industry best practices
    │
    └─ Alternative Input Methods
        ├─ Upload BPMN/XML process diagrams
        ├─ Upload screenshots/images (GPT-4o Vision extraction)
        ├─ Extract from web URLs
        └─ Import CSV/JSON data
```

**Data produced:** `value_streams`, `value_stream_steps`, `value_stream_metrics`, `value_stream_levers`, `value_stream_benchmarks`
**Gate 2:** Refine opportunity levers, approve value stream analysis

---

### Step 3: SWOT to TOWS Action Engine

**Purpose:** Identify strategic problems and convert them into actionable strategies.

**Workflow:**

```
Steps 1-2 Data Available
    │
    ├─ Context Aggregation
    │   ├─ Financial metrics from Step 1
    │   ├─ Value stream efficiency gaps from Step 2
    │   ├─ Competitor advantages/weaknesses
    │   ├─ High-impact improvement levers
    │   └─ RAG context (if Live mode)
    │
    ├─ SWOT Generation (AI or manual)
    │   ├─ Strengths (3-5 entries) — Internal advantages
    │   ├─ Weaknesses (3-5 entries) — Internal disadvantages
    │   ├─ Opportunities (3-5 entries) — External favorable factors
    │   └─ Threats (3-5 entries) — External unfavorable factors
    │   Each entry has: description, severity (1-5), confidence (1-5)
    │
    └─ TOWS Action Mapping
        ├─ SO (Maxi-Maxi): Use Strengths to capture Opportunities
        ├─ WO (Mini-Maxi): Overcome Weaknesses to capture Opportunities
        ├─ ST (Maxi-Mini): Use Strengths to mitigate Threats
        └─ WT (Mini-Mini): Minimize Weaknesses to avoid Threats
        Each action has: description, priority (high/medium/low), impact_score
```

**Data produced:** `swot_entries`, `tows_actions`
**Gate 3:** Validate SWOT entries, approve TOWS strategies

---

### Step 4: Four-Layer Strategy & Strategic OKRs

**Purpose:** Create a multi-dimensional strategy with measurable objectives.

**Workflow:**

```
TOWS Actions Available
    │
    ├─ Strategy Inputs (User-provided context)
    │   ├─ Business Strategy: Market positioning, growth plans
    │   ├─ Digital Strategy: Technology vision, digital channels
    │   ├─ Data Strategy: Data governance, analytics roadmap
    │   ├─ Gen AI Strategy: AI/ML capabilities, automation plans
    │   └─ Competitor Strategy: Competitive response plans
    │
    ├─ Strategy Generation (4 layers)
    │   ├─ Business Strategy (Green): Market positioning, growth
    │   ├─ Digital Strategy (Blue): Technology platforms, digital channels
    │   ├─ Data Strategy (Orange): Data governance, analytics
    │   └─ Gen AI Strategy (Purple): AI/ML, intelligent automation
    │   Each strategy has: description, risk_level, risks, approval status
    │
    ├─ Strategic OKR Creation
    │   ├─ 2-3 Objectives per strategy
    │   │   e.g., "Reduce loan processing time by 70%"
    │   └─ 2-4 Key Results per objective
    │       ├─ Target value (e.g., "< 8 hours")
    │       ├─ Optimistic target (e.g., "< 6 hours")
    │       ├─ Pessimistic target (e.g., "< 12 hours")
    │       ├─ Current value (baseline)
    │       └─ Rationale for target
    │
    └─ Strategy Approval
        └─ User approves/rejects each strategy before it feeds Step 5
```

**Data produced:** `strategy_inputs`, `strategies`, `strategic_okrs`, `strategic_key_results`
**Gate 4:** Review strategies, approve Strategic OKRs

---

### Step 5: Digital Initiatives & RICE Prioritization

**Purpose:** Convert approved strategies into prioritized digital product initiatives.

**Workflow:**

```
Approved Strategies + OKRs Available
    │
    ├─ Product Group Creation
    │   └─ Logical groupings (e.g., "Digital Lending", "Customer Platform", "Data Analytics")
    │
    ├─ Digital Product Mapping
    │   └─ Products within groups (e.g., "Mobile Lending App", "Customer 360 Dashboard")
    │
    ├─ Initiative Generation (15-25 per org)
    │   ├─ Linked to approved strategies
    │   ├─ Linked to digital products
    │   └─ Each initiative has description + AI rationale
    │
    ├─ RICE Scoring
    │   ├─ Reach (1-10): Users/processes affected
    │   ├─ Impact (0.25-3.0): Degree of improvement
    │   ├─ Confidence (0.5-1.0): Estimate certainty
    │   ├─ Effort (1-10): Person-months of work
    │   └─ Score = (Reach × Impact × Confidence) / Effort
    │
    ├─ Manual Override
    │   └─ User can override RICE score with rationale
    │
    └─ Roadmap Phasing (8 quarters / 2 years)
        ├─ Quick Wins: High score, low effort
        ├─ Strategic: High score, high effort
        └─ Long-Term: Future potential
```

**Data produced:** `product_groups`, `digital_products`, `initiatives`
**Gate 5:** RICE manual override complete, approve initiative list

---

### Step 6: Epic & Team Collaboration + Product OKRs

**Purpose:** Break initiatives into delivery epics, form teams, and set product-level OKRs.

**Workflow:**

```
Initiatives + Product Groups Available
    │
    ├─ Team Creation (4-6 teams)
    │   ├─ AI recommends team structure based on work breakdown
    │   └─ e.g., "Digital Lending Team", "Platform Engineering", "Data Science"
    │
    ├─ Epic Generation (2-4 per initiative)
    │   ├─ Cross-layer dependencies: Gen AI → Data → Digital → Business
    │   ├─ Effort estimation (days)
    │   ├─ Priority scoring: (value × size) / effort
    │   └─ Status tracking: draft → in_progress → done
    │
    ├─ Team Assignment
    │   └─ AI maps epics to best-fit teams based on capability
    │
    ├─ Dependency Mapping
    │   ├─ blocks / blocked_by relationships between epics
    │   └─ Critical path identification
    │
    ├─ Product OKR Generation
    │   ├─ Cascaded from Strategic OKRs (Step 4)
    │   └─ Team-level key results with targets
    │
    └─ Quarterly Roadmap (4 quarters / 1 year)
        └─ Epics distributed across quarters by priority
```

**Data produced:** `teams`, `epics`, `epic_dependencies`, `product_okrs`, `product_key_results`
**Gate 6:** Review team dependencies, approve Product OKRs

---

### Step 7: Feature Backlog & Delivery OKRs

**Purpose:** Create detailed feature specifications with acceptance criteria and a quarterly delivery roadmap.

**Workflow:**

```
Epics + Teams Available
    │
    ├─ Feature Generation (2-5 per epic)
    │   ├─ Detailed description
    │   ├─ Acceptance criteria (Given/When/Then format)
    │   ├─ Priority scoring: (value × size) / effort
    │   ├─ Risk level assessment
    │   └─ Status tracking: draft → in_progress → done
    │
    ├─ Feature Dependencies
    │   ├─ blocks / blocked_by relationships
    │   └─ Cross-epic dependency tracking
    │
    ├─ Delivery OKR Generation
    │   ├─ Team-level execution objectives
    │   └─ Sprint/quarter-aligned key results
    │
    └─ Quarterly Feature Roadmap (4 quarters / 1 year)
        ├─ Features organized by quarter
        ├─ Linked to: Epic → Initiative → Product → Strategy
        └─ Color-coded by strategy layer
```

**Data produced:** `features`, `feature_dependencies`, `delivery_okrs`, `delivery_key_results`
**Gate 7:** Review Delivery OKRs, approve final roadmap

---

## Generate All — One-Click End-to-End Flow

When the user clicks "Generate All Steps", the Orchestrator Agent runs the entire pipeline automatically:

```
User clicks "Generate All Steps"
    │
    ├─ Backend creates generation_runs record (status: running)
    ├─ Frontend opens progress overlay modal
    │
    ├─ Step 1: Business Data (~5 sec)
    │   ├─ Public company? → API ingestion (Finnhub + Alpha Vantage)
    │   └─ Private company? → AI generates synthetic BUs, revenue, metrics, competitors
    │
    ├─ Step 2: Value Streams (~8 sec)
    │   ├─ AI determines 3-4 industry-relevant segment names
    │   └─ For each: generates steps, metrics, benchmarks
    │
    ├─ Step 3: SWOT / TOWS (~5 sec)
    │   └─ Generates SWOT entries + TOWS actions from Steps 1-2 context
    │
    ├─ Step 4: Strategies & OKRs (~5 sec)
    │   └─ Creates 4-layer strategies + cascading OKRs + key results
    │
    ├─ Step 5: Initiatives (~5 sec)
    │   └─ Creates product groups, products, RICE-scored initiatives
    │
    ├─ Step 6: Epics & Teams (~5 sec)
    │   └─ Creates teams, generates epics, maps dependencies
    │
    ├─ Step 7: Features & Roadmap (~5 sec)
    │   └─ Creates features with acceptance criteria + quarterly roadmap
    │
    └─ Creates 7 review gates (all status: pending)
```

**Progress tracking:** Frontend polls `/api/generate-all/status/{run_id}` every 2 seconds
**Error recovery:** If a step fails, generation continues; user can retry failed steps
**Duration:** ~30-60 seconds total
**Cost:** ~$0.03-0.05 per full generation (GPT-4o-mini)

---

## Human-in-the-Loop Review Flow

After AI generation (whether step-by-step or Generate All), users enter a review cycle:

```
AI Generation Complete
    │
    ├─ Review Wizard Opens
    │   ├─ 7 step cards showing generated item counts
    │   └─ Each card: "Review & Edit" + "Approve" buttons
    │
    ├─ For Each Step:
    │   ├─ Navigate to step's detail page
    │   ├─ Review AI-generated content (tagged with ai_generated = 1)
    │   ├─ Edit, delete, or add entries manually
    │   ├─ Re-generate individual step if needed
    │   └─ Click "Approve" → review gate status = approved
    │       ├─ Enter reviewer name
    │       └─ Add optional review notes
    │
    ├─ Progress Tracking
    │   └─ Sidebar shows: "X/7 steps approved" with color indicators
    │       ├─ Green checkmark: Approved
    │       ├─ Yellow circle: Pending review
    │       └─ Red X: Rejected (needs revision)
    │
    └─ All 7 Gates Approved → Transformation Plan Complete
```

---

## Data Flow Between Steps

Each step's output feeds into the next step's AI context:

```
Step 1 Output                    Step 2 Input
─────────────────                ─────────────────
Business Units        ─────▶    Segment context for value streams
Revenue Splits        ─────▶    Financial baseline for benchmarks
Ops Efficiency        ─────▶    Current process performance
Competitors           ─────▶    Competitor comparison data

Step 2 Output                    Step 3 Input
─────────────────                ─────────────────
Value Stream Steps    ─────▶    Process efficiency analysis
Flow Efficiency       ─────▶    Weakness identification
Improvement Levers    ─────▶    Opportunity discovery
Benchmarks            ─────▶    Competitive gap analysis

Step 3 Output                    Step 4 Input
─────────────────                ─────────────────
SWOT Entries          ─────▶    Strategic problem framing
TOWS Actions          ─────▶    Foundation for strategy generation

Step 4 Output                    Step 5 Input
─────────────────                ─────────────────
Strategies (approved) ─────▶    Initiative scoping
Strategic OKRs        ─────▶    Product OKR alignment
Key Results           ─────▶    Target setting for initiatives

Step 5 Output                    Step 6 Input
─────────────────                ─────────────────
Initiatives           ─────▶    Epic breakdown source
Product Groups        ─────▶    Team organization context
Digital Products      ─────▶    Product OKR containers

Step 6 Output                    Step 7 Input
─────────────────                ─────────────────
Epics                 ─────▶    Feature decomposition source
Teams                 ─────▶    Delivery OKR assignment
Epic Dependencies     ─────▶    Feature dependency seeding
Product OKRs          ─────▶    Delivery OKR cascading
```

---

## RAG (Knowledge Base) Integration

The RAG system enriches AI outputs with organization-specific knowledge:

```
Document Upload Flow
    │
    ├─ User uploads document (PDF, DOCX, XLSX, CSV, TXT, JSON, MD)
    ├─ Text extracted from document
    ├─ Text chunked (400 words, 80-word overlap)
    ├─ Each chunk embedded via OpenAI text-embedding-3-small
    └─ Stored in document_chunks table with embedding vectors

AI Generation Flow (Live Mode)
    │
    ├─ AI agent prepares prompt for generation
    ├─ RAG engine queries: "What documents are relevant to [topic]?"
    ├─ Cosine similarity search across all embedded chunks
    ├─ Top-K relevant chunks (similarity > 0.6) assembled as context
    ├─ Context injected into AI prompt as additional knowledge
    └─ AI generates output grounded in organization's actual documents
```

**Integration Points:**
| Agent | RAG Context Used For |
|-------|---------------------|
| Dashboard Insights | Executive summary enrichment |
| Value Stream Research | Industry-specific process knowledge |
| SWOT/TOWS Engine | Organization-specific strength/weakness evidence |
| Strategy & OKR | Strategic planning document alignment |
| Initiative & RICE | Prior initiative/project knowledge |

---

## Demo vs Live Mode

| Aspect | Demo Mode | Live Mode |
|--------|-----------|-----------|
| Data source | Seed scripts (pre-loaded sample data) | User uploads + API ingestion |
| RAG | Disabled | Active — documents enrich AI |
| AI prompts | Generic industry context | Organization-specific context |
| Best for | Exploring the platform | Real transformation planning |
| Toggle | Sidebar "Demo Mode" badge | Sidebar "Live Mode" badge |

---

## External Integration Points

```
                    ┌─────────────────────┐
                    │   BMAD Platform      │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                      │
   ┌────▼────┐          ┌────▼────┐           ┌─────▼────┐
   │ Financial│          │   AI    │           │ Process  │
   │   APIs   │          │ Models  │           │ Sources  │
   ├─────────┤          ├─────────┤           ├──────────┤
   │ Finnhub │          │ GPT-4o  │           │ Jira     │
   │ Alpha   │          │ mini    │           │ Service  │
   │ Vantage │          │ GPT-4o  │           │ Now      │
   │         │          │ (vision)│           │ Web URLs │
   │         │          │ text-   │           │ BPMN     │
   │         │          │ embed-  │           │ Files    │
   │         │          │ ding-3  │           │          │
   └─────────┘          └─────────┘           └──────────┘
```

| Integration | Purpose | Used In |
|-------------|---------|---------|
| Finnhub API | Ticker search, company profiles, peer discovery | Step 1 |
| Alpha Vantage API | Financial metrics, revenue data | Step 1 |
| OpenAI GPT-4o-mini | All AI text generation | Steps 1-7 |
| OpenAI GPT-4o | Image/diagram vision analysis | Step 2 |
| OpenAI text-embedding-3-small | Document embeddings for RAG | Knowledge Base |
| Jira | Project/sprint data (when configured) | Step 2 |
| ServiceNow | ITSM incident/change data (when configured) | Step 2 |
| Brave Search | Web search for market research | Step 2 |

---

## Frontend Navigation Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  SIDEBAR                          MAIN CONTENT AREA          │
│  ┌──────────┐                     ┌────────────────────────┐ │
│  │ Step 1   │  ──────────────▶   │  Dynamic Content       │ │
│  │ Step 2   │                     │  (renders based on     │ │
│  │ Step 3   │                     │   active step)         │ │
│  │ Step 4   │                     │                        │ │
│  │ Step 5   │                     │  ┌─────────────────┐   │ │
│  │ Step 6   │                     │  │ Phase Tabs      │   │ │
│  │ Step 7   │                     │  │ (Step 1 only)   │   │ │
│  ├──────────┤                     │  │ Setup │ Data │   │   │ │
│  │ KB       │                     │  │ Analysis │ AI │  │   │ │
│  │ Demo/Live│                     │  └─────────────────┘   │ │
│  ├──────────┤                     │                        │ │
│  │ User Info│                     │  ┌─────────────────┐   │ │
│  │ Logout   │                     │  │ Data Tables     │   │ │
│  └──────────┘                     │  │ Forms           │   │ │
│                                    │  │ Charts          │   │ │
│                                    │  │ AI Generate Btn │   │ │
│                                    │  │ Review Gate     │   │ │
│                                    │  └─────────────────┘   │ │
│                                    └────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

MODAL OVERLAYS (appear on top of main content):
  ┌─────────────────────────────┐
  │ Generate All Progress Modal │  ← Shows 7-step progress
  │ Knowledge Base Modal        │  ← Upload, search, manage docs
  │ Review Wizard Modal         │  ← Post-generation review flow
  └─────────────────────────────┘
```

**Step 1 has 4 sub-phases:** Setup → Data Ingestion → Analysis → AI Dashboard
**Steps 2-7** each have: Data display + Edit forms + AI Generate button + Review Gate

---

## Summary: The Complete Journey

```
Company Name + Industry
         │
         ▼
   ┌─ Step 1 ─┐     Financial data ingested, health scored
         │
         ▼
   ┌─ Step 2 ─┐     Business processes mapped, bottlenecks found
         │
         ▼
   ┌─ Step 3 ─┐     Strategic problems identified (SWOT → TOWS)
         │
         ▼
   ┌─ Step 4 ─┐     4-layer strategy with measurable OKRs
         │
         ▼
   ┌─ Step 5 ─┐     Digital initiatives prioritized by RICE score
         │
         ▼
   ┌─ Step 6 ─┐     Epics assigned to teams with dependencies
         │
         ▼
   ┌─ Step 7 ─┐     Feature backlog with quarterly roadmap
         │
         ▼
   TRANSFORMATION PLAN READY
   (All 7 gates approved by human reviewers)
```

**From company name to actionable roadmap in under 60 seconds with AI, or at your own pace with manual entry and review.**
