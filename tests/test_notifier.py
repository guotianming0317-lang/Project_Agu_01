"""Tests for console notifier formatting."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from app.alerts.notifier import (
    build_alert_digest_text,
    build_notification_channel_status,
    format_alert_message,
    notify_console,
    select_alerts_for_digest,
)


class NotifierTests(unittest.TestCase):
    """Verify console output is human-friendly."""

    def test_build_notification_channel_status_defaults_to_console_only(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            status = build_notification_channel_status()

        self.assertEqual("console-only", status["status"])
        self.assertEqual("console", status["channel"])

    def test_build_notification_channel_status_reports_webhook_ready(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "MONITOR_WEBHOOK_URL": "https://example.com/webhook",
                "MONITOR_NOTIFICATION_CHANNEL": "feishu",
            },
            clear=True,
        ):
            status = build_notification_channel_status()

        self.assertEqual("webhook-ready", status["status"])
        self.assertEqual("feishu", status["channel"])

    def test_format_alert_message_uses_expected_layout(self) -> None:
        message = format_alert_message(
            {
                "level": "中优先级",
                "timestamp": "10:17",
                "direction": "半导体材料、半导体气体",
                "related_stocks": "中巨芯-U, 华特气体, 安集科技",
                "message": "材料线异动",
                "trend_state": "趋势增强",
                "focus": "关注中巨芯-U能否放量确认",
            }
        )

        self.assertIn("[中优先级] Alert", message)
        self.assertIn("10:17", message)
        self.assertIn("半导体材料、半导体气体", message)

    def test_format_alert_message_can_append_stock_pool_observation(self) -> None:
        message = format_alert_message(
            {
                "level": "中优先级",
                "timestamp": "10:17",
                "direction": "半导体材料",
                "related_stocks": "安集科技",
                "message": "材料链走强",
                "trend_state": "趋势增强",
                "focus": "观察材料链扩散",
                "stock_pool_structure_summary": "当前监控池偏向材料链，core 池占比约 2/3。",
                "stock_pool_comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "产业链暴露",
                        "tag_labels": ["材料链加仓"],
                        "summary": "产业链暴露 材料链加仓",
                    }
                ],
                "stock_pool_health_hints": ["Priority-1 stocks are missing."],
            }
        )

        self.assertIn("Stock pool observation:", message)
        self.assertIn("当前监控池偏向材料链", message)
        self.assertIn("产业链暴露", message)

    def test_select_alerts_for_digest_prioritizes_high_value_intraday(self) -> None:
        alerts = [
            {
                "alert_type": "volume_spike",
                "level": "中优先级",
                "direction": "半导体设备",
                "message": "成交量放大",
            },
            {
                "alert_type": "sector_move",
                "level": "中优先级",
                "direction": "半导体材料",
                "message": "材料线异动",
            },
            {
                "alert_type": "news_flash",
                "level": "高优先级",
                "direction": "半导体设备",
                "message": "出口管制升级",
            },
            {
                "alert_type": "price_spike",
                "level": "中优先级",
                "direction": "半导体气体",
                "message": "单日大涨",
            },
        ]

        selected = select_alerts_for_digest(alerts, stage="intraday")

        self.assertEqual(
            ["news_flash", "sector_move"],
            [alert["alert_type"] for alert in selected],
        )

    def test_build_alert_digest_text_can_include_grouped_context(self) -> None:
        digest = build_alert_digest_text(
            [
                {
                    "alert_type": "materials_focus",
                    "level": "中优先级",
                    "direction": "材料气体链",
                    "message": "材料气体链至少两只涨超 5%",
                    "stock_pool_comparison_tag_groups": [
                        {
                            "group_key": "chain_exposure",
                            "group_label": "产业链暴露",
                            "tag_labels": ["材料链加仓"],
                            "summary": "产业链暴露 材料链加仓",
                        }
                    ],
                }
            ],
            stage="close",
        )

        self.assertIn("Close Alert Digest", digest)
        self.assertIn("材料气体链", digest)
        self.assertIn("产业链暴露", digest)

    def test_select_alerts_for_digest_can_follow_preferred_type_strategy(self) -> None:
        alerts = [
            {
                "alert_type": "sector_move",
                "level": "中优先级",
                "direction": "半导体材料",
                "message": "材料线异动",
            },
            {
                "alert_type": "news_flash",
                "level": "高优先级",
                "direction": "半导体设备",
                "message": "出口管制升级",
            },
            {
                "alert_type": "materials_focus",
                "level": "中优先级",
                "direction": "材料气体链",
                "message": "材料链强化",
            },
        ]

        selected = select_alerts_for_digest(
            alerts,
            stage="intraday",
            digest_strategy={
                "high_value_only": True,
                "max_items": 2,
                "preferred_alert_types": ["news_flash", "materials_focus"],
            },
        )

        self.assertEqual(
            ["news_flash", "materials_focus"],
            [alert["alert_type"] for alert in selected],
        )

    def test_select_alerts_for_digest_can_prioritize_stage_chain_alignment(self) -> None:
        alerts = [
            {
                "alert_type": "sector_move",
                "level": "中优先级",
                "direction": "半导体材料",
                "message": "材料线异动",
            },
            {
                "alert_type": "news_flash",
                "level": "中优先级",
                "direction": "半导体设备",
                "message": "设备订单催化",
            },
        ]

        selected = select_alerts_for_digest(
            alerts,
            stage="close",
            digest_strategy={"preferred_chain_groups": ["设备"]},
        )

        self.assertEqual(
            ["news_flash", "sector_move"],
            [alert["alert_type"] for alert in selected],
        )

    def test_notify_console_prints_formatted_message(self) -> None:
        alert = {
            "level": "高优先级",
            "timestamp": "09:02",
            "direction": "半导体设备",
            "related_stocks": "北方华创",
            "message": "出口管制升级",
            "trend_state": "情绪升温",
            "focus": "关注龙头反馈与设备链扩散",
        }

        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            notify_console(alert)

        output = stdout.getvalue()
        self.assertIn("Time: 09:02", output)
        self.assertIn("北方华创", output)

    def test_format_alert_message_can_include_structure_highlight_summary(self) -> None:
        message = format_alert_message(
            {
                "level": "info",
                "timestamp": "10:17",
                "direction": "Materials",
                "related_stocks": "Alpha",
                "message": "Materials chain is active",
                "trend_state": "watch",
                "focus": "Confirm follow-through",
                "stock_pool_structure_summary": "Current pool remains material-chain heavy.",
                "stock_pool_comparison_highlight_summary": (
                    "Key change: materials exposure increased (+2)."
                ),
                "stock_pool_comparison_tag_groups": [],
                "stock_pool_health_hints": [],
            }
        )

        self.assertIn(
            "Key change: materials exposure increased (+2).",
            message,
        )

    def test_build_alert_digest_text_prefers_structure_highlight_summary(self) -> None:
        digest = build_alert_digest_text(
            [
                {
                    "alert_type": "materials_focus",
                    "level": "info",
                    "direction": "Materials",
                    "message": "Materials chain is active",
                    "stock_pool_comparison_highlight_summary": (
                        "Key change: materials exposure increased (+2)."
                    ),
                    "stock_pool_comparison_tag_groups": [
                        {
                            "group_key": "chain_exposure",
                            "group_label": "Chain exposure",
                            "tag_labels": ["Materials Exposure Up"],
                            "summary": "Chain exposure: materials exposure increased.",
                        }
                    ],
                }
            ],
            stage="close",
        )

        self.assertIn(
            "Key change: materials exposure increased (+2).",
            digest,
        )
        self.assertNotIn(
            "Chain exposure: materials exposure increased.",
            digest,
        )


if __name__ == "__main__":
    unittest.main()
