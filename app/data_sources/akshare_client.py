"""Realtime A-share quote adapters with AKShare-first fallback behavior."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
import json
import logging
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import time
from urllib.parse import urlencode
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener

import pandas as pd

from app.universe.stock_pool import get_all_stocks


LOGGER = logging.getLogger(__name__)
QUOTE_SOURCE_ATTR = "quote_source"
FETCH_PATH_ATTR = "fetch_path"
AKSHARE_SOURCE = "akshare"
EASTMONEY_DIRECT_SOURCE = "eastmoney-direct"
LOCAL_SNAPSHOT_SOURCE = "local-json-snapshot"
EASTMONEY_QUOTE_ENDPOINT = "https://push2.eastmoney.com/api/qt/ulist.np/get"
EASTMONEY_MARKET_QUOTE_ENDPOINT = "https://82.push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_MARKET_QUOTE_ENDPOINT_FALLBACK = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_QUERY_PARAMS = {
    "fltt": "2",
    "invt": "2",
    "fields": "f12,f14,f2,f3,f5,f6,f8,f9,f10,f20,f21,f23",
}
EASTMONEY_MARKET_QUERY_PARAMS = {
    "pn": "1",
    "pz": "6000",
    "po": "1",
    "np": "1",
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": "2",
    "invt": "2",
    "fid": "f3",
    "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
    "fields": "f12,f14,f2,f3,f5,f6,f8,f9,f10,f20,f21,f23",
}
EASTMONEY_FIELD_MAP = {
    "f12": "code",
    "f14": "name",
    "f2": "price",
    "f3": "pct_chg",
    "f5": "volume",
    "f6": "turnover",
    "f8": "turnover_rate",
    "f9": "pe_dynamic",
    "f10": "volume_ratio",
    "f20": "total_market_cap",
    "f21": "float_market_cap",
    "f23": "pb",
}

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
    "浠ｇ爜": "code",
    "名称": "name",
    "鍚嶇О": "name",
    "最新价": "price",
    "鏈€鏂颁环": "price",
    "涨跌幅": "pct_chg",
    "娑ㄨ穼骞?": "pct_chg",
    "成交额": "turnover",
    "鎴愪氦棰?": "turnover",
    "量比": "volume_ratio",
    "閲忔瘮": "volume_ratio",
    "换手率": "turnover_rate",
    "鎹㈡墜鐜?": "turnover_rate",
    "市盈率-动态": "pe_dynamic",
    "甯傜泩鐜?鍔ㄦ€?": "pe_dynamic",
    "市净率": "pb",
    "甯傚噣鐜?": "pb",
    "总市值": "total_market_cap",
    "鎬诲競鍊?": "total_market_cap",
    "流通市值": "float_market_cap",
    "娴侀€氬競鍊?": "float_market_cap",
}


def fetch_realtime_quotes(
    raw_fetcher: Callable[[], pd.DataFrame] | None = None,
    backup_fetcher: Callable[[], pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Fetch realtime quotes and normalize them for the configured universe.

    When `raw_fetcher` is omitted, this function tries to call
    `ak.stock_zh_a_spot_em()` first and then falls back to a direct Eastmoney
    HTTP adapter. In tests or offline contexts, callers can inject fake
    fetchers and keep the rest of the pipeline unchanged.
    """
    if raw_fetcher is None and backup_fetcher is None:
        primary_fetcher = _default_eastmoney_fetcher
        primary_source = EASTMONEY_DIRECT_SOURCE
        secondary_fetcher = _default_akshare_fetcher
        secondary_source = AKSHARE_SOURCE
        tertiary_fetcher = _default_local_snapshot_fetcher
        tertiary_source = LOCAL_SNAPSHOT_SOURCE
    else:
        primary_fetcher = raw_fetcher or _default_akshare_fetcher
        primary_source = AKSHARE_SOURCE
        if backup_fetcher is not None:
            secondary_fetcher = backup_fetcher
            secondary_source = EASTMONEY_DIRECT_SOURCE
        else:
            secondary_fetcher = None
            secondary_source = ""
        tertiary_fetcher = None
        tertiary_source = ""

    primary_error: Exception | None = None
    primary_result = _run_quote_fetcher(primary_fetcher, source=primary_source)
    if not primary_result.empty:
        return primary_result

    try:
        primary_error = getattr(primary_result, "_fetch_error", None)
    except Exception:  # noqa: BLE001 - defensive metadata access
        primary_error = None

    if secondary_fetcher is None:
        if primary_error is not None and not _is_missing_akshare_error(primary_error):
            LOGGER.warning("Realtime quote fetch failed, returning empty frame: %s", primary_error)
        return _empty_quotes_frame()

    secondary_result = _run_quote_fetcher(secondary_fetcher, source=secondary_source)
    if not secondary_result.empty:
        return secondary_result

    secondary_error: Exception | None = None
    try:
        secondary_error = getattr(secondary_result, "_fetch_error", None)
    except Exception:  # noqa: BLE001 - defensive metadata access
        secondary_error = None

    if tertiary_fetcher is not None:
        tertiary_result = _run_quote_fetcher(tertiary_fetcher, source=tertiary_source)
        if not tertiary_result.empty:
            return tertiary_result
        tertiary_error: Exception | None = None
        try:
            tertiary_error = getattr(tertiary_result, "_fetch_error", None)
        except Exception:  # noqa: BLE001 - defensive metadata access
            tertiary_error = None
        if tertiary_error is not None:
            secondary_error = tertiary_error

    if secondary_error is not None:
        LOGGER.warning("Realtime quote fetch failed, returning empty frame: %s", secondary_error)
    elif primary_error is not None and not _is_missing_akshare_error(primary_error):
        LOGGER.warning("Realtime quote fetch failed, returning empty frame: %s", primary_error)

    return _empty_quotes_frame()


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


