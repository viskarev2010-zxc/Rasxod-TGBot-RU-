"""Минималистичный Telegram-бот: учёт бюджета + Pomodoro-таймер."""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from bot.database.db import init_db
from bot.handlers import finance, pomodoro
from bot.services.timer import pomodoro_timer


async def main() -> None:
    load_dotenv()

    token = (
        os.getenv("BOT_TOKEN", "").strip()
        or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    if not token:
        raise SystemExit("BOT_TOKEN не задан. Создайте .env по образцу .env.example.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("main")

    await init_db()
    logger.info("База данных готова")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(pomodoro.router)
    dp.include_router(finance.router)

    logger.info("Бот запускается в режиме polling")
    try:
        await dp.start_polling(bot)
    finally:
        pomodoro_timer.cancel_all()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code:
            print(exc.code)
