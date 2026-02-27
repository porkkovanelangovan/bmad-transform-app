"""
Step 6b: Target Operating Model & Governance (Enhancement #9).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available, ensure_str

router = APIRouter()
logger = logging.getLogger(__name__)

TOM_DIMENSIONS = ["people", "process", "technology", "data", "governance", "partnerships"]
GOVERNANCE_DECISIONS = ["strategic_investment", "technology_selection", "vendor_management",
                        "resource_allocation", "risk_management", "change_approval"]


@router.get("/operating-model")
async def get_operating_model(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM operating_model WHERE org_id = ? ORDER BY dimension", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/operating-model")
async def upsert_operating_model(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    dimension = data.get("dimension", "")

    existing = await db.execute_fetchone(
        "SELECT id FROM operating_model WHERE org_id = ? AND dimension = ?",
        [org_id, dimension],
    )
    if existing:
        await db.execute(
            "UPDATE operating_model SET current_state=?, target_state=?, gap=?, transformation_actions=? WHERE id=?",
            [data.get("current_state", ""), data.get("target_state", ""),
             data.get("gap", ""), data.get("transformation_actions", ""), existing["id"]],
        )
    else:
        await db.execute(
            "INSERT INTO operating_model (org_id, dimension, current_state, target_state, gap, transformation_actions) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [org_id, dimension, data.get("current_state", ""), data.get("target_state", ""),
             data.get("gap", ""), data.get("transformation_actions", "")],
        )
    await db.commit()
    return {"success": True}


@router.get("/governance")
async def get_governance(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM governance_model WHERE org_id = ? ORDER BY decision_type", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/governance")
async def upsert_governance(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    decision_type = data.get("decision_type", "")

    existing = await db.execute_fetchone(
        "SELECT id FROM governance_model WHERE org_id = ? AND decision_type = ?",
        [org_id, decision_type],
    )
    if existing:
        await db.execute(
            "UPDATE governance_model SET authority=?, escalation_path=?, cadence=? WHERE id=?",
            [data.get("authority", ""), data.get("escalation_path", ""), data.get("cadence", ""), existing["id"]],
        )
    else:
        await db.execute(
            "INSERT INTO governance_model (org_id, decision_type, authority, escalation_path, cadence) "
            "VALUES (?, ?, ?, ?, ?)",
            [org_id, decision_type, data.get("authority", ""), data.get("escalation_path", ""), data.get("cadence", "")],
        )
    await db.commit()
    return {"success": True}


@router.post("/operating-model/ai-generate")
async def ai_generate_tom(db=Depends(get_db)):
    """AI-generate target operating model and governance."""
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    org_dict = dict(org)

    if not is_openai_available():
        count = 0
        for dim in TOM_DIMENSIONS:
            existing = await db.execute_fetchone(
                "SELECT id FROM operating_model WHERE org_id = ? AND dimension = ?", [org_id, dim]
            )
            if not existing:
                await db.execute(
                    "INSERT INTO operating_model (org_id, dimension, current_state, target_state, gap, transformation_actions, ai_generated, ai_confidence) "
                    "VALUES (?, ?, 'Assessment pending', 'Target pending', 'Gap analysis pending', 'Actions TBD', 1, 50)",
                    [org_id, dim],
                )
                count += 1
        for dt in GOVERNANCE_DECISIONS:
            existing = await db.execute_fetchone(
                "SELECT id FROM governance_model WHERE org_id = ? AND decision_type = ?", [org_id, dt]
            )
            if not existing:
                await db.execute(
                    "INSERT INTO governance_model (org_id, decision_type, authority, escalation_path, cadence, ai_generated, ai_confidence) "
                    "VALUES (?, ?, 'TBD', 'TBD', 'Monthly', 1, 50)",
                    [org_id, dt],
                )
                count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    prompt = f"""Design the target operating model for {org_dict.get('name', 'the organization')}
(industry: {org_dict.get('industry', 'unknown')}).

For these TOM dimensions: {', '.join(TOM_DIMENSIONS)}
Provide: dimension, current_state, target_state, gap, transformation_actions, confidence (0-100)

For these governance decisions: {', '.join(GOVERNANCE_DECISIONS)}
Provide: decision_type, authority, escalation_path, cadence, confidence (0-100)

Return JSON: {{
  "operating_model": [{{"dimension": "...", "current_state": "...", "target_state": "...", "gap": "...", "transformation_actions": "...", "confidence": N}}],
  "governance": [{{"decision_type": "...", "authority": "...", "escalation_path": "...", "cadence": "...", "confidence": N}}]
}}"""

    result = await call_openai_json(prompt)
    count = 0
    if isinstance(result, dict):
        for item in result.get("operating_model", []):
            dim = item.get("dimension", "")
            if dim not in TOM_DIMENSIONS:
                continue
            existing = await db.execute_fetchone(
                "SELECT id FROM operating_model WHERE org_id = ? AND dimension = ?", [org_id, dim]
            )
            if existing:
                await db.execute(
                    "UPDATE operating_model SET current_state=?, target_state=?, gap=?, transformation_actions=?, ai_generated=1, ai_confidence=? WHERE id=?",
                    [ensure_str(item.get("current_state", "")), ensure_str(item.get("target_state", "")), ensure_str(item.get("gap", "")),
                     ensure_str(item.get("transformation_actions", "")), item.get("confidence", 70), existing["id"]],
                )
            else:
                await db.execute(
                    "INSERT INTO operating_model (org_id, dimension, current_state, target_state, gap, transformation_actions, ai_generated, ai_confidence) "
                    "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                    [org_id, dim, ensure_str(item.get("current_state", "")), ensure_str(item.get("target_state", "")),
                     ensure_str(item.get("gap", "")), ensure_str(item.get("transformation_actions", "")), item.get("confidence", 70)],
                )
            count += 1

        for item in result.get("governance", []):
            dt = item.get("decision_type", "")
            if dt not in GOVERNANCE_DECISIONS:
                continue
            existing = await db.execute_fetchone(
                "SELECT id FROM governance_model WHERE org_id = ? AND decision_type = ?", [org_id, dt]
            )
            if existing:
                await db.execute(
                    "UPDATE governance_model SET authority=?, escalation_path=?, cadence=?, ai_generated=1, ai_confidence=? WHERE id=?",
                    [ensure_str(item.get("authority", "")), ensure_str(item.get("escalation_path", "")),
                     ensure_str(item.get("cadence", "")), item.get("confidence", 70), existing["id"]],
                )
            else:
                await db.execute(
                    "INSERT INTO governance_model (org_id, decision_type, authority, escalation_path, cadence, ai_generated, ai_confidence) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?)",
                    [org_id, dt, ensure_str(item.get("authority", "")), ensure_str(item.get("escalation_path", "")),
                     ensure_str(item.get("cadence", "")), item.get("confidence", 70)],
                )
            count += 1
        await db.commit()

    return {"generated": count, "ai": True}