def get_quote_source(quotes: pd.DataFrame) -> str:
    """Return the attached quote source label for one normalized dataframe."""
    if not isinstance(quotes, pd.DataFrame):
        return ""
    return str(quotes.attrs.get(QUOTE_SOURCE_ATTR, "")).strip()


def get_fetch_path(quotes: pd.DataFrame) -> str:
    """Return the attached fetch-path label for one normalized dataframe."""
    if not isinstance(quotes, pd.DataFrame):
        return ""
    return str(quotes.attrs.get(FETCH_PATH_ATTR, "")).strip()


def build_quote_source_display_text(source: str) -> str:
    """Build one user-facing quote-source label with a short explanation."""
    normalized_source = str(source or "").strip()
    source_labels = {
        EASTMONEY_DIRECT_SOURCE: "eastmoney-direct (live direct endpoint)",
        AKSHARE_SOURCE: "akshare (live adapter)",
        LOCAL_SNAPSHOT_SOURCE: "local-json-snapshot (local real quote snapshot)",
        "demo-fallback": "demo-fallback (built-in demo data)",
    }
    return source_labels.get(normalized_source, normalized_source or "unknown")


def get_local_quote_snapshot_path() -> Path:
    """Return the configured local quote snapshot path."""
    configured_path = str(os.getenv("MONITOR_LOCAL_QUOTE_PATH", "")).strip()
    if configured_path:
        return Path(configured_path)
    return Path("data/runtime/latest_quotes.json")


def load_local_quote_snapshot(snapshot_path: Path | None = None) -> pd.DataFrame:
    """Load one local realtime-quote snapshot and normalize it."""
    resolved_path = snapshot_path or get_local_quote_snapshot_path()
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Local quote snapshot not found: {resolved_path.as_posix()}"
        )
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    normalized_rows = _normalize_local_snapshot_payload(payload)
    return normalize_quote_fields(normalized_rows)


def detect_local_quote_snapshot_shape(payload: object) -> str:
    """Return a compact label for the supported local snapshot JSON shape."""
    if isinstance(payload, dict):
        if "rows" in payload and isinstance(payload.get("rows"), list):
            return "rows-array"
        data_block = payload.get("data", {})
        if isinstance(data_block, dict) and "diff" in data_block and isinstance(
            data_block.get("diff"), list
        ):
            return "eastmoney-data-diff"
    if isinstance(payload, list):
        return "plain-array"
    return "unsupported"


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


def _default_akshare_fetcher() -> pd.DataFrame:
    """Call the real AKShare endpoint when available."""
    import akshare as ak

    return ak.stock_zh_a_spot_em()


