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
    _load_local_env_file()
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


def _load_local_env_file() -> None:
    """Load simple KEY=VALUE settings without requiring python-dotenv."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
