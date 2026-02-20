"""
AI SWOT, TOWS, and Strategy Generation Module.
Uses OpenAI GPT-4o-mini for AI-powered generation, falls back gracefully when unavailable.
"""

import json
import os

from ai_research import is_openai_available
from source_gatherers import (
    gather_web_search,
    gather_industry_benchmarks,
    gather_jira,
    gather_servicenow,
    gather_finnhub_data,
)


async def gather_full_context(db, business_unit_id: int) -> dict:
    """Collect ALL data from Steps 1-3 + external sources into a single context dict."""
    ctx = {}

    # Organization info
    org_rows = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    ctx["organization"] = dict(org_rows[0]) if org_rows else {}

    org_name = ctx["organization"].get("name", "")
    industry = ctx["organization"].get("industry", "")

    # Financial metrics from ops_efficiency
    ops_rows = await db.execute_fetchall("SELECT * FROM ops_efficiency ORDER BY period DESC")
    ctx["financial_metrics"] = [dict(r) for r in ops_rows]

    # Revenue trends
    rev_rows = await db.execute_fetchall("SELECT * FROM revenue_splits ORDER BY period")
    ctx["revenue_trends"] = [dict(r) for r in rev_rows]

    # Competitors from DB
    comp_rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    ctx["competitors"] = [dict(r) for r in comp_rows]

    # Value stream data with metrics
    vs_rows = await db.execute_fetchall(
        "SELECT vs.*, vsm.total_lead_time_hours, vsm.total_process_time_hours, "
        "vsm.total_wait_time_hours, vsm.flow_efficiency, vsm.bottleneck_step, vsm.bottleneck_reason "
        "FROM value_streams vs LEFT JOIN value_stream_metrics vsm ON vs.id = vsm.value_stream_id "
        "WHERE vs.business_unit_id = ?",
        (business_unit_id,),
    )
    ctx["value_streams"] = [dict(r) for r in vs_rows]

    # Value stream benchmarks
    for vs in ctx["value_streams"]:
        bench_rows = await db.execute_fetchall(
            "SELECT * FROM value_stream_benchmarks WHERE value_stream_id = ?", (vs["id"],)
        )
        vs["benchmarks"] = [dict(r) for r in bench_rows]

    # Value stream levers
    lever_rows = await db.execute_fetchall(
        "SELECT * FROM value_stream_levers WHERE impact_estimate = 'high' ORDER BY lever_type"
    )
    ctx["high_impact_levers"] = [dict(r) for r in lever_rows]

    # SWOT entries (for strategy generation)
    swot_rows = await db.execute_fetchall(
        "SELECT * FROM swot_entries WHERE business_unit_id = ? ORDER BY category",
        (business_unit_id,),
    )
    ctx["swot_entries"] = [dict(r) for r in swot_rows]

    # TOWS actions (for strategy generation)
    tows_rows = await db.execute_fetchall(
        "SELECT * FROM tows_actions ORDER BY strategy_type, priority DESC"
    )
    ctx["tows_actions"] = [dict(r) for r in tows_rows]

    # User strategy inputs (full content)
    input_rows = await db.execute_fetchall("SELECT * FROM strategy_inputs ORDER BY input_type")
    inputs_by_type = {}
    for inp in input_rows:
        inp_dict = dict(inp)
        itype = inp_dict["input_type"]
        if itype not in inputs_by_type:
            inputs_by_type[itype] = []
        inputs_by_type[itype].append(inp_dict)
    ctx["user_inputs"] = inputs_by_type

    # Gather external sources (all fail gracefully)
    segment_names = [vs.get("name", "") for vs in ctx["value_streams"]]
    segment = segment_names[0] if segment_names else "general"
    competitor_names = [c.get("name", "") for c in ctx["competitors"] if c.get("name")]

    try:
        ctx["web_search"] = await gather_web_search(segment, industry)
    except Exception:
        ctx["web_search"] = {}

    try:
        ctx["industry_benchmarks"] = await gather_industry_benchmarks(segment, industry)
    except Exception:
        ctx["industry_benchmarks"] = {}

    try:
        ctx["jira_data"] = await gather_jira(segment, industry)
    except Exception:
        ctx["jira_data"] = {}

    try:
        ctx["servicenow_data"] = await gather_servicenow(segment, industry)
    except Exception:
        ctx["servicenow_data"] = {}

    try:
        ctx["finnhub_data"] = await gather_finnhub_data(org_name, industry, competitor_names)
    except Exception:
        ctx["finnhub_data"] = {}

    # RAG: Include relevant document context when in live mode
    try:
        from rag_engine import build_rag_context, is_live_mode
        if await is_live_mode(db):
            org_id = ctx["organization"].get("id")
            query = f"{org_name} {industry} business performance financial metrics strategy value stream"
            rag_text = await build_rag_context(db, query, org_id=org_id, top_k=8)
            if rag_text:
                ctx["rag_context"] = rag_text
    except Exception:
        pass

    return ctx