def _default_local_snapshot_fetcher() -> pd.DataFrame:
    """Load one local realtime-quote snapshot when network fetchers are unavailable."""
    return load_local_quote_snapshot()


def _default_eastmoney_fetcher() -> pd.DataFrame:
    """Call Eastmoney directly and shape the payload into the normalized schema."""
    market_payload_error: Exception | None = None
    fetch_path = ""
    universe = get_all_stocks()
    try:
        payload = _fetch_eastmoney_market_payload_with_powershell()
        fetch_path = "eastmoney-market-powershell"
        diff_rows = payload.get("data", {}).get("diff", [])
        if not isinstance(diff_rows, list):
            raise ValueError("Eastmoney market quote payload is missing data.diff rows.")
    except Exception as exc:  # noqa: BLE001 - fallback to the next proven direct path
        market_payload_error = exc
        curl_executable = shutil.which("curl.exe") or shutil.which("curl")
        if curl_executable:
            payload = _fetch_eastmoney_market_payload_with_curl(curl_executable)
            fetch_path = "eastmoney-market-curl"
            diff_rows = payload.get("data", {}).get("diff", [])
            if not isinstance(diff_rows, list):
                raise ValueError("Eastmoney market quote payload is missing data.diff rows.")
        else:
            tracked_secids = _build_eastmoney_secids(get_all_stocks())
            fetch_path = "eastmoney-secid-batch"
            diff_rows = []
            for secid_chunk in _chunk_values(tracked_secids, size=20):
                payload = _fetch_eastmoney_payload_for_secids(secid_chunk)
                chunk_rows = payload.get("data", {}).get("diff", [])
                if not isinstance(chunk_rows, list):
                    raise ValueError("Eastmoney direct quote payload is missing data.diff rows.")
                diff_rows.extend(row for row in chunk_rows if isinstance(row, dict))
            if not diff_rows and market_payload_error is not None:
                raise market_payload_error

    if not _diff_rows_include_universe_codes(diff_rows, universe):
        diff_rows = _fetch_eastmoney_tracked_diff_rows(universe)
        fetch_path = "eastmoney-secid-batch"

    normalized_rows = [
        {target_key: raw_row.get(source_key) for source_key, target_key in EASTMONEY_FIELD_MAP.items()}
        for raw_row in diff_rows
    ]

    return _attach_fetch_path(pd.DataFrame(normalized_rows), fetch_path)


def _fetch_eastmoney_tracked_diff_rows(universe: list[dict[str, Any]]) -> list[dict[str, object]]:
    """Fetch quote rows directly for the monitored universe codes."""
    tracked_secids = _build_eastmoney_secids(universe)
    diff_rows: list[dict[str, object]] = []
    seen_codes: set[str] = set()
    for secid_chunk in _chunk_values(tracked_secids, size=20):
        payload = _fetch_eastmoney_payload_for_secids(secid_chunk)
        chunk_rows = payload.get("data", {}).get("diff", [])
        if not isinstance(chunk_rows, list):
            raise ValueError("Eastmoney direct quote payload is missing data.diff rows.")
        for row in chunk_rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get("f12", "")).strip()
            if code and code in seen_codes:
                continue
            if code:
                seen_codes.add(code)
            diff_rows.append(row)
    return diff_rows


def _diff_rows_include_universe_codes(
    diff_rows: list[object],
    universe: list[dict[str, Any]],
) -> bool:
    """Return whether broad-market rows already include at least one tracked code."""
    tracked_codes = {str(stock.get("code", "")).strip() for stock in universe}
    if not tracked_codes:
        return False
    for row in diff_rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("f12", "")).strip() in tracked_codes:
            return True
    return False


def _normalize_local_snapshot_payload(payload: object) -> list[dict[str, Any]]:
    """Normalize one local quote snapshot JSON payload into raw quote rows."""
    if isinstance(payload, dict):
        if "rows" in payload and isinstance(payload.get("rows"), list):
            snapshot_rows = payload.get("rows", [])
            return [dict(row) for row in snapshot_rows if isinstance(row, dict)]
        data_block = payload.get("data", {})
        if isinstance(data_block, dict) and "diff" in data_block and isinstance(
            data_block.get("diff"), list
        ):
            diff_rows = data_block.get("diff", [])
            return [
                {
                    target_key: raw_row.get(source_key)
                    for source_key, target_key in EASTMONEY_FIELD_MAP.items()
                }
                for raw_row in diff_rows
                if isinstance(raw_row, dict)
            ]
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, dict)]
    raise ValueError("Local quote snapshot payload is not a supported JSON shape.")


