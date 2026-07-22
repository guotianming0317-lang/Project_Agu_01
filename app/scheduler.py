"""Scheduler setup for periodic monitor jobs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from app.config import AppConfig
from app.pipeline import (
    MonitorCycleResult,
    build_cycle_console_output_with_strategy,
    run_monitor_cycle,
)
from app.task_profiles import (
    DEFAULT_SCHEDULED_JOBS,
    JOB_INTENT_STRATEGIES,
    JOB_OUTPUT_STRATEGIES,
    build_job_view_mode_lines,
    build_output_profiles_lines,
    build_task_overview_lines,
    get_task_display_job_ids,
)


class SchedulerLike(Protocol):
    """Small interface used by the app bootstrap."""

    def add_job(
        self,
        func: Any,
        trigger: str,
        *,
        id: str,
        replace_existing: bool,
        kwargs: dict[str, Any],
        **trigger_kwargs: Any,
    ) -> None:
        """Register a scheduled job."""

    def shutdown(self, wait: bool = True) -> None:
        """Stop the scheduler."""

    def start(self) -> None:
        """Start the scheduler when supported."""


@dataclass(slots=True)
class NoOpScheduler:
    """Fallback scheduler used before third-party dependencies are installed."""

    timezone: str = "Asia/Shanghai"
    jobs: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        """Initialize lightweight in-memory job tracking."""
        if self.jobs is None:
            self.jobs = []

    def add_job(
        self,
        func: Any,
        trigger: str,
        *,
        id: str,
        replace_existing: bool,
        kwargs: dict[str, Any],
        **trigger_kwargs: Any,
    ) -> None:
        """Record scheduled jobs without requiring APScheduler."""
        assert self.jobs is not None
        self.jobs.append(
            {
                "func": func,
                "trigger_type": trigger,
                "id": id,
                "replace_existing": replace_existing,
                "kwargs": kwargs,
                "trigger": trigger_kwargs,
            }
        )

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


def run_monitor_job(config: AppConfig, job_id: str = "manual") -> MonitorCycleResult:
    """Run one reusable monitor cycle for scheduler-triggered execution."""
    _ = job_id
    return run_monitor_cycle(config)


def resolve_job_output_strategy(job_id: str) -> dict[str, bool]:
    """Resolve one reusable output strategy for a scheduler or manual job id."""
    return dict(JOB_OUTPUT_STRATEGIES.get(job_id, JOB_OUTPUT_STRATEGIES["manual"]))


def resolve_job_intent_strategy(job_id: str) -> dict[str, dict[str, object] | str]:
    """Resolve one reusable task-intent strategy for a scheduler or manual job id."""
    return dict(JOB_INTENT_STRATEGIES.get(job_id, JOB_INTENT_STRATEGIES["manual"]))


def build_job_console_output(
    config: AppConfig,
    result: MonitorCycleResult,
    *,
    job_id: str,
) -> str:
    """Build scheduler-aware console output for one specific job type."""
    report_body = build_cycle_console_output_with_strategy(
        config,
        result,
        output_strategy=resolve_job_output_strategy(job_id),
        intent_strategy=resolve_job_intent_strategy(job_id),
    )
    view_mode_lines = build_job_view_mode_lines(job_id)
    if not view_mode_lines:
        return report_body
    return "\n".join([*view_mode_lines, "", report_body])


def register_default_jobs(scheduler: SchedulerLike, config: AppConfig) -> None:
    """Register explicit phase-one monitoring jobs."""
    for job in DEFAULT_SCHEDULED_JOBS:
        scheduler.add_job(
            run_monitor_job,
            "cron",
            id=job["id"],
            replace_existing=True,
            kwargs={"config": config, "job_id": job["id"]},
            hour=job["hour"],
            minute=job["minute"],
        )


def build_scheduler_status_text(
    config: AppConfig,
    scheduler: SchedulerLike | None = None,
) -> str:
    """Build a simple local status summary for scheduler configuration."""
    runtime_mode, persistent_loop = _describe_scheduler_runtime(scheduler)
    lines = [
        "Scheduler Status",
        f"Scheduler enabled: {'yes' if config.enable_scheduler else 'no'}",
        f"Default protocol: {config.default_protocol}",
        f"Database: {config.database_url}",
        f"Runtime mode: {runtime_mode}",
        f"Persistent loop available: {'yes' if persistent_loop else 'no'}",
    ]
    lines.extend(["", *build_task_overview_lines()])
    lines.extend(build_output_profiles_lines())
    if runtime_mode == "fallback-noop":
        lines.extend(
            [
                "Install hint:",
                "- Install scheduler dependencies: pip install -r requirements.txt",
                "- Verify runtime again: python -m app.main scheduler-status",
            ]
        )
        lines.append("Next recommended command: pip install -r requirements.txt")
    elif runtime_mode == "scheduler-ready":
        lines.append("Next recommended command: python -m app.main run-scheduler")
    else:
        lines.append("Next recommended command: python -m app.main scheduler-status")
    return "\n".join(lines)


def run_scheduler_loop(
    scheduler: SchedulerLike,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> str:
    """Run a lightweight scheduler loop when runtime support is available."""
    if isinstance(scheduler, NoOpScheduler) or not hasattr(scheduler, "start"):
        return "APScheduler is not available. Install it before using run-scheduler."

    scheduler.start()
    try:
        while True:
            sleep_fn(60.0)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
        return "Scheduler stopped."


def _describe_scheduler_runtime(
    scheduler: SchedulerLike | None,
) -> tuple[str, bool]:
    """Describe whether the current scheduler can run persistently."""
    if scheduler is None:
        return "unknown", False
    if isinstance(scheduler, NoOpScheduler):
        return "fallback-noop", False
    if hasattr(scheduler, "start"):
        return "scheduler-ready", True
    return "unknown", False


def build_registered_jobs_summary() -> str:
    """Build one short registered-job summary line from the task config."""
    scheduled_job_ids = set(get_task_display_job_ids(group_key="scheduled_day_flow"))
    job_chunks = [
        f"{job['id']} ({job['hour']:02d}:{job['minute']:02d})"
        for job in DEFAULT_SCHEDULED_JOBS
        if str(job["id"]) in scheduled_job_ids
    ]
    return "Registered jobs: " + ", ".join(job_chunks)
