"""
Version Toggle Router — Switch between platform v1.0 and v2.0.
"""

from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()


@router.get("")
async def get_version(db=Depends(get_db)):
    """Get the current platform version."""
    row = await db.execute_fetchone("SELECT platform_version FROM organization LIMIT 1")
    version = (row.get("platform_version") if row else "1.0") or "1.0"
    return {"platform_version": version}


@router.post("")
async def set_version(data: dict, db=Depends(get_db)):
    """Toggle between v1.0 and v2.0."""
    version = data.get("platform_version", "1.0")
    if version not in ("1.0", "2.0"):
        return {"error": "platform_version must be '1.0' or '2.0'"}

    await db.execute("UPDATE organization SET platform_version = ?", [version])
    await db.commit()
    return {"platform_version": version, "message": f"Switched to v{version}"}
