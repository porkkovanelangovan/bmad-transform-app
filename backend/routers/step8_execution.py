"""
Step 8: Execution Tracking Dashboard (Enhancement #5).
"""

import json
import logging

from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def execution_dashboard(db=Depends(get_db)):
    """Get comprehensive execution tracking data."""

    # Strategic OKR progress
    strategic_krs = await db.execute_fetchall(
        "SELECT skr.*, so.objective, s.name as strategy_name, s.layer "
        "FROM strategic_key_results skr "
        "JOIN strategic_okrs so ON skr.okr_id = so.id "
        "JOIN strategies s ON so.strategy_id = s.id "
        "ORDER BY s.layer, so.objective"
    )

    # Initiative progress
    initiatives = await db.execute_fetchall(
        "SELECT i.id, i.name, i.status, i.completion_pct, i.actual_start_date, i.actual_end_date, "
        "dp.name as product_name, s.name as strategy_name "
        "FROM initiatives i "
        "JOIN digital_products dp ON i.digital_product_id = dp.id "
        "LEFT JOIN strategies s ON i.strategy_id = s.id "
        "ORDER BY i.completion_pct DESC"
    )

    # Epic progress
    epics = await db.execute_fetchall(
        "SELECT e.id, e.name, e.status, e.completion_pct, e.actual_start_date, e.actual_end_date, "
        "i.name as initiative_name "
        "FROM epics e "
        "JOIN initiatives i ON e.initiative_id = i.id "
        "ORDER BY e.status, e.completion_pct DESC"
    )

    # Off-track items (below expected progress)
    off_track = []
    for init in initiatives:
        init_d = dict(init)
        if init_d.get("status") == "in_progress" and (init_d.get("completion_pct") or 0) < 25:
            off_track.append({"type": "initiative", "name": init_d["name"], "completion_pct": init_d.get("completion_pct", 0)})

    for ep in epics:
        ep_d = dict(ep)
        if ep_d.get("status") == "in_progress" and (ep_d.get("completion_pct") or 0) < 25:
            off_track.append({"type": "epic", "name": ep_d["name"], "completion_pct": ep_d.get("completion_pct", 0)})

    # Summary stats
    total_initiatives = len(initiatives)
    completed_initiatives = sum(1 for i in initiatives if dict(i).get("status") == "completed")
    total_epics = len(epics)
    completed_epics = sum(1 for e in epics if dict(e).get("status") == "done")

    return {
        "strategic_key_results": [dict(r) for r in strategic_krs],
        "initiatives": [dict(i) for i in initiatives],
        "epics": [dict(e) for e in epics],
        "off_track": off_track,
        "summary": {
            "total_initiatives": total_initiatives,
            "completed_initiatives": completed_initiatives,
            "total_epics": total_epics,
            "completed_epics": completed_epics,
            "initiative_completion_rate": round(completed_initiatives / max(total_initiatives, 1) * 100),
            "epic_completion_rate": round(completed_epics / max(total_epics, 1) * 100),
        },
    }


@router.put("/initiative/{item_id}/progress")
async def update_initiative_progress(item_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for col in ["completion_pct", "actual_start_date", "actual_end_date", "status"]:
        if col in data:
            fields.append(f"{col} = ?")
            values.append(data[col])
    if fields:
        values.append(item_id)
        await db.execute(f"UPDATE initiatives SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"success": True}


@router.put("/epic/{item_id}/progress")
async def update_epic_progress(item_id: int, data: dict, db=Depends(get_db)):
    fields = []
    values = []
    for col in ["completion_pct", "actual_start_date", "actual_end_date", "status"]:
        if col in data:
            fields.append(f"{col} = ?")
            values.append(data[col])
    if fields:
        values.append(item_id)
        await db.execute(f"UPDATE epics SET {', '.join(fields)} WHERE id = ?", values)
        await db.commit()
    return {"success": True}


@router.put("/kr/{item_id}/actual")
async def update_kr_actual(item_id: int, data: dict, db=Depends(get_db)):
    """Update actual value for a key result."""
    table = data.get("table", "strategic_key_results")
    if table not in ("strategic_key_results", "product_key_results", "delivery_key_results"):
        return {"error": "Invalid table"}
    await db.execute(
        f"UPDATE {table} SET actual_value = ?, last_updated = datetime('now') WHERE id = ?",
        [data.get("actual_value", 0), item_id],
    )
    await db.commit()
    return {"success": True}
