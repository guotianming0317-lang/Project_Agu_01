"""Database-backed overview helpers for the local dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.analysis.leader_detector import detect_sector_leaders
from app.data_sources.akshare_client import build_quote_source_display_text
from app.database import (
    fetch_alerts,
    fetch_latest_alerts,
    fetch_latest_market_snapshots,
    fetch_market_snapshots,
)
from app.history import list_snapshot_batches
from app.reports.context_rules import (
    build_next_session_action_summary,
    rank_sectors_by_pct_chg,
)
from app.reports.shared import build_stock_pool_drift_summary_text
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
    get_all_stocks,
)


NEGATIVE_ALERT_KEYWORDS = (
    "risk",
    "disturb",
    "warning",
    "selloff",
    "drop",
    "weak",
    "export control",
    "风险",
    "扰动",
    "利空",
    "下跌",
    "走弱",
    "出口管制",
)


def build_dashboard_payload(
    database_path: Path,
    *,
    selected_timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a lightweight payload for the latest dashboard view."""
    batches = list_snapshot_batches(database_path)
    if selected_timestamp:
        snapshots = [
            row
            for row in fetch_market_snapshots(database_path)
            if str(row.get("timestamp", "")) == selected_timestamp
        ]
        alerts = [
            row
            for row in fetch_alerts(database_path)
            if str(row.get("timestamp", "")) == selected_timestamp
        ]
    else:
        snapshots = fetch_latest_market_snapshots(database_path)
        alerts = fetch_latest_alerts(database_path)

    if not snapshots:
        stock_pool_health = _build_stock_pool_health_summary()
        return {
            "latest_timestamp": None,
            "quote_source": "",
            "quote_source_display": "",
            "quote_status_summary": "Quote status: unavailable.",
            "snapshot_count": 0,
            "alert_count": 0,
            "positive_alert_count": 0,
            "negative_alert_count": 0,
            "mainline_summary": "No main-line summary",
            "risk_summary": "No risk summary",
            "strongest_sector": "No data yet",
            "strongest_sector_summary": {
                "sector": "No data yet",
                "avg_pct_chg": 0.0,
                "stock_count": 0,
            },
            "top_movers": [],
            "latest_alerts": [],
            "available_batches": batches,
            "sector_cards": [],
            "sector_chart": [],
            "top_mover_chart": [],
            "leader_summary": {},
            "next_session_action_summary": {},
            "today_priority_summary": {},
            "stock_pool_drift_summary": str(
                stock_pool_health.get("drift_summary", "")
            ).strip(),
            "stock_pool_health": stock_pool_health,
        }

    strongest_sector = _find_strongest_sector(snapshots)
    sector_cards = _build_sector_cards(snapshots)
    sector_chart = _build_sector_chart(sector_cards)
    leader_summary = _build_leader_summary(snapshots)
    next_session_action_summary = _build_next_session_action_dashboard_summary(
        snapshots,
        alerts,
    )
    alert_balance = _build_alert_balance(alerts)
    top_movers = sorted(
        snapshots,
        key=lambda row: float(row.get("pct_chg", 0.0) or 0.0),
        reverse=True,
    )[:5]
    top_mover_chart = _build_top_mover_chart(top_movers)
    stock_pool_health = _build_stock_pool_health_summary()
    today_priority_summary = _build_today_priority_summary()
    mainline_summary = _build_mainline_summary(
        snapshots,
        positive_alert_count=alert_balance["positive_alert_count"],
        negative_alert_count=alert_balance["negative_alert_count"],
    )
    risk_summary = _build_risk_summary(
        negative_alert_count=alert_balance["negative_alert_count"],
        positive_alert_count=alert_balance["positive_alert_count"],
        alert_count=len(alerts),
    )

    quote_source = str(snapshots[0].get("quote_source", "")).strip()

    return {
        "latest_timestamp": str(snapshots[0]["timestamp"]),
        "quote_source": quote_source,
        "quote_source_display": build_quote_source_display_text(quote_source),
        "quote_status_summary": _build_quote_status_summary(quote_source),
        "snapshot_count": len(snapshots),
        "alert_count": len(alerts),
        "positive_alert_count": alert_balance["positive_alert_count"],
        "negative_alert_count": alert_balance["negative_alert_count"],
        "mainline_summary": mainline_summary,
        "risk_summary": risk_summary,
        "strongest_sector": strongest_sector,
        "strongest_sector_summary": _build_strongest_sector_summary(
            strongest_sector,
            sector_cards,
        ),
        "top_movers": top_movers,
        "latest_alerts": alerts[:5],
        "available_batches": batches,
        "sector_cards": sector_cards,
        "sector_chart": sector_chart,
        "top_mover_chart": top_mover_chart,
        "leader_summary": leader_summary,
        "next_session_action_summary": next_session_action_summary,
        "today_priority_summary": today_priority_summary,
        "stock_pool_drift_summary": str(
            stock_pool_health.get("drift_summary", "")
        ).strip(),
        "stock_pool_health": stock_pool_health,
    }


