import asyncio
import csv
import io
import json

from fastapi import APIRouter, Depends, UploadFile, File
from database import get_db
from openai_client import generate_value_stream
from source_gatherers import (
    gather_app_data,
    gather_erp_simulation,
    gather_industry_benchmarks,
    gather_finnhub_data,
    gather_web_search,
)
from ai_research import is_openai_available, research_value_stream

router = APIRouter()


# ──────────────────────────────────────────────
# Existing CRUD — Value Streams & Levers
# ──────────────────────────────────────────────

@router.get("/value-streams")
async def list_value_streams(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT vs.*, bu.name as business_unit_name FROM value_streams vs "
        "JOIN business_units bu ON vs.business_unit_id = bu.id"
    )
    return [dict(r) for r in rows]


@router.post("/value-streams")
async def create_value_stream(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO value_streams (business_unit_id, name, description) VALUES (?, ?, ?)",
        (data["business_unit_id"], data["name"], data.get("description")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.delete("/value-streams/{vs_id}")
async def delete_value_stream(vs_id: int, db=Depends(get_db)):
    # Cascade delete child data
    await db.execute("DELETE FROM value_stream_benchmarks WHERE value_stream_id = ?", (vs_id,))
    await db.execute("DELETE FROM value_stream_metrics WHERE value_stream_id = ?", (vs_id,))
    await db.execute("DELETE FROM value_stream_steps WHERE value_stream_id = ?", (vs_id,))
    await db.execute("DELETE FROM value_stream_levers WHERE value_stream_id = ?", (vs_id,))
    await db.execute("DELETE FROM value_streams WHERE id = ?", (vs_id,))
    await db.commit()
    return {"deleted": True}


# --- Levers ---

@router.get("/levers")
async def list_levers(value_stream_id: int = None, db=Depends(get_db)):
    if value_stream_id:
        rows = await db.execute_fetchall(
            "SELECT vl.*, vs.name as value_stream_name FROM value_stream_levers vl "
            "JOIN value_streams vs ON vl.value_stream_id = vs.id WHERE vl.value_stream_id = ?",
            (value_stream_id,),
        )
    else:
        rows = await db.execute_fetchall(
            "SELECT vl.*, vs.name as value_stream_name FROM value_stream_levers vl "
            "JOIN value_streams vs ON vl.value_stream_id = vs.id"
        )
    return [dict(r) for r in rows]


@router.post("/levers")
async def create_lever(data: dict, db=Depends(get_db)):
    cursor = await db.execute(
        "INSERT INTO value_stream_levers (value_stream_id, lever_type, opportunity, current_state, target_state, impact_estimate) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (data["value_stream_id"], data["lever_type"], data["opportunity"],
         data.get("current_state"), data.get("target_state"), data.get("impact_estimate")),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


# ──────────────────────────────────────────────
# NEW — AI Generation
# ──────────────────────────────────────────────

@router.post("/generate")
async def generate_vs(data: dict, db=Depends(get_db)):
    """Generate a value stream from templates, store steps + metrics + benchmarks."""
    segment_name = data["segment_name"]
    business_unit_id = data["business_unit_id"]

    # Fetch org info for context
    org_row = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    org = dict(org_row[0]) if org_row else {}
    org_name = org.get("name", "the organization")
    industry = org.get("industry", "general")
    competitors = [c for c in [org.get("competitor_1_name"), org.get("competitor_2_name")] if c]

    # Create the value stream record
    cursor = await db.execute(
        "INSERT INTO value_streams (business_unit_id, name, description) VALUES (?, ?, ?)",
        (business_unit_id, segment_name, f"Template-generated value stream for {segment_name}"),
    )
    vs_id = cursor.lastrowid

    # Generate from templates
    result = generate_value_stream(segment_name, industry, org_name, competitors)

    # Store steps
    for step in result.get("steps", []):
        pt = step.get("process_time_hours", 0) or 0
        wt = step.get("wait_time_hours", 0) or 0
        await db.execute(
            "INSERT INTO value_stream_steps "
            "(value_stream_id, step_order, step_name, description, step_type, "
            "process_time_hours, wait_time_hours, lead_time_hours, resources, is_bottleneck, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                vs_id,
                step.get("step_order", 0),
                step.get("step_name", "Step"),
                step.get("description"),
                step.get("step_type", "process"),
                pt,
                wt,
                pt + wt,
                step.get("resources"),
                1 if step.get("is_bottleneck") else 0,
                step.get("notes"),
            ),
        )

    # Store metrics
    metrics = result.get("overall_metrics", {})
    await db.execute(
        "INSERT INTO value_stream_metrics "
        "(value_stream_id, total_lead_time_hours, total_process_time_hours, total_wait_time_hours, "
        "flow_efficiency, bottleneck_step, bottleneck_reason, data_source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'template')",
        (
            vs_id,
            metrics.get("total_lead_time_hours", 0),
            metrics.get("total_process_time_hours", 0),
            metrics.get("total_wait_time_hours", 0),
            metrics.get("flow_efficiency", 0),
            metrics.get("bottleneck_step"),
            metrics.get("bottleneck_reason"),
        ),
    )

    # Store benchmarks
    for bm in result.get("competitor_benchmarks", []):
        await db.execute(
            "INSERT INTO value_stream_benchmarks "
            "(value_stream_id, competitor_name, total_lead_time_hours, total_process_time_hours, "
            "flow_efficiency, bottleneck_step, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                vs_id,
                bm.get("competitor_name", "Competitor"),
                bm.get("total_lead_time_hours"),
                bm.get("total_process_time_hours"),
                bm.get("flow_efficiency"),
                bm.get("bottleneck_step"),
                bm.get("notes"),
            ),
        )

    await db.commit()
    return {"id": vs_id, "steps": len(result.get("steps", [])), "benchmarks": len(result.get("competitor_benchmarks", []))}


