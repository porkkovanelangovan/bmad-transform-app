# Agent Workflow Guide: End-to-End Platform Functionality

## What This Platform Does

The **Business Transformation Architect (BTA)** is an AI-powered platform that takes a company name and industry as input and generates a complete 7-step digital transformation plan — from financial analysis all the way down to feature-level user stories. It uses **13 specialized AI agents** that collaborate sequentially, where each agent builds on the output of previous agents.

---

## How It Works: The Big Picture

```
You enter: "US Bancorp" + "Financial Services"
                    |
                    v
   +------------------------------------------+
   |  STEP 1: Data Ingestion Agent            |  Fetches real financial data
   |  + Dashboard Agent                       |  from APIs (Finnhub, Alpha Vantage)
   +------------------------------------------+
                    |
                    v  (business units, revenue, metrics, competitors)
   +------------------------------------------+
   |  STEP 2: Value Stream Research Agent     |  Maps end-to-end business
   |  + Process Parser Agent                  |  processes with timing data
   +------------------------------------------+
                    |
                    v  (value streams, process steps, benchmarks)
   +------------------------------------------+
   |  STEP 3: SWOT/TOWS Agent                |  Analyzes strengths, weaknesses,
   |                                          |  opportunities, threats
   +------------------------------------------+
                    |
                    v  (SWOT entries, TOWS strategic actions)
   +------------------------------------------+
   |  STEP 4: Strategy & OKR Agent            |  Creates 4-layer transformation
   |                                          |  strategy with measurable goals
   +------------------------------------------+
                    |
                    v  (strategies, OKRs, key results)
   +------------------------------------------+
   |  STEP 5: Initiative & RICE Agent         |  Defines digital initiatives
   |                                          |  with priority scoring
   +------------------------------------------+
                    |
                    v  (initiatives, products, RICE scores)
   +------------------------------------------+
   |  STEP 6: Epic & Team Agent               |  Breaks initiatives into epics,
   |                                          |  creates and assigns teams
   +------------------------------------------+
                    |
                    v  (epics, teams, product OKRs, dependencies)
   +------------------------------------------+
   |  STEP 7: Feature & Roadmap Agent         |  Creates user stories with
   |                                          |  acceptance criteria
   +------------------------------------------+
                    |
                    v
   COMPLETE TRANSFORMATION PLAN READY FOR REVIEW
```

**Two ways to run this:**
- **Step-by-step**: Navigate to each step, click "Auto-Generate", review, refine, then move to the next step
- **One-click "Generate All"**: Runs all 7 steps automatically in ~3-5 minutes

---

## Detailed Agent Workflows

---

### AGENT 1: Data Ingestion Agent (Step 1)

**What it does:** Gathers business performance data — financial metrics, revenue trends, operational KPIs, and competitor information.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | User enters company name | e.g., "US Bancorp" |
| 2 | Agent searches for stock ticker | Queries Finnhub API with name variations (USB, US Bancorp, U.S. Bancorp) |
| 3 | Fetches company profile | Industry, country, market cap, currency from Finnhub |
| 4 | Fetches financial metrics (PRIMARY) | 20+ KPIs from Finnhub: margins, ROE, ROA, EPS, beta, growth rates |
| 5 | Fetches income statements (SUPPLEMENT) | 5-year annual revenue, profit, EBITDA from Alpha Vantage |
| 6 | Fetches competitor data | Searches for named competitors (e.g., JPMC, BOA), pulls their financials too |
| 7 | Fetches peer companies | Discovers 4 additional peers from Finnhub peer API |
| 8 | Stores everything in database | business_units, revenue_splits, ops_efficiency, competitors tables |

**For non-public companies (no ticker found):**
- Falls back to AI (GPT-4o-mini) to generate realistic synthetic data
- Creates 3-5 business units, 3 years of revenue, 10+ metrics, 3-4 competitors
- Last resort: uses template data

**Alternative data inputs:**
- **File upload**: CSV, Excel, PDF, Word, images — AI extracts financial data automatically
- **URL extraction**: Paste a webpage URL, AI scrapes and parses financial information
- **Manual entry**: Add business units, revenue splits, metrics by hand

**What it outputs (used by later agents):**
- Business units (e.g., "US Bancorp", "Consumer Banking", "Wealth Management")
- Revenue splits by year and segment
- 12+ operational metrics (margins, growth, returns)
- 5+ competitor profiles with their financial data

