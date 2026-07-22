"""Tests for keyword-based news classification."""

from __future__ import annotations

import unittest

from app.analysis.news_classifier import classify_news


class NewsClassifierTests(unittest.TestCase):
    """Verify high-level sentiment routing for important keywords."""

    def test_classify_news_marks_major_risk_keywords_as_s_negative(self) -> None:
        result = classify_news(
            title="美国出口管制升级",
            content="实体清单继续扩大，行业承压。",
        )

        self.assertEqual("negative", result["sentiment"])
        self.assertEqual("S", result["level"])

    def test_classify_news_marks_supply_progress_as_positive(self) -> None:
        result = classify_news(
            title="公司产品进入批量供货阶段",
            content="核心材料完成客户认证并加速国产替代。",
        )

        self.assertEqual("positive", result["sentiment"])
        self.assertEqual("A", result["level"])

    def test_classify_news_infers_related_sector_from_keywords(self) -> None:
        result = classify_news(
            title="半导体设备出口管制升级",
            content="刻蚀、薄膜沉积等半导体设备链或再受影响。",
        )

        self.assertEqual("negative", result["sentiment"])
        self.assertEqual("S", result["level"])
        self.assertEqual("半导体设备", result["related_sector"])

    def test_classify_news_infers_related_stocks_from_text(self) -> None:
        result = classify_news(
            title="中巨芯U和华特气体加速批量供货",
            content="电子特气和半导体气体供应链继续改善。",
        )

        self.assertIn("中巨芯-U", result["related_stocks"])
        self.assertIn("华特气体", result["related_stocks"])


if __name__ == "__main__":
    unittest.main()
