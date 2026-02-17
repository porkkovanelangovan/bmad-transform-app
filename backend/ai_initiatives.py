"""
AI Initiatives, Epics & Features Generation Module.
Uses OpenAI GPT-4o-mini for AI-powered generation, falls back gracefully when unavailable.
Follows the same pattern as ai_swot_strategy.py.
"""

import json

from ai_research import is_openai_available
from ai_swot_strategy import _build_context_prompt
from source_gatherers import (
    gather_web_search,
    gather_industry_benchmarks,
    gather_finnhub_data,
)


async def gather_initiative_context(db) -> dict:
    """Collect ALL upstream data relevant to initiative/epic/feature generation."""
    ctx = {}

    # Organization info
    org_rows = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    ctx["organization"] = dict(org_rows[0]) if org_rows else {}

    org_name = ctx["organization"].get("name", "")
    industry = ctx["organization"].get("industry", "")

    # Financial metrics
    ops_rows = await db.execute_fetchall("SELECT * FROM ops_efficiency ORDER BY period DESC")
    ctx["financial_metrics"] = [dict(r) for r in ops_rows]

    # Revenue trends
    rev_rows = await db.execute_fetchall("SELECT * FROM revenue_splits ORDER BY period")
    ctx["revenue_trends"] = [dict(r) for r in rev_rows]

    # Competitors
    comp_rows = await db.execute_fetchall("SELECT * FROM competitors ORDER BY name")
    ctx["competitors"] = [dict(r) for r in comp_rows]

    # Value streams with metrics and benchmarks
    vs_rows = await db.execute_fetchall(
        "SELECT vs.*, vsm.total_lead_time_hours, vsm.total_process_time_hours, "
        "vsm.total_wait_time_hours, vsm.flow_efficiency, vsm.bottleneck_step, vsm.bottleneck_reason "
        "FROM value_streams vs LEFT JOIN value_stream_metrics vsm ON vs.id = vsm.value_stream_id"
    )
    ctx["value_streams"] = [dict(r) for r in vs_rows]

    for vs in ctx["value_streams"]:
        bench_rows = await db.execute_fetchall(
            "SELECT * FROM value_stream_benchmarks WHERE value_stream_id = ?", (vs["id"],)
        )
        vs["benchmarks"] = [dict(r) for r in bench_rows]

    # High-impact levers
    lever_rows = await db.execute_fetchall(
        "SELECT * FROM value_stream_levers WHERE impact_estimate = 'high' ORDER BY lever_type"
    )
    ctx["high_impact_levers"] = [dict(r) for r in lever_rows]

    # SWOT entries with severity/confidence
    swot_rows = await db.execute_fetchall(
        "SELECT * FROM swot_entries ORDER BY category"
    )
    ctx["swot_entries"] = [dict(r) for r in swot_rows]

    # TOWS actions with impact scores
    tows_rows = await db.execute_fetchall(
        "SELECT * FROM tows_actions ORDER BY strategy_type, priority DESC"
    )
    ctx["tows_actions"] = [dict(r) for r in tows_rows]

    # User strategy inputs
    input_rows = await db.execute_fetchall("SELECT * FROM strategy_inputs ORDER BY input_type")
    inputs_by_type = {}
    for inp in input_rows:
        inp_dict = dict(inp)
        itype = inp_dict["input_type"]
        if itype not in inputs_by_type:
            inputs_by_type[itype] = []
        inputs_by_type[itype].append(inp_dict)
    ctx["user_inputs"] = inputs_by_type

    # Approved strategies with OKRs and key results
    strat_rows = await db.execute_fetchall(
        "SELECT * FROM strategies WHERE approved = 1 ORDER BY layer, id"
    )
    strategies = []
    for s in strat_rows:
        s_dict = dict(s)
        okr_rows = await db.execute_fetchall(
            "SELECT * FROM strategic_okrs WHERE strategy_id = ?", (s_dict["id"],)
        )
        s_dict["okrs"] = []
        for okr in okr_rows:
            okr_dict = dict(okr)
            kr_rows = await db.execute_fetchall(
                "SELECT * FROM strategic_key_results WHERE okr_id = ?", (okr_dict["id"],)
            )
            okr_dict["key_results"] = [dict(kr) for kr in kr_rows]
            s_dict["okrs"].append(okr_dict)
        strategies.append(s_dict)
    ctx["approved_strategies"] = strategies

    # Existing initiatives (for deduplication in epic generation)
    init_rows = await db.execute_fetchall(
        "SELECT i.*, s.layer as strategy_layer, s.name as strategy_name "
        "FROM initiatives i LEFT JOIN strategies s ON i.strategy_id = s.id "
        "ORDER BY i.id"
    )
    ctx["existing_initiatives"] = [dict(r) for r in init_rows]

    # Existing epics (for deduplication in feature generation)
    epic_rows = await db.execute_fetchall(
        "SELECT e.*, i.name as initiative_name "
        "FROM epics e JOIN initiatives i ON e.initiative_id = i.id ORDER BY e.id"
    )
    ctx["existing_epics"] = [dict(r) for r in epic_rows]

    # Existing teams (for team recommendation)
    team_rows = await db.execute_fetchall("SELECT * FROM teams ORDER BY name")
    ctx["existing_teams"] = [dict(r) for r in team_rows]

    # External sources (fail gracefully)
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
        ctx["finnhub_data"] = await gather_finnhub_data(org_name, industry, competitor_names)
    except Exception:
        ctx["finnhub_data"] = {}

    return ctx


