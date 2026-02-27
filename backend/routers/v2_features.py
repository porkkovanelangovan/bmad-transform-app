"""
V2 Features Router — Patterns DB, Risk Registry, AI Feedback, Collaboration,
Competitive Intel, Benchmarks, ROI Calculator, Executive Briefing, Pilot Scopes,
Tech Recommendations, Multi-Scenario, Process Mining config, Multi-Model config.
(Enhancements #6, #7, #11, #12, #13, #14, #15-25)
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available, extract_list

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Enhancement #12: Transformation Patterns ─────────────────────────────


@router.get("/patterns")
async def get_patterns(industry: str = None, db=Depends(get_db)):
    if industry:
        rows = await db.execute_fetchall(
            "SELECT * FROM transformation_patterns WHERE industry = ? OR industry = 'all' ORDER BY pattern_name",
            [industry],
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM transformation_patterns ORDER BY industry, pattern_name")
    return [dict(r) for r in rows]


@router.post("/patterns/seed")
async def seed_patterns(db=Depends(get_db)):
    """Seed transformation patterns database."""
    existing = await db.execute_fetchone("SELECT COUNT(*) as c FROM transformation_patterns")
    if existing and existing["c"] > 0:
        return {"message": "Patterns already seeded", "count": existing["c"]}

    patterns = [
        ("Digital Channel Migration", "banking", "High branch costs, low digital adoption", "digital", "Migrate customers from physical to digital channels", "30-50% cost reduction, improved CX", "Basic digital infrastructure", "Customer segment abandonment"),
        ("API-First Platform", "banking", "Siloed systems, slow integration", "digital", "Build API layer across core systems for composability", "50% faster integration, partner ecosystem", "API gateway, developer portal", "Legacy system complexity"),
        ("AI-Powered Credit Decisioning", "banking", "Slow underwriting, manual processes", "gen_ai", "Deploy ML models for credit risk and decisioning", "60% faster decisions, reduced defaults", "Quality historical data", "Model bias, regulatory scrutiny"),
        ("Real-Time Fraud Detection", "banking", "Rising fraud losses, batch processing", "data", "Implement real-time transaction monitoring with ML", "70% fraud reduction", "Streaming data platform", "False positive management"),
        ("Cloud-Native Core Banking", "banking", "Legacy mainframe, high maintenance", "digital", "Replace or wrap core banking with cloud-native", "40% TCO reduction, faster deployment", "Cloud strategy, vendor selection", "Migration risk, regulatory approval"),
        ("Hyper-Personalization Engine", "banking", "Generic customer offers, low conversion", "gen_ai", "Use AI to personalize offers, content, and pricing", "3x conversion improvement", "Customer data platform", "Privacy concerns, data quality"),
        ("Process Mining & Automation", "banking", "Unknown process bottlenecks", "data", "Deploy process mining to discover and automate", "30% efficiency gain", "Event log data", "Change resistance"),
        ("Open Banking Ecosystem", "banking", "Closed ecosystem, limited partnerships", "business", "Build open banking platform and partner marketplace", "New revenue streams", "API platform, compliance framework", "Security, data sharing concerns"),
        ("Data Mesh Architecture", "banking", "Centralized data bottleneck", "data", "Implement domain-oriented data ownership and sharing", "4x faster data delivery", "Data governance framework", "Cultural shift, complexity"),
        ("GenAI Customer Service", "banking", "High contact center costs", "gen_ai", "Deploy conversational AI for customer interactions", "40% call deflection", "Knowledge base, training data", "Hallucination risk, CX degradation"),
        ("Regulatory Tech (RegTech)", "banking", "Manual compliance, high cost", "digital", "Automate regulatory reporting and compliance", "50% compliance cost reduction", "Structured regulatory data", "Regulatory change pace"),
        ("Embedded Finance", "banking", "Limited distribution channels", "business", "Embed financial products in partner platforms", "New customer acquisition channels", "API platform, partnerships", "Brand dilution"),
        ("Zero-Trust Security", "banking", "Perimeter-based security gaps", "digital", "Implement zero-trust architecture across all systems", "Reduced breach risk", "Identity management platform", "Complexity, user friction"),
        ("Sustainable Finance Platform", "banking", "ESG compliance gaps", "business", "Build ESG scoring and sustainable product platform", "Regulatory compliance, new market", "ESG data sources", "Data availability, greenwashing risk"),
        ("Digital Twin Operations", "banking", "Reactive operations", "data", "Create digital twins of key business processes", "Predictive operations, scenario planning", "Real-time data feeds", "Implementation complexity"),
        ("Claims Automation", "insurance", "Slow claims processing", "gen_ai", "AI-powered claims assessment and processing", "60% faster settlement", "Historical claims data", "Complex claims handling"),
        ("Telematics Integration", "insurance", "Limited risk data for pricing", "data", "IoT/telematics data for usage-based insurance", "Better risk pricing, lower loss ratios", "IoT infrastructure", "Privacy, data volume"),
        ("Patient Digital Experience", "healthcare", "Fragmented patient journey", "digital", "Unified digital patient portal and engagement", "Improved patient satisfaction", "EHR integration", "Interoperability, privacy"),
        ("Clinical AI Decision Support", "healthcare", "Diagnostic variability", "gen_ai", "AI-assisted diagnosis and treatment planning", "Improved outcomes, reduced variation", "Quality clinical data", "Liability, trust"),
        ("Supply Chain Digitization", "retail", "Manual supply chain, poor visibility", "digital", "End-to-end digital supply chain with real-time tracking", "30% inventory reduction", "IoT sensors, ERP integration", "Supplier adoption"),
        ("Omnichannel Commerce", "retail", "Disconnected channels", "digital", "Unified commerce across physical and digital", "20% revenue uplift", "Unified customer data", "System integration complexity"),
        ("Demand Forecasting AI", "retail", "Inaccurate demand planning", "gen_ai", "ML-based demand forecasting and auto-replenishment", "40% forecast accuracy improvement", "Historical sales data", "Seasonal volatility"),
        ("Customer Data Platform", "all", "Fragmented customer data", "data", "Unified CDP for 360-degree customer view", "Improved personalization, analytics", "Data governance", "Data quality, integration"),
        ("DevOps Transformation", "all", "Slow release cycles", "digital", "CI/CD, IaC, platform engineering adoption", "10x deployment frequency", "Cloud infrastructure", "Cultural change"),
        ("Data Governance Framework", "all", "Poor data quality, no ownership", "data", "Implement data governance with stewards and policies", "Improved data trust and compliance", "Executive sponsorship", "Cultural adoption"),
    ]

    for p in patterns:
        await db.execute(
            "INSERT INTO transformation_patterns (pattern_name, industry, trigger_condition, strategy_type, "
            "description, typical_outcomes, prerequisites, risks, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seed')",
            list(p),
        )
    await db.commit()
    return {"seeded": len(patterns)}


# ─── Enhancement #19: Industry Profiles ─────────────────────────────────


@router.get("/industry-profiles")
async def get_industry_profiles(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM industry_profiles ORDER BY industry")
    return [dict(r) for r in rows]


@router.post("/industry-profiles/seed")
async def seed_industry_profiles(db=Depends(get_db)):
    """Seed industry profiles."""
    existing = await db.execute_fetchone("SELECT COUNT(*) as c FROM industry_profiles")
    if existing and existing["c"] > 0:
        return {"message": "Already seeded", "count": existing["c"]}

    profiles = [
        ("Financial Services",
         json.dumps(["Account Opening", "Lending", "Payments", "Wealth Management", "Claims Processing"]),
         json.dumps({"strengths": ["Strong regulatory compliance", "Established trust"], "threats": ["Fintech disruption", "Regulatory complexity"]}),
         json.dumps(["OCC", "CFPB", "Basel III", "BSA/AML", "Fair Lending"]),
         json.dumps({"avg_digital_maturity": 2.8, "avg_cloud_adoption": 35, "avg_ai_adoption": 22}),
         json.dumps(["Digital-First Banking", "Platform Banking", "AI-Powered Operations"])),
        ("Insurance",
         json.dumps(["Underwriting", "Claims", "Policy Admin", "Distribution", "Risk Assessment"]),
         json.dumps({"strengths": ["Deep risk expertise", "Large data sets"], "threats": ["InsurTech disruption", "Climate risk"]}),
         json.dumps(["Solvency II", "NAIC", "GDPR", "State regulations"]),
         json.dumps({"avg_digital_maturity": 2.4, "avg_cloud_adoption": 28, "avg_ai_adoption": 18}),
         json.dumps(["Connected Insurance", "Usage-Based Products", "Automated Claims"])),
        ("Healthcare",
         json.dumps(["Patient Registration", "Clinical Care", "Billing", "Pharmacy", "Population Health"]),
         json.dumps({"strengths": ["Clinical expertise", "Patient relationships"], "threats": ["Regulatory complexity", "Cybersecurity"]}),
         json.dumps(["HIPAA", "FDA", "CMS", "State health regulations"]),
         json.dumps({"avg_digital_maturity": 2.2, "avg_cloud_adoption": 30, "avg_ai_adoption": 15}),
         json.dumps(["Digital Health Platform", "AI-Assisted Diagnosis", "Virtual Care"])),
        ("Retail",
         json.dumps(["Sourcing", "Merchandising", "Marketing", "Commerce", "Fulfillment", "Returns"]),
         json.dumps({"strengths": ["Customer data", "Brand recognition"], "threats": ["Amazon effect", "Supply chain disruption"]}),
         json.dumps(["PCI-DSS", "GDPR/CCPA", "Consumer protection"]),
         json.dumps({"avg_digital_maturity": 3.1, "avg_cloud_adoption": 45, "avg_ai_adoption": 28}),
         json.dumps(["Omnichannel Commerce", "Personalization Engine", "Autonomous Supply Chain"])),
    ]

    for p in profiles:
        await db.execute(
            "INSERT INTO industry_profiles (industry, value_stream_templates, swot_patterns, regulatory_framework, benchmarks, strategy_archetypes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            list(p),
        )
    await db.commit()
    return {"seeded": len(profiles)}


# ─── Enhancement #16: Risk Registry ─────────────────────────────────────


@router.get("/risks")
async def get_risks(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM risk_registry WHERE org_id = ? ORDER BY risk_score DESC", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/risks")
async def create_risk(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    prob = data.get("probability", 3)
    impact = data.get("impact_score", 3)
    await db.execute(
        "INSERT INTO risk_registry (org_id, risk_name, category, probability, impact_score, risk_score, mitigation, owner, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [org["id"], data.get("risk_name"), data.get("category", ""), prob, impact, prob * impact,
         data.get("mitigation", ""), data.get("owner", ""), data.get("status", "open")],
    )
    await db.commit()
    return {"success": True}


@router.put("/risks/{item_id}")
async def update_risk(item_id: int, data: dict, db=Depends(get_db)):
    prob = data.get("probability", 3)
    impact = data.get("impact_score", 3)
    await db.execute(
        "UPDATE risk_registry SET risk_name=?, category=?, probability=?, impact_score=?, risk_score=?, "
        "mitigation=?, owner=?, status=? WHERE id=?",
        [data.get("risk_name"), data.get("category", ""), prob, impact, prob * impact,
         data.get("mitigation", ""), data.get("owner", ""), data.get("status", "open"), item_id],
    )
    await db.commit()
    return {"success": True}


@router.delete("/risks/{item_id}")
async def delete_risk(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM risk_registry WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


@router.post("/risks/ai-generate")
async def ai_generate_risks(db=Depends(get_db)):
    """AI-generate risk registry from strategies and initiatives."""
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]

    strategies = await db.execute_fetchall("SELECT name, description, risks FROM strategies")
    initiatives = await db.execute_fetchall("SELECT name, description, risks FROM initiatives")

    if not is_openai_available():
        risk_templates = [
            ("Technology Integration Risk", "technology", 4, 4),
            ("Change Resistance Risk", "organizational", 3, 3),
            ("Regulatory Compliance Risk", "regulatory", 3, 5),
            ("Talent Shortage Risk", "talent", 4, 3),
            ("Data Quality Risk", "data", 3, 4),
            ("Cybersecurity Risk", "security", 2, 5),
            ("Budget Overrun Risk", "financial", 3, 4),
            ("Vendor Dependency Risk", "vendor", 3, 3),
        ]
        count = 0
        for name, cat, prob, impact in risk_templates:
            existing = await db.execute_fetchone(
                "SELECT id FROM risk_registry WHERE org_id = ? AND risk_name = ?", [org_id, name]
            )
            if not existing:
                await db.execute(
                    "INSERT INTO risk_registry (org_id, risk_name, category, probability, impact_score, risk_score, "
                    "mitigation, ai_generated, ai_confidence) VALUES (?, ?, ?, ?, ?, ?, 'Mitigation TBD', 1, 50)",
                    [org_id, name, cat, prob, impact, prob * impact],
                )
                count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    ctx = "Strategies: " + ", ".join([dict(s).get("name", "") for s in strategies])
    ctx += "\nInitiatives: " + ", ".join([dict(i).get("name", "") for i in initiatives])
    prompt = f"""Identify the top 10 transformation risks for this organization based on:
{ctx}

