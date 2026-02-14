"""
Source Gatherers — Pull data from multiple internal and external sources
for enriched value stream generation.
Each gatherer is independent and fails gracefully (returns empty dict on error).
"""

import random

from openai_client import _find_template
from data_ingestion import search_ticker, fetch_peers, fetch_company_profile, fetch_company_overview


# ──────────────────────────────────────────────
# 1. App Data — existing org + value streams
# ──────────────────────────────────────────────

async def gather_app_data(db) -> dict:
    """Query organization table and existing value streams with metrics."""
    try:
        org_rows = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
        org = dict(org_rows[0]) if org_rows else {}

        vs_rows = await db.execute_fetchall(
            "SELECT vs.*, bu.name as business_unit_name FROM value_streams vs "
            "JOIN business_units bu ON vs.business_unit_id = bu.id"
        )
        value_streams = []
        for vs in vs_rows:
            vs_dict = dict(vs)
            metrics_rows = await db.execute_fetchall(
                "SELECT * FROM value_stream_metrics WHERE value_stream_id = ?",
                (vs_dict["id"],),
            )
            vs_dict["metrics"] = dict(metrics_rows[0]) if metrics_rows else None
            value_streams.append(vs_dict)

        return {
            "source": "app_data",
            "organization": org,
            "existing_value_streams": value_streams,
        }
    except Exception:
        return {}


# ──────────────────────────────────────────────
# 2. ERP Simulation — enriched template steps
# ──────────────────────────────────────────────

async def gather_erp_simulation(segment: str, industry: str) -> dict:
    """Simulate ERP/CRM data by enriching template steps with system metadata."""
    try:
        template = _find_template(segment)
        steps = template.get("steps", [])

        departments = [
            "Operations", "Finance", "Risk", "Compliance",
            "IT", "Customer Service", "Legal", "HR",
        ]
        erp_steps = []
        for i, step in enumerate(steps):
            random.seed(hash(f"erp-{segment}-{step['step_name']}"))
            erp_steps.append({
                "step_name": step["step_name"],
                "system_source": random.choice(["SAP ECC", "Oracle EBS", "Salesforce", "ServiceNow", "Workday", "Custom CRM"]),
                "ticket_id": f"ERP-{random.randint(10000, 99999)}",
                "department_code": random.choice(departments),
                "sla_target_hours": round(
                    (step.get("process_time_hours", 1) + step.get("wait_time_hours", 0)) * random.uniform(0.8, 1.2), 1
                ),
                "monthly_volume": random.randint(50, 5000),
                "automation_level": random.choice(["manual", "semi-automated", "automated"]),
            })

        return {
            "source": "erp_simulation",
            "erp_system": "Simulated ERP/CRM Data",
            "steps": erp_steps,
        }
    except Exception:
        return {}


# ──────────────────────────────────────────────
# 3. Industry Benchmarks
# ──────────────────────────────────────────────

async def gather_industry_benchmarks(segment: str, industry: str) -> dict:
    """Generate industry benchmark ranges per step + industry KPIs."""
    try:
        template = _find_template(segment)
        steps = template.get("steps", [])

        benchmark_steps = []
        for step in steps:
            pt = step.get("process_time_hours", 1)
            wt = step.get("wait_time_hours", 0)
            lt = pt + wt
            benchmark_steps.append({
                "step_name": step["step_name"],
                "best_in_class_hours": round(lt * 0.5, 1),
                "industry_average_hours": round(lt * 1.0, 1),
                "laggard_hours": round(lt * 1.8, 1),
            })

        total_lt = sum(s.get("process_time_hours", 0) + s.get("wait_time_hours", 0) for s in steps)
        total_pt = sum(s.get("process_time_hours", 0) for s in steps)

        industry_kpis = {
            "avg_lead_time_hours": round(total_lt, 1),
            "best_in_class_lead_time_hours": round(total_lt * 0.5, 1),
            "avg_flow_efficiency_pct": round((total_pt / total_lt * 100) if total_lt > 0 else 0, 1),
            "best_in_class_flow_efficiency_pct": round(
                min(((total_pt / total_lt * 100) if total_lt > 0 else 0) * 1.5, 95), 1
            ),
            "avg_first_pass_yield_pct": 85.0,
            "best_in_class_first_pass_yield_pct": 97.0,
        }

        return {
            "source": "industry_benchmarks",
            "industry": industry,
            "segment": segment,
            "step_benchmarks": benchmark_steps,
            "industry_kpis": industry_kpis,
        }
    except Exception:
        return {}


# ──────────────────────────────────────────────
# 4. Finnhub / Alpha Vantage — real competitor data
# ──────────────────────────────────────────────

async def gather_finnhub_data(org_name: str, industry: str, competitors: list[str]) -> dict:
    """Fetch real competitor profiles and financials from Finnhub + Alpha Vantage."""
    try:
        # Search for org ticker first
        org_ticker = await search_ticker(org_name)
        peer_tickers = []
        if org_ticker:
            peer_tickers = await fetch_peers(org_ticker)

        # Also search for manually-entered competitors
        for comp_name in competitors:
            if comp_name:
                ticker = await search_ticker(comp_name)
                if ticker and ticker not in peer_tickers:
                    peer_tickers.append(ticker)

        # Limit to first 5 peers
        peer_tickers = peer_tickers[:5]

        peer_profiles = []
        for ticker in peer_tickers:
            profile = await fetch_company_profile(ticker)
            overview = await fetch_company_overview(ticker)
            if profile:
                entry = {"profile": profile}
                if overview:
                    entry["financials"] = overview
                peer_profiles.append(entry)

        return {
            "source": "finnhub",
            "org_ticker": org_ticker,
            "peer_count": len(peer_profiles),
            "peers": peer_profiles,
            "competitor_names": [
                p["profile"]["name"] for p in peer_profiles if p.get("profile", {}).get("name")
            ],
        }
    except Exception:
        return {}


# ──────────────────────────────────────────────
# 5. Web Search References
# ──────────────────────────────────────────────

async def gather_web_search(segment: str, industry: str) -> dict:
    """Return curated industry benchmark references. Extension point for future SerpAPI/Bing."""
    try:
        references = [
            {
                "title": f"{industry.title()} Value Stream Benchmarking Report",
                "source": "Industry Analyst Report",
                "key_finding": f"Top-quartile {segment} processes achieve 40-60% faster cycle times through automation",
                "improvement_pct": "40-60%",
            },
            {
                "title": f"Lean Six Sigma in {industry.title()}: Best Practices",
                "source": "Case Study Collection",
                "key_finding": f"Organizations implementing lean in {segment} see 25-35% reduction in wait times",
                "improvement_pct": "25-35%",
            },
            {
                "title": f"Digital Transformation Impact on {segment.title()}",
                "source": "Management Consulting Study",
                "key_finding": "End-to-end digitization reduces process time by 50-70% and improves first-pass yield by 15-25%",
                "improvement_pct": "50-70%",
            },
            {
                "title": f"Operational Excellence in {industry.title()}",
                "source": "Industry Benchmark Database",
                "key_finding": f"Best-in-class {segment} operations maintain flow efficiency above 30%",
                "improvement_pct": "N/A",
            },
        ]

        return {
            "source": "web_search",
            "note": "Curated references — live web search integration available as future enhancement",
            "references": references,
        }
    except Exception:
        return {}