**Collaborates with:**
- **Dashboard Agent** → Uses this data to generate AI-powered analysis
- **Step 2 Agent** → Provides business context for value stream mapping
- **Step 3 Agent** → Financial metrics feed into SWOT analysis
- **RAG Agent** → Uploaded documents are stored in knowledge base (live mode)

---

### AGENT 2: AI Dashboard Agent (Step 1 — AI Insights)

**What it does:** Provides 10 AI-powered analytical capabilities on top of Step 1 data.

**Capabilities:**

| # | Function | What It Generates |
|---|----------|-------------------|
| 1 | Financial Analysis | Strengths, weaknesses, opportunities, threats from financial data |
| 2 | Competitor Discovery | Finds competitors not in your data, maps competitive positioning |
| 3 | Trend Analysis | Revenue trends, CAGR, YoY growth, forecasts, seasonal patterns |
| 4 | Anomaly Detection | Data quality issues, benchmark deviations, missing fields |
| 5 | Executive Summary | C-level narrative briefing with key findings |
| 6 | Data Enrichment | Suggests missing metrics, new business units, revenue dimensions |
| 7 | Transformation Health | Scores progress across all 7 steps (0-100) |
| 8 | Natural Language Query | Ask questions like "How does our margin compare to competitors?" |
| 9 | What-If Scenarios | Model scenarios: "What if revenue drops 20%?" |
| 10 | Report Generation | Full reports for C-suite, technical teams, or board audiences |

**Collaborates with:**
- **Data Ingestion Agent** → Consumes all Step 1 data
- **RAG Agent** → Includes uploaded document context in analysis (live mode)
- **All Steps** → Transformation Health function reads data from all 7 steps

---

### AGENT 3: Value Stream Research Agent (Step 2)

**What it does:** Maps end-to-end business processes (value streams) with detailed process steps, timing data, bottlenecks, and competitor benchmarks.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Determine value stream names | AI suggests 3-4 industry-relevant names (e.g., "Customer Onboarding", "Loan Processing", "Payment Operations") |
| 2 | Gather data from 8+ sources | Runs sources in parallel — see below |
| 3 | AI synthesizes all gathered data | GPT-4o-mini combines all sources into a coherent value stream map |
| 4 | Generate process steps | 6-10 steps per value stream with process time, wait time, resources |
| 5 | Identify bottlenecks | Marks steps with highest wait-to-process ratio |
| 6 | Generate competitor benchmarks | How competitors perform the same process (lead time, automation level) |
| 7 | Calculate flow efficiency | Total process time / total lead time (higher = better) |

**Data sources gathered in parallel:**

| Source | What It Provides |
|--------|-----------------|
| App Data | Existing organization and value stream records |
| ERP Simulation | Simulated enterprise system metadata |
| Industry Benchmarks | Standard KPI ranges for the industry |
| Finnhub | Real competitor financial data for context |
| Web Search | Industry trends and best practices |
| Competitor Operations | How competitors run similar processes |
| Jira (simulated) | Project management velocity data |
| ServiceNow (simulated) | IT service management metrics |
| OpenAI Research | AI synthesis of all above sources |
| RAG Knowledge Base | Relevant uploaded documents (live mode) |

**What it outputs (used by later agents):**
- Value streams with descriptive names
- Process steps with timing (process_time_hours, wait_time_hours)
- Bottleneck identification
- Flow efficiency metrics
- Competitor benchmark comparisons
- Improvement levers

**Collaborates with:**
- **Data Ingestion Agent (Step 1)** → Uses company profile, industry, competitors as context
- **RAG Agent** → Queries knowledge base for value stream documents
- **SWOT Agent (Step 3)** → Value stream inefficiencies become weaknesses; strengths become strengths
- **Process Parser Agent** → Extracts structured steps from AI output

---

### AGENT 4: Process Parser Agent (Step 2 — Sub-agent)

**What it does:** Takes raw AI-generated value stream data and structures it into database-ready records.

**Workflow:**
1. Receives JSON from Value Stream Research Agent
2. Parses each step: order, name, type (trigger/process/decision/delivery), timing
3. Calculates overall metrics (total lead time, process time, flow efficiency)
4. Validates data integrity (no negative times, reasonable ranges)
5. Inserts into value_stream_steps, value_stream_metrics tables

**Collaborates with:**
- **Value Stream Research Agent** → Receives raw AI output
- **Database** → Writes structured records

---

