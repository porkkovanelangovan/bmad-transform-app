"""
AI Dashboard Module — 10 AI-powered capabilities for the Performance Dashboard.
Uses OpenAI GPT-4o-mini for AI-powered analysis, falls back gracefully when unavailable.
"""

import hashlib
import json
import logging

from ai_research import is_openai_available

logger = logging.getLogger(__name__)


# ─── Context Gatherer ────────────────────────────────────────────────────────


async def gather_dashboard_context(db) -> dict:
    """Collect ALL data across all 7 steps into a single context dict."""
    ctx = {}

    # Step 1: Organization
    org_rows = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    ctx["organization"] = dict(org_rows[0]) if org_rows else {}

    # Step 1: Ops efficiency
    ops_rows = await db.execute_fetchall("SELECT * FROM ops_efficiency ORDER BY period DESC")
    ctx["ops_metrics"] = [dict(r) for r in ops_rows]

    # Step 1: Revenue splits
    rev_rows = await db.execute_fetchall(
        "SELECT rs.*, bu.name as business_unit_name FROM revenue_splits rs "
        "LEFT JOIN business_units bu ON rs.business_unit_id = bu.id ORDER BY rs.period"
    )
    ctx["revenue_trends"] = [dict(r) for r in rev_rows]

    # Step 1: Competitors
    comp_rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    ctx["competitors"] = [dict(r) for r in comp_rows]

    # Step 1: Business units
    bu_rows = await db.execute_fetchall("SELECT * FROM business_units ORDER BY name")
    ctx["business_units"] = [dict(r) for r in bu_rows]

    # Step 2: Value streams with metrics
    try:
        vs_rows = await db.execute_fetchall(
            "SELECT vs.*, vsm.total_lead_time_hours, vsm.total_process_time_hours, "
            "vsm.total_wait_time_hours, vsm.flow_efficiency, vsm.bottleneck_step "
            "FROM value_streams vs LEFT JOIN value_stream_metrics vsm ON vs.id = vsm.value_stream_id"
        )
        ctx["value_streams"] = [dict(r) for r in vs_rows]
    except Exception:
        ctx["value_streams"] = []

    # Step 2: Value stream levers
    try:
        lever_rows = await db.execute_fetchall("SELECT * FROM value_stream_levers ORDER BY lever_type")
        ctx["levers"] = [dict(r) for r in lever_rows]
    except Exception:
        ctx["levers"] = []

    # Step 3: SWOT entries
    try:
        swot_rows = await db.execute_fetchall("SELECT * FROM swot_entries ORDER BY category")
        ctx["swot_entries"] = [dict(r) for r in swot_rows]
    except Exception:
        ctx["swot_entries"] = []

    # Step 3: TOWS actions
    try:
        tows_rows = await db.execute_fetchall("SELECT * FROM tows_actions ORDER BY strategy_type")
        ctx["tows_actions"] = [dict(r) for r in tows_rows]
    except Exception:
        ctx["tows_actions"] = []

    # Step 4: Strategies + OKRs + Key Results
    try:
        strat_rows = await db.execute_fetchall("SELECT * FROM strategies ORDER BY layer, id")
        ctx["strategies"] = [dict(r) for r in strat_rows]
    except Exception:
        ctx["strategies"] = []

    try:
        okr_rows = await db.execute_fetchall("SELECT * FROM strategic_okrs ORDER BY id")
        ctx["strategic_okrs"] = [dict(r) for r in okr_rows]
    except Exception:
        ctx["strategic_okrs"] = []

    try:
        kr_rows = await db.execute_fetchall("SELECT * FROM strategic_key_results ORDER BY id")
        ctx["key_results"] = [dict(r) for r in kr_rows]
    except Exception:
        ctx["key_results"] = []

    # Step 5: Initiatives
    try:
        init_rows = await db.execute_fetchall("SELECT * FROM initiatives ORDER BY rice_score DESC")
        ctx["initiatives"] = [dict(r) for r in init_rows]
    except Exception:
        ctx["initiatives"] = []

    # Step 6: Epics
    try:
        epic_rows = await db.execute_fetchall("SELECT * FROM epics ORDER BY id")
        ctx["epics"] = [dict(r) for r in epic_rows]
    except Exception:
        ctx["epics"] = []

    # Step 7: Features
    try:
        feat_rows = await db.execute_fetchall("SELECT * FROM features ORDER BY id")
        ctx["features"] = [dict(r) for r in feat_rows]
    except Exception:
        ctx["features"] = []

    # Review gates
    try:
        gate_rows = await db.execute_fetchall("SELECT * FROM review_gates ORDER BY step, gate_number")
        ctx["review_gates"] = [dict(r) for r in gate_rows]
    except Exception:
        ctx["review_gates"] = []

    # RAG: Include relevant document context when in live mode
    try:
        from rag_engine import build_rag_context, is_live_mode
        if await is_live_mode(db):
            org_name = ctx["organization"].get("name", "")
            industry = ctx["organization"].get("industry", "")
            org_id = ctx["organization"].get("id")
            query = f"{org_name} {industry} business performance financial analysis transformation"
            rag_text = await build_rag_context(db, query, org_id=org_id, top_k=6)
            if rag_text:
                ctx["rag_context"] = rag_text
    except Exception:
        pass

    return ctx


