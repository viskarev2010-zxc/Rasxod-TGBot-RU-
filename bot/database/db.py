"""Асинхронная инициализация SQLite-базы бота."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parents[2] / "bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    amount      REAL    NOT NULL CHECK (amount >= 0),
    category    TEXT    NOT NULL,
    type        TEXT    NOT NULL CHECK (type IN ('income', 'expense')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_month
    ON transactions (user_id, created_at);

CREATE TABLE IF NOT EXISTS pomodoro_sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    completed_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_pomodoro_user_day
    ON pomodoro_sessions (user_id, completed_at);
"""


def get_connection() -> aiosqlite.Connection:
    """Открыть соединение с базой (использовать через `async with`)."""
    return aiosqlite.connect(DB_PATH)


async def init_db() -> None:
    """Создать базу и таблицы, если их ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(SCHEMA)
        await db.commit()
