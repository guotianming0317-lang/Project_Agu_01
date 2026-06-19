"""AKShare client wrapper for A-share market data."""

from __future__ import annotations

from typing import Any
import logging

import pandas as pd


LOGGER = logging.getLogger(__name__)

REQUIRED_QUOTE_COLUMNS = [
    "code",
    "name",
    "price",
    "pct_chg",
    "turnover",
    "volume_ratio",
    "turnover_rate",
    "pe_dynamic",
    "pb",
    "total_market_cap",
    "float_market_cap",
]

RAW_TO_NORMALIZED_FIELD_MAP = {
    "代码": "code",
    "名称": "name",
    "最新价": "price",
    "涨跌幅": "pct_chg",
    "成交额": "turnover",
    "量比": "volume_ratio",
    "换手率": "turnover_rate",
    "市盈率-动态": "pe_dynamic",
    "市净率": "pb",
    "总市值": "total_market_cap",
    "流通市值": "float_market_cap",
}


def fetch_realtime_quotes() -> pd.DataFrame:
    """Fetch realtime quotes for the observation universe.

    This is a placeholder in phase one. A later step will connect AKShare.
    """
    LOGGER.info("Realtime quote fetch requested, returning empty frame in phase one.")
    return pd.DataFrame(
        columns=REQUIRED_QUOTE_COLUMNS
    )


def normalize_quote_fields(raw_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Normalize raw quote payloads into a dataframe.

    The function accepts dict rows shaped like AKShare output and returns a
    stable dataframe schema for downstream analysis modules.
    """
    if not raw_rows:
        return pd.DataFrame(columns=REQUIRED_QUOTE_COLUMNS)

    dataframe = pd.DataFrame(raw_rows).rename(columns=RAW_TO_NORMALIZED_FIELD_MAP)

    for column in REQUIRED_QUOTE_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = None

    return dataframe[REQUIRED_QUOTE_COLUMNS]


def filter_to_universe(
    quotes: pd.DataFrame,
    universe: list[dict[str, Any]],
) -> pd.DataFrame:
    """Keep only quotes that belong to the configured stock universe."""
    if quotes.empty:
        return pd.DataFrame(columns=REQUIRED_QUOTE_COLUMNS)

    tracked_codes = {str(stock["code"]) for stock in universe}
    filtered = quotes[quotes["code"].astype(str).isin(tracked_codes)].copy()
    return filtered.reset_index(drop=True)
