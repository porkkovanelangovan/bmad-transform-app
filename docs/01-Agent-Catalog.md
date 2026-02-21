# Agent Catalog — BMAD Multi-Agent Transformation Platform

## Platform Overview

The BMAD Business Transformation Architect is a **multi-agent AI platform** where each agent is a specialized AI module responsible for a specific domain of business transformation analysis. The agents work sequentially — each agent's output feeds into the next — creating a complete transformation plan from raw business data.

**AI Model:** OpenAI GPT-4o-mini (all agents)
**Embedding Model:** OpenAI text-embedding-3-small (RAG agent)
**Vision Model:** GPT-4o with vision (Process Parser agent)

---

## Agent Architecture Diagram

```
                    +---------------------------+
                    |    ORCHESTRATOR AGENT      |
                    |  (Generate All - Step 1-7) |
                    +---------------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
   +---------+          +---------+          +---------+
   |  DATA   |          |   RAG   |          | EXTERNAL|
   | INGEST  |          | ENGINE  |          |   API   |
   | AGENT   |          |  AGENT  |          |  AGENT  |
   +---------+          +---------+          +---------+
        |                     |                     |
        +---------------------+---------------------+
                              |
  +------------------------------------------------------------------+
  |                    AI ANALYSIS PIPELINE                           |
  |                                                                  |
  |  Step 1         Step 2        Step 3       Step 4                |
  |  +----------+  +----------+  +---------+  +-----------+         |
  |  | DASHBOARD|  |VALUE     |  | SWOT /  |  | STRATEGY  |         |
  |  | INSIGHTS |->|STREAM    |->| TOWS    |->| & OKR     |         |
  |  | AGENT    |  |RESEARCH  |  | ENGINE  |  | AGENT     |         |
  |  |          |  |AGENT     |  | AGENT   |  |           |         |
  |  +----------+  +----------+  +---------+  +-----------+         |
  |                                                |                 |
  |  Step 5         Step 6        Step 7           |                 |
  |  +----------+  +----------+  +-----------+    |                 |
  |  |INITIATIVE|  | EPIC &   |  | FEATURE & |<---+                 |
  |  |& RICE    |->| TEAM     |->| ROADMAP   |                      |
  |  |AGENT     |  | AGENT    |  | AGENT     |                      |
  |  +----------+  +----------+  +-----------+                      |
  +------------------------------------------------------------------+
                              |
                    +---------------------------+
                    |    REVIEW GATE AGENT       |
                    |  (Human-in-the-Loop)       |
                    +---------------------------+
```

---

## 1. Data Ingestion Agent

**Module:** `backend/data_ingestion.py`
**Purpose:** Connects to external financial APIs to fetch real company data
**Activation:** Step 1 — when user enters a company name and clicks "Submit & Fetch Data"

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Ticker Search** | Searches Finnhub for company ticker symbol using multiple query variations (abbreviations, corporate suffixes) | Company name (e.g., "US Bancorp") | Ticker symbol (e.g., "USB") |
| 2 | **Company Profile Fetch** | Retrieves company profile including industry, country, market cap, currency | Ticker symbol | Organization metadata |
| 3 | **Peer Discovery** | Fetches list of competitor tickers from Finnhub | Ticker symbol | List of peer ticker symbols |
| 4 | **Financial Metrics Fetch** | Retrieves revenue, profit margins, PE ratio, EPS, ROE, ROA from Alpha Vantage | Ticker symbol | Financial metrics dataset |
| 5 | **Competitor Profile Fetch** | Fetches profiles and financials for each discovered peer | Peer ticker list | Competitor profiles with financials |
| 6 | **Data Normalization** | Normalizes and stores fetched data into business_units, revenue_splits, ops_efficiency, competitors tables | Raw API responses | Structured database records |

**External APIs:** Finnhub (ticker search, profiles, peers), Alpha Vantage (financials)
**Fallback:** Returns empty data if APIs unavailable; app continues with manual data entry

---

## 2. Dashboard Insights Agent

