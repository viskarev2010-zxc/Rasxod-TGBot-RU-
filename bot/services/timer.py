"""Обратный отсчёт Pomodoro на asyncio.create_task."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

NotifyFunc = Callable[[int, int], Awaitable[None]]


class PomodoroTimer:
    """Держит активные таймеры пользователей и вызывает callback по истечении."""

    def __init__(self) -> None:
        self._tasks: dict[int, asyncio.Task[None]] = {}
        self._ends: dict[int, float] = {}

    def is_running(self, user_id: int) -> bool:
        task = self._tasks.get(user_id)
        return task is not None and not task.done()

    def remaining(self, user_id: int) -> int | None:
        """Сколько секунд осталось (None, если таймер не запущен)."""
        if not self.is_running(user_id):
            return None
        return max(0, int(round(self._ends[user_id] - time.monotonic())))

    def start(
        self,
        user_id: int,
        minutes: int,
        notify: NotifyFunc,
    ) -> asyncio.Task[None]:
        """Запустить отсчёт; notify(user_id, minutes) вызовется по завершении."""
        if self.is_running(user_id):
            raise RuntimeError("Таймер уже запущен")

        self._ends[user_id] = time.monotonic() + minutes * 60
        task = asyncio.create_task(
            self._countdown(user_id, minutes, notify),
            name=f"pomodoro-{user_id}",
        )
        self._tasks[user_id] = task
        return task

    async def _countdown(self, user_id: int, minutes: int, notify: NotifyFunc) -> None:
        try:
            await asyncio.sleep(minutes * 60)
            await notify(user_id, minutes)
        except asyncio.CancelledError:
            logger.info("Таймер пользователя %s отменён", user_id)
            raise
        except Exception:
            logger.exception("Ошибка в таймере пользователя %s", user_id)
        finally:
            self._ends.pop(user_id, None)
            self._tasks.pop(user_id, None)

    def cancel(self, user_id: int) -> bool:
        """Остановить таймер. True — если он был активен."""
        task = self._tasks.pop(user_id, None)
        self._ends.pop(user_id, None)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    def cancel_all(self) -> None:
        for user_id in list(self._tasks):
            self.cancel(user_id)


pomodoro_timer = PomodoroTimer()
