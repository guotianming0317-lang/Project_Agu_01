import unittest

from app.reports.us_market_overview import build_us_market_overview_text


class UsMarketOverviewTests(unittest.TestCase):
    def test_missing_snapshot_is_explicitly_not_fake(self) -> None:
        text = build_us_market_overview_text({"status": "unavailable"})
        self.assertIn("美股收盘概括", text)
        self.assertIn("暂无可用的美股收盘数据", text)
        self.assertIn("未使用演示值", text)

    def test_ready_snapshot_contains_required_top_level_sections(self) -> None:
        text = build_us_market_overview_text(
            {
                "status": "ready",
                "date": "2026-07-23",
                "source_name": "真实行情快照",
                "nasdaq": {
                    "open": "20,000",
                    "intraday": "20,100",
                    "close": "20,080",
                    "change": "+0.4%",
                    "trend": "高开后震荡",
                },
                "sox": {
                    "open": "5,500",
                    "intraday": "5,560",
                    "close": "5,540",
                    "change": "+0.7%",
                    "trend": "盘中走强",
                },
                "strong_sectors": ["半导体设备"],
                "weak_sectors": ["传统能源"],
                "sector_analysis": "科技成长相对强，能源偏弱。",
            }
        )
        for expected in (
            "纳斯达克综合指数",
            "费城半导体指数",
            "开盘",
            "盘中",
            "收盘",
            "强势板块：半导体设备",
            "弱势板块：传统能源",
            "科技成长相对强",
        ):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
