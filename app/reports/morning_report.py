"""Morning report builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.data_sources.akshare_client import build_quote_source_display_text
from app.database import fetch_latest_alerts, fetch_latest_market_snapshots
from app.reports.context_rules import (
    build_industry_chain_mapping,
    build_position_bias_hint,
    classify_strength_label,
    collect_risk_alert_messages,
    get_top_sector_average_pct_chg,
    pick_top_stock_names,
    rank_sectors_by_pct_chg,
)
from app.reports.shared import (
    ReportSection,
    build_stock_pool_observation_lines,
    build_text_report,
    join_report_items,
)
from app.sectors import DEFAULT_FOCUS_SECTORS_TEXT
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
)


def build_morning_report(context: dict[str, Any] | None = None) -> str:
    """Build a morning report from structured inputs."""
    context = context or {}
    overseas_strength = context.get("overseas_strength", "待接入")
    a_share_mapping = context.get("a_share_mapping", "待判断")
    focus_sectors = join_report_items(
        context.get("focus_sectors"),
        default=DEFAULT_FOCUS_SECTORS_TEXT,
    )
    focus_stocks = join_report_items(
        context.get("focus_stocks"),
        default="中巨芯-U、华特气体、沪硅产业",
    )
    main_risks = context.get("main_risks", "待接入")
    position_bias = context.get("position_bias", "观察")
    stock_pool_lines = build_stock_pool_observation_lines(
        structure_summary=str(context.get("stock_pool_structure_summary", "")).strip(),
        comparison_tag_groups=list(context.get("stock_pool_comparison_tag_groups", [])),
        highlight_summary=str(
            context.get("stock_pool_comparison_highlight_summary", "")
        ).strip(),
        change_rows=list(context.get("stock_pool_comparison_change_rows", [])),
        health_hints=list(context.get("stock_pool_health_hints", [])),
    )
    quote_source_display = str(context.get("quote_source_display", "")).strip()
    intro_lines = [f"行情来源：{quote_source_display}"] if quote_source_display else None

    return build_text_report(
        "【今日主线判断】",
        [
            ReportSection(
                heading=None,
                lines=(
                    f"1. 海外AI半导体强弱：{overseas_strength}",
                    f"2. A股可能映射方向：{a_share_mapping}",
                    f"3. 今日重点观察板块：{focus_sectors}",
                    f"4. 今日重点观察个股：{focus_stocks}",
                    f"5. 主要风险：{main_risks}",
                    f"6. 仓位倾向：{position_bias}",
                ),
            ),
            ReportSection(
                heading="7. 监控池结构观察",
                lines=stock_pool_lines,
            ),
        ],
        intro_lines=intro_lines,
    )


def build_morning_report_from_database(database_path: Path) -> str:
    """Build a morning report from the latest persisted snapshots and alerts."""
    snapshots = fetch_latest_market_snapshots(database_path)
    alerts = fetch_latest_alerts(database_path)
    if not snapshots:
        return build_morning_report()

    frame = pd.DataFrame(snapshots)
    focus_sectors = rank_sectors_by_pct_chg(frame, limit=3)
    focus_stocks = pick_top_stock_names(frame, limit=3)
    strongest_sector = focus_sectors[0] if focus_sectors else DEFAULT_FOCUS_SECTORS_TEXT
    strongest_avg = get_top_sector_average_pct_chg(frame)
    risk_messages = collect_risk_alert_messages(alerts, limit=3)
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)

    context = {
        "quote_source_display": build_quote_source_display_text(
            str(snapshots[0].get("quote_source", "")).strip()
        ),
        "overseas_strength": classify_strength_label(strongest_avg),
        "a_share_mapping": build_industry_chain_mapping(strongest_sector),
        "focus_sectors": focus_sectors or DEFAULT_FOCUS_SECTORS_TEXT,
        "focus_stocks": focus_stocks,
        "main_risks": join_report_items(
            risk_messages,
            default="出口限制与海外波动仍需继续跟踪",
        ),
        "position_bias": build_position_bias_hint(strongest_avg, len(risk_messages)),
        "stock_pool_structure_summary": str(
            stock_pool_summary.get("structure_summary", "")
        ).strip(),
        "stock_pool_comparison_tag_groups": list(
            stock_pool_comparison.get("comparison_tag_groups", [])
        ),
        "stock_pool_comparison_highlight_summary": str(
            stock_pool_comparison.get("highlight_summary", "")
        ).strip(),
        "stock_pool_comparison_change_rows": list(
            stock_pool_comparison.get("change_rows", [])
        ),
        "stock_pool_health_hints": list(stock_pool_summary.get("health_hints", [])),
    }
    return build_morning_report(context)
