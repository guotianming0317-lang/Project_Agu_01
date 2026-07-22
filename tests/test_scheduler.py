"""Tests for scheduler-facing monitor helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import unittest
from unittest.mock import patch

from app.config import AppConfig
from app.scheduler import (
    NoOpScheduler,
    build_job_console_output,
    build_registered_jobs_summary,
    build_scheduler_status_text,
    register_default_jobs,
    resolve_job_intent_strategy,
    resolve_job_output_strategy,
    run_monitor_job,
    run_scheduler_loop,
)
from app.pipeline import MonitorCycleResult
from app.task_profiles import (
    DEFAULT_SCHEDULED_JOBS,
    OUTPUT_PROFILES_DISPLAY,
    TASK_PROFILE_CONFIG_PATH,
    TASK_DISPLAY_GROUPS,
    TASK_OVERVIEW_DISPLAY,
    TASK_RESULT_SUMMARY_DECISION_RULES,
    validate_task_profile_config,
)


class SchedulerTests(unittest.TestCase):
    """Verify scheduler helpers reuse the core monitor pipeline."""

    def test_run_monitor_job_delegates_to_pipeline(self) -> None:
        config = _build_test_config()
        sentinel = object()

        with patch("app.scheduler.run_monitor_cycle", return_value=sentinel) as mocked:
            result = run_monitor_job(config)

        self.assertIs(sentinel, result)
        mocked.assert_called_once_with(config)

    def test_register_default_jobs_adds_phase_one_cron_jobs(self) -> None:
        config = _build_test_config()
        scheduler = FakeScheduler()

        register_default_jobs(scheduler, config)

        self.assertEqual(4, len(scheduler.jobs))
        self.assertEqual("pre-open-check", scheduler.jobs[0]["id"])
        self.assertEqual("morning-check", scheduler.jobs[1]["id"])
        self.assertEqual("midday-check", scheduler.jobs[2]["id"])
        self.assertEqual("afternoon-review", scheduler.jobs[3]["id"])
        self.assertEqual({"hour": 9, "minute": 15}, scheduler.jobs[0]["trigger"])
        self.assertEqual({"hour": 9, "minute": 35}, scheduler.jobs[1]["trigger"])
        self.assertEqual({"hour": 11, "minute": 30}, scheduler.jobs[2]["trigger"])
        self.assertEqual({"hour": 14, "minute": 45}, scheduler.jobs[3]["trigger"])
        self.assertIs(config, scheduler.jobs[0]["kwargs"]["config"])
        self.assertIs(config, scheduler.jobs[1]["kwargs"]["config"])
        self.assertIs(config, scheduler.jobs[2]["kwargs"]["config"])
        self.assertIs(config, scheduler.jobs[3]["kwargs"]["config"])
        self.assertEqual("pre-open-check", scheduler.jobs[0]["kwargs"]["job_id"])
        self.assertEqual("morning-check", scheduler.jobs[1]["kwargs"]["job_id"])
        self.assertEqual("midday-check", scheduler.jobs[2]["kwargs"]["job_id"])
        self.assertEqual("afternoon-review", scheduler.jobs[3]["kwargs"]["job_id"])
        self.assertTrue(TASK_PROFILE_CONFIG_PATH.exists())
        self.assertEqual("pre-open-check", DEFAULT_SCHEDULED_JOBS[0]["id"])
        self.assertEqual("Manual Preview", TASK_DISPLAY_GROUPS[0]["label"])
        self.assertEqual("Task Overview", TASK_OVERVIEW_DISPLAY["heading"])
        self.assertEqual("Output profiles:", OUTPUT_PROFILES_DISPLAY["heading"])

    def test_register_default_jobs_is_safe_for_noop_scheduler(self) -> None:
        config = _build_test_config()
        scheduler = NoOpScheduler()

        register_default_jobs(scheduler, config)

        self.assertEqual(4, len(scheduler.jobs))
        self.assertEqual("pre-open-check", scheduler.jobs[0]["id"])
        self.assertEqual("morning-check", scheduler.jobs[1]["id"])
        self.assertEqual("midday-check", scheduler.jobs[2]["id"])
        self.assertEqual("afternoon-review", scheduler.jobs[3]["id"])

    def test_resolve_job_output_strategy_returns_stage_specific_sections(self) -> None:
        pre_open_strategy = resolve_job_output_strategy("pre-open-check")
        morning_strategy = resolve_job_output_strategy("morning-check")
        midday_strategy = resolve_job_output_strategy("midday-check")
        afternoon_strategy = resolve_job_output_strategy("afternoon-review")

        self.assertTrue(pre_open_strategy["include_morning_report"])
        self.assertTrue(pre_open_strategy["include_market_focus_snapshot"])
        self.assertFalse(pre_open_strategy["include_intraday_digest"])
        self.assertFalse(pre_open_strategy["include_detailed_alerts"])
        self.assertTrue(morning_strategy["include_morning_report"])
        self.assertFalse(morning_strategy["include_evening_report"])
        self.assertTrue(midday_strategy["include_intraday_digest"])
        self.assertFalse(midday_strategy["include_morning_report"])
        self.assertFalse(midday_strategy["include_evening_report"])
        self.assertFalse(afternoon_strategy["include_morning_report"])
        self.assertTrue(afternoon_strategy["include_evening_report"])

    def test_resolve_job_intent_strategy_returns_stage_specific_digest_preferences(self) -> None:
        pre_open_strategy = resolve_job_intent_strategy("pre-open-check")
        morning_strategy = resolve_job_intent_strategy("morning-check")
        midday_strategy = resolve_job_intent_strategy("midday-check")
        afternoon_strategy = resolve_job_intent_strategy("afternoon-review")

        self.assertEqual(
            ["news_flash"],
            pre_open_strategy["intraday_digest"]["preferred_alert_types"],
        )
        self.assertEqual("盘前检查", pre_open_strategy["console_title"])
        self.assertEqual("pre_open", pre_open_strategy["result_summary_style"])
        self.assertEqual(
            ["overnight-news", "pre-open-risk"],
            pre_open_strategy["focus_tags"],
        )
        self.assertEqual(
            ["光模块", "服务器", "设备", "材料", "气体"],
            pre_open_strategy["preferred_chain_groups"],
        )
        self.assertIn(
            "overnight disruption",
            pre_open_strategy["strategy_note"],
        )
        self.assertEqual(
            ["news_flash", "materials_focus"],
            morning_strategy["intraday_digest"]["preferred_alert_types"],
        )
        self.assertTrue(morning_strategy["intraday_digest"]["high_value_only"])
        self.assertEqual(
            ["sector_move", "materials_focus", "news_flash"],
            midday_strategy["intraday_digest"]["preferred_alert_types"],
        )
        self.assertEqual(
            ["sector_move", "materials_focus", "news_flash"],
            afternoon_strategy["close_digest"]["preferred_alert_types"],
        )
        self.assertEqual("开盘检查", morning_strategy["console_title"])
        self.assertEqual("盘中检查", midday_strategy["console_title"])
        self.assertEqual("尾盘复盘", afternoon_strategy["console_title"])
        self.assertEqual("afternoon_review", afternoon_strategy["result_summary_style"])
        self.assertEqual(
            "strong",
            TASK_RESULT_SUMMARY_DECISION_RULES["midday_check"][0]["case"],
        )

    def test_build_job_console_output_uses_scheduler_specific_output_profile(self) -> None:
        config = _build_test_config()
        result = MonitorCycleResult(
            snapshot_time="2026-06-20 10:00:00",
            quote_source="demo-fallback",
            all_stocks_count=43,
            high_priority_count=27,
            market_rows=[
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.2},
                {"sector": "Materials", "name": "Beta", "pct_chg": 4.8},
                {"sector": "Equipment", "name": "Gamma", "pct_chg": 3.1},
            ],
            alerts=[
                {
                    "alert_type": "news_flash",
                    "level": "红色",
                    "direction": "半导体设备",
                    "message": "出口管制升级",
                },
                {
                    "alert_type": "materials_focus",
                    "level": "橙色",
                    "direction": "材料气体链",
                    "message": "材料链强化",
                },
                {
                    "alert_type": "sector_move",
                    "level": "橙色",
                    "direction": "半导体材料",
                    "message": "板块异动",
                },
            ],
            morning_report="Morning report body",
            evening_report="Evening report body",
        )

        pre_open_output = build_job_console_output(config, result, job_id="pre-open-check")
        morning_output = build_job_console_output(config, result, job_id="morning-check")
        midday_output = build_job_console_output(config, result, job_id="midday-check")
        afternoon_output = build_job_console_output(
            config,
            result,
            job_id="afternoon-review",
        )

        self.assertIn("盘前检查", pre_open_output)
        self.assertIn("View mode: Pre-open View (pre_open_view)", pre_open_output)
        self.assertIn("焦点：盘前准备与隔夜风险扫描", pre_open_output)
        self.assertIn(
            "结果：盘前准备偏活跃；有 3 条高价值题材或消息信号需要观察。",
            pre_open_output,
        )
        self.assertIn("开盘市场焦点", pre_open_output)
        self.assertIn("Morning report body", pre_open_output)
        self.assertNotIn("Intraday Alert Digest", pre_open_output)
        self.assertNotIn("Evening report body", pre_open_output)
        self.assertIn("Morning report body", morning_output)
        self.assertNotIn("Evening report body", morning_output)
        self.assertIn("View mode: Opening Task View (opening_task_view)", morning_output)
        self.assertIn("开盘检查", morning_output)
        self.assertIn("焦点：开盘风险与题材确认", morning_output)
        self.assertIn(
            "结果：开盘题材确认较强；早盘出现 3 条高价值信号。",
            morning_output,
        )
        self.assertNotIn("Morning report body", midday_output)
        self.assertNotIn("Evening report body", midday_output)
        self.assertIn(
            "View mode: Mid-session Task View (mid_session_task_view)",
            midday_output,
        )
        self.assertIn("Intraday Alert Digest", midday_output)
        self.assertIn("盘中检查", midday_output)
        self.assertIn("焦点：盘中扩散与广度检查", midday_output)
        self.assertIn(
            "结果：盘中扩散较强；3 条高价值信号显示扩散有进一步延续迹象。",
            midday_output,
        )
        self.assertIn("盘中市场焦点", midday_output)
        self.assertNotIn("Morning report body", afternoon_output)
        self.assertIn("Evening report body", afternoon_output)
        self.assertIn(
            "View mode: Close Review View (close_review_task_view)",
            afternoon_output,
        )
        self.assertIn("尾盘复盘", afternoon_output)
        self.assertIn("焦点：收盘结构与题材复盘", afternoon_output)
        self.assertIn(
            "结果：收盘结构偏积极；3 条高价值信号延续到复盘时段。",
            afternoon_output,
        )
        self.assertIn("出口管制升级", morning_output)
        self.assertIn("板块异动", midday_output)
        self.assertIn("板块异动", morning_output)
        self.assertIn("板块异动", afternoon_output)

    def test_run_scheduler_loop_returns_hint_for_noop_scheduler(self) -> None:
        scheduler = NoOpScheduler()

        message = run_scheduler_loop(scheduler)

        self.assertIn("APScheduler is not available", message)

    def test_run_scheduler_loop_starts_and_shuts_down_real_scheduler_like(self) -> None:
        scheduler = FakeRunningScheduler()

        def interrupting_sleep(_: float) -> None:
            raise KeyboardInterrupt

        message = run_scheduler_loop(scheduler, sleep_fn=interrupting_sleep)

        self.assertTrue(scheduler.started)
        self.assertTrue(scheduler.stopped)
        self.assertIn("Scheduler stopped", message)

    def test_build_scheduler_status_text_reports_noop_runtime(self) -> None:
        config = _build_test_config()

        text = build_scheduler_status_text(config, NoOpScheduler())

        self.assertIn("Runtime mode: fallback-noop", text)
        self.assertIn("Persistent loop available: no", text)
        self.assertIn("Default protocol: http", text)
        self.assertIn("Database:", text)
        self.assertIn("sqlite:///test.db", text)
        self.assertIn("Install hint:", text)
        self.assertIn("pip install -r requirements.txt", text)
        self.assertIn("python -m app.main scheduler-status", text)
        self.assertIn("Next recommended command: pip install -r requirements.txt", text)
        self.assertIn("Task Overview", text)
        self.assertIn(
            "Result summary styles: full_monitor, pre_open, morning_check, midday_check, afternoon_review",
            text,
        )
        self.assertIn(
            "Scheduled job labels: pre-open-check = Pre-open Check, morning-check = Morning Check, midday-check = Midday Check, afternoon-review = Afternoon Review",
            text,
        )
        self.assertIn("Output profiles:", text)
        self.assertIn("pre-open-check / Pre-open Check", text)
        self.assertIn("midday-check / Midday Check", text)
        self.assertIn("task-summary: Overnight risk scan before the opening session.", text)
        self.assertIn("view-mode: Pre-open View (pre_open_view)", text)
        self.assertIn(
            "view-summary: Keep the pre-open run focused on overnight risk and opening preparation.",
            text,
        )
        self.assertIn("focus-tags: overnight-news, pre-open-risk", text)
        self.assertIn("focus-chains: 光模块, 服务器, 设备, 材料, 气体", text)
        self.assertIn("strategy-note: Bias toward overnight disruption", text)
        self.assertIn(
            "alert-bundles: Overnight News Only (overnight_news_only)",
            text,
        )
        self.assertIn(
            "chain-bundle: Overnight News Impact Chains (overnight_news_impact)",
            text,
        )

    def test_build_scheduler_status_text_reports_live_runtime(self) -> None:
        config = _build_test_config(enable_scheduler=True)

        text = build_scheduler_status_text(config, FakeRunningScheduler())

        self.assertIn("Runtime mode: scheduler-ready", text)
        self.assertIn("Persistent loop available: yes", text)
        self.assertIn("Default protocol: http", text)
        self.assertIn("Database:", text)
        self.assertIn("sqlite:///test.db", text)
        self.assertIn(
            "Next recommended command: python -m app.main run-scheduler",
            text,
        )
        self.assertNotIn("Install hint:", text)
        self.assertIn("Task Overview", text)
        self.assertIn("Manual preview jobs: manual", text)
        self.assertIn(
            "Scheduled day-flow jobs: pre-open-check, morning-check, midday-check, afternoon-review",
            text,
        )
        self.assertIn("Scheduled Day Flow:", text)
        self.assertIn("pre-open-check / Pre-open Check: morning-report, market-focus-snapshot, universe-observation", text)
        self.assertIn("morning-check / Morning Check: morning-report", text)
        self.assertIn("midday-check / Midday Check: market-focus-snapshot, universe-observation, intraday-digest, detailed-alerts", text)
        self.assertIn("view-mode: Opening Task View (opening_task_view)", text)
        self.assertIn("view-mode: Mid-session Task View (mid_session_task_view)", text)
        self.assertIn(
            "alert-bundles: Opening Theme Confirmation (opening_theme_confirmation)",
            text,
        )
        self.assertIn(
            "chain-bundle: Opening Confirmation Chains (opening_confirmation_chains)",
            text,
        )
        self.assertIn("intent: pre-open-preparation-check", text)
        self.assertIn("intent: opening-risk-and-theme-check", text)
        self.assertIn("intent: mid-session-expansion-check", text)

    def test_build_registered_jobs_summary_follows_configured_order(self) -> None:
        summary = build_registered_jobs_summary()

        self.assertIn("pre-open-check (09:15)", summary)
        self.assertIn("morning-check (09:35)", summary)
        self.assertIn("midday-check (11:30)", summary)
        self.assertIn("afternoon-review (14:45)", summary)

    def test_validate_task_profile_config_rejects_duplicate_display_job_ids(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]},
                {"key": "b", "label": "B", "job_ids": ["morning-check"]},
            ],
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {"result_summary_style": "morning_check"}
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "quiet"}]
            },
        }

        with self.assertRaisesRegex(ValueError, "Duplicate task display job ids"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )

    def test_validate_task_profile_config_rejects_unknown_summary_style(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]}
            ],
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {"result_summary_style": "missing_style"}
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "quiet"}]
            },
        }

        with self.assertRaisesRegex(ValueError, "unknown summary style"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )

    def test_validate_task_profile_config_rejects_missing_summary_case_wording(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]}
            ],
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {"result_summary_style": "morning_check"}
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "mixed"}]
            },
        }

        with self.assertRaisesRegex(ValueError, "no matching wording template"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )

    def test_validate_task_profile_config_rejects_unknown_task_overview_field(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]}
            ],
            "task_overview_display": {
                "heading": "Task Overview",
                "display_groups_heading": "Display groups:",
                "fields": [{"key": "unknown_field", "label": "Unknown"}],
            },
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {"result_summary_style": "morning_check"}
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "quiet"}]
            },
        }

        with self.assertRaisesRegex(ValueError, "unknown field keys"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )

    def test_validate_task_profile_config_rejects_unknown_output_profile_block(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]}
            ],
            "task_overview_display": {
                "heading": "Task Overview",
                "display_groups_heading": "Display groups:",
                "fields": [{"key": "scheduled_jobs", "label": "Scheduled jobs"}],
            },
            "output_profiles_display": {
                "heading": "Output profiles:",
                "intent_label_prefix": "  intent: ",
                "block_labels": {"unknown_block": "unknown"},
            },
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {"result_summary_style": "morning_check"}
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "quiet"}]
            },
        }

        with self.assertRaisesRegex(ValueError, "unknown block keys"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )

    def test_validate_task_profile_config_rejects_unknown_alert_type_bundle(self) -> None:
        config = {
            "scheduled_jobs": [{"id": "morning-check", "hour": 9, "minute": 35}],
            "task_display_groups": [
                {"key": "a", "label": "A", "job_ids": ["morning-check"]}
            ],
            "job_output_strategies": {"morning-check": {}},
            "job_intent_strategies": {
                "morning-check": {
                    "result_summary_style": "morning_check",
                    "intraday_digest": {
                        "preferred_alert_type_bundle": "missing_bundle"
                    },
                }
            },
            "task_result_summary_decision_rules": {
                "morning_check": [{"case": "quiet"}]
            },
            "alert_type_bundles": {
                "known_bundle": ["news_flash"]
            },
        }

        with self.assertRaisesRegex(ValueError, "unknown alert-type bundle"):
            validate_task_profile_config(
                config,
                {"morning_check": {"quiet": "quiet"}},
            )


def _build_test_config(*, enable_scheduler: bool = False) -> AppConfig:
    """Create a stable config fixture for scheduler tests."""
    return AppConfig(
        environment="test",
        default_protocol="http",
        database_path=Path("test.db"),
        database_url="sqlite:///test.db",
        log_level="INFO",
        auto_latest_review=False,
        enable_scheduler=enable_scheduler,
    )


@dataclass
class FakeScheduler:
    """Minimal scheduler test double that records added jobs."""

    jobs: list[dict[str, Any]] = field(default_factory=list)

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
        _ = wait


@dataclass
class FakeRunningScheduler(FakeScheduler):
    """Scheduler test double with start/stop lifecycle hooks."""

    started: bool = False
    stopped: bool = False

    def start(self) -> None:
        self.started = True

    def shutdown(self, wait: bool = True) -> None:
        _ = wait
        self.stopped = True


if __name__ == "__main__":
    unittest.main()