def _find_strongest_sector(snapshots: list[dict[str, Any]]) -> str:
    """Find the strongest sector by average percentage change."""
    sector_values: dict[str, list[float]] = {}
    for row in snapshots:
        sector = str(row.get("sector", "Unknown"))
        sector_values.setdefault(sector, []).append(float(row.get("pct_chg", 0.0) or 0.0))

    ranked = sorted(
        (
            (sector, sum(values) / len(values))
            for sector, values in sector_values.items()
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0][0] if ranked else "Unknown"


def _build_sector_cards(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build compact sector summary cards for the latest batch."""
    sector_values: dict[str, list[float]] = {}
    sector_counts: dict[str, int] = {}
    for row in snapshots:
        sector = str(row.get("sector", "Unknown"))
        sector_values.setdefault(sector, []).append(float(row.get("pct_chg", 0.0) or 0.0))
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    ranked = sorted(
        [
            {
                "sector": sector,
                "avg_pct_chg": round(sum(values) / len(values), 2),
                "stock_count": sector_counts[sector],
            }
            for sector, values in sector_values.items()
        ],
        key=lambda item: item["avg_pct_chg"],
        reverse=True,
    )
    return ranked


def _build_leader_summary(snapshots: list[dict[str, Any]]) -> dict[str, str]:
    """Build a compact leader summary keyed by leader type."""
    frame = pd.DataFrame(snapshots)
    leader_frame = detect_sector_leaders(frame)
    if leader_frame.empty:
        return {}
    return {
        str(row["leader_type"]): str(row["name"])
        for _, row in leader_frame.iterrows()
    }


def _build_sector_chart(sector_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a simple chart-ready sector strength series."""
    return [
        {"sector": str(card["sector"]), "avg_pct_chg": float(card["avg_pct_chg"])}
        for card in sector_cards
    ]


def _build_strongest_sector_summary(
    strongest_sector: str,
    sector_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a compact strongest-sector summary block."""
    for card in sector_cards:
        if str(card.get("sector", "")) == strongest_sector:
            return {
                "sector": strongest_sector,
                "avg_pct_chg": float(card.get("avg_pct_chg", 0.0) or 0.0),
                "stock_count": int(card.get("stock_count", 0) or 0),
            }
    return {
        "sector": strongest_sector,
        "avg_pct_chg": 0.0,
        "stock_count": 0,
    }


def _build_top_mover_chart(top_movers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a simple chart-ready top mover series."""
    return [
        {
            "name": str(row.get("name", "")),
            "pct_chg": float(row.get("pct_chg", 0.0) or 0.0),
        }
        for row in top_movers
    ]


def _build_mainline_summary(
    snapshots: list[dict[str, Any]],
    *,
    positive_alert_count: int,
    negative_alert_count: int,
) -> str:
    """Build one concise main-line conclusion for the dashboard KPI area."""
    if not snapshots:
        return "No main-line summary"

    frame = pd.DataFrame(snapshots)
    ranked_sectors = rank_sectors_by_pct_chg(frame)
    strongest_sector = ranked_sectors[0] if ranked_sectors else "No data yet"
    secondary_sector = (
        ranked_sectors[1] if len(ranked_sectors) >= 2 else strongest_sector
    )

    if negative_alert_count > positive_alert_count:
        return (
            f"Main line is not clean; {strongest_sector} still leads, but risk is rising."
        )
    if secondary_sector and secondary_sector != strongest_sector:
        return (
            f"Main line: {strongest_sector}; {secondary_sector} is the first follow-through lane."
        )
    return f"Main line: {strongest_sector} remains the clearest strength."


def _build_risk_summary(
    *,
    negative_alert_count: int,
    positive_alert_count: int,
    alert_count: int,
) -> str:
    """Build one concise risk-state conclusion for the dashboard KPI area."""
    if alert_count <= 0:
        return "Risk state: no active warning signal yet."
    if negative_alert_count >= 2:
        return f"Risk state: elevated; {negative_alert_count} warning signal(s) need review."
    if negative_alert_count > positive_alert_count:
        return "Risk state: caution; warning signals outweigh supportive ones."
    if negative_alert_count > 0:
        return "Risk state: watch closely; risk is present but not dominant."
    return "Risk state: stable; no dominant warning signal is active."


def _build_quote_status_summary(quote_source: str) -> str:
    """Build one compact homepage-friendly quote-source status summary."""
    normalized_source = str(quote_source).strip()
    if normalized_source == "eastmoney-direct":
        return "Quote status: live direct quotes active."
    if normalized_source == "akshare":
        return "Quote status: live adapter quotes active."
    if normalized_source == "local-json-snapshot":
        return "Quote status: using local real quote snapshot."
    if normalized_source == "demo-fallback":
        return "Quote status: demo fallback active."
    return "Quote status: source status unknown."


def _build_next_session_action_dashboard_summary(
    snapshots: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a dashboard-ready next-session action summary from one snapshot batch."""
    frame = pd.DataFrame(snapshots)
    ranked_sectors = rank_sectors_by_pct_chg(frame)
    strongest_sector = ranked_sectors[0] if len(ranked_sectors) >= 1 else "n/a"
    secondary_sector = ranked_sectors[1] if len(ranked_sectors) >= 2 else strongest_sector
    fading_sector = ranked_sectors[-1] if ranked_sectors else strongest_sector
    summary = build_next_session_action_summary(
        frame,
        alerts,
        strongest_sector=strongest_sector,
        secondary_sector=secondary_sector,
        fading_sector=fading_sector,
    )
    core = dict(summary.get("core", {}))
    candidate = dict(summary.get("candidate", {}))
    avoid = dict(summary.get("avoid", {}))
    return {
        "rule_summary_lines": tuple(summary.get("rule_summary_lines", ())),
        "core": core,
        "candidate": candidate,
        "avoid": avoid,
        "core_count": len(list(core.get("watchlist", []))),
        "candidate_count": len(list(candidate.get("watchlist", []))),
        "avoid_count": len(list(avoid.get("watchlist", []))),
    }


def _build_alert_balance(alerts: list[dict[str, Any]]) -> dict[str, int]:
    """Count positive and negative alerts with explicit keyword rules."""
    negative_alert_count = 0
    for row in alerts:
        message = str(row.get("message", "")).casefold()
        if any(keyword in message for keyword in NEGATIVE_ALERT_KEYWORDS):
            negative_alert_count += 1

    return {
        "positive_alert_count": max(len(alerts) - negative_alert_count, 0),
        "negative_alert_count": negative_alert_count,
    }


def _build_stock_pool_health_summary() -> dict[str, Any]:
    """Build a compact stock-pool validation summary for dashboard reuse."""
    summary = dict(build_stock_pool_health_summary())
    summary["extension_summary"] = _build_extension_pool_summary()
    comparison = build_stock_pool_health_comparison(summary)
    drift_summary = build_stock_pool_drift_summary_text(
        structure_summary=str(summary.get("structure_summary", "")).strip(),
        comparison_tag_groups=list(comparison.get("comparison_tag_groups", [])),
        highlight_summary=str(comparison.get("highlight_summary", "")).strip(),
    )
    summary.update(
        {
            "comparison_snapshot_path": str(comparison.get("snapshot_path", "")),
            "comparison_baseline_exists": bool(
                comparison.get("baseline_exists", False)
            ),
            "comparison_baseline_saved_at": str(
                comparison.get("baseline_saved_at", "")
            ).strip(),
            "comparison_tags": list(comparison.get("comparison_tags", [])),
            "comparison_tag_labels": list(comparison.get("comparison_tag_labels", [])),
            "comparison_tag_groups": list(comparison.get("comparison_tag_groups", [])),
            "comparison_summary": str(
                comparison.get("comparison_summary", "")
            ).strip(),
            "comparison_highlight_summary": str(
                comparison.get("highlight_summary", "")
            ).strip(),
            "comparison_change_rows": list(comparison.get("change_rows", [])),
            "drift_summary": drift_summary,
        }
    )
    return summary


def _build_extension_pool_summary() -> str:
    """Summarize the AI upstream/downstream extension layer for the dashboard."""
    extended = [
        row for row in get_all_stocks()
        if str(row.get("pool_type", "")).strip() == "extended"
    ]
    if not extended:
        return "扩展观察池：暂无标的"
    sector_counts: dict[str, int] = {}
    for row in extended:
        sector = str(row.get("monitor_sector") or row.get("sector") or "待分类").strip()
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    distribution = "、".join(
        f"{sector}{count}只" for sector, count in sorted(sector_counts.items())
    )
    return f"扩展观察池：{len(extended)}只；产业链分布：{distribution}"


def _build_today_priority_summary() -> dict[str, Any]:
    """Load the latest saved daily news priority summary for dashboard reuse."""
    summary_path = _find_latest_priority_summary_path()
    if summary_path is None:
        return {}
    return _parse_priority_summary_markdown(summary_path)


def _find_latest_priority_summary_path() -> Path | None:
    """Find the newest archived priority-summary markdown file in the local news folder."""
    news_dir = Path("data/news")
    if not news_dir.exists():
        return None
    candidates = sorted(
        news_dir.glob("news_batch_priority_summary_*.md"),
        key=lambda path: path.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _parse_priority_summary_markdown(path: Path) -> dict[str, Any]:
    """Parse one saved priority-summary markdown into a stable dashboard payload."""
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    watch_groups: list[dict[str, Any]] = []
    action_groups: list[dict[str, Any]] = []

    current_section = ""
    current_group_title = ""
    current_group_items: list[str] = []
    current_group_target = ""

    def flush_group() -> None:
        nonlocal current_group_title, current_group_items, current_group_target
        if not current_group_target or not current_group_title:
            current_group_title = ""
            current_group_items = []
            current_group_target = ""
            return
        target = watch_groups if current_group_target == "watch" else action_groups
        target.append(
            {
                "title": current_group_title,
                "items": list(current_group_items),
            }
        )
        current_group_title = ""
        current_group_items = []
        current_group_target = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if line.startswith("- ") and current_section == "":
            key, _, value = line[2:].partition("：")
            if key and value:
                metadata[key.strip()] = value.strip().strip("`")
            continue
        if line.startswith("## "):
            flush_group()
            current_section = line[3:].strip()
            sections.setdefault(current_section, [])
            continue
        if line.startswith("### "):
            flush_group()
            current_group_title = line[4:].strip()
            if current_section == "重点观察名单":
                current_group_target = "watch"
            elif current_section == "建议动作":
                current_group_target = "action"
            else:
                current_group_target = ""
            continue
        if line.startswith("- "):
            content = line[2:].strip()
            if current_group_target:
                current_group_items.append(content)
            else:
                sections.setdefault(current_section, []).append(content)
            continue
        sections.setdefault(current_section, []).append(line)
    flush_group()

    read_order = list(sections.get("阅读顺序", []))
    watch_rows = [
        f"- {group['title']}：{'、'.join(str(item) for item in group['items'])}"
        for group in watch_groups
        if group.get("items")
    ]
    action_rows: list[str] = []
    for group in action_groups:
        title = str(group.get("title", "")).strip()
        items = [str(item).strip() for item in list(group.get("items", [])) if str(item).strip()]
        if not title or not items:
            continue
        action_rows.append(f"- {title}")
        action_rows.extend(f"  - {item}" for item in items)

    shown_items = _safe_int_from_text(metadata.get("高优先级展示条数", "0/0").split("/")[0])
    total_items = _safe_int_from_text(metadata.get("总新闻条数", "0"))
    return {
        "summary_date": metadata.get("日期", ""),
        "source_batch": metadata.get("来源批次", ""),
        "source_path": str(path),
        "total_items": total_items,
        "shown_items": shown_items,
        "impact_summary": metadata.get("影响分布", ""),
        "filter_mode": metadata.get("过滤模式", ""),
        "core_summary": " ".join(sections.get("核心摘要", [])).strip(),
        "one_line_advice": " ".join(sections.get("一句话建议", [])).strip(),
        "daily_conclusion": " ".join(sections.get("当日结论", [])).strip(),
        "operation_tips": " ".join(sections.get("操作提示", [])).strip(),
        "read_order": read_order,
        "watch_groups": watch_groups,
        "watch_group_count": len(watch_groups),
        "watch_rows": watch_rows,
        "action_groups": action_groups,
        "action_rows": action_rows,
        "priority_channel_rows": list(sections.get("优先级通道", [])),
    }


def _safe_int_from_text(value: str) -> int:
    """Extract the first integer-like number from a short text value."""
    digits = "".join(character for character in str(value) if character.isdigit())
    return int(digits) if digits else 0