def _build_context_prompt(context: dict) -> str:
    """Build a text representation of the full context for AI prompts."""
    parts = []

    org = context.get("organization", {})
    if org:
        parts.append(f"Organization: {org.get('name', 'Unknown')} | Industry: {org.get('industry', 'Unknown')}")
        if org.get("market_cap"):
            parts.append(f"Market Cap: ${org['market_cap']:,.0f}M")

    # Financial metrics
    fm = context.get("financial_metrics", [])
    if fm:
        metrics_str = "; ".join(f"{m.get('metric_name')}: {m.get('metric_value')}" for m in fm[:10])
        parts.append(f"Financial Metrics: {metrics_str}")

    # Revenue trends
    rev = context.get("revenue_trends", [])
    if rev:
        rev_str = "; ".join(
            f"{r.get('period', '?')}: ${r.get('revenue', 0):,.0f}" for r in rev[:6]
        )
        parts.append(f"Revenue Trends: {rev_str}")

    # Competitors
    comps = context.get("competitors", [])
    if comps:
        comp_strs = []
        for c in comps[:5]:
            s = c.get("name", "Unknown")
            if c.get("profit_margin") is not None:
                s += f" (PM: {c['profit_margin']:.1%})"
            if c.get("market_cap_value"):
                s += f" (MCap: ${c['market_cap_value']:,.0f}M)"
            comp_strs.append(s)
        parts.append(f"Competitors: {', '.join(comp_strs)}")

    # Value streams
    vs_list = context.get("value_streams", [])
    if vs_list:
        vs_strs = []
        for vs in vs_list:
            s = vs.get("name", "Unknown")
            if vs.get("flow_efficiency"):
                s += f" (FE: {vs['flow_efficiency']:.1f}%)"
            if vs.get("total_lead_time_hours"):
                s += f" (LT: {vs['total_lead_time_hours']:.1f}h)"
            if vs.get("bottleneck_step"):
                s += f" [Bottleneck: {vs['bottleneck_step']}]"
            vs_strs.append(s)
        parts.append(f"Value Streams: {'; '.join(vs_strs)}")

    # Levers
    levers = context.get("high_impact_levers", [])
    if levers:
        lever_strs = [f"{l.get('opportunity', '')}" for l in levers[:5]]
        parts.append(f"High-Impact Levers: {'; '.join(lever_strs)}")

    # Web search
    ws = context.get("web_search", {})
    if ws.get("references"):
        ref_strs = [f"{r.get('title', '')}: {r.get('key_finding', '')}" for r in ws["references"][:5]]
        parts.append(f"Web Search Insights: {'; '.join(ref_strs)}")

    # Industry benchmarks
    ib = context.get("industry_benchmarks", {})
    if ib.get("industry_kpis"):
        parts.append(f"Industry Benchmarks: {json.dumps(ib['industry_kpis'], default=str)}")

    # Jira data
    jira = context.get("jira_data", {})
    if jira and jira.get("source"):
        parts.append(f"Jira Data: {json.dumps(jira, default=str)[:500]}")

    # ServiceNow data
    snow = context.get("servicenow_data", {})
    if snow and snow.get("source"):
        parts.append(f"ServiceNow Data: {json.dumps(snow, default=str)[:500]}")

    # Finnhub data
    fh = context.get("finnhub_data", {})
    if fh.get("peers"):
        peer_strs = []
        for p in fh["peers"][:3]:
            profile = p.get("profile", {})
            financials = p.get("financials", {})
            s = profile.get("name", "Unknown")
            if financials.get("profit_margin"):
                s += f" (PM: {financials['profit_margin']:.1%})"
            peer_strs.append(s)
        parts.append(f"Finnhub Peer Data: {', '.join(peer_strs)}")

    # User inputs
    ui = context.get("user_inputs", {})
    if ui:
        for itype, items in ui.items():
            if items:
                parts.append(f"User Input ({itype}): {items[0].get('content', '')}")

    # SWOT entries (for strategy generation)
    swot = context.get("swot_entries", [])
    if swot:
        by_cat = {}
        for s in swot:
            cat = s.get("category", "unknown")
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(s.get("description", ""))
        for cat, descs in by_cat.items():
            parts.append(f"SWOT {cat}s: {'; '.join(descs[:5])}")

    # TOWS actions (for strategy generation)
    tows = context.get("tows_actions", [])
    if tows:
        tows_strs = [f"[{t.get('strategy_type')}] {t.get('action_description', '')}" for t in tows[:10]]
        parts.append(f"TOWS Actions: {'; '.join(tows_strs)}")

    # RAG: Retrieved document context (only present in live mode)
    rag = context.get("rag_context", "")
    if rag:
        parts.append(f"\n--- Organization Knowledge Base (Retrieved Documents) ---\n{rag}")

    return "\n".join(parts)