### AGENT 5: SWOT/TOWS Agent (Step 3)

**What it does:** Generates comprehensive SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) from Steps 1-2 data, then creates TOWS strategic actions by pairing SWOT entries.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Gather full context | Collects ALL data from Steps 1-2: financials, metrics, competitors, value streams, benchmarks |
| 2 | Add external sources | Web search, industry benchmarks, Finnhub data, RAG documents |
| 3 | Generate SWOT entries | AI creates 4 strengths, 4 weaknesses, 4 opportunities, 4 threats (16 total) |
| 4 | Score each entry | Severity (high/medium/low) and Confidence (high/medium/low) |
| 5 | Generate TOWS actions | Pairs SWOT entries to create strategic actions |
| 6 | Categorize TOWS | SO (leverage), WO (improve), ST (defend), WT (avoid) — 12-15 actions |
| 7 | Priority score | Each TOWS action gets priority (critical/high/medium/low) and impact score (1-10) |

**TOWS Matrix explained:**

| | Strengths (S) | Weaknesses (W) |
|---|---|---|
| **Opportunities (O)** | **SO**: Use strengths to capture opportunities | **WO**: Fix weaknesses to capture opportunities |
| **Threats (T)** | **ST**: Use strengths to defend against threats | **WT**: Minimize weaknesses to avoid threats |

**Example output:**
- Strength: "Strong ROE of 15.2% exceeds industry average" (severity: high, confidence: high)
- Weakness: "Customer onboarding lead time 3x industry benchmark" (severity: high, confidence: medium)
- SO Action: "Leverage financial strength to invest in digital onboarding" (priority: critical, impact: 9)

**What it outputs (used by later agents):**
- 16 SWOT entries with severity and confidence scores
- 12-15 TOWS actions with priority and impact scores
- Data source attribution for each entry

**Collaborates with:**
- **Data Ingestion Agent (Step 1)** → Financial metrics, competitor data
- **Value Stream Agent (Step 2)** → Process inefficiencies, bottlenecks, benchmarks
- **RAG Agent** → Organization knowledge base documents
- **Strategy Agent (Step 4)** → SWOT + TOWS feed directly into strategy formulation

**Fallback:** If OpenAI unavailable, generates rule-based SWOT from financial ratios and value stream metrics.

---

### AGENT 6: Strategy & OKR Agent (Step 4)

**What it does:** Creates a 4-layer transformation strategy with Objectives and Key Results (OKRs) based on all upstream analysis.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Gather all context | Steps 1-3 data + user strategy inputs (if provided) |
| 2 | Analyze TOWS actions | Groups by priority and strategy type |
| 3 | Generate 4-layer strategy | Business, Digital, Data, Gen AI — 2 strategies per layer |
| 4 | Create OKRs per strategy | 1 objective + 1-3 key results per strategy |
| 5 | Set KR targets from data | Baselines from current metrics, targets from benchmarks |
| 6 | Add cross-layer notes | How the 4 layers reinforce each other |
| 7 | Suggest initiatives | 2-3 initiative ideas for Step 5 |

**The 4 Strategy Layers:**

| Layer | Focus | Example Strategy |
|-------|-------|-----------------|
| **Business** | Process optimization, market positioning | "Launch customer loyalty program to increase retention by 15%" |
| **Digital** | Technology enablement, automation | "Implement unified digital banking platform across all channels" |
| **Data** | Analytics, insights, intelligence | "Build real-time customer analytics for personalized services" |
| **Gen AI** | AI/ML capabilities, intelligent automation | "Deploy AI-powered customer service reducing response time by 60%" |

**OKR Structure:**
```
Strategy: Launch customer loyalty program
  Objective: Increase customer retention and lifetime value
    KR1: Reduce churn rate from 12% to 8% (baseline: current metric)
    KR2: Increase NPS from 35 to 55 (target: industry benchmark)
    KR3: Grow cross-sell ratio from 1.2 to 2.0 (target: competitor average)
```

**User Inputs (optional):** Users can provide strategic direction before auto-generating:
- Business strategy priorities
- Digital transformation goals
- Data strategy vision
- Gen AI ambitions
- Ongoing initiatives to consider

**What it outputs (used by later agents):**
- 6-8 strategies across 4 layers
- 6-8 OKRs with measurable key results
- Cross-layer alignment notes
- Initiative suggestions

