"""Учёт трат и доходов: кнопки, inline-категории и быстрый парсинг текста."""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.database import queries
from bot.keyboards.main_kb import (
    BTN_ADD_EXPENSE,
    BTN_STATS,
    CATEGORY_ICONS,
    EXPENSE_CATEGORIES,
    MENU_BUTTONS,
    cancel_kb,
    categories_kb,
    main_menu_kb,
)

router = Router(name="finance")

INCOME_WORDS = {"доход", "зарплата", "аванс", "прибыль", "income"}
ENTRY_RE = re.compile(r"^(?P<name>.+?)\s+(?P<amount>\d+(?:[.,]\d{1,2})?)$")
AMOUNT_ONLY_RE = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


class FinanceStates(StatesGroup):
    waiting_amount = State()


def _fmt(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def parse_entry(text: str) -> tuple[str, float, str] | None:
    """Разбирает строку вида «кофе 250», «еда 350», «+зарплата 50000».

    Возвращает (категория, сумма, тип) или None, если формат не распознан.
    """
    raw = text.strip().replace(",", ".")
    is_income = raw.startswith("+")
    if is_income:
        raw = raw[1:].strip()

    match = ENTRY_RE.match(raw)
    if not match:
        return None

    amount = float(match["amount"])
    if amount <= 0:
        return None

    name = match["name"].strip()
    lower = name.lower()

    if is_income or lower in INCOME_WORDS:
        return "Доход", amount, "income"

    canonical = next((c for c in EXPENSE_CATEGORIES if c.lower() == lower), None)
    return (canonical or name.capitalize()), amount, "expense"


async def _confirm(message: Message, category: str, amount: float, type_: str) -> None:
    balance = await queries.get_balance(message.from_user.id)
    if type_ == "income":
        icon, title = "💵", "Доход добавлен"
    else:
        icon = CATEGORY_ICONS.get(category, "🧾")
        title = "Расход добавлен"
    await message.answer(
        f"{icon} <b>{title}</b>\n\n"
        f"▫️ {category}: <b>{_fmt(amount)} ₽</b>\n"
        f"💰 Баланс: <b>{_fmt(balance)} ₽</b>",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 <b>Привет!</b> Я помогу вести бюджет и не забывать про отдых.\n\n"
        "➕ «Добавить расход» — выбор категории кнопками\n"
        "⌨️ Или просто напишите: <code>кофе 250</code>\n"
        "💵 Доход: <code>+зарплата 50000</code>\n"
        "🍅 «Pomodoro 25 мин» — таймер фокуса",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == BTN_ADD_EXPENSE)
async def ask_category(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите категорию расхода:", reply_markup=categories_kb())


@router.callback_query(F.data.startswith("cat:"))
async def choose_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = (callback.data or "").split(":", 1)[-1]
    await state.set_state(FinanceStates.waiting_amount)
    await state.update_data(category=category, type="expense")
    await callback.message.edit_text(
        f"Категория: <b>{CATEGORY_ICONS.get(category, '•')} {category}</b>\n"
        "Введите сумму числом, например <code>350</code> или <code>350,50</code>.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Отменено. Возвращайтесь, когда понадобится 🙂")
    await callback.answer()


@router.message(F.text == BTN_STATS)
async def show_stats(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    balance = await queries.get_balance(user_id)
    month_expenses = await queries.get_month_expenses(user_id)
    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        f"💰 Баланс: <b>{_fmt(balance)} ₽</b>\n"
        f"📉 Расходы за месяц: <b>{_fmt(month_expenses)} ₽</b>\n\n"
        "Быстрая запись: <code>еда 350</code>, <code>+зарплата 50000</code>",
        reply_markup=main_menu_kb(),
    )


@router.message(
    FinanceStates.waiting_amount,
    F.text,
    ~F.text.in_(MENU_BUTTONS),
    ~F.text.startswith("/"),
)
async def enter_amount(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    data = await state.get_data()

    if AMOUNT_ONLY_RE.match(text):
        amount = float(text.replace(",", "."))
        if amount <= 0:
            await message.answer("Сумма должна быть больше нуля. Попробуйте ещё раз:")
            return
        category = data.get("category", "Другое")
        type_ = data.get("type", "expense")
    else:
        parsed = parse_entry(text)
        if parsed is None:
            await message.answer(
                "Не разобрал сумму 🤔 Введите число, например <code>350</code>, "
                "или отмените выбор.",
                reply_markup=cancel_kb(),
            )
            return
        category, amount, type_ = parsed

    await state.clear()
    await queries.add_transaction(message.from_user.id, amount, category, type_)
    await _confirm(message, category, amount, type_)


@router.message(F.text, ~F.text.in_(MENU_BUTTONS), ~F.text.startswith("/"))
async def quick_entry(message: Message, state: FSMContext) -> None:
    parsed = parse_entry(message.text or "")
    if parsed is None:
        await message.answer(
            "Не понял запись 🤔 Используйте формат <code>название сумма</code>, "
            "например <code>кофе 250</code>, или меню ниже.",
            reply_markup=main_menu_kb(),
        )
        return

    await state.clear()
    category, amount, type_ = parsed
    await queries.add_transaction(message.from_user.id, amount, category, type_)
    await _confirm(message, category, amount, type_)