def _build_initiative_context_prompt(context: dict) -> str:
    """Build the full context prompt including Step 4+ data on top of the base context."""
    parts = [_build_context_prompt(context)]

    # Approved strategies with OKRs
    strategies = context.get("approved_strategies", [])
    if strategies:
        parts.append("\n--- APPROVED STRATEGIES WITH OKRs ---")
        for s in strategies:
            parts.append(f"\nStrategy [{s.get('layer', '?')}]: {s.get('name', '?')}")
            if s.get("description"):
                parts.append(f"  Description: {s['description']}")
            if s.get("risk_level"):
                parts.append(f"  Risk Level: {s['risk_level']}")
            if s.get("risks"):
                parts.append(f"  Risks: {s['risks']}")
            for okr in s.get("okrs", []):
                parts.append(f"  OKR: {okr.get('objective', '?')} (Horizon: {okr.get('time_horizon', '?')})")
                for kr in okr.get("key_results", []):
                    parts.append(
                        f"    KR: {kr.get('key_result', '?')} | "
                        f"{kr.get('metric', '?')}: {kr.get('current_value', 0)} -> {kr.get('target_value', 0)} {kr.get('unit', '')}"
                    )

    return "\n".join(parts)


async def generate_ai_initiatives(context: dict) -> list[dict] | None:
    """Use AI to generate initiatives with RICE scoring from strategic context. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a senior product strategist and portfolio manager. Given an organization's "
            "approved transformation strategies with OKRs, SWOT analysis, market context, and "
            "competitive landscape, generate digital initiatives with RICE prioritization.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "initiatives": [\n'
            "    {\n"
            '      "strategy_name": "Name of the parent strategy this initiative belongs to",\n'
            '      "strategy_layer": "business|digital|data|gen_ai",\n'
            '      "name": "Clear, actionable initiative name (max 80 chars)",\n'
            '      "description": "Detailed scope description with measurable outcomes",\n'
            '      "reach": 1-10,\n'
            '      "impact": 0.25,\n'
            '      "confidence": 0.5,\n'
            '      "effort": 1-10,\n'
            '      "value_score": 1-5,\n'
            '      "size_score": 1-5,\n'
            '      "risks": "Specific risk factors and mitigation strategies",\n'
            '      "dependencies": "Cross-initiative dependencies",\n'
            '      "impacted_segments": "Business segments or customer groups affected",\n'
            '      "roadmap_phase": "quick_win|strategic|long_term",\n'
            '      "rationale": "Why this initiative, why this RICE score"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Generate 1-2 initiatives per strategic OKR (total depends on strategy count)\n"
            "- RICE scores must reflect actual data:\n"
            "  - Reach: based on impacted user/customer base from org data (1-10)\n"
            "  - Impact: based on strategic importance from SWOT severity (must be one of: 0.25, 0.5, 1, 2, 3)\n"
            "  - Confidence: based on data availability and market validation (must be one of: 0.5, 0.8, 1.0)\n"
            "  - Effort: based on scope complexity and resource requirements (1-10)\n"
            "- Name must be specific and actionable, not a truncated OKR objective\n"
            "- Description must include scope, expected outcomes, and success criteria\n"
            "- risks must be specific (not 'may fail') — reference actual threats from SWOT\n"
            "- dependencies should reference other initiative names when cross-dependencies exist\n"
            "- impacted_segments should be specific business units or customer segments\n"
            "- roadmap_phase: quick_win = high impact + low effort, long_term = complex + foundational"
        )

        user_prompt = (
            "Based on the following comprehensive context, generate digital initiatives with RICE scoring:\n\n"
            + _build_initiative_context_prompt(context)
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

        initiatives = result.get("initiatives", [])
        if not initiatives:
            return None

        valid_impacts = {0.25, 0.5, 1, 2, 3}
        valid_confidences = {0.5, 0.8, 1.0}

        for init in initiatives:
            init.setdefault("strategy_name", "")
            init.setdefault("strategy_layer", "digital")
            init.setdefault("name", "Unnamed Initiative")
            init.setdefault("description", "")
            init.setdefault("risks", "")
            init.setdefault("dependencies", "")
            init.setdefault("impacted_segments", "")
            init.setdefault("roadmap_phase", "strategic")
            init.setdefault("rationale", "")

            # Clamp RICE values
            try:
                init["reach"] = max(1, min(10, int(init.get("reach", 3))))
            except (ValueError, TypeError):
                init["reach"] = 3
            try:
                impact = float(init.get("impact", 1))
                init["impact"] = min(valid_impacts, key=lambda x: abs(x - impact))
            except (ValueError, TypeError):
                init["impact"] = 1
            try:
                conf = float(init.get("confidence", 0.8))
                init["confidence"] = min(valid_confidences, key=lambda x: abs(x - conf))
            except (ValueError, TypeError):
                init["confidence"] = 0.8
            try:
                init["effort"] = max(1, min(10, int(init.get("effort", 3))))
            except (ValueError, TypeError):
                init["effort"] = 3
            try:
                init["value_score"] = max(1, min(5, int(init.get("value_score", 3))))
            except (ValueError, TypeError):
                init["value_score"] = 3
            try:
                init["size_score"] = max(1, min(5, int(init.get("size_score", 3))))
            except (ValueError, TypeError):
                init["size_score"] = 3

            if init["roadmap_phase"] not in ("quick_win", "strategic", "long_term"):
                init["roadmap_phase"] = "strategic"

        return initiatives

    except Exception:
        return None


async def generate_ai_epics(initiatives: list[dict], context: dict) -> dict | None:
    """Use AI to decompose initiatives into epics with product OKRs. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are an agile delivery lead and program manager. Given digital initiatives with "
            "their strategies, OKRs, and organizational context, decompose each initiative into "
            "well-scoped epics with realistic effort estimates.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "epics": [\n'
            "    {\n"
            '      "initiative_name": "Parent initiative name (must match exactly)",\n'
            '      "name": "Specific epic name describing a deliverable body of work",\n'
            '      "description": "Detailed description with scope boundaries and success criteria",\n'
            '      "value_score": 1-5,\n'
            '      "size_score": 1-5,\n'
            '      "effort_score": 1-5,\n'
            '      "estimated_effort_days": 10-120,\n'
            '      "risk_level": "low|medium|high|critical",\n'
            '      "risks": "Specific epic-level risks",\n'
            '      "dependencies_text": "Dependencies on other epics or external factors",\n'
            '      "recommended_team_type": "Type of team best suited",\n'
            '      "rationale": "Why this epic breakdown, why these scores"\n'
            "    }\n"
            "  ],\n"
            '  "product_okrs": [\n'
            "    {\n"
            '      "strategy_name": "Parent strategy name",\n'
            '      "product_name": "Digital product name",\n'
            '      "objective": "Product-team-actionable objective",\n'
            '      "key_results": [\n'
            "        {\n"
            '          "key_result": "Team-level measurable outcome",\n'
            '          "metric": "What to measure",\n'
            '          "current_value": 0,\n'
            '          "target_value": 15,\n'
            '          "unit": "%"\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            '  "cross_epic_dependencies": [\n'
            "    {\n"
            '      "epic_name": "Dependent epic",\n'
            '      "depends_on_epic_name": "Foundation epic",\n'
            '      "dependency_type": "blocks|relates_to",\n'
            '      "notes": "Why this dependency exists"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Generate 2-5 epics per initiative (varies by initiative complexity, NOT always 3)\n"
            "- Epic names must be specific to the initiative content, not generic templates\n"
            "- Descriptions should include acceptance criteria and definition of done\n"
            "- effort_score and estimated_effort_days should reflect actual complexity\n"
            "- Differentiate value_score/size_score/effort_score PER epic (not all same as parent)\n"
            "- recommended_team_type helps with team assignment\n"
            "- Product OKR objectives must be rewritten for product teams, not just appended product name\n"
            "- Product KR targets should be translated from strategic level to product delivery level\n"
            "- Cross-epic dependencies should capture both within-initiative and cross-initiative deps"
        )

        # Build initiative context for the prompt
        init_text = "\n--- INITIATIVES TO DECOMPOSE ---"
        for init in initiatives:
            init_text += f"\n\nInitiative: {init.get('name', '?')}"
            init_text += f"\n  Strategy: {init.get('strategy_name', '?')} [{init.get('strategy_layer', '?')}]"
            init_text += f"\n  Description: {init.get('description', '')}"
            init_text += f"\n  RICE: R={init.get('reach')}, I={init.get('impact')}, C={init.get('confidence')}, E={init.get('effort')}"
            if init.get("risks"):
                init_text += f"\n  Risks: {init['risks']}"
            if init.get("dependencies"):
                init_text += f"\n  Dependencies: {init['dependencies']}"
            if init.get("okrs"):
                for okr in init["okrs"]:
                    init_text += f"\n  OKR: {okr.get('objective', '?')}"
                    for kr in okr.get("key_results", []):
                        init_text += f"\n    KR: {kr.get('key_result', '?')}"

        user_prompt = (
            "Decompose these initiatives into epics with product OKRs:\n\n"
            + _build_initiative_context_prompt(context)
            + init_text
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
            max_tokens=6000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        epics = result.get("epics", [])
        if not epics:
            return None

        # Validate epics
        for epic in epics:
            epic.setdefault("initiative_name", "")
            epic.setdefault("name", "Unnamed Epic")
            epic.setdefault("description", "")
            epic.setdefault("risks", "")
            epic.setdefault("dependencies_text", "")
            epic.setdefault("recommended_team_type", "")
            epic.setdefault("rationale", "")
            for field in ["value_score", "size_score", "effort_score"]:
                try:
                    epic[field] = max(1, min(5, int(epic.get(field, 3))))
                except (ValueError, TypeError):
                    epic[field] = 3
            try:
                epic["estimated_effort_days"] = max(1, min(365, float(epic.get("estimated_effort_days", 30))))
            except (ValueError, TypeError):
                epic["estimated_effort_days"] = 30
            if epic.get("risk_level") not in ("low", "medium", "high", "critical"):
                epic["risk_level"] = "medium"

        # Validate product OKRs
        product_okrs = result.get("product_okrs", [])
        for pokr in product_okrs:
            pokr.setdefault("strategy_name", "")
            pokr.setdefault("product_name", "")
            pokr.setdefault("objective", "Product objective")
            pokr.setdefault("key_results", [])
            for kr in pokr["key_results"]:
                kr.setdefault("key_result", "Key result")
                kr.setdefault("metric", "")
                kr.setdefault("current_value", 0)
                kr.setdefault("target_value", 0)
                kr.setdefault("unit", "")

        # Validate dependencies
        cross_deps = result.get("cross_epic_dependencies", [])
        for dep in cross_deps:
            dep.setdefault("epic_name", "")
            dep.setdefault("depends_on_epic_name", "")
            if dep.get("dependency_type") not in ("blocks", "relates_to"):
                dep["dependency_type"] = "blocks"
            dep.setdefault("notes", "")

        return {
            "epics": epics,
            "product_okrs": product_okrs,
            "cross_epic_dependencies": cross_deps,
        }

    except Exception:
        return None


async def generate_ai_features(epics: list[dict], context: dict) -> dict | None:
    """Use AI to decompose epics into features with delivery OKRs. Returns None on failure."""
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a product owner and technical lead. Given epics with their initiatives, "
            "strategies, and organizational context, decompose each epic into deliverable features "
            "written as user stories with acceptance criteria.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "features": [\n'
            "    {\n"
            '      "epic_name": "Parent epic name (must match exactly)",\n'
            '      "name": "Feature name as user story title",\n'
            '      "description": "As a [role], I want [feature] so that [value]",\n'
            '      "acceptance_criteria": "- Given/When/Then criteria\\n- Criterion 2\\n- Criterion 3",\n'
            '      "value_score": 1-5,\n'
            '      "size_score": 1-5,\n'
            '      "effort_score": 1-5,\n'
            '      "estimated_effort": 1-40,\n'
            '      "risk_level": "low|medium|high|critical",\n'
            '      "risks": "Feature-level risks",\n'
            '      "dependencies_text": "Dependencies on other features",\n'
            '      "rationale": "Why this feature, why these scores"\n'
            "    }\n"
            "  ],\n"
            '  "delivery_okrs": [\n'
            "    {\n"
            '      "product_okr_objective": "Parent product OKR objective (must match)",\n'
            '      "team_name": "Team name (must match existing team)",\n'
            '      "objective": "Team-specific delivery objective (actionable)",\n'
            '      "key_results": [\n'
            "        {\n"
            '          "key_result": "Sprint-level measurable deliverable",\n'
            '          "metric": "What to measure",\n'
            '          "current_value": 0,\n'
            '          "target_value": 100,\n'
            '          "unit": "%"\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            '  "feature_dependencies": [\n'
            "    {\n"
            '      "feature_name": "Dependent feature",\n'
            '      "depends_on_feature_name": "Foundation feature",\n'
            '      "notes": "Why this dependency"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Generate 2-5 features per epic (varies by epic scope, NOT always 3)\n"
            "- Feature names should be concise user-story-style titles\n"
            "- Descriptions in 'As a [role], I want [X] so that [Y]' format\n"
            "- acceptance_criteria with concrete, testable criteria\n"
            "- estimated_effort in story points (1-40)\n"
            "- Differentiate scores PER feature (not all inherited from parent epic)\n"
            "- Delivery OKR objectives must be team-specific and actionable\n"
            "- Delivery KRs should be sprint/delivery-level metrics, not product-level copies\n"
            "- Feature dependencies should capture sequencing within an epic"
        )

        # Build epic context for the prompt
        epic_text = "\n--- EPICS TO DECOMPOSE ---"
        for epic in epics:
            epic_text += f"\n\nEpic: {epic.get('name', '?')}"
            epic_text += f"\n  Initiative: {epic.get('initiative_name', '?')}"
            epic_text += f"\n  Strategy: {epic.get('strategy_name', '?')} [{epic.get('strategy_layer', '?')}]"
            epic_text += f"\n  Description: {epic.get('description', '')}"
            epic_text += f"\n  Value: {epic.get('value_score', 3)}, Size: {epic.get('size_score', 3)}, Effort: {epic.get('effort_score', 3)}"
            if epic.get("risks"):
                epic_text += f"\n  Risks: {epic['risks']}"
            if epic.get("team_name"):
                epic_text += f"\n  Team: {epic['team_name']}"
            if epic.get("okr_objective"):
                epic_text += f"\n  Product OKR: {epic['okr_objective']}"

        # Add available teams for delivery OKR assignment
        teams = context.get("existing_teams", [])
        if teams:
            epic_text += "\n\n--- AVAILABLE TEAMS ---"
            for t in teams:
                epic_text += f"\n  Team: {t.get('name', '?')} (Capacity: {t.get('capacity', '?')})"

        user_prompt = (
            "Decompose these epics into features with delivery OKRs:\n\n"
            + _build_initiative_context_prompt(context)
            + epic_text
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
            max_tokens=6000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        features = result.get("features", [])
        if not features:
            return None

        # Validate features
        for feat in features:
            feat.setdefault("epic_name", "")
            feat.setdefault("name", "Unnamed Feature")
            feat.setdefault("description", "")
            feat.setdefault("acceptance_criteria", "")
            feat.setdefault("risks", "")
            feat.setdefault("dependencies_text", "")
            feat.setdefault("rationale", "")
            for field in ["value_score", "size_score", "effort_score"]:
                try:
                    feat[field] = max(1, min(5, int(feat.get(field, 3))))
                except (ValueError, TypeError):
                    feat[field] = 3
            try:
                feat["estimated_effort"] = max(1, min(40, int(feat.get("estimated_effort", 5))))
            except (ValueError, TypeError):
                feat["estimated_effort"] = 5
            if feat.get("risk_level") not in ("low", "medium", "high", "critical"):
                feat["risk_level"] = "medium"

        # Validate delivery OKRs
        delivery_okrs = result.get("delivery_okrs", [])
        for dokr in delivery_okrs:
            dokr.setdefault("product_okr_objective", "")
            dokr.setdefault("team_name", "")
            dokr.setdefault("objective", "Delivery objective")
            dokr.setdefault("key_results", [])
            for kr in dokr["key_results"]:
                kr.setdefault("key_result", "Key result")
                kr.setdefault("metric", "")
                kr.setdefault("current_value", 0)
                kr.setdefault("target_value", 0)
                kr.setdefault("unit", "")

        # Validate feature dependencies
        feat_deps = result.get("feature_dependencies", [])
        for dep in feat_deps:
            dep.setdefault("feature_name", "")
            dep.setdefault("depends_on_feature_name", "")
            dep.setdefault("notes", "")

        return {
            "features": features,
            "delivery_okrs": delivery_okrs,
            "feature_dependencies": feat_deps,
        }

    except Exception:
        return None


async def recommend_team_assignments(epics: list[dict], teams: list[dict]) -> dict | None:
    """Use AI to recommend team-to-epic assignments. Returns None on failure."""
    if not is_openai_available() or not teams:
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a delivery manager. Given epics with recommended team types and available teams, "
            "suggest optimal team-to-epic assignments.\n\n"
            "Return JSON:\n"
            "{\n"
            '  "assignments": [\n'
            "    {\n"
            '      "epic_name": "Epic name (must match exactly)",\n'
            '      "team_name": "Team name (must match exactly from available teams)"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Only assign to teams from the available list\n"
            "- Match based on team name keywords vs epic recommended_team_type\n"
            "- Distribute work somewhat evenly across teams\n"
            "- If no good match, assign to the team with the most capacity"
        )

        epic_text = "Epics:\n"
        for e in epics:
            epic_text += f"- {e.get('name', '?')} (recommended: {e.get('recommended_team_type', 'any')})\n"

        team_text = "\nAvailable Teams:\n"
        for t in teams:
            team_text += f"- {t.get('name', '?')} (capacity: {t.get('capacity', '?')})\n"

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": epic_text + team_text},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        assignments = result.get("assignments", [])
        for a in assignments:
            a.setdefault("epic_name", "")
            a.setdefault("team_name", "")

        return result

    except Exception:
        return None
