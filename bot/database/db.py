import aiosqlite
from bot.config import DB_PATH

_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    username  TEXT,
    city      TEXT DEFAULT '',
    lat       REAL,
    lon       REAL,
    tone      TEXT DEFAULT 'neutral',
    health_mode TEXT DEFAULT '',
    notify_enabled INTEGER DEFAULT 0,
    notify_time TEXT DEFAULT '08:00',
    created_at TEXT DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(_CREATE_USERS)
        await db.commit()


async def upsert_user(user_id: int, username: str | None = None) -> None:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
            """,
            (user_id, username or ""),
        )
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def update_user(user_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
        )
        await db.execute(
            f"UPDATE users SET {set_clause} WHERE user_id = ?",
            values,
        )
        await db.commit()
