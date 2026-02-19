"""
AI Generate All — Orchestrator for end-to-end 7-step transformation generation.
Chains Steps 1→7 sequentially, with AI-powered generation for each step.
"""

import asyncio
import json
import logging
import traceback

from ai_research import is_openai_available

logger = logging.getLogger(__name__)

STEP_NAMES = {
    1: "Business Performance",
    2: "Value Streams",
    3: "SWOT & TOWS",
    4: "Strategy & OKRs",
    5: "Initiatives & RICE",
    6: "Epics & Teams",
    7: "Features & Roadmap",
}

GATE_NAMES = {
    1: "Business Performance Review",
    2: "Value Stream Analysis Review",
    3: "SWOT/TOWS Review",
    4: "Strategy & OKRs Review",
    5: "Initiatives Review",
    6: "Epics & Team Review",
    7: "Feature Backlog Review",
}


async def generate_all_steps(run_id: int, org_id: int, db):
    """Main orchestrator — runs Steps 1-7 sequentially, updates generation_runs progress."""
    from database import get_db_connection

    steps_completed = []
    steps_failed = []

    async def _update_run(status, step, message, error=None):
        conn = await get_db_connection()
        try:
            completed_at = "CURRENT_TIMESTAMP" if status in ("completed", "failed", "partial") else None
            if completed_at:
                await conn.execute(
                    "UPDATE generation_runs SET status=?, current_step=?, steps_completed=?, "
                    "steps_failed=?, message=?, error_message=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    [status, step, json.dumps(steps_completed), json.dumps(steps_failed),
                     message, error, run_id],
                )
            else:
                await conn.execute(
                    "UPDATE generation_runs SET status=?, current_step=?, steps_completed=?, "
                    "steps_failed=?, message=?, error_message=? WHERE id=?",
                    [status, step, json.dumps(steps_completed), json.dumps(steps_failed),
                     message, error, run_id],
                )
            await conn.commit()
        finally:
            await conn.close()

    try:
        await _update_run("running", 1, "Starting generation pipeline...")

        # --- Step 1: Business Performance ---
        await _update_run("running", 1, "Generating business units, revenue & metrics...")
        try:
            result = await _run_step1(org_id, db)
            steps_completed.append(1)
            await _update_run("running", 1, f"Step 1 complete: {result.get('summary', 'done')}")
        except Exception as e:
            logger.error("Step 1 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(1)
            await _update_run("running", 1, f"Step 1 failed: {e}", str(e))

        # --- Step 2: Value Streams ---
        await _update_run("running", 2, "Generating value streams...")
        try:
            result = await _run_step2(org_id, db)
            steps_completed.append(2)
            await _update_run("running", 2, f"Step 2 complete: {result.get('summary', 'done')}")
        except Exception as e:
            logger.error("Step 2 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(2)
            await _update_run("running", 2, f"Step 2 failed: {e}", str(e))

        # --- Step 3: SWOT & TOWS ---
        await _update_run("running", 3, "Generating SWOT analysis & TOWS actions...")
        try:
            bu_rows = await db.execute_fetchall("SELECT id FROM business_units LIMIT 1")
            if bu_rows:
                bu_id = bu_rows[0]["id"]
                from routers.step3_swot_tows import auto_generate as step3_auto
                result = await step3_auto({"business_unit_id": bu_id}, db)
                steps_completed.append(3)
                swot_count = result.get("swot_generated", 0)
                tows_count = result.get("tows_generated", 0)
                await _update_run("running", 3, f"Step 3 complete: {swot_count} SWOT, {tows_count} TOWS")
            else:
                steps_failed.append(3)
                await _update_run("running", 3, "Step 3 skipped: no business units")
        except Exception as e:
            logger.error("Step 3 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(3)
            await _update_run("running", 3, f"Step 3 failed: {e}", str(e))

        # --- Step 4: Strategy & OKRs ---
        await _update_run("running", 4, "Generating strategies & OKRs...")
        try:
            from routers.step4_strategy_okrs import auto_generate_strategies as step4_auto
            result = await step4_auto(db)
            # Auto-approve all strategies so Step 5 can use them
            await db.execute("UPDATE strategies SET approved = 1")
            await db.commit()
            steps_completed.append(4)
            s_count = result.get("strategies", 0)
            okr_count = result.get("okrs", 0)
            await _update_run("running", 4, f"Step 4 complete: {s_count} strategies, {okr_count} OKRs")
        except Exception as e:
            logger.error("Step 4 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(4)
            await _update_run("running", 4, f"Step 4 failed: {e}", str(e))

        # --- Step 5: Initiatives & RICE ---
        await _update_run("running", 5, "Generating initiatives with RICE scoring...")
        try:
            from routers.step5_initiatives import auto_generate_initiatives as step5_auto
            result = await step5_auto(db)
            steps_completed.append(5)
            init_count = result.get("initiatives", 0)
            await _update_run("running", 5, f"Step 5 complete: {init_count} initiatives")
        except Exception as e:
            logger.error("Step 5 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(5)
            await _update_run("running", 5, f"Step 5 failed: {e}", str(e))

        # --- Step 6: Teams + Epics ---
        await _update_run("running", 6, "Generating teams & epics...")
        try:
            # Create teams first (required for epic generation)
            await _generate_teams(db)
            from routers.step6_epics_teams import auto_generate as step6_auto
            result = await step6_auto(db)
            steps_completed.append(6)
            epic_count = len(result.get("epics", []))
            await _update_run("running", 6, f"Step 6 complete: {epic_count} epics")
        except Exception as e:
            logger.error("Step 6 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(6)
            await _update_run("running", 6, f"Step 6 failed: {e}", str(e))

        # --- Step 7: Features & Roadmap ---
        await _update_run("running", 7, "Generating features & delivery OKRs...")
        try:
            from routers.step7_features import auto_generate as step7_auto
            result = await step7_auto(db)
            steps_completed.append(7)
            feat_count = len(result.get("features", []))
            await _update_run("running", 7, f"Step 7 complete: {feat_count} features")
        except Exception as e:
            logger.error("Step 7 failed: %s\n%s", e, traceback.format_exc())
            steps_failed.append(7)
            await _update_run("running", 7, f"Step 7 failed: {e}", str(e))

        # --- Create Review Gates ---
        try:
            await _create_review_gates(db)
        except Exception as e:
            logger.error("Review gates creation failed: %s", e)

        # Final status
        if len(steps_completed) == 7:
            await _update_run("completed", 7, "All 7 steps generated successfully!")
        elif steps_failed:
            await _update_run("partial", max(steps_completed) if steps_completed else 0,
                              f"Completed {len(steps_completed)}/7 steps. Failed: {steps_failed}")
        else:
            await _update_run("failed", 0, "No steps completed")

    except Exception as e:
        logger.error("Orchestrator error: %s\n%s", e, traceback.format_exc())
        await _update_run("failed", 0, f"Orchestrator error: {e}", str(e))


# ─────────────────────────────────────────────────
# Step 1: AI-powered business data generation
# ─────────────────────────────────────────────────

async def _run_step1(org_id: int, db):
    """Generate Step 1 data. Tries API ingestion first, falls back to AI generation."""
    org = await db.execute_fetchone(
        "SELECT * FROM organization WHERE id = ?", [org_id]
    )
    if not org:
        raise ValueError("Organization not found")

    org = dict(org)
    org_name = org["name"]
    industry = org["industry"]

    # Try API ingestion for public companies
    try:
        from routers.step1_performance import _run_api_ingestion
        result = await _run_api_ingestion(org, db)
        if result.get("success") and result.get("summary", {}).get("ops_metrics", 0) > 0:
            return {"summary": f"API: {result['summary'].get('ops_metrics', 0)} metrics, {result['summary'].get('financials', 0)} revenue splits"}
    except Exception as e:
        logger.info("API ingestion not available, falling back to AI: %s", e)

    # Check if any data already exists
    bu_count = await db.execute_fetchone("SELECT COUNT(*) as c FROM business_units")
    if bu_count and bu_count["c"] > 0:
        return {"summary": "Existing data preserved"}

    # AI-powered generation for non-public companies
    if is_openai_available():
        try:
            return await _generate_step1_ai(org_name, industry, db)
        except Exception as e:
            logger.error("AI Step 1 generation failed: %s", e)

    # Template fallback
    return await _generate_step1_template(org_name, industry, db)


async def _generate_step1_ai(org_name: str, industry: str, db) -> dict:
    """Use OpenAI to generate synthetic business data for Step 1."""
    from openai import AsyncOpenAI

    prompt = f"""Generate realistic business data for "{org_name}" in the "{industry}" industry.

Return a JSON object with:
{{
  "business_units": [
    {{"name": "...", "description": "..."}}
  ],
  "revenue_splits": [
    {{"business_unit": "...", "dimension": "product", "dimension_value": "...", "revenue": 1000000, "period": "2023"}},
    {{"business_unit": "...", "dimension": "product", "dimension_value": "...", "revenue": 1100000, "period": "2024"}},
    {{"business_unit": "...", "dimension": "product", "dimension_value": "...", "revenue": 1200000, "period": "2025"}}
  ],
  "ops_metrics": [
    {{"business_unit": "...", "metric_name": "...", "metric_value": 0.15, "period": "TTM"}}
  ],
  "competitors": [
    {{"name": "...", "strengths": "...", "weaknesses": "..."}}
  ]
}}

Rules:
- Generate 3-5 business units relevant to the industry
- Revenue splits: 3 years of data per BU, with realistic growth
- Ops metrics: Include Net Profit Margin, Operating Margin, ROE, ROA, Revenue Growth (use decimal form, e.g. 0.15 for 15%)
- Competitors: 3-4 real or realistic competitors with strengths/weaknesses
- Use realistic revenue figures in dollars (not millions)
"""

    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=3000,
        temperature=0.7,
    )

    data = json.loads(response.choices[0].message.content)

    # Insert business units
    bu_map = {}
    for bu in data.get("business_units", []):
        name = bu.get("name", org_name)
        existing = await db.execute_fetchall("SELECT id FROM business_units WHERE name = ?", [name])
        if existing:
            bu_map[name] = existing[0]["id"]
        else:
            cursor = await db.execute(
                "INSERT INTO business_units (name, description) VALUES (?, ?)",
                [name, bu.get("description", "")],
            )
            bu_map[name] = cursor.lastrowid

    # Insert revenue splits
    rev_count = 0
    for rs in data.get("revenue_splits", []):
        bu_name = rs.get("business_unit", org_name)
        bu_id = bu_map.get(bu_name) or list(bu_map.values())[0] if bu_map else None
        if not bu_id:
            continue
        revenue = rs.get("revenue")
        if revenue is None:
            continue
        await db.execute(
            "INSERT INTO revenue_splits (business_unit_id, dimension, dimension_value, revenue, period) VALUES (?, ?, ?, ?, ?)",
            [bu_id, rs.get("dimension", "product"), rs.get("dimension_value", "Total Revenue"),
             float(revenue), rs.get("period", "2024")],
        )
        rev_count += 1

    # Insert ops metrics
    ops_count = 0
    for m in data.get("ops_metrics", []):
        bu_name = m.get("business_unit", org_name)
        bu_id = bu_map.get(bu_name) or list(bu_map.values())[0] if bu_map else None
        if not bu_id or not m.get("metric_name"):
            continue
        await db.execute(
            "INSERT INTO ops_efficiency (business_unit_id, metric_name, metric_value, period) VALUES (?, ?, ?, ?)",
            [bu_id, m["metric_name"], float(m.get("metric_value", 0)), m.get("period", "TTM")],
        )
        ops_count += 1

    # Insert competitors
    comp_count = 0
    for c in data.get("competitors", []):
        name = c.get("name")
        if not name:
            continue
        existing = await db.execute_fetchall("SELECT id FROM competitors WHERE name = ?", [name])
        if not existing:
            await db.execute(
                "INSERT INTO competitors (name, strengths, weaknesses, data_source) VALUES (?, ?, ?, ?)",
                [name, c.get("strengths"), c.get("weaknesses"), "AI-generated"],
            )
            comp_count += 1

    await db.commit()
    return {"summary": f"AI: {len(bu_map)} BUs, {rev_count} revenue, {ops_count} metrics, {comp_count} competitors"}


async def _generate_step1_template(org_name: str, industry: str, db) -> dict:
    """Template fallback for Step 1 generation."""
    # Create a single business unit
    cursor = await db.execute(
        "INSERT INTO business_units (name, description) VALUES (?, ?)",
        [org_name, f"Primary business unit for {org_name}"],
    )
    bu_id = cursor.lastrowid

    # Add template revenue
    for year, rev in [("2023", 50000000), ("2024", 55000000), ("2025", 60000000)]:
        await db.execute(
            "INSERT INTO revenue_splits (business_unit_id, dimension, dimension_value, revenue, period) VALUES (?, ?, ?, ?, ?)",
            [bu_id, "product", "Total Revenue", rev, year],
        )

    # Add template metrics
    for name, value in [("Net Profit Margin", 0.12), ("Operating Margin", 0.18),
                        ("Return on Equity (ROE)", 0.15), ("Return on Assets (ROA)", 0.08)]:
        await db.execute(
            "INSERT INTO ops_efficiency (business_unit_id, metric_name, metric_value, period) VALUES (?, ?, ?, ?)",
            [bu_id, name, value, "TTM"],
        )

    # Add template competitors
    for comp in [f"{industry} Leader Co", f"{industry} Challenger Inc"]:
        await db.execute(
            "INSERT INTO competitors (name, data_source) VALUES (?, ?)",
            [comp, "Template"],
        )

    await db.commit()
    return {"summary": "Template: 1 BU, 3 revenue, 4 metrics, 2 competitors"}


# ─────────────────────────────────────────────────
# Step 2: AI-powered value stream generation
# ─────────────────────────────────────────────────

async def _run_step2(org_id: int, db):
    """Generate value streams for Step 2."""
    org = await db.execute_fetchone("SELECT * FROM organization WHERE id = ?", [org_id])
    if not org:
        raise ValueError("Organization not found")

    org = dict(org)
    org_name = org["name"]
    industry = org["industry"]

    # Check if value streams already exist
    vs_count = await db.execute_fetchone("SELECT COUNT(*) as c FROM value_streams")
    if vs_count and vs_count["c"] > 0:
        return {"summary": "Existing value streams preserved"}

    # Get first business unit
    bu_rows = await db.execute_fetchall("SELECT id FROM business_units LIMIT 1")
    if not bu_rows:
        raise ValueError("No business units found — Step 1 must run first")
    bu_id = bu_rows[0]["id"]

    # Determine value stream names
    segment_names = await _determine_value_stream_names(org_name, industry)

    # Generate each value stream using pull-sources logic
    total_steps = 0
    for segment_name in segment_names:
        try:
            from routers.step2_value_streams import pull_from_sources

            sources = ["openai_research", "industry_benchmarks"] if is_openai_available() else ["industry_benchmarks"]
            result = await pull_from_sources(
                {"segment_name": segment_name, "business_unit_id": bu_id, "sources": sources},
                db,
            )
            total_steps += result.get("steps", 0)
        except Exception as e:
            logger.warning("Value stream '%s' generation failed, using template: %s", segment_name, e)
            # Fallback: use template generation
            try:
                from routers.step2_value_streams import generate_vs
                result = await generate_vs(
                    {"segment_name": segment_name, "business_unit_id": bu_id},
                    db,
                )
                total_steps += result.get("steps", 0)
            except Exception as e2:
                logger.error("Template generation also failed for '%s': %s", segment_name, e2)

    return {"summary": f"{len(segment_names)} value streams, {total_steps} steps"}


async def _determine_value_stream_names(org_name: str, industry: str) -> list[str]:
    """Use AI to determine industry-relevant value stream names."""
    if is_openai_available():
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        f'For "{org_name}" in the "{industry}" industry, suggest 3-4 key value stream names. '
                        'These should be end-to-end business processes (e.g., "Customer Onboarding", '
                        '"Order Fulfillment", "Product Development"). '
                        'Return JSON: {"value_streams": ["name1", "name2", "name3"]}'
                    ),
                }],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.7,
            )
            data = json.loads(response.choices[0].message.content)
            names = data.get("value_streams", [])
            if names and len(names) >= 2:
                return names[:4]
        except Exception as e:
            logger.warning("AI value stream name generation failed: %s", e)

    # Fallback: generic value streams
    return [
        "Customer Acquisition & Onboarding",
        "Service Delivery & Operations",
        "Product Development & Innovation",
    ]


# ─────────────────────────────────────────────────
# Step 6: Team generation
# ─────────────────────────────────────────────────

async def _generate_teams(db):
    """Create teams based on the strategies and initiatives context."""
    # Check if teams already exist
    team_count = await db.execute_fetchone("SELECT COUNT(*) as c FROM teams")
    if team_count and team_count["c"] > 0:
        return  # Teams already exist

    if is_openai_available():
        try:
            # Gather context for AI team generation
            strategies = await db.execute_fetchall("SELECT name, layer, description FROM strategies LIMIT 10")
            initiatives = await db.execute_fetchall("SELECT name, description FROM initiatives LIMIT 15")

            strat_text = "\n".join(f"- [{dict(s)['layer']}] {dict(s)['name']}" for s in strategies)
            init_text = "\n".join(f"- {dict(i)['name']}" for i in initiatives)

            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Based on these strategies and initiatives, recommend 4-6 cross-functional teams.\n\n"
                        f"Strategies:\n{strat_text}\n\nInitiatives:\n{init_text}\n\n"
                        'Return JSON: {"teams": [{"name": "Team Name", "capacity": 8}]}\n'
                        "Team names should be descriptive (e.g., 'Platform Engineering', 'Data & Analytics', 'Growth Marketing')."
                    ),
                }],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.7,
            )
            data = json.loads(response.choices[0].message.content)
            teams = data.get("teams", [])

            for team in teams:
                name = team.get("name")
                if not name:
                    continue
                existing = await db.execute_fetchall("SELECT id FROM teams WHERE name = ?", [name])
                if not existing:
                    await db.execute(
                        "INSERT INTO teams (name, capacity) VALUES (?, ?)",
                        [name, team.get("capacity", 8)],
                    )
            await db.commit()
            return
        except Exception as e:
            logger.warning("AI team generation failed, using templates: %s", e)

    # Template fallback
    default_teams = [
        ("Platform Engineering", 10),
        ("Data & Analytics", 8),
        ("Product Development", 8),
        ("Business Operations", 6),
        ("Customer Experience", 6),
    ]
    for name, capacity in default_teams:
        existing = await db.execute_fetchall("SELECT id FROM teams WHERE name = ?", [name])
        if not existing:
            await db.execute("INSERT INTO teams (name, capacity) VALUES (?, ?)", [name, capacity])
    await db.commit()


# ─────────────────────────────────────────────────
# Review Gates
# ─────────────────────────────────────────────────

async def _create_review_gates(db):
    """Create 7 review gates (one per step), all pending."""
    for step_num in range(1, 8):
        existing = await db.execute_fetchall(
            "SELECT id FROM review_gates WHERE step_number = ? AND gate_number = 1",
            [step_num],
        )
        if not existing:
            await db.execute(
                "INSERT INTO review_gates (step_number, gate_number, gate_name, status) VALUES (?, 1, ?, 'pending')",
                [step_num, GATE_NAMES.get(step_num, f"Step {step_num} Review")],
            )
    await db.commit()
