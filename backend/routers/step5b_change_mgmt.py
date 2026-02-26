"""
Step 5b: Change Management Plans (Enhancement #10).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db
from ai_research import is_openai_available

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/change-plans")
async def get_change_plans(initiative_id: int = None, db=Depends(get_db)):
    if initiative_id:
        rows = await db.execute_fetchall(
            "SELECT * FROM change_plans WHERE initiative_id = ? ORDER BY stakeholder_group", [initiative_id]
        )
    else:
        rows = await db.execute_fetchall("SELECT * FROM change_plans ORDER BY initiative_id, stakeholder_group")
    return [dict(r) for r in rows]


@router.post("/change-plans")
async def create_change_plan(data: dict, db=Depends(get_db)):
    await db.execute(
        "INSERT INTO change_plans (initiative_id, stakeholder_group, impact_level, communication_plan, "
        "training_needs, resistance_risks, adoption_metrics, wiifm) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [data.get("initiative_id"), data.get("stakeholder_group"), data.get("impact_level", "medium"),
         data.get("communication_plan", ""), data.get("training_needs", ""),
         data.get("resistance_risks", ""), data.get("adoption_metrics", ""), data.get("wiifm", "")],
    )
    await db.commit()
    return {"success": True}


@router.put("/change-plans/{item_id}")
async def update_change_plan(item_id: int, data: dict, db=Depends(get_db)):
    await db.execute(
        "UPDATE change_plans SET impact_level=?, communication_plan=?, training_needs=?, "
        "resistance_risks=?, adoption_metrics=?, wiifm=? WHERE id=?",
        [data.get("impact_level", "medium"), data.get("communication_plan", ""),
         data.get("training_needs", ""), data.get("resistance_risks", ""),
         data.get("adoption_metrics", ""), data.get("wiifm", ""), item_id],
    )
    await db.commit()
    return {"success": True}


@router.delete("/change-plans/{item_id}")
async def delete_change_plan(item_id: int, db=Depends(get_db)):
    await db.execute("DELETE FROM change_plans WHERE id = ?", [item_id])
    await db.commit()
    return {"deleted": True}


@router.post("/change-plans/ai-generate")
async def ai_generate_change_plans(data: dict, db=Depends(get_db)):
    """AI-generate change management plans for an initiative."""
    initiative_id = data.get("initiative_id")
    if not initiative_id:
        initiatives = await db.execute_fetchall("SELECT id, name FROM initiatives LIMIT 10")
        if not initiatives:
            return {"error": "No initiatives found"}
    else:
        initiatives = await db.execute_fetchall("SELECT id, name, description FROM initiatives WHERE id = ?", [initiative_id])

    init_list = [dict(i) for i in initiatives]
    stakeholder_groups = ["executive_leadership", "middle_management", "frontline_staff", "it_teams", "customers", "regulators"]

    if not is_openai_available():
        count = 0
        for init in init_list:
            for sg in stakeholder_groups:
                existing = await db.execute_fetchone(
                    "SELECT id FROM change_plans WHERE initiative_id = ? AND stakeholder_group = ?",
                    [init["id"], sg],
                )
                if not existing:
                    await db.execute(
                        "INSERT INTO change_plans (initiative_id, stakeholder_group, impact_level, communication_plan, "
                        "training_needs, resistance_risks, adoption_metrics, wiifm, ai_generated, ai_confidence) "
                        "VALUES (?, ?, 'medium', 'Plan pending', 'Training TBD', 'Risks TBD', 'Metrics TBD', 'Benefits TBD', 1, 50)",
                        [init["id"], sg],
                    )
                    count += 1
        await db.commit()
        return {"generated": count, "ai": False}

    from ai_research import call_openai_json
    count = 0
    for init in init_list:
        prompt = f"""Create change management plans for this transformation initiative:
Initiative: {init['name']}
Description: {init.get('description', '')}

For each stakeholder group ({', '.join(stakeholder_groups)}), provide:
- stakeholder_group
- impact_level (high/medium/low)
- communication_plan (how and when to communicate)
- training_needs (what training is needed)
- resistance_risks (likely resistance and how to handle)
- adoption_metrics (how to measure adoption)
- wiifm (What's In It For Me - the value proposition)
- confidence (0-100)

Return JSON array."""

        result = await call_openai_json(prompt)
        if isinstance(result, list):
            for item in result:
                sg = item.get("stakeholder_group", "")
                if sg not in stakeholder_groups:
                    continue
                existing = await db.execute_fetchone(
                    "SELECT id FROM change_plans WHERE initiative_id = ? AND stakeholder_group = ?",
                    [init["id"], sg],
                )
                if existing:
                    await db.execute(
                        "UPDATE change_plans SET impact_level=?, communication_plan=?, training_needs=?, "
                        "resistance_risks=?, adoption_metrics=?, wiifm=?, ai_generated=1, ai_confidence=? WHERE id=?",
                        [item.get("impact_level", "medium"), item.get("communication_plan", ""),
                         item.get("training_needs", ""), item.get("resistance_risks", ""),
                         item.get("adoption_metrics", ""), item.get("wiifm", ""),
                         item.get("confidence", 70), existing["id"]],
                    )
                else:
                    await db.execute(
                        "INSERT INTO change_plans (initiative_id, stakeholder_group, impact_level, communication_plan, "
                        "training_needs, resistance_risks, adoption_metrics, wiifm, ai_generated, ai_confidence) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                        [init["id"], sg, item.get("impact_level", "medium"), item.get("communication_plan", ""),
                         item.get("training_needs", ""), item.get("resistance_risks", ""),
                         item.get("adoption_metrics", ""), item.get("wiifm", ""), item.get("confidence", 70)],
                    )
                count += 1
    await db.commit()
    return {"generated": count, "ai": True}