For each risk provide:
- risk_name, category (technology/organizational/regulatory/talent/data/security/financial/vendor),
  probability (1-5), impact_score (1-5), mitigation, confidence (0-100)

Return JSON array."""

    result = await call_openai_json(prompt)
    count = 0
    for item in extract_list(result):
        prob = item.get("probability", 3)
        impact = item.get("impact_score", 3)
        await db.execute(
            "INSERT INTO risk_registry (org_id, risk_name, category, probability, impact_score, risk_score, "
            "mitigation, ai_generated, ai_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
            [org_id, item.get("risk_name", ""), item.get("category", ""), prob, impact,
             prob * impact, item.get("mitigation", ""), item.get("confidence", 70)],
        )
        count += 1
    await db.commit()
    return {"generated": count, "ai": True}


# ─── Enhancement #17: AI Feedback ───────────────────────────────────────


@router.post("/feedback")
async def submit_feedback(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO ai_feedback (entity_type, entity_id, original_text, edited_text, feedback_type) "
        "VALUES (?, ?, ?, ?, ?)",
        [data.get("entity_type"), data.get("entity_id"), data.get("original_text", ""),
         data.get("edited_text", ""), data.get("feedback_type", "edit")],
    )
    await db.commit()
    return {"success": True}


@router.get("/feedback/stats")
async def feedback_stats(db=Depends(get_db)):
    total = await db.execute_fetchone("SELECT COUNT(*) as c FROM ai_feedback")
    edits = await db.execute_fetchone("SELECT COUNT(*) as c FROM ai_feedback WHERE feedback_type = 'edit'")
    accepts = await db.execute_fetchone("SELECT COUNT(*) as c FROM ai_feedback WHERE feedback_type = 'accept'")
    rejects = await db.execute_fetchone("SELECT COUNT(*) as c FROM ai_feedback WHERE feedback_type = 'reject'")
    return {
        "total": total["c"] if total else 0,
        "edits": edits["c"] if edits else 0,
        "accepts": accepts["c"] if accepts else 0,
        "rejects": rejects["c"] if rejects else 0,
        "accuracy_rate": round(
            (accepts["c"] if accepts else 0) / max((total["c"] if total else 1), 1) * 100
        ),
    }


# ─── Enhancement #20: Comments ──────────────────────────────────────────


@router.get("/comments")
async def get_comments(entity_type: str, entity_id: int, db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM comments WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC",
        [entity_type, entity_id],
    )
    return [dict(r) for r in rows]


@router.post("/comments")
async def create_comment(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO comments (entity_type, entity_id, user_name, comment_text) VALUES (?, ?, ?, ?)",
        [data.get("entity_type"), data.get("entity_id"), data.get("user_name", "User"),
         data.get("comment_text", "")],
    )
    await db.commit()
    return {"success": True}


@router.delete("/comments/{item_id}")
async def delete_comment(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM comments WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


# ─── Enhancement #21: Pipeline Runs ─────────────────────────────────────


@router.get("/pipeline-runs")
async def get_pipeline_runs(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM pipeline_runs WHERE org_id = ? ORDER BY started_at DESC LIMIT 20", [org["id"]]
    )
    return [dict(r) for r in rows]


# ─── Enhancement #22: Competitive Alerts ─────────────────────────────────


@router.get("/competitive-alerts")
async def get_competitive_alerts(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM competitive_alerts WHERE org_id = ? ORDER BY created_at DESC LIMIT 50", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/competitive-alerts/refresh")
async def refresh_competitive_alerts(db=Depends(get_db)):
    """Fetch latest competitive news from Finnhub."""
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    org_dict = dict(org)

    competitors = await db.execute_fetchall("SELECT name, ticker FROM competitors")
    count = 0

    try:
        import os, httpx
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            return {"error": "FINNHUB_API_KEY not configured"}
        async with httpx.AsyncClient() as http:
            for comp in competitors:
                cd = dict(comp)
                ticker = cd.get("ticker")
                if not ticker:
                    continue
                resp = await http.get(
                    f"https://finnhub.io/api/v1/company-news",
                    params={"symbol": ticker, "from": "2024-01-01", "to": "2025-12-31", "token": finnhub_key},
                    timeout=15,
                )
                if resp.status_code == 200:
                    news = resp.json()
                    if isinstance(news, list):
                        for article in news[:5]:
                            await db.execute(
                                "INSERT INTO competitive_alerts (org_id, competitor_name, alert_type, headline, summary, source_url, severity) "
                                "VALUES (?, ?, 'news', ?, ?, ?, 'info')",
                                [org_id, cd.get("name", ticker), article.get("headline", ""),
                                 article.get("summary", ""), article.get("url", "")],
                            )
                            count += 1
        await db.commit()
    except Exception as e:
        logger.warning("Competitive alert refresh failed: %s", e)
        return {"error": str(e)}

    return {"alerts_added": count}


@router.put("/competitive-alerts/{item_id}/read")
async def mark_alert_read(item_id: int, db=Depends(get_db)):
    await db.execute("UPDATE competitive_alerts SET is_read = 1 WHERE id = ?", [item_id])
    await db.commit()
    return {"success": True}


# ─── Enhancement #23: Benchmarks ────────────────────────────────────────


@router.get("/benchmarks")
async def get_benchmarks(industry: str = None, db=Depends(get_db)):
    if industry:
        rows = await db.execute_fetchall(
            "SELECT * FROM benchmarks WHERE industry = ? ORDER BY metric_name", [industry]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM benchmarks ORDER BY industry, metric_name")
    return [dict(r) for r in rows]


@router.post("/benchmarks/seed")
async def seed_benchmarks(db=Depends(get_db)):
    """Seed benchmark data."""
    existing = await db.execute_fetchone("SELECT COUNT(*) as c FROM benchmarks")
    if existing and existing["c"] > 0:
        return {"message": "Already seeded", "count": existing["c"]}

    benchmarks_data = [
        ("Financial Services", "Digital Channel Adoption", 65, 45, 65, 82, "Industry Report 2024"),
        ("Financial Services", "Cost-to-Income Ratio", 55, 48, 55, 62, "Industry Report 2024"),
        ("Financial Services", "Customer Satisfaction (NPS)", 42, 28, 42, 58, "Industry Report 2024"),
        ("Financial Services", "Cloud Adoption %", 40, 25, 40, 60, "Industry Report 2024"),
        ("Financial Services", "AI/ML Use Cases in Production", 8, 3, 8, 15, "Industry Report 2024"),
        ("Financial Services", "Time-to-Market (weeks)", 16, 8, 16, 24, "Industry Report 2024"),
        ("Insurance", "Claims Processing Time (days)", 12, 5, 12, 22, "Industry Report 2024"),
        ("Insurance", "Digital Policy Issuance %", 35, 20, 35, 55, "Industry Report 2024"),
        ("Healthcare", "Patient Portal Adoption %", 55, 35, 55, 72, "Industry Report 2024"),
        ("Healthcare", "EHR Interoperability Score", 3.2, 2.0, 3.2, 4.5, "Industry Report 2024"),
        ("Retail", "E-commerce Revenue %", 28, 15, 28, 45, "Industry Report 2024"),
        ("Retail", "Inventory Turnover", 8.5, 5.0, 8.5, 12.0, "Industry Report 2024"),
    ]

    for b in benchmarks_data:
        await db.execute(
            "INSERT INTO benchmarks (industry, metric_name, metric_value, percentile_25, percentile_50, percentile_75, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            list(b),
        )
    await db.commit()
    return {"seeded": len(benchmarks_data)}


# ─── Enhancement #25: ROI Calculator (Portfolio View) ────────────────────


@router.get("/roi-portfolio")
async def roi_portfolio(db=Depends(get_db)):
    """Aggregate business cases across all initiatives."""
    rows = await db.execute_fetchall(
        "SELECT i.id, i.name, i.estimated_cost_k, i.annual_benefit_k, i.npv_k, i.payback_months, i.roi_pct, "
        "i.status, dp.name as product_name "
        "FROM initiatives i "
        "JOIN digital_products dp ON i.digital_product_id = dp.id "
        "WHERE i.estimated_cost_k IS NOT NULL "
        "ORDER BY i.roi_pct DESC NULLS LAST"
    )
    items = [dict(r) for r in rows]
    total_cost = sum(r.get("estimated_cost_k") or 0 for r in items)
    total_benefit = sum(r.get("annual_benefit_k") or 0 for r in items)
    total_npv = sum(r.get("npv_k") or 0 for r in items)
    avg_roi = round(sum(r.get("roi_pct") or 0 for r in items) / max(len(items), 1), 1)

    return {
        "initiatives": items,
        "portfolio_summary": {
            "total_investment_k": round(total_cost, 1),
            "total_annual_benefit_k": round(total_benefit, 1),
            "total_npv_k": round(total_npv, 1),
            "average_roi_pct": avg_roi,
            "initiative_count": len(items),
        },
    }


# ─── Enhancement #6: Pilot Scopes ───────────────────────────────────────


@router.get("/pilot-scopes")
async def get_pilot_scopes(initiative_id: int = None, db=Depends(get_db)):
    if initiative_id:
        rows = await db.execute_fetchall(
            "SELECT * FROM pilot_scopes WHERE initiative_id = ?", [initiative_id]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM pilot_scopes ORDER BY initiative_id")
    return [dict(r) for r in rows]


@router.post("/pilot-scopes")
async def create_pilot_scope(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO pilot_scopes (initiative_id, mvp_description, success_criteria, duration_weeks, "
        "team_size, go_nogo_criteria, scale_up_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [data.get("initiative_id"), data.get("mvp_description", ""), data.get("success_criteria", ""),
         data.get("duration_weeks", 8), data.get("team_size", 5),
         data.get("go_nogo_criteria", ""), data.get("scale_up_path", "")],
    )
    await db.commit()
    return {"success": True}


@router.post("/pilot-scopes/ai-generate")
async def ai_generate_pilot_scopes(data: dict, db=Depends(get_db)):
    """AI-generate pilot scope for initiatives."""
    initiative_id = data.get("initiative_id")
    if initiative_id:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives WHERE id = ?", [initiative_id])
    else:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives LIMIT 10")

    if not initiatives:
        return {"error": "No initiatives found"}

    init_list = [dict(i) for i in initiatives]

    if not is_openai_available():
        count = 0
        for init in init_list:
            existing = await db.execute_fetchone(
                "SELECT id FROM pilot_scopes WHERE initiative_id = ?", [init["id"]]
            )
            if not existing:
                await db.execute(
                    "INSERT INTO pilot_scopes (initiative_id, mvp_description, success_criteria, duration_weeks, "
                    "team_size, go_nogo_criteria, scale_up_path, ai_generated, ai_confidence) "
                    "VALUES (?, 'MVP scope pending', 'Success criteria TBD', 8, 5, 'Go/No-Go TBD', 'Scale path TBD', 1, 50)",
                    [init["id"]],
                )
                count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    count = 0
    for init in init_list:
        existing = await db.execute_fetchone("SELECT id FROM pilot_scopes WHERE initiative_id = ?", [init["id"]])
        if existing:
            continue
        prompt = f"""Design a pilot/MVP scope for this initiative:
