from fastapi import APIRouter, Depends
from database import get_db
from datetime import datetime
from ai_research import is_openai_available

router = APIRouter()


# ===================== Strategy Inputs CRUD =====================

@router.get("/inputs")
async def list_inputs(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM strategy_inputs ORDER BY input_type, created_at")
    return [dict(r) for r in rows]


@router.post("/inputs")
async def create_or_upsert_input(data: dict, db=Depends(get_db)):
    input_type = data["input_type"]
    content = data["content"]
    title = data.get("title")
    file_name = data.get("file_name")

    # Singleton types: upsert (one per type)
    singleton_types = ['business_strategy', 'digital_strategy', 'data_strategy',
                       'gen_ai_strategy', 'ongoing_initiatives']
    if input_type in singleton_types:
        existing = await db.execute_fetchall(
            "SELECT id FROM strategy_inputs WHERE input_type = ?", (input_type,)
        )
        if existing:
            await db.execute(
                "UPDATE strategy_inputs SET content = ?, title = ?, file_name = ? WHERE input_type = ?",
                (content, title, file_name, input_type),
            )
            await db.commit()
            return {"id": dict(existing[0])["id"], "updated": True}

    cursor = await db.execute(
        "INSERT INTO strategy_inputs (input_type, title, content, file_name) VALUES (?, ?, ?, ?)",
        (input_type, title, content, file_name),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/inputs/{input_id}")
async def delete_input(input_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM strategy_inputs WHERE id = ?", (input_id,))
    await db.commit()
    return {"deleted": True}


# ===================== Data Sources Check =====================

@router.get("/data-sources")
async def check_data_sources(db=Depends(get_db)):
    org = await db.execute_fetchall("SELECT COUNT(*) as c FROM organization")
    org_count = dict(org[0])["c"]

    streams = await db.execute_fetchall("SELECT COUNT(*) as c FROM value_streams")
    stream_count = dict(streams[0])["c"]

    swot = await db.execute_fetchall("SELECT COUNT(*) as c FROM swot_entries")
    swot_count = dict(swot[0])["c"]

    tows = await db.execute_fetchall("SELECT COUNT(*) as c FROM tows_actions")
    tows_count = dict(tows[0])["c"]

    inputs = await db.execute_fetchall("SELECT COUNT(*) as c FROM strategy_inputs")
    input_count = dict(inputs[0])["c"]

    input_types = await db.execute_fetchall(
        "SELECT DISTINCT input_type FROM strategy_inputs"
    )
    input_type_list = [dict(r)["input_type"] for r in input_types]

    return {
        "organization": org_count > 0,
        "value_streams": stream_count > 0,
        "swot": swot_count > 0,
        "tows": tows_count > 0,
        "user_inputs": input_count > 0,
        "input_types": input_type_list,
        "counts": {
            "organization": org_count,
            "value_streams": stream_count,
            "swot": swot_count,
            "tows": tows_count,
            "inputs": input_count,
        }
    }


# ===================== Existing Endpoints (kept) =====================

@router.get("/strategies")
async def list_strategies(db=Depends(get_db)):
    rows = await db.execute_fetchall("SELECT * FROM strategies ORDER BY layer")
    return [dict(r) for r in rows]


@router.post("/strategies")
async def create_strategy(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO strategies (layer, name, description, tows_action_id, risk_level, risks) VALUES (?, ?, ?, ?, ?, ?)",
        (data["layer"], data["name"], data.get("description"), data.get("tows_action_id"),
         data.get("risk_level", "medium"), data.get("risks")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/strategies/{strategy_id}")
async def update_strategy(strategy_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for key in ["name", "description", "approved", "risk_level", "risks"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if fields:
        values.append(strategy_id)
        await db.execute(f"UPDATE strategies SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"updated": True}


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, db=Depends(get_db)):
    # Cascade: nullify initiative refs -> delete key results -> OKRs -> strategy
    await db.execute("UPDATE initiatives SET strategy_id = NULL WHERE strategy_id = ?", (strategy_id,))
    okrs = await db.execute_fetchall(
        "SELECT id FROM strategic_okrs WHERE strategy_id = ?", (strategy_id,)
    )
    for okr in okrs:
        okr_id = dict(okr)["id"]
        await db.execute("DELETE FROM strategic_key_results WHERE okr_id = ?", (okr_id,))
    await db.execute("DELETE FROM strategic_okrs WHERE strategy_id = ?", (strategy_id,))
    await db.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    await db.commit()
    return {"deleted": True}


# --- Strategic OKRs ---

@router.get("/okrs")
async def list_strategic_okrs(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT o.*, s.name as strategy_name, s.layer as strategy_layer "
        "FROM strategic_okrs o JOIN strategies s ON o.strategy_id = s.id"
    )
    return [dict(r) for r in rows]


@router.post("/okrs")
async def create_strategic_okr(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO strategic_okrs (strategy_id, objective, time_horizon, status) VALUES (?, ?, ?, ?)",
        (data["strategy_id"], data["objective"], data.get("time_horizon"), data.get("status", "draft")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/okrs/{okr_id}")
async def update_strategic_okr(okr_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for key in ["objective", "time_horizon", "status"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if fields:
        values.append(okr_id)
        await db.execute(f"UPDATE strategic_okrs SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"updated": True}


@router.delete("/okrs/{okr_id}")
async def delete_okr(okr_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM strategic_key_results WHERE okr_id = ?", (okr_id,))
    await db.execute("DELETE FROM strategic_okrs WHERE id = ?", (okr_id,))
    await db.commit()
    return {"deleted": True}


# --- Key Results ---

@router.get("/okrs/{okr_id}/key-results")
async def list_key_results(okr_id: int, db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM strategic_key_results WHERE okr_id = ?", (okr_id,)
    )
    return [dict(r) for r in rows]


@router.post("/okrs/{okr_id}/key-results")
async def create_key_result(okr_id: int, data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO strategic_key_results (okr_id, key_result, metric, current_value, target_value, unit, "
        "target_optimistic, target_pessimistic, rationale) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (okr_id, data["key_result"], data.get("metric"), data.get("current_value", 0),
         data["target_value"], data.get("unit"),
         data.get("target_optimistic"), data.get("target_pessimistic"), data.get("rationale")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/okrs/{okr_id}/key-results/{kr_id}")
async def delete_key_result(okr_id: int, kr_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM strategic_key_results WHERE id = ? AND okr_id = ?", (kr_id, okr_id))
    await db.commit()
    return {"deleted": True}


# ===================== Full Nested Query =====================

@router.get("/strategies-full")
async def list_strategies_full(db=Depends(get_db)):
    strategies = await db.execute_fetchall("SELECT * FROM strategies ORDER BY layer, id")
    result = []
    for s in strategies:
        s_dict = dict(s)
        okrs = await db.execute_fetchall(
            "SELECT * FROM strategic_okrs WHERE strategy_id = ? ORDER BY id", (s_dict["id"],)
        )
        okr_list = []
        for o in okrs:
            o_dict = dict(o)
            krs = await db.execute_fetchall(
                "SELECT * FROM strategic_key_results WHERE okr_id = ? ORDER BY id", (o_dict["id"],)
            )
            o_dict["key_results"] = [dict(kr) for kr in krs]
            okr_list.append(o_dict)
        s_dict["okrs"] = okr_list
        result.append(s_dict)
    return result


# ===================== Approve All =====================

@router.post("/approve-all")
async def approve_all_strategies(db=Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    try:
        await db.execute("UPDATE strategies SET approved = 1")
        # Update review gate for step 4
        existing = await db.execute_fetchall(
            "SELECT id FROM review_gates WHERE step_number = 4 AND gate_number = 1"
        )
        now = datetime.now().isoformat()
        if existing:
            await db.execute(
                "UPDATE review_gates SET status = 'approved', reviewed_at = ? WHERE step_number = 4 AND gate_number = 1",
                [now],
            )
        else:
            await db.execute(
                "INSERT INTO review_gates (step_number, gate_number, gate_name, status, reviewed_at) VALUES (4, 1, 'Strategy Approval', 'approved', ?)",
                [now],
            )
        await db.commit()
        row = await db.execute_fetchone("SELECT COUNT(*) as c FROM strategies")
        return {"approved": row["c"] if row else 0}
    except Exception as e:
        logger.error("approve-all failed: %s", e, exc_info=True)
        return {"error": str(e), "approved": 0}


# ===================== Auto-Generate Engine =====================

async def _gather_strategy_context(db):
    """Gather all upstream data for strategy generation."""
    ctx = {}

    # Organization info
    org_rows = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    ctx["organization"] = dict(org_rows[0]) if org_rows else None

    # Financial metrics from ops_efficiency
    ops_rows = await db.execute_fetchall(
        "SELECT * FROM ops_efficiency ORDER BY period DESC"
    )
    ctx["financial_metrics"] = [dict(r) for r in ops_rows]

    # Revenue trends
    rev_rows = await db.execute_fetchall(
        "SELECT * FROM revenue_splits ORDER BY period"
    )
    ctx["revenue_trends"] = [dict(r) for r in rev_rows]

    # Value stream data
    vs_rows = await db.execute_fetchall(
        "SELECT vs.*, vsm.total_lead_time_hours, vsm.total_process_time_hours, "
        "vsm.total_wait_time_hours, vsm.flow_efficiency, vsm.bottleneck_step "
        "FROM value_streams vs LEFT JOIN value_stream_metrics vsm ON vs.id = vsm.value_stream_id"
    )
    ctx["value_streams"] = [dict(r) for r in vs_rows]

    # Value stream levers
    lever_rows = await db.execute_fetchall(
        "SELECT * FROM value_stream_levers WHERE impact_estimate = 'high' ORDER BY lever_type"
    )
    ctx["high_impact_levers"] = [dict(r) for r in lever_rows]

    # TOWS actions grouped by type
    tows_rows = await db.execute_fetchall(
        "SELECT * FROM tows_actions ORDER BY strategy_type, priority DESC"
    )
    tows_grouped = {"SO": [], "WO": [], "ST": [], "WT": []}
    for t in tows_rows:
        td = dict(t)
        stype = td["strategy_type"]
        if stype in tows_grouped:
            tows_grouped[stype].append(td)
    ctx["tows"] = tows_grouped

    # User strategy inputs by type (full content, not truncated)
    input_rows = await db.execute_fetchall("SELECT * FROM strategy_inputs ORDER BY input_type")
    inputs_by_type = {}
    for inp in input_rows:
        inp_dict = dict(inp)
        itype = inp_dict["input_type"]
        if itype not in inputs_by_type:
            inputs_by_type[itype] = []
        inputs_by_type[itype].append(inp_dict)
    ctx["user_inputs"] = inputs_by_type

    # SWOT entries for AI context
    swot_rows = await db.execute_fetchall("SELECT * FROM swot_entries ORDER BY category")
    ctx["swot_entries"] = [dict(r) for r in swot_rows]

    # Industry benchmarks (best-effort)
    try:
        from source_gatherers import gather_industry_benchmarks
        org = ctx.get("organization") or {}
        vs_list = ctx.get("value_streams", [])
        segment = vs_list[0].get("name", "general") if vs_list else "general"
        industry = org.get("industry", "")
        ctx["industry_benchmarks"] = await gather_industry_benchmarks(segment, industry)
    except Exception:
        ctx["industry_benchmarks"] = {}

    # Web search results (best-effort)
    try:
        from source_gatherers import gather_web_search
        org = ctx.get("organization") or {}
        vs_list = ctx.get("value_streams", [])
        segment = vs_list[0].get("name", "general") if vs_list else "general"
        industry = org.get("industry", "")
        ctx["web_search"] = await gather_web_search(segment, industry)
    except Exception:
        ctx["web_search"] = {}

    return ctx


def _generate_business_strategy(ctx):
    """Generate business layer strategies from context."""
    strategies = []
    org = ctx.get("organization") or {}
    org_name = org.get("name", "Organization")
    rev_trends = ctx.get("revenue_trends", [])
    so_tows = ctx.get("tows", {}).get("SO", [])
    st_tows = ctx.get("tows", {}).get("ST", [])
    user_biz = ctx.get("user_inputs", {}).get("business_strategy", [])
    financial = ctx.get("financial_metrics", [])

    # Derive revenue context
    revenue_desc = ""
    if rev_trends:
        total_rev = sum(r.get("revenue", 0) for r in rev_trends)
        periods = set(r.get("period", "") for r in rev_trends)
        revenue_desc = f" across {len(periods)} period(s) with ${total_rev:,.0f} total tracked revenue"

    # Derive financial context and dynamic targets
    profit_margin = None
    for fm in financial:
        if "margin" in (fm.get("metric_name") or "").lower() and "profit" in (fm.get("metric_name") or "").lower():
            profit_margin = fm.get("metric_value")
            break

    # Compute actual YoY growth rate for dynamic target
    rev_target = 15  # default growth target %
    actual_growth = None
    org_revenues = [r for r in rev_trends if r.get("dimension_value") == "Total Revenue" and r.get("revenue")]
    if len(org_revenues) >= 2:
        sorted_rev = sorted(org_revenues, key=lambda x: x.get("period", ""))
        latest = sorted_rev[-1]["revenue"]
        prev = sorted_rev[-2]["revenue"]
        if prev > 0:
            actual_growth = ((latest - prev) / prev) * 100
            rev_target = round(actual_growth + 5, 1)  # stretch by 5%
            if rev_target < 5:
                rev_target = 5  # minimum target

    profit_target = 5  # default improvement points

    # User input context (full content)
    user_context = ""
    if user_biz:
        user_context = f" User strategic context: {user_biz[0]['content']}."

    # Strategy 1: Growth
    so_desc = ""
    so_action_id = None
    if so_tows:
        so_desc = f" Aligned with TOWS action: {so_tows[0]['action_description'][:100]}."
        so_action_id = so_tows[0]["id"]

    growth_desc = (
        f"Auto-generated: Drive revenue growth for {org_name}{revenue_desc}."
        f"{so_desc}{user_context}"
    )

    growth_okrs = [{
        "objective": f"Accelerate revenue growth and market expansion for {org_name}",
        "time_horizon": "12 months",
        "key_results": [
            {"key_result": "Increase annual revenue growth rate", "metric": "Revenue Growth %",
             "current_value": round(actual_growth, 1) if actual_growth is not None else 0,
             "target_value": rev_target,
             "target_optimistic": round(rev_target * 1.3, 1),
             "target_pessimistic": round(rev_target * 0.7, 1),
             "unit": "%",
             "rationale": f"Based on actual YoY growth of {actual_growth:.1f}% + 5% stretch" if actual_growth is not None else "Default growth target"},
            {"key_result": "Expand into new market segments", "metric": "New Segments",
             "current_value": 0, "target_value": 2,
             "target_optimistic": 3, "target_pessimistic": 1,
             "unit": "segments", "rationale": "Market expansion objective"},
        ]
    }]

    if profit_margin is not None:
        pm_pct = round(profit_margin * 100, 1) if profit_margin < 1 else profit_margin
        target_pm = round(pm_pct + profit_target, 1)
        growth_okrs[0]["key_results"].append(
            {"key_result": "Improve profit margin", "metric": "Profit Margin",
             "current_value": pm_pct, "target_value": target_pm,
             "target_optimistic": round(target_pm + 2, 1),
             "target_pessimistic": round(target_pm - 2, 1),
             "unit": "%",
             "rationale": f"Current margin {pm_pct}%, targeting +{profit_target}pp improvement"}
        )

    strategies.append({
        "name": "Revenue Growth & Market Expansion",
        "description": growth_desc,
        "tows_action_id": so_action_id,
        "risk_level": "medium",
        "risks": "Market entry barriers, competitive response, execution risk on new segments",
        "okrs": growth_okrs,
    })

    # Strategy 2: Competitive Defense
    st_desc = ""
    st_action_id = None
    if st_tows:
        st_desc = f" Aligned with TOWS action: {st_tows[0]['action_description'][:100]}."
        st_action_id = st_tows[0]["id"]

    defense_desc = f"Auto-generated: Strengthen competitive position and customer loyalty for {org_name}.{st_desc}"
    strategies.append({
        "name": "Competitive Positioning & Customer Retention",
        "description": defense_desc,
        "tows_action_id": st_action_id,
        "risk_level": "medium",
        "risks": "Customer churn during transition, competitor pricing pressure",
        "okrs": [{
            "objective": f"Strengthen market position and customer loyalty",
            "time_horizon": "12 months",
            "key_results": [
                {"key_result": "Maintain or grow market share", "metric": "Market Share",
                 "current_value": 0, "target_value": 5,
                 "target_optimistic": 8, "target_pessimistic": 3,
                 "unit": "% gain", "rationale": "Competitive positioning target"},
                {"key_result": "Improve customer retention rate", "metric": "Retention Rate",
                 "current_value": 80, "target_value": 92,
                 "target_optimistic": 95, "target_pessimistic": 88,
                 "unit": "%", "rationale": "Industry best-in-class retention benchmarks"},
            ]
        }],
    })

    return strategies


def _generate_digital_strategy(ctx):
    """Generate digital layer strategies from context."""
    strategies = []
    value_streams = ctx.get("value_streams", [])
    wo_tows = ctx.get("tows", {}).get("WO", [])
    levers = ctx.get("high_impact_levers", [])
    user_dig = ctx.get("user_inputs", {}).get("digital_strategy", [])
    bench = ctx.get("industry_benchmarks", {})
    bench_kpis = bench.get("industry_kpis", {}) if bench else {}

    # Identify bottleneck streams
    bottleneck_streams = [vs for vs in value_streams if vs.get("bottleneck_step")]
    avg_efficiency = 0
    if value_streams:
        effs = [vs.get("flow_efficiency", 0) for vs in value_streams if vs.get("flow_efficiency")]
        avg_efficiency = sum(effs) / len(effs) if effs else 0

    wo_desc = ""
    wo_action_id = None
    if wo_tows:
        wo_desc = f" Aligned with TOWS action: {wo_tows[0]['action_description'][:100]}."
        wo_action_id = wo_tows[0]["id"]

    user_context = ""
    if user_dig:
        user_context = f" User strategic context: {user_dig[0]['content']}."

    lever_desc = ""
    if levers:
        lever_types = set(l.get("lever_type", "") for l in levers)
        lever_desc = f" High-impact levers identified in: {', '.join(lever_types)}."

    desc = (
        f"Auto-generated: Transform core processes through digital enablement. "
        f"{len(bottleneck_streams)} bottleneck stream(s) identified, "
        f"avg flow efficiency {avg_efficiency:.1f}%.{wo_desc}{lever_desc}{user_context}"
    )

    # Dynamic efficiency target from benchmarks
    best_in_class_fe = bench_kpis.get("best_in_class_flow_efficiency_pct")
    if best_in_class_fe and avg_efficiency > 0:
        efficiency_target = min(round((avg_efficiency + best_in_class_fe) / 2, 0), 80)
    else:
        efficiency_target = min(round(avg_efficiency + 10, 0), 80) if avg_efficiency > 0 else 40

    lead_times = [vs.get("total_lead_time_hours", 0) for vs in value_streams if vs.get("total_lead_time_hours")]
    avg_lead = sum(lead_times) / len(lead_times) if lead_times else 100

    strategies.append({
        "name": "Digital Process Transformation",
        "description": desc,
        "tows_action_id": wo_action_id,
        "risk_level": "medium",
        "risks": "Technology adoption resistance, integration complexity, training overhead",
        "okrs": [{
            "objective": "Improve operational efficiency through digital process transformation",
            "time_horizon": "12 months",
            "key_results": [
                {"key_result": "Improve average flow efficiency across value streams", "metric": "Flow Efficiency",
                 "current_value": round(avg_efficiency, 1), "target_value": efficiency_target,
                 "target_optimistic": min(round(efficiency_target * 1.2, 1), 90),
                 "target_pessimistic": round(efficiency_target * 0.8, 1),
                 "unit": "%",
                 "rationale": f"Current avg: {avg_efficiency:.1f}%, industry best-in-class: {best_in_class_fe:.1f}%" if best_in_class_fe else f"Current avg: {avg_efficiency:.1f}%, targeting +10pp improvement"},
                {"key_result": "Reduce average lead time by 25%", "metric": "Lead Time Reduction",
                 "current_value": round(avg_lead, 1), "target_value": round(avg_lead * 0.75, 1),
                 "target_optimistic": round(avg_lead * 0.6, 1),
                 "target_pessimistic": round(avg_lead * 0.85, 1),
                 "unit": "hours",
                 "rationale": f"Current avg lead time: {avg_lead:.1f}h, targeting 25% reduction"},
                {"key_result": "Launch digital platform features for core processes", "metric": "Platform Features",
                 "current_value": 0, "target_value": max(len(value_streams), 3),
                 "target_optimistic": max(len(value_streams), 3) + 2,
                 "target_pessimistic": max(len(value_streams), 3) - 1,
                 "unit": "features",
                 "rationale": f"One feature per value stream ({len(value_streams)} streams)"},
            ]
        }],
    })

    return strategies


def _generate_data_strategy(ctx):
    """Generate data layer strategies from context."""
    strategies = []
    value_streams = ctx.get("value_streams", [])
    user_data = ctx.get("user_inputs", {}).get("data_strategy", [])

    user_context = ""
    if user_data:
        user_context = f" User strategic context: {user_data[0]['content']}."

    vs_count = len(value_streams)
    desc = (
        f"Auto-generated: Build enterprise data and analytics capabilities. "
        f"{vs_count} value stream(s) to instrument with real-time analytics.{user_context}"
    )

    strategies.append({
        "name": "Enterprise Data & Analytics Platform",
        "description": desc,
        "tows_action_id": None,
        "risk_level": "low",
        "risks": "Data quality challenges, cross-team alignment, privacy compliance requirements",
        "okrs": [{
            "objective": "Establish data-driven decision making across the organization",
            "time_horizon": "12 months",
            "key_results": [
                {"key_result": "Deploy real-time dashboards per value stream", "metric": "Dashboards",
                 "current_value": 0, "target_value": max(vs_count, 3),
                 "target_optimistic": max(vs_count, 3) + 2,
                 "target_pessimistic": max(vs_count, 3) - 1,
                 "unit": "dashboards",
                 "rationale": f"One dashboard per value stream ({vs_count} streams)"},
                {"key_result": "Achieve data quality score above target", "metric": "Data Quality",
                 "current_value": 0, "target_value": 85,
                 "target_optimistic": 92, "target_pessimistic": 78,
                 "unit": "%", "rationale": "Industry standard data quality benchmark"},
                {"key_result": "Reduce reporting cycle time", "metric": "Reporting Cycle",
                 "current_value": 5, "target_value": 1,
                 "target_optimistic": 0.5, "target_pessimistic": 2,
                 "unit": "days", "rationale": "Move from weekly to daily/real-time reporting"},
                {"key_result": "Drive analytics adoption across teams", "metric": "Adoption Rate",
                 "current_value": 20, "target_value": 75,
                 "target_optimistic": 85, "target_pessimistic": 60,
                 "unit": "%", "rationale": "Target majority adoption across organization"},
            ]
        }],
    })

    return strategies


def _generate_gen_ai_strategy(ctx):
    """Generate gen_ai layer strategies from context."""
    strategies = []
    value_streams = ctx.get("value_streams", [])
    user_ai = ctx.get("user_inputs", {}).get("gen_ai_strategy", [])

    # Identify automation candidates: streams with high wait-to-process ratio
    automation_candidates = [
        vs for vs in value_streams
        if vs.get("total_wait_time_hours") and vs.get("total_process_time_hours")
        and vs["total_wait_time_hours"] > vs["total_process_time_hours"] * 2
    ]

    user_context = ""
    if user_ai:
        user_context = f" User strategic context: {user_ai[0]['content']}."

    candidate_count = len(automation_candidates)
    desc = (
        f"Auto-generated: Deploy Gen AI to transform operations. "
        f"{candidate_count} process(es) identified as high-potential automation candidates "
        f"(wait time > 2x process time).{user_context}"
    )

    strategies.append({
        "name": "Gen AI Operational Transformation",
        "description": desc,
        "tows_action_id": None,
        "risk_level": "high",
        "risks": "AI model accuracy, data privacy concerns, governance gaps, change management challenges",
        "okrs": [{
            "objective": "Deploy Gen AI capabilities to automate and augment key processes",
            "time_horizon": "18 months",
            "key_results": [
                {"key_result": "Automate high-wait-time processes with AI", "metric": "Processes Automated",
                 "current_value": 0, "target_value": max(candidate_count, 2),
                 "target_optimistic": max(candidate_count, 2) + 2,
                 "target_pessimistic": max(candidate_count, 2) - 1,
                 "unit": "processes",
                 "rationale": f"{candidate_count} automation candidates identified from value stream analysis"},
                {"key_result": "Achieve time savings through AI-powered workflows", "metric": "Time Savings",
                 "current_value": 0, "target_value": 30,
                 "target_optimistic": 40, "target_pessimistic": 20,
                 "unit": "%", "rationale": "Industry benchmark for AI-driven process automation savings"},
                {"key_result": "Establish AI governance framework", "metric": "Governance Score",
                 "current_value": 0, "target_value": 100,
                 "target_optimistic": 100, "target_pessimistic": 80,
                 "unit": "%", "rationale": "Full governance framework required before scaling AI"},
                {"key_result": "Train teams on AI tools and responsible use", "metric": "Teams Trained",
                 "current_value": 0, "target_value": 100,
                 "target_optimistic": 100, "target_pessimistic": 75,
                 "unit": "%", "rationale": "Organization-wide AI literacy target"},
            ]
        }],
    })

    return strategies


@router.post("/auto-generate")
async def auto_generate_strategies(db=Depends(get_db)):
    """Generate strategies + OKRs + KRs from Steps 1-3 + user inputs.
    Uses AI when OpenAI is available, falls back to rule-based generation."""

    # Step 1: Cleanup auto-generated strategies (cascade delete)
    auto_strategies = await db.execute_fetchall(
        "SELECT id FROM strategies WHERE description LIKE 'Auto-generated%'"
    )
    for s in auto_strategies:
        sid = dict(s)["id"]
        # Nullify initiative references to this strategy
        await db.execute("UPDATE initiatives SET strategy_id = NULL WHERE strategy_id = ?", (sid,))
        okrs = await db.execute_fetchall("SELECT id FROM strategic_okrs WHERE strategy_id = ?", (sid,))
        for okr in okrs:
            await db.execute("DELETE FROM strategic_key_results WHERE okr_id = ?", (dict(okr)["id"],))
        await db.execute("DELETE FROM strategic_okrs WHERE strategy_id = ?", (sid,))
        await db.execute("DELETE FROM strategies WHERE id = ?", (sid,))

    # Step 2: Gather context
    ctx = await _gather_strategy_context(db)

    ai_powered = False
    cross_layer_notes = ""
    initiative_suggestions = []

    # Step 3: Try AI-powered generation
    if is_openai_available():
        try:
            from ai_swot_strategy import generate_ai_strategies

            # Get TOWS actions for AI context
            tows_flat = []
            for stype_actions in ctx.get("tows", {}).values():
                tows_flat.extend(stype_actions)

            ai_result = await generate_ai_strategies(ctx, tows_flat)

            if ai_result and ai_result.get("layers"):
                ai_powered = True
                cross_layer_notes = ai_result.get("cross_layer_notes", "")
                initiative_suggestions = ai_result.get("initiative_suggestions", [])

                strategy_count = 0
                okr_count = 0
                kr_count = 0

                for layer_name in ["business", "digital", "data", "gen_ai"]:
                    layer_data = ai_result["layers"].get(layer_name, {})
                    for strat in layer_data.get("strategies", []):
                        cursor = await db.execute(
                            "INSERT INTO strategies (layer, name, description, tows_action_id, risk_level, risks) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (layer_name,
                             strat.get("name", f"{layer_name.title()} Strategy"),
                             f"Auto-generated (AI): {strat.get('description', '')}",
                             None,  # AI doesn't map to specific TOWS action IDs
                             strat.get("risk_level", "medium"),
                             strat.get("risks", "")),
                        )
                        strategy_id = cursor.lastrowid
                        strategy_count += 1

                        for okr in strat.get("okrs", []):
                            okr_cursor = await db.execute(
                                "INSERT INTO strategic_okrs (strategy_id, objective, time_horizon, status) VALUES (?, ?, ?, 'draft')",
                                (strategy_id, okr.get("objective", "Strategic objective"), okr.get("time_horizon", "12 months")),
                            )
                            okr_id = okr_cursor.lastrowid
                            okr_count += 1

                            for kr in okr.get("key_results", []):
                                await db.execute(
                                    "INSERT INTO strategic_key_results (okr_id, key_result, metric, current_value, target_value, unit, "
                                    "target_optimistic, target_pessimistic, rationale) "
                                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (okr_id, kr.get("key_result", "Key result"),
                                     kr.get("metric"), kr.get("current_value", 0),
                                     kr.get("target_value", 0), kr.get("unit"),
                                     kr.get("target_optimistic"), kr.get("target_pessimistic"),
                                     kr.get("rationale", "")),
                                )
                                kr_count += 1

                await db.commit()
                return {
                    "strategies": strategy_count, "okrs": okr_count, "key_results": kr_count,
                    "ai_powered": True,
                    "cross_layer_notes": cross_layer_notes,
                    "initiative_suggestions": initiative_suggestions,
                }
        except Exception:
            pass  # Fall through to rule-based

    # Step 3b: Rule-based fallback
    all_layers = [
        ("business", _generate_business_strategy(ctx)),
        ("digital", _generate_digital_strategy(ctx)),
        ("data", _generate_data_strategy(ctx)),
        ("gen_ai", _generate_gen_ai_strategy(ctx)),
    ]

    strategy_count = 0
    okr_count = 0
    kr_count = 0

    for layer, layer_strategies in all_layers:
        for strat in layer_strategies:
            cursor = await db.execute(
                "INSERT INTO strategies (layer, name, description, tows_action_id, risk_level, risks) VALUES (?, ?, ?, ?, ?, ?)",
                (layer, strat["name"], strat["description"], strat.get("tows_action_id"),
                 strat.get("risk_level", "medium"), strat.get("risks", "")),
            )
            strategy_id = cursor.lastrowid
            strategy_count += 1

            for okr in strat.get("okrs", []):
                okr_cursor = await db.execute(
                    "INSERT INTO strategic_okrs (strategy_id, objective, time_horizon, status) VALUES (?, ?, ?, 'draft')",
                    (strategy_id, okr["objective"], okr.get("time_horizon")),
                )
                okr_id = okr_cursor.lastrowid
                okr_count += 1

                for kr in okr.get("key_results", []):
                    await db.execute(
                        "INSERT INTO strategic_key_results (okr_id, key_result, metric, current_value, target_value, unit, "
                        "target_optimistic, target_pessimistic, rationale) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (okr_id, kr["key_result"], kr.get("metric"), kr.get("current_value", 0),
                         kr["target_value"], kr.get("unit"),
                         kr.get("target_optimistic"), kr.get("target_pessimistic"),
                         kr.get("rationale", "")),
                    )
                    kr_count += 1

    await db.commit()
    return {
        "strategies": strategy_count, "okrs": okr_count, "key_results": kr_count,
        "ai_powered": False,
        "cross_layer_notes": "",
        "initiative_suggestions": [],
    }
