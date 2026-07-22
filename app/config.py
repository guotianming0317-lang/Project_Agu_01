"""Configuration helpers for the AI semiconductor monitor project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class AppConfig:
    """Application settings loaded from environment variables."""

    environment: str
    default_protocol: str
    database_path: Path
    database_url: str
    log_level: str
    auto_latest_review: bool
    enable_scheduler: bool


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    database_path = Path(
        os.getenv("MONITOR_DATABASE_PATH", BASE_DIR / "data" / "monitor.db")
    )
    return AppConfig(
        environment=os.getenv("MONITOR_ENV", "dev"),
        default_protocol=os.getenv("MONITOR_DEFAULT_PROTOCOL", "http"),
        database_path=database_path,
        database_url=f"sqlite:///{database_path.as_posix()}",
        log_level=os.getenv("MONITOR_LOG_LEVEL", "INFO"),
        auto_latest_review=_parse_bool(
            os.getenv("MONITOR_AUTO_LATEST_REVIEW", "false")
        ),
        enable_scheduler=_parse_bool(
            os.getenv("MONITOR_ENABLE_SCHEDULER", "false")
        ),
    )


def _parse_bool(value: str) -> bool:
    """Parse a small set of truthy environment values."""
    return value.strip().lower() in {"1", "true", "yes", "on"}
