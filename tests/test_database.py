"""Tests for SQLite persistence helpers."""

from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from app.database import (
    fetch_alerts,
    fetch_latest_alerts,
    fetch_latest_market_snapshots,
    fetch_market_snapshots,
    initialize_database,
    save_alerts,
    save_market_snapshots,
)


class DatabaseTests(unittest.TestCase):
    """Verify phase-one SQLite bootstrap and persistence."""

    def test_initialize_database_creates_required_tables(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)

            snapshots = fetch_market_snapshots(database_path)
            alerts = fetch_alerts(database_path)

            self.assertEqual([], snapshots)
            self.assertEqual([], alerts)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_and_fetch_market_snapshots(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.34,
                        "pct_chg": 8.6,
                        "turnover": 123456789,
                        "volume_ratio": 2.3,
                        "turnover_rate": 4.5,
                        "sector": "半导体气体",
                        "quote_source": "local-json-snapshot",
                    }
                ],
            )

            snapshots = fetch_market_snapshots(database_path)

            self.assertEqual(1, len(snapshots))
            self.assertEqual("688549", snapshots[0]["code"])
            self.assertEqual("半导体气体", snapshots[0]["sector"])
            self.assertEqual("local-json-snapshot", snapshots[0]["quote_source"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_and_fetch_alerts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "alert_type": "price_spike",
                        "level": "橙色",
                        "message": "中巨芯-U 单日涨幅达到 8.6%",
                        "related_stocks": "中巨芯-U",
                        "direction": "半导体气体",
                    }
                ],
            )

            alerts = fetch_alerts(database_path)

            self.assertEqual(1, len(alerts))
            self.assertEqual("price_spike", alerts[0]["alert_type"])
            self.assertEqual("橙色", alerts[0]["level"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_latest_rows_returns_only_latest_timestamp_batch(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 09:30:00",
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.34,
                        "pct_chg": 3.1,
                        "turnover": 100.0,
                        "volume_ratio": 1.1,
                        "turnover_rate": 2.0,
                        "sector": "半导体气体",
                        "quote_source": "demo-fallback",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 200.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 4.5,
                        "sector": "半导体气体",
                        "quote_source": "eastmoney-direct",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 09:31:00",
                        "alert_type": "price_spike",
                        "level": "橙色",
                        "message": "旧预警",
                        "related_stocks": "中巨芯-U",
                        "direction": "半导体气体",
                    },
                    {
                        "timestamp": "2026-06-19 10:18:00",
                        "alert_type": "materials_focus",
                        "level": "橙色",
                        "message": "新预警",
                        "related_stocks": "中巨芯-U",
                        "direction": "半导体材料、半导体气体",
                    },
                ],
            )

            latest_snapshots = fetch_latest_market_snapshots(database_path)
            latest_alerts = fetch_latest_alerts(database_path)

            self.assertEqual(1, len(latest_snapshots))
            self.assertEqual("2026-06-19 10:17:00", latest_snapshots[0]["timestamp"])
            self.assertEqual("eastmoney-direct", latest_snapshots[0]["quote_source"])
            self.assertEqual(1, len(latest_alerts))
            self.assertEqual("新预警", latest_alerts[0]["message"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialize_database_adds_quote_source_column_for_older_local_db(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    """
                    CREATE TABLE market_snapshot (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        code TEXT NOT NULL,
                        name TEXT NOT NULL,
                        price REAL,
                        pct_chg REAL,
                        turnover REAL,
                        volume_ratio REAL,
                        turnover_rate REAL,
                        sector TEXT
                    )
                    """
                )
                connection.commit()

            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.34,
                        "pct_chg": 8.6,
                        "turnover": 123456789,
                        "volume_ratio": 2.3,
                        "turnover_rate": 4.5,
                        "sector": "半导体气体",
                        "quote_source": "local-json-snapshot",
                    }
                ],
            )

            snapshots = fetch_market_snapshots(database_path)

            self.assertEqual("local-json-snapshot", snapshots[0]["quote_source"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