async def generate_ai_swot(context: dict) -> dict | None:
    """Use AI to generate SWOT analysis from comprehensive context. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a senior management consultant specializing in strategic analysis. "
            "Given comprehensive data about an organization — financials, value streams, "
            "competitor benchmarks, industry research, and operational data — produce a "
            "SWOT analysis.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "strengths": [{"description": "...", "severity": "high|medium|low", "confidence": "high|medium|low", "data_source": "..."}],\n'
            '  "weaknesses": [...same structure...],\n'
            '  "opportunities": [...same structure...],\n'
            '  "threats": [...same structure...]\n'
            "}\n\n"
            "Rules:\n"
            "- Generate 4-8 entries per category based on actual data, not generic statements\n"
            "- severity: how impactful this factor is (high = critical to strategy)\n"
            "- confidence: how well-supported by data (high = multiple data points confirm)\n"
            "- data_source: which input data supports this (e.g. 'financial metrics', 'value stream analysis', 'web search', 'competitor data')\n"
            "- Be specific — reference actual numbers, competitor names, and process names from the data\n"
            "- For opportunities/threats, consider external market factors from web search results"
        )

        user_prompt = (
            "Based on the following comprehensive context, generate a SWOT analysis:\n\n"
            + _build_context_prompt(context)
        )

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=3000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate minimal structure
        for cat in ["strengths", "weaknesses", "opportunities", "threats"]:
            if cat not in result or not isinstance(result[cat], list):
                result[cat] = []
            # Ensure each entry has required fields
            for entry in result[cat]:
                if isinstance(entry, str):
                    # AI returned plain strings; wrap them
                    idx = result[cat].index(entry)
                    result[cat][idx] = {
                        "description": entry,
                        "severity": "medium",
                        "confidence": "medium",
                        "data_source": "AI-generated",
                    }
                elif isinstance(entry, dict):
                    entry.setdefault("severity", "medium")
                    entry.setdefault("confidence", "medium")
                    entry.setdefault("data_source", "AI-generated")

        return result

    except Exception:
        return None


async def generate_ai_tows(swot_entries: list[dict], context: dict) -> list[dict] | None:
    """Use AI to generate TOWS strategic actions from SWOT entries. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a strategic planning expert. Given a SWOT analysis with severity-scored "
            "entries, generate TOWS strategic actions by intelligently pairing entries.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "actions": [\n'
            "    {\n"
            '      "strategy_type": "SO|WO|ST|WT",\n'
            '      "action_description": "Specific, actionable strategic recommendation",\n'
            '      "swot_1_description": "The first SWOT entry used",\n'
            '      "swot_2_description": "The second SWOT entry used",\n'
            '      "priority": "critical|high|medium|low",\n'
            '      "impact_score": 1-10,\n'
            '      "rationale": "Why this pairing matters"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Generate 12-20 actions total, covering all 4 types (SO, WO, ST, WT)\n"
            "- Prioritize high-severity SWOT entries\n"
            "- Action descriptions must be specific and actionable, not generic\n"
            "- Avoid duplicate or near-duplicate actions\n"
            "- impact_score: 10 = transformational, 1 = marginal improvement\n"
            "- SO actions should be offensive/growth strategies\n"
            "- WO actions should address weaknesses using opportunities\n"
            "- ST actions should use strengths to defend against threats\n"
            "- WT actions should be survival/risk-mitigation strategies"
        )

        # Build SWOT summary for the prompt
        swot_by_cat = {"strength": [], "weakness": [], "opportunity": [], "threat": []}
        for entry in swot_entries:
            cat = entry.get("category", "")
            if cat in swot_by_cat:
                swot_by_cat[cat].append(entry)

        swot_text = ""
        for cat, entries in swot_by_cat.items():
            if entries:
                swot_text += f"\n{cat.upper()}S:\n"
                for e in entries:
                    sev = e.get("severity", "medium")
                    conf = e.get("confidence", "medium")
                    swot_text += f"- [{sev} severity, {conf} confidence] {e.get('description', '')}\n"

        user_prompt = (
            "Generate TOWS strategic actions based on this SWOT analysis:\n"
            + swot_text
            + "\n\nAdditional context:\n"
            + _build_context_prompt(context)
        )

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        actions = result.get("actions", [])
        if not actions:
            return None

        # Validate each action
        for action in actions:
            action.setdefault("strategy_type", "SO")
            action.setdefault("action_description", "Strategic action")
            action.setdefault("swot_1_description", "")
            action.setdefault("swot_2_description", "")
            action.setdefault("priority", "medium")
            action.setdefault("impact_score", 5)
            action.setdefault("rationale", "")
            # Clamp impact_score
            try:
                action["impact_score"] = max(1, min(10, int(action["impact_score"])))
            except (ValueError, TypeError):
                action["impact_score"] = 5

        return actions

    except Exception:
        return None


