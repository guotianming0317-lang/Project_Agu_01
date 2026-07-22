"""Historical review helpers built on persisted snapshots and alerts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.database import fetch_alerts, fetch_market_snapshots
from app.reports.context_rules import (
    build_next_session_action_summary,
    rank_sectors_by_pct_chg,
    render_next_session_action_summary_lines,
)
from app.reports.shared import build_stock_pool_observation_lines
from app.reports.shared import build_stock_pool_drift_summary_text
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
)


def list_snapshot_batches(database_path: Path) -> list[str]:
    """List unique snapshot timestamps in descending order."""
    snapshots = fetch_market_snapshots(database_path)
    timestamps = sorted({str(row["timestamp"]) for row in snapshots}, reverse=True)
    return timestamps


def build_history_summary(database_path: Path, timestamp: str) -> str:
    """Build a human-readable summary for one stored timestamp batch."""
    snapshots = [
        row
        for row in fetch_market_snapshots(database_path)
        if str(row["timestamp"]) == timestamp
    ]
    alerts = [
        row for row in fetch_alerts(database_path) if str(row["timestamp"]) == timestamp
    ]

    if not snapshots:
        return (
            "\u65f6\u95f4\u6279\u6b21\uff1a"
            + str(timestamp)
            + "\n\u672a\u627e\u5230\u5bf9\u5e94\u5feb\u7167\u6570\u636e\u3002"
            + "\n\u53ef\u5148\u8fd0\u884c `python -m app.main` \u751f\u6210\u7b2c\u4e00\u6279\u672c\u5730\u76d1\u63a7\u6570\u636e\u3002"
        )

    frame = pd.DataFrame(snapshots)
    strongest_sector = _build_strongest_sector_text(frame)
    ranked_sectors = rank_sectors_by_pct_chg(frame)
    strongest_live_sector = ranked_sectors[0] if len(ranked_sectors) >= 1 else strongest_sector
    secondary_sector = (
        ranked_sectors[1] if len(ranked_sectors) >= 2 else strongest_live_sector
    )
    fading_sector = ranked_sectors[-1] if ranked_sectors else strongest_live_sector
    next_session_action_summary = build_next_session_action_summary(
        frame,
        alerts,
        strongest_sector=strongest_live_sector,
        secondary_sector=secondary_sector,
        fading_sector=fading_sector,
    )
    next_session_action_lines = render_next_session_action_summary_lines(
        next_session_action_summary
    )

    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)
    stock_pool_lines = build_stock_pool_observation_lines(
        structure_summary=str(stock_pool_summary.get("structure_summary", "")).strip(),
        comparison_tag_groups=list(
            stock_pool_comparison.get("comparison_tag_groups", [])
        ),
        highlight_summary=str(
            stock_pool_comparison.get("highlight_summary", "")
        ).strip(),
        change_rows=list(stock_pool_comparison.get("change_rows", [])),
        health_hints=list(stock_pool_summary.get("health_hints", [])),
    )
    stock_pool_drift_summary = build_stock_pool_drift_summary_text(
        structure_summary=str(stock_pool_summary.get("structure_summary", "")).strip(),
        comparison_tag_groups=list(
            stock_pool_comparison.get("comparison_tag_groups", [])
        ),
        highlight_summary=str(
            stock_pool_comparison.get("highlight_summary", "")
        ).strip(),
    )

    return "\n".join(
        [
            "\u65f6\u95f4\u6279\u6b21\uff1a" + str(timestamp),
            stock_pool_drift_summary,
            "\u5feb\u7167\u6570\u91cf\uff1a" + str(len(snapshots)),
            "\u9884\u8b66\u6570\u91cf\uff1a" + str(len(alerts)),
            "\u6700\u5f3a\u677f\u5757\uff1a" + str(strongest_sector),
            "",
            "\u76d1\u63a7\u6c60\u7ed3\u6784\u89c2\u5bdf",
            *stock_pool_lines,
            "",
            "\u6b21\u65e5\u7b56\u7565\u6458\u8981",
            *next_session_action_lines,
        ]
    )


def _build_strongest_sector_text(frame: pd.DataFrame) -> str:
    """Build the strongest-sector text from one historical snapshot frame."""
    if frame.empty or "sector" not in frame or "pct_chg" not in frame:
        return "unclassified"
    ranked_sectors = sorted(
        (
            (str(sector), float(group["pct_chg"].mean()))
            for sector, group in frame.groupby("sector", dropna=False)
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked_sectors[0][0] if ranked_sectors else "unclassified"
