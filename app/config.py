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
    database_path: Path
    database_url: str
    log_level: str


def load_config() -> AppConfig:
    """Load application configuration from environment variables."""
    database_path = Path(
        os.getenv("MONITOR_DATABASE_PATH", BASE_DIR / "data" / "monitor.db")
    )
    return AppConfig(
        environment=os.getenv("MONITOR_ENV", "dev"),
        database_path=database_path,
        database_url=f"sqlite:///{database_path.as_posix()}",
        log_level=os.getenv("MONITOR_LOG_LEVEL", "INFO"),
    )
