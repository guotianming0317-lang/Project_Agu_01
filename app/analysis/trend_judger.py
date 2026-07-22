"""Short-term trend judgement rules."""

from __future__ import annotations

from statistics import mean
from typing import Any


def judge_trend(
    recent_history: list[dict[str, Any]],
    realtime_quote: dict[str, Any],
    sector_pct_chg: float,
) -> dict[str, Any]:
    """Judge the short-term trend state for one stock.

    Phase-one rules are intentionally simple and explainable. They use:

    - moving averages from recent closes
    - current turnover versus 5-day average turnover
    - stock performance versus sector performance
    - intraday high versus close change
    """
    code = str(realtime_quote.get("code", ""))
    name = str(realtime_quote.get("name", ""))

    if len(recent_history) < 20:
        return {
            "code": code,
            "name": name,
            "trend_state": "数据不足",
            "trend_score": 0.0,
            "reason": "Need at least 20 sessions of history to compute MA20.",
            "sector_pct_chg": sector_pct_chg,
            "history_size": len(recent_history),
        }

    closes = [_to_float(row.get("close")) for row in recent_history]
    turnovers = [_to_float(row.get("turnover")) for row in recent_history]

    ma5 = mean(closes[-5:])
    ma10 = mean(closes[-10:])
    ma20 = mean(closes[-20:])
    avg_turnover_5d = mean(turnovers[-5:])

    price = _to_float(realtime_quote.get("price"))
    pct_chg = _to_float(realtime_quote.get("pct_chg"))
    turnover = _to_float(realtime_quote.get("turnover"))
    intraday_high_pct = _to_float(realtime_quote.get("intraday_high_pct"))
    close_pct_chg = _to_float(realtime_quote.get("close_pct_chg", pct_chg))
    turnover_ratio_vs_5d = turnover / avg_turnover_5d if avg_turnover_5d else 0.0

    if (
        intraday_high_pct > 5.0
        and close_pct_chg < intraday_high_pct * 0.5
        and turnover_ratio_vs_5d > 1.5
    ):
        return _build_result(
            code=code,
            name=name,
            trend_state="冲高回落",
            trend_score=0.38,
            reason=(
                "intraday_high_pct exceeded 5%, close_pct_chg faded below half of "
                "the intraday peak, and turnover expanded versus 5-day average."
            ),
            sector_pct_chg=sector_pct_chg,
            history_size=len(recent_history),
        )

    if (
        price > ma5 > ma10 > ma20
        and pct_chg > sector_pct_chg
        and turnover_ratio_vs_5d > 1.3
    ):
        return _build_result(
            code=code,
            name=name,
            trend_state="强趋势",
            trend_score=0.86,
            reason=(
                f"MA alignment is bullish (price > MA5 > MA10 > MA20), pct_chg "
                f"beats sector, and turnover is {turnover_ratio_vs_5d:.2f}x 5-day average."
            ),
            sector_pct_chg=sector_pct_chg,
            history_size=len(recent_history),
        )

    if (
        (price < ma10 or price < ma20)
        and turnover_ratio_vs_5d > 1.3
        and pct_chg < sector_pct_chg
    ):
        return _build_result(
            code=code,
            name=name,
            trend_state="退潮",
            trend_score=0.22,
            reason=(
                f"price fell below ma10/ma20, turnover expanded to {turnover_ratio_vs_5d:.2f}x "
                "5-day average, and performance lagged the sector."
            ),
            sector_pct_chg=sector_pct_chg,
            history_size=len(recent_history),
        )

    if price > ma10 and turnover_ratio_vs_5d >= 1.0:
        return _build_result(
            code=code,
            name=name,
            trend_state="弱趋势",
            trend_score=0.58,
            reason="price stays above MA10, but confirmation is weaker than a strong trend.",
            sector_pct_chg=sector_pct_chg,
            history_size=len(recent_history),
        )

    return _build_result(
        code=code,
        name=name,
        trend_state="震荡",
        trend_score=0.5,
        reason="price is moving around medium-term averages without a decisive breakout.",
        sector_pct_chg=sector_pct_chg,
        history_size=len(recent_history),
    )


def _build_result(
    *,
    code: str,
    name: str,
    trend_state: str,
    trend_score: float,
    reason: str,
    sector_pct_chg: float,
    history_size: int,
) -> dict[str, Any]:
    """Build the normalized trend response payload."""
    return {
        "code": code,
        "name": name,
        "trend_state": trend_state,
        "trend_score": trend_score,
        "reason": reason,
        "sector_pct_chg": sector_pct_chg,
        "history_size": history_size,
    }


def _to_float(value: Any) -> float:
    """Convert raw numeric-like values into floats."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