**Collaborates with:**
- **SWOT/TOWS Agent (Step 3)** → TOWS actions drive strategy priorities
- **Data Ingestion Agent (Step 1)** → Financial baselines for KR targets
- **Value Stream Agent (Step 2)** → Process metrics for operational targets
- **Initiative Agent (Step 5)** → Strategies must be **approved** before initiatives can be generated

**Human-in-the-loop:** User must review and **approve strategies** before proceeding to Step 5. In "Generate All" mode, strategies are auto-approved.

---

### AGENT 7: Initiative & RICE Agent (Step 5)

**What it does:** Translates approved strategies into concrete digital initiatives with RICE prioritization scoring.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Fetch approved strategies | Only strategies marked "approved" in Step 4 |
| 2 | Gather full context | All Steps 1-4 data + external sources |
| 3 | Generate initiatives | 1-2 initiatives per strategic OKR |
| 4 | RICE score each initiative | Reach x Impact x Confidence / Effort |
| 5 | Assign roadmap phase | Quick Win / Strategic / Long Term |
| 6 | Identify risks & dependencies | Per initiative |
| 7 | Create product groups & products | Auto-creates organizational structure |

**RICE Scoring explained:**

| Factor | Scale | What It Measures |
|--------|-------|-----------------|
| **Reach** | 1-10 | How many users/customers affected |
| **Impact** | 0.25, 0.5, 1, 2, 3 | How much it moves the needle |
| **Confidence** | 0.5, 0.8, 1.0 | How sure are we about the estimates |
| **Effort** | 1-10 | How many person-months to deliver |

**RICE Score** = (Reach x Impact x Confidence) / Effort

**Roadmap Phases:**
- **Quick Win**: RICE > 5, Effort < 3 — do first (0-3 months)
- **Strategic**: RICE 2-5, medium effort — plan for next (3-9 months)
- **Long Term**: RICE < 2 or high effort — future consideration (9-18 months)

**Example output:**
```
Initiative: "AI-Powered Customer Onboarding"
  Strategy: Digital Layer - Unified Banking Platform
  Reach: 8  |  Impact: 3  |  Confidence: 0.8  |  Effort: 6
  RICE Score: 3.2 (Strategic)
  Risks: Integration complexity with legacy systems
  Dependencies: Core banking API modernization
  Phase: Strategic (Q2-Q3)
```

**What it outputs (used by later agents):**
- 6-12 initiatives with RICE scores
- Product groups and digital products
- Quarterly roadmap placement
- Risk and dependency maps

**Collaborates with:**
- **Strategy Agent (Step 4)** → Initiatives map 1:1 to strategic OKRs
- **All previous steps** → Context for realistic scoring
- **Epic Agent (Step 6)** → Each initiative gets decomposed into epics

---

### AGENT 8: Epic & Team Agent (Step 6)

**What it does:** Breaks each initiative into delivery epics (large work packages), creates cross-functional teams, and assigns epics to teams.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Create teams (if needed) | AI recommends 4-6 teams based on strategy/initiative context |
| 2 | Fetch all initiatives | From Step 5 |
| 3 | Decompose into epics | 2-5 epics per initiative |
| 4 | Generate Product OKRs | Translates strategic OKRs to product-level |
| 5 | Map dependencies | Cross-epic and cross-initiative dependencies |
| 6 | Assign to teams | Matches epic type to team capabilities |

**Team Creation:**
- AI analyzes strategies and initiatives to recommend team structure
- Example teams: "Platform Engineering (10)", "Data & Analytics (8)", "Customer Experience (6)"
- Capacity number = team size for workload balancing

**Epic Structure:**
```
Initiative: "AI-Powered Customer Onboarding"
  Epic 1: "Design Onboarding UX Flow" (value: 5, effort: 20 days)
    Team: Customer Experience
  Epic 2: "Build Identity Verification API" (value: 4, effort: 30 days)
    Team: Platform Engineering
  Epic 3: "Integrate AI Document Processing" (value: 5, effort: 25 days)
    Team: Data & Analytics

  Product OKR: "Reduce onboarding time from 5 days to 1 day"
    KR1: 80% of applications completed same-day
    KR2: Document verification automated for 90% of cases
```

**What it outputs (used by later agents):**
- 15-25 epics with effort estimates and risk levels
- 4-6 cross-functional teams
- Product OKRs (translated from strategic OKRs)
- Epic dependency map
- Team assignments