**Module:** `backend/ai_dashboard.py`
**Purpose:** AI-powered financial analysis, health scoring, trend detection, and executive summary generation
**Activation:** Step 1 — AI Insights tab

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Financial Health Scoring** | Calculates overall health score (0-100) from revenue trends, margins, profitability ratios | Revenue splits, ops metrics, competitor data | Health score with breakdown |
| 2 | **Trend Analysis** | Detects revenue growth/decline patterns, calculates moving averages | Multi-period revenue data | Trend direction, growth rates, projections |
| 3 | **Anomaly Detection** | Identifies statistical outliers in financial metrics | Ops efficiency metrics | Flagged anomalies with severity |
| 4 | **Executive Summary Generation** | AI synthesizes comprehensive org health report with key findings and strategic implications | All Step 1 data + competitor analysis | Multi-paragraph summary, 5 key findings, competitor narrative, strategic recommendations |
| 5 | **Enrichment Suggestions** | Recommends missing data points to improve analysis quality | Current data completeness | Prioritized list of missing data |
| 6 | **Transformation Readiness Score** | Assesses organizational readiness for digital transformation | All available metrics | Readiness score with dimension breakdown |

**AI Model:** GPT-4o-mini
**Caching:** Results cached in `ai_analysis_cache` table with TTL expiry

---

## 3. Value Stream Research Agent

**Module:** `backend/ai_research.py`, `backend/source_gatherers.py`
**Purpose:** Synthesizes data from multiple sources into comprehensive lean value stream maps
**Activation:** Step 2 — Pull from Sources, AI Research, Competitor Benchmarks

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Multi-Source Data Gathering** | Concurrently collects data from 8 configurable sources | Segment name, industry, org context | Aggregated source data |
| 2 | **Value Stream Synthesis** | AI analyzes gathered data to create end-to-end process map with 6-10 steps | Source data, org context, RAG context | Steps with timings, bottleneck identification |
| 3 | **Metrics Calculation** | Computes total lead time, process time, wait time, flow efficiency | Process steps | Value stream metrics |
| 4 | **Competitor Benchmarking** | AI generates detailed competitor operational comparisons | Competitor names, org metrics, RAG context | Competitor benchmarks with automation levels, tech stacks, differentiators |
| 5 | **Industry Best Practices** | Identifies relevant best practices for the value stream | Segment, industry | Best practices with adoption rates and impact estimates |
| 6 | **Template Generation** | Creates value streams from built-in industry templates (no API needed) | Segment name, industry | Template-based value stream with steps and benchmarks |

### Data Sources (Configurable)

| Source | Type | Description |
|--------|------|-------------|
| `app_data` | Internal | Existing org records and value streams |
| `erp_simulation` | Internal | Simulated ERP/CRM system metadata |
| `industry_benchmarks` | Internal | Industry standard metrics and KPIs |
| `finnhub` | External | Real competitor financial data |
| `web_search` | External | Live web search for market research |
| `openai_research` | AI | GPT-4o-mini synthesis of all gathered data |
| `competitor_operations` | AI | AI-generated competitor operational benchmarks |
| `jira` | External | Jira workflow data (if configured) |
| `servicenow` | External | ServiceNow incident/change data (if configured) |

---

## 4. Process Parser Agent

**Module:** `backend/process_parser.py`, `backend/url_extractor.py`
**Purpose:** Extracts process steps from visual diagrams, documents, and URLs
**Activation:** Step 2 — Upload Process Map, Extract from URL

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **BPMN XML Parsing** | Parses BPMN/XML files to extract process flows, tasks, gateways | BPMN file | Structured steps with types and flows |
| 2 | **Image OCR/Vision** | Uses GPT-4o vision to extract process steps from screenshots and diagrams | PNG/JPG/PDF image | Steps with descriptions and estimated timings |
| 3 | **URL Content Extraction** | Fetches web pages, strips HTML, extracts process descriptions | Web URL | Raw text + AI-extracted steps |
| 4 | **CSV/JSON Import** | Parses structured files with value stream step data | CSV/JSON file | Database records |

**Vision Model:** GPT-4o (for image/diagram parsing)
**Fallback:** BPMN parsing works without any API key

---

## 5. SWOT/TOWS Engine Agent