Name: {init['name']}
Description: {init.get('description', '')}

Provide: mvp_description, success_criteria, duration_weeks, team_size, go_nogo_criteria, scale_up_path, confidence (0-100)
Return JSON object."""

        result = await call_openai_json(prompt)
        if isinstance(result, dict):
            await db.execute(
                "INSERT INTO pilot_scopes (initiative_id, mvp_description, success_criteria, duration_weeks, "
                "team_size, go_nogo_criteria, scale_up_path, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
                [init["id"], result.get("mvp_description", ""), result.get("success_criteria", ""),
                 result.get("duration_weeks", 8), result.get("team_size", 5),
                 result.get("go_nogo_criteria", ""), result.get("scale_up_path", ""),
                 result.get("confidence", 70)],
            )
            count += 1
    await db.commit()
    return {"generated": count, "ai": True}


# ─── Enhancement #13: Tech Recommendations ──────────────────────────────


@router.get("/tech-recommendations")
async def get_tech_recommendations(initiative_id: int = None, db=Depends(get_db)):
    if initiative_id:
        rows = await db.execute_fetchall(
            "SELECT * FROM tech_recommendations WHERE initiative_id = ?", [initiative_id]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM tech_recommendations ORDER BY initiative_id")
    return [dict(r) for r in rows]


@router.post("/tech-recommendations/ai-generate")
async def ai_generate_tech(data: dict, db=Depends(get_db)):
    """AI-generate tech architecture recommendations."""
    initiative_id = data.get("initiative_id")
    if initiative_id:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives WHERE id = ?", [initiative_id])
    else:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives LIMIT 10")

    if not initiatives:
        return {"error": "No initiatives found"}

    init_list = [dict(i) for i in initiatives]

    if not is_openai_available():
        count = 0
        components = ["frontend", "backend", "data_layer", "integration"]
        for init in init_list:
            for comp in components:
                existing = await db.execute_fetchone(
                    "SELECT id FROM tech_recommendations WHERE initiative_id = ? AND component = ?",
                    [init["id"], comp],
                )
                if not existing:
                    await db.execute(
                        "INSERT INTO tech_recommendations (initiative_id, component, recommendation, platform_options, "
                        "integration_pattern, cloud_model, tech_risks, ai_generated, ai_confidence) "
                        "VALUES (?, ?, 'build', 'Options TBD', 'API-based', 'hybrid', 'Risks TBD', 1, 50)",
                        [init["id"], comp],
                    )
                    count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    count = 0
    for init in init_list:
        prompt = f"""Recommend technology architecture for this initiative:
