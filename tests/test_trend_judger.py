"""Tests for short-term trend judgement."""

from __future__ import annotations

import unittest

from app.analysis.trend_judger import judge_trend


class TrendJudgerTests(unittest.TestCase):
    """Verify trend-state classification and explainability."""

    def test_judge_trend_identifies_strong_trend(self) -> None:
        recent_history = [
            {"close": 10.1, "turnover": 100.0},
            {"close": 10.3, "turnover": 110.0},
            {"close": 10.5, "turnover": 115.0},
            {"close": 10.8, "turnover": 120.0},
            {"close": 11.0, "turnover": 125.0},
            {"close": 11.2, "turnover": 130.0},
            {"close": 11.4, "turnover": 135.0},
            {"close": 11.7, "turnover": 140.0},
            {"close": 12.0, "turnover": 145.0},
            {"close": 12.2, "turnover": 150.0},
            {"close": 12.5, "turnover": 155.0},
            {"close": 12.8, "turnover": 160.0},
            {"close": 13.0, "turnover": 165.0},
            {"close": 13.3, "turnover": 170.0},
            {"close": 13.5, "turnover": 175.0},
            {"close": 13.8, "turnover": 180.0},
            {"close": 14.0, "turnover": 185.0},
            {"close": 14.3, "turnover": 190.0},
            {"close": 14.6, "turnover": 195.0},
            {"close": 15.0, "turnover": 200.0},
        ]
        realtime_quote = {
            "code": "688019",
            "name": "安集科技",
            "price": 15.4,
            "pct_chg": 6.2,
            "turnover": 280.0,
            "intraday_high_pct": 6.8,
            "close_pct_chg": 6.2,
        }

        result = judge_trend(recent_history, realtime_quote, sector_pct_chg=3.1)

        self.assertEqual("强趋势", result["trend_state"])
        self.assertGreater(result["trend_score"], 0.7)
        self.assertIn("MA", result["reason"])

    def test_judge_trend_identifies_intraday_pullback(self) -> None:
        recent_history = [{"close": 20 + index * 0.1, "turnover": 100.0} for index in range(20)]
        realtime_quote = {
            "code": "688549",
            "name": "中巨芯-U",
            "price": 22.1,
            "pct_chg": 2.1,
            "turnover": 180.0,
            "intraday_high_pct": 7.0,
            "close_pct_chg": 2.1,
        }

        result = judge_trend(recent_history, realtime_quote, sector_pct_chg=2.8)

        self.assertEqual("冲高回落", result["trend_state"])
        self.assertIn("intraday_high_pct", result["reason"])

    def test_judge_trend_identifies_fading_state(self) -> None:
        recent_history = [
            {"close": 30.0, "turnover": 100.0},
            {"close": 29.8, "turnover": 105.0},
            {"close": 29.5, "turnover": 110.0},
            {"close": 29.2, "turnover": 115.0},
            {"close": 29.0, "turnover": 120.0},
            {"close": 28.7, "turnover": 125.0},
            {"close": 28.5, "turnover": 130.0},
            {"close": 28.1, "turnover": 135.0},
            {"close": 27.9, "turnover": 140.0},
            {"close": 27.6, "turnover": 145.0},
            {"close": 27.4, "turnover": 150.0},
            {"close": 27.1, "turnover": 155.0},
            {"close": 26.9, "turnover": 160.0},
            {"close": 26.6, "turnover": 165.0},
            {"close": 26.4, "turnover": 170.0},
            {"close": 26.0, "turnover": 175.0},
            {"close": 25.8, "turnover": 180.0},
            {"close": 25.5, "turnover": 185.0},
            {"close": 25.2, "turnover": 190.0},
            {"close": 25.0, "turnover": 195.0},
        ]
        realtime_quote = {
            "code": "300054",
            "name": "鼎龙股份",
            "price": 24.5,
            "pct_chg": -3.2,
            "turnover": 260.0,
            "intraday_high_pct": 0.5,
            "close_pct_chg": -3.2,
        }

        result = judge_trend(recent_history, realtime_quote, sector_pct_chg=1.1)

        self.assertEqual("退潮", result["trend_state"])
        self.assertLess(result["trend_score"], 0.4)
        self.assertIn("ma10", result["reason"].lower())


if __name__ == "__main__":
    unittest.main()