**Module:** `backend/ai_swot_strategy.py` (SWOT + TOWS functions)
**Purpose:** Generates SWOT analysis and converts to actionable TOWS strategies
**Activation:** Step 3 — Auto-generate

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Context Aggregation** | Gathers comprehensive org context from Steps 1-2 including financials, value streams, competitors, levers | All upstream data | Structured context prompt |
| 2 | **SWOT Generation** | AI creates Strengths, Weaknesses, Opportunities, and Threats with severity and confidence ratings | Aggregated context + RAG context | 8-16 SWOT entries with severity/confidence |
| 3 | **TOWS Action Mapping** | Converts SWOT pairs into strategic actions across 4 quadrants (SO, WO, ST, WT) | SWOT entries | TOWS actions with priority and impact scores |
| 4 | **Lever Integration** | Incorporates high-impact value stream improvement levers into SWOT analysis | Value stream levers | Enhanced SWOT with operational insights |

**Quadrant Definitions:**
- **SO (Maxi-Maxi):** Use Strengths to capture Opportunities
- **WO (Mini-Maxi):** Overcome Weaknesses to capture Opportunities
- **ST (Maxi-Mini):** Use Strengths to mitigate Threats
- **WT (Mini-Mini):** Minimize Weaknesses to avoid Threats

---

## 6. Strategy & OKR Agent

**Module:** `backend/ai_swot_strategy.py` (Strategy + OKR functions)
**Purpose:** Creates four-layer strategies and aligned OKRs from TOWS actions
**Activation:** Step 4 — Auto-generate

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Four-Layer Strategy Generation** | Creates strategies across 4 layers from TOWS actions and user strategy inputs | TOWS actions, strategy inputs, RAG context | 10-16 strategies across 4 layers |
| 2 | **Strategic OKR Creation** | Generates Objectives and Key Results aligned to each strategy | Approved strategies | OKRs with time horizons and target values |
| 3 | **Key Result Quantification** | Sets measurable targets with optimistic/pessimistic bounds | Strategic objectives | Key results with metrics, targets, bounds |
| 4 | **Risk Assessment** | Identifies risks for each strategy with severity levels | Strategy descriptions | Risk statements with levels |

**Strategy Layers:**
| Layer | Color | Focus |
|-------|-------|-------|
| Business Strategy | Green | Market positioning, growth, competitive advantage |
| Digital Strategy | Blue | Technology platforms, digital channels, automation |
| Data Strategy | Orange | Data governance, analytics, data-driven decisions |
| Gen AI Strategy | Purple | AI/ML capabilities, intelligent automation, GenAI use cases |

---

## 7. Initiative & RICE Agent

**Module:** `backend/ai_initiatives.py` (Initiative functions)
**Purpose:** Generates digital product initiatives with RICE prioritization scoring
**Activation:** Step 5 — Auto-generate

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Initiative Generation** | Creates digital product initiatives from approved strategies | Strategies, OKRs, value streams, RAG context | 15-25 initiatives with descriptions |
| 2 | **RICE Scoring** | Calculates priority score: (Reach x Impact x Confidence) / Effort | Initiative parameters | RICE score per initiative |
| 3 | **Product Group Creation** | Organizes initiatives into logical product groups | Initiative list | Product groups with descriptions |
| 4 | **Digital Product Mapping** | Maps initiatives to specific digital products | Initiatives, product groups | Digital product catalog |
| 5 | **Roadmap Phasing** | Assigns initiatives to phases: Quick Wins, Strategic, Long-Term | RICE scores, dependencies | Phase assignments |
| 6 | **Product OKR Generation** | Creates product-level OKRs linked to strategic OKRs | Strategic OKRs, digital products | Product OKRs with key results |

**RICE Formula:** `Score = (Reach x Impact x Confidence) / Effort`

| Factor | Scale | Description |
|--------|-------|-------------|
| Reach | 1-10 | How many users/processes affected |
| Impact | 0.25 - 3.0 | Degree of improvement (minimal to massive) |
| Confidence | 0.5 - 1.0 | How confident in estimates |
| Effort | 1-10 | Person-months of work required |

---

## 8. Epic & Team Agent