**Collaborates with:**
- **Initiative Agent (Step 5)** → Each initiative becomes 2-5 epics
- **Strategy Agent (Step 4)** → Strategic OKRs translated to product OKRs
- **Feature Agent (Step 7)** → Each epic gets decomposed into features

---

### AGENT 9: Feature & Roadmap Agent (Step 7)

**What it does:** Decomposes each epic into deliverable features written as user stories with acceptance criteria and creates delivery OKRs.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | Fetch all epics | From Step 6, with team assignments |
| 2 | Decompose into features | 2-5 features per epic |
| 3 | Write user stories | "As a [role], I want [feature] so that [value]" format |
| 4 | Define acceptance criteria | Given/When/Then testable criteria |
| 5 | Estimate effort | Story points (1-40) per feature |
| 6 | Generate Delivery OKRs | Team-specific, sprint-level goals |
| 7 | Map feature dependencies | Sequencing within and across epics |

**Feature Structure:**
```
Epic: "Design Onboarding UX Flow"
  Feature 1: "Implement Step-by-Step Wizard"
    As a new customer, I want a guided onboarding wizard
    so that I can open an account without confusion.

    Acceptance Criteria:
    - Given I start onboarding, When I complete step 1, Then step 2 is highlighted
    - Given I leave mid-flow, When I return, Then my progress is saved

    Effort: 8 story points  |  Value: 5  |  Risk: Low

  Feature 2: "Add Document Upload Component"
    As a new customer, I want to upload my ID documents
    so that I can verify my identity digitally.

    Effort: 13 story points  |  Value: 4  |  Risk: Medium
```

**OKR Cascade (complete picture):**
```
STRATEGIC OKR (Step 4):
  "Increase customer acquisition by 25%"
    ↓
PRODUCT OKR (Step 6):
  "Reduce onboarding time from 5 days to 1 day"
    ↓
DELIVERY OKR (Step 7):
  "Ship onboarding MVP with 90% test coverage in Sprint 3"
    KR1: All 5 features passing acceptance tests
    KR2: Load testing handles 1000 concurrent applications
    KR3: Accessibility audit score > 95
```

**What it outputs:**
- 30-60 features with user stories and acceptance criteria
- Delivery OKRs per team
- Feature dependency map
- Complete backlog ready for sprint planning

**Collaborates with:**
- **Epic Agent (Step 6)** → Each epic becomes 2-5 features
- **Team assignments** → Delivery OKRs are team-specific
- **Strategy cascade** → Strategic → Product → Delivery OKR hierarchy

---

### AGENT 10: RAG (Knowledge Base) Agent

**What it does:** Manages an organization's document knowledge base and provides relevant context to all other agents.

**Workflow:**

| # | Action | Details |
|---|--------|---------|
| 1 | User uploads documents | PDF, Word, Excel, CSV, images, JSON |
| 2 | Extract text | PyMuPDF for PDF, python-docx for Word, etc. |
| 3 | Chunk text | 400-word chunks with 80-word overlap |
| 4 | Generate embeddings | OpenAI text-embedding-3-small (1536 dimensions) |
| 5 | Store in database | org_documents + document_chunks tables |
| 6 | Semantic search | When agents need context, RAG retrieves top-K similar chunks |

**How RAG feeds into other agents:**

| Agent | RAG Query Used | Chunks Retrieved |
|-------|---------------|-----------------|
| Value Stream Agent (Step 2) | "[segment] value stream [industry] operations" | 8 chunks |
| Competitor Benchmarks (Step 2) | "[vs_name] competitor operations benchmarks" | 5 chunks |
| AI Dashboard (Step 1) | "[org_name] [industry] business performance" | 6 chunks |
| SWOT Agent (Step 3) | "[org_name] strategy value stream metrics" | 6 chunks |

**Data modes:**
- **Demo mode**: RAG disabled, agents work with gathered data only
- **Live mode**: RAG enabled, uploaded documents enhance all AI analysis

**Collaborates with:** Every AI agent that generates analysis. RAG context appears in their prompts under "Organization Knowledge Base" section.

---

### AGENT 11: Orchestrator Agent (Generate All)

**What it does:** Chains all 7 steps together for one-click generation of a complete transformation plan.

**Workflow:**

