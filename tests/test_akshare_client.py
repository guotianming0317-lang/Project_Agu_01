"""Tests for the AKShare client normalization layer."""

from __future__ import annotations

import unittest

from app.data_sources.akshare_client import (
    REQUIRED_QUOTE_COLUMNS,
    filter_to_universe,
    normalize_quote_fields,
)
from app.universe.stock_pool import get_all_stocks


class AkshareClientTests(unittest.TestCase):
    """Verify quote normalization before wiring the real datasource."""

    def test_normalize_quote_fields_renames_chinese_columns(self) -> None:
        raw_rows = [
            {
                "代码": "688549",
                "名称": "中巨芯-U",
                "最新价": 12.34,
                "涨跌幅": 8.6,
                "成交额": 123456789,
                "量比": 2.3,
                "换手率": 4.5,
                "市盈率-动态": 88.8,
                "市净率": 5.6,
                "总市值": 1000000000,
                "流通市值": 800000000,
            }
        ]

        result = normalize_quote_fields(raw_rows)

        self.assertEqual(REQUIRED_QUOTE_COLUMNS, list(result.columns))
        self.assertEqual("688549", result.loc[0, "code"])
        self.assertEqual("中巨芯-U", result.loc[0, "name"])
        self.assertEqual(12.34, result.loc[0, "price"])

    def test_normalize_quote_fields_keeps_required_columns_for_partial_rows(self) -> None:
        raw_rows = [{"代码": "688126", "名称": "沪硅产业"}]

        result = normalize_quote_fields(raw_rows)

        self.assertEqual(REQUIRED_QUOTE_COLUMNS, list(result.columns))
        self.assertIsNone(result.loc[0, "price"])

    def test_filter_to_universe_keeps_only_tracked_codes(self) -> None:
        quotes = normalize_quote_fields(
            [
                {"代码": "688549", "名称": "中巨芯-U", "最新价": 12.34},
                {"代码": "000001", "名称": "平安银行", "最新价": 11.11},
                {"代码": "688126", "名称": "沪硅产业", "最新价": 19.99},
            ]
        )

        result = filter_to_universe(quotes, get_all_stocks())

        self.assertEqual(["688549", "688126"], result["code"].tolist())
        self.assertTrue(all(code != "000001" for code in result["code"].tolist()))


if __name__ == "__main__":
    unittest.main()
