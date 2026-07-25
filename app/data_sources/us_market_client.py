"""Small Yahoo Finance chart client for the US market overview snapshot."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


INDEXES = {
    "nasdaq": ("^IXIC", "纳斯达克综合指数"),
    "sox": ("^SOX", "费城半导体指数"),
}
SECTORS = {
    "XLK": "科技",
    "SOXX": "半导体",
    "SMH": "半导体设备",
    "XLF": "金融",
    "XLE": "能源",
    "XLI": "工业",
    "XLY": "可选消费",
    "XLP": "必选消费",
    "XLV": "医疗",
    "XLU": "公用事业",
    "XLC": "通信服务",
    "XLB": "原材料",
}


def fetch_us_market_overview(timeout: int = 5) -> tuple[dict[str, Any] | None, str]:
    """Fetch one-day chart data and rank sector ETFs by daily change."""
    symbols = [symbol for symbol, _label in INDEXES.values()] + list(SECTORS)
    with ThreadPoolExecutor(max_workers=min(16, len(symbols))) as pool:
        results = dict(zip(symbols, pool.map(lambda item: _fetch_chart(item, timeout), symbols)))
    indexes = {key: results.get(symbol) for key, (symbol, _label) in INDEXES.items()}
    for key, (symbol, _label) in INDEXES.items():
        if not indexes[key]:
            return None, f"无法获取 {symbol} 行情"

    sectors: list[tuple[str, float]] = []
    for symbol, name in SECTORS.items():
        quote_data = results.get(symbol)
        if quote_data and isinstance(quote_data.get("change_value"), (int, float)):
            sectors.append((name, float(quote_data["change_value"])))
    sectors.sort(key=lambda item: item[1], reverse=True)
    sector_by_name = {name: value for name, value in sectors}
    strong = [_format_sector(name, value) for name, value in sectors[:3]]
    weak = [_format_sector(name, value) for name, value in sectors[-3:][::-1]]
    session_date = str(indexes["nasdaq"].get("session_date", "")).strip()
    return {
        "status": "ready",
        "date": session_date or datetime.now().strftime("%Y-%m-%d"),
        "source_name": "Yahoo Finance Chart API",
        "nasdaq": indexes["nasdaq"],
        "sox": indexes["sox"],
        "strong_sectors": strong or ["暂无"],
        "weak_sectors": weak or ["暂无"],
        "sector_analysis": _build_sector_analysis(sectors),
        "focus_sectors": {
            "半导体": [
                _format_sector("半导体设备", sector_by_name.get("半导体设备", 0.0)),
                _format_sector("半导体", sector_by_name.get("半导体", 0.0)),
            ],
            "AI": [
                _format_sector("科技", sector_by_name.get("科技", 0.0)),
                _format_sector("通信服务", sector_by_name.get("通信服务", 0.0)),
            ],
        },
    }, "获取成功"


def save_us_market_overview(payload: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _fetch_chart(symbol: str, timeout: int) -> dict[str, Any] | None:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote(symbol, safe='')}?range=1d&interval=5m"
    )
    request = Request(url, headers={"User-Agent": "Project-Agu-01/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return None
    meta = result[0].get("meta") or {}
    indicators = result[0].get("indicators") or {}
    quote_rows = (indicators.get("quote") or [{}])[0]
    closes = [value for value in quote_rows.get("close", []) if value is not None]
    opens = [value for value in quote_rows.get("open", []) if value is not None]
    highs = [value for value in quote_rows.get("high", []) if value is not None]
    lows = [value for value in quote_rows.get("low", []) if value is not None]
    if not closes or not opens:
        return None
    opening = float(opens[0])
    closing = float(closes[-1])
    previous = meta.get("chartPreviousClose")
    change = ((closing - float(previous)) / float(previous) * 100) if previous else 0.0
    market_time = meta.get("regularMarketTime")
    return {
        "open": _format_price(opening),
        "intraday": _format_price(max(highs) if highs else closing),
        "close": _format_price(closing),
        "change": f"{change:+.2f}%",
        "change_value": change,
        "session_date": (
            datetime.fromtimestamp(int(market_time)).strftime("%Y-%m-%d")
            if market_time
            else ""
        ),
        "trend": _trend_text(opening, closing, max(highs) if highs else closing),
    }


def _format_price(value: float) -> str:
    return f"{value:,.2f}"


def _trend_text(opening: float, closing: float, high: float) -> str:
    if closing > opening * 1.003:
        return "开盘后整体走强，收盘高于开盘"
    if closing < opening * 0.997:
        return "开盘后整体走弱，收盘低于开盘"
    if high > opening * 1.005:
        return "盘中有冲高，收盘回到开盘附近"
    return "盘中震荡，收盘与开盘接近"


def _format_sector(name: str, value: float) -> str:
    return f"{name}（{value:+.2f}%）"


def _build_sector_analysis(sectors: list[tuple[str, float]]) -> str:
    if not sectors:
        return "暂无足够行业ETF数据"
    strong = sectors[0][0]
    weak = sectors[-1][0]
    return f"{strong}相对强势，{weak}相对偏弱；行业强弱按主要ETF当日涨跌幅排序。"