async def generate_ai_strategies(context: dict, tows_actions: list[dict]) -> dict | None:
    """Use AI to generate 4-layer transformation strategies. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a transformation strategist. Given an organization's complete context "
            "including SWOT analysis, TOWS actions, value stream data, financial metrics, "
            "and user-provided strategic direction, generate a 4-layer transformation strategy.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "layers": {\n'
            '    "business": {\n'
            '      "strategies": [\n'
            "        {\n"
            '          "name": "Strategy name",\n'
            '          "description": "Detailed description incorporating user inputs and data",\n'
            '          "risk_level": "low|medium|high|critical",\n'
            '          "risks": "Key risks and mitigations",\n'
            '          "tows_alignment": "Which TOWS actions this addresses",\n'
            '          "okrs": [\n'
            "            {\n"
            '              "objective": "Measurable objective",\n'
            '              "time_horizon": "12 months",\n'
            '              "key_results": [\n'
            "                {\n"
            '                  "key_result": "Specific measurable outcome",\n'
            '                  "metric": "What to measure",\n'
            '                  "current_value": 0,\n'
            '                  "target_value": 15,\n'
            '                  "target_optimistic": 20,\n'
            '                  "target_pessimistic": 10,\n'
            '                  "unit": "%",\n'
            '                  "rationale": "Why this target based on data"\n'
            "                }\n"
            "              ]\n"
            "            }\n"
            "          ]\n"
            "        }\n"
            "      ]\n"
            "    },\n"
            '    "digital": { "strategies": [...same structure...] },\n'
            '    "data": { "strategies": [...same structure...] },\n'
            '    "gen_ai": { "strategies": [...same structure...] }\n'
            "  },\n"
            '  "cross_layer_notes": "How these 4 layers reinforce each other",\n'
            '  "initiative_suggestions": ["Suggested initiative 1", "Suggested initiative 2"]\n'
            "}\n\n"
            "Rules:\n"
            "- Generate 1-2 strategies per layer (6-8 total)\n"
            "- KR targets MUST be derived from actual data:\n"
            "  - Use current financial metrics as baselines\n"
            "  - Use industry benchmarks for target-setting\n"
            "  - Use competitor data for competitive targets\n"
            "- target_optimistic/target_pessimistic provide scenario ranges\n"
            "- risk_level and risks should be specific, not generic\n"
            "- Incorporate user-provided strategy inputs as primary direction\n"
            "- cross_layer_notes should identify synergies and dependencies\n"
            "- initiative_suggestions should be concrete, actionable project ideas"
        )

        # Build TOWS summary
        tows_text = ""
        if tows_actions:
            tows_text = "\nTOWS Actions:\n"
            for t in tows_actions[:15]:
                tows_text += f"- [{t.get('strategy_type')}] {t.get('action_description', '')} (priority: {t.get('priority', 'medium')})\n"

        user_prompt = (
            "Generate a comprehensive 4-layer transformation strategy:\n\n"
            + _build_context_prompt(context)
            + tows_text
        )

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=5000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate structure
        layers = result.get("layers", {})
        for layer_name in ["business", "digital", "data", "gen_ai"]:
            if layer_name not in layers:
                layers[layer_name] = {"strategies": []}
            layer = layers[layer_name]
            if "strategies" not in layer:
                layer["strategies"] = []
            for strat in layer["strategies"]:
                strat.setdefault("name", f"{layer_name.title()} Strategy")
                strat.setdefault("description", "")
                strat.setdefault("risk_level", "medium")
                strat.setdefault("risks", "")
                strat.setdefault("tows_alignment", "")
                strat.setdefault("okrs", [])
                for okr in strat["okrs"]:
                    okr.setdefault("objective", "Strategic objective")
                    okr.setdefault("time_horizon", "12 months")
                    okr.setdefault("key_results", [])
                    for kr in okr["key_results"]:
                        kr.setdefault("key_result", "Key result")
                        kr.setdefault("metric", "")
                        kr.setdefault("current_value", 0)
                        kr.setdefault("target_value", 0)
                        kr.setdefault("target_optimistic", None)
                        kr.setdefault("target_pessimistic", None)
                        kr.setdefault("unit", "")
                        kr.setdefault("rationale", "")

        result["layers"] = layers
        result.setdefault("cross_layer_notes", "")
        result.setdefault("initiative_suggestions", [])

        return result

    except Exception:
        return None