# ─── Caching Helpers ─────────────────────────────────────────────────────────


def _compute_data_hash(data) -> str:
    """MD5 hash of input data for cache key."""
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


async def _get_cached_analysis(db, analysis_type: str, input_hash: str) -> dict | None:
    """Check ai_analysis_cache table for a valid cached result."""
    try:
        row = await db.execute_fetchone(
            "SELECT result_json FROM ai_analysis_cache "
            "WHERE analysis_type = ? AND input_hash = ? "
            "AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP) "
            "ORDER BY created_at DESC LIMIT 1",
            (analysis_type, input_hash),
        )
        if row:
            return json.loads(row["result_json"])
    except Exception:
        pass
    return None


async def _cache_analysis(db, analysis_type: str, input_hash: str, result: dict):
    """Store analysis result in cache with 24-hour expiry."""
    from datetime import datetime, timedelta
    try:
        expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        await db.execute(
            "INSERT INTO ai_analysis_cache (analysis_type, input_hash, result_json, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (analysis_type, input_hash, json.dumps(result, default=str), expires),
        )
        await db.commit()
    except Exception:
        pass


# ─── Context Prompt Builder ──────────────────────────────────────────────────


def _build_dashboard_prompt(ctx: dict) -> str:
    """Build a text representation of dashboard context for AI prompts."""
    parts = []

    org = ctx.get("organization", {})
    if org:
        parts.append(f"Organization: {org.get('name', 'Unknown')} | Industry: {org.get('industry', 'Unknown')}")
        if org.get("market_cap"):
            parts.append(f"Market Cap: ${org['market_cap']:,.0f}M")

    # Ops metrics
    ops = ctx.get("ops_metrics", [])
    if ops:
        metrics_str = "; ".join(f"{m.get('metric_name')}: {m.get('metric_value')}" for m in ops[:15])
        parts.append(f"Operational Metrics: {metrics_str}")

    # Revenue trends
    rev = ctx.get("revenue_trends", [])
    if rev:
        rev_str = "; ".join(
            f"{r.get('business_unit_name', '?')} {r.get('period', '?')}: ${r.get('revenue', 0):,.0f}"
            for r in rev[:10]
        )
        parts.append(f"Revenue Data: {rev_str}")

    # Competitors
    comps = ctx.get("competitors", [])
    if comps:
        comp_strs = []
        for c in comps[:6]:
            s = c.get("name", "Unknown")
            if c.get("profit_margin") is not None:
                try:
                    s += f" (PM: {float(c['profit_margin']):.1%})"
                except (ValueError, TypeError):
                    pass
            if c.get("market_cap_value"):
                s += f" (MCap: ${c['market_cap_value']:,.0f}M)"
            comp_strs.append(s)
        parts.append(f"Competitors: {', '.join(comp_strs)}")

    # Value streams
    vs_list = ctx.get("value_streams", [])
    if vs_list:
        vs_strs = []
        for vs in vs_list[:5]:
            s = vs.get("name", "Unknown")
            if vs.get("flow_efficiency"):
                s += f" (FE: {vs['flow_efficiency']:.1f}%)"
            vs_strs.append(s)
        parts.append(f"Value Streams: {'; '.join(vs_strs)}")

    # SWOT entries
    swot = ctx.get("swot_entries", [])
    if swot:
        by_cat = {}
        for s in swot:
            cat = s.get("category", "unknown")
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(s.get("description", ""))
        for cat, descs in by_cat.items():
            parts.append(f"SWOT {cat}s: {'; '.join(descs[:4])}")

    # Strategies
    strats = ctx.get("strategies", [])
    if strats:
        strat_strs = [f"[{s.get('layer')}] {s.get('name', '')}" for s in strats[:6]]
        parts.append(f"Strategies: {'; '.join(strat_strs)}")

    # Initiatives
    inits = ctx.get("initiatives", [])
    if inits:
        init_strs = [f"{i.get('name', '')} (RICE: {i.get('rice_score', '?')})" for i in inits[:5]]
        parts.append(f"Top Initiatives: {'; '.join(init_strs)}")

    # Epics
    epics = ctx.get("epics", [])
    if epics:
        parts.append(f"Epics: {len(epics)} total")

    # Features
    features = ctx.get("features", [])
    if features:
        parts.append(f"Features: {len(features)} total")

    return "\n".join(parts)


