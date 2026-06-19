"""Application entry point for the AI semiconductor monitor demo."""

from __future__ import annotations

from app.config import AppConfig, load_config
from app.database import initialize_database
from app.reports.evening_report import build_evening_report
from app.reports.morning_report import build_morning_report
from app.scheduler import build_scheduler
from app.universe.stock_pool import get_all_stocks, get_high_priority_stocks


def run_demo(config: AppConfig) -> None:
    """Run a minimal demo that proves the project wiring works."""
    all_stocks = get_all_stocks()
    high_priority = get_high_priority_stocks()

    print("AI Semiconductor Monitor Demo")
    print(f"Environment: {config.environment}")
    print(f"Database: {config.database_url}")
    print(f"Total stocks in universe: {len(all_stocks)}")
    print(f"High priority stocks: {len(high_priority)}")
    print()
    print(build_morning_report())
    print()
    print(build_evening_report())


def main() -> None:
    """Bootstrap the application."""
    config = load_config()
    initialize_database(config.database_path)
    scheduler = build_scheduler()
    scheduler.shutdown(wait=False)
    run_demo(config)


if __name__ == "__main__":
    main()
