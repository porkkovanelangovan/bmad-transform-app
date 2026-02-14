import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "bmad_transform.db")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()
