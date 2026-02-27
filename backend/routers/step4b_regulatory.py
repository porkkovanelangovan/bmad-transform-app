"""
Step 4b: Regulatory Impact Assessment (Enhancement #4).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available, extract_list, ensure_str

router = APIRouter()
logger = logging.getLogger(__name__)

REGULATIONS = [
    "occ_model_risk", "fair_lending", "bsa_aml", "basel_iii",
    "cfpb", "cyber_ffiec", "third_party_risk",
]


@router.get("/regulatory")
async def get_regulatory(strategy_id: int = None, db=Depends(get_db)):
    if strategy_id:
        rows = await db.execute_fetchall(
            "SELECT * FROM regulatory_impacts WHERE strategy_id = ? ORDER BY regulation", [strategy_id]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM regulatory_impacts ORDER BY regulation")
    return [dict(r) for r in rows]


@router.post("/regulatory")
async def create_regulatory(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO regulatory_impacts (strategy_id, regulation, impact_level, requirement, mitigation) "
        "VALUES (?, ?, ?, ?, ?)",
        [data.get("strategy_id"), data.get("regulation"), data.get("impact_level", "medium"),
         data.get("requirement", ""), data.get("mitigation", "")],
    )
    await db.commit()
    return {"success": True}


@router.put("/regulatory/{item_id}")
async def update_regulatory(item_id: int, data: dict, db=Depends(get_db)):
    await db.execute(
        "UPDATE regulatory_impacts SET impact_level=?, requirement=?, mitigation=? WHERE id=?",
        [data.get("impact_level", "medium"), data.get("requirement", ""), data.get("mitigation", ""), item_id],
    )
    await db.commit()
    return {"success": True}


@router.delete("/regulatory/{item_id}")
async def delete_regulatory(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM regulatory_impacts WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


@router.post("/regulatory/ai-generate")
async def ai_generate_regulatory(db=Depends(get_db)):
    """AI-generate regulatory impact assessment for strategies."""
    strategies = await db.execute_fetchall("SELECT * FROM strategies ORDER BY layer")
    if not strategies:
        return {"error": "No strategies found. Generate strategies first."}

    strategy_list = [dict(s) for s in strategies]

    if not is_openai_available():
        count = 0
        for s in strategy_list:
            for reg in REGULATIONS:
                existing = await db.execute_fetchone(
                    "SELECT id FROM regulatory_impacts WHERE strategy_id = ? AND regulation = ?",
                    [s["id"], reg],
                )
                if not existing:
                    await db.execute(
                        "INSERT INTO regulatory_impacts (strategy_id, regulation, impact_level, requirement, mitigation, ai_generated, ai_confidence) "
                        "VALUES (?, ?, 'medium', 'Assessment pending', 'Review required', 1, 50)",
                        [s["id"], reg],
                    )
                    count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    strategies_text = "\n".join([f"- {s['name']}: {s.get('description', '')}" for s in strategy_list])
    prompt = f"""Assess the regulatory impact of these transformation strategies in the banking/financial services context:

{strategies_text}

Regulations to assess: {', '.join(REGULATIONS)}

For each strategy-regulation pair where there is material impact, provide:
- strategy_id (integer)
- regulation (from list above)
- impact_level (high/medium/low)
- requirement (what the regulation requires)
- mitigation (how to address it)
- confidence (0-100)

Return JSON array. Only include pairs where impact_level is medium or high.
Strategy IDs: {json.dumps({s['name']: s['id'] for s in strategy_list})}"""

    result = await call_openai_json(prompt)
    count = 0
    for item in extract_list(result):
        sid = item.get("strategy_id")
        reg = item.get("regulation", "")
        if not sid or reg not in REGULATIONS:
            continue
        existing = await db.execute_fetchone(
            "SELECT id FROM regulatory_impacts WHERE strategy_id = ? AND regulation = ?",
            [sid, reg],
        )
        if existing:
            await db.execute(
                "UPDATE regulatory_impacts SET impact_level=?, requirement=?, mitigation=?, ai_generated=1, ai_confidence=? WHERE id=?",
                [ensure_str(item.get("impact_level", "medium")), ensure_str(item.get("requirement", "")),
                 ensure_str(item.get("mitigation", "")), item.get("confidence", 70), existing["id"]],
            )
        else:
            await db.execute(
                "INSERT INTO regulatory_impacts (strategy_id, regulation, impact_level, requirement, mitigation, ai_generated, ai_confidence) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                [sid, reg, ensure_str(item.get("impact_level", "medium")), ensure_str(item.get("requirement", "")),
                 ensure_str(item.get("mitigation", "")), item.get("confidence", 70)],
            )
        count += 1
    await db.commit()

    return {"generated": count, "ai": True}