# ──────────────────────────────────────────────
# NEW — File Upload (CSV / JSON)
# ──────────────────────────────────────────────

@router.post("/upload")
async def upload_vs(business_unit_id: int, file: UploadFile = File(...), db=Depends(get_db)):
    """Upload a CSV or JSON file with value stream step data."""
    content = await file.read()
    text = content.decode("utf-8")
    steps = []

    if file.filename.endswith(".json"):
        parsed = json.loads(text)
        steps = parsed if isinstance(parsed, list) else parsed.get("steps", [])
    elif file.filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            steps.append({
                "step_order": int(row.get("step_order", 0)),
                "step_name": row.get("step_name", "Step"),
                "description": row.get("description", ""),
                "step_type": row.get("step_type", "process"),
                "process_time_hours": float(row.get("process_time_hours", 0)),
                "wait_time_hours": float(row.get("wait_time_hours", 0)),
                "resources": row.get("resources", ""),
                "is_bottleneck": row.get("is_bottleneck", "").lower() in ("1", "true", "yes"),
                "notes": row.get("notes", ""),
            })
    else:
        return {"error": "Unsupported file type. Use .csv or .json"}

    if not steps:
        return {"error": "No steps found in file"}

    # Derive name from filename
    vs_name = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

    cursor = await db.execute(
        "INSERT INTO value_streams (business_unit_id, name, description) VALUES (?, ?, ?)",
        (business_unit_id, vs_name, "Uploaded from file"),
    )
    vs_id = cursor.lastrowid

    for step in steps:
        pt = float(step.get("process_time_hours", 0) or 0)
        wt = float(step.get("wait_time_hours", 0) or 0)
        await db.execute(
            "INSERT INTO value_stream_steps "
            "(value_stream_id, step_order, step_name, description, step_type, "
            "process_time_hours, wait_time_hours, lead_time_hours, resources, is_bottleneck, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                vs_id,
                step.get("step_order", 0),
                step.get("step_name", "Step"),
                step.get("description"),
                step.get("step_type", "process"),
                pt,
                wt,
                pt + wt,
                step.get("resources"),
                1 if step.get("is_bottleneck") else 0,
                step.get("notes"),
            ),
        )

    # Compute and store metrics
    await _recalculate_metrics(vs_id, db, data_source="uploaded")
    await db.commit()
    return {"id": vs_id, "steps": len(steps)}


# ──────────────────────────────────────────────
# NEW — Pull from Sources
# ──────────────────────────────────────────────

VALID_SOURCES = {"app_data", "erp_simulation", "industry_benchmarks", "finnhub", "web_search", "openai_research"}

GATHERER_MAP = {
    "app_data": lambda db, segment, industry, org_name, competitors: gather_app_data(db),
    "erp_simulation": lambda db, segment, industry, org_name, competitors: gather_erp_simulation(segment, industry),
    "industry_benchmarks": lambda db, segment, industry, org_name, competitors: gather_industry_benchmarks(segment, industry),
    "finnhub": lambda db, segment, industry, org_name, competitors: gather_finnhub_data(org_name, industry, competitors),
    "web_search": lambda db, segment, industry, org_name, competitors: gather_web_search(segment, industry),
}


