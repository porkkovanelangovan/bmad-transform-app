import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "bmad_transform.db")
DATABASE_URL = os.getenv("DATABASE_URL")

# Detect mode
USE_POSTGRES = bool(DATABASE_URL)

# Connection pool (initialized at startup for PostgreSQL)
_pg_pool = None


def _sqlite_to_pg_query(query: str, params: list | None = None):
    """Convert SQLite-style ? placeholders to PostgreSQL $1, $2, ... style."""
    if params is None:
        return query, params
    converted = []
    counter = [0]

    def replacer(match):
        counter[0] += 1
        return f"${counter[0]}"

    converted_query = re.sub(r"\?", replacer, query)
    return converted_query, params


class SQLiteRow:
    """Wrapper to make aiosqlite Row dict-accessible via both ['key'] and .items()."""
    def __init__(self, row, description):
        if row is None:
            self._data = {}
        elif hasattr(row, 'keys'):
            self._data = dict(row)
        else:
            cols = [d[0] for d in description] if description else []
            self._data = dict(zip(cols, row))

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return repr(self._data)


class CursorResult:
    """Unified cursor result with lastrowid."""
    def __init__(self, lastrowid=None):
        self.lastrowid = lastrowid


class DBConnection:
    """Unified database connection interface for both SQLite and PostgreSQL."""

    def __init__(self, conn, is_postgres=False):
        self._conn = conn
        self._is_postgres = is_postgres

    async def execute_fetchall(self, query: str, params: list | None = None) -> list:
        if self._is_postgres:
            q, p = _sqlite_to_pg_query(query, params)
            rows = await self._conn.fetch(q, *(p or []))
            return [dict(r) for r in rows]
        else:
            cursor = await self._conn.execute(query, params or [])
            rows = await cursor.fetchall()
            desc = cursor.description
            return [SQLiteRow(r, desc) for r in rows]

    async def execute_fetchone(self, query: str, params: list | None = None):
        if self._is_postgres:
            q, p = _sqlite_to_pg_query(query, params)
            row = await self._conn.fetchrow(q, *(p or []))
            return dict(row) if row else None
        else:
            cursor = await self._conn.execute(query, params or [])
            row = await cursor.fetchone()
            if row is None:
                return None
            return SQLiteRow(row, cursor.description)

    async def execute(self, query: str, params: list | None = None) -> CursorResult:
        if self._is_postgres:
            q, p = _sqlite_to_pg_query(query, params)
            # For INSERT ... RETURNING id, try to get the id
            if q.strip().upper().startswith("INSERT") and "RETURNING" not in q.upper():
                q = q.rstrip(";") + " RETURNING id"
                try:
                    row = await self._conn.fetchrow(q, *(p or []))
                    return CursorResult(lastrowid=row["id"] if row else None)
                except Exception:
                    # Table may not have 'id' column, fall back
                    q = q.rsplit("RETURNING", 1)[0].strip()
                    await self._conn.execute(q, *(p or []))
                    return CursorResult()
            else:
                result = await self._conn.execute(q, *(p or []))
                return CursorResult()
        else:
            cursor = await self._conn.execute(query, params or [])
            return CursorResult(lastrowid=cursor.lastrowid)

    async def executescript(self, script: str):
        if self._is_postgres:
            await self._conn.execute(script)
        else:
            await self._conn.executescript(script)

    async def commit(self):
        if not self._is_postgres:
            await self._conn.commit()

    async def close(self):
        if self._is_postgres:
            await _pg_pool.release(self._conn)
        else:
            await self._conn.close()


async def init_pg_pool():
    """Initialize PostgreSQL connection pool at app startup."""
    global _pg_pool
    if USE_POSTGRES and _pg_pool is None:
        import asyncpg
        # Render provides DATABASE_URL starting with postgres:// but asyncpg needs postgresql://
        db_url = DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = "postgresql://" + db_url[len("postgres://"):]
        _pg_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)


async def close_pg_pool():
    """Close PostgreSQL connection pool at app shutdown."""
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None


async def get_db_connection() -> DBConnection:
    """Get a raw database connection (not a generator). Caller must close."""
    if USE_POSTGRES:
        conn = await _pg_pool.acquire()
        return DBConnection(conn, is_postgres=True)
    else:
        import aiosqlite
        conn = await aiosqlite.connect(DB_PATH)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        return DBConnection(conn, is_postgres=False)


async def get_db():
    """FastAPI dependency that yields a DBConnection."""
    db = await get_db_connection()
    try:
        yield db
    finally:
        await db.close()
