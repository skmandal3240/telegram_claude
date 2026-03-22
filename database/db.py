import aiosqlite
import json
from datetime import datetime

import config

_db_path = config.DB_PATH


async def init_db():
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                task_type TEXT NOT NULL,
                task_data TEXT NOT NULL DEFAULT '{}',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user ON scheduled_tasks(user_id)"
        )
        await db.commit()


async def save_message(user_id: int, role: str, content: str):
    async with aiosqlite.connect(_db_path) as db:
        await db.execute(
            "INSERT INTO conversations (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_history(user_id: int, limit: int | None = None) -> list[dict]:
    limit = limit or config.MAX_CONVERSATION_HISTORY
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


async def clear_history(user_id: int):
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        await db.commit()


async def save_task(
    user_id: int, name: str, cron_expression: str, task_type: str, task_data: dict
) -> int:
    async with aiosqlite.connect(_db_path) as db:
        cursor = await db.execute(
            "INSERT INTO scheduled_tasks (user_id, name, cron_expression, task_type, task_data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, cron_expression, task_type, json.dumps(task_data), datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def get_tasks(user_id: int) -> list[dict]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, cron_expression, task_type, task_data, created_at FROM scheduled_tasks WHERE user_id = ? AND active = 1",
            (user_id,),
        )
        rows = await cursor.fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "cron": row["cron_expression"],
            "type": row["task_type"],
            "data": json.loads(row["task_data"]),
            "created": row["created_at"],
        }
        for row in rows
    ]


async def get_all_active_tasks() -> list[dict]:
    async with aiosqlite.connect(_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, user_id, name, cron_expression, task_type, task_data FROM scheduled_tasks WHERE active = 1"
        )
        rows = await cursor.fetchall()
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "cron": row["cron_expression"],
            "type": row["task_type"],
            "data": json.loads(row["task_data"]),
        }
        for row in rows
    ]


async def delete_task(task_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(_db_path) as db:
        cursor = await db.execute(
            "UPDATE scheduled_tasks SET active = 0 WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0
