"""Alert rule evaluation for market and news signals."""

from __future__ import annotations

from typing import Any


def evaluate_alerts(market_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Evaluate market rows and return triggered alerts.

    Phase one returns an empty list until the concrete rules are implemented.
    """
    _ = market_rows
    return []
