"""Tests for the minimal application bootstrap path."""

from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from app.database import (
    fetch_alerts,
    fetch_market_snapshots,
    initialize_database,
    save_market_snapshots,
)
from app.pipeline import MonitorCycleResult
from app.main import main, print_history_review, print_latest_database_review
from app.scheduler import NoOpScheduler


class MainTests(unittest.TestCase):
    """Verify the demo bootstrap stays runnable."""

    @staticmethod
    def _today_batch_stamp() -> str:
        return datetime.now().strftime("%Y%m%d")

    def test_main_does_not_register_scheduler_jobs_by_default(self) -> None:
        scheduler = Mock()
        scheduler.shutdown = Mock()
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.build_scheduler", return_value=scheduler),
                patch("app.main.register_default_jobs") as register_jobs,
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main()

            register_jobs.assert_not_called()
            scheduler.shutdown.assert_not_called()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_registers_scheduler_jobs_when_enabled(self) -> None:
        scheduler = Mock(start=Mock(), shutdown=Mock())
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_ENABLE_SCHEDULER": "true",
                    },
                    clear=False,
                ),
                patch("app.main.build_scheduler", return_value=scheduler),
                patch("app.main.register_default_jobs") as register_jobs,
                patch("app.main.run_scheduler_loop", return_value="Scheduler stopped."),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["run-scheduler"])

            register_jobs.assert_called_once()
            output = stdout.getvalue()
            self.assertIn("监控命令", output)
            self.assertIn("模式：run-scheduler", output)
            self.assertIn("Task Overview", output)
            self.assertIn(
                "Scheduled timings: pre-open-check (09:15), morning-check (09:35), midday-check (11:30), afternoon-review (14:45)",
                output,
            )
            self.assertIn("Scheduler Status", output)
            self.assertIn("Runtime mode: scheduler-ready", output)
            self.assertIn("Scheduler mode enabled.", output)
            self.assertLess(output.index("Task Overview"), output.index("Scheduler Status"))
            scheduler.shutdown.assert_not_called()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_scheduler_status_shows_disabled_flag(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.build_scheduler", return_value=NoOpScheduler()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["scheduler-status"])

            output = stdout.getvalue()
            self.assertIn("Scheduler enabled: no", output)
            self.assertIn("Database: sqlite:///", output)
            self.assertIn("Runtime mode: fallback-noop", output)
            self.assertIn("pip install -r requirements.txt", output)
            self.assertIn(
                "Next recommended command: pip install -r requirements.txt",
                output,
            )
            self.assertIn("pre-open-check", output)
            self.assertIn("morning-check", output)
            self.assertIn("midday-check", output)
            self.assertIn("afternoon-review", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_scheduler_status_shows_enabled_flag(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_ENABLE_SCHEDULER": "true",
                    },
                    clear=False,
                ),
                patch("app.main.build_scheduler", return_value=Mock(start=Mock(), shutdown=Mock())),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["scheduler-status"])

            output = stdout.getvalue()
            self.assertIn("Scheduler enabled: yes", output)
            self.assertIn("Database: sqlite:///", output)
            self.assertIn("Runtime mode: scheduler-ready", output)
            self.assertIn(
                "Next recommended command: python -m app.main run-scheduler",
                output,
            )
            self.assertIn(
                "Scheduled timings: pre-open-check (09:15), morning-check (09:35), midday-check (11:30), afternoon-review (14:45)",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_task_profiles_prints_validation_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-task-profiles"])

            output = stdout.getvalue()
            self.assertIn("Task Profile Validation", output)
            self.assertIn("Status: ok", output)
            self.assertIn("Scheduled job count: 4", output)
            self.assertIn("Scheduled jobs: pre-open-check, morning-check, midday-check, afternoon-review", output)
            self.assertIn(
                "Scheduled job labels: pre-open-check = Pre-open Check, morning-check = Morning Check, midday-check = Midday Check, afternoon-review = Afternoon Review",
                output,
            )
            self.assertIn(
                "Scheduled timings: pre-open-check (09:15), morning-check (09:35), midday-check (11:30), afternoon-review (14:45)",
                output,
            )
            self.assertIn(
                "Result summary styles: full_monitor, pre_open, morning_check, midday_check, afternoon_review",
                output,
            )
            self.assertIn("Manual preview jobs: manual", output)
            self.assertIn(
                "Scheduled day-flow jobs: pre-open-check, morning-check, midday-check, afternoon-review",
                output,
            )
            self.assertIn("Manual Preview: manual", output)
            self.assertIn(
                "Scheduled Day Flow: pre-open-check, morning-check, midday-check, afternoon-review",
                output,
            )
            self.assertIn("view-mode: Opening Task View (opening_task_view)", output)
            self.assertIn(
                "view-summary: Emphasize opening risk, theme confirmation, and early alert reading.",
                output,
            )
            self.assertIn(
                "view-mode: Close Review View (close_review_task_view)",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_run_job_now_executes_scheduler_job_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-06-20 10:00:00",
            quote_source="demo-fallback",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[],
            alerts=[],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_job", return_value=cycle_result) as run_job,
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["run-job-now"])

            run_job.assert_called_once()
            output = stdout.getvalue()
            self.assertIn("监控命令", output)
            self.assertIn("模式：run-job-now", output)
            self.assertIn("View mode: Manual Full View (manual_full_view)", output)
            self.assertIn("AI 半导体监控", output)
            self.assertIn("焦点：全流程本地监控", output)
            self.assertIn("结果：", output)
            self.assertIn("Morning report body", output)
            self.assertIn("Evening report body", output)
            self.assertIn("Manual scheduler job completed.", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_run_job_now_can_preview_morning_check_profile(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-06-20 10:00:00",
            quote_source="demo-fallback",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[],
            alerts=[],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_job", return_value=cycle_result) as run_job,
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["run-job-now", "morning-check"])

            run_job.assert_called_once_with(unittest.mock.ANY, job_id="morning-check")
            output = stdout.getvalue()
            self.assertIn("View mode: Opening Task View (opening_task_view)", output)
            self.assertIn("开盘检查", output)
            self.assertIn("焦点：开盘风险与题材确认", output)
            self.assertIn("结果：", output)
            self.assertIn("Morning report body", output)
            self.assertNotIn("Evening report body", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_run_job_now_can_preview_pre_open_check_profile(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-06-20 10:00:00",
            quote_source="demo-fallback",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[],
            alerts=[
                {
                    "alert_type": "news_flash",
                    "level": "绾㈣壊",
                    "direction": "\u534a\u5bfc\u4f53\u8bbe\u5907",
                    "message": "\u51fa\u53e3\u7ba1\u5236\u5347\u7ea7",
                }
            ],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_job", return_value=cycle_result) as run_job,
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["run-job-now", "pre-open-check"])

            run_job.assert_called_once_with(unittest.mock.ANY, job_id="pre-open-check")
            output = stdout.getvalue()
            self.assertIn("View mode: Pre-open View (pre_open_view)", output)
            self.assertIn("盘前检查", output)
            self.assertIn("焦点：盘前准备与隔夜风险扫描", output)
            self.assertIn("结果：", output)
            self.assertIn("Morning report body", output)
            self.assertNotIn("Intraday Alert Digest", output)
            self.assertNotIn("Evening report body", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_run_job_now_can_preview_midday_check_profile(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-06-20 10:00:00",
            quote_source="demo-fallback",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[],
            alerts=[
                {
                    "alert_type": "sector_move",
                    "level": "姗欒壊",
                    "direction": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "message": "\u677f\u5757\u5f02\u52a8",
                }
            ],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_job", return_value=cycle_result) as run_job,
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["run-job-now", "midday-check"])

            run_job.assert_called_once_with(unittest.mock.ANY, job_id="midday-check")
            output = stdout.getvalue()
            self.assertIn(
                "View mode: Mid-session Task View (mid_session_task_view)",
                output,
            )
            self.assertIn("盘中检查", output)
            self.assertIn("焦点：盘中扩散与广度检查", output)
            self.assertIn("结果：", output)
            self.assertNotIn("Morning report body", output)
            self.assertNotIn("Evening report body", output)
            self.assertIn("Intraday Alert Digest", output)
            self.assertIn("\u677f\u5757\u5f02\u52a8", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_falls_back_to_demo_rows_when_realtime_quotes_are_unavailable(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main()

            output = stdout.getvalue()
            snapshots = fetch_market_snapshots(database_path)
            alerts = fetch_alerts(database_path)

            self.assertTrue(database_path.exists())
            self.assertIn("监控命令", output)
            self.assertIn("模式：demo", output)
            self.assertIn("AI 半导体监控", output)
            self.assertIn(
                "行情来源：demo-fallback (built-in demo data)",
                output,
            )
            self.assertGreaterEqual(len(snapshots), 6)
            self.assertGreaterEqual(len(alerts), 1)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_prefers_realtime_quotes_when_available(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        realtime_frame = pd.DataFrame(
            [
                {
                    "code": "688549",
                    "name": "\u4e2d\u5de8\u82afU",
                    "price": 12.34,
                    "pct_chg": 8.6,
                    "turnover": 800.0,
                    "volume_ratio": 2.8,
                    "turnover_rate": 5.5,
                    "pe_dynamic": None,
                    "pb": None,
                    "total_market_cap": None,
                    "float_market_cap": None,
                },
                {
                    "code": "688268",
                    "name": "\u534e\u7279\u6c14\u4f53",
                    "price": 45.20,
                    "pct_chg": 5.2,
                    "turnover": 500.0,
                    "volume_ratio": 1.9,
                    "turnover_rate": 3.2,
                    "pe_dynamic": None,
                    "pb": None,
                    "total_market_cap": None,
                    "float_market_cap": None,
                },
            ]
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=realtime_frame),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main()

            output = stdout.getvalue()
            snapshots = fetch_market_snapshots(database_path)

            self.assertIn("监控命令", output)
            self.assertIn("模式：demo", output)
            self.assertIn("行情来源：akshare (live adapter)", output)
            self.assertEqual(2, len(snapshots))
            self.assertEqual("688549", snapshots[0]["code"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_can_append_latest_database_review_when_enabled(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_AUTO_LATEST_REVIEW": "true",
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main()

            output = stdout.getvalue()

            self.assertIn("最新数据库复盘", output)
            self.assertIn("AI 半导体监控", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_print_latest_database_review_outputs_database_backed_report(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main()

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                print_latest_database_review(database_path)

            output = stdout.getvalue()
            self.assertIn("复盘阅读提示", output)
            self.assertIn(
                "最佳阅读时机：先运行 python -m app.main start-daily-news-workflow",
                output,
            )
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a", output)
            self.assertIn("AI + \u534a\u5bfc\u4f53\u6536\u76d8\u590d\u76d8", output)
            self.assertIn("\u6700\u5f3a\u65b9\u5411\uff1a", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_print_latest_database_review_on_empty_database_shows_first_run_hint(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                print_latest_database_review(database_path)

            output = stdout.getvalue()
            self.assertIn("复盘阅读提示", output)
            self.assertIn(
                "最佳阅读时机：先运行 python -m app.main start-daily-news-workflow",
                output,
            )
            self.assertIn("最新数据库复盘", output)
            self.assertIn("暂无已保存的监控批次。", output)
            self.assertIn("请先运行 `python -m app.main`", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_print_history_review_outputs_selected_batch_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main()

            latest_timestamp = fetch_market_snapshots(database_path)[-1]["timestamp"]

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                print_history_review(database_path, latest_timestamp)

            output = stdout.getvalue()
            self.assertIn("\u65f6\u95f4\u6279\u6b21\uff1a", output)
            self.assertIn("\u5feb\u7167\u6570\u91cf\uff1a", output)
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u89c2\u5bdf", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_with_latest_review_mode_prints_database_review(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main()

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                main(["latest-review"])

            output = stdout.getvalue()
            self.assertIn("复盘阅读提示", output)
            self.assertIn(
                "最佳阅读时机：先运行 python -m app.main start-daily-news-workflow",
                output,
            )
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a", output)
            self.assertIn("AI + \u534a\u5bfc\u4f53\u6536\u76d8\u590d\u76d8", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_with_latest_morning_review_mode_prints_database_review(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-29 09:31:00",
                        "code": "000001",
                        "name": "Alpha",
                        "price": 11.2,
                        "pct_chg": 6.1,
                        "turnover": 120.0,
                        "volume_ratio": 2.2,
                        "turnover_rate": 3.4,
                        "sector": "Materials",
                    }
                ],
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["latest-morning-review"])

            output = stdout.getvalue()
            self.assertIn("\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a", output)
            self.assertIn("\u3010\u4eca\u65e5\u4e3b\u7ebf\u5224\u65ad\u3011", output)
            self.assertIn("Alpha", output)
            self.assertIn("Materials", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_with_history_review_mode_prints_selected_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main()

            latest_timestamp = fetch_market_snapshots(database_path)[-1]["timestamp"]

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                main(["history-review", latest_timestamp])

            output = stdout.getvalue()
            self.assertIn("\u65f6\u95f4\u6279\u6b21\uff1a", output)
            self.assertIn(latest_timestamp, output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_with_history_review_mode_on_empty_database_shows_batch_hint(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)

            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                main(["history-review", "2026-07-15 09:35:00"])

            output = stdout.getvalue()
            self.assertIn("\u65f6\u95f4\u6279\u6b21\uff1a2026-07-15 09:35:00", output)
            self.assertIn("\u672a\u627e\u5230\u5bf9\u5e94\u5feb\u7167\u6570\u636e\u3002", output)
            self.assertIn("\u53ef\u5148\u8fd0\u884c `python -m app.main`", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


    def test_main_validate_stock_pool_prints_validation_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600300","name":"校验股","sector":"校验板块","sub_sector":"子方向","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Stock Pool Validation", output)
            self.assertIn("Status Summary", output)
            self.assertIn("Structure Summary", output)
            self.assertIn("Detailed Validation", output)
            self.assertIn("Status: valid", output)
            self.assertIn("Record count: 1", output)
            self.assertIn("Structure summary:", output)
            self.assertIn("Registered sectors:", output)
            self.assertIn("Sector counts:", output)
            self.assertIn("- 校验板块: 1", output)
            self.assertIn("Chain-group counts:", output)
            self.assertIn("- none", output)
            self.assertIn("Priority counts:", output)
            self.assertIn("- P1: 1", output)
            self.assertIn(str(stock_pool_path), output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_chain_group_counts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_chain_group_counts.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                (
                    '[{"code":"600306","name":"Alpha","monitor_sector":"半导体材料",'
                    '"sub_sector":"硅片","chain_group":"材料","priority":1,"notes":""},'
                    '{"code":"600307","name":"Beta","monitor_sector":"半导体气体",'
                    '"sub_sector":"电子特气","chain_group":"气体","priority":1,"notes":""}]'
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Chain-group counts:", output)
            self.assertIn("- 材料: 1", output)
            self.assertIn("- 气体: 1", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_sorts_structure_counts_by_weight(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_sorted_counts.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                (
                    '[{"code":"600320","name":"Alpha","monitor_sector":"半导体材料",'
                    '"sub_sector":"硅片","chain_group":"材料","pool_type":"core","priority":2,"notes":""},'
                    '{"code":"600321","name":"Beta","monitor_sector":"半导体材料",'
                    '"sub_sector":"前驱体","chain_group":"材料","pool_type":"core","priority":1,"notes":""},'
                    '{"code":"600322","name":"Gamma","monitor_sector":"半导体气体",'
                    '"sub_sector":"电子特气","chain_group":"气体","pool_type":"extended","priority":2,"notes":""}]'
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertLess(
                output.index("- 半导体材料: 2"),
                output.index("- 半导体气体: 1"),
            )
            self.assertLess(
                output.index("- 材料: 2"),
                output.index("- 气体: 1"),
            )
            self.assertLess(
                output.index("- core: 2"),
                output.index("- extended: 1"),
            )
            self.assertLess(
                output.index("- P2: 2"),
                output.index("- P1: 1"),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_structure_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_structure_summary.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                (
                    '[{"code":"600308","name":"Alpha","monitor_sector":"半导体材料",'
                    '"sub_sector":"硅片","chain_group":"材料","pool_type":"core","priority":1,"notes":""},'
                    '{"code":"600309","name":"Beta","monitor_sector":"半导体气体",'
                    '"sub_sector":"电子特气","chain_group":"气体","pool_type":"extended","priority":2,"notes":""}]'
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Structure summary:", output)
            self.assertIn("当前监控池偏向材料链", output)
            self.assertIn("core池占比约为1/2", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_structure_comparison(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_structure_comparison.json"
        snapshot_path = temp_dir / "stock_pool_health_snapshot.json"
        database_path = temp_dir / "monitor.db"
        baseline_records = [
            {
                "code": "600430",
                "name": "Alpha",
                "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                "sub_sector": "\u7845\u7247",
                "chain_group": "\u6750\u6599",
                "pool_type": "core",
                "priority": 1,
                "notes": "",
            },
            {
                "code": "600431",
                "name": "Beta",
                "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                "sub_sector": "\u7535\u5b50\u7279\u6c14",
                "chain_group": "\u6c14\u4f53",
                "pool_type": "extended",
                "priority": 2,
                "notes": "",
            },
        ]
        changed_records = [
            {
                "code": "600430",
                "name": "Alpha",
                "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                "sub_sector": "\u7845\u7247",
                "chain_group": "\u6750\u6599",
                "pool_type": "core",
                "priority": 1,
                "notes": "",
            },
            {
                "code": "600432",
                "name": "Gamma",
                "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                "sub_sector": "\u524d\u9a71\u4f53",
                "chain_group": "\u6750\u6599",
                "pool_type": "extended",
                "priority": 2,
                "notes": "",
            },
        ]
        try:
            stock_pool_path.write_text(
                json.dumps(baseline_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main(["validate-stock-pool"])

            stock_pool_path.write_text(
                json.dumps(changed_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Structure Comparison", output)
            self.assertIn(f"Snapshot path: {snapshot_path}", output)
            self.assertIn("Change tags:", output)
            self.assertIn("Change groups:", output)
            self.assertIn("\u4f18\u5148\u7ea7\u7126\u70b9: \u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d", output)
            self.assertIn("\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d", output)
            self.assertIn("Change highlight:", output)
            self.assertIn("\u91cd\u70b9\u53d8\u5316", output)
            self.assertIn("\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316", output)
            self.assertIn("Top structure changes:", output)
            self.assertIn("- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +1", output)
            self.assertIn("- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599: +1", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


    def test_main_validate_stock_pool_includes_health_hints_section(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600301","name":"Alpha","sector":"Only-Sector","sub_sector":"Branch-A","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Health hints:", output)
            self.assertIn("Sector coverage is narrow", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_chain_group_concentration_hint(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_chain_group_concentration.json"
        database_path = temp_dir / "monitor.db"
        try:
            records = [
                {
                    "code": f"6015{i:02d}",
                    "name": f"Name-{i}",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": f"Branch-{i}",
                    "chain_group": "\u6750\u6599",
                    "priority": 1 if i == 0 else 2,
                    "notes": "",
                }
                for i in range(7)
            ]
            records.extend(
                [
                    {
                        "code": "601580",
                        "name": "Edge-1",
                        "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                        "sub_sector": "\u7535\u5b50\u7279\u6c14",
                        "chain_group": "\u6c14\u4f53",
                        "priority": 2,
                        "notes": "",
                    },
                    {
                        "code": "601581",
                        "name": "Edge-2",
                        "monitor_sector": "\u534a\u5bfc\u4f53\u8bbe\u5907",
                        "sub_sector": "\u523b\u8680",
                        "chain_group": "\u8bbe\u5907",
                        "priority": 2,
                        "notes": "",
                    },
                ]
            )
            stock_pool_path.write_text(
                json.dumps(records, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Chain-group concentration is high", output)
            self.assertIn("\u6750\u6599 holds 7/9 stocks", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_unknown_sector_warning(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600302","name":"Alpha","monitor_sector":"半导体材科","sub_sector":"硅片","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Unknown sectors: 半导体材科", output)
            self.assertIn("Unknown monitor sectors detected", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_possible_sector_match(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_match.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600303","name":"Alpha","monitor_sector":"半导体材科","sub_sector":"硅片","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Possible matches:", output)
            self.assertIn("半导体材科 -> 半导体材料", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_possible_chain_group_match(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_chain_group_match.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600304","name":"Alpha","monitor_sector":"半导体材料","sub_sector":"硅片","chain_group":"材科","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Unknown chain groups: 材科", output)
            self.assertIn("Possible chain-group matches:", output)
            self.assertIn("材科 -> 材料", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_stock_pool_prints_possible_market_and_pool_type_match(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "stock_pool_market_pool_type_match.json"
        database_path = temp_dir / "monitor.db"
        try:
            stock_pool_path.write_text(
                '[{"code":"600305","name":"Alpha","monitor_sector":"半导体材料","sub_sector":"硅片","market":"沪B","pool_type":"cores","priority":1,"notes":""}]',
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                        "MONITOR_DATABASE_PATH": str(database_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-stock-pool"])

            output = stdout.getvalue()
            self.assertIn("Unknown markets: 沪B", output)
            self.assertIn("Possible market matches:", output)
            self.assertIn("沪B -> 沪A", output)
            self.assertIn("Unknown pool types: cores", output)
            self.assertIn("Possible pool-type matches:", output)
            self.assertIn("cores -> core", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_help_prints_command_guide(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["help"])

            output = stdout.getvalue()
            self.assertIn("AI 半导体监控命令", output)
            self.assertIn("日常使用：", output)
            self.assertIn("成功信号：", output)
            self.assertIn("最小可运行检查：", output)
            self.assertIn("批量新闻速查：", output)
            self.assertIn("完整命令目录：", output)
            self.assertIn("先确认本地主线是否可用", output)
            self.assertIn("python -m app.main create-daily-news-batch", output)
            self.assertIn("python -m app.main self-check", output)
            self.assertIn("python -m app.main mainline-smoke-test", output)
            self.assertIn("python -m app.main full-regression-check", output)
            self.assertIn("python -m app.main quote-connectivity-check", output)
            self.assertIn("python -m app.main create-local-quote-template", output)
            self.assertIn("python -m app.main refresh-local-quote-snapshot", output)
            self.assertIn("python -m app.main refresh-local-quote-pass-check", output)
            self.assertIn("python -m app.main validate-local-quote", output)
            self.assertIn("python -m app.main import-local-quote-pass-check", output)
            self.assertIn("python -m app.main start-daily-news-workflow", output)
            self.assertIn("python -m app.main latest-review", output)
            self.assertIn("主流程：ok", output)
            self.assertIn("真实数据状态：live-pass 或 snapshot-pass", output)
            self.assertIn("股票池校验：valid", output)
            self.assertIn("今日摘要文件：", output)
            self.assertIn("已保存优先级摘要到：", output)
            self.assertIn("可选可视化页面", output)
            self.assertIn(
                'python -m app.main create-news-batch-template "news_batch.json"',
                output,
            )
            self.assertIn('python -m app.main validate-news-batch "news_batch.json"', output)
            self.assertIn('python -m app.main news-batch-first-pass "news_batch.json"', output)
            self.assertIn('python -m app.main news-batch-priority-pass "news_batch.json"', output)
            self.assertIn('python -m app.main news-batch-priority-export "news_batch.json"', output)
            self.assertIn('python -m app.main batch-news-daily-flow "news_batch.json"', output)
            self.assertIn('python -m app.main batch-news-daily-export "news_batch.json"', output)
            self.assertIn("可把 news_batch.example.json 复制为 news_batch.json", output)
            self.assertIn(
                "首次运行时，把 news_batch.json 放在项目根目录最省事",
                output,
            )
            self.assertIn(
                "如果文件在其他位置，直接传完整路径",
                output,
            )
            self.assertIn(
                "通用 export-news-batch 默认保存到源文件旁边",
                output,
            )
            self.assertIn("python -m app.main", output)
            self.assertIn('python -m app.main classify-news "title" "content"', output)
            self.assertIn('python -m app.main classify-news-batch "news_batch.json"', output)
            self.assertIn(
                'python -m app.main classify-news-batch "news_batch.json" high-priority-only',
                output,
            )
            self.assertIn(
                'python -m app.main classify-news-batch "news_batch.json" summary-only',
                output,
            )
            self.assertIn(
                'python -m app.main export-news-batch "news_batch.json" "news_batch_summary.md"',
                output,
            )
            self.assertIn(
                'python -m app.main export-news-batch "news_batch.json"',
                output,
            )
            self.assertIn("python -m app.main self-check", output)
            self.assertIn("python -m app.main latest-review", output)
            self.assertIn("python -m app.main latest-morning-review", output)
            self.assertIn("python -m app.main validate-stock-pool", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_local_quote_template_writes_default_shape_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        template_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(template_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-local-quote-template"])

            output = stdout.getvalue()
            self.assertIn("本地行情快照模板", output)
            self.assertIn(f"保存到：{template_path}", output)
            self.assertIn("结构：rows-array", output)
            self.assertTrue(template_path.exists())
            loaded = json.loads(template_path.read_text(encoding="utf-8"))
            example_payload = json.loads(
                Path("data/examples/real_quote_sample.json").read_text(encoding="utf-8")
            )
            self.assertIn("rows", loaded)
            self.assertEqual(3, len(loaded["rows"]))
            self.assertEqual("中巨芯-U", loaded["rows"][0]["name"])
            self.assertEqual("沪硅产业", loaded["rows"][1]["name"])
            self.assertEqual("北方华创", loaded["rows"][2]["name"])
            self.assertEqual(example_payload, loaded)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_quote_reports_missing_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-quote"])

            output = stdout.getvalue()
            self.assertIn("本地行情快照校验", output)
            self.assertIn("状态：缺失", output)
            self.assertIn("create-local-quote-template", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_quote_reports_valid_snapshot(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(
                json.dumps(
                    {
                        "rows": [
                            {"code": "688549", "name": "中巨芯-U", "price": 12.34},
                            {"code": "688126", "name": "沪硅产业", "price": 19.99},
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-quote"])

            output = stdout.getvalue()
            self.assertIn("本地行情快照校验", output)
            self.assertIn("结构：rows-array", output)
            self.assertIn("状态：有效", output)
            self.assertIn("行数：2", output)
            self.assertIn("第一只代码：688549", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_quote_snapshot_writes_live_rows_into_runtime_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        live_quotes = pd.DataFrame(
            [
                {"code": "688549", "name": "中巨芯-U", "price": 12.34},
                {"code": "688126", "name": "沪硅产业", "price": 19.99},
            ]
        )
        live_quotes.attrs["quote_source"] = "eastmoney-direct"
        live_quotes.attrs["fetch_path"] = "eastmoney-market-powershell"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("app.main.fetch_realtime_quotes", return_value=live_quotes),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-quote-snapshot"])

            output = stdout.getvalue()
            self.assertIn("刷新本地行情快照", output)
            self.assertIn(f"保存到：{snapshot_path}", output)
            self.assertIn("行数：2", output)
            self.assertIn("行情来源：eastmoney-direct (live direct endpoint)", output)
            self.assertIn("直连路径：eastmoney-market-powershell", output)
            self.assertIn("真实数据状态：live-pass", output)
            self.assertTrue(snapshot_path.exists())
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual("688549", payload["rows"][0]["code"])
            self.assertEqual("中巨芯-U", payload["rows"][0]["name"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_quote_snapshot_reports_failure_when_live_fetch_is_empty(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("app.main.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-quote-snapshot"])

            output = stdout.getvalue()
            self.assertIn("刷新本地行情快照", output)
            self.assertIn("状态：受阻", output)
            self.assertIn("结果：实时行情刷新未通过。", output)
            self.assertIn("quote-connectivity-check", output)
            self.assertFalse(snapshot_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_quote_pass_check_runs_refresh_validate_and_self_check(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        live_quotes = pd.DataFrame(
            [
                {
                    "code": "688549",
                    "name": "中巨芯-U",
                    "price": 12.34,
                    "pct_chg": 8.6,
                    "turnover": 123456789,
                    "volume_ratio": 2.3,
                    "turnover_rate": 4.5,
                },
                {
                    "code": "688126",
                    "name": "沪硅产业",
                    "price": 19.99,
                    "pct_chg": 3.5,
                    "turnover": 987654321,
                    "volume_ratio": 1.8,
                    "turnover_rate": 3.2,
                },
            ]
        )
        live_quotes.attrs["quote_source"] = "eastmoney-direct"
        live_quotes.attrs["fetch_path"] = "eastmoney-market-powershell"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("app.main.fetch_realtime_quotes", return_value=live_quotes),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-quote-pass-check"])

            output = stdout.getvalue()
            self.assertIn("刷新本地行情一体化检查", output)
            self.assertIn("步骤 1：刷新", output)
            self.assertIn("步骤 2：校验", output)
            self.assertIn("步骤 3：自检", output)
            self.assertIn("结果：本地真实行情刷新路径已通过。", output)
            self.assertIn("真实数据状态：snapshot-pass", output)
            self.assertIn("行情来源：local-json-snapshot (local real quote snapshot)", output)
            self.assertIn(f'下一步：python -m app.main validate-local-quote "{snapshot_path}"', output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_quote_pass_check_reports_refresh_failure(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        snapshot_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path),
                    },
                    clear=False,
                ),
                patch("app.main.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-quote-pass-check"])

            output = stdout.getvalue()
            self.assertIn("刷新本地行情一体化检查", output)
            self.assertIn("结果：实时刷新未通过。", output)
            self.assertIn("失败原因：实时行情刷新没有返回可用行", output)
            self.assertIn("quote-connectivity-check", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_requires_source_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote"])

            output = stdout.getvalue()
            self.assertIn("导入本地行情快照", output)
            self.assertIn("未提供源文件。", output)
            self.assertIn("用法：python -m app.main import-local-quote", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_requires_source_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check"])

            output = stdout.getvalue()
            self.assertIn("导入本地行情一体化检查", output)
            self.assertIn("未提供源文件。", output)
            self.assertIn("结果：源文件导入未通过。", output)
            self.assertIn("失败原因：缺少源文件", output)
            self.assertIn(
                "用法：python -m app.main import-local-quote-pass-check",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_reports_invalid_source_format(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        try:
            source_path.write_text(
                json.dumps({"unexpected": [{"bad": "shape"}]}, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check", str(source_path)])

            output = stdout.getvalue()
            self.assertIn("导入本地行情一体化检查", output)
            self.assertIn("导入本地行情快照", output)
            self.assertIn("状态：源文件无效", output)
            self.assertIn("结果：源文件导入未通过。", output)
            self.assertIn(
                "失败原因：源 JSON 格式不符合支持的本地行情结构",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_normalizes_external_payload_into_runtime_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        target_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            source_path.write_text(
                json.dumps(
                    {
                        "data": {
                            "diff": [
                                {"f12": "688549", "f14": "中巨芯-U", "f2": 12.34, "f3": 8.6},
                                {"f12": "688126", "f14": "沪硅产业", "f2": 19.99, "f3": 3.5},
                            ]
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(target_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote", str(source_path)])

            output = stdout.getvalue()
            self.assertIn("导入本地行情快照", output)
            self.assertIn(f"源文件：{source_path}", output)
            self.assertIn(f"保存到：{target_path}", output)
            self.assertIn("保存结构：rows-array", output)
            self.assertIn("行数：2", output)
            self.assertTrue(target_path.exists())
            loaded = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertIn("rows", loaded)
            self.assertEqual("688549", loaded["rows"][0]["code"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_runs_import_validate_and_self_check(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        target_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            source_path.write_text(
                json.dumps(
                    {
                        "data": {
                            "diff": [
                                {
                                    "f12": "688549",
                                    "f14": "中巨芯-U",
                                    "f2": 12.34,
                                    "f3": 8.6,
                                    "f6": 123456789,
                                    "f8": 2.3,
                                    "f10": 4.5,
                                },
                                {
                                    "f12": "688126",
                                    "f14": "沪硅产业",
                                    "f2": 19.99,
                                    "f3": 3.5,
                                    "f6": 987654321,
                                    "f8": 1.8,
                                    "f10": 3.2,
                                },
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            realtime_quotes = pd.DataFrame(
                [
                    {
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.34,
                        "pct_chg": 8.6,
                        "turnover": 123456789,
                        "volume_ratio": 2.3,
                        "turnover_rate": 4.5,
                    },
                    {
                        "code": "688126",
                        "name": "沪硅产业",
                        "price": 19.99,
                        "pct_chg": 3.5,
                        "turnover": 987654321,
                        "volume_ratio": 1.8,
                        "turnover_rate": 3.2,
                    },
                ]
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(target_path),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=realtime_quotes),
                patch(
                    "app.pipeline.get_quote_source",
                    return_value="local-json-snapshot",
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check", str(source_path)])

            output = stdout.getvalue()
            self.assertIn("导入本地行情一体化检查", output)
            self.assertIn("步骤 1：导入", output)
            self.assertIn("步骤 2：校验", output)
            self.assertIn("步骤 3：自检", output)
            self.assertIn("导入本地行情快照", output)
            self.assertIn("本地行情快照校验", output)
            self.assertIn("最小可运行自检", output)
            self.assertIn("真实数据状态：snapshot-pass", output)
            self.assertIn("结果：本地真实数据路径已就绪。", output)
            self.assertIn("下一步：python -m app.main start-daily-news-workflow", output)
            self.assertTrue(target_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_reports_demo_fallback_after_import(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        target_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            source_path.write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "code": "688549",
                                "name": "中巨芯-U",
                                "price": 12.34,
                                "pct_chg": 8.6,
                                "turnover": 123456789,
                                "volume_ratio": 2.3,
                                "turnover_rate": 4.5,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(target_path),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check", str(source_path)])

            output = stdout.getvalue()
            self.assertIn("步骤 1：导入", output)
            self.assertIn("步骤 2：校验", output)
            self.assertIn("步骤 3：自检", output)
            self.assertIn("真实数据状态：not-passed (still on demo fallback)", output)
            self.assertIn("结果：本地真实数据路径仍需检查。", output)
            self.assertIn(
                "失败原因：导入成功，但自检仍回落到演示数据",
                output,
            )
            self.assertIn(
                "运行时诊断：runtime snapshot is valid and matches the monitored stock pool, but the active quote fetch path still returned no rows.",
                output,
            )
            self.assertIn(
                f'下一步：python -m app.main validate-local-quote "{target_path}"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_reports_zero_row_snapshot_diagnosis(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        target_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            source_path.write_text(
                json.dumps({"rows": []}, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(target_path),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check", str(source_path)])

            output = stdout.getvalue()
            self.assertIn(
                "运行时诊断：runtime snapshot loaded, but it currently contains 0 rows.",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_import_local_quote_pass_check_reports_unmatched_stock_pool_diagnosis(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        source_path = temp_dir / "external_quotes.json"
        target_path = temp_dir / "runtime" / "latest_quotes.json"
        try:
            source_path.write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "code": "000001",
                                "name": "平安银行",
                                "price": 11.11,
                                "pct_chg": 0.2,
                                "turnover": 123456789,
                                "volume_ratio": 1.0,
                                "turnover_rate": 2.0,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_LOCAL_QUOTE_PATH": str(target_path),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["import-local-quote-pass-check", str(source_path)])

            output = stdout.getvalue()
            self.assertIn(
                "运行时诊断：runtime snapshot loaded, but 0 rows matched the current monitored stock pool.",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_self_check_runs_minimal_acceptance_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["self-check"])

            output = stdout.getvalue()
            self.assertIn("最小可运行自检", output)
            self.assertIn("主流程：ok", output)
            self.assertIn(
                "真实数据状态：not-passed (still on demo fallback)",
                output,
            )
            self.assertIn("最新复盘：ok", output)
            self.assertIn("股票池校验：valid", output)
            self.assertIn(
                "行情来源：demo-fallback (built-in demo data)",
                output,
            )
            self.assertIn(
                "建议诊断：先运行 python -m app.main validate-local-quote。若本地快照有效，再运行 python -m app.main quote-connectivity-check。",
                output,
            )
            self.assertIn("下一步：python -m app.main validate-local-quote", output)
            self.assertIn(
                "可选可视化页面：streamlit run app/dashboard/streamlit_app.py",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_self_check_prefers_news_workflow_after_snapshot_pass(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-07-19 10:00:00",
            quote_source="local-json-snapshot",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[{"code": "688549"}],
            alerts=[],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_cycle", return_value=cycle_result),
                patch("app.main.build_stock_pool_health_summary", return_value={"status": "valid"}),
                patch("app.main.build_stock_pool_health_comparison", return_value={}),
                patch("app.main.save_stock_pool_health_snapshot"),
                patch("app.main._build_latest_database_review_text", return_value="最新数据库复盘\n\nok"),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["self-check"])

            output = stdout.getvalue()
            self.assertIn("真实数据状态：snapshot-pass", output)
            self.assertIn(
                "建议诊断：本地真实行情快照路径已通过，继续运行 python -m app.main start-daily-news-workflow。",
                output,
            )
            self.assertNotIn("quote-connectivity-check", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_self_check_shows_direct_path_when_live_path_is_present(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        cycle_result = MonitorCycleResult(
            snapshot_time="2026-07-19 10:05:00",
            quote_source="eastmoney-direct",
            fetch_path="eastmoney-market-powershell",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[{"code": "688549"}],
            alerts=[],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_monitor_cycle", return_value=cycle_result),
                patch("app.main.build_stock_pool_health_summary", return_value={"status": "valid"}),
                patch("app.main.build_stock_pool_health_comparison", return_value={}),
                patch("app.main.save_stock_pool_health_snapshot"),
                patch("app.main._build_latest_database_review_text", return_value="最新数据库复盘\n\nok"),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["self-check"])

            output = stdout.getvalue()
            self.assertIn("行情来源：eastmoney-direct (live direct endpoint)", output)
            self.assertIn("直连路径：eastmoney-market-powershell", output)
            self.assertIn("真实数据状态：live-pass", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_prints_alert_preview_for_s_level_risk(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(
                    [
                        "classify-news",
                        "半导体设备出口管制升级",
                        "刻蚀设备与薄膜沉积环节承压。",
                    ]
                )

            output = stdout.getvalue()
            self.assertIn("新闻分类", output)
            self.assertIn("情绪：negative", output)
            self.assertIn("级别：S", output)
            self.assertIn("相关板块：半导体设备", output)
            self.assertIn("链条提示：偏半导体设备链", output)
            self.assertIn("影响判断：更偏风险扩散", output)
            self.assertIn("预警预览：news_flash", output)
            self.assertIn("预警级别：红色", output)
            self.assertIn("结论：更偏风险扩散", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_prints_observation_suggestion_for_positive_signal(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(
                    [
                        "classify-news",
                        "中巨芯U批量供货推进",
                        "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                    ]
                )

            output = stdout.getvalue()
            self.assertIn("情绪：positive", output)
            self.assertIn("级别：A", output)
            self.assertIn("相关股票：中巨芯-U, 华特气体", output)
            self.assertIn("链条提示：偏半导体气体链", output)
            self.assertIn("影响判断：更偏主线强化", output)
            self.assertIn("建议动作：优先盯核心池", output)
            self.assertIn("结论：更偏主线强化", output)
            self.assertIn("中巨芯-U", output)
            self.assertIn("华特气体", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_can_suggest_sector_watchlist_when_no_stock_matches(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(
                    [
                        "classify-news",
                        "半导体设备出口管制升级",
                        "刻蚀设备与薄膜沉积环节承压。",
                    ]
                )

            output = stdout.getvalue()
            self.assertIn("相关股票：无", output)
            self.assertIn("影响判断：更偏风险扩散", output)
            self.assertIn("建议动作：优先盯核心池", output)
            self.assertIn("北方华创", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_prints_bottom_lines_for_multiple_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                        },
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量分类", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("新闻条数：2", output)
            self.assertIn("影响摘要：风险扩散 1 | 主线强化 1 | 局部验证 0", output)
            self.assertIn("1. 半导体设备出口管制升级", output)
            self.assertIn("结论：更偏风险扩散", output)
            self.assertIn("2. 中巨芯U批量供货推进", output)
            self.assertIn("结论：更偏主线强化", output)
            self.assertLess(
                output.index("1. 半导体设备出口管制升级"),
                output.index("2. 中巨芯U批量供货推进"),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_news_batch_reports_valid_input(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量校验", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("状态：有效", output)
            self.assertIn("新闻条数：2", output)
            self.assertIn("第一条标题：半导体设备出口管制升级", output)
            self.assertIn(
                '下一步：python -m app.main classify-news-batch "news_batch.json" summary-only',
                output,
            )
            self.assertIn(
                '可选导出：python -m app.main export-news-batch "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_news_batch_template_writes_template_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        template_path = temp_dir / "news_batch.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-news-batch-template", str(template_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量模板", output)
            self.assertIn(f"保存到：{template_path}", output)
            self.assertIn("新闻条数：3", output)
            self.assertIn(
                '下一步：python -m app.main validate-news-batch "news_batch.json"',
                output,
            )
            self.assertTrue(template_path.exists())
            loaded = json.loads(template_path.read_text(encoding="utf-8"))
            self.assertEqual(3, len(loaded))
            self.assertEqual("半导体设备出口管制升级", loaded[0]["title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_news_batch_template_requires_target_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-news-batch-template"])

            output = stdout.getvalue()
            self.assertIn("新闻批量模板", output)
            self.assertIn("未提供目标文件。", output)
            self.assertIn(
                '用法：python -m app.main create-news-batch-template "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_daily_news_batch_writes_template_to_default_daily_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        template_path = batch_dir / f"news_batch_{self._today_batch_stamp()}.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-daily-news-batch"])

            output = stdout.getvalue()
            self.assertIn("每日新闻批量模板", output)
            self.assertIn(f"保存到：{template_path}", output)
            self.assertIn("新闻条数：3", output)
            self.assertIn("默认源文件规则：data/news/news_batch_YYYYMMDD.json", output)
            self.assertIn(
                f'下一步：python -m app.main batch-news-daily-export "{template_path}"',
                output,
            )
            self.assertTrue(template_path.exists())
            loaded = json.loads(template_path.read_text(encoding="utf-8"))
            self.assertEqual(3, len(loaded))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_daily_news_batch_can_use_explicit_target_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        template_path = temp_dir / "custom" / "daily_news_batch.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-daily-news-batch", str(template_path)])

            output = stdout.getvalue()
            self.assertIn("每日新闻批量模板", output)
            self.assertIn(f"保存到：{template_path}", output)
            self.assertTrue(template_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_daily_news_batch_writes_auto_candidates(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        batch_path = batch_dir / f"news_batch_{self._today_batch_stamp()}.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-daily-news-batch"])

            output = stdout.getvalue()
            self.assertIn("刷新每日新闻批量源", output)
            self.assertIn(f"保存到：{batch_path}", output)
            self.assertIn("来源模式：自动候选", output)
            self.assertIn("新闻条数：", output)
            self.assertTrue(batch_path.exists())
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(loaded), 3)
            self.assertTrue(all(item.get("title") and item.get("content") for item in loaded))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_local_news_feed_template_writes_feed_shape(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-local-news-feed-template", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地新闻源模板", output)
            self.assertIn(f"保存到：{feed_path}", output)
            self.assertIn("环境变量：MONITOR_NEWS_FEED_PATH", output)
            self.assertIn("下一步：设置 MONITOR_NEWS_FEED_PATH 后运行 python -m app.main refresh-daily-news-batch", output)
            self.assertTrue(feed_path.exists())
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(loaded), 2)
            self.assertTrue(all(item.get("title") and item.get("content") for item in loaded))
            self.assertTrue(all(item.get("source") == "local-feed-template" for item in loaded))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_local_news_feed_template_uses_default_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_dir = temp_dir / "news_workspace"
        feed_path = feed_dir / "local_news_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(feed_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-local-news-feed-template"])

            output = stdout.getvalue()
            self.assertIn(f"保存到：{feed_path}", output)
            self.assertTrue(feed_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_news_feed_reports_valid_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地源：先进封装订单改善",
                            "content": "Chiplet和先进封装订单预期改善。",
                            "source": "manual-feed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-news-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地新闻源校验", output)
            self.assertIn(f"来源文件：{feed_path}", output)
            self.assertIn("状态：有效", output)
            self.assertIn("有效新闻条数：1", output)
            self.assertIn("第一条标题：本地源：先进封装订单改善", output)
            self.assertIn("来源分布：manual-feed 1", output)
            self.assertIn("重复标题：无", output)
            self.assertIn("下一步：设置 MONITOR_NEWS_FEED_PATH 后运行 python -m app.main refresh-daily-news-batch", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_source_status_reports_configured_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [{"title": "本地源", "content": "本地新闻正文。", "source": "manual-feed"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-source-status", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("新闻源状态", output)
            self.assertIn("状态：local-feed-ready", output)
            self.assertIn(f"本地新闻源：{feed_path}", output)
            self.assertIn("新闻条数：1", output)
            self.assertIn("来源分布：manual-feed 1", output)
            self.assertIn("下一步：python -m app.main local-news-feed-daily-pass-check", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_news_feed_reports_duplicate_title_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "重复标题",
                            "content": "第一条。",
                            "source": "manual-feed",
                        },
                        {
                            "title": "重复标题",
                            "content": "第二条。",
                            "source": "rss-feed",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-news-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("状态：有效", output)
            self.assertIn("有效新闻条数：2", output)
            self.assertIn("来源分布：manual-feed 1 | rss-feed 1", output)
            self.assertIn("重复标题：重复标题 (2)", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_news_feed_reports_item_issues(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {"title": "只有标题"},
                        {"content": "只有正文。"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-news-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地新闻源校验", output)
            self.assertIn("状态：无效", output)
            self.assertIn("第 1 条：缺少 content。", output)
            self.assertIn("第 2 条：缺少 title。", output)
            self.assertIn(
                '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_append_local_news_feed_item_creates_or_updates_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(
                    [
                        "append-local-news-feed",
                        "本地源：先进封装订单改善",
                        "Chiplet和先进封装订单预期改善。",
                        str(feed_path),
                    ]
                )

            output = stdout.getvalue()
            self.assertIn("追加本地新闻源", output)
            self.assertIn(f"保存到：{feed_path}", output)
            self.assertIn("状态：已追加", output)
            self.assertIn("新闻条数：1", output)
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertEqual("本地源：先进封装订单改善", loaded[0]["title"])
            self.assertEqual("Chiplet和先进封装订单预期改善。", loaded[0]["content"])
            self.assertEqual("local-feed-manual", loaded[0]["source"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_append_local_news_feed_item_skips_duplicate_title(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地源：先进封装订单改善",
                            "content": "旧内容。",
                            "source": "manual-feed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(
                    [
                        "append-local-news-feed",
                        "本地源：先进封装订单改善",
                        "新内容。",
                        str(feed_path),
                    ]
                )

            output = stdout.getvalue()
            self.assertIn("状态：已存在，未重复追加", output)
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertEqual(1, len(loaded))
            self.assertEqual("旧内容。", loaded[0]["content"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_news_feed_writes_remote_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_FEED_URL": "https://example.test/news.json",
                    },
                    clear=False,
                ),
                patch(
                    "app.main.fetch_remote_news_items",
                    return_value=(
                        [
                            {
                                "title": "远程源：AI服务器订单改善",
                                "content": "算力硬件链订单预期改善。",
                                "source": "remote-news-feed",
                                "source_date": "",
                            }
                        ],
                        {
                            "status": "ok",
                            "reason": "Remote news feed is readable.",
                            "next_step": "python -m app.main refresh-daily-news-batch",
                        },
                    ),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-news-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("刷新本地新闻源", output)
            self.assertIn("状态：成功", output)
            self.assertIn("写入新闻条数：1", output)
            self.assertTrue(feed_path.exists())
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertEqual("远程源：AI服务器订单改善", loaded[0]["title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_news_feed_does_not_write_on_failure(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch(
                    "app.main.fetch_remote_news_items",
                    return_value=(
                        [],
                        {
                            "status": "not-configured",
                            "reason": "No news feed URL configured.",
                            "next_step": "set MONITOR_NEWS_FEED_URL",
                        },
                    ),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-news-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("状态：未配置", output)
            self.assertIn("下一步：set MONITOR_NEWS_FEED_URL", output)
            self.assertFalse(feed_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_external_feeds_pass_check_runs_daily_chain(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                        "MONITOR_NEWS_FEED_URL": "https://example.test/news.json",
                        "MONITOR_ANNOUNCEMENT_FEED_URL": "https://example.test/announcements.json",
                    },
                    clear=False,
                ),
                patch(
                    "app.main.fetch_remote_news_items",
                    return_value=(
                        [
                            {
                                "title": "远程源：AI服务器订单改善",
                                "content": "算力硬件链订单预期改善。",
                                "source": "remote-news-feed",
                                "source_date": "",
                            }
                        ],
                        {
                            "status": "ok",
                            "reason": "Remote news feed is readable.",
                            "next_step": "python -m app.main refresh-daily-news-batch",
                        },
                    ),
                ),
                patch(
                    "app.main.fetch_remote_announcement_items",
                    return_value=(
                        [
                            {
                                "title": "公告源：半导体材料扩产进展",
                                "content": "公司公告披露材料产能扩张和客户验证进展。",
                                "source": "remote-announcement-feed",
                            }
                        ],
                        {
                            "status": "ok",
                            "reason": "Remote announcement feed is readable.",
                            "next_step": "python -m app.main start-daily-news-workflow",
                        },
                    ),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-external-feeds-pass-check"])

            output = stdout.getvalue()
            self.assertIn("外部输入源每日一体化检查", output)
            self.assertIn("步骤 1：刷新远程新闻源到本地", output)
            self.assertIn("步骤 2：刷新远程公告源到本地", output)
            self.assertIn("步骤 3：生成每日新闻批量源", output)
            self.assertIn("步骤 4：导出每日优先摘要", output)
            self.assertIn("结果：外部输入源每日流程已通过。", output)
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            loaded_titles = [item["title"] for item in loaded]
            self.assertIn("公告源：半导体材料扩产进展", loaded_titles)
            self.assertIn("远程源：AI服务器订单改善", loaded_titles)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_external_feeds_pass_check_falls_back_without_remote_urls(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        batch_path = batch_dir / f"news_batch_{self._today_batch_stamp()}.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=True,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-external-feeds-pass-check"])

            output = stdout.getvalue()
            self.assertIn("状态：未配置", output)
            self.assertIn("结果：外部输入源每日流程已通过。", output)
            self.assertTrue(batch_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_external_feeds_status_reports_fallback_ready_without_remote_urls(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=True,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["external-feeds-status"])

            output = stdout.getvalue()
            self.assertIn("外部输入源状态", output)
            self.assertIn("远程新闻 URL：未配置", output)
            self.assertIn("远程公告 URL：未配置", output)
            self.assertIn("每日流程：可运行", output)
            self.assertIn("配置结论：远程源未配置，但每日流程可用本地源或自动候选兜底。", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_external_feeds_status_reports_remote_sources_configured(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                        "MONITOR_NEWS_FEED_URL": "https://example.test/news.json",
                        "MONITOR_ANNOUNCEMENT_FEED_URL": "https://example.test/announcements.json",
                    },
                    clear=True,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["external-feeds-status"])

            output = stdout.getvalue()
            self.assertIn("远程新闻 URL：已配置", output)
            self.assertIn("远程公告 URL：已配置", output)
            self.assertIn("配置结论：外部输入源已具备自动刷新入口。", output)
            self.assertIn("下一步：python -m app.main refresh-external-feeds-pass-check", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_local_news_feed_daily_pass_check_runs_compact_chain(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        feed_path = temp_dir / "local_news_feed.json"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地源：HBM订单继续改善",
                            "content": "存储和HBM方向订单预期改善，关注核心池是否跟随。",
                            "source": "manual-feed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["local-news-feed-daily-pass-check", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地新闻源每日一体化检查", output)
            self.assertIn("步骤 1：校验本地新闻源", output)
            self.assertIn("步骤 2：刷新每日新闻批量源", output)
            self.assertIn("步骤 3：导出每日优先摘要", output)
            self.assertIn("结果：本地新闻源每日流程已通过。", output)
            self.assertIn(f"新闻批量文件：{batch_path}", output)
            self.assertIn(f"摘要文件：{export_path}", output)
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertEqual("本地源：HBM订单继续改善", loaded[0]["title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_local_news_feed_daily_pass_check_stops_on_invalid_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        feed_path = temp_dir / "local_news_feed.json"
        try:
            feed_path.write_text(
                json.dumps([{"title": "只有标题"}], ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["local-news-feed-daily-pass-check", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地新闻源每日一体化检查", output)
            self.assertIn("结果：本地新闻源校验未通过。", output)
            self.assertIn("第 1 条：缺少 content。", output)
            self.assertFalse(list(batch_dir.glob("news_batch_*.json")))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_daily_news_batch_uses_configured_local_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        feed_path = temp_dir / "local_feed.json"
        batch_path = batch_dir / f"news_batch_{self._today_batch_stamp()}.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地源：HBM订单继续改善",
                            "content": "存储和HBM方向订单预期改善，关注核心池是否跟随。",
                            "source": "manual-feed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                        "MONITOR_NEWS_FEED_PATH": str(feed_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-daily-news-batch"])

            output = stdout.getvalue()
            self.assertIn("本地新闻源 + 自动候选", output)
            self.assertIn(str(feed_path), output)
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertEqual("本地源：HBM订单继续改善", loaded[0]["title"])
            self.assertEqual("manual-feed", loaded[0]["source"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_daily_news_batch_merges_configured_announcement_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        announcement_path = temp_dir / "local_announcement_feed.json"
        batch_path = batch_dir / f"news_batch_{self._today_batch_stamp()}.json"
        try:
            announcement_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "公告源：AI服务器订单进展",
                            "content": "公司公告披露AI服务器相关订单进展，关注算力硬件链确认。",
                            "source": "company-announcement",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                        "MONITOR_ANNOUNCEMENT_FEED_PATH": str(announcement_path),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-daily-news-batch"])

            output = stdout.getvalue()
            self.assertIn("本地公告源", output)
            self.assertIn(str(announcement_path), output)
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertEqual("公告源：AI服务器订单进展", loaded[0]["title"])
            self.assertEqual("company-announcement", loaded[0]["source"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_start_daily_news_workflow_creates_default_source_then_runs_export(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["start-daily-news-workflow"])

            output = stdout.getvalue()
            self.assertIn("启动每日新闻工作流", output)
            self.assertIn("今日第一遍阅读", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("源文件状态：自动生成", output)
            self.assertIn(f"今日摘要文件：{export_path}", output)
            self.assertIn("建议阅读顺序：", output)
            self.assertIn("1. 先打开已保存的每日优先级摘要。", output)
            self.assertIn("批量新闻每日导出", output)
            self.assertIn(f"已保存优先级摘要到：{export_path}", output)
            self.assertNotIn(
                "Usage: python -m app.main start-daily-news-workflow",
                output,
            )
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_start_daily_news_workflow_reuses_existing_source_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        custom_payload = [
            {
                "title": "自定义新闻标题",
                "content": "自定义新闻内容。",
            }
        ]
        try:
            batch_dir.mkdir(parents=True, exist_ok=True)
            batch_path.write_text(
                json.dumps(custom_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["start-daily-news-workflow"])

            output = stdout.getvalue()
            self.assertIn("启动每日新闻工作流", output)
            self.assertIn("今日第一遍阅读", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("源文件状态：复用已有文件", output)
            self.assertIn(f"今日摘要文件：{export_path}", output)
            self.assertIn("建议阅读顺序：", output)
            self.assertIn(f"已保存优先级摘要到：{export_path}", output)
            self.assertNotIn(
                "Usage: python -m app.main start-daily-news-workflow",
                output,
            )
            self.assertEqual(
                json.loads(batch_path.read_text(encoding="utf-8")),
                custom_payload,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_daily_mainline_can_run_end_to_end(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as self_check_stdout,
            ):
                main(["self-check"])

            self_check_output = self_check_stdout.getvalue()
            self.assertIn("最小可运行自检", self_check_output)
            self.assertIn("主流程：ok", self_check_output)
            self.assertIn(
                "真实数据状态：not-passed (still on demo fallback)",
                self_check_output,
            )
            self.assertIn("最新复盘：ok", self_check_output)
            self.assertIn(
                "下一步：python -m app.main validate-local-quote",
                self_check_output,
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as workflow_stdout,
            ):
                main(["start-daily-news-workflow"])

            workflow_output = workflow_stdout.getvalue()
            self.assertIn("启动每日新闻工作流", workflow_output)
            self.assertIn(f"新闻源文件：{batch_path}", workflow_output)
            self.assertIn(f"今日摘要文件：{export_path}", workflow_output)
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as review_stdout,
            ):
                main(["latest-review"])

            review_output = review_stdout.getvalue()
            self.assertIn("复盘阅读提示", review_output)
            self.assertIn(
                "最佳阅读时机：先运行 python -m app.main start-daily-news-workflow",
                review_output,
            )
            self.assertIn("AI + 半导体收盘复盘", review_output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_mainline_smoke_test_runs_compact_daily_chain(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["mainline-smoke-test"])

            output = stdout.getvalue()
            self.assertIn("每日主线烟雾测试", output)
            self.assertIn("自检：通过", output)
            self.assertIn("真实数据：not-passed", output)
            self.assertIn("每日工作流：通过", output)
            self.assertIn("最新复盘：通过", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn(f"摘要文件：{export_path}", output)
            self.assertIn(
                "优先打开文件：data/news/news_batch_priority_summary_YYYYMMDD.md",
                output,
            )
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_mainline_smoke_test_uses_default_local_news_feed_when_available(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        feed_path = batch_dir / "local_news_feed.json"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            batch_dir.mkdir(parents=True, exist_ok=True)
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地源：HBM订单继续改善",
                            "content": "存储和HBM方向订单预期改善，关注核心池是否跟随。",
                            "source": "manual-feed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["mainline-smoke-test"])

            output = stdout.getvalue()
            self.assertIn("每日主线烟雾测试", output)
            self.assertIn("新闻源模式：本地新闻源", output)
            self.assertIn(f"本地新闻源：{feed_path}", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn(f"摘要文件：{export_path}", output)
            self.assertTrue(batch_path.exists())
            self.assertTrue(export_path.exists())
            loaded = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertEqual("本地源：HBM订单继续改善", loaded[0]["title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_phase_one_ready_check_reports_local_runnable_ready(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["phase-one-ready-check"])

            output = stdout.getvalue()
            self.assertIn("阶段一就绪检查", output)
            self.assertIn("自检：通过", output)
            self.assertIn("股票池：valid", output)
            self.assertIn("每日主线：通过", output)
            self.assertIn("最新复盘：通过", output)
            self.assertIn("结果：阶段一可运行版本已就绪。", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn(f"摘要文件：{export_path}", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_phase_two_ready_check_reports_enhanced_local_ready(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        stamp = self._today_batch_stamp()
        batch_path = batch_dir / f"news_batch_{stamp}.json"
        export_path = batch_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["phase-two-ready-check"])

            output = stdout.getvalue()
            self.assertIn("阶段二就绪检查", output)
            self.assertIn("阶段一：通过", output)
            self.assertIn("新闻源状态：auto-candidate-only", output)
            self.assertIn("调度入口：可检查", output)
            self.assertIn("每日新闻增强链路：通过", output)
            self.assertIn("结果：阶段二增强版已就绪。", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn(f"摘要文件：{export_path}", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_daily_automation_status_reports_scheduler_and_news_source(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["daily-automation-status"])

            output = stdout.getvalue()
            self.assertIn("每日自动化状态", output)
            self.assertIn("调度运行时：", output)
            self.assertIn("注册任务：Registered jobs:", output)
            self.assertIn("新闻源状态：auto-candidate-only", output)
            self.assertIn("下一步：", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_announcement_source_status_reports_not_configured(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict("os.environ", {"MONITOR_DATABASE_PATH": str(database_path)}, clear=True),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["announcement-source-status"])

            output = stdout.getvalue()
            self.assertIn("公告源状态", output)
            self.assertIn("状态：not-configured", output)
            self.assertIn("公告源文件：未配置", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_create_local_announcement_feed_template_writes_feed_shape(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_announcement_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["create-local-announcement-feed-template", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地公告源模板", output)
            self.assertIn(f"保存到：{feed_path}", output)
            self.assertIn("环境变量：MONITOR_ANNOUNCEMENT_FEED_PATH", output)
            self.assertTrue(feed_path.exists())
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(loaded), 2)
            self.assertTrue(all(item.get("title") and item.get("content") for item in loaded))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_local_announcement_feed_reports_valid_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_announcement_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "公告源：半导体材料扩产进展",
                            "content": "公司公告披露材料产能扩张和客户验证进展。",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-local-announcement-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("本地公告源校验", output)
            self.assertIn(f"来源文件：{feed_path}", output)
            self.assertIn("状态：有效", output)
            self.assertIn("有效公告条数：1", output)
            self.assertIn("第一条标题：公告源：半导体材料扩产进展", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_announcement_feed_writes_remote_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_announcement_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_ANNOUNCEMENT_FEED_URL": "https://example.test/announcements.json",
                    },
                    clear=False,
                ),
                patch(
                    "app.main.fetch_remote_announcement_items",
                    return_value=(
                        [
                            {
                                "title": "公告源：AI服务器订单进展",
                                "content": "公司公告披露AI服务器订单进展。",
                                "source": "remote-announcement-feed",
                            }
                        ],
                        {
                            "status": "ok",
                            "reason": "Remote announcement feed is readable.",
                            "next_step": "python -m app.main start-daily-news-workflow",
                        },
                    ),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-announcement-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("刷新本地公告源", output)
            self.assertIn("状态：成功", output)
            self.assertIn("写入公告条数：1", output)
            self.assertTrue(feed_path.exists())
            loaded = json.loads(feed_path.read_text(encoding="utf-8"))
            self.assertEqual("公告源：AI服务器订单进展", loaded[0]["title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_refresh_local_announcement_feed_does_not_write_on_failure(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        feed_path = temp_dir / "local_announcement_feed.json"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch(
                    "app.main.fetch_remote_announcement_items",
                    return_value=(
                        [],
                        {
                            "status": "not-configured",
                            "reason": "No announcement feed URL configured.",
                            "next_step": "set MONITOR_ANNOUNCEMENT_FEED_URL",
                        },
                    ),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["refresh-local-announcement-feed", str(feed_path)])

            output = stdout.getvalue()
            self.assertIn("状态：未配置", output)
            self.assertIn("下一步：set MONITOR_ANNOUNCEMENT_FEED_URL", output)
            self.assertFalse(feed_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_notification_status_reports_console_only(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict("os.environ", {"MONITOR_DATABASE_PATH": str(database_path)}, clear=True),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["notification-status"])

            output = stdout.getvalue()
            self.assertIn("推送通知状态", output)
            self.assertIn("状态：console-only", output)
            self.assertIn("通道：console", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_phase_three_ready_check_reports_external_framework_ready(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_dir = temp_dir / "news_workspace"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(batch_dir),
                    },
                    clear=False,
                ),
                patch("app.pipeline.fetch_realtime_quotes", return_value=pd.DataFrame()),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["phase-three-ready-check"])

            output = stdout.getvalue()
            self.assertIn("阶段三就绪检查", output)
            self.assertIn("阶段二：通过", output)
            self.assertIn("公告源状态：not-configured", output)
            self.assertIn("推送状态：console-only", output)
            self.assertIn("自动化状态：可检查", output)
            self.assertIn("结果：阶段三外部集成框架已就绪。", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_full_regression_check_prints_compact_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"

        class FakeResult:
            testsRun = 12
            failures: list[object] = []
            errors: list[object] = []
            skipped: list[object] = []

            @staticmethod
            def wasSuccessful() -> bool:
                return True

        fake_suite = unittest.TestSuite()
        fake_result = FakeResult()
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.unittest.TestLoader.discover", return_value=fake_suite),
                patch("app.main.unittest.TextTestRunner.run", return_value=fake_result),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["full-regression-check"])

            output = stdout.getvalue()
            self.assertIn("Full Regression Check", output)
            self.assertIn("Status: ok", output)
            self.assertIn("Tests run: 12", output)
            self.assertIn("Failures: 0", output)
            self.assertIn("Errors: 0", output)
            self.assertIn("Skipped: 0", output)
            self.assertIn('Runner mode: unittest discover -s tests -p "test_*.py"', output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_quote_connectivity_check_reports_missing_dependency(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.importlib.util.find_spec", return_value=None),
                patch(
                    "app.main._default_eastmoney_fetcher",
                    side_effect=RuntimeError("Connection aborted."),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["quote-connectivity-check"])

            output = stdout.getvalue()
            self.assertIn("实时行情连通性检查", output)
            self.assertIn("依赖状态：missing", output)
            self.assertIn("端点访问：blocked", output)
            self.assertIn("直连备用源也仍不可达", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_quote_connectivity_check_reports_blocked_endpoint(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        blocked_error = (
            "HTTPSConnectionPool(host='82.push2.eastmoney.com', port=443): "
            "Failed to establish a new connection: [WinError 10013]"
        )
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.importlib.util.find_spec", return_value=object()),
                patch("app.main._default_akshare_fetcher", side_effect=RuntimeError(blocked_error)),
                patch("app.main._default_eastmoney_fetcher", side_effect=RuntimeError(blocked_error)),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["quote-connectivity-check"])

            output = stdout.getvalue()
            self.assertIn("依赖状态：installed", output)
            self.assertIn("端点访问：blocked", output)
            self.assertIn("失败类型：socket-permission-blocked", output)
            self.assertIn("Local socket or network permission", output)
            self.assertIn("WinError 10013", output)
            self.assertIn("受阻阶段：Eastmoney direct fallback", output)
            self.assertIn(
                "运行时诊断摘要：the failure is still inside the realtime quote acquisition layer before stock-pool filtering or report generation.",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_quote_connectivity_check_reports_tcp_connect_failure(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        blocked_error = "Command '['curl.exe', 'https://push2.eastmoney.com']' returned non-zero exit status 7."
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.importlib.util.find_spec", return_value=object()),
                patch("app.main._default_akshare_fetcher", side_effect=RuntimeError(blocked_error)),
                patch("app.main._default_eastmoney_fetcher", side_effect=RuntimeError(blocked_error)),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["quote-connectivity-check"])

            output = stdout.getvalue()
            self.assertIn("端点访问：blocked", output)
            self.assertIn("失败类型：tcp-connect-failed", output)
            self.assertIn("could not complete the TCP connection", output)
            self.assertIn("current Python or Codex runtime", output)
            self.assertIn(
                "运行时诊断摘要：shell or browser access may still work, but the active Python runtime cannot complete the outbound quote request yet.",
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_quote_connectivity_check_reports_ready_backup_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        direct_frame = pd.DataFrame([{"code": "688549"}, {"code": "688126"}])
        direct_frame.attrs["fetch_path"] = "eastmoney-market-powershell"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.importlib.util.find_spec", return_value=object()),
                patch("app.main._default_akshare_fetcher", side_effect=RuntimeError("RemoteDisconnected")),
                patch(
                    "app.main._default_eastmoney_fetcher",
                    return_value=direct_frame,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["quote-connectivity-check"])

            output = stdout.getvalue()
            self.assertIn("依赖状态：installed", output)
            self.assertIn("端点访问：ok", output)
            self.assertIn("获取行数：2", output)
            self.assertIn(
                "行情来源：eastmoney-direct (live direct endpoint)",
                output,
            )
            self.assertIn("直连路径：eastmoney-market-powershell", output)
            self.assertIn("真实数据状态：live-pass", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_quote_connectivity_check_reports_ready_realtime_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.importlib.util.find_spec", return_value=object()),
                patch(
                    "app.main._default_akshare_fetcher",
                    return_value=pd.DataFrame([{"code": "688549"}, {"code": "688126"}]),
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["quote-connectivity-check"])

            output = stdout.getvalue()
            self.assertIn("依赖状态：installed", output)
            self.assertIn("端点访问：ok", output)
            self.assertIn("获取行数：2", output)
            self.assertIn("行情来源：akshare (live adapter)", output)
            self.assertIn("真实数据状态：live-pass", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_first_pass_runs_validation_and_summary_only_view(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-first-pass", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量初筛", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("校验：通过", output)
            self.assertIn("新闻条数：2", output)
            self.assertIn("新闻批量分类", output)
            self.assertIn("筛选模式：summary-only", output)
            self.assertIn("显示条数：2/2", output)
            self.assertNotIn("结论：", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_first_pass_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-first-pass"])

            output = stdout.getvalue()
            self.assertIn("新闻批量初筛", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main news-batch-first-pass "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_priority_pass_runs_validation_and_high_priority_view(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-priority-pass", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量优先级筛选", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("校验：通过", output)
            self.assertIn("新闻条数：2", output)
            self.assertIn("新闻批量分类", output)
            self.assertIn("筛选模式：high-priority-only", output)
            self.assertIn("显示条数：1/2", output)
            self.assertIn("1. 半导体设备出口管制升级", output)
            self.assertNotIn("一般性行业跟踪", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_priority_pass_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-priority-pass"])

            output = stdout.getvalue()
            self.assertIn("新闻批量优先级筛选", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main news-batch-priority-pass "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_priority_export_writes_fixed_summary_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        export_path = temp_dir / "news_batch_priority_summary.md"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-priority-export", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量优先级导出", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("校验：通过", output)
            self.assertIn(f"保存到：{export_path}", output)
            self.assertIn("筛选模式：high-priority-only", output)
            self.assertTrue(export_path.exists())
            exported_text = export_path.read_text(encoding="utf-8")
            self.assertIn("筛选模式：high-priority-only", exported_text)
            self.assertIn("1. 半导体设备出口管制升级", exported_text)
            self.assertNotIn("一般性行业跟踪", exported_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_news_batch_priority_export_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["news-batch-priority-export"])

            output = stdout.getvalue()
            self.assertIn("新闻批量优先级导出", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main news-batch-priority-export "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_batch_news_daily_flow_runs_summary_and_priority_passes(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["batch-news-daily-flow", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("批量新闻每日流程", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("校验：通过", output)
            self.assertIn("新闻条数：2", output)
            self.assertIn("摘要初筛", output)
            self.assertIn("优先级筛选", output)
            self.assertIn("筛选模式：summary-only", output)
            self.assertIn("显示条数：2/2", output)
            self.assertIn("筛选模式：high-priority-only", output)
            self.assertIn("显示条数：1/2", output)
            self.assertNotIn(
                'Usage: python -m app.main classify-news-batch "news_batch.json"',
                output,
            )
            self.assertIn(
                '下一步归档命令：python -m app.main news-batch-priority-export "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_batch_news_daily_flow_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["batch-news-daily-flow"])

            output = stdout.getvalue()
            self.assertIn("批量新闻每日流程", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main batch-news-daily-flow "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_batch_news_daily_export_runs_flow_and_writes_priority_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        export_dir = temp_dir / "news_archive"
        stamp = self._today_batch_stamp()
        export_path = export_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(export_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["batch-news-daily-export", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("批量新闻每日导出", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn("校验：通过", output)
            self.assertIn("摘要初筛", output)
            self.assertIn("优先级筛选", output)
            self.assertIn("筛选模式：summary-only", output)
            self.assertIn("筛选模式：high-priority-only", output)
            self.assertIn(f"已保存优先级摘要到：{export_path}", output)
            self.assertIn(
                "默认归档规则：data/news/news_batch_priority_summary_YYYYMMDD.md",
                output,
            )
            self.assertNotIn(
                'Usage: python -m app.main classify-news-batch "news_batch.json"',
                output,
            )
            self.assertNotIn(
                'Usage: python -m app.main batch-news-daily-export "news_batch.json"',
                output,
            )
            self.assertTrue(export_path.exists())
            exported_text = export_path.read_text(encoding="utf-8")
            self.assertIn("# Daily News Priority Summary", exported_text)
            self.assertIn(
                "This note is the same-day high-priority news watch summary for quick research reading.",
                exported_text,
            )
            self.assertIn(f"- Date: {datetime.now().strftime('%Y-%m-%d')}", exported_text)
            self.assertIn(f"- Source batch: {batch_path}", exported_text)
            self.assertIn("- Total batch items: 2", exported_text)
            self.assertIn("- Priority items shown: 1/2", exported_text)
            self.assertIn("- 影响摘要：风险扩散 1 | 主线强化 0 | 局部验证 1", exported_text)
            self.assertIn("## Core Summary", exported_text)
            self.assertIn(
                "红色：偏风险扩散 | 主题: 风险扩散 | 观察验证 | 需要重点防守：先确认风险是否扩散，再决定是否处理强化跟踪。",
                exported_text,
            )
            self.assertIn("## One-Line Advice", exported_text)
            self.assertIn(
                "今天先以防守为主，先确认风险名单是否扩散，再处理其他机会。",
                exported_text,
            )
            self.assertNotIn("## Status Color", exported_text)
            self.assertNotIn("## Defense Status", exported_text)
            self.assertNotIn("## Theme Tags", exported_text)
            self.assertIn("## Daily Conclusion", exported_text)
            self.assertIn(
                "今日重点偏风险扩散，优先处理风险项。当前高优先级显示 1/2，其中风险扩散 1 条、主线强化 0 条。",
                exported_text,
            )
            self.assertIn("## Operation Tip", exported_text)
            self.assertIn(
                "先看风险优先名单，再看强化跟踪名单；如果风险未扩散，再回到观察验证名单。",
                exported_text,
            )
            self.assertIn("## Processing Order", exported_text)
            self.assertIn("1. 先看风险优先名单", exported_text)
            self.assertIn("## Watchlist", exported_text)
            self.assertIn("### 风险优先名单", exported_text)
            self.assertIn("- 中微公司", exported_text)
            self.assertIn("- 北方华创", exported_text)
            self.assertIn("- 拓荆科技", exported_text)
            self.assertNotIn("### 强化跟踪名单", exported_text)
            self.assertIn("## Suggested Actions", exported_text)
            self.assertIn("### 风险优先动作", exported_text)
            self.assertIn(
                "- 半导体设备出口管制升级: 更偏风险扩散，优先检查相关板块是否同步承压。 当前建议：优先盯核心池 中微公司、北方华创、拓荆科技 是否出现同步承压。",
                exported_text,
            )
            self.assertNotIn("### 强化跟踪动作", exported_text)
            self.assertIn("## 优先级筛选", exported_text)
            self.assertIn("- 筛选模式：high-priority-only", exported_text)
            self.assertIn("### 1. 半导体设备出口管制升级", exported_text)
            self.assertIn("- 级别：S | 板块：半导体设备", exported_text)
            self.assertIn(
                "- 结论：更偏风险扩散，优先检查相关板块是否同步承压。 当前建议：优先盯核心池 中微公司、北方华创、拓荆科技 是否出现同步承压。",
                exported_text,
            )
            self.assertNotIn("一般性行业跟踪", exported_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_batch_news_daily_export_balanced_branch_keeps_daily_summary_readable(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        export_dir = temp_dir / "news_archive"
        stamp = self._today_batch_stamp()
        export_path = export_dir / f"news_batch_priority_summary_{stamp}.md"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气环节景气度提升。",
                        },
                        {
                            "title": "AI服务器需求延续",
                            "content": "算力链订单预期改善，液冷与高速互连方向继续活跃。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {
                        "MONITOR_DATABASE_PATH": str(database_path),
                        "MONITOR_NEWS_DAILY_EXPORT_DIR": str(export_dir),
                    },
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                main(["batch-news-daily-export", str(batch_path)])

            exported_text = export_path.read_text(encoding="utf-8")
            self.assertIn("- 影响摘要：风险扩散 1 | 主线强化 1 | 局部验证 1", exported_text)
            self.assertIn(
                "橙色：偏均衡跟踪 | 主题: 均衡跟踪 | 风险扩散 | 主线强化 | 观察验证 | 需要边防守边跟踪：风险与强化信号同时存在。",
                exported_text,
            )
            self.assertIn("今天防守和跟踪都要兼顾，先看风险，再看强化。", exported_text)
            self.assertIn(
                "今日重点在风险与强化之间相对均衡，建议并行跟踪。当前高优先级显示 2/3，风险扩散 1 条、主线强化 1 条。",
                exported_text,
            )
            self.assertIn(
                "先看风险优先名单，再看强化跟踪名单；如果风险未扩散，再回到观察验证名单。",
                exported_text,
            )
            self.assertIn("### 风险优先名单", exported_text)
            self.assertIn("### 强化跟踪名单", exported_text)
            self.assertIn("- 中微公司", exported_text)
            self.assertIn("- 华特气体", exported_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_batch_news_daily_export_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["batch-news-daily-export"])

            output = stdout.getvalue()
            self.assertIn("批量新闻每日导出", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main batch-news-daily-export "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_news_batch_requires_input_path(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-news-batch"])

            output = stdout.getvalue()
            self.assertIn("新闻批量校验", output)
            self.assertIn("未提供新闻批量文件。", output)
            self.assertIn(
                '用法：python -m app.main validate-news-batch "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_validate_news_batch_rejects_invalid_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {"title": "半导体设备出口管制升级"},
                        {"content": "只有正文，没有标题。"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["validate-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量校验", output)
            self.assertIn(f"新闻批量条目错误：{batch_path}", output)
            self.assertIn("第 1 条：缺少 content。", output)
            self.assertIn("第 2 条：缺少 title。", output)
            self.assertIn(
                '用法：python -m app.main validate-news-batch "news_batch.json"',
                output,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_can_filter_to_high_priority_only(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path), "high-priority-only"])

            output = stdout.getvalue()
            self.assertIn("筛选模式：high-priority-only", output)
            self.assertIn("显示条数：1/2", output)
            self.assertIn("1. 半导体设备出口管制升级", output)
            self.assertNotIn("一般性行业跟踪", output)
            self.assertIn("影响摘要：风险扩散 1 | 主线强化 0 | 局部验证 1", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_can_use_summary_only_mode(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path), "summary-only"])

            output = stdout.getvalue()
            self.assertIn("筛选模式：summary-only", output)
            self.assertIn("显示条数：2/2", output)
            self.assertIn("1. 半导体设备出口管制升级", output)
            self.assertIn("2. 中巨芯U批量供货推进", output)
            self.assertIn("级别：S | 板块：半导体设备", output)
            self.assertIn("级别：A | 板块：半导体气体", output)
            self.assertNotIn("结论：", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_rejects_unsupported_filter_mode(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [{"title": "半导体设备出口管制升级", "content": "刻蚀设备与薄膜沉积环节承压。"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path), "priority-only"])

            output = stdout.getvalue()
            self.assertIn("不支持的筛选模式：priority-only", output)
            self.assertIn("可用筛选模式：high-priority-only, summary-only", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_rejects_invalid_json(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text('{"title": "broken"', encoding="utf-8")

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn(f"新闻批量文件 JSON 格式错误：{batch_path}", output)
            self.assertIn("JSON 错误：", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_rejects_non_list_json(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps({"title": "not-a-list", "content": "bad-shape"}, ensure_ascii=False),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn(f"新闻批量文件结构错误：{batch_path}", output)
            self.assertIn("顶层 JSON 必须是列表。", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_classify_news_batch_rejects_items_with_missing_required_fields(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {"title": "半导体设备出口管制升级"},
                        {"content": "只有正文，没有标题。"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["classify-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn(f"新闻批量条目错误：{batch_path}", output)
            self.assertIn("第 1 条：缺少 content。", output)
            self.assertIn("第 2 条：缺少 title。", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_export_news_batch_writes_summary_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        export_path = temp_dir / "news_batch_summary.md"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "中巨芯U批量供货推进",
                            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["export-news-batch", str(batch_path), str(export_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量导出", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            self.assertIn(f"保存到：{export_path}", output)
            self.assertTrue(export_path.exists())
            exported_text = export_path.read_text(encoding="utf-8")
            self.assertIn("新闻批量分类", exported_text)
            self.assertIn("影响摘要：风险扩散 1 | 主线强化 1 | 局部验证 0", exported_text)
            self.assertIn("1. 半导体设备出口管制升级", exported_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_export_news_batch_can_auto_generate_timestamped_filename(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["export-news-batch", str(batch_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量导出", output)
            self.assertIn(f"新闻源文件：{batch_path}", output)
            exported_files = list(temp_dir.glob("news_batch_summary_*.md"))
            self.assertEqual(1, len(exported_files))
            self.assertIn(f"保存到：{exported_files[0]}", output)
            exported_text = exported_files[0].read_text(encoding="utf-8")
            self.assertIn("新闻批量分类", exported_text)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_export_news_batch_auto_filename_includes_filter_mode(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        try:
            batch_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "刻蚀设备与薄膜沉积环节承压。",
                        },
                        {
                            "title": "一般性行业跟踪",
                            "content": "半导体设备链等待进一步确认。",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["export-news-batch", str(batch_path), "", "high-priority-only"])

            output = stdout.getvalue()
            exported_files = list(temp_dir.glob("news_batch_summary_high-priority-only_*.md"))
            self.assertEqual(1, len(exported_files))
            self.assertIn(f"保存到：{exported_files[0]}", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_export_news_batch_does_not_write_file_when_batch_json_is_invalid(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        batch_path = temp_dir / "news_batch.json"
        export_path = temp_dir / "news_batch_summary.md"
        try:
            batch_path.write_text('{"title": "broken"', encoding="utf-8")

            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["export-news-batch", str(batch_path), str(export_path)])

            output = stdout.getvalue()
            self.assertIn("新闻批量导出", output)
            self.assertIn(f"新闻批量文件 JSON 格式错误：{batch_path}", output)
            self.assertFalse(export_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_unknown_command_prints_help_instead_of_running_demo(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_DATABASE_PATH": str(database_path)},
                    clear=False,
                ),
                patch("app.main.run_demo") as run_demo,
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                main(["unknown-command"])

            run_demo.assert_not_called()
            output = stdout.getvalue()
            self.assertIn("Unknown command: unknown-command", output)
            self.assertIn("AI 半导体监控命令", output)
            self.assertIn("python -m app.main run-job-now [job-id]", output)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
