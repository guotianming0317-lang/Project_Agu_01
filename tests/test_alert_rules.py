"""Tests for alert rule evaluation."""

from __future__ import annotations

import unittest

from app.alerts.alert_rules import evaluate_alerts


class AlertRuleTests(unittest.TestCase):
    """Verify phase-one alert triggers."""

    def test_evaluate_alerts_triggers_market_and_sector_alerts(self) -> None:
        market_rows = [
            {
                "sector": "半导体气体",
                "code": "688549",
                "name": "中巨芯-U",
                "pct_chg": 8.6,
                "volume_ratio": 2.8,
                "priority": 1,
            },
            {
                "sector": "半导体气体",
                "code": "688268",
                "name": "华特气体",
                "pct_chg": 5.2,
                "volume_ratio": 1.9,
                "priority": 1,
            },
            {
                "sector": "半导体材料",
                "code": "688019",
                "name": "安集科技",
                "pct_chg": 5.1,
                "volume_ratio": 2.1,
                "priority": 1,
            },
            {
                "sector": "AI服务器算力硬件",
                "code": "601138",
                "name": "工业富联",
                "pct_chg": 2.4,
                "volume_ratio": 1.2,
                "priority": 1,
            },
        ]

        alerts = evaluate_alerts(market_rows)
        alert_types = {alert["alert_type"] for alert in alerts}

        self.assertIn("price_spike", alert_types)
        self.assertIn("materials_focus", alert_types)
        self.assertIn("volume_spike", alert_types)
        self.assertNotIn("sector_move", alert_types)

    def test_evaluate_alerts_triggers_sector_move_for_single_split_sector(self) -> None:
        market_rows = [
            {
                "sector": "半导体材料",
                "code": "688019",
                "name": "安集科技",
                "pct_chg": 5.1,
                "volume_ratio": 2.1,
                "priority": 1,
            },
            {
                "sector": "半导体材料",
                "code": "688126",
                "name": "沪硅产业",
                "pct_chg": 5.6,
                "volume_ratio": 1.8,
                "priority": 1,
            },
            {
                "sector": "半导体材料",
                "code": "300666",
                "name": "江丰电子",
                "pct_chg": 6.3,
                "volume_ratio": 2.2,
                "priority": 1,
            },
        ]

        alerts = evaluate_alerts(market_rows)
        alert_types = {alert["alert_type"] for alert in alerts}

        self.assertIn("sector_move", alert_types)
        self.assertIn("materials_focus", alert_types)

    def test_evaluate_alerts_can_attach_stock_pool_context_to_high_value_alerts(self) -> None:
        market_rows = [
            {
                "sector": "半导体材料",
                "code": "688019",
                "name": "安集科技",
                "pct_chg": 5.1,
                "volume_ratio": 2.1,
                "priority": 1,
            },
            {
                "sector": "半导体材料",
                "code": "688126",
                "name": "沪硅产业",
                "pct_chg": 5.6,
                "volume_ratio": 1.8,
                "priority": 1,
            },
            {
                "sector": "半导体材料",
                "code": "300666",
                "name": "江丰电子",
                "pct_chg": 6.3,
                "volume_ratio": 2.2,
                "priority": 1,
            },
        ]

        alerts = evaluate_alerts(
            market_rows,
            stock_pool_summary={
                "structure_summary": "当前监控池偏向材料链，core池占比约2/3。",
                "health_hints": ["Priority-1 stocks are missing."],
            },
            stock_pool_comparison={
                "comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "产业链暴露",
                        "tag_labels": ["材料链加仓"],
                        "summary": "产业链暴露: 材料链加仓",
                    }
                ]
            },
        )

        sector_move_alert = next(
            alert for alert in alerts if alert["alert_type"] == "sector_move"
        )
        self.assertEqual(
            "当前监控池偏向材料链，core池占比约2/3。",
            sector_move_alert["stock_pool_structure_summary"],
        )
        self.assertEqual(
            "产业链暴露: 材料链加仓",
            sector_move_alert["stock_pool_comparison_tag_groups"][0]["summary"],
        )
        self.assertEqual(
            ["Priority-1 stocks are missing."],
            sector_move_alert["stock_pool_health_hints"],
        )

        volume_spike_alert = next(
            alert for alert in alerts if alert["alert_type"] == "volume_spike"
        )
        self.assertNotIn("stock_pool_structure_summary", volume_spike_alert)

    def test_evaluate_alerts_triggers_s_level_news_alert(self) -> None:
        alerts = evaluate_alerts(
            market_rows=[],
            news_event={
                "title": "美国出口管制升级",
                "sentiment": "negative",
                "level": "S",
                "related_sector": "半导体设备",
            },
            stock_pool_summary={
                "structure_summary": "当前监控池偏向设备链。",
                "health_hints": [],
            },
            stock_pool_comparison={
                "comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "产业链暴露",
                        "tag_labels": ["设备链加仓"],
                        "summary": "产业链暴露: 设备链加仓",
                    }
                ]
            },
        )

        self.assertEqual(1, len(alerts))
        self.assertEqual("news_flash", alerts[0]["alert_type"])
        self.assertEqual("红色", alerts[0]["level"])
        self.assertIn("美国出口管制升级", alerts[0]["message"])
        self.assertEqual("当前监控池偏向设备链。", alerts[0]["stock_pool_structure_summary"])

    def test_evaluate_alerts_attaches_stock_pool_highlight_summary(self) -> None:
        alerts = evaluate_alerts(
            market_rows=[],
            news_event={
                "title": "S-level test signal",
                "sentiment": "negative",
                "level": "S",
                "related_sector": "Equipment",
            },
            stock_pool_summary={
                "structure_summary": "Current pool leans to equipment.",
                "health_hints": [],
            },
            stock_pool_comparison={
                "highlight_summary": "Key change: equipment exposure increased (+2).",
                "comparison_tag_groups": [],
            },
        )

        self.assertEqual(
            "Key change: equipment exposure increased (+2).",
            alerts[0]["stock_pool_comparison_highlight_summary"],
        )


if __name__ == "__main__":
    unittest.main()
