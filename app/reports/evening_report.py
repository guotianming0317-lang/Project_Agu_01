"""Evening report builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.analysis.leader_detector import detect_sector_leaders
from app.data_sources.akshare_client import build_quote_source_display_text
from app.database import fetch_latest_alerts, fetch_latest_market_snapshots
from app.reports.context_rules import (
    build_next_session_action_summary,
    build_tomorrow_plan,
    collect_positive_alert_messages,
    collect_risk_alert_messages,
    rank_sectors_by_pct_chg,
    render_compact_next_session_action_lines,
    render_next_session_action_summary_lines,
)
from app.reports.shared import (
    ReportSection,
    build_stock_pool_observation_lines,
    build_text_report,
    join_report_items,
)
from app.sectors import MATERIAL_RELATED_SECTORS
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
)


def build_evening_report(context: dict[str, Any] | None = None) -> str:
    """Build an evening report from structured inputs."""
    context = context or {}
    leaders = context.get("leaders", {})
    materials_watch = join_report_items(context.get("materials_watch"), default="待补充")
    positive_news = join_report_items(context.get("positive_news"), default="待补充")
    negative_news = join_report_items(context.get("negative_news"), default="待补充")
    stock_pool_lines = build_stock_pool_observation_lines(
        structure_summary=str(context.get("stock_pool_structure_summary", "")).strip(),
        comparison_tag_groups=list(context.get("stock_pool_comparison_tag_groups", [])),
        highlight_summary=str(
            context.get("stock_pool_comparison_highlight_summary", "")
        ).strip(),
        change_rows=list(context.get("stock_pool_comparison_change_rows", [])),
        health_hints=list(context.get("stock_pool_health_hints", [])),
    )
    next_session_action_summary = context.get("next_session_action_summary")
    if isinstance(next_session_action_summary, dict):
        next_session_action_lines = render_compact_next_session_action_lines(
            next_session_action_summary
        )
    else:
        next_session_action_lines = tuple(
            str(line).strip()
            for line in list(context.get("next_session_action_lines", []))
            if str(line).strip()
        )

    quote_source_display = str(context.get("quote_source_display", "")).strip()
    intro_lines = [f"日期：{context.get('date', '待补充')}"]
    if quote_source_display:
        intro_lines.append(f"行情来源：{quote_source_display}")

    return build_text_report(
        "【AI + 半导体收盘复盘】",
        [
            ReportSection(
                heading="一、今日主线",
                lines=(
                    f"最强方向：{context.get('strongest_sector', '待补充')}",
                    f"次强方向：{context.get('secondary_sector', '待补充')}",
                    f"退潮方向：{context.get('fading_sector', '待补充')}",
                ),
            ),
            ReportSection(
                heading="二、龙头判断",
                lines=(
                    f"涨幅龙头：{leaders.get('涨幅龙头', '待补充')}",
                    f"成交额龙头：{leaders.get('成交额龙头', '待补充')}",
                    f"趋势龙头：{leaders.get('趋势龙头', '待补充')}",
                    f"情绪龙头：{leaders.get('情绪龙头', '待补充')}",
                ),
            ),
            ReportSection(
                heading="三、材料/气体线专项",
                lines=(f"重点跟踪：{materials_watch}",),
            ),
            ReportSection(
                heading="四、监控池结构观察",
                lines=stock_pool_lines,
            ),
            ReportSection(
                heading="五、消息面",
                lines=(
                    f"利好消息：{positive_news}",
                    f"利空消息：{negative_news}",
                ),
            ),
            ReportSection(
                heading="六、明日策略",
                lines=(
                    f"观察重点：{context.get('tomorrow_plan', '待补充')}",
                    *next_session_action_lines,
                ),
            ),
        ],
        intro_lines=intro_lines,
    )


def build_evening_report_from_database(database_path: Path) -> str:
    """Build an evening report from the latest persisted snapshots and alerts."""
    snapshots = fetch_latest_market_snapshots(database_path)
    alerts = fetch_latest_alerts(database_path)
    if not snapshots:
        return build_evening_report()

    frame = pd.DataFrame(snapshots)
    leaders = detect_sector_leaders(frame)
    ranked_sectors = rank_sectors_by_pct_chg(frame)
    strongest_sector = ranked_sectors[0] if len(ranked_sectors) >= 1 else "待补充"
    secondary_sector = ranked_sectors[1] if len(ranked_sectors) >= 2 else strongest_sector
    fading_sector = ranked_sectors[-1] if ranked_sectors else "待补充"

    leader_map = {
        leader_type: group.iloc[0]["name"]
        for leader_type, group in leaders.groupby("leader_type", sort=False)
    }
    positive_news = collect_positive_alert_messages(alerts, limit=3)
    negative_news = collect_risk_alert_messages(alerts, limit=3)
    materials_watch = (
        frame[frame["sector"].isin(MATERIAL_RELATED_SECTORS)]["name"].head(3).tolist()
        or ["待补充"]
    )
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)

    context = {
        "date": str(snapshots[0]["timestamp"]).split(" ")[0],
        "quote_source_display": build_quote_source_display_text(
            str(snapshots[0].get("quote_source", "")).strip()
        ),
        "strongest_sector": strongest_sector,
        "secondary_sector": secondary_sector,
        "fading_sector": fading_sector,
        "leaders": leader_map,
        "materials_watch": materials_watch,
        "positive_news": positive_news or ["待补充"],
        "negative_news": negative_news or ["待补充"],
        "tomorrow_plan": build_tomorrow_plan(
            strongest_sector,
            secondary_sector,
            risk_count=len(negative_news),
        ),
        "next_session_action_summary": build_next_session_action_summary(
            frame,
            alerts,
            strongest_sector=strongest_sector,
            secondary_sector=secondary_sector,
            fading_sector=fading_sector,
        ),
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
    return build_evening_report(context)