# ─── Function 1: AI Financial Analysis ───────────────────────────────────────


async def ai_financial_analysis(org, ops_metrics, competitors, revenue_trends) -> dict | None:
    """AI-powered financial SWOT with contextual insights. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a senior financial analyst specializing in corporate performance assessment. "
            "Given an organization's financial data, operational metrics, competitor benchmarks, "
            "and revenue trends, produce a comprehensive financial analysis.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "strengths": [{"description": "...", "severity": "high|medium|low", "confidence": "high|medium|low", "metric_reference": "..."}],\n'
            '  "weaknesses": [same structure],\n'
            '  "opportunities": [same structure],\n'
            '  "threats": [same structure],\n'
            '  "key_insights": [{"insight": "...", "supporting_data": "...", "strategic_implication": "..."}],\n'
            '  "data_quality_score": 0-100,\n'
            '  "analysis_confidence": "high|medium|low"\n'
            "}\n\n"
            "Rules:\n"
            "- Generate 3-6 entries per SWOT category based on actual data\n"
            "- Reference specific numbers and competitor names\n"
            "- key_insights should highlight non-obvious patterns\n"
            "- data_quality_score: 100 = comprehensive data, 0 = almost no data\n"
        )

        user_prompt = (
            "Analyze the following organization's financial performance:\n\n"
            f"Organization: {json.dumps(org, default=str)}\n\n"
            f"Operational Metrics: {json.dumps(ops_metrics[:15], default=str)}\n\n"
            f"Competitors: {json.dumps(competitors[:6], default=str)}\n\n"
            f"Revenue Trends: {json.dumps(revenue_trends[:12], default=str)}\n"
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

        # Validate structure
        for cat in ["strengths", "weaknesses", "opportunities", "threats"]:
            if cat not in result or not isinstance(result[cat], list):
                result[cat] = []
            for entry in result[cat]:
                if isinstance(entry, str):
                    idx = result[cat].index(entry)
                    result[cat][idx] = {
                        "description": entry,
                        "severity": "medium",
                        "confidence": "medium",
                        "metric_reference": "AI-generated",
                    }
                elif isinstance(entry, dict):
                    entry.setdefault("severity", "medium")
                    entry.setdefault("confidence", "medium")
                    entry.setdefault("metric_reference", "")

        if "key_insights" not in result or not isinstance(result["key_insights"], list):
            result["key_insights"] = []

        # Clamp data_quality_score
        try:
            result["data_quality_score"] = max(0, min(100, int(result.get("data_quality_score", 50))))
        except (ValueError, TypeError):
            result["data_quality_score"] = 50

        if result.get("analysis_confidence") not in ("high", "medium", "low"):
            result["analysis_confidence"] = "medium"

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 2: AI Discover Competitors ─────────────────────────────────────


async def ai_discover_competitors(org_name, industry, existing_competitors) -> dict | None:
    """Auto-discover competitors and analyze competitive positioning. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a competitive intelligence analyst. Given an organization's name, industry, "
            "and existing known competitors, discover additional competitors and analyze positioning.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "discovered_competitors": [{"name": "...", "ticker": "...", "relevance": "direct|indirect|emerging", "threat_score": 1-10, "rationale": "..."}],\n'
            '  "competitive_positioning": {"org_position": "leader|challenger|follower|niche", "market_dynamics": "...", "key_differentiators": [...], "vulnerability_areas": [...]},\n'
            '  "market_opportunities": [{"opportunity": "...", "competitor_gap": "...", "estimated_impact": "high|medium|low"}]\n'
            "}\n\n"
            "Rules:\n"
            "- Discover 4-8 competitors not already in the existing list\n"
            "- threat_score: 10 = existential threat, 1 = minimal overlap\n"
            "- Include ticker symbols where available\n"
            "- Focus on actionable competitive intelligence\n"
        )

        existing_names = [c.get("name", "") for c in existing_competitors] if existing_competitors else []
        user_prompt = (
            f"Organization: {org_name}\n"
            f"Industry: {industry}\n"
            f"Existing competitors (do NOT repeat these): {', '.join(existing_names)}\n\n"
            "Discover additional competitors and analyze competitive positioning."
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

        # Validate
        if "discovered_competitors" not in result or not isinstance(result["discovered_competitors"], list):
            result["discovered_competitors"] = []
        for comp in result["discovered_competitors"]:
            comp.setdefault("name", "Unknown")
            comp.setdefault("ticker", "")
            if comp.get("relevance") not in ("direct", "indirect", "emerging"):
                comp["relevance"] = "indirect"
            try:
                comp["threat_score"] = max(1, min(10, int(comp.get("threat_score", 5))))
            except (ValueError, TypeError):
                comp["threat_score"] = 5
            comp.setdefault("rationale", "")

        result.setdefault("competitive_positioning", {})
        pos = result["competitive_positioning"]
        if pos.get("org_position") not in ("leader", "challenger", "follower", "niche"):
            pos["org_position"] = "challenger"
        pos.setdefault("market_dynamics", "")
        pos.setdefault("key_differentiators", [])
        pos.setdefault("vulnerability_areas", [])

        if "market_opportunities" not in result or not isinstance(result["market_opportunities"], list):
            result["market_opportunities"] = []
        for opp in result["market_opportunities"]:
            if opp.get("estimated_impact") not in ("high", "medium", "low"):
                opp["estimated_impact"] = "medium"

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 3: AI Trend Analysis ───────────────────────────────────────────


async def ai_trend_analysis(revenue_trends, ops_metrics, org_name) -> dict | None:
    """Revenue trends, growth forecasting, metric trajectory analysis. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a financial forecasting analyst. Given revenue data and operational metrics, "
            "analyze trends, forecast growth, and identify metric trajectories.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "revenue_trend": {"direction": "growing|declining|stable|volatile", "cagr_pct": 12.5, '
            '"yoy_growth_rates": [{"period": "...", "rate_pct": 8.5}], "narrative": "..."},\n'
            '  "forecasts": [{"period": "next_year", "revenue_estimate": 1500000000, '
            '"confidence_interval_low": ..., "confidence_interval_high": ..., "methodology": "..."}],\n'
            '  "metric_trajectories": [{"metric_name": "...", "current_value": ..., '
            '"trajectory": "improving|declining|stable", "rate_of_change": "..."}],\n'
            '  "seasonal_patterns": "...",\n'
            '  "risk_indicators": ["..."]\n'
            "}\n\n"
            "Rules:\n"
            "- Base analysis on actual data provided\n"
            "- cagr_pct should be calculated from revenue data if possible\n"
            "- Provide 1-3 forecast periods\n"
            "- Be specific about methodology used\n"
        )

        user_prompt = (
            f"Organization: {org_name}\n\n"
            f"Revenue Data: {json.dumps(revenue_trends[:15], default=str)}\n\n"
            f"Operational Metrics: {json.dumps(ops_metrics[:15], default=str)}\n"
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

        # Validate revenue_trend
        rt = result.get("revenue_trend", {})
        if not isinstance(rt, dict):
            rt = {}
        if rt.get("direction") not in ("growing", "declining", "stable", "volatile"):
            rt["direction"] = "stable"
        try:
            rt["cagr_pct"] = max(-100, min(500, float(rt.get("cagr_pct", 0))))
        except (ValueError, TypeError):
            rt["cagr_pct"] = 0
        rt.setdefault("yoy_growth_rates", [])
        rt.setdefault("narrative", "")
        result["revenue_trend"] = rt

        # Validate forecasts
        if "forecasts" not in result or not isinstance(result["forecasts"], list):
            result["forecasts"] = []

        # Validate metric_trajectories
        if "metric_trajectories" not in result or not isinstance(result["metric_trajectories"], list):
            result["metric_trajectories"] = []
        for mt in result["metric_trajectories"]:
            if mt.get("trajectory") not in ("improving", "declining", "stable"):
                mt["trajectory"] = "stable"

        result.setdefault("seasonal_patterns", "")
        result.setdefault("risk_indicators", [])

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 4: AI Anomaly Detection ────────────────────────────────────────


async def ai_anomaly_detection(org_data, ops_metrics, competitors, revenue_trends) -> dict | None:
    """Flag unusual metric values and data quality issues. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a data quality and anomaly detection specialist. Given an organization's data, "
            "identify anomalies, data quality issues, and benchmark deviations.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "anomalies": [{"metric_name": "...", "entity": "...", "value": ..., "expected_range": "...", '
            '"severity": "critical|high|medium|low", "explanation": "...", "possible_cause": "..."}],\n'
            '  "data_quality_issues": [{"issue": "...", "affected_entity": "...", "recommendation": "...", "impact": "..."}],\n'
            '  "benchmark_deviations": [{"metric": "...", "entity": "...", "deviation_pct": ..., '
            '"direction": "above|below", "significance": "significant|moderate|minor"}],\n'
            '  "overall_data_health": {"score": 0-100, "missing_critical_fields": [...], "recommendations": [...]}\n'
            "}\n\n"
            "Rules:\n"
            "- Flag metrics that are unusual for the industry\n"
            "- Identify missing or incomplete data\n"
            "- Compare against competitors where possible\n"
            "- Be specific about what constitutes the anomaly\n"
        )

        user_prompt = (
            f"Organization: {json.dumps(org_data, default=str)}\n\n"
            f"Operational Metrics: {json.dumps(ops_metrics[:15], default=str)}\n\n"
            f"Competitors: {json.dumps(competitors[:6], default=str)}\n\n"
            f"Revenue Trends: {json.dumps(revenue_trends[:12], default=str)}\n"
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

        # Validate
        if "anomalies" not in result or not isinstance(result["anomalies"], list):
            result["anomalies"] = []
        for a in result["anomalies"]:
            if a.get("severity") not in ("critical", "high", "medium", "low"):
                a["severity"] = "medium"

        if "data_quality_issues" not in result or not isinstance(result["data_quality_issues"], list):
            result["data_quality_issues"] = []

        if "benchmark_deviations" not in result or not isinstance(result["benchmark_deviations"], list):
            result["benchmark_deviations"] = []
        for bd in result["benchmark_deviations"]:
            if bd.get("direction") not in ("above", "below"):
                bd["direction"] = "above"
            if bd.get("significance") not in ("significant", "moderate", "minor"):
                bd["significance"] = "moderate"

        health = result.get("overall_data_health", {})
        if not isinstance(health, dict):
            health = {}
        try:
            health["score"] = max(0, min(100, int(health.get("score", 50))))
        except (ValueError, TypeError):
            health["score"] = 50
        health.setdefault("missing_critical_fields", [])
        health.setdefault("recommendations", [])
        result["overall_data_health"] = health

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 5: AI Executive Summary ────────────────────────────────────────


async def ai_executive_summary(org_data, ops_metrics, competitors, revenue_trends, swot) -> dict | None:
    """Generate narrative executive summary. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a management consulting partner writing an executive briefing. "
            "Given comprehensive organizational data, produce a concise executive summary.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "headline": "One-sentence performance headline",\n'
            '  "summary_paragraphs": ["paragraph1", "paragraph2", "paragraph3"],\n'
            '  "key_findings": [{"finding": "...", "impact": "high|medium|low", "action_required": "immediate|short_term|monitoring"}],\n'
            '  "competitor_narrative": "...",\n'
            '  "strategic_implications": [{"implication": "...", "timeframe": "immediate|6_months|12_months", "recommended_action": "..."}],\n'
            '  "data_completeness_note": "..."\n'
            "}\n\n"
            "Rules:\n"
            "- Headline should be impactful and data-driven\n"
            "- 3 summary paragraphs: performance overview, competitive position, outlook\n"
            "- 3-5 key findings with specific data references\n"
            "- Strategic implications should be actionable\n"
        )

        user_prompt = (
            f"Organization: {json.dumps(org_data, default=str)}\n\n"
            f"Metrics: {json.dumps(ops_metrics[:15], default=str)}\n\n"
            f"Competitors: {json.dumps(competitors[:6], default=str)}\n\n"
            f"Revenue: {json.dumps(revenue_trends[:12], default=str)}\n\n"
            f"SWOT: {json.dumps(swot[:20], default=str)}\n"
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

        # Validate
        result.setdefault("headline", "Executive Summary")
        if "summary_paragraphs" not in result or not isinstance(result["summary_paragraphs"], list):
            result["summary_paragraphs"] = []
        if "key_findings" not in result or not isinstance(result["key_findings"], list):
            result["key_findings"] = []
        for f in result["key_findings"]:
            if f.get("impact") not in ("high", "medium", "low"):
                f["impact"] = "medium"
            if f.get("action_required") not in ("immediate", "short_term", "monitoring"):
                f["action_required"] = "monitoring"
        result.setdefault("competitor_narrative", "")
        if "strategic_implications" not in result or not isinstance(result["strategic_implications"], list):
            result["strategic_implications"] = []
        for si in result["strategic_implications"]:
            if si.get("timeframe") not in ("immediate", "6_months", "12_months"):
                si["timeframe"] = "6_months"
        result.setdefault("data_completeness_note", "")

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 6: AI Data Enrichment Suggestions ─────────────────────────────


async def ai_data_enrichment_suggestions(org_data, industry, existing_data_summary) -> dict | None:
    """Suggest missing data fields, infer business units, suggest revenue dimensions. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a data strategy consultant. Given an organization's existing data, "
            "identify gaps and suggest enrichment opportunities.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "missing_metrics": [{"metric_name": "...", "importance": "high|medium|low", "industry_typical_range": "...", "how_to_obtain": "..."}],\n'
            '  "suggested_business_units": [{"name": "...", "description": "...", "rationale": "..."}],\n'
            '  "revenue_dimensions": [{"dimension": "product|region|segment", "dimension_value": "...", "rationale": "..."}],\n'
            '  "competitor_suggestions": [{"name": "...", "rationale": "..."}],\n'
            '  "data_completeness_score": 0-100,\n'
            '  "priority_actions": ["..."]\n'
            "}\n\n"
            "Rules:\n"
            "- Suggest 5-10 missing metrics important for the industry\n"
            "- Business unit suggestions should be industry-appropriate\n"
            "- Revenue dimensions should enable deeper analysis\n"
            "- Priority actions should be ordered by impact\n"
        )

        user_prompt = (
            f"Organization: {json.dumps(org_data, default=str)}\n"
            f"Industry: {industry}\n\n"
            f"Existing Data Summary: {json.dumps(existing_data_summary, default=str)}\n"
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

        # Validate
        if "missing_metrics" not in result or not isinstance(result["missing_metrics"], list):
            result["missing_metrics"] = []
        for mm in result["missing_metrics"]:
            if mm.get("importance") not in ("high", "medium", "low"):
                mm["importance"] = "medium"

        if "suggested_business_units" not in result or not isinstance(result["suggested_business_units"], list):
            result["suggested_business_units"] = []
        if "revenue_dimensions" not in result or not isinstance(result["revenue_dimensions"], list):
            result["revenue_dimensions"] = []
        if "competitor_suggestions" not in result or not isinstance(result["competitor_suggestions"], list):
            result["competitor_suggestions"] = []

        try:
            result["data_completeness_score"] = max(0, min(100, int(result.get("data_completeness_score", 50))))
        except (ValueError, TypeError):
            result["data_completeness_score"] = 50

        if "priority_actions" not in result or not isinstance(result["priority_actions"], list):
            result["priority_actions"] = []

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 7: AI Transformation Health ────────────────────────────────────


async def ai_transformation_health(all_step_data: dict) -> dict | None:
    """Cross-step transformation health assessment. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a transformation program manager assessing the health of a 7-step "
            "business transformation. Given data from all steps, evaluate completeness, "
            "quality, and readiness.\n\n"
            "The 7 steps are:\n"
            "1. Performance Dashboard (organization, metrics, competitors, revenue)\n"
            "2. Value Stream Analysis (value streams, metrics, benchmarks, levers)\n"
            "3. SWOT/TOWS Engine (swot entries, tows actions)\n"
            "4. Strategy & OKRs (strategies, strategic OKRs, key results)\n"
            "5. Initiatives & RICE (initiatives with RICE scoring)\n"
            "6. Epics & Roadmap (epics, teams)\n"
            "7. Features & Roadmap (features, delivery OKRs)\n\n"
            "Return JSON:\n"
            "{\n"
            '  "overall_health_score": 0-100,\n'
            '  "step_scores": [{"step": 1, "name": "Performance Dashboard", "score": 0-100, "completeness_pct": 0-100, '
            '"quality_rating": "excellent|good|fair|poor", "issues": [...], "recommendations": [...]}],\n'
            '  "transformation_readiness": "ready|nearly_ready|needs_work|not_ready",\n'
            '  "critical_gaps": [{"gap": "...", "affected_steps": [1,3], "remediation": "...", "priority": "critical|high|medium"}],\n'
            '  "gate_recommendations": [{"step": 1, "gate_name": "...", "recommendation": "approve|revision_needed|reject", "rationale": "..."}],\n'
            '  "next_actions": ["..."]\n'
            "}\n\n"
            "Rules:\n"
            "- Score each step based on data completeness and quality\n"
            "- A step with no data should score 0-10\n"
            "- Identify dependencies between steps\n"
            "- Be specific about what's missing in each step\n"
        )

        user_prompt = (
            "Assess the transformation health based on this data:\n\n"
            + _build_dashboard_prompt(all_step_data)
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

        # Validate
        try:
            result["overall_health_score"] = max(0, min(100, int(result.get("overall_health_score", 50))))
        except (ValueError, TypeError):
            result["overall_health_score"] = 50

        if "step_scores" not in result or not isinstance(result["step_scores"], list):
            result["step_scores"] = []
        for ss in result["step_scores"]:
            try:
                ss["score"] = max(0, min(100, int(ss.get("score", 0))))
            except (ValueError, TypeError):
                ss["score"] = 0
            try:
                ss["completeness_pct"] = max(0, min(100, int(ss.get("completeness_pct", 0))))
            except (ValueError, TypeError):
                ss["completeness_pct"] = 0
            if ss.get("quality_rating") not in ("excellent", "good", "fair", "poor"):
                ss["quality_rating"] = "poor"
            ss.setdefault("issues", [])
            ss.setdefault("recommendations", [])

        if result.get("transformation_readiness") not in ("ready", "nearly_ready", "needs_work", "not_ready"):
            result["transformation_readiness"] = "needs_work"

        if "critical_gaps" not in result or not isinstance(result["critical_gaps"], list):
            result["critical_gaps"] = []
        for cg in result["critical_gaps"]:
            if cg.get("priority") not in ("critical", "high", "medium"):
                cg["priority"] = "medium"

        if "gate_recommendations" not in result or not isinstance(result["gate_recommendations"], list):
            result["gate_recommendations"] = []

        result.setdefault("next_actions", [])

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 8: AI Natural Language Query ───────────────────────────────────


async def ai_natural_language_query(question: str, all_data_context: dict) -> dict | None:
    """Answer natural language questions about org data. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a business intelligence assistant. Given comprehensive organizational data "
            "from a 7-step transformation tool, answer the user's question accurately.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "answer": "Direct, concise answer",\n'
            '  "supporting_data": [{"source": "...", "data_point": "...", "relevance": "..."}],\n'
            '  "confidence": "high|medium|low",\n'
            '  "caveats": ["..."],\n'
            '  "follow_up_questions": ["..."],\n'
            '  "data_tables_queried": ["organization", "competitors", "..."]\n'
            "}\n\n"
            "Rules:\n"
            "- Answer directly and specifically\n"
            "- Reference actual data values in supporting_data\n"
            "- Acknowledge data limitations in caveats\n"
            "- Suggest 2-3 relevant follow-up questions\n"
            "- data_tables_queried should list which data sources were used\n"
        )

        user_prompt = (
            f"Question: {question}\n\n"
            "Available data:\n"
            + _build_dashboard_prompt(all_data_context)
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

        # Validate
        result.setdefault("answer", "Unable to determine from available data.")
        if "supporting_data" not in result or not isinstance(result["supporting_data"], list):
            result["supporting_data"] = []
        if result.get("confidence") not in ("high", "medium", "low"):
            result["confidence"] = "medium"
        if "caveats" not in result or not isinstance(result["caveats"], list):
            result["caveats"] = []
        if "follow_up_questions" not in result or not isinstance(result["follow_up_questions"], list):
            result["follow_up_questions"] = []
        if "data_tables_queried" not in result or not isinstance(result["data_tables_queried"], list):
            result["data_tables_queried"] = []

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 9: AI What-If Scenario ─────────────────────────────────────────


async def ai_whatif_scenario(scenario_params: dict, org_data, competitors, revenue_trends) -> dict | None:
    """Model what-if scenarios with downstream impact analysis. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a strategic scenario planner. Given a what-if scenario and organizational data, "
            "model the potential impacts across financial, competitive, and operational dimensions.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "scenario_summary": "...",\n'
            '  "impact_analysis": {\n'
            '    "financial_impact": {"revenue_change_pct": ..., "margin_impact_pct": ..., "narrative": "..."},\n'
            '    "competitive_impact": {"market_position_change": "improves|stable|weakens", "narrative": "..."},\n'
            '    "operational_impact": {"complexity_change": "increases|stable|decreases", "narrative": "..."}\n'
            "  },\n"
            '  "risks": [{"risk": "...", "probability": "high|medium|low", "mitigation": "..."}],\n'
            '  "opportunities": [{"opportunity": "...", "probability": "high|medium|low"}],\n'
            '  "downstream_effects": {"on_strategies": "...", "on_initiatives": "...", "on_value_streams": "..."},\n'
            '  "recommendation": "...",\n'
            '  "confidence": "high|medium|low"\n'
            "}\n\n"
            "Rules:\n"
            "- Base analysis on actual organizational data\n"
            "- Be specific about financial impact estimates\n"
            "- Consider competitive dynamics\n"
            "- Provide actionable recommendations\n"
        )

        user_prompt = (
            f"Scenario: {json.dumps(scenario_params, default=str)}\n\n"
            f"Organization: {json.dumps(org_data, default=str)}\n\n"
            f"Competitors: {json.dumps(competitors[:6], default=str)}\n\n"
            f"Revenue: {json.dumps(revenue_trends[:12], default=str)}\n"
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

        # Validate
        result.setdefault("scenario_summary", "")

        ia = result.get("impact_analysis", {})
        if not isinstance(ia, dict):
            ia = {}
        ia.setdefault("financial_impact", {"revenue_change_pct": 0, "margin_impact_pct": 0, "narrative": ""})
        ci = ia.get("competitive_impact", {})
        if ci.get("market_position_change") not in ("improves", "stable", "weakens"):
            ci["market_position_change"] = "stable"
        ia.setdefault("competitive_impact", ci)
        oi = ia.get("operational_impact", {})
        if oi.get("complexity_change") not in ("increases", "stable", "decreases"):
            oi["complexity_change"] = "stable"
        ia.setdefault("operational_impact", oi)
        result["impact_analysis"] = ia

        if "risks" not in result or not isinstance(result["risks"], list):
            result["risks"] = []
        for r in result["risks"]:
            if r.get("probability") not in ("high", "medium", "low"):
                r["probability"] = "medium"

        if "opportunities" not in result or not isinstance(result["opportunities"], list):
            result["opportunities"] = []
        for o in result["opportunities"]:
            if o.get("probability") not in ("high", "medium", "low"):
                o["probability"] = "medium"

        result.setdefault("downstream_effects", {"on_strategies": "", "on_initiatives": "", "on_value_streams": ""})
        result.setdefault("recommendation", "")
        if result.get("confidence") not in ("high", "medium", "low"):
            result["confidence"] = "medium"

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None


# ─── Function 10: AI Generate Report ─────────────────────────────────────────


async def ai_generate_report(org_data, ops_metrics, competitors, revenue_trends, swot, audience) -> dict | None:
    """Generate transformation report tailored by audience. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            f"You are a management consultant generating a transformation report for a {audience} audience. "
            "Tailor depth, terminology, and focus accordingly.\n\n"
            "Audience guidelines:\n"
            "- c_suite: Strategic focus, financial impact, key decisions needed\n"
            "- technical: Implementation details, architecture, technical risks\n"
            "- board: High-level governance, risk, ROI, competitive position\n\n"
            "Return JSON:\n"
            "{\n"
            '  "report_title": "...",\n'
            '  "date": "YYYY-MM-DD",\n'
            '  "audience": "c_suite|technical|board",\n'
            '  "sections": [{"title": "...", "content": "Markdown content", '
            '"data_visualizations": [{"type": "bar_chart|table|metric_card", "title": "...", "description": "..."}]}],\n'
            '  "key_takeaways": ["..."],\n'
            '  "appendix_notes": ["..."]\n'
            "}\n\n"
            "Rules:\n"
            "- Generate 4-6 sections with substantive content\n"
            "- Use markdown formatting in content\n"
            "- Reference specific data points\n"
            "- Key takeaways should be 3-5 bullet points\n"
        )

        user_prompt = (
            f"Organization: {json.dumps(org_data, default=str)}\n\n"
            f"Metrics: {json.dumps(ops_metrics[:15], default=str)}\n\n"
            f"Competitors: {json.dumps(competitors[:6], default=str)}\n\n"
            f"Revenue: {json.dumps(revenue_trends[:12], default=str)}\n\n"
            f"SWOT: {json.dumps(swot[:20], default=str)}\n"
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

        # Validate
        result.setdefault("report_title", "Transformation Report")
        result.setdefault("date", "")
        if result.get("audience") not in ("c_suite", "technical", "board"):
            result["audience"] = audience
        if "sections" not in result or not isinstance(result["sections"], list):
            result["sections"] = []
        for section in result["sections"]:
            section.setdefault("title", "Section")
            section.setdefault("content", "")
            if "data_visualizations" not in section or not isinstance(section["data_visualizations"], list):
                section["data_visualizations"] = []
        if "key_takeaways" not in result or not isinstance(result["key_takeaways"], list):
            result["key_takeaways"] = []
        if "appendix_notes" not in result or not isinstance(result["appendix_notes"], list):
            result["appendix_notes"] = []

        return result

    except Exception as e:
        logger.error("AI dashboard call failed: %s", e)
        return None
