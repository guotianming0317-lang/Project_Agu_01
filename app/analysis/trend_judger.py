"""Short-term trend judgement rules."""

from __future__ import annotations

from typing import Any


def judge_trend(
    recent_history: list[dict[str, Any]],
    realtime_quote: dict[str, Any],
    sector_pct_chg: float,
) -> dict[str, Any]:
    """Return a placeholder trend judgement for one stock."""
    return {
        "code": realtime_quote.get("code", ""),
        "name": realtime_quote.get("name", ""),
        "trend_state": "未判断",
        "trend_score": 0.0,
        "reason": "phase one placeholder",
        "sector_pct_chg": sector_pct_chg,
        "history_size": len(recent_history),
    }