Name: {init['name']}
Description: {init.get('description', '')}

For each technology component (frontend, backend, data_layer, integration, security), provide:
- component, recommendation (build/buy/partner), platform_options,
  integration_pattern, cloud_model, tech_risks, confidence (0-100)

Return JSON array."""

        result = await call_openai_json(prompt)
        for item in extract_list(result):
                comp = item.get("component", "")
                existing = await db.execute_fetchone(
                    "SELECT id FROM tech_recommendations WHERE initiative_id = ? AND component = ?",
                    [init["id"], comp],
                )
                if existing:
                    await db.execute(
                        "UPDATE tech_recommendations SET recommendation=?, platform_options=?, integration_pattern=?, "
                        "cloud_model=?, tech_risks=?, ai_generated=1, ai_confidence=? WHERE id=?",
                        [item.get("recommendation", "build"), item.get("platform_options", ""),
                         item.get("integration_pattern", ""), item.get("cloud_model", ""),
                         item.get("tech_risks", ""), item.get("confidence", 70), existing["id"]],
                    )
                else:
                    await db.execute(
                        "INSERT INTO tech_recommendations (initiative_id, component, recommendation, platform_options, "
                        "integration_pattern, cloud_model, tech_risks, ai_generated, ai_confidence) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
                        [init["id"], comp, item.get("recommendation", "build"),
                         item.get("platform_options", ""), item.get("integration_pattern", ""),
                         item.get("cloud_model", ""), item.get("tech_risks", ""), item.get("confidence", 70)],
                    )
                count += 1
        await db.commit()
    return {"generated": count, "ai": True}


# ─── Enhancement #14: Business Case Generation ──────────────────────────


@router.post("/business-case/ai-generate")
async def ai_generate_business_case(data: dict, db=Depends(get_db)):
    """AI-generate business case for initiatives."""
    initiative_id = data.get("initiative_id")
    if initiative_id:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives WHERE id = ?", [initiative_id])
    else:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives LIMIT 10")

    if not initiatives:
        return {"error": "No initiatives found"}

    init_list = [dict(i) for i in initiatives]

    if not is_openai_available():
        count = 0
        for init in init_list:
            if init.get("estimated_cost_k"):
                continue
            await db.execute(
                "UPDATE initiatives SET estimated_cost_k=500, annual_benefit_k=1200, npv_k=800, "
                "payback_months=12, roi_pct=140, cost_assumptions='Template estimate', "
                "benefit_assumptions='Template estimate' WHERE id=?",
                [init["id"]],
            )
            count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    count = 0
    for init in init_list:
        prompt = f"""Create a business case for this initiative:
