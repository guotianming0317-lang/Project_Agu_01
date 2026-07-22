"""Tests for sector leader detection."""

from __future__ import annotations

import unittest

import pandas as pd

from app.analysis.leader_detector import detect_sector_leaders


class LeaderDetectorTests(unittest.TestCase):
    """Verify ranking and leader classification behavior."""

    def test_detect_sector_leaders_returns_top_three_per_sector(self) -> None:
        quotes = pd.DataFrame(
            [
                {
                    "sector": "AI服务器/算力硬件",
                    "code": "601138",
                    "name": "工业富联",
                    "pct_chg": 6.2,
                    "turnover": 1200.0,
                    "turnover_rate": 3.2,
                    "volume_ratio": 2.0,
                    "priority": 1,
                },
                {
                    "sector": "AI服务器/算力硬件",
                    "code": "000977",
                    "name": "浪潮信息",
                    "pct_chg": 4.8,
                    "turnover": 1500.0,
                    "turnover_rate": 2.8,
                    "volume_ratio": 1.6,
                    "priority": 1,
                },
                {
                    "sector": "AI服务器/算力硬件",
                    "code": "603019",
                    "name": "中科曙光",
                    "pct_chg": 3.5,
                    "turnover": 900.0,
                    "turnover_rate": 1.8,
                    "volume_ratio": 1.2,
                    "priority": 1,
                },
                {
                    "sector": "AI服务器/算力硬件",
                    "code": "000938",
                    "name": "紫光股份",
                    "pct_chg": 1.2,
                    "turnover": 300.0,
                    "turnover_rate": 0.9,
                    "volume_ratio": 0.8,
                    "priority": 2,
                },
                {
                    "sector": "半导体材料/气体",
                    "code": "688549",
                    "name": "中巨芯-U",
                    "pct_chg": 8.6,
                    "turnover": 800.0,
                    "turnover_rate": 5.5,
                    "volume_ratio": 2.8,
                    "priority": 1,
                },
                {
                    "sector": "半导体材料/气体",
                    "code": "688268",
                    "name": "华特气体",
                    "pct_chg": 5.2,
                    "turnover": 500.0,
                    "turnover_rate": 3.2,
                    "volume_ratio": 1.9,
                    "priority": 1,
                },
            ]
        )

        result = detect_sector_leaders(quotes)

        self.assertEqual(5, len(result))
        self.assertEqual(3, len(result[result["sector"] == "AI服务器/算力硬件"]))
        ai_rows = result[result["sector"] == "AI服务器/算力硬件"]
        self.assertEqual("601138", ai_rows.iloc[0]["code"])
        self.assertGreaterEqual(ai_rows.iloc[0]["leader_score"], ai_rows.iloc[1]["leader_score"])

    def test_detect_sector_leaders_assigns_explainable_types(self) -> None:
        quotes = pd.DataFrame(
            [
                {
                    "sector": "半导体材料/气体",
                    "code": "688549",
                    "name": "中巨芯-U",
                    "pct_chg": 9.1,
                    "turnover": 700.0,
                    "turnover_rate": 5.8,
                    "volume_ratio": 2.6,
                    "priority": 1,
                },
                {
                    "sector": "半导体材料/气体",
                    "code": "300666",
                    "name": "江丰电子",
                    "pct_chg": 4.2,
                    "turnover": 1800.0,
                    "turnover_rate": 2.7,
                    "volume_ratio": 1.4,
                    "priority": 1,
                },
                {
                    "sector": "半导体材料/气体",
                    "code": "688019",
                    "name": "安集科技",
                    "pct_chg": 6.4,
                    "turnover": 900.0,
                    "turnover_rate": 4.1,
                    "volume_ratio": 1.9,
                    "priority": 1,
                },
            ]
        )

        result = detect_sector_leaders(quotes)
        type_map = dict(zip(result["code"], result["leader_type"]))
        reason_map = dict(zip(result["code"], result["reason"]))

        self.assertEqual("情绪龙头", type_map["688549"])
        self.assertEqual("成交额龙头", type_map["300666"])
        self.assertEqual("趋势龙头", type_map["688019"])
        self.assertIn("涨跌幅", reason_map["688549"])


if __name__ == "__main__":
    unittest.main()