def _fetch_eastmoney_payload_for_secids(secids: list[str]) -> dict[str, object]:
    """Fetch one compact Eastmoney payload for a small monitored secid batch."""
    powershell_result = _fetch_eastmoney_payload_with_powershell(secids)
    if powershell_result is not None:
        return powershell_result

    curl_executable = shutil.which("curl.exe") or shutil.which("curl")
    if curl_executable:
        return _fetch_eastmoney_payload_with_curl(curl_executable, secids)
    return _fetch_eastmoney_payload_with_urllib(secids)


def _fetch_eastmoney_market_payload_with_curl(curl_executable: str) -> dict[str, object]:
    """Fetch one broad Eastmoney market payload through curl, matching the proven local path."""
    last_error: Exception | None = None
    for endpoint in (
        EASTMONEY_MARKET_QUOTE_ENDPOINT,
        EASTMONEY_MARKET_QUOTE_ENDPOINT_FALLBACK,
    ):
        url = f"{endpoint}?{urlencode(EASTMONEY_MARKET_QUERY_PARAMS)}"
        try:
            result = subprocess.run(
                [
                    curl_executable,
                    "--silent",
                    "--show-error",
                    "--location",
                    "--header",
                    "User-Agent: Mozilla/5.0",
                    "--header",
                    "Referer: https://quote.eastmoney.com/",
                    url,
                ],
                env=_build_direct_request_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=15,
                check=True,
            )
            return json.loads(result.stdout)
        except Exception as exc:  # noqa: BLE001 - endpoint retry
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("Eastmoney market quote curl fetch failed.")


def _fetch_eastmoney_market_payload_with_powershell() -> dict[str, object]:
    """Fetch one broad Eastmoney market payload through PowerShell on Windows when available."""
    powershell_executable = shutil.which("powershell.exe")
    if not powershell_executable:
        raise FileNotFoundError("powershell.exe not found")

    last_error: Exception | None = None
    for endpoint in (
        EASTMONEY_MARKET_QUOTE_ENDPOINT,
        EASTMONEY_MARKET_QUOTE_ENDPOINT_FALLBACK,
    ):
        url = f"{endpoint}?{urlencode(EASTMONEY_MARKET_QUERY_PARAMS)}"
        command = (
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            f"(Invoke-WebRequest -UseBasicParsing '{url}').Content"
        )
        try:
            result = subprocess.run(
                [
                    powershell_executable,
                    "-NoProfile",
                    "-Command",
                    command,
                ],
                env=_build_direct_request_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=20,
                check=True,
            )
            return json.loads(result.stdout)
        except Exception as exc:  # noqa: BLE001 - endpoint retry
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("Eastmoney market quote PowerShell fetch failed.")


def _fetch_eastmoney_payload_with_powershell(
    secids: list[str],
) -> dict[str, object] | None:
    """Fetch one Eastmoney payload through PowerShell on Windows when available."""
    powershell_executable = shutil.which("powershell.exe")
    if not powershell_executable:
        return None

    params = dict(EASTMONEY_QUERY_PARAMS)
    params["secids"] = ",".join(secids)
    url = f"{EASTMONEY_QUOTE_ENDPOINT}?{urlencode(params)}"
    command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        f"(Invoke-WebRequest -UseBasicParsing '{url}').Content"
    )
    result = subprocess.run(
        [
            powershell_executable,
            "-NoProfile",
            "-Command",
            command,
        ],
        env=_build_direct_request_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=True,
    )
    return json.loads(result.stdout)