**Module:** `backend/ai_initiatives.py` (Epic functions)
**Purpose:** Breaks initiatives into delivery epics and assigns to teams
**Activation:** Step 6 — Auto-generate

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Epic Generation** | Breaks each initiative into 2-4 delivery epics | Initiatives, strategies, value streams | Epics with descriptions and effort estimates |
| 2 | **Effort Estimation** | Estimates effort in days for each epic | Epic scope, complexity | estimated_effort_days per epic |
| 3 | **Team Creation** | AI recommends 4-6 teams based on the work | Initiatives, epics, product groups | Teams with capacity settings |
| 4 | **Team Assignment** | Maps epics to teams based on capability fit | Epics, teams | Epic-team assignments |
| 5 | **Dependency Mapping** | Identifies blocking/relating relationships between epics | Epic descriptions, flow analysis | Epic dependency graph |
| 6 | **Delivery OKR Generation** | Creates team-level delivery OKRs from product OKRs | Product OKRs, teams | Delivery OKRs with key results |

---

## 9. Feature & Roadmap Agent

**Module:** `backend/ai_initiatives.py` (Feature functions)
**Purpose:** Creates feature backlog with acceptance criteria and quarterly roadmap
**Activation:** Step 7 — Auto-generate

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Feature Generation** | Creates 2-5 features per epic with detailed descriptions | Epics, initiatives, value stream steps | Features with descriptions |
| 2 | **Acceptance Criteria** | Writes testable acceptance criteria for each feature | Feature descriptions | AC in Given/When/Then format |
| 3 | **Priority Scoring** | Calculates feature priority from value, size, effort, risk | Feature parameters | Priority scores with risk levels |
| 4 | **Quarterly Roadmap** | Distributes features across quarters based on priority | Feature priorities, dependencies | 4-quarter timeline (Steps 6-7) or 8-quarter (Step 5) |
| 5 | **Dependency Resolution** | Identifies feature-level dependencies and critical paths | Feature relationships | Feature dependency graph |

**Roadmap Distribution:**
- Step 5 (Initiatives): 8 quarters / 2-year timeline
- Step 6 (Epics): 4 quarters / 1-year timeline with product/initiative references
- Step 7 (Features): 4 quarters / 1-year timeline with epic/product/initiative references

---

## 10. RAG (Knowledge Base) Agent

**Module:** `backend/rag_engine.py`, `backend/routers/documents.py`
**Purpose:** Manages organization knowledge base, generates embeddings, provides semantic search for AI context enrichment
**Activation:** Knowledge Base modal (any time), automatically during AI generation in Live mode

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Document Ingestion** | Accepts and stores documents (PDF, DOCX, XLSX, CSV, TXT, JSON, MD) | Uploaded file | Stored document with extracted text |
| 2 | **Text Chunking** | Splits document text into 400-word overlapping chunks (80-word overlap) | Raw text | Chunk list |
| 3 | **Embedding Generation** | Creates vector embeddings using OpenAI text-embedding-3-small | Text chunks (batches of 20) | 1536-dimension embedding vectors |
| 4 | **Semantic Search** | Finds most relevant chunks by cosine similarity to a query | Search query + optional category filter | Ranked results with similarity scores |
| 5 | **Keyword Fallback Search** | SQL LIKE-based search when embeddings unavailable | Search keywords | Matching chunks |
| 6 | **Context Building** | Assembles retrieved chunks into formatted context for AI prompts | Query, org_id, top_k | Formatted context string with source/relevance headers |
| 7 | **Data Mode Management** | Toggles between Demo (sample data) and Live (RAG-enhanced) modes | User toggle | Updated org data_mode |

**Integration Points:** RAG context is injected into SWOT, Strategy, Initiative, Dashboard, and Value Stream AI prompts when in Live mode.

---

## 11. Orchestrator Agent

**Module:** `backend/ai_generate_all.py`, `backend/routers/generate_all.py`
**Purpose:** Chains all 7 steps into a single end-to-end AI generation pipeline
**Activation:** "Generate All Steps" button in Step 1

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Step 1: Business Data** | Ingests API data (public) or AI-generates synthetic data (private companies) | Org name, industry | Business units, revenue, metrics, competitors |
| 2 | **Step 2: Value Streams** | AI determines 3-4 industry-relevant segments, generates value streams | Industry, BU context | Value streams with steps, metrics, benchmarks |
| 3 | **Step 3: SWOT/TOWS** | Calls SWOT generation then TOWS action mapping | Steps 1-2 data | SWOT entries + TOWS actions |
| 4 | **Step 4: Strategies** | Generates 4-layer strategies and strategic OKRs | TOWS actions | Strategies + OKRs + Key Results |
| 5 | **Step 5: Initiatives** | Creates product groups, products, initiatives with RICE | Strategies + OKRs | Product catalog + scored initiatives |
| 6 | **Step 6: Epics** | Creates teams, generates epics, assigns teams | Initiatives | Teams + Epics + Delivery OKRs |
| 7 | **Step 7: Features** | Creates feature backlog with acceptance criteria | Epics | Features + Quarterly roadmap |
| 8 | **Progress Tracking** | Reports real-time status via polling endpoint | Run ID | Step status, errors, completion % |
| 9 | **Error Recovery** | Catches per-step failures, preserves partial progress | Failed step info | Retry capability from failed step |