Name: {init['name']}
Description: {init.get('description', '')}
RICE Score: {init.get('rice_score', 'N/A')}

Provide financial estimates:
- estimated_cost_k (implementation cost in $K)
- annual_benefit_k (annual benefit in $K)
- npv_k (3-year NPV in $K)
- payback_months (months to payback)
- roi_pct (ROI percentage)
- cost_assumptions (key cost assumptions)
- benefit_assumptions (key benefit assumptions)
- confidence (0-100)

Return JSON object."""

        result = await call_openai_json(prompt)
        if isinstance(result, dict):
            await db.execute(
                "UPDATE initiatives SET estimated_cost_k=?, annual_benefit_k=?, npv_k=?, "
                "payback_months=?, roi_pct=?, cost_assumptions=?, benefit_assumptions=? WHERE id=?",
                [result.get("estimated_cost_k", 0), result.get("annual_benefit_k", 0),
                 result.get("npv_k", 0), result.get("payback_months", 12),
                 result.get("roi_pct", 0), result.get("cost_assumptions", ""),
                 result.get("benefit_assumptions", ""), init["id"]],
            )
            count += 1
    await db.commit()
    return {"generated": count, "ai": True}


# ─── Enhancement #11: Feasibility Scoring ────────────────────────────────


@router.post("/feasibility/ai-generate")
async def ai_generate_feasibility(data: dict, db=Depends(get_db)):
    """AI-generate feasibility scores for initiatives."""
    initiative_id = data.get("initiative_id")
    if initiative_id:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives WHERE id = ?", [initiative_id])
    else:
        initiatives = await db.execute_fetchall("SELECT * FROM initiatives LIMIT 10")

    if not initiatives:
        return {"error": "No initiatives found"}

    init_list = [dict(i) for i in initiatives]

    if not is_openai_available():
        count = 0
        for init in init_list:
            await db.execute(
                "UPDATE initiatives SET technical_feasibility=3, org_feasibility=3, regulatory_feasibility=3, "
                "financial_feasibility=3, talent_feasibility=3 WHERE id=?",
                [init["id"]],
            )
            count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    count = 0
    for init in init_list:
        prompt = f"""Score the feasibility of this initiative on 5 dimensions (1-5 each):