def _fetch_eastmoney_payload_with_curl(
    curl_executable: str,
    secids: list[str],
) -> dict[str, object]:
    """Fetch one Eastmoney payload through curl, matching the proven local path."""
    params = dict(EASTMONEY_QUERY_PARAMS)
    params["secids"] = ",".join(secids)
    url = f"{EASTMONEY_QUOTE_ENDPOINT}?{urlencode(params)}"
    result = subprocess.run(
        [
            curl_executable,
            "--silent",
            "--show-error",
            "--location",
            "--header",
            "User-Agent: Mozilla/5.0",
            "--header",
            "Referer: https://quote.eastmoney.com/",
            url,
        ],
        env=_build_direct_request_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
        check=True,
    )
    return json.loads(result.stdout)


def _fetch_eastmoney_payload_with_urllib(secids: list[str]) -> dict[str, object]:
    """Fetch one Eastmoney payload through urllib without inheriting proxy settings."""
    last_error: Exception | None = None
    params = dict(EASTMONEY_QUERY_PARAMS)
    params["secids"] = ",".join(secids)
    for attempt in range(3):
        request = Request(
            f"{EASTMONEY_QUOTE_ENDPOINT}?{urlencode(params)}",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://quote.eastmoney.com/",
            },
            method="GET",
        )
        try:
            opener = build_opener(
                ProxyHandler({}),
                HTTPSHandler(context=ssl.create_default_context()),
            )
            with opener.open(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except Exception as exc:  # noqa: BLE001 - retry transient endpoint disconnects
            last_error = exc
            if attempt == 2:
                raise
            time.sleep(0.5)
    else:
        raise RuntimeError("Eastmoney direct quote fetch failed.") from last_error
    return payload


def _build_eastmoney_secids(universe: list[dict[str, Any]]) -> list[str]:
    """Convert tracked A-share codes into Eastmoney secid tokens."""
    secids: list[str] = []
    for stock in universe:
        code = str(stock.get("code", "")).strip()
        if not code:
            continue
        market_prefix = "1" if code.startswith("6") else "0"
        secids.append(f"{market_prefix}.{code}")
    return secids


def _chunk_values(values: list[str], *, size: int) -> list[list[str]]:
    """Split one list into small stable chunks."""
    return [values[index : index + size] for index in range(0, len(values), size)]


def _build_direct_request_env() -> dict[str, str]:
    """Build a subprocess env that does not inherit common proxy variables."""
    env = dict(os.environ)
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
    ):
        env.pop(key, None)
    return env


def _run_quote_fetcher(fetcher: Callable[[], pd.DataFrame], *, source: str) -> pd.DataFrame:
    """Run one quote adapter and attach source metadata when it succeeds."""
    try:
        raw_result = fetcher()
    except ModuleNotFoundError as exc:
        if _is_missing_akshare_error(exc):
            return _empty_quotes_frame()
        return _empty_quotes_frame(error=exc)
    except Exception as exc:  # noqa: BLE001 - intentional graceful fallback
        return _empty_quotes_frame(error=exc)

    if isinstance(raw_result, pd.DataFrame):
        raw_rows = raw_result.to_dict(orient="records")
    else:
        raw_rows = list(raw_result)

    normalized = normalize_quote_fields(raw_rows)
    filtered = filter_to_universe(normalized, get_all_stocks())
    return _attach_quote_source(filtered, source)


def _attach_quote_source(quotes: pd.DataFrame, source: str) -> pd.DataFrame:
    """Attach one stable source label to a dataframe copy."""
    attached = quotes.copy()
    attached.attrs[QUOTE_SOURCE_ATTR] = source
    return attached


def _attach_fetch_path(quotes: pd.DataFrame, fetch_path: str) -> pd.DataFrame:
    """Attach one stable fetch-path label to a dataframe copy."""
    attached = quotes.copy()
    attached.attrs[FETCH_PATH_ATTR] = str(fetch_path or "").strip()
    return attached


def _empty_quotes_frame(*, error: Exception | None = None) -> pd.DataFrame:
    """Build an empty normalized quote frame with optional hidden error metadata."""
    empty = pd.DataFrame(columns=REQUIRED_QUOTE_COLUMNS)
    if error is not None:
        setattr(empty, "_fetch_error", error)
    return empty


def _is_missing_akshare_error(exc: Exception) -> bool:
    """Check whether one import error simply means AKShare is not installed."""
    return isinstance(exc, ModuleNotFoundError) and str(exc).find("akshare") != -1