```
User clicks "Generate All Steps"
    |
    v
[1] Check org exists (name + industry required)
    |
[2] Create generation_runs record (status: running)
    |
[3] STEP 1: Try API ingestion → AI fallback → Template fallback
    |  Progress: "Fetching financial data for US Bancorp..."
    |
[4] STEP 2: AI determines 3-4 value stream names
    |  For each: pull from sources (OpenAI + benchmarks)
    |  Progress: "Creating value stream: Customer Onboarding..."
    |
[5] STEP 3: Auto-generate SWOT + TOWS
    |  Progress: "Analyzing strengths, weaknesses, opportunities, threats..."
    |
[6] STEP 4: Auto-generate strategies + OKRs
    |  AUTO-APPROVE all strategies (unblocks Step 5)
    |  Progress: "Generated 8 strategies across 4 layers..."
    |
[7] STEP 5: Auto-generate initiatives with RICE
    |  Progress: "Created 8 initiatives with priority scoring..."
    |
[8] STEP 6: AI generates teams → Auto-generate epics
    |  Progress: "Created 5 teams, 17 epics with assignments..."
    |
[9] STEP 7: Auto-generate features + delivery OKRs
    |  Progress: "Created 30 features with user stories..."
    |
[10] Create 7 review gates (all pending)
    |
    v
DONE — "Generation complete: 7/7 steps"
```

**Error handling:**
- Each step is wrapped in try/catch — failure in one step doesn't stop the pipeline
- Status tracked: `steps_completed: [1,2,3,5]`, `steps_failed: [4]`
- Final status: "completed" (7/7), "partial" (some failed), "failed" (all failed)
- User can click "Retry" to re-run from failed steps

**Frontend progress:**
- Modal overlay shows 7 step indicators
- Polls `/generate-all/status` every 2 seconds
- Each step transitions: Pending → Running (spinner) → Complete (checkmark) / Failed (X)

**Estimated time:** 3-5 minutes (7-12 OpenAI API calls)

---

### AGENT 12: Review Gate Agent

**What it does:** Manages human-in-the-loop review checkpoints between steps.

**7 Review Gates:**

| Gate | Step | What Gets Reviewed |
|------|------|--------------------|
| Gate 1 | Business Performance | Business units, revenue, metrics, competitors |
| Gate 2 | Value Stream Analysis | Process steps, timing, bottlenecks, benchmarks |
| Gate 3 | SWOT/TOWS Review | SWOT entries, TOWS actions, severity scores |
| Gate 4 | Strategy & OKRs Review | 4-layer strategies, OKRs, key results |
| Gate 5 | Initiatives Review | Initiatives, RICE scores, roadmap phases |
| Gate 6 | Epics & Teams Review | Epics, team assignments, product OKRs |
| Gate 7 | Feature Backlog Review | Features, user stories, delivery OKRs |

**Gate status flow:** `Pending` → `Approved` (with reviewer name + notes) or `Rejected`

**Human review actions at each gate:**
- Edit/delete any AI-generated entries
- Add manual entries
- Adjust scores, priorities, estimates
- Add reviewer notes
- Approve or reject the gate

---

### AGENT 13: Template Engine Agent

**What it does:** Provides fallback data generation when OpenAI API is unavailable.

**Templates available:**

| Step | Template Fallback |
|------|-------------------|
| Step 1 | 1 business unit, 3-year revenue ($50M-$60M), 4 standard metrics, 2 generic competitors |
| Step 2 | 3 generic value streams with 6 template process steps each |
| Step 3 | Rule-based SWOT from financial ratios (margin > industry avg = strength, etc.) |
| Step 4 | 4-layer template strategies with generic OKRs |
| Step 5 | 1 initiative per strategy with default RICE scores |
| Step 6 | 5 default teams, 2 template epics per initiative |
| Step 7 | 2 template features per epic with generic user stories |

---

## Cross-Agent Data Flow: Complete Picture

