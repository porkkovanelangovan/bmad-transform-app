"""
Step 2b: Customer Personas & Journeys (Enhancement #8).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available, extract_list

router = APIRouter()
logger = logging.getLogger(__name__)

JOURNEY_STAGES = ["awareness", "consideration", "acquisition", "onboarding", "usage", "retention", "advocacy"]


@router.get("/personas")
async def get_personas(db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return []
    rows = await db.execute_fetchall(
        "SELECT * FROM customer_personas WHERE org_id = ? ORDER BY name", [org["id"]]
    )
    return [dict(r) for r in rows]


@router.post("/personas")
async def create_persona(data: dict, db=Depends(get_db)):
    org = await db.execute_fetchone("SELECT id FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    await db.execute(
        "INSERT INTO customer_personas (org_id, name, demographics, needs, behaviors) VALUES (?, ?, ?, ?, ?)",
        [org["id"], data.get("name"), data.get("demographics", ""), data.get("needs", ""), data.get("behaviors", "")],
    )
    await db.commit()
    return {"success": True}


@router.delete("/personas/{item_id}")
async def delete_persona(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM customer_journeys WHERE persona_id = ?", [item_id])
    await db.execute("DELETE FROM customer_personas WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


@router.get("/journeys")
async def get_journeys(persona_id: int = None, db=Depends(get_db)):
    if persona_id:
        rows = await db.execute_fetchall(
            "SELECT * FROM customer_journeys WHERE persona_id = ? ORDER BY stage", [persona_id]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM customer_journeys ORDER BY persona_id, stage")
    return [dict(r) for r in rows]


@router.post("/journeys")
async def create_journey(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO customer_journeys (persona_id, stage, touchpoint, channel, emotion_score, pain_point, opportunity) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [data.get("persona_id"), data.get("stage"), data.get("touchpoint", ""),
         data.get("channel", ""), data.get("emotion_score", 0),
         data.get("pain_point", ""), data.get("opportunity", "")],
    )
    await db.commit()
    return {"success": True}


@router.delete("/journeys/{item_id}")
async def delete_journey(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM customer_journeys WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


@router.post("/journeys/ai-generate")
async def ai_generate_journeys(db=Depends(get_db)):
    """AI-generate customer personas and journey maps."""
    import traceback
    try:
        return await _ai_generate_journeys_impl(db)
    except Exception as e:
        logger.error("ai_generate_journeys failed: %s\n%s", e, traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}


async def _ai_generate_journeys_impl(db):
    org = await db.execute_fetchone("SELECT * FROM organization LIMIT 1")
    if not org:
        return {"error": "No organization found"}
    org_id = org["id"]
    org_dict = dict(org)

    if not is_openai_available():
        # Create 3 default personas with journeys
        personas_data = [
            ("Digital-First Customer", "Age 25-40, tech-savvy", "Speed, convenience, self-service", "Mobile-first, low branch usage"),
            ("Traditional Customer", "Age 50+, relationship-driven", "Trust, personal service, stability", "Branch visits, phone calls"),
            ("Small Business Owner", "Business owners, mixed digital", "Efficiency, cash flow management", "Multi-channel, time-constrained"),
        ]
        count = 0
        for name, demo, needs, behaviors in personas_data:
            cursor = await db.execute(
                "INSERT INTO customer_personas (org_id, name, demographics, needs, behaviors, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, ?, 1, 50)",
                [org_id, name, demo, needs, behaviors],
            )
            pid = cursor.lastrowid
            for stage in JOURNEY_STAGES:
                await db.execute(
                    "INSERT INTO customer_journeys (persona_id, stage, touchpoint, channel, emotion_score, pain_point, opportunity, ai_generated, ai_confidence) "
                    "VALUES (?, ?, 'TBD', 'digital', 0, 'Assessment pending', 'Analysis pending', 1, 50)",
                    [pid, stage],
                )
                count += 1
        await db.commit()
        return {"personas_generated": 3, "journeys_generated": count, "ai": False}

    from ai_research import call_openai_json
    prompt = f"""Create 3 customer personas and journey maps for {org_dict.get('name', 'the organization')}
(industry: {org_dict.get('industry', 'unknown')}).

For each persona, provide:
- name, demographics, needs, behaviors, confidence (0-100)

For each persona, create a journey with these stages: {', '.join(JOURNEY_STAGES)}
Each stage needs: touchpoint, channel, emotion_score (-2 to 2), pain_point, opportunity, confidence (0-100)

Return JSON: {{
  "personas": [{{"name": "...", "demographics": "...", "needs": "...", "behaviors": "...", "confidence": N,
    "journey": [{{"stage": "...", "touchpoint": "...", "channel": "...", "emotion_score": N, "pain_point": "...", "opportunity": "...", "confidence": N}}]
  }}]
}}"""

    result = await call_openai_json(prompt)
    personas_count = 0
    journeys_count = 0
    personas_list = extract_list(result, "personas")
    for p in personas_list:
        cursor = await db.execute(
            "INSERT INTO customer_personas (org_id, name, demographics, needs, behaviors, ai_generated, ai_confidence) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            [org_id, p.get("name", ""), p.get("demographics", ""), p.get("needs", ""),
             p.get("behaviors", ""), p.get("confidence", 70)],
        )
        pid = cursor.lastrowid
        personas_count += 1
        for j in p.get("journey", []):
            await db.execute(
                "INSERT INTO customer_journeys (persona_id, stage, touchpoint, channel, emotion_score, pain_point, opportunity, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
                [pid, j.get("stage", ""), j.get("touchpoint", ""), j.get("channel", ""),
                 j.get("emotion_score", 0), j.get("pain_point", ""), j.get("opportunity", ""),
                 j.get("confidence", 70)],
            )
            journeys_count += 1
    if personas_count:
        await db.commit()

    return {"personas_generated": personas_count, "journeys_generated": journeys_count, "ai": True}
