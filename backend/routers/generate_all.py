"""
Generate All — API router for end-to-end 7-step generation.
Provides start, status polling, and retry endpoints.
"""

import asyncio
import json

from fastapi import APIRouter, Depends
from database import get_db, get_db_connection

router = APIRouter()

# In-memory tracking of running tasks (by run_id)
_running_tasks: dict[int, asyncio.Task] = {}


@router.post("/start")
async def start_generation(data: dict, db=Depends(get_db)):
    """Kick off end-to-end generation for an organization.
    Body: {"org_id": 1}
    Returns: {"run_id": 1, "status": "running"}
    """
    org_id = data.get("org_id")
    if not org_id:
        # Default: use the latest org
        org_row = await db.execute_fetchone("SELECT id FROM organization ORDER BY id DESC LIMIT 1")
        if not org_row:
            return {"error": "No organization found. Create one first."}
        org_id = org_row["id"]

    # Create generation_runs record
    cursor = await db.execute(
        "INSERT INTO generation_runs (org_id, status, current_step, message) VALUES (?, 'running', 0, 'Starting...')",
        [org_id],
    )
    await db.commit()
    run_id = cursor.lastrowid

    # Launch background task
    async def _run_orchestrator():
        conn = await get_db_connection()
        try:
            from ai_generate_all import generate_all_steps
            await generate_all_steps(run_id, org_id, conn)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Orchestrator crashed: %s", e)
            try:
                await conn.execute(
                    "UPDATE generation_runs SET status='failed', message=?, error_message=? WHERE id=?",
                    [f"Crashed: {e}", str(e), run_id],
                )
                await conn.commit()
            except Exception:
                pass
        finally:
            await conn.close()
            _running_tasks.pop(run_id, None)

    task = asyncio.create_task(_run_orchestrator())
    _running_tasks[run_id] = task

    return {"run_id": run_id, "status": "running"}


@router.get("/status/{run_id}")
async def get_status(run_id: int, db=Depends(get_db)):
    """Poll for generation progress.
    Returns current step, completed/failed steps, and message.
    """
    row = await db.execute_fetchone(
        "SELECT * FROM generation_runs WHERE id = ?", [run_id]
    )
    if not row:
        return {"error": "Run not found"}

    row = dict(row)

    # Parse JSON arrays
    steps_completed = json.loads(row.get("steps_completed") or "[]")
    steps_failed = json.loads(row.get("steps_failed") or "[]")

    return {
        "run_id": row["id"],
        "org_id": row["org_id"],
        "status": row["status"],
        "current_step": row["current_step"],
        "steps_completed": steps_completed,
        "steps_failed": steps_failed,
        "message": row.get("message"),
        "error_message": row.get("error_message"),
        "started_at": str(row.get("started_at") or ""),
        "completed_at": str(row.get("completed_at") or ""),
    }


@router.post("/retry/{run_id}")
async def retry_generation(run_id: int, db=Depends(get_db)):
    """Retry generation from where it failed.
    Re-runs the full pipeline (completed steps are idempotent and will be skipped).
    """
    row = await db.execute_fetchone(
        "SELECT * FROM generation_runs WHERE id = ?", [run_id]
    )
    if not row:
        return {"error": "Run not found"}

    row = dict(row)
    org_id = row["org_id"]

    # Check if already running
    if run_id in _running_tasks and not _running_tasks[run_id].done():
        return {"error": "Generation is already running", "run_id": run_id}

    # Reset status
    await db.execute(
        "UPDATE generation_runs SET status='running', message='Retrying...', error_message=NULL, completed_at=NULL WHERE id=?",
        [run_id],
    )
    await db.commit()

    # Re-launch
    async def _run_orchestrator():
        conn = await get_db_connection()
        try:
            from ai_generate_all import generate_all_steps
            await generate_all_steps(run_id, org_id, conn)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Retry orchestrator crashed: %s", e)
        finally:
            await conn.close()
            _running_tasks.pop(run_id, None)

    task = asyncio.create_task(_run_orchestrator())
    _running_tasks[run_id] = task

    return {"run_id": run_id, "status": "running", "message": "Retrying generation..."}


@router.get("/latest")
async def get_latest_run(db=Depends(get_db)):
    """Get the most recent generation run."""
    row = await db.execute_fetchone(
        "SELECT * FROM generation_runs ORDER BY id DESC LIMIT 1"
    )
    if not row:
        return None

    row = dict(row)
    steps_completed = json.loads(row.get("steps_completed") or "[]")
    steps_failed = json.loads(row.get("steps_failed") or "[]")

    return {
        "run_id": row["id"],
        "org_id": row["org_id"],
        "status": row["status"],
        "current_step": row["current_step"],
        "steps_completed": steps_completed,
        "steps_failed": steps_failed,
        "message": row.get("message"),
        "error_message": row.get("error_message"),
        "started_at": str(row.get("started_at") or ""),
        "completed_at": str(row.get("completed_at") or ""),
    }
