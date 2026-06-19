"""Tests for the stock observation universe."""

from __future__ import annotations

import unittest

from app.universe.stock_pool import (
    get_all_stocks,
    get_high_priority_stocks,
    get_stocks_by_sector,
)


class StockPoolTests(unittest.TestCase):
    """Verify the static observation universe shape and content."""

    def test_get_all_stocks_returns_expected_core_sectors(self) -> None:
        stocks = get_all_stocks()

        self.assertGreaterEqual(len(stocks), 40)
        sectors = {stock["sector"] for stock in stocks}

        self.assertIn("AI光模块/CPO", sectors)
        self.assertIn("半导体材料/气体", sectors)
        self.assertIn("先进封装/Chiplet", sectors)

    def test_get_stocks_by_sector_filters_correctly(self) -> None:
        stocks = get_stocks_by_sector("半导体材料/气体")

        self.assertEqual(14, len(stocks))
        self.assertTrue(all(stock["sector"] == "半导体材料/气体" for stock in stocks))
        self.assertIn("688549", {stock["code"] for stock in stocks})

    def test_get_high_priority_stocks_only_returns_priority_one(self) -> None:
        stocks = get_high_priority_stocks()

        self.assertTrue(stocks)
        self.assertTrue(all(stock["priority"] == 1 for stock in stocks))


if __name__ == "__main__":
    unittest.main()
