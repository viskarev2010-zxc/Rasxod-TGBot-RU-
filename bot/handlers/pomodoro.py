"""Pomodoro-таймер: запуск, отмена и статистика фокуса."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.database import queries
from bot.keyboards.main_kb import BTN_POMODORO, main_menu_kb, pomodoro_kb
from bot.services.timer import pomodoro_timer

router = Router(name="pomodoro")

POMODORO_MINUTES = 25


def _fmt_time(seconds: int) -> str:
    return f"{seconds // 60} мин {seconds % 60:02d} сек"


@router.message(F.text == BTN_POMODORO)
@router.message(Command("pomodoro"))
async def start_pomodoro(message: Message) -> None:
    user_id = message.from_user.id

    if pomodoro_timer.is_running(user_id):
        left = pomodoro_timer.remaining(user_id) or 0
        await message.answer(
            f"⏳ Фокус уже идёт: осталось <b>{_fmt_time(left)}</b>.",
            reply_markup=pomodoro_kb(),
        )
        return

    bot = message.bot

    async def notify(uid: int, minutes: int) -> None:
        await queries.add_pomodoro_session(uid, minutes)
        today = await queries.get_today_sessions(uid)
        minutes_today = await queries.get_today_focus_minutes(uid)
        await bot.send_message(
            uid,
            f"✅ <b>Помидор на {minutes} мин завершён!</b>\n\n"
            f"Сегодня: <b>{today}</b> сессий, <b>{minutes_today}</b> мин в фокусе.\n"
            "Отдохните 5 минут и возвращайтесь 🍵",
            reply_markup=main_menu_kb(),
        )

    pomodoro_timer.start(user_id, POMODORO_MINUTES, notify)
    await message.answer(
        f"🍅 <b>Помидор запущен на {POMODORO_MINUTES} минут.</b>\n"
        "Телефон можно отложить — я напомню, когда время выйдет.",
        reply_markup=pomodoro_kb(),
    )


@router.callback_query(F.data == "pomo:stop")
async def stop_pomodoro(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    stopped = pomodoro_timer.cancel(user_id)
    text = "⏹ Таймер остановлен." if stopped else "Активного таймера нет."
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "pomo:stats")
async def focus_stats(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    today = await queries.get_today_sessions(user_id)
    minutes_today = await queries.get_today_focus_minutes(user_id)
    suffix = ""
    if pomodoro_timer.is_running(user_id):
        left = pomodoro_timer.remaining(user_id) or 0
        suffix = f"\n⏳ Идёт ещё одна сессия: осталось {_fmt_time(left)}"

    await callback.message.answer(
        "📈 <b>Статистика фокуса</b>\n\n"
        f"🍅 Сессий сегодня: <b>{today}</b>\n"
        f"⏱ Минут в фокусе: <b>{minutes_today}</b>"
        f"{suffix}",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
