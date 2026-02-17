"""
Step 1 AI Dashboard Router — 13 endpoints for AI-powered dashboard capabilities.
"""

import json

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available
from ai_dashboard import (
    gather_dashboard_context,
    _compute_data_hash,
    _get_cached_analysis,
    _cache_analysis,
    ai_financial_analysis,
    ai_discover_competitors,
    ai_trend_analysis,
    ai_anomaly_detection,
    ai_executive_summary,
    ai_data_enrichment_suggestions,
    ai_transformation_health,
    ai_natural_language_query,
    ai_whatif_scenario,
    ai_generate_report,
)

router = APIRouter()


# ─── 1. AI Financial Analysis ────────────────────────────────────────────────


@router.post("/ai/financial-analysis")
async def run_financial_analysis(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    cache_key = _compute_data_hash({
        "org": ctx["organization"].get("name"),
        "ops": [(m.get("metric_name"), m.get("metric_value")) for m in ctx["ops_metrics"][:10]],
        "comps": [c.get("name") for c in ctx["competitors"][:6]],
    })
    cached = await _get_cached_analysis(db, "financial", cache_key)
    if cached:
        return {**cached, "ai_powered": True, "cached": True}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_financial_analysis(
        ctx["organization"], ctx["ops_metrics"], ctx["competitors"], ctx["revenue_trends"]
    )
    if result:
        await _cache_analysis(db, "financial", cache_key, result)
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI analysis failed. Please try again."}


# ─── 2. AI Discover Competitors ──────────────────────────────────────────────


@router.post("/ai/discover-competitors")
async def discover_competitors(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_discover_competitors(
        ctx["organization"].get("name", ""),
        ctx["organization"].get("industry", ""),
        ctx["competitors"],
    )
    if result:
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI competitor discovery failed. Please try again."}


# ─── 3. Save Discovered Competitors ──────────────────────────────────────────


@router.post("/ai/discover-competitors/save")
async def save_discovered_competitors(data: dict, db=Depends(get_db)):
    competitors = data.get("competitors", [])
    saved = 0
    for comp in competitors:
        name = comp.get("name")
        if not name:
            continue
        # Check if already exists
        existing = await db.execute_fetchall(
            "SELECT id FROM competitors WHERE name = ?", (name,)
        )
        if not existing:
            await db.execute(
                "INSERT INTO competitors (name, ticker, strengths, data_source) VALUES (?, ?, ?, ?)",
                (
                    name,
                    comp.get("ticker", ""),
                    comp.get("rationale", ""),
                    f"AI-discovered ({comp.get('relevance', 'indirect')})",
                ),
            )
            saved += 1
    await db.commit()
    return {"saved": saved}


# ─── 4. AI Trend Analysis ────────────────────────────────────────────────────


@router.get("/ai/trend-analysis")
async def get_trend_analysis(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    cache_key = _compute_data_hash({
        "org": ctx["organization"].get("name"),
        "rev": [(r.get("period"), r.get("revenue")) for r in ctx["revenue_trends"][:10]],
    })
    cached = await _get_cached_analysis(db, "trend", cache_key)
    if cached:
        return {**cached, "ai_powered": True, "cached": True}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_trend_analysis(
        ctx["revenue_trends"], ctx["ops_metrics"], ctx["organization"].get("name", "")
    )
    if result:
        await _cache_analysis(db, "trend", cache_key, result)
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI trend analysis failed. Please try again."}


# ─── 5. AI Anomaly Detection ─────────────────────────────────────────────────


@router.get("/ai/anomaly-detection")
async def get_anomaly_detection(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    cache_key = _compute_data_hash({
        "org": ctx["organization"].get("name"),
        "ops": [(m.get("metric_name"), m.get("metric_value")) for m in ctx["ops_metrics"][:10]],
    })
    cached = await _get_cached_analysis(db, "anomaly", cache_key)
    if cached:
        return {**cached, "ai_powered": True, "cached": True}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_anomaly_detection(
        ctx["organization"], ctx["ops_metrics"], ctx["competitors"], ctx["revenue_trends"]
    )
    if result:
        await _cache_analysis(db, "anomaly", cache_key, result)
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI anomaly detection failed. Please try again."}


# ─── 6. AI Executive Summary ─────────────────────────────────────────────────


@router.post("/ai/executive-summary")
async def generate_executive_summary(data: dict = None, db=Depends(get_db)):
    data = data or {}
    refresh = data.get("refresh", False)

    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not refresh:
        cache_key = _compute_data_hash({
            "org": ctx["organization"].get("name"),
            "ops_count": len(ctx["ops_metrics"]),
            "comp_count": len(ctx["competitors"]),
        })
        cached = await _get_cached_analysis(db, "executive_summary", cache_key)
        if cached:
            return {**cached, "ai_powered": True, "cached": True}
    else:
        cache_key = _compute_data_hash({
            "org": ctx["organization"].get("name"),
            "ops_count": len(ctx["ops_metrics"]),
            "comp_count": len(ctx["competitors"]),
        })

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_executive_summary(
        ctx["organization"], ctx["ops_metrics"], ctx["competitors"],
        ctx["revenue_trends"], ctx["swot_entries"]
    )
    if result:
        await _cache_analysis(db, "executive_summary", cache_key, result)
        # Store on organization record
        try:
            await db.execute(
                "UPDATE organization SET ai_executive_summary = ?, ai_summary_updated_at = datetime('now') WHERE id = ?",
                (json.dumps(result, default=str), ctx["organization"]["id"]),
            )
            await db.commit()
        except Exception:
            pass
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI executive summary generation failed. Please try again."}


# ─── 7. AI Enrichment Suggestions ────────────────────────────────────────────


@router.get("/ai/enrichment-suggestions")
async def get_enrichment_suggestions(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    existing_summary = {
        "business_units": len(ctx["business_units"]),
        "ops_metrics": len(ctx["ops_metrics"]),
        "revenue_records": len(ctx["revenue_trends"]),
        "competitors": len(ctx["competitors"]),
        "value_streams": len(ctx["value_streams"]),
        "swot_entries": len(ctx["swot_entries"]),
        "strategies": len(ctx["strategies"]),
        "initiatives": len(ctx["initiatives"]),
        "metric_names": list(set(m.get("metric_name", "") for m in ctx["ops_metrics"][:20])),
    }

    result = await ai_data_enrichment_suggestions(
        ctx["organization"],
        ctx["organization"].get("industry", ""),
        existing_summary,
    )
    if result:
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI enrichment suggestion failed. Please try again."}


# ─── 8. AI Transformation Health ─────────────────────────────────────────────


@router.get("/ai/transformation-health")
async def get_transformation_health(db=Depends(get_db)):
    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    cache_key = _compute_data_hash({
        "org": ctx["organization"].get("name"),
        "vs": len(ctx["value_streams"]),
        "swot": len(ctx["swot_entries"]),
        "strat": len(ctx["strategies"]),
        "init": len(ctx["initiatives"]),
        "epic": len(ctx["epics"]),
        "feat": len(ctx["features"]),
    })
    cached = await _get_cached_analysis(db, "transformation_health", cache_key)
    if cached:
        return {**cached, "ai_powered": True, "cached": True}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_transformation_health(ctx)
    if result:
        await _cache_analysis(db, "transformation_health", cache_key, result)
        # Store health score on organization
        try:
            await db.execute(
                "UPDATE organization SET ai_health_score = ? WHERE id = ?",
                (result.get("overall_health_score", 0), ctx["organization"]["id"]),
            )
            await db.commit()
        except Exception:
            pass
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI transformation health assessment failed. Please try again."}


# ─── 9. AI Natural Language Query ────────────────────────────────────────────


@router.post("/ai/query")
async def natural_language_query(data: dict, db=Depends(get_db)):
    question = data.get("question", "").strip()
    if not question:
        return {"error": "Please provide a question."}

    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_natural_language_query(question, ctx)
    if result:
        # Save to history
        try:
            tables_queried = ",".join(result.get("data_tables_queried", []))
            await db.execute(
                "INSERT INTO nlq_history (question, answer_json, data_tables_queried) VALUES (?, ?, ?)",
                (question, json.dumps(result, default=str), tables_queried),
            )
            await db.commit()
        except Exception:
            pass
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI query failed. Please try again."}


# ─── 10. AI What-If Scenario ─────────────────────────────────────────────────


@router.post("/ai/scenario")
async def run_whatif_scenario(data: dict, db=Depends(get_db)):
    scenario_type = data.get("scenario_type", "custom")
    scenario_name = data.get("scenario_name", "Custom Scenario")
    parameters = data.get("parameters", {})

    if not parameters:
        return {"error": "Please provide scenario parameters."}

    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    scenario_params = {
        "scenario_type": scenario_type,
        "scenario_name": scenario_name,
        **parameters,
    }

    result = await ai_whatif_scenario(
        scenario_params, ctx["organization"], ctx["competitors"], ctx["revenue_trends"]
    )
    if result:
        # Save scenario
        try:
            await db.execute(
                "INSERT INTO ai_scenarios (scenario_name, scenario_type, parameters_json, result_json) VALUES (?, ?, ?, ?)",
                (scenario_name, scenario_type, json.dumps(parameters, default=str), json.dumps(result, default=str)),
            )
            await db.commit()
        except Exception:
            pass
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI scenario modeling failed. Please try again."}


# ─── 11. List Saved Scenarios ─────────────────────────────────────────────────


@router.get("/ai/scenarios")
async def list_scenarios(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM ai_scenarios ORDER BY created_at DESC LIMIT 50"
    )
    results = []
    for r in rows:
        row_dict = dict(r)
        try:
            row_dict["parameters"] = json.loads(row_dict.get("parameters_json", "{}"))
        except Exception:
            row_dict["parameters"] = {}
        try:
            row_dict["result"] = json.loads(row_dict.get("result_json", "{}"))
        except Exception:
            row_dict["result"] = {}
        results.append(row_dict)
    return results


# ─── 12. AI Generate Report ──────────────────────────────────────────────────


@router.post("/ai/generate-report")
async def generate_report(data: dict, db=Depends(get_db)):
    audience = data.get("audience", "c_suite")
    if audience not in ("c_suite", "technical", "board"):
        audience = "c_suite"

    ctx = await gather_dashboard_context(db)
    if not ctx["organization"]:
        return {"error": "No organization set up. Complete Org Setup first."}

    if not is_openai_available():
        return {"ai_powered": False, "message": "OpenAI not configured. Set OPENAI_API_KEY environment variable."}

    result = await ai_generate_report(
        ctx["organization"], ctx["ops_metrics"], ctx["competitors"],
        ctx["revenue_trends"], ctx["swot_entries"], audience
    )
    if result:
        return {**result, "ai_powered": True}

    return {"ai_powered": False, "message": "AI report generation failed. Please try again."}


# ─── 13. NLQ Query History ───────────────────────────────────────────────────


@router.get("/ai/query-history")
async def get_query_history(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM nlq_history ORDER BY created_at DESC LIMIT 50"
    )
    results = []
    for r in rows:
        row_dict = dict(r)
        try:
            row_dict["answer"] = json.loads(row_dict.get("answer_json", "{}"))
        except Exception:
            row_dict["answer"] = {}
        results.append(row_dict)
    return results