```
                    EXTERNAL DATA SOURCES
                    |
    +---------------+---------------+
    |               |               |
  Finnhub      Alpha Vantage    Web Search
  (Ticker,      (Revenue,       (Industry
   Metrics,      Income          trends,
   Peers)        Statement)      benchmarks)
    |               |               |
    +-------+-------+-------+-------+
            |               |
            v               v
    +------------------+  +------------------+
    |  STEP 1          |  |  RAG KNOWLEDGE   |
    |  Data Ingestion  |  |  BASE            |
    |  Agent           |  |  (Documents,     |
    |                  |  |   Embeddings)    |
    +--------+---------+  +--------+---------+
             |                     |
             v                     | (context injected into all agents)
    +------------------+           |
    |  STEP 2          |<----------+
    |  Value Stream    |
    |  Research Agent  |
    +--------+---------+
             |
             v
    +------------------+
    |  STEP 3          |<--- Reads: Steps 1 + 2 data
    |  SWOT/TOWS       |
    |  Agent           |
    +--------+---------+
             |
             v
    +------------------+
    |  STEP 4          |<--- Reads: Steps 1 + 2 + 3 data
    |  Strategy & OKR  |     + User strategy inputs
    |  Agent           |
    +--------+---------+
             |
             v  (requires strategy approval)
    +------------------+
    |  STEP 5          |<--- Reads: Approved strategies + OKRs
    |  Initiative &    |     + Steps 1-4 context
    |  RICE Agent      |
    +--------+---------+
             |
             v
    +------------------+
    |  STEP 6          |<--- Reads: Initiatives + Steps 1-5 context
    |  Epic & Team     |     Creates teams from strategy context
    |  Agent           |
    +--------+---------+
             |
             v
    +------------------+
    |  STEP 7          |<--- Reads: Epics + team assignments
    |  Feature &       |     + Steps 1-6 context
    |  Roadmap Agent   |
    +------------------+
             |
             v
    +------------------+
    |  7 REVIEW GATES  |
    |  (Human-in-the-  |
    |   loop approval) |
    +------------------+
```

---

## Key Concepts

### OKR Cascade
Objectives and Key Results flow down through three levels, getting more specific at each level:

| Level | Set In | Example Objective | Example Key Result |
|-------|--------|-------------------|--------------------|
| **Strategic** | Step 4 | Increase customer acquisition by 25% | Reduce churn rate from 12% to 8% |
| **Product** | Step 6 | Reduce onboarding time to 1 day | 80% same-day application completion |
| **Delivery** | Step 7 | Ship onboarding MVP in Sprint 3 | All features passing acceptance tests |

### Decomposition Hierarchy
Work items get more granular at each step:

```
Strategy (Step 4)          "Unified Digital Banking Platform"
  └─ Initiative (Step 5)   "AI-Powered Customer Onboarding" (RICE: 3.2)
       └─ Epic (Step 6)    "Build Identity Verification API" (30 days)
            └─ Feature (Step 7)  "Add Document Upload Component" (13 SP)
```

### RICE Prioritization
Every initiative gets scored to determine priority:
- **High RICE (>5)**: Quick Wins — do first
- **Medium RICE (2-5)**: Strategic — plan for next quarter
- **Low RICE (<2)**: Long Term — future consideration

### 4-Layer Strategy Model
Every transformation addresses four complementary dimensions:
1. **Business**: What processes and market positions to improve
2. **Digital**: What technology to build or adopt
3. **Data**: What insights and analytics to enable
4. **Gen AI**: What AI/ML capabilities to deploy

### Demo vs Live Mode
- **Demo mode** (default): Uses API data + AI generation only. Fast, no document persistence.
- **Live mode**: Enables RAG knowledge base. Uploaded documents are chunked, embedded, and used to enhance all AI analysis with organization-specific context.

---

## Typical User Journey

### Quick Demo (5 minutes)
1. Open app → Enter "US Bancorp" + "Financial Services"
2. Click **"Generate All Steps"** → Wait 3-5 minutes
3. Review each step's auto-generated data
4. Navigate through Steps 1-7 to explore results

### Detailed Analysis (30-60 minutes)
1. **Step 1**: Enter company → Review ingested data → Upload additional documents → Run AI Dashboard analysis
2. **Step 2**: Create value streams → Pull from sources → Review bottlenecks and benchmarks
3. **Step 3**: Auto-generate SWOT → Adjust severity scores → Review TOWS actions
4. **Step 4**: Provide strategy inputs → Auto-generate → Review 4-layer strategies → **Approve all**
5. **Step 5**: Generate initiatives → Review RICE scores → Adjust roadmap phases
6. **Step 6**: Generate teams and epics → Review assignments → Adjust effort estimates
7. **Step 7**: Generate features → Review user stories → Finalize backlog
8. **Gates**: Approve each review gate with notes

### Knowledge-Enhanced Analysis (Live Mode)
1. Switch to **Live mode** in Step 1
2. Upload company documents (annual reports, strategy decks, process maps)
3. Documents are chunked and embedded into knowledge base
4. Run generation — all agents now include document context in their analysis
5. Results are more specific and grounded in your actual organizational data