@router.post("/pull-sources")
async def pull_from_sources(data: dict, db=Depends(get_db)):
    """Pull data from multiple sources and synthesize into a value stream."""
    segment_name = data.get("segment_name", "").strip()
    business_unit_id = data.get("business_unit_id")
    sources = data.get("sources", [])

    if not segment_name:
        return {"error": "segment_name is required"}
    if not business_unit_id:
        return {"error": "business_unit_id is required"}

    # Validate sources
    invalid = set(sources) - VALID_SOURCES
    if invalid:
        return {"error": f"Invalid sources: {', '.join(invalid)}. Valid: {', '.join(sorted(VALID_SOURCES))}"}
    if not sources:
        return {"error": "At least one source is required"}

    # Fetch org info
    org_row = await db.execute_fetchall("SELECT * FROM organization LIMIT 1")
    org = dict(org_row[0]) if org_row else {}
    org_name = org.get("name", "the organization")
    industry = org.get("industry", "general")
    competitors = [c for c in [org.get("competitor_1_name"), org.get("competitor_2_name")] if c]

    # Run all selected non-OpenAI gatherers concurrently
    non_openai_sources = [s for s in sources if s != "openai_research"]
    gather_tasks = []
    gather_source_names = []
    for src in non_openai_sources:
        if src in GATHERER_MAP:
            gather_tasks.append(GATHERER_MAP[src](db, segment_name, industry, org_name, competitors))
            gather_source_names.append(src)

    gathered_results = await asyncio.gather(*gather_tasks, return_exceptions=True)

    # Collect results, tracking status per source
    sources_used = {}
    gathered_data = []
    finnhub_data = {}
    for src_name, result in zip(gather_source_names, gathered_results):
        if isinstance(result, Exception) or not result:
            sources_used[src_name] = "error"
        else:
            sources_used[src_name] = "ok"
            gathered_data.append(result)
            if src_name == "finnhub":
                finnhub_data = result

    # Determine synthesis method
    synthesis_method = "template"
    result = None

    if "openai_research" in sources and is_openai_available():
        result = await research_value_stream(
            segment_name=segment_name,
            industry=industry,
            org_name=org_name,
            org_context=org,
            competitor_data=finnhub_data,
            sources_context=gathered_data,
        )
        if result:
            synthesis_method = "ai_generated"
            sources_used["openai_research"] = "ok"
        else:
            sources_used["openai_research"] = "error"
    elif "openai_research" in sources:
        sources_used["openai_research"] = "unavailable"

    # Fallback to enhanced template generation
    if not result:
        result = _enhanced_template_generation(segment_name, industry, org_name, competitors, finnhub_data, gathered_data)
        synthesis_method = "template"

    # Create the value stream record
    cursor = await db.execute(
        "INSERT INTO value_streams (business_unit_id, name, description) VALUES (?, ?, ?)",
        (business_unit_id, segment_name, f"Generated via pull-sources ({synthesis_method})"),
    )
    vs_id = cursor.lastrowid

    data_source = synthesis_method

    # Store steps
    for step in result.get("steps", []):
        pt = step.get("process_time_hours", 0) or 0
        wt = step.get("wait_time_hours", 0) or 0
        await db.execute(
            "INSERT INTO value_stream_steps "
            "(value_stream_id, step_order, step_name, description, step_type, "
            "process_time_hours, wait_time_hours, lead_time_hours, resources, is_bottleneck, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                vs_id,
                step.get("step_order", 0),
                step.get("step_name", "Step"),
                step.get("description"),
                step.get("step_type", "process"),
                pt,
                wt,
                pt + wt,
                step.get("resources"),
                1 if step.get("is_bottleneck") else 0,
                step.get("notes"),
            ),
        )

    # Store metrics
    metrics = result.get("overall_metrics", {})
    await db.execute(
        "INSERT INTO value_stream_metrics "
        "(value_stream_id, total_lead_time_hours, total_process_time_hours, total_wait_time_hours, "
        "flow_efficiency, bottleneck_step, bottleneck_reason, data_source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            vs_id,
            metrics.get("total_lead_time_hours", 0),
            metrics.get("total_process_time_hours", 0),
            metrics.get("total_wait_time_hours", 0),
            metrics.get("flow_efficiency", 0),
            metrics.get("bottleneck_step"),
            metrics.get("bottleneck_reason"),
            data_source,
        ),
    )

    # Store benchmarks
    benchmarks = result.get("competitor_benchmarks", [])
    for bm in benchmarks:
        await db.execute(
            "INSERT INTO value_stream_benchmarks "
            "(value_stream_id, competitor_name, total_lead_time_hours, total_process_time_hours, "
            "flow_efficiency, bottleneck_step, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                vs_id,
                bm.get("competitor_name", "Competitor"),
                bm.get("total_lead_time_hours"),
                bm.get("total_process_time_hours"),
                bm.get("flow_efficiency"),
                bm.get("bottleneck_step"),
                bm.get("notes"),
            ),
        )

    await db.commit()

    return {
        "id": vs_id,
        "steps": len(result.get("steps", [])),
        "benchmarks": len(benchmarks),
        "sources_used": sources_used,
        "synthesis_method": synthesis_method,
    }


