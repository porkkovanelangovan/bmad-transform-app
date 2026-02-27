"""
Step 0: Organizational Readiness Assessment & Digital Maturity Model (Enhancements #1, #3).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available, extract_list

router = APIRouter()
logger = logging.getLogger(__name__)

READINESS_DIMENSIONS = [
    "leadership_alignment", "digital_maturity", "change_capacity",
    "talent_readiness", "data_maturity", "tech_foundation",
    "culture_innovation", "governance",
]

MATURITY_DIMENSIONS = [
    "strategy", "customer", "technology", "operations",
    "organization", "culture", "data_analytics",
]


# ─── Readiness CRUD ─────────────────────────────────────────────────────────


@router.get("/readiness")
async def get_readiness(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM org_readiness WHERE org_id = ? ORDER BY dimension", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/readiness")
async def upsert_readiness(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    dimension = data.get("dimension", "")
    score = data.get("score", 3)
    evidence = data.get("evidence", "")

    existing = await db.execute_fetchone(
        "SELECT id FROM org_readiness WHERE org_id = ? AND dimension = ?",
        [org_id, dimension],
    )
    if existing:
        await db.execute(
            "UPDATE org_readiness SET score = ?, evidence = ? WHERE id = ?",
            [score, evidence, existing["id"]],
        )
    else:
        await db.execute(
            "INSERT INTO org_readiness (org_id, dimension, score, evidence) VALUES (?, ?, ?, ?)",
            [org_id, dimension, score, evidence],
        )
    await db.commit()
    return {"success": True}


@router.post("/readiness/ai-generate")
async def ai_generate_readiness(db=Depends(get_db)):
    """AI-generate readiness assessment for all 8 dimensions."""
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    org_dict = dict(org)

    if not is_openai_available():
        # Fallback: generate template scores
        for dim in READINESS_DIMENSIONS:
            existing = await db.execute_fetchone(
                "SELECT id FROM org_readiness WHERE org_id = ? AND dimension = ?",
                [org_id, dim],
            )
            if not existing:
                await db.execute(
                    "INSERT INTO org_readiness (org_id, dimension, score, evidence, ai_generated, ai_confidence) "
                    "VALUES (?, ?, 3, 'AI assessment pending - OpenAI not configured', 1, 50)",
                    [org_id, dim],
                )
        await db.commit()
        return {"generated": len(READINESS_DIMENSIONS), "ai": False}

    from ai_research import call_openai_json
    prompt = f"""Assess the organizational readiness of {org_dict.get('name', 'the organization')}
(industry: {org_dict.get('industry', 'unknown')}) across these 8 dimensions.

Dimensions: {', '.join(READINESS_DIMENSIONS)}

For each dimension, provide:
- score (1-5, where 1=not ready, 5=fully ready)
- evidence (brief justification)
- confidence (0-100)

Return JSON array: [{{"dimension": "...", "score": N, "evidence": "...", "confidence": N}}]"""

    result = await call_openai_json(prompt)
    items = extract_list(result)
    for item in items:
        dim = item.get("dimension", "")
        if dim not in READINESS_DIMENSIONS:
            continue
        existing = await db.execute_fetchone(
            "SELECT id FROM org_readiness WHERE org_id = ? AND dimension = ?",
            [org_id, dim],
        )
        if existing:
            await db.execute(
                "UPDATE org_readiness SET score=?, evidence=?, ai_generated=1, ai_confidence=? WHERE id=?",
                [item.get("score", 3), item.get("evidence", ""), item.get("confidence", 70), existing["id"]],
            )
        else:
            await db.execute(
                "INSERT INTO org_readiness (org_id, dimension, score, evidence, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                [org_id, dim, item.get("score", 3), item.get("evidence", ""), item.get("confidence", 70)],
            )
    if items:
        await db.commit()
    return {"generated": len(items), "ai": True}


# ─── Digital Maturity CRUD ───────────────────────────────────────────────────


@router.get("/maturity")
async def get_maturity(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM digital_maturity WHERE org_id = ? ORDER BY dimension", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/maturity")
async def upsert_maturity(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    dimension = data.get("dimension", "")
    current_level = data.get("current_level", 1)
    target_level = data.get("target_level", 3)
    evidence = data.get("evidence", "")

    existing = await db.execute_fetchone(
        "SELECT id FROM digital_maturity WHERE org_id = ? AND dimension = ?",
        [org_id, dimension],
    )
    if existing:
        await db.execute(
            "UPDATE digital_maturity SET current_level=?, target_level=?, evidence=? WHERE id=?",
            [current_level, target_level, evidence, existing["id"]],
        )
    else:
        await db.execute(
            "INSERT INTO digital_maturity (org_id, dimension, current_level, target_level, evidence) "
            "VALUES (?, ?, ?, ?, ?)",
            [org_id, dimension, current_level, target_level, evidence],
        )
    await db.commit()
    return {"success": True}


@router.post("/maturity/ai-generate")
async def ai_generate_maturity(db=Depends(get_db)):
    """AI-generate digital maturity assessment."""
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    org_dict = dict(org)

    if not is_openai_available():
        for dim in MATURITY_DIMENSIONS:
            existing = await db.execute_fetchone(
                "SELECT id FROM digital_maturity WHERE org_id = ? AND dimension = ?",
                [org_id, dim],
            )
            if not existing:
                await db.execute(
                    "INSERT INTO digital_maturity (org_id, dimension, current_level, target_level, evidence, gap_description, ai_generated, ai_confidence) "
                    "VALUES (?, ?, 2, 4, 'AI assessment pending', 'Gap analysis pending', 1, 50)",
                    [org_id, dim],
                )
        await db.commit()
        return {"generated": len(MATURITY_DIMENSIONS), "ai": False}

    from ai_research import call_openai_json
    prompt = f"""Assess the digital maturity of {org_dict.get('name', 'the organization')}
(industry: {org_dict.get('industry', 'unknown')}) across these 7 dimensions.

Dimensions: {', '.join(MATURITY_DIMENSIONS)}

For each, provide:
- current_level (1-5)
- target_level (1-5)
- evidence (brief)
- gap_description (what needs to change)
- confidence (0-100)

Return JSON array: [{{"dimension": "...", "current_level": N, "target_level": N, "evidence": "...", "gap_description": "...", "confidence": N}}]"""

    result = await call_openai_json(prompt)
    items = extract_list(result)
    for item in items:
        dim = item.get("dimension", "")
        if dim not in MATURITY_DIMENSIONS:
            continue
        existing = await db.execute_fetchone(
            "SELECT id FROM digital_maturity WHERE org_id = ? AND dimension = ?",
            [org_id, dim],
        )
        if existing:
            await db.execute(
                "UPDATE digital_maturity SET current_level=?, target_level=?, evidence=?, gap_description=?, ai_generated=1, ai_confidence=? WHERE id=?",
                [item.get("current_level", 2), item.get("target_level", 4), item.get("evidence", ""),
                 item.get("gap_description", ""), item.get("confidence", 70), existing["id"]],
            )
        else:
            await db.execute(
                "INSERT INTO digital_maturity (org_id, dimension, current_level, target_level, evidence, gap_description, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                [org_id, dim, item.get("current_level", 2), item.get("target_level", 4),
                 item.get("evidence", ""), item.get("gap_description", ""), item.get("confidence", 70)],
            )
    if items:
        await db.commit()
    return {"generated": len(items), "ai": True}
