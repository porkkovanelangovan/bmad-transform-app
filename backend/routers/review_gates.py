from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()


@router.get("/")
async def list_gates(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM review_gates ORDER BY step_number, gate_number"
    )
    return [dict(r) for r in rows]


@router.get("/step/{step_number}")
async def get_step_gates(step_number: int, db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT * FROM review_gates WHERE step_number = ? ORDER BY gate_number",
        (step_number,),
    )
    return [dict(r) for r in rows]


@router.post("/")
async def create_gate(data: dict, db=Depends(get_db)):
    status = data.get("status", "pending")
    reviewer = data.get("reviewer")
    review_notes = data.get("review_notes")
    reviewed_at = "CURRENT_TIMESTAMP" if status == "approved" else None
    cursor = await db.execute(
        "INSERT INTO review_gates (step_number, gate_number, gate_name, status, reviewer, review_notes, reviewed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, " + ("CURRENT_TIMESTAMP" if status == "approved" else "NULL") + ")",
        (data["step_number"], data["gate_number"], data["gate_name"], status, reviewer, review_notes),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.put("/{gate_id}")
async def update_gate(gate_id: int, data: dict, db=Depends(get_db)):
    await db.execute(
        "UPDATE review_gates SET status = ?, reviewer = ?, review_notes = ?, "
        "reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (data["status"], data.get("reviewer"), data.get("review_notes"), gate_id),
    )
    await db.commit()
    return {"updated": True}


@router.get("/progress")
async def get_progress(db=Depends(get_db)):
    rows = await db.execute_fetchall(
        "SELECT step_number, "
        "COUNT(*) as total_gates, "
        "SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_gates "
        "FROM review_gates GROUP BY step_number ORDER BY step_number"
    )
    return [dict(r) for r in rows]
