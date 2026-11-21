"""Главное меню и inline-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Тексты кнопок главного меню (используются и в фильтрах хендлеров).
BTN_ADD_EXPENSE = "➕ Добавить расход"
BTN_STATS = "📊 Статистика"
BTN_POMODORO = "🍅 Pomodoro 25 мин"

MENU_BUTTONS: tuple[str, ...] = (BTN_ADD_EXPENSE, BTN_STATS, BTN_POMODORO)

EXPENSE_CATEGORIES: tuple[str, ...] = ("Еда", "Транспорт", "Развлечения", "Другое")

CATEGORY_ICONS: dict[str, str] = {
    "Еда": "🍔",
    "Транспорт": "🚌",
    "Развлечения": "🎮",
    "Другое": "📦",
}


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Постоянное Reply-меню под полем ввода."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_ADD_EXPENSE)
    builder.button(text=BTN_STATS)
    builder.button(text=BTN_POMODORO)
    builder.adjust(2, 1)
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Например: кофе 250 или +зарплата 50000",
    )


def categories_kb() -> InlineKeyboardMarkup:
    """Inline-кнопки выбора категории расхода."""
    builder = InlineKeyboardBuilder()
    for category in EXPENSE_CATEGORIES:
        icon = CATEGORY_ICONS.get(category, "•")
        builder.button(text=f"{icon} {category}", callback_data=f"cat:{category}")
    builder.button(text="✖️ Отмена", callback_data="cancel")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены ввода суммы."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✖️ Отмена", callback_data="cancel")
    return builder.as_markup()


def pomodoro_kb() -> InlineKeyboardMarkup:
    """Управление активным Pomodoro-таймером."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏹ Остановить", callback_data="pomo:stop")
    builder.button(text="📈 Статистика фокуса", callback_data="pomo:stats")
    builder.adjust(1)
    return builder.as_markup()
