"""Scheduler setup for periodic monitor jobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SchedulerLike(Protocol):
    """Small interface used by the app bootstrap."""

    def shutdown(self, wait: bool = True) -> None:
        """Stop the scheduler."""


@dataclass(slots=True)
class NoOpScheduler:
    """Fallback scheduler used before third-party dependencies are installed."""

    timezone: str = "Asia/Shanghai"

    def shutdown(self, wait: bool = True) -> None:
        """Provide the same API as APScheduler for local bootstrap."""
        _ = wait


def build_scheduler() -> SchedulerLike:
    """Create a scheduler instance for future timed jobs.

    The project prefers APScheduler, but phase one should still be runnable
    before dependencies are installed in VS Code.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ModuleNotFoundError:
        return NoOpScheduler()

    return BackgroundScheduler(timezone="Asia/Shanghai")
