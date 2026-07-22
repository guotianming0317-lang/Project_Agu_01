"""Tests for the AKShare client normalization layer."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from app.data_sources.akshare_client import (
    EASTMONEY_DIRECT_SOURCE,
    LOCAL_SNAPSHOT_SOURCE,
    REQUIRED_QUOTE_COLUMNS,
    _default_eastmoney_fetcher,
    _default_local_snapshot_fetcher,
    fetch_realtime_quotes,
    filter_to_universe,
    get_quote_source,
    normalize_quote_fields,
)
from app.universe.stock_pool import get_all_stocks


class AkshareClientTests(unittest.TestCase):
    """Verify quote normalization and adapter behavior."""

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

    def test_fetch_realtime_quotes_uses_adapter_and_filters_to_universe(self) -> None:
        def fake_fetcher() -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {"代码": "688549", "名称": "中巨芯-U", "最新价": 12.34, "涨跌幅": 8.6},
                    {"代码": "000001", "名称": "平安银行", "最新价": 11.11, "涨跌幅": 0.2},
                    {"代码": "688126", "名称": "沪硅产业", "最新价": 19.99, "涨跌幅": 3.5},
                ]
            )

        result = fetch_realtime_quotes(raw_fetcher=fake_fetcher)

        self.assertEqual(REQUIRED_QUOTE_COLUMNS, list(result.columns))
        self.assertEqual(["688549", "688126"], result["code"].tolist())

    def test_fetch_realtime_quotes_returns_empty_frame_on_fetch_failure(self) -> None:
        def broken_fetcher() -> pd.DataFrame:
            raise RuntimeError("network unavailable")

        result = fetch_realtime_quotes(raw_fetcher=broken_fetcher)

        self.assertTrue(result.empty)
        self.assertEqual(REQUIRED_QUOTE_COLUMNS, list(result.columns))

    def test_fetch_realtime_quotes_silently_falls_back_when_akshare_is_missing(self) -> None:
        def direct_fetcher() -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {"code": "688549", "name": "中巨芯-U", "price": 12.34},
                    {"code": "688126", "name": "沪硅产业", "price": 19.99},
                ]
            )

        def missing_akshare_fetcher() -> pd.DataFrame:
            raise ModuleNotFoundError("No module named 'akshare'")

        with patch("app.data_sources.akshare_client.LOGGER.warning") as warning_log:
            result = fetch_realtime_quotes(
                raw_fetcher=missing_akshare_fetcher,
                backup_fetcher=direct_fetcher,
            )

        self.assertFalse(result.empty)
        self.assertEqual(REQUIRED_QUOTE_COLUMNS, list(result.columns))
        self.assertEqual(EASTMONEY_DIRECT_SOURCE, get_quote_source(result))
        warning_log.assert_not_called()

    def test_fetch_realtime_quotes_falls_back_to_direct_source_when_primary_breaks(self) -> None:
        def broken_fetcher() -> pd.DataFrame:
            raise RuntimeError("RemoteDisconnected")

        def direct_fetcher() -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {"code": "688549", "name": "中巨芯-U", "price": 12.34},
                    {"code": "688126", "name": "沪硅产业", "price": 19.99},
                ]
            )

        with patch("app.data_sources.akshare_client.LOGGER.warning") as warning_log:
            result = fetch_realtime_quotes(
                raw_fetcher=broken_fetcher,
                backup_fetcher=direct_fetcher,
            )

        self.assertEqual(["688549", "688126"], result["code"].tolist())
        self.assertEqual(EASTMONEY_DIRECT_SOURCE, get_quote_source(result))
        warning_log.assert_not_called()

    def test_default_eastmoney_fetcher_prefers_curl_market_path_when_available(self) -> None:
        market_payload = {
            "data": {
                "diff": [
                    {"f12": "688549", "f14": "中巨芯-U", "f2": 12.34, "f3": 8.6},
                    {"f12": "688126", "f14": "沪硅产业", "f2": 19.99, "f3": 3.5},
                    {"f12": "000001", "f14": "平安银行", "f2": 11.11, "f3": 0.2},
                ]
            }
        }

        with (
            patch("app.data_sources.akshare_client.shutil.which", return_value="curl.exe"),
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_curl",
                return_value=market_payload,
            ) as market_fetch,
        ):
            result = _default_eastmoney_fetcher()

        self.assertEqual(["688549", "688126", "000001"], result["code"].tolist())
        market_fetch.assert_called_once_with("curl.exe")

    def test_default_eastmoney_fetcher_prefers_powershell_market_path_when_available(self) -> None:
        market_payload = {
            "data": {
                "diff": [
                    {"f12": "688549", "f14": "涓法鑺?U", "f2": 12.34, "f3": 8.6},
                    {"f12": "688126", "f14": "娌浜т笟", "f2": 19.99, "f3": 3.5},
                ]
            }
        }

        with (
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_powershell",
                return_value=market_payload,
            ) as powershell_fetch,
            patch("app.data_sources.akshare_client.shutil.which") as which_mock,
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_curl",
            ) as curl_fetch,
        ):
            result = _default_eastmoney_fetcher()

        self.assertEqual(["688549", "688126"], result["code"].tolist())
        self.assertEqual("eastmoney-market-powershell", result.attrs.get("fetch_path"))
        powershell_fetch.assert_called_once_with()
        curl_fetch.assert_not_called()
        which_mock.assert_not_called()

    def test_default_eastmoney_fetcher_falls_back_to_curl_when_powershell_market_path_fails(self) -> None:
        market_payload = {
            "data": {
                "diff": [
                    {"f12": "688549", "f14": "涓法鑺?U", "f2": 12.34, "f3": 8.6},
                    {"f12": "688126", "f14": "娌浜т笟", "f2": 19.99, "f3": 3.5},
                ]
            }
        }

        with (
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_powershell",
                side_effect=RuntimeError("RemoteDisconnected"),
            ) as powershell_fetch,
            patch("app.data_sources.akshare_client.shutil.which", return_value="curl.exe"),
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_curl",
                return_value=market_payload,
            ) as curl_fetch,
        ):
            result = _default_eastmoney_fetcher()

        self.assertEqual(["688549", "688126"], result["code"].tolist())
        self.assertEqual("eastmoney-market-curl", result.attrs.get("fetch_path"))
        powershell_fetch.assert_called_once_with()
        curl_fetch.assert_called_once_with("curl.exe")

    def test_default_eastmoney_fetcher_falls_back_to_tracked_secids_when_market_payload_misses_universe(self) -> None:
        market_payload = {
            "data": {
                "diff": [
                    {"f12": "000001", "f14": "other", "f2": 11.11, "f3": 0.2},
                ]
            }
        }
        tracked_payload = {
            "data": {
                "diff": [
                    {"f12": "688549", "f14": "tracked-a", "f2": 12.34, "f3": 8.6},
                    {"f12": "688126", "f14": "tracked-b", "f2": 19.99, "f3": 3.5},
                ]
            }
        }

        with (
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_market_payload_with_powershell",
                return_value=market_payload,
            ),
            patch(
                "app.data_sources.akshare_client._fetch_eastmoney_payload_for_secids",
                return_value=tracked_payload,
            ) as tracked_fetch,
        ):
            result = _default_eastmoney_fetcher()

        self.assertEqual(["688549", "688126"], result["code"].tolist())
        self.assertEqual("eastmoney-secid-batch", result.attrs.get("fetch_path"))
        tracked_fetch.assert_called()

    def test_default_local_snapshot_fetcher_supports_eastmoney_payload_shape(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        snapshot_path = temp_dir / "latest_quotes.json"
        try:
            snapshot_path.write_text(
                json.dumps(
                    {
                        "data": {
                            "diff": [
                                {"f12": "688549", "f14": "中巨芯-U", "f2": 12.34, "f3": 8.6},
                                {"f12": "688126", "f14": "沪硅产业", "f2": 19.99, "f3": 3.5},
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                "os.environ",
                {"MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path)},
                clear=False,
            ):
                result = _default_local_snapshot_fetcher()

            self.assertEqual(["688549", "688126"], result["code"].tolist())
            self.assertEqual(12.34, result.loc[0, "price"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_realtime_quotes_falls_back_to_local_snapshot_when_network_paths_fail(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        snapshot_path = temp_dir / "latest_quotes.json"
        try:
            snapshot_path.write_text(
                json.dumps(
                    [
                        {"code": "688549", "name": "中巨芯-U", "price": 12.34},
                        {"code": "688126", "name": "沪硅产业", "price": 19.99},
                    ]
                ),
                encoding="utf-8",
            )
            with (
                patch.dict(
                    "os.environ",
                    {"MONITOR_LOCAL_QUOTE_PATH": str(snapshot_path)},
                    clear=False,
                ),
                patch(
                    "app.data_sources.akshare_client._default_eastmoney_fetcher",
                    side_effect=RuntimeError("curl exit status 7"),
                ),
                patch(
                    "app.data_sources.akshare_client._default_akshare_fetcher",
                    side_effect=RuntimeError("RemoteDisconnected"),
                ),
                patch("app.data_sources.akshare_client.LOGGER.warning") as warning_log,
            ):
                result = fetch_realtime_quotes()

            self.assertEqual(["688549", "688126"], result["code"].tolist())
            self.assertEqual(LOCAL_SNAPSHOT_SOURCE, get_quote_source(result))
            warning_log.assert_not_called()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
