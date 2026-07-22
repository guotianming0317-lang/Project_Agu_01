"""Tests for historical review helpers."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from app.database import initialize_database, save_alerts, save_market_snapshots
from app.history import build_history_summary, list_snapshot_batches


class HistoryTests(unittest.TestCase):
    """Verify lightweight historical review helpers."""

    def test_list_snapshot_batches_returns_unique_timestamps_desc(self) -> None:
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
                        "name": "Alpha",
                        "price": 12.34,
                        "pct_chg": 3.1,
                        "turnover": 100.0,
                        "volume_ratio": 1.1,
                        "turnover_rate": 2.0,
                        "sector": "Materials",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688268",
                        "name": "Beta",
                        "price": 45.20,
                        "pct_chg": 5.2,
                        "turnover": 150.0,
                        "volume_ratio": 1.9,
                        "turnover_rate": 3.2,
                        "sector": "Equipment",
                    },
                ],
            )

            batches = list_snapshot_batches(database_path)

            self.assertEqual(["2026-06-19 10:17:00", "2026-06-19 09:30:00"], batches)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_history_summary_uses_selected_timestamp_batch(self) -> None:
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
                        "name": "Alpha",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 200.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 4.5,
                        "sector": "Materials",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "002371",
                        "name": "Gamma",
                        "price": 310.5,
                        "pct_chg": 3.4,
                        "turnover": 300.0,
                        "volume_ratio": 1.4,
                        "turnover_rate": 2.0,
                        "sector": "Equipment",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "300001",
                        "name": "Delta",
                        "price": 15.2,
                        "pct_chg": -2.4,
                        "turnover": 60.0,
                        "volume_ratio": 0.8,
                        "turnover_rate": 1.1,
                        "sector": "Compute",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "alert_type": "materials_focus",
                        "level": "orange",
                        "message": "Materials line strength confirmed",
                        "related_stocks": "Alpha",
                        "direction": "Materials",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "alert_type": "risk",
                        "level": "yellow",
                        "message": "Opening risk still needs confirmation",
                        "related_stocks": "Delta",
                        "direction": "Compute",
                    },
                ],
            )

            summary = build_history_summary(database_path, "2026-06-19 10:17:00")

            self.assertIn("时间批次：2026-06-19 10:17:00", summary)
            self.assertIn("快照数量：3", summary)
            self.assertIn("预警数量：2", summary)
            self.assertIn("最强板块：Materials", summary)
            self.assertIn("次日策略摘要", summary)
            self.assertIn(
                "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
                summary,
            )
            self.assertIn("核心观察名单：Alpha", summary)
            self.assertIn("候选观察名单：Gamma", summary)
            self.assertIn("规避分数：", summary)
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u89c2\u5bdf", summary)
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\uff1a", summary)
            self.assertIn("Delta (-7)", summary)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_history_summary_includes_stock_pool_drift_header(self) -> None:
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
                        "name": "Alpha",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 200.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 4.5,
                        "sector": "Materials",
                    }
                ],
            )

            summary = build_history_summary(database_path, "2026-06-19 10:17:00")

            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a", summary)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