Name: {init['name']}
Description: {init.get('description', '')}

Dimensions:
- technical_feasibility (1=very hard, 5=straightforward)
- org_feasibility (organizational readiness)
- regulatory_feasibility (regulatory complexity)
- financial_feasibility (funding availability)
- talent_feasibility (skills availability)

Return JSON object with these 5 fields and confidence (0-100)."""

        result = await call_openai_json(prompt)
        if isinstance(result, dict):
            await db.execute(
                "UPDATE initiatives SET technical_feasibility=?, org_feasibility=?, regulatory_feasibility=?, "
                "financial_feasibility=?, talent_feasibility=? WHERE id=?",
                [result.get("technical_feasibility", 3), result.get("org_feasibility", 3),
                 result.get("regulatory_feasibility", 3), result.get("financial_feasibility", 3),
                 result.get("talent_feasibility", 3), init["id"]],
            )
            count += 1
    await db.commit()
    return {"generated": count, "ai": True}


# ─── Enhancement #7: Multi-Scenario Strategy ────────────────────────────


@router.post("/scenarios/ai-generate")
async def ai_generate_scenarios(db=Depends(get_db)):
    """Generate strategies for conservative, balanced, and aggressive scenarios."""
    from ai_swot_strategy import gather_full_context

    bu_rows = await db.execute_fetchall("SELECT id FROM business_units LIMIT 1")
    if not bu_rows:
        return {"error": "No business units found"}
    bu_id = bu_rows[0]["id"]

    ctx = await gather_full_context(db, bu_id)

    if not is_openai_available():
        # Just tag existing strategies with 'balanced' scenario
        await db.execute("UPDATE strategies SET scenario = 'balanced' WHERE scenario IS NULL OR scenario = 'balanced'")
        await db.execute("UPDATE strategic_okrs SET scenario = 'balanced' WHERE scenario IS NULL OR scenario = 'balanced'")
        await db.commit()
        return {"generated": 0, "ai": False, "message": "Existing strategies tagged as balanced"}

    from ai_research import call_openai_json
    from ai_swot_strategy import _build_context_prompt
    context_prompt = _build_context_prompt(ctx)

    scenarios_generated = 0
    for scenario in ["conservative", "aggressive"]:
        prompt = f"""{context_prompt}