**Execution:** Background async task with polling (2-second intervals)
**Duration:** ~30-60 seconds for full pipeline
**Cost:** ~$0.03-0.05 per generation (GPT-4o-mini)

---

## 12. Review Gate Agent (Human-in-the-Loop)

**Module:** `backend/routers/review_gates.py`
**Purpose:** Manages approval checkpoints at each step for human review
**Activation:** Gate cards at the bottom of each step's page

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Gate Initialization** | Creates review gates for each step during generation | Step number, gate config | Gate records (status: pending) |
| 2 | **Gate Presentation** | Displays gate status with approve/reject buttons | Gate ID, step number | UI card with status badge |
| 3 | **Approval Processing** | Records reviewer approval with optional notes | Gate ID, reviewer, notes | Updated gate (status: approved) |
| 4 | **Rejection Processing** | Records rejection requiring revisions | Gate ID, reviewer, notes | Updated gate (status: rejected) |
| 5 | **Progress Tracking** | Shows overall approval progress (e.g., "5/7 steps approved") | All gates | Progress indicator |

### Gate Configuration

| Step | Gates |
|------|-------|
| Step 1 | Review dashboard metrics, Approve performance baseline |
| Step 2 | Refine opportunity levers |
| Step 3 | Validate SWOT entries, Approve TOWS strategies |
| Step 4 | Review strategies, Approve Strategic OKRs |
| Step 5 | RICE manual override complete, Approve initiative list |
| Step 6 | Review team dependencies, Approve Product OKRs |
| Step 7 | Review Delivery OKRs, Approve final roadmap |

---

## 13. Template Engine Agent

**Module:** `backend/openai_client.py`
**Purpose:** Provides deterministic value stream generation without AI API dependency
**Activation:** Step 2 — Template-based generation (fallback when OpenAI unavailable)

### Tasks

| # | Task | Description | Input | Output |
|---|------|-------------|-------|--------|
| 1 | **Template Matching** | Fuzzy-matches segment name to 8+ industry templates | Segment name | Best-match template |
| 2 | **Step Generation** | Creates realistic process steps with timings from templates | Template, industry | 6-10 steps with process/wait times |
| 3 | **Benchmark Fabrication** | Generates competitor benchmarks with +/-15-30% variance | Org metrics, competitor names | Competitor comparison data |
| 4 | **Metric Calculation** | Computes lead time, process time, flow efficiency | Generated steps | Overall metrics |

**Templates Available:** Financial Services (Loan Processing, Account Opening, Claims), Technology (Software Delivery, Incident Management), Healthcare (Patient Journey), Retail (Order Fulfillment), Manufacturing (Production Line)

---

## Agent Interaction Summary

```
User Input (Company + Industry)
       |
       v
[Data Ingestion Agent] --> Fetches real financial data from APIs
       |
       v
[Dashboard Insights Agent] --> Analyzes health, trends, anomalies
       |
       v
[Value Stream Research Agent] --> Creates lean process maps
       |                    \
       |              [Process Parser Agent] --> Extracts from uploads/URLs
       |                    /
       v                   v
[RAG Agent] <--> Enriches all downstream agents with KB context
       |
       v
[SWOT/TOWS Engine Agent] --> Identifies strengths, weaknesses, actions
       |
       v
[Strategy & OKR Agent] --> Creates 4-layer strategy with measurable goals
       |
       v
[Initiative & RICE Agent] --> Prioritizes digital product initiatives
       |
       v
[Epic & Team Agent] --> Breaks into delivery work, assigns teams
       |
       v
[Feature & Roadmap Agent] --> Creates backlog with quarterly timeline
       |
       v
[Review Gate Agent] --> Human approves/refines at each step
```
