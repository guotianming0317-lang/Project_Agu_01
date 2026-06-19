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


if __name__ == "__main__":
    unittest.main()