Generate a {scenario} strategy scenario. For a {scenario} approach:
{"- Focus on cost optimization, risk reduction, incremental improvements" if scenario == "conservative" else "- Focus on market disruption, rapid digital transformation, bold bets"}

Provide 4 strategies (one per layer: business, digital, data, gen_ai).
Each with: name, description, risk_level (low/medium/high), confidence (0-100)
And 1-2 OKRs per strategy with key_results.

Return JSON: {{
  "strategies": [{{
    "layer": "...", "name": "...", "description": "...", "risk_level": "...", "confidence": N,
    "okrs": [{{"objective": "...", "key_results": [{{"key_result": "...", "metric": "...", "target_value": N, "unit": "..."}}]}}]
  }}]
}}"""

        result = await call_openai_json(prompt)
        if isinstance(result, dict) and "strategies" in result:
            for s in result["strategies"]:
                cursor = await db.execute(
                    "INSERT INTO strategies (layer, name, description, risk_level, ai_confidence, scenario) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    [s.get("layer", "digital"), s.get("name", ""), s.get("description", ""),
                     s.get("risk_level", "medium"), s.get("confidence", 70), scenario],
                )
                strategy_id = cursor.lastrowid
                for okr in s.get("okrs", []):
                    okr_cursor = await db.execute(
                        "INSERT INTO strategic_okrs (strategy_id, objective, scenario) VALUES (?, ?, ?)",
                        [strategy_id, okr.get("objective", ""), scenario],
                    )
                    okr_id = okr_cursor.lastrowid
                    for kr in okr.get("key_results", []):
                        await db.execute(
                            "INSERT INTO strategic_key_results (okr_id, key_result, metric, target_value, unit, scenario) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            [okr_id, kr.get("key_result", ""), kr.get("metric", ""),
                             kr.get("target_value", 0), kr.get("unit", ""), scenario],
                        )
                scenarios_generated += 1
        await db.commit()

    return {"scenarios_generated": scenarios_generated, "ai": True}
