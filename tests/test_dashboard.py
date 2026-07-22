"""Tests for the minimal dashboard data layer."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.dashboard.overview import build_dashboard_payload
from app.database import initialize_database, save_alerts, save_market_snapshots
from app.universe.stock_pool import build_stock_pool_health_summary, save_stock_pool_health_snapshot


class DashboardTests(unittest.TestCase):
    """Verify dashboard summaries are stable and database-backed."""

    def test_build_dashboard_payload_returns_empty_state(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)

            with patch(
                "app.dashboard.overview._find_latest_priority_summary_path",
                return_value=None,
            ):
                payload = build_dashboard_payload(database_path)

            self.assertIsNone(payload["latest_timestamp"])
            self.assertEqual("", payload["quote_source"])
            self.assertEqual("", payload["quote_source_display"])
            self.assertEqual("Quote status: unavailable.", payload["quote_status_summary"])
            self.assertEqual(0, payload["snapshot_count"])
            self.assertEqual(0, payload["alert_count"])
            self.assertEqual(0, payload["positive_alert_count"])
            self.assertEqual(0, payload["negative_alert_count"])
            self.assertEqual("No main-line summary", payload["mainline_summary"])
            self.assertEqual("No risk summary", payload["risk_summary"])
            self.assertEqual([], payload["top_movers"])
            self.assertEqual([], payload["latest_alerts"])
            self.assertEqual([], payload["available_batches"])
            self.assertEqual([], payload["sector_cards"])
            self.assertEqual([], payload["sector_chart"])
            self.assertEqual([], payload["top_mover_chart"])
            self.assertEqual({}, payload["leader_summary"])
            self.assertEqual({}, payload["next_session_action_summary"])
            self.assertEqual({}, payload["today_priority_summary"])
            self.assertIsInstance(payload["stock_pool_drift_summary"], str)
            self.assertEqual("No data yet", payload["strongest_sector"])
            self.assertEqual("No data yet", payload["strongest_sector_summary"]["sector"])
            self.assertEqual(0.0, payload["strongest_sector_summary"]["avg_pct_chg"])
            self.assertEqual(0, payload["strongest_sector_summary"]["stock_count"])
            self.assertIn("stock_pool_health", payload)
            self.assertIn("status", payload["stock_pool_health"])
            self.assertIn("health_hints", payload["stock_pool_health"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_summarizes_latest_batch(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 09:35:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.34,
                        "pct_chg": 4.2,
                        "turnover": 300.0,
                        "volume_ratio": 1.8,
                        "turnover_rate": 3.1,
                        "sector": "Semi Materials",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 800.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 5.5,
                        "sector": "Semi Materials",
                        "quote_source": "local-json-snapshot",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "code": "688268",
                        "name": "NorthGas",
                        "price": 45.20,
                        "pct_chg": 5.2,
                        "turnover": 500.0,
                        "volume_ratio": 1.9,
                        "turnover_rate": 3.2,
                        "sector": "Semi Materials",
                        "quote_source": "local-json-snapshot",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "code": "002371",
                        "name": "FabEquip",
                        "price": 310.5,
                        "pct_chg": 3.4,
                        "turnover": 1100.0,
                        "volume_ratio": 1.4,
                        "turnover_rate": 2.0,
                        "sector": "Semi Equipment",
                        "quote_source": "local-json-snapshot",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "price_spike",
                        "level": "orange",
                        "message": "GiantChip-U surged 8.6% intraday",
                        "related_stocks": "GiantChip-U",
                        "direction": "Semi Materials",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "materials_focus",
                        "level": "orange",
                        "message": "Materials line is strengthening",
                        "related_stocks": "GiantChip-U, NorthGas",
                        "direction": "Semi Materials",
                    },
                ],
            )

            with patch(
                "app.dashboard.overview._find_latest_priority_summary_path",
                return_value=None,
            ):
                payload = build_dashboard_payload(database_path)

            self.assertEqual("2026-06-20 14:45:00", payload["latest_timestamp"])
            self.assertEqual("local-json-snapshot", payload["quote_source"])
            self.assertEqual(
                "local-json-snapshot (local real quote snapshot)",
                payload["quote_source_display"],
            )
            self.assertEqual(
                "Quote status: using local real quote snapshot.",
                payload["quote_status_summary"],
            )
            self.assertEqual(3, payload["snapshot_count"])
            self.assertEqual(2, payload["alert_count"])
            self.assertEqual(2, payload["positive_alert_count"])
            self.assertEqual(0, payload["negative_alert_count"])
            self.assertEqual(
                "Main line: Semi Materials; Semi Equipment is the first follow-through lane.",
                payload["mainline_summary"],
            )
            self.assertEqual(
                "Risk state: stable; no dominant warning signal is active.",
                payload["risk_summary"],
            )
            self.assertEqual("Semi Materials", payload["strongest_sector"])
            self.assertEqual("Semi Materials", payload["strongest_sector_summary"]["sector"])
            self.assertAlmostEqual(6.9, payload["strongest_sector_summary"]["avg_pct_chg"], places=2)
            self.assertEqual(2, payload["strongest_sector_summary"]["stock_count"])
            self.assertEqual(2, len(payload["available_batches"]))
            self.assertEqual("GiantChip-U", payload["top_movers"][0]["name"])
            self.assertEqual(
                "GiantChip-U surged 8.6% intraday",
                payload["latest_alerts"][0]["message"],
            )
            self.assertEqual(2, len(payload["sector_cards"]))
            self.assertEqual("Semi Materials", payload["sector_cards"][0]["sector"])
            self.assertAlmostEqual(6.9, payload["sector_cards"][0]["avg_pct_chg"], places=2)
            self.assertEqual("Semi Materials", payload["sector_chart"][0]["sector"])
            self.assertEqual("GiantChip-U", payload["top_mover_chart"][0]["name"])
            self.assertAlmostEqual(8.6, payload["top_mover_chart"][0]["pct_chg"], places=2)
            self.assertIn("GiantChip-U", payload["leader_summary"].values())
            self.assertIn("rule_summary_lines", payload["next_session_action_summary"])
            self.assertEqual(2, payload["next_session_action_summary"]["core_count"])
            self.assertIn("GiantChip-U", payload["next_session_action_summary"]["core"]["watchlist"])
            self.assertEqual({}, payload["today_priority_summary"])
            self.assertIsInstance(payload["stock_pool_drift_summary"], str)
            self.assertTrue(payload["stock_pool_drift_summary"])
            self.assertEqual("valid", payload["stock_pool_health"]["status"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_includes_today_priority_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        summary_path = temp_dir / "news_batch_priority_summary_20260718.md"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-07-18 14:45:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 800.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 5.5,
                        "sector": "Semi Materials",
                    },
                ],
            )
            summary_path.write_text(
                "\n".join(
                    [
                        "# 当日新闻优先级摘要",
                        "- 日期：2026-07-18",
                        "- 来源批次：data/news/news_batch_20260718.json",
                        "- 总新闻条数：3",
                        "- 高优先级展示条数：2/3",
                        "- 影响分布：风险扩散 1 | 主线强化 1 | 局部验证 1",
                        "- 过滤模式：high-priority-only",
                        "## 核心摘要",
                        "今天先看风险扩散，再看主线强化。",
                        "## 一句话建议",
                        "先防守，再确认强化是否获得跟随。",
                        "## 当日结论",
                        "风险扩散与主线强化并存。",
                        "## 操作提示",
                        "先读风险名单，再看强化名单。",
                        "## 阅读顺序",
                        "1. 先看风险优先名单",
                        "2. 再看强化跟踪名单",
                        "## 重点观察名单",
                        "### 风险优先名单",
                        "- 中微公司",
                        "- 北方华创",
                        "### 强化跟踪名单",
                        "- 中巨芯-U",
                        "## 建议动作",
                        "### 风险优先动作",
                        "- 先确认设备链是否同步承压",
                        "### 强化跟踪动作",
                        "- 先确认气体链是否获得跟随",
                        "## 优先级通道",
                        "- 来源：data/news/news_batch_20260718.json",
                        "- 条数：2",
                    ]
                ),
                encoding="utf-8",
            )

            with patch(
                "app.dashboard.overview._find_latest_priority_summary_path",
                return_value=summary_path,
            ):
                payload = build_dashboard_payload(database_path)

            summary = payload["today_priority_summary"]
            self.assertEqual("2026-07-18", summary["summary_date"])
            self.assertEqual(3, summary["total_items"])
            self.assertEqual(2, summary["shown_items"])
            self.assertEqual(
                "今天先看风险扩散，再看主线强化。",
                summary["core_summary"],
            )
            self.assertEqual(2, len(summary["read_order"]))
            self.assertEqual(2, summary["watch_group_count"])
            self.assertIn("风险优先名单", summary["watch_rows"][0])
            self.assertTrue(summary["action_rows"])
            self.assertEqual(
                "风险扩散 1 | 主线强化 1 | 局部验证 1",
                summary["impact_summary"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_counts_negative_alerts_separately(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 800.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 5.5,
                        "sector": "Semi Materials",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "price_spike",
                        "level": "orange",
                        "message": "GiantChip-U surged 8.6% intraday",
                        "related_stocks": "GiantChip-U",
                        "direction": "Semi Materials",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "news_flash",
                        "level": "red",
                        "message": "Export control risk is disturbing chip sentiment",
                        "related_stocks": "GiantChip-U",
                        "direction": "Semi Materials",
                    },
                ],
            )

            with patch(
                "app.dashboard.overview._find_latest_priority_summary_path",
                return_value=None,
            ):
                payload = build_dashboard_payload(database_path)

            self.assertEqual(1, payload["positive_alert_count"])
            self.assertEqual(1, payload["negative_alert_count"])
            self.assertEqual(
                "Main line: Semi Materials remains the clearest strength.",
                payload["mainline_summary"],
            )
            self.assertEqual(
                "Risk state: watch closely; risk is present but not dominant.",
                payload["risk_summary"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_can_select_historical_batch(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 09:35:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.34,
                        "pct_chg": 4.2,
                        "turnover": 300.0,
                        "volume_ratio": 1.8,
                        "turnover_rate": 3.1,
                        "sector": "Semi Materials",
                        "quote_source": "eastmoney-direct",
                    },
                    {
                        "timestamp": "2026-06-20 09:35:00",
                        "code": "002371",
                        "name": "FabEquip",
                        "price": 300.0,
                        "pct_chg": 2.0,
                        "turnover": 600.0,
                        "volume_ratio": 1.2,
                        "turnover_rate": 1.5,
                        "sector": "Semi Equipment",
                        "quote_source": "eastmoney-direct",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "code": "688549",
                        "name": "GiantChip-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 800.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 5.5,
                        "sector": "Semi Materials",
                        "quote_source": "local-json-snapshot",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-20 09:35:00",
                        "alert_type": "sector_move",
                        "level": "orange",
                        "message": "Equipment names followed through early",
                        "related_stocks": "FabEquip",
                        "direction": "Semi Equipment",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "price_spike",
                        "level": "orange",
                        "message": "GiantChip-U surged 8.6% intraday",
                        "related_stocks": "GiantChip-U",
                        "direction": "Semi Materials",
                    },
                ],
            )

            payload = build_dashboard_payload(
                database_path,
                selected_timestamp="2026-06-20 09:35:00",
            )

            self.assertEqual("2026-06-20 09:35:00", payload["latest_timestamp"])
            self.assertEqual("eastmoney-direct", payload["quote_source"])
            self.assertEqual(
                "eastmoney-direct (live direct endpoint)",
                payload["quote_source_display"],
            )
            self.assertEqual(
                "Quote status: live direct quotes active.",
                payload["quote_status_summary"],
            )
            self.assertEqual(2, payload["snapshot_count"])
            self.assertEqual(1, payload["alert_count"])
            self.assertEqual(1, payload["positive_alert_count"])
            self.assertEqual(0, payload["negative_alert_count"])
            self.assertEqual("Semi Materials", payload["strongest_sector"])
            self.assertEqual("Semi Materials", payload["strongest_sector_summary"]["sector"])
            self.assertEqual(
                "Equipment names followed through early",
                payload["latest_alerts"][0]["message"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_includes_stock_pool_health_summary(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)

            payload = build_dashboard_payload(database_path)
            stock_pool_health = payload["stock_pool_health"]

            self.assertIn(stock_pool_health["status"], {"valid", "invalid"})
            self.assertIn(stock_pool_health["risk_level"], {"clean", "warning", "blocking"})
            self.assertIsInstance(stock_pool_health["risk_text"], str)
            self.assertIsInstance(stock_pool_health["structure_summary"], str)
            self.assertIsInstance(stock_pool_health["record_count"], int)
            self.assertIsInstance(stock_pool_health["health_hints"], list)
            self.assertIsInstance(stock_pool_health["unknown_sectors"], list)
            self.assertIsInstance(stock_pool_health["registered_sectors"], list)
            self.assertIsInstance(stock_pool_health["unknown_chain_groups"], list)
            self.assertIsInstance(stock_pool_health["registered_chain_groups"], list)
            self.assertIsInstance(stock_pool_health["unknown_markets"], list)
            self.assertIsInstance(stock_pool_health["registered_markets"], list)
            self.assertIsInstance(stock_pool_health["unknown_pool_types"], list)
            self.assertIsInstance(stock_pool_health["registered_pool_types"], list)
            self.assertIsInstance(stock_pool_health["sector_counts"], dict)
            self.assertIsInstance(stock_pool_health["chain_group_counts"], dict)
            self.assertIsInstance(stock_pool_health["pool_type_counts"], dict)
            self.assertIsInstance(stock_pool_health["priority_counts"], dict)
            self.assertIsInstance(stock_pool_health["comparison_snapshot_path"], str)
            self.assertIsInstance(stock_pool_health["comparison_baseline_exists"], bool)
            self.assertIsInstance(stock_pool_health["comparison_baseline_saved_at"], str)
            self.assertIsInstance(stock_pool_health["comparison_tags"], list)
            self.assertIsInstance(stock_pool_health["comparison_tag_labels"], list)
            self.assertIsInstance(stock_pool_health["comparison_tag_groups"], list)
            self.assertIsInstance(stock_pool_health["comparison_highlight_summary"], str)
            self.assertIsInstance(stock_pool_health["comparison_summary"], str)
            self.assertIsInstance(stock_pool_health["comparison_change_rows"], list)
            self.assertIsInstance(stock_pool_health["drift_summary"], str)
            self.assertEqual(
                len(stock_pool_health["health_hints"]),
                stock_pool_health["hint_count"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_dashboard_payload_includes_stock_pool_health_comparison(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        stock_pool_path = temp_dir / "stock_pool.json"
        snapshot_path = temp_dir / "stock_pool_health_snapshot.json"
        try:
            initialize_database(database_path)
            baseline_records = [
                {
                    "code": "600501",
                    "name": "Alpha",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u7845\u7247",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "core",
                    "priority": 1,
                    "notes": "",
                },
                {
                    "code": "600502",
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
                    "code": "600501",
                    "name": "Alpha",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u7845\u7247",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "core",
                    "priority": 1,
                    "notes": "",
                },
                {
                    "code": "600503",
                    "name": "Gamma",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u524d\u9a71\u4f53",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "extended",
                    "priority": 2,
                    "notes": "",
                },
            ]
            stock_pool_path.write_text(
                json.dumps(baseline_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                    "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                },
                clear=False,
            ):
                save_stock_pool_health_snapshot(build_stock_pool_health_summary())

            stock_pool_path.write_text(
                json.dumps(changed_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                    "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                },
                clear=False,
            ):
                payload = build_dashboard_payload(database_path)

            stock_pool_health = payload["stock_pool_health"]
            self.assertTrue(stock_pool_health["comparison_baseline_exists"])
            self.assertEqual(
                str(snapshot_path),
                stock_pool_health["comparison_snapshot_path"],
            )
            self.assertIn(
                "\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316",
                stock_pool_health["comparison_summary"],
            )
            self.assertIn(
                "\u91cd\u70b9\u53d8\u5316\uff1a",
                stock_pool_health["comparison_highlight_summary"],
            )
            self.assertIn(
                "Priority-1 Focus Down",
                stock_pool_health["comparison_tags"],
            )
            self.assertIn(
                "\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d",
                stock_pool_health["comparison_tag_labels"],
            )
            self.assertTrue(
                any(
                    group["group_key"] == "priority_focus"
                    and group["group_label"] == "\u4f18\u5148\u7ea7\u7126\u70b9"
                    for group in stock_pool_health["comparison_tag_groups"]
                )
            )
            self.assertIn(
                "- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +1",
                stock_pool_health["comparison_change_rows"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

