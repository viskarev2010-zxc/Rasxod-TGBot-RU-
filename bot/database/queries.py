"""Запросы к базе данных бота."""

from __future__ import annotations

from datetime import datetime

import aiosqlite

from .db import get_connection


async def add_transaction(
    user_id: int,
    amount: float,
    category: str,
    type_: str,
) -> int:
    """Добавить транзакцию и вернуть её id."""
    if type_ not in ("income", "expense"):
        raise ValueError("type_ должен быть 'income' или 'expense'")

    async with get_connection() as db:
        cursor = await db.execute(
            "INSERT INTO transactions (user_id, amount, category, type) "
            "VALUES (?, ?, ?, ?)",
            (user_id, float(amount), category.strip(), type_),
        )
        await db.commit()
        return cursor.lastrowid


async def get_balance(user_id: int) -> float:
    """Текущий баланс: доходы минус расходы за всё время."""
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(CASE WHEN type = 'income' THEN amount "
            "ELSE -amount END), 0) FROM transactions WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return float(row[0] or 0)


async def get_month_expenses(
    user_id: int,
    now: datetime | None = None,
) -> float:
    """Сумма расходов за текущий календарный месяц."""
    now = now or datetime.now()
    month_prefix = now.strftime("%Y-%m")

    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions "
            "WHERE user_id = ? AND type = 'expense' "
            "AND strftime('%Y-%m', created_at) = ?",
            (user_id, month_prefix),
        )
        row = await cursor.fetchone()
        return float(row[0] or 0)


async def add_pomodoro_session(user_id: int, duration_minutes: int) -> int:
    """Записать завершённую Pomodoro-сессию и вернуть её id."""
    async with get_connection() as db:
        cursor = await db.execute(
            "INSERT INTO pomodoro_sessions (user_id, duration_minutes) "
            "VALUES (?, ?)",
            (user_id, int(duration_minutes)),
        )
        await db.commit()
        return cursor.lastrowid


async def get_today_sessions(user_id: int) -> int:
    """Количество завершённых Pomodoro-сессий за сегодня."""
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM pomodoro_sessions "
            "WHERE user_id = ? AND date(completed_at) = date('now', 'localtime')",
            (user_id,),
        )
        row = await cursor.fetchone()
        return int(row[0] or 0)


async def get_today_focus_minutes(user_id: int) -> int:
    """Суммарное время в фокусе за сегодня, в минутах."""
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) FROM pomodoro_sessions "
            "WHERE user_id = ? AND date(completed_at) = date('now', 'localtime')",
            (user_id,),
        )
        row = await cursor.fetchone()
        return int(row[0] or 0)