def _enhanced_template_generation(
    segment_name: str,
    industry: str,
    org_name: str,
    competitors: list[str],
    finnhub_data: dict,
    gathered_data: list[dict],
) -> dict:
    """Enriched template generation using gathered source data."""
    # Enrich competitor names from Finnhub data
    enriched_competitors = list(competitors)
    if finnhub_data and finnhub_data.get("competitor_names"):
        for name in finnhub_data["competitor_names"]:
            if name not in enriched_competitors:
                enriched_competitors.append(name)
    # Ensure at least 2 competitor names for benchmarks
    if len(enriched_competitors) < 2:
        enriched_competitors.extend(["Industry Leader", "Market Average"])
    enriched_competitors = enriched_competitors[:4]

    # Generate base value stream from templates
    result = generate_value_stream(segment_name, industry, org_name, enriched_competitors)

    # Enrich steps with ERP system source notes if available
    erp_data = next((d for d in gathered_data if d.get("source") == "erp_simulation"), None)
    if erp_data and erp_data.get("steps"):
        erp_steps = {s["step_name"]: s for s in erp_data["steps"]}
        for step in result.get("steps", []):
            erp_info = erp_steps.get(step["step_name"])
            if erp_info:
                existing_notes = step.get("notes", "") or ""
                erp_note = f" [ERP: {erp_info['system_source']}, Dept: {erp_info['department_code']}, Vol: {erp_info['monthly_volume']}/mo]"
                step["notes"] = existing_notes + erp_note

    return result


# ──────────────────────────────────────────────
# NEW — Detail view
# ──────────────────────────────────────────────

@router.get("/value-streams/{vs_id}/detail")
async def value_stream_detail(vs_id: int, db=Depends(get_db)):
    """Full detail: value stream + steps + metrics + benchmarks."""
    vs_rows = await db.execute_fetchall(
        "SELECT vs.*, bu.name as business_unit_name FROM value_streams vs "
        "JOIN business_units bu ON vs.business_unit_id = bu.id WHERE vs.id = ?",
        (vs_id,),
    )
    if not vs_rows:
        return {"error": "Value stream not found"}
    vs = dict(vs_rows[0])

    steps = [dict(r) for r in await db.execute_fetchall(
        "SELECT * FROM value_stream_steps WHERE value_stream_id = ? ORDER BY step_order",
        (vs_id,),
    )]

    metrics_rows = await db.execute_fetchall(
        "SELECT * FROM value_stream_metrics WHERE value_stream_id = ?", (vs_id,),
    )
    metrics = dict(metrics_rows[0]) if metrics_rows else None

    benchmarks = [dict(r) for r in await db.execute_fetchall(
        "SELECT * FROM value_stream_benchmarks WHERE value_stream_id = ?", (vs_id,),
    )]

    return {"value_stream": vs, "steps": steps, "metrics": metrics, "benchmarks": benchmarks}


# ──────────────────────────────────────────────
# NEW — Step CRUD
# ──────────────────────────────────────────────

@router.post("/value-streams/{vs_id}/steps")
async def add_step(vs_id: int, data: dict, db=Depends(get_db)):
    pt = float(data.get("process_time_hours", 0) or 0)
    wt = float(data.get("wait_time_hours", 0) or 0)
    cursor = await db.execute(
        "INSERT INTO value_stream_steps "
        "(value_stream_id, step_order, step_name, description, step_type, "
        "process_time_hours, wait_time_hours, lead_time_hours, resources, is_bottleneck, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            vs_id,
            data.get("step_order", 99),
            data.get("step_name", "New Step"),
            data.get("description"),
            data.get("step_type", "process"),
            pt,
            wt,
            pt + wt,
            data.get("resources"),
            1 if data.get("is_bottleneck") else 0,
            data.get("notes"),
        ),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/value-streams/{vs_id}/steps/{step_id}")
async def update_step(vs_id: int, step_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for col in [
        "step_order", "step_name", "description", "step_type",
        "process_time_hours", "wait_time_hours", "resources", "is_bottleneck", "notes",
    ]:
        if col in data:
            fields.append(f"{col} = ?")
            val = data[col]
            if col == "is_bottleneck":
                val = 1 if val else 0
            values.append(val)

    if not fields:
        return {"error": "No fields to update"}

    # Recalculate lead_time if time fields changed
    if "process_time_hours" in data or "wait_time_hours" in data:
        # Fetch current values for any missing field
        row = await db.execute_fetchall("SELECT process_time_hours, wait_time_hours FROM value_stream_steps WHERE id = ?", (step_id,))
        if row:
            cur = dict(row[0])
            pt = float(data.get("process_time_hours", cur["process_time_hours"]) or 0)
            wt = float(data.get("wait_time_hours", cur["wait_time_hours"]) or 0)
            fields.append("lead_time_hours = ?")
            values.append(pt + wt)

    values.append(step_id)
    await db.execute(f"UPDATE value_stream_steps SET {', '.join(fields)} WHERE id = ?", values)
    await db.commit()
    return {"updated": True}


@router.delete("/value-streams/{vs_id}/steps/{step_id}")
async def delete_step(vs_id: int, step_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM value_stream_steps WHERE id = ? AND value_stream_id = ?", (step_id, vs_id))
    await db.commit()
    return {"deleted": True}


# ──────────────────────────────────────────────
# NEW — Recalculate metrics
# ──────────────────────────────────────────────

@router.post("/value-streams/{vs_id}/recalculate")
async def recalculate(vs_id: int, db=Depends(get_db)):
    result = await _recalculate_metrics(vs_id, db)
    await db.commit()
    return result


async def _recalculate_metrics(vs_id: int, db, data_source: str = "manual") -> dict:
    """Recompute summary metrics from steps."""
    steps = [dict(r) for r in await db.execute_fetchall(
        "SELECT * FROM value_stream_steps WHERE value_stream_id = ? ORDER BY step_order", (vs_id,),
    )]

    total_pt = sum(s.get("process_time_hours", 0) or 0 for s in steps)
    total_wt = sum(s.get("wait_time_hours", 0) or 0 for s in steps)
    total_lt = total_pt + total_wt
    flow_eff = (total_pt / total_lt * 100) if total_lt > 0 else 0

    # Find bottleneck: step with highest lead_time
    bottleneck = max(steps, key=lambda s: (s.get("lead_time_hours", 0) or 0)) if steps else {}
    bn_name = bottleneck.get("step_name")
    bn_reason = f"Highest lead time ({bottleneck.get('lead_time_hours', 0):.1f}h)" if bottleneck else None

    # Also check explicit bottleneck flags
    flagged = [s for s in steps if s.get("is_bottleneck")]
    if flagged:
        bn_name = flagged[0]["step_name"]
        bn_reason = f"Flagged as bottleneck (lead time: {flagged[0].get('lead_time_hours', 0):.1f}h)"

    # Upsert metrics
    existing = await db.execute_fetchall(
        "SELECT id FROM value_stream_metrics WHERE value_stream_id = ?", (vs_id,),
    )
    if existing:
        await db.execute(
            "UPDATE value_stream_metrics SET total_lead_time_hours=?, total_process_time_hours=?, "
            "total_wait_time_hours=?, flow_efficiency=?, bottleneck_step=?, bottleneck_reason=?, data_source=? "
            "WHERE value_stream_id = ?",
            (total_lt, total_pt, total_wt, round(flow_eff, 1), bn_name, bn_reason, data_source, vs_id),
        )
    else:
        await db.execute(
            "INSERT INTO value_stream_metrics "
            "(value_stream_id, total_lead_time_hours, total_process_time_hours, total_wait_time_hours, "
            "flow_efficiency, bottleneck_step, bottleneck_reason, data_source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (vs_id, total_lt, total_pt, total_wt, round(flow_eff, 1), bn_name, bn_reason, data_source),
        )

    return {
        "total_lead_time_hours": round(total_lt, 1),
        "total_process_time_hours": round(total_pt, 1),
        "total_wait_time_hours": round(total_wt, 1),
        "flow_efficiency": round(flow_eff, 1),
        "bottleneck_step": bn_name,
    }
