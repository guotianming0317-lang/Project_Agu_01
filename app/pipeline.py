"""Reusable monitor pipeline for manual and scheduled runs."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.alerts.alert_rules import evaluate_alerts
from app.alerts.notifier import build_alert_digest_text
from app.analysis.leader_detector import detect_sector_leaders
from app.config import AppConfig
from app.data_sources.akshare_client import (
    build_quote_source_display_text,
    fetch_realtime_quotes,
    get_fetch_path,
    get_quote_source,
)
from app.database import initialize_database, save_alerts, save_market_snapshots
from app.reports.context_rules import (
    build_industry_chain_mapping,
    build_position_bias_hint,
    build_tomorrow_plan,
    classify_strength_label,
    collect_positive_alert_messages,
    collect_risk_alert_messages,
    get_top_sector_average_pct_chg,
    pick_sector_stock_names,
    pick_top_stock_names,
    rank_sectors_by_pct_chg,
)
from app.reports.evening_report import (
    build_evening_report,
    build_evening_report_from_database,
)
from app.reports.morning_report import build_morning_report
from app.reports.shared import join_report_items
from app.sectors import (
    CONSOLE_OVERVIEW_DISPLAY,
    DETAILED_ALERT_DISPLAY,
    HIGH_VALUE_ALERT_TYPES,
    MARKET_FOCUS_OBSERVATION_TEMPLATES,
    MARKET_FOCUS_SNAPSHOT_DISPLAY,
    MARKET_FOCUS_STATE_RULES,
    MATERIAL_RELATED_SECTORS,
    MONITOR_UNIVERSE_DISPLAY,
    SEMICONDUCTOR_EQUIPMENT_SECTOR,
    SEMICONDUCTOR_GAS_SECTOR,
    SEMICONDUCTOR_MATERIAL_SECTOR,
    STAGE_ALIGNMENT_TEMPLATES,
    TASK_RESULT_SUMMARY_RULES,
    build_default_focus_sectors,
)
from app.task_profiles import JOB_INTENT_STRATEGIES, TASK_RESULT_SUMMARY_DECISION_RULES
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
    get_all_stocks,
    get_high_priority_stocks,
)


@dataclass(slots=True)
class MonitorCycleResult:
    """Structured result of one monitor cycle."""

    snapshot_time: str
    quote_source: str
    all_stocks_count: int
    high_priority_count: int
    market_rows: list[dict[str, object]]
    alerts: list[dict[str, object]]
    morning_report: str
    evening_report: str
    fetch_path: str = ""
    stock_pool_structure_summary: str = ""
    stock_pool_comparison_highlight_summary: str = ""
    stock_pool_comparison_tag_labels: list[str] | None = None
    stock_pool_health_hints: list[str] | None = None


def run_monitor_cycle(config: AppConfig) -> MonitorCycleResult:
    """Run one monitor cycle and persist outputs."""
    from datetime import datetime

    initialize_database(config.database_path)
    all_stocks = get_all_stocks()
    high_priority = get_high_priority_stocks()
    snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    market_rows, quote_source, fetch_path = _resolve_market_rows(snapshot_time)
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)
    alerts = evaluate_alerts(
        market_rows,
        stock_pool_summary=stock_pool_summary,
        stock_pool_comparison=stock_pool_comparison,
    )
    market_frame = pd.DataFrame(market_rows)
    leader_frame = detect_sector_leaders(market_frame)
    morning_context = _build_morning_context(
        market_frame,
        alerts,
        stock_pool_summary=stock_pool_summary,
        stock_pool_comparison=stock_pool_comparison,
    )
    evening_context = _build_evening_context(
        market_frame,
        leader_frame,
        alerts,
        snapshot_time,
        stock_pool_summary=stock_pool_summary,
        stock_pool_comparison=stock_pool_comparison,
    )

    save_market_snapshots(config.database_path, market_rows)
    save_alerts(config.database_path, _attach_alert_timestamps(alerts, snapshot_time))

    return MonitorCycleResult(
        snapshot_time=snapshot_time,
        quote_source=quote_source,
        fetch_path=fetch_path,
        all_stocks_count=len(all_stocks),
        high_priority_count=len(high_priority),
        market_rows=market_rows,
        alerts=alerts,
        morning_report=build_morning_report(morning_context),
        evening_report=build_evening_report(evening_context),
        stock_pool_structure_summary=str(
            stock_pool_summary.get("structure_summary", "")
        ).strip(),
        stock_pool_comparison_highlight_summary=str(
            stock_pool_comparison.get("highlight_summary", "")
        ).strip(),
        stock_pool_comparison_tag_labels=list(
            stock_pool_comparison.get("comparison_tag_labels", [])
        ),
        stock_pool_health_hints=list(stock_pool_summary.get("health_hints", [])),
    )


def build_cycle_console_output(config: AppConfig, result: MonitorCycleResult) -> str:
    """Build the console output for one monitor cycle."""
    return build_cycle_console_output_with_strategy(
        config,
        result,
        intent_strategy=dict(JOB_INTENT_STRATEGIES.get("manual", {})),
    )


def build_cycle_console_output_with_strategy(
    config: AppConfig,
    result: MonitorCycleResult,
    *,
    output_strategy: dict[str, bool] | None = None,
    intent_strategy: dict[str, object] | None = None,
) -> str:
    """Build one monitor-cycle console output with a replaceable section strategy."""
    output_strategy = output_strategy or {}
    intent_strategy = intent_strategy or {}
    include_morning_report = output_strategy.get("include_morning_report", True)
    include_market_focus_snapshot = output_strategy.get(
        "include_market_focus_snapshot",
        True,
    )
    include_monitor_universe_observation = output_strategy.get(
        "include_monitor_universe_observation",
        True,
    )
    include_intraday_digest = output_strategy.get("include_intraday_digest", True)
    include_detailed_alerts = output_strategy.get("include_detailed_alerts", True)
    include_evening_report = output_strategy.get("include_evening_report", True)
    include_close_digest = output_strategy.get("include_close_digest", True)
    include_latest_review = output_strategy.get(
        "include_latest_review",
        config.auto_latest_review,
    )
    intraday_digest_strategy = _merge_digest_strategy_with_stage_chain_focus(
        dict(intent_strategy.get("intraday_digest", {})),
        intent_strategy=intent_strategy,
    )
    close_digest_strategy = _merge_digest_strategy_with_stage_chain_focus(
        dict(intent_strategy.get("close_digest", {})),
        intent_strategy=intent_strategy,
    )
    console_title = str(
        intent_strategy.get("console_title", "AI 半导体监控")
    ).strip() or "AI 半导体监控"
    console_subtitle = str(intent_strategy.get("console_subtitle", "")).strip()
    result_summary_style = str(
        intent_strategy.get("result_summary_style", "full_monitor")
    ).strip() or "full_monitor"
    result_summary = _build_task_result_summary(
        result,
        summary_style=result_summary_style,
        intent_strategy=intent_strategy,
    )

    overview_value_map = {
        "focus": console_subtitle,
        "result": result_summary,
        "environment": str(config.environment),
        "database": str(config.database_url),
        "quote_source": build_quote_source_display_text(result.quote_source),
        "total_stocks": str(result.all_stocks_count),
        "high_priority_stocks": str(result.high_priority_count),
    }
    sections = [console_title]
    console_overview_display_variant = _resolve_display_variant(
        CONSOLE_OVERVIEW_DISPLAY,
        intent_strategy=intent_strategy,
        specific_variant_key="console_overview_display_variant",
    )
    overview_block = _render_display_fields(
        list(console_overview_display_variant["fields"]),
        overview_value_map,
    )
    if overview_block:
        sections.append(overview_block)
    market_focus_snapshot = _build_market_focus_snapshot(
        result,
        intent_strategy=intent_strategy,
    )
    if include_market_focus_snapshot and market_focus_snapshot:
        market_focus_display_variant = _resolve_display_variant(
            MARKET_FOCUS_SNAPSHOT_DISPLAY,
            intent_strategy=intent_strategy,
            specific_variant_key="market_focus_display_variant",
        )
        sections.extend(
            ["", str(market_focus_display_variant["block_title"]), market_focus_snapshot, ""]
        )
    if include_morning_report:
        sections.extend(["", result.morning_report, ""])

    stock_pool_observation = _extract_stock_pool_observation_from_report(result.morning_report)
    stage_chain_focus_snapshot = _build_stage_chain_focus_snapshot(
        intent_strategy,
        market_rows=result.market_rows,
    )
    if include_monitor_universe_observation and stock_pool_observation:
        monitor_universe_display_variant = _resolve_display_variant(
            MONITOR_UNIVERSE_DISPLAY,
            intent_strategy=intent_strategy,
            specific_variant_key="monitor_universe_display_variant",
        )
        monitor_universe_lines = [stock_pool_observation]
        if stage_chain_focus_snapshot:
            monitor_universe_lines.extend(["", stage_chain_focus_snapshot])
        sections.extend(
            [
                str(monitor_universe_display_variant["block_title"]),
                "\n".join(monitor_universe_lines),
                "",
            ]
        )

    intraday_digest = build_alert_digest_text(
        result.alerts,
        stage="intraday",
        digest_strategy=intraday_digest_strategy,
    )
    if include_intraday_digest and intraday_digest:
        sections.extend([intraday_digest, ""])

    if include_detailed_alerts:
        sections.extend(
            _build_detailed_alert_section_lines(
                result.alerts,
                intent_strategy=intent_strategy,
                market_rows=result.market_rows,
            )
        )

    if include_evening_report:
        sections.append(result.evening_report)
    close_digest = build_alert_digest_text(
        result.alerts,
        stage="close",
        digest_strategy=close_digest_strategy,
    )
    if include_close_digest and close_digest:
        sections.extend(["", close_digest])

    if include_latest_review:
        sections.extend(
            [
                "",
                "最新数据库复盘",
                build_evening_report_from_database(config.database_path),
            ]
        )
        include_latest_review = False

    if include_latest_review:
        sections.extend(
            [
                "",
                "最新数据库复盘",
                build_evening_report_from_database(config.database_path),
            ]
        )

    return "\n".join(sections)


def _build_detailed_alert_section_lines(
    alerts: list[dict[str, object]],
    *,
    intent_strategy: dict[str, object],
    market_rows: list[dict[str, object]],
) -> list[str]:
    """Build the titled detailed-alert section for one monitor cycle."""
    display_variant = _resolve_detailed_alert_display_variant(intent_strategy)
    section_lines = ["", str(display_variant["block_title"])]
    sorted_alerts = _sort_alerts_for_detailed_view(
        alerts,
        intent_strategy=intent_strategy,
    )
    if not sorted_alerts:
        empty_message = str(display_variant.get("empty_message", "")).strip()
        if empty_message:
            section_lines.extend([empty_message, ""])
            return section_lines
        return []

    for alert in sorted_alerts:
        section_lines.append(
            _format_alert_block(
                alert,
                intent_strategy=intent_strategy,
                market_rows=market_rows,
            )
        )
        section_lines.append("")
    return section_lines


def _resolve_market_rows(snapshot_time: str) -> tuple[list[dict[str, object]], str, str]:
    """Prefer real quote ingestion and fall back to deterministic demo rows."""
    realtime_quotes = fetch_realtime_quotes()
    if realtime_quotes.empty:
        return _build_demo_market_rows(snapshot_time), "demo-fallback", ""
    quote_source = get_quote_source(realtime_quotes) or "akshare"
    fetch_path = get_fetch_path(realtime_quotes)
    return _enrich_realtime_quotes(
        realtime_quotes,
        snapshot_time,
        quote_source=quote_source,
    ), quote_source, fetch_path


def _enrich_realtime_quotes(
    quotes: pd.DataFrame,
    snapshot_time: str,
    *,
    quote_source: str,
) -> list[dict[str, object]]:
    """Attach universe metadata to normalized realtime quotes."""
    universe_map = {stock["code"]: stock for stock in get_all_stocks()}
    enriched_rows: list[dict[str, object]] = []

    for row in quotes.to_dict(orient="records"):
        stock_meta = universe_map.get(str(row.get("code", "")), {})
        enriched_rows.append(
            {
                "timestamp": snapshot_time,
                "sector": stock_meta.get("sector", "n/a"),
                "code": str(row.get("code", "")),
                "name": str(row.get("name", "")),
                "price": row.get("price"),
                "pct_chg": row.get("pct_chg"),
                "turnover": row.get("turnover"),
                "turnover_rate": row.get("turnover_rate"),
                "volume_ratio": row.get("volume_ratio"),
                "priority": stock_meta.get("priority", 2),
                "quote_source": quote_source,
            }
        )

    return enriched_rows


def _build_demo_market_rows(snapshot_time: str) -> list[dict[str, object]]:
    """Create a small deterministic market snapshot for local demo runs."""
    return [
        {
            "timestamp": snapshot_time,
            "sector": SEMICONDUCTOR_GAS_SECTOR,
            "code": "688549",
            "name": "Demo Gas 1",
            "price": 12.34,
            "pct_chg": 8.6,
            "turnover": 800.0,
            "turnover_rate": 5.5,
            "volume_ratio": 2.8,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
        {
            "timestamp": snapshot_time,
            "sector": SEMICONDUCTOR_GAS_SECTOR,
            "code": "688268",
            "name": "Demo Gas 2",
            "price": 45.20,
            "pct_chg": 5.2,
            "turnover": 500.0,
            "turnover_rate": 3.2,
            "volume_ratio": 1.9,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
        {
            "timestamp": snapshot_time,
            "sector": SEMICONDUCTOR_MATERIAL_SECTOR,
            "code": "688019",
            "name": "Demo Material 1",
            "price": 132.8,
            "pct_chg": 5.1,
            "turnover": 450.0,
            "turnover_rate": 2.6,
            "volume_ratio": 2.1,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
        {
            "timestamp": snapshot_time,
            "sector": SEMICONDUCTOR_EQUIPMENT_SECTOR,
            "code": "002371",
            "name": "Demo Equipment 1",
            "price": 310.5,
            "pct_chg": 3.4,
            "turnover": 1100.0,
            "turnover_rate": 2.0,
            "volume_ratio": 1.4,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
        {
            "timestamp": snapshot_time,
            "sector": SEMICONDUCTOR_EQUIPMENT_SECTOR,
            "code": "688012",
            "name": "Demo Equipment 2",
            "price": 162.2,
            "pct_chg": 2.8,
            "turnover": 700.0,
            "turnover_rate": 1.7,
            "volume_ratio": 1.1,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
        {
            "timestamp": snapshot_time,
            "sector": "AI Server",
            "code": "601138",
            "name": "Demo Server",
            "price": 28.6,
            "pct_chg": 1.2,
            "turnover": 900.0,
            "turnover_rate": 1.0,
            "volume_ratio": 0.9,
            "priority": 1,
            "quote_source": "demo-fallback",
        },
    ]


def _build_morning_context(
    market_frame: pd.DataFrame,
    alerts: list[dict[str, object]],
    *,
    stock_pool_summary: dict[str, object] | None = None,
    stock_pool_comparison: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build structured inputs for the morning report."""
    ranked_sectors = rank_sectors_by_pct_chg(market_frame, limit=3)
    top_sector = ranked_sectors[0] if ranked_sectors else SEMICONDUCTOR_MATERIAL_SECTOR
    focus_sectors = ranked_sectors or build_default_focus_sectors(top_sector)
    strongest_avg = get_top_sector_average_pct_chg(market_frame)
    risk_messages = collect_risk_alert_messages(alerts, limit=3)
    stock_pool_summary = stock_pool_summary or build_stock_pool_health_summary()
    stock_pool_comparison = stock_pool_comparison or build_stock_pool_health_comparison(
        stock_pool_summary
    )

    return {
        "overseas_strength": classify_strength_label(strongest_avg),
        "a_share_mapping": build_industry_chain_mapping(top_sector),
        "focus_sectors": focus_sectors,
        "focus_stocks": pick_top_stock_names(market_frame, limit=3),
        "main_risks": " | ".join(risk_messages)
        if risk_messages
        else "Export restriction and overseas volatility still need tracking",
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
        "stock_pool_health_hints": list(stock_pool_summary.get("health_hints", [])),
    }


def _build_evening_context(
    market_frame: pd.DataFrame,
    leader_frame: pd.DataFrame,
    alerts: list[dict[str, object]],
    snapshot_time: str,
    *,
    stock_pool_summary: dict[str, object] | None = None,
    stock_pool_comparison: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build structured inputs for the evening report."""
    ranked_sectors = rank_sectors_by_pct_chg(market_frame)
    strongest_sector = ranked_sectors[0] if len(ranked_sectors) >= 1 else "n/a"
    secondary_sector = ranked_sectors[1] if len(ranked_sectors) >= 2 else strongest_sector
    fading_sector = ranked_sectors[-1] if ranked_sectors else "n/a"
    leaders = {
        leader_type: group.iloc[0]["name"]
        for leader_type, group in leader_frame.groupby("leader_type", sort=False)
    }
    negative_news = collect_risk_alert_messages(alerts, limit=3)
    stock_pool_summary = stock_pool_summary or build_stock_pool_health_summary()
    stock_pool_comparison = stock_pool_comparison or build_stock_pool_health_comparison(
        stock_pool_summary
    )

    return {
        "date": snapshot_time.split(" ")[0],
        "strongest_sector": strongest_sector,
        "secondary_sector": secondary_sector,
        "fading_sector": fading_sector,
        "leaders": leaders,
        "materials_watch": pick_sector_stock_names(
            market_frame,
            set(MATERIAL_RELATED_SECTORS),
            limit=3,
        )
        or ["Materials", "Gas", "Equipment"],
        "positive_news": collect_positive_alert_messages(alerts, limit=3)
        or ["Materials and gas stayed relatively strong during the session"],
        "negative_news": negative_news or ["Export restriction risk still needs confirmation"],
        "tomorrow_plan": build_tomorrow_plan(
            strongest_sector,
            secondary_sector,
            risk_count=len(negative_news),
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
        "stock_pool_health_hints": list(stock_pool_summary.get("health_hints", [])),
    }


def _attach_alert_timestamps(
    alerts: list[dict[str, object]], snapshot_time: str
) -> list[dict[str, object]]:
    """Attach a common timestamp to alert rows before persistence."""
    enriched: list[dict[str, object]] = []
    for alert in alerts:
        alert_copy = dict(alert)
        alert_copy.setdefault("timestamp", snapshot_time)
        enriched.append(alert_copy)
    return enriched


def _format_alert_block(alert: dict[str, object]) -> str:
    """Render alert details as a simple legacy-compatible console block."""
    lines = [
        f"[{alert.get('severity', 'info')}] 预警",
        f"时间：{alert.get('time_label', 'intraday')}",
        f"方向：{alert.get('sector', 'n/a')}",
        f"相关个股：{alert.get('stock_name', 'n/a')}",
        f"原因：{alert.get('reason', 'n/a')}",
        f"趋势：{alert.get('trend', 'watch')}",
        f"关注点：{alert.get('action', 'continue tracking')}",
    ]
    return "\n".join(lines)


def _extract_stock_pool_observation_from_report(report_text: str) -> str:
    """Extract the reusable stock-pool observation block from one report text."""
    lines = [line.rstrip() for line in str(report_text).splitlines()]
    section_start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("7."):
            section_start = index + 1
            break
    if section_start is None:
        return ""

    section_lines: list[str] = []
    for line in lines[section_start:]:
        if not line.strip():
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def _merge_digest_strategy_with_stage_chain_focus(
    digest_strategy: dict[str, object],
    *,
    intent_strategy: dict[str, object],
) -> dict[str, object]:
    """Attach stage chain-focus preferences to one digest strategy."""
    merged_strategy = dict(digest_strategy)
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    if preferred_chain_groups:
        merged_strategy["preferred_chain_groups"] = preferred_chain_groups
    return merged_strategy


def _build_stage_chain_focus_snapshot(
    intent_strategy: dict[str, object],
    *,
    market_rows: list[dict[str, object]] | None = None,
) -> str:
    """Build one short stage-specific chain-focus snapshot from stock-pool coverage."""
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    if not preferred_chain_groups:
        return ""

    stock_pool_summary = build_stock_pool_health_summary()
    chain_group_counts = dict(stock_pool_summary.get("chain_group_counts", {}))
    live_strength_by_chain_group = _build_stage_chain_group_strength_map(
        market_rows or []
    )
    ranked_chain_groups = _rank_stage_chain_groups(
        preferred_chain_groups,
        chain_group_counts=chain_group_counts,
        live_strength_by_chain_group=live_strength_by_chain_group,
    )
    coverage_items = [
        f"{chain_group} {int(chain_group_counts.get(chain_group, 0) or 0)}"
        for chain_group in ranked_chain_groups
    ]
    missing_groups = [
        chain_group
        for chain_group in ranked_chain_groups
        if int(chain_group_counts.get(chain_group, 0) or 0) <= 0
    ]

    stage_chain_value_map = {
        "stage_chain_focus": join_report_items(ranked_chain_groups, default="n/a"),
        "pool_coverage": join_report_items(coverage_items, default="n/a"),
        "live_strength": "",
        "coverage_gap": "",
    }
    live_strength_items = [
        f"{chain_group} {live_strength_by_chain_group.get(chain_group, 0.0):.2f}%"
        for chain_group in ranked_chain_groups
        if chain_group in live_strength_by_chain_group
    ]
    if live_strength_items:
        stage_chain_value_map["live_strength"] = join_report_items(
            live_strength_items,
            default="n/a",
        )
    if missing_groups:
        stage_chain_value_map["coverage_gap"] = join_report_items(
            missing_groups,
            default="n/a",
        )
    display_variant = _resolve_display_variant(
        MONITOR_UNIVERSE_DISPLAY,
        intent_strategy=intent_strategy,
        specific_variant_key="monitor_universe_display_variant",
    )
    return _render_display_fields(
        list(display_variant["stage_chain_fields"]),
        stage_chain_value_map,
    )


def _build_stage_focus_observation_suffix(
    intent_strategy: dict[str, object],
    *,
    market_rows: list[dict[str, object]],
    alerts: list[dict[str, object]],
) -> str:
    """Build one short stage-aware observation suffix from aligned chain strength."""
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    if not preferred_chain_groups:
        return ""

    live_strength_by_chain_group = _build_stage_chain_group_strength_map(market_rows)
    ranked_chain_groups = _rank_stage_chain_groups(
        preferred_chain_groups,
        chain_group_counts={},
        live_strength_by_chain_group=live_strength_by_chain_group,
    )
    if not ranked_chain_groups:
        return ""

    strongest_chain_group = ranked_chain_groups[0]
    strongest_chain_strength = live_strength_by_chain_group.get(strongest_chain_group)
    if strongest_chain_strength is None:
        return ""
    confirmation_text = _build_stage_focus_confirmation_text(
        strongest_chain_group,
        alerts=alerts,
    )
    return (
        f"For this stage, {strongest_chain_group} is the strongest aligned chain "
        f"at {strongest_chain_strength:.2f}%. {confirmation_text}"
    )


def _build_stage_focus_confirmation_text(
    strongest_chain_group: str,
    *,
    alerts: list[dict[str, object]],
) -> str:
    """Build one short confirmation hint from high-value alerts aligned with the chain."""
    matching_alert_types = _collect_matching_high_value_alert_types(
        strongest_chain_group,
        alerts=alerts,
    )
    if not matching_alert_types:
        return "No high-value alert confirmation is active yet."
    return (
        "Signal confirmation is active via "
        + join_report_items(matching_alert_types, default="n/a")
        + "."
    )


def _collect_matching_high_value_alert_types(
    strongest_chain_group: str,
    *,
    alerts: list[dict[str, object]],
) -> list[str]:
    """Collect unique high-value alert types aligned with one chain group."""
    matching_alert_types: list[str] = []
    for alert in alerts:
        alert_type = str(alert.get("alert_type", "")).strip()
        if alert_type not in HIGH_VALUE_ALERT_TYPES:
            continue
        if not _alert_matches_chain_group(alert, strongest_chain_group):
            continue
        if alert_type not in matching_alert_types:
            matching_alert_types.append(alert_type)
    return matching_alert_types


def _alert_matches_chain_group(
    alert: dict[str, object],
    strongest_chain_group: str,
) -> bool:
    """Return whether one alert text appears aligned with one chain-group label."""
    normalized_chain_group = str(strongest_chain_group).strip()
    if not normalized_chain_group:
        return False

    alert_text = " ".join(
        [
            str(alert.get("direction", "")).strip(),
            str(alert.get("message", "")).strip(),
            str(alert.get("focus", "")).strip(),
        ]
    )
    alias_map = {
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮村杈┬㈤梻浣规偠閸庮垶宕濆畝鍕垫晪闂侇剙绉甸悡娑橆熆鐠轰警鍎忛柣蹇婃櫆閵囧嫰鏁傜拠鍙夌彎濠殿喖锕ュ钘夌暦椤愶箑绀嬫い鎾寸⊕閻庨亶姊绘担鍛婂暈闁挎岸鏌曢崼銏╃劸闁?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮村杈┬㈤梻浣规偠閸庮垶宕濆畝鍕垫晪闂侇剙绉甸悡娑橆熆鐠轰警鍎忛柣蹇婃櫆閵囧嫰鏁傜拠鍙夌彎濠殿喖锕ュ钘夌暦椤愶箑绀嬫い鎾寸⊕閻庨亶姊绘担鍛婂暈闁挎岸鏌曢崼銏╃劸闁?", "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑娑⑺囬悽绋挎瀬闁瑰墽绮崑鎰亜閺冨倹鍤€濞存粓绠栭弻娑㈠箛闂堟稒鐏堥悗鐟版啞缁诲牓骞冨Δ鈧埥澶娾枍閾忣偄鐏ラ柍璇茬Ч瀹曞爼顢楁担鍙夊闂傚倸鍊搁悧濠勭矙閹惧瓨娅犻柡鍥╁枂娴滄粓鏌ㄩ弮鍥ㄧ《闁活厽鐟ч埀顒侇問閸ｎ噣宕戦崱娑樼劦妞ゆ帒锕︾粔鐢告煕閻樺磭澧遍柣銉海椤﹀綊鏌＄仦鍓ф创妞ゃ垺娲熼弫鎰板炊閿濆棭娼旀繝鐢靛Т閻ュ濡堕崱鈺傤棄闂備礁鐤囬～澶愬垂閸фぜ鈧礁鈽夊Ο閿嬵潔濠电偛妫楃换鎰板绩椤撱垺鈷掑ù锝呮啞閹牓鏌ｉ鈧妶绋跨暦娴兼潙鍐€妞ゆ挾濮寸粊锕傛⒑缁洖澧查柛鎴犳嚀鍗卞Δ锝呭暞閳锋垿鏌涢敂璇插箺婵炲懏娲栭埞鎴︻敋閳ь剟藟閹炬緞锝夊箛閺夎法顔掗梺褰掝暒缁€渚€骞冮幋锔解拺闁告稑锕ｇ欢閬嶆煕閵婏箑鈻曟い銏＄懇楠炴帒螖娴ｅ弶瀚?", "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮村杈┬㈤梻浣规偠閸庮垶宕濆畝鍕垫晪闂侇剙绉甸悡娑橆熆鐠轰警鍎忛柣蹇婃櫆閵囧嫰鏁傜拠鍙夌彎濠殿喖锕ュ钘夌暦椤愶箑绀嬫い鎾寸⊕閻庨亶姊绘担鍛婂暈闁挎岸鏌曢崼銏╃劸闁伙絽鍢查埢搴ㄥ箻閺夋垳姹楃紓鍌氬€烽悞锕傗€﹂崶顒€鍌ㄩ柟鍓х帛閳锋垿姊婚崼鐔剁繁婵＄嫏鍛＜闁绘ê鍟块悘锕傛煛閸涱厾鍩ｆい銏＄☉閳藉顫濇鏍ф櫗闂備浇顕х换鎰崲閹达附鍋嬫俊銈傚亾闁宠绉电换婵嬪炊閵娧冨箰闁诲骸鍘滈崑鎾绘倵閿濆骸澧伴柣锕€鐗撻幃妤冩喆閸曨剛顦ㄩ柣銏╁灡鐢繝鏁愰悙娴嬫斀閻庯絽鐏氶弲鐐烘⒑閸忛棿鑸柛搴ㄤ憾閹焦娼忛埡鍐紳?"),
        "婵犵數濮烽弫鍛婃叏閻戣棄鏋侀柛娑橈攻閸欏繘鏌ｉ姀鐘差棌闁轰礁锕弻鈥愁吋鎼粹€崇缂備焦鍔栭〃鍡樼┍婵犲洤围闁告侗鍙庢禒楣冩⒑閻熸澘鏆遍柣顓炲€搁～蹇曠磼濡顎撻梺鍛婄☉閿曘儵宕曢幘缁樷拺婵炶尪顕ф禍婵嬫煟閻斿弶娅呴柣锝囧厴婵℃悂鍩℃繝鍐╂珫婵犵數濮撮敃銈団偓娑掓櫇閻?": ("婵犵數濮烽弫鍛婃叏閻戣棄鏋侀柛娑橈攻閸欏繘鏌ｉ姀鐘差棌闁轰礁锕弻鈥愁吋鎼粹€崇缂備焦鍔栭〃鍡樼┍婵犲洤围闁告侗鍙庢禒楣冩⒑閻熸澘鏆遍柣顓炲€搁～蹇曠磼濡顎撻梺鍛婄☉閿曘儵宕曢幘缁樷拺婵炶尪顕ф禍婵嬫煟閻斿弶娅呴柣锝囧厴婵℃悂鍩℃繝鍐╂珫婵犵數濮撮敃銈団偓娑掓櫇閻?", "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑娑⑺囬悽绋挎瀬闁瑰墽绮崑鎰亜閺冨倹鍤€濞存粓绠栭弻娑㈠箛闂堟稒鐏堥悗鐟版啞缁诲牓骞冨Δ鈧埥澶娾枍閾忣偄鐏ラ柍璇茬Ч瀹曞爼顢楁担鍙夊闂傚倸鍊搁悧濠勭矙閹惧瓨娅犻柡鍥╁枂娴滄粓鏌ㄩ弮鍥ㄧ《闁活厽鐟ч埀顒侇問閸ｎ噣宕戦崱娑樼劦妞ゆ帒锕︾粔鐢告煕閻樺磭澧遍柣銉海椤﹀綊鏌＄仦鍓ф创妞ゃ垺娲熼弫鎰板炊閿濆棭娼旀繝鐢靛Т閻ュ濡堕崱鈺傤棄闂備礁鐤囬～澶愬垂閸фぜ鈧礁鈽夊Ο閿嬵潔濠电偛妫楃换鎰板绩椤撱垺鈷掑ù锝呮啞閹牓鏌ｉ鈧妶绋跨暦娴兼潙鍐€妞ゆ挾濮寸粊锕傛⒑缁洖澧查柛鎴犳嚀椤﹪濡搁埡鍌楁嫼闂佺鍋愰崑娑㈠焵椤掍緡娈滅€规洑鍗抽獮鍥级鐠恒劎鏉介梻渚€娼ц墝闁哄懏绮撳鏌ュ蓟閵夛妇鍘遍梺鏂ユ櫅閸熶即骞婇崨瀛樼厽闁圭虎鍨版禍楣冩⒒?", "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮村杈┬㈤梻浣规偠閸庮垶宕濆畝鍕垫晪闂侇剙绉甸悡娑橆熆鐠轰警鍎忛柣蹇婃櫆閵囧嫰鏁傜拠鍙夌彎濠殿喖锕ュ钘夌暦椤愶箑绀嬫い鎾寸⊕閻庨亶姊绘担鍛婂暈闁挎岸鏌曢崼銏╃劸闁伙絽鍢查埢搴ㄥ箻閺夋垳姹楃紓鍌氬€烽悞锕傗€﹂崶顒€鍌ㄩ柟鍓х帛閳锋垿姊婚崼鐔剁繁婵＄嫏鍛＜闁绘ê鍟块悘锕傛煛閸涱厾鍩ｆい銏＄☉閳藉顫濇鏍ф櫗闂備浇顕х换鎰崲閹达附鍋嬫俊銈傚亾闁宠绉电换婵嬪炊閵娧冨箰闁诲骸鍘滈崑鎾绘倵閿濆骸澧伴柣锕€鐗撻幃妤冩喆閸曨剛顦ㄩ柣銏╁灡鐢繝鏁愰悙娴嬫斀閻庯絽鐏氶弲鐐烘⒑閸忛棿鑸柛搴ㄤ憾閹焦娼忛埡鍐紳?"),
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞鐟滃繘寮抽敃鍌涚厱妞ゎ厽鍨垫禍婵嬫煕濞嗗繒绠婚柡宀€鍠栭獮鍡涘级閸熷啯鎹囬弻娑欑節閸屾稑浠撮梺鍝勮閸旀垵顕ｉ幘顔藉€锋繛鏉戭儏娴滈箖鏌涘┑鍕姎妞ゃ儲宀搁弻娑滎槼妞ゃ劌妫濋幃鈥斥枎閹炬潙浠梺鍛婄箓鐎氼參骞嗛崼鐔翠簻?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞鐟滃繘寮抽敃鍌涚厱妞ゎ厽鍨垫禍婵嬫煕濞嗗繒绠婚柡宀€鍠栭獮鍡涘级閸熷啯鎹囬弻娑欑節閸屾稑浠撮梺鍝勮閸旀垵顕ｉ幘顔藉€锋繛鏉戭儏娴滈箖鏌涘┑鍕姎妞ゃ儲宀搁弻娑滎槼妞ゃ劌妫濋幃鈥斥枎閹炬潙浠梺鍛婄箓鐎氼參骞嗛崼鐔翠簻?", "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑娑⑺囬悽绋挎瀬闁瑰墽绮崑鎰亜閺冨倹鍤€濞存粓绠栭弻娑㈠箛闂堟稒鐏堥悗鐟版啞缁诲牓骞冨Δ鈧埥澶娾枍閾忣偄鐏ラ柍璇茬Ч瀹曞爼顢楁担鍙夊闂傚倸鍊搁悧濠勭矙閹惧瓨娅犻柡鍥╁枂娴滄粓鏌ㄩ弮鍥ㄧ《闁活厽鐟ч埀顒侇問閸ｎ噣宕戦崱娑樼劦妞ゆ帒锕︾粔鐢告煕閻樺磭澧遍柣銉海椤﹀綊鏌＄仦鍓ф创妞ゃ垺娲熼弫鎰板炊閿濆棭娼旀繝鐢靛Т閻ュ濡堕崱鈺傤棄闂備礁鐤囬～澶愬垂閸фぜ鈧礁鈽夊Ο閿嬵潔濠电偛妫楃换鎰板绩椤撱垺鈷掑ù锝呮啞閹牓鏌ｉ鈧妶绋跨暦娴兼潙鍐€妞ゆ挾濮寸粊锕傛⒑绾懏褰х紒鐘冲灩缁鈽夐姀鈾€鎷婚梺鍓插亞閸犳捇鍩婇弴銏＄厽闁挎繂瀚畵鍡樻叏婵犲嫮甯涢柟宄版嚇瀹曘劍绻濋崘銊︾€鹃梻鍌欑閹芥粍鎱ㄧ€电硶鍋撳☉鎺撴珚闁靛棗鍟存俊鐑藉煛娴ｄ警鍟囧┑鐐舵彧缁插墽绮婇幘顔肩；?"),
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌ｉ幋锝呅撻柛銈呭閺屾盯顢曢敐鍡欙紩闂侀€炲苯澧剧紒鐘虫尭閻ｉ攱绺界粙娆炬綂闂佺偨鍎遍崯璺ㄨ姳閵夆晜鈷掑ù锝囩摂濞兼劖绻濋姀鈽呰€跨€规洩缍侀獮妯兼嫚閼碱剙鈧偛顪冮妶鍡楀潑闁稿鎸剧槐鎺楁偑閳ь剟宕归崼鏇炵畺婵せ鍋撻柟顔界懅閹瑰嫰鎯勯幒鎾村鞍缂佺粯鐩畷濂告偄閸濆嫬缁╂繝?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌ｉ幋锝呅撻柛銈呭閺屾盯顢曢敐鍡欙紩闂侀€炲苯澧剧紒鐘虫尭閻ｉ攱绺界粙娆炬綂闂佺偨鍎遍崯璺ㄨ姳閵夆晜鈷掑ù锝囩摂濞兼劖绻濋姀鈽呰€跨€规洩缍侀獮妯兼嫚閼碱剙鈧偛顪冮妶鍡楀潑闁稿鎸剧槐鎺楁偑閳ь剟宕归崼鏇炵畺婵せ鍋撻柟顔界懅閹瑰嫰鎯勯幒鎾村鞍缂佺粯鐩畷濂告偄閸濆嫬缁╂繝?", "CPO"),
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮撮姀鈩冩珕闂佽姤锚椤︻喚绱旈弴銏♀拻濞达綀娅ｉ妴濠囨煕閹惧绠為柟顔炬焿椤﹀綊鏌熼姘辩劯妤犵偞顭囩槐鎺懳熺悰鈥充壕闁割煈鍋嗙粻楣冩煙鐎电鍓卞ù鐓庢閺岀喐娼忛崜褏鏆犻梺娲诲幗椤ㄥ﹪鎮￠锕€鐐婇柕濞р偓婵洭姊虹紒妯诲暗闁哥姵鐗犲濠氭晸閻樿尙顦ㄩ梺闈涱焾閸庮噣宕戦幘璇蹭紶闁靛闄勫▓浼存⒑閸撴彃浜濇繛鍙夛耿閸?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾剧懓顪冪€ｎ亝鎹ｉ柣顓炴閵嗘帒顫濋敐鍛婵°倗濮烽崑鐐烘偋閻樻眹鈧線寮撮姀鈩冩珕闂佽姤锚椤︻喚绱旈弴銏♀拻濞达綀娅ｉ妴濠囨煕閹惧绠為柟顔炬焿椤﹀綊鏌熼姘辩劯妤犵偞顭囩槐鎺懳熺悰鈥充壕闁割煈鍋嗙粻楣冩煙鐎电鍓卞ù鐓庢閺岀喐娼忛崜褏鏆犻梺娲诲幗椤ㄥ﹪鎮￠锕€鐐婇柕濞р偓婵洭姊虹紒妯诲暗闁哥姵鐗犲濠氭晸閻樿尙顦ㄩ梺闈涱焾閸庮噣宕戦幘璇蹭紶闁靛闄勫▓浼存⒑閸撴彃浜濇繛鍙夛耿閸?", "缂傚倸鍊搁崐鎼佸磹閹间礁纾归柟闂寸绾惧綊鏌熼梻瀵割槮缁炬儳缍婇弻锝夊箣閿濆憛鎾绘煕閵堝懎顏柡灞诲€楃划娆戞崉閵娿倗椹抽梻浣告啞閻熴儳鎹㈠鈧濠氭晲婢跺娼婇梺鏂ユ櫅閸燁偅绂掗埡鍛拺闂侇偆鍋涢懟顖涙櫠椤曗偓閺屾盯鎮㈤崨濠勭▏闂佷紮绲块崗妯讳繆閹间礁鐓涘┑鐘插暞濞呮捇姊绘担钘壭撻柨姘亜閿旇鐏￠悗?"),
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞妞ゆ帒顦伴弲顏堟偡濠婂啰绠婚柛鈹惧亾濡炪倖甯婇懗鍫曞煝閹剧粯鐓涢柛娑卞枤缁犳﹢鏌涢幒鎾崇瑨闁宠閰ｉ獮妯虹暦閸ヨ泛鏁藉┑鐘茬棄閺夊簱鍋撻幘缁樺€块柨鏇楀亾闁宠绉瑰顕€宕奸悢鍙夊?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞妞ゆ帒顦伴弲顏堟偡濠婂啰绠婚柛鈹惧亾濡炪倖甯婇懗鍫曞煝閹剧粯鐓涢柛娑卞枤缁犳﹢鏌涢幒鎾崇瑨闁宠閰ｉ獮妯虹暦閸ヨ泛鏁藉┑鐘茬棄閺夊簱鍋撻幘缁樺€块柨鏇楀亾闁宠绉瑰顕€宕奸悢鍙夊?", "HBM"),
        "闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞妞ゆ帒顦伴弲顏堟偡濠婂啰绠绘鐐村灴婵偓闁靛牆鎳愰悿鈧俊鐐€栧Λ浣肝涢崟顒佸劅濠电姴娲﹂悡鐔煎箹閹碱厼鐏ｇ紒澶屾暬閺屾盯鎮╅幇浣圭杹閻庤娲橀崝娆忕暦缁嬭鏃€鎷呴崫鍕辈闂傚倷绀侀幖顐﹀磹閹间焦鍊舵繝闈涱儏閻撴洟鏌￠崘銊у闁?": ("闂傚倸鍊搁崐鎼佸磹閹间礁纾圭€瑰嫭鍣磋ぐ鎺戠倞妞ゆ帒顦伴弲顏堟偡濠婂啰绠绘鐐村灴婵偓闁靛牆鎳愰悿鈧俊鐐€栧Λ浣肝涢崟顒佸劅濠电姴娲﹂悡鐔煎箹閹碱厼鐏ｇ紒澶屾暬閺屾盯鎮╅幇浣圭杹閻庤娲橀崝娆忕暦缁嬭鏃€鎷呴崫鍕辈闂傚倷绀侀幖顐﹀磹閹间焦鍊舵繝闈涱儏閻撴洟鏌￠崘銊у闁?", "Chiplet"),
    }
    aliases = alias_map.get(normalized_chain_group, (normalized_chain_group,))
    return any(alias and alias in alert_text for alias in aliases)


def _rank_stage_chain_groups(
    preferred_chain_groups: list[str],
    *,
    chain_group_counts: dict[str, int],
    live_strength_by_chain_group: dict[str, float] | None = None,
) -> list[str]:
    """Rank one stage's preferred chain groups by current pool coverage strength."""
    live_strength_by_chain_group = live_strength_by_chain_group or {}
    indexed_chain_groups = list(enumerate(preferred_chain_groups))
    ranked_chain_groups = sorted(
        indexed_chain_groups,
        key=lambda item: (
            -float(live_strength_by_chain_group.get(item[1], float("-inf"))),
            -int(chain_group_counts.get(item[1], 0) or 0),
            item[0],
        ),
    )
    return [chain_group for _, chain_group in ranked_chain_groups]


def _build_stage_chain_group_strength_map(
    market_rows: list[dict[str, object]],
) -> dict[str, float]:
    """Map one stage's chain groups to current average percentage change."""
    if not market_rows:
        return {}

    stock_chain_group_map = {
        str(stock.get("code", "")).strip(): str(stock.get("chain_group", "")).strip()
        for stock in get_all_stocks()
        if str(stock.get("code", "")).strip() and str(stock.get("chain_group", "")).strip()
    }
    strength_rows: dict[str, list[float]] = {}
    for row in market_rows:
        code = str(row.get("code", "")).strip()
        chain_group = stock_chain_group_map.get(code, "")
        if not chain_group:
            continue
        pct_chg = pd.to_numeric(row.get("pct_chg"), errors="coerce")
        if pd.isna(pct_chg):
            continue
        strength_rows.setdefault(chain_group, []).append(float(pct_chg))

    return {
        chain_group: sum(values) / len(values)
        for chain_group, values in strength_rows.items()
        if values
    }


def _build_market_focus_snapshot(
    result: MonitorCycleResult,
    *,
    intent_strategy: dict[str, object] | None = None,
) -> str:
    """Build one compact business-facing market focus snapshot."""
    if not result.market_rows:
        return ""

    intent_strategy = intent_strategy or {}
    market_frame = pd.DataFrame(result.market_rows)
    ranked_sectors = rank_sectors_by_pct_chg(market_frame, limit=2)
    strongest_sector = ranked_sectors[0] if ranked_sectors else "n/a"
    secondary_sector = ranked_sectors[1] if len(ranked_sectors) >= 2 else "n/a"
    focus_stocks = pick_top_stock_names(market_frame, limit=3)
    strongest_avg = get_top_sector_average_pct_chg(market_frame)
    secondary_avg = _get_sector_average_pct_chg(market_frame, secondary_sector)
    red_count = _count_alert_level(result.alerts, "red")
    orange_count = _count_alert_level(result.alerts, "orange")
    high_value_count = _count_high_value_alerts(result.alerts)
    market_state = _classify_market_focus_state(
        strongest_avg=strongest_avg,
        secondary_avg=secondary_avg,
        red_count=red_count,
        high_value_count=high_value_count,
    )
    market_observation = _build_market_focus_observation(
        market_state=market_state,
        strongest_sector=strongest_sector,
        secondary_sector=secondary_sector,
    )
    stage_focus_observation = _build_stage_focus_observation_suffix(
        intent_strategy,
        market_rows=result.market_rows,
        alerts=result.alerts,
    )
    if stage_focus_observation:
        market_observation = f"{market_observation} {stage_focus_observation}"

    value_map = {
        "market_state": _format_market_focus_state(market_state),
        "observation": market_observation,
        "strongest_sector": strongest_sector,
        "second_sector": secondary_sector,
        "top_sector_average_move": f"{strongest_avg:.2f}%",
        "top_focus_stocks": join_report_items(focus_stocks, default="n/a"),
        "alert_mix": f"红色 {red_count}，橙色 {orange_count}，高价值 {high_value_count}",
    }
    display_variant = _resolve_display_variant(
        MARKET_FOCUS_SNAPSHOT_DISPLAY,
        intent_strategy=intent_strategy,
        specific_variant_key="market_focus_display_variant",
    )
    return _render_display_fields(
        list(display_variant["fields"]),
        value_map,
    )


def _format_market_focus_state(market_state: str) -> str:
    """Map internal market-state keys to readable Chinese display text."""
    display_map = {
        "breadth expansion": "广度扩散",
        "leader continuation": "龙头延续",
        "divergence risk rising": "分歧风险升高",
        "mixed rotation": "混合轮动",
        "quiet rotation": "安静轮动",
    }
    return display_map.get(str(market_state).strip(), str(market_state).strip() or "n/a")


def _get_sector_average_pct_chg(market_frame: pd.DataFrame, sector: str) -> float:
    """Return the average percentage change for one sector in the current frame."""
    if not sector or sector == "n/a" or market_frame.empty:
        return 0.0
    sector_frame = market_frame[market_frame["sector"] == sector]
    if sector_frame.empty:
        return 0.0
    return float(pd.to_numeric(sector_frame["pct_chg"], errors="coerce").fillna(0.0).mean())


def _classify_market_focus_state(
    *,
    strongest_avg: float,
    secondary_avg: float,
    red_count: int,
    high_value_count: int,
) -> str:
    """Classify whether the current market focus looks concentrated, expanding, or diverging."""
    strongest_gap = strongest_avg - secondary_avg
    for rule in MARKET_FOCUS_STATE_RULES:
        if red_count < int(rule["minimum_red_count"]):
            continue
        if strongest_avg < float(rule["minimum_strongest_avg"]):
            continue
        if secondary_avg < float(rule["minimum_secondary_avg"]):
            continue
        if high_value_count < int(rule["minimum_high_value_count"]):
            continue
        if strongest_gap < float(rule["minimum_strongest_gap"]):
            continue
        return str(rule["state"])
    return "quiet rotation"


def _build_market_focus_observation(
    *,
    market_state: str,
    strongest_sector: str,
    secondary_sector: str,
) -> str:
    """Build one short business-facing observation from the market state."""
    templates = MARKET_FOCUS_OBSERVATION_TEMPLATES.get(market_state, {})
    strongest_is_material_chain = strongest_sector in {
        *MATERIAL_RELATED_SECTORS,
        "Materials",
        "Gas",
    }
    secondary_is_material_chain = secondary_sector in {
        *MATERIAL_RELATED_SECTORS,
        "Materials",
        "Gas",
    }
    strongest_is_equipment = strongest_sector in {
        SEMICONDUCTOR_EQUIPMENT_SECTOR,
        "Equipment",
    }
    secondary_is_equipment = secondary_sector in {
        SEMICONDUCTOR_EQUIPMENT_SECTOR,
        "Equipment",
    }

    if market_state == "breadth expansion":
        if strongest_is_material_chain and secondary_is_material_chain:
            return templates.get(
                "material_chain_internal",
                "expansion is forming inside the materials-gas chain.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        if strongest_is_material_chain and secondary_is_equipment:
            return templates.get(
                "material_chain_to_equipment",
                "strength is centered on the materials-gas chain, and expansion into equipment is starting to show.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        if strongest_is_equipment and secondary_is_material_chain:
            return templates.get(
                "equipment_to_material_chain",
                "equipment is leading first, and follow-through into the materials-gas chain is starting to appear.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        return templates.get(
            "default",
            "leadership is expanding from {strongest_sector} toward {secondary_sector}.",
        ).format(
            strongest_sector=strongest_sector,
            secondary_sector=secondary_sector,
        )
    if market_state == "leader continuation":
        if strongest_is_material_chain:
            return templates.get(
                "material_chain",
                "strength is still concentrated in the materials-gas chain; expansion into equipment is not confirmed yet.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        if strongest_is_equipment:
            return templates.get(
                "equipment",
                "equipment is carrying the move on its own; broader follow-through across the chain is not confirmed yet.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        return templates.get(
            "default",
            "strength is still concentrated in {strongest_sector}; broader expansion is not confirmed yet.",
        ).format(
            strongest_sector=strongest_sector,
            secondary_sector=secondary_sector,
        )
    if market_state == "divergence risk rising":
        return templates.get(
            "default",
            "risk is rising and the current main line may be diverging; confirm whether {strongest_sector} can still hold leadership.",
        ).format(
            strongest_sector=strongest_sector,
            secondary_sector=secondary_sector,
        )
    if market_state == "mixed rotation":
        if (
            strongest_is_material_chain and secondary_is_equipment
        ) or (
            strongest_is_equipment and secondary_is_material_chain
        ):
            return templates.get(
                "material_chain_vs_equipment",
                "rotation is active between the materials-gas chain and equipment, but a clean lead direction is not fully established yet.",
            ).format(
                strongest_sector=strongest_sector,
                secondary_sector=secondary_sector,
            )
        return templates.get(
            "default",
            "rotation is active, but leadership is not fully clean between {strongest_sector} and {secondary_sector}.",
        ).format(
            strongest_sector=strongest_sector,
            secondary_sector=secondary_sector,
        )
    quiet_templates = MARKET_FOCUS_OBSERVATION_TEMPLATES.get("quiet rotation", {})
    return quiet_templates.get(
        "default",
        "no clear broadening is visible yet; keep watching {strongest_sector} for confirmation.",
    ).format(
        strongest_sector=strongest_sector,
        secondary_sector=secondary_sector,
    )


def _count_alert_level(alerts: list[dict[str, object]], expected_level: str) -> int:
    """Count alerts by one normalized level label."""
    return sum(
        1
        for alert in alerts
        if _normalize_alert_level(str(alert.get("level", "")).strip())
        == _normalize_alert_level(expected_level)
    )


def _count_high_value_alerts(alerts: list[dict[str, object]]) -> int:
    """Count alerts that belong to the shared high-value alert-type set."""
    return sum(
        1
        for alert in alerts
        if str(alert.get("alert_type", "")).strip() in HIGH_VALUE_ALERT_TYPES
    )


def _normalize_alert_level(level: str) -> str:
    """Normalize alert levels across readable and legacy-encoded variants."""
    normalized_level = str(level).strip()
    level_aliases = {
        "red": "red",
        "orange": "orange",
        "yellow": "yellow",
        "gray": "gray",
        "缁俱垼澹?": "red",
        "濮楁瑨澹?": "orange",
        "姒涘嫯澹?": "yellow",
        "閻忔媽澹?": "gray",
    }
    return level_aliases.get(normalized_level, normalized_level)


def _build_task_result_summary(
    result: MonitorCycleResult,
    *,
    summary_style: str,
    intent_strategy: dict[str, object] | None = None,
) -> str:
    """Build one concise top-line task result summary from the cycle result."""
    intent_strategy = intent_strategy or {}
    alert_count = len(result.alerts)
    high_value_count = sum(
        1
        for alert in result.alerts
        if str(alert.get("alert_type", "")).strip() in HIGH_VALUE_ALERT_TYPES
    )
    red_count = sum(
        1 for alert in result.alerts if _normalize_alert_level(str(alert.get("level", "")).strip()) == "red"
    )
    orange_count = sum(
        1 for alert in result.alerts if _normalize_alert_level(str(alert.get("level", "")).strip()) == "orange"
    )
    counts = {
        "red_count": red_count,
        "alert_count": alert_count,
        "orange_count": orange_count,
        "high_value_count": high_value_count,
    }
    effective_style = (
        summary_style
        if summary_style in TASK_RESULT_SUMMARY_DECISION_RULES
        else "full_monitor"
    )
    case_key = _resolve_task_result_summary_case(effective_style, counts)
    if not case_key:
        return ""
    summary_text = _render_task_result_summary_template(
        effective_style,
        case_key,
        **counts,
    )
    stock_pool_suffix = _build_result_stock_pool_suffix(result)
    stage_summary_suffix = _build_result_stage_focus_suffix(
        intent_strategy,
        market_rows=result.market_rows,
        alerts=result.alerts,
    )
    suffixes = [suffix for suffix in (stock_pool_suffix, stage_summary_suffix) if suffix]
    if suffixes:
        return " ".join([summary_text, *suffixes])
    return summary_text


def _build_result_stock_pool_suffix(result: MonitorCycleResult) -> str:
    """Build one compact stock-pool drift suffix for the top-line result."""
    comparison_labels = [
        str(label).strip()
        for label in (result.stock_pool_comparison_tag_labels or [])
        if str(label).strip()
    ]
    if any(
        label in {"Awaiting baseline", "\u7b49\u5f85\u9996\u4e2a\u57fa\u7ebf"}
        for label in comparison_labels
    ):
        return "Pool drift: awaiting first baseline."
    if comparison_labels == ["Structure Stable"] or comparison_labels == [
        "\u7ed3\u6784\u7a33\u5b9a"
    ]:
        return "Pool drift: stable vs baseline."

    highlight_summary = str(result.stock_pool_comparison_highlight_summary).strip()
    if highlight_summary:
        return f"Pool drift: {highlight_summary}"

    structure_summary = str(result.stock_pool_structure_summary).strip()
    if structure_summary:
        return f"Pool structure: {structure_summary}"
    return ""


def _resolve_task_result_summary_case(
    summary_style: str,
    counts: dict[str, int],
) -> str:
    """Resolve the first matching configured summary case for one task style."""
    for rule in TASK_RESULT_SUMMARY_DECISION_RULES.get(summary_style, []):
        if _task_result_summary_rule_matches(rule, counts):
            return str(rule.get("case", "")).strip()
    return ""


def _build_result_stage_focus_suffix(
    intent_strategy: dict[str, object],
    *,
    market_rows: list[dict[str, object]],
    alerts: list[dict[str, object]],
) -> str:
    """Build one compact stage-aligned chain suffix for the top-line result."""
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    if not preferred_chain_groups:
        return ""

    live_strength_by_chain_group = _build_stage_chain_group_strength_map(market_rows)
    ranked_chain_groups = _rank_stage_chain_groups(
        preferred_chain_groups,
        chain_group_counts={},
        live_strength_by_chain_group=live_strength_by_chain_group,
    )
    if not ranked_chain_groups:
        return ""

    strongest_chain_group = ranked_chain_groups[0]
    strongest_chain_strength = live_strength_by_chain_group.get(strongest_chain_group)
    if strongest_chain_strength is None:
        return ""

    matching_alert_types = _collect_matching_high_value_alert_types(
        strongest_chain_group,
        alerts=alerts,
    )
    if matching_alert_types:
        return (
            f"Aligned chain: {strongest_chain_group} {strongest_chain_strength:.2f}%, "
            f"confirmed by {join_report_items(matching_alert_types, default='n/a')}."
        )
    return f"Aligned chain: {strongest_chain_group} {strongest_chain_strength:.2f}%."


def _format_alert_block(
    alert: dict[str, object],
    *,
    intent_strategy: dict[str, object] | None = None,
    market_rows: list[dict[str, object]] | None = None,
) -> str:
    """Render alert details as a console block."""
    intent_strategy = intent_strategy or {}
    stage_alignment_line = _build_alert_stage_alignment_line(
        alert,
        intent_strategy=intent_strategy,
        market_rows=market_rows or [],
    )
    priority_label = _build_detailed_alert_priority_label(alert)
    display_variant = _resolve_detailed_alert_display_variant(intent_strategy)
    lines = [
        str(display_variant["title_template"]).format(
            level=alert.get("level", "info"),
            priority_label=priority_label,
        )
    ]
    field_value_map = {
        "timestamp": alert.get("timestamp", "intraday"),
        "direction": alert.get("direction", "n/a"),
        "related_stocks": alert.get("related_stocks", "n/a"),
        "message": alert.get("message", "n/a"),
        "trend_state": alert.get("trend_state", "watch"),
        "focus": alert.get("focus", "continue tracking"),
        "stage_alignment": stage_alignment_line,
    }
    for field in _resolve_detailed_alert_field_specs(
        alert,
        intent_strategy=intent_strategy,
    ):
        field_key = str(field.get("key", "")).strip()
        if not field_key:
            continue
        raw_value = str(field_value_map.get(field_key, field.get("default", ""))).strip()
        if not raw_value:
            continue
        field_label = str(field.get("label", "")).strip()
        if field_label:
            lines.append(_format_label_value(field_label, raw_value))
        else:
            lines.append(raw_value)
    return "\n".join(lines)


def _resolve_detailed_alert_field_specs(
    alert: dict[str, object],
    *,
    intent_strategy: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Resolve the configured field set for one detailed alert block."""
    display_variant = _resolve_display_variant(
        DETAILED_ALERT_DISPLAY,
        intent_strategy=intent_strategy,
        specific_variant_key="detailed_alert_style_variant",
    )
    configured_field_sets = dict(display_variant.get("field_sets", {}))
    if not configured_field_sets:
        return list(DETAILED_ALERT_DISPLAY["fields"])

    priority_key = (
        "high_value"
        if str(alert.get("alert_type", "")).strip() in HIGH_VALUE_ALERT_TYPES
        else "watch"
    )
    selected_field_specs = list(configured_field_sets.get(priority_key, []))
    if selected_field_specs:
        return selected_field_specs
    return list(DETAILED_ALERT_DISPLAY["fields"])


def _resolve_detailed_alert_display_variant(
    intent_strategy: dict[str, object] | None = None,
) -> dict[str, object]:
    """Resolve one detailed-alert display variant from the task intent strategy."""
    return _resolve_display_variant(
        DETAILED_ALERT_DISPLAY,
        intent_strategy=intent_strategy,
        specific_variant_key="detailed_alert_style_variant",
    )


def _resolve_display_variant(
    display_config: dict[str, object],
    *,
    intent_strategy: dict[str, object] | None = None,
    specific_variant_key: str,
) -> dict[str, object]:
    """Resolve one shared display variant with optional task-specific override."""
    intent_strategy = intent_strategy or {}
    configured_variants = dict(display_config.get("style_variants", {}))
    variant_key = str(intent_strategy.get(specific_variant_key, "")).strip() or str(
        intent_strategy.get("display_variant", "")
    ).strip()
    selected_variant = dict(configured_variants.get(variant_key, {}))
    if not selected_variant:
        return {
            config_key: config_value
            for config_key, config_value in dict(display_config).items()
            if config_key != "style_variants"
        }

    resolved_variant = {
        config_key: config_value
        for config_key, config_value in dict(display_config).items()
        if config_key != "style_variants"
    }
    resolved_variant.update(selected_variant)
    return resolved_variant


def _sort_alerts_for_detailed_view(
    alerts: list[dict[str, object]],
    *,
    intent_strategy: dict[str, object],
) -> list[dict[str, object]]:
    """Sort detailed alerts so high-value and stage-relevant items surface first."""
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    return sorted(
        alerts,
        key=lambda alert: (
            int(
                any(
                    _alert_matches_chain_group(alert, chain_group)
                    for chain_group in preferred_chain_groups
                )
            ),
            int(str(alert.get("alert_type", "")).strip() in HIGH_VALUE_ALERT_TYPES),
            int(_normalize_alert_level(str(alert.get("level", "")).strip()) == "red"),
            int(_normalize_alert_level(str(alert.get("level", "")).strip()) == "orange"),
            str(alert.get("alert_type", "")).strip(),
        ),
        reverse=True,
    )


def _build_detailed_alert_priority_label(alert: dict[str, object]) -> str:
    """Build a short business-facing priority label for one detailed alert."""
    priority_labels = dict(DETAILED_ALERT_DISPLAY.get("priority_labels", {}))
    alert_type = str(alert.get("alert_type", "")).strip()
    if alert_type in HIGH_VALUE_ALERT_TYPES:
        return str(priority_labels.get("high_value", "High-Value"))
    return str(priority_labels.get("watch", "Watch"))


def _build_alert_stage_alignment_line(
    alert: dict[str, object],
    *,
    intent_strategy: dict[str, object],
    market_rows: list[dict[str, object]],
) -> str:
    """Build one short stage-alignment line for a detailed alert block."""
    preferred_chain_groups = [
        str(chain_group).strip()
        for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
        if str(chain_group).strip()
    ]
    if not preferred_chain_groups:
        return ""

    live_strength_by_chain_group = _build_stage_chain_group_strength_map(market_rows)
    ranked_chain_groups = _rank_stage_chain_groups(
        preferred_chain_groups,
        chain_group_counts={},
        live_strength_by_chain_group=live_strength_by_chain_group,
    )
    matched_chain_groups = [
        chain_group
        for chain_group in ranked_chain_groups
        if _alert_matches_chain_group(alert, chain_group)
    ]
    if matched_chain_groups:
        strongest_match = matched_chain_groups[0]
        strongest_strength = live_strength_by_chain_group.get(strongest_match)
        if strongest_strength is not None:
            return STAGE_ALIGNMENT_TEMPLATES["aligned_with_strength"].format(
                chain_group=strongest_match,
                strength=strongest_strength,
            )
        return STAGE_ALIGNMENT_TEMPLATES["aligned_without_strength"].format(
            chain_group=strongest_match,
        )

    return STAGE_ALIGNMENT_TEMPLATES["not_aligned"].format(
        preferred_chain_groups=join_report_items(ranked_chain_groups, default="n/a"),
    )


def _render_display_fields(
    field_specs: list[dict[str, object]],
    value_map: dict[str, str],
) -> str:
    """Render one ordered labeled field block from shared display metadata."""
    lines: list[str] = []
    for field in field_specs:
        if not bool(field.get("enabled", True)):
            continue
        field_key = str(field.get("key", "")).strip()
        if not field_key:
            continue
        raw_value = str(value_map.get(field_key, field.get("default", ""))).strip()
        if not raw_value:
            continue
        field_label = str(field.get("label", "")).strip()
        if field_label:
            lines.append(_format_label_value(field_label, raw_value))
        else:
            lines.append(raw_value)
    return "\n".join(lines)


def _format_label_value(label: str, value: str) -> str:
    """Render Chinese labels without an extra space after the separator."""
    if any("\u4e00" <= character <= "\u9fff" for character in label):
        return f"{label}：{value}"
    return f"{label}: {value}"


def _task_result_summary_rule_matches(
    rule: dict[str, int | str],
    counts: dict[str, int],
) -> bool:
    """Return whether one configured summary rule matches current alert counts."""
    minimum_thresholds = (
        ("minimum_red_count", "red_count"),
        ("minimum_alert_count", "alert_count"),
        ("minimum_orange_count", "orange_count"),
        ("minimum_high_value_count", "high_value_count"),
    )
    for minimum_key, count_key in minimum_thresholds:
        if minimum_key not in rule:
            continue
        if counts[count_key] < int(rule[minimum_key]):
            return False
    return True


def _render_task_result_summary_template(
    summary_style: str,
    case_key: str,
    **template_values: int,
) -> str:
    """Render one configured task result-summary template."""
    style_rules = TASK_RESULT_SUMMARY_RULES.get(summary_style, {})
    template = str(style_rules.get(case_key, "")).strip()
    if not template:
        return ""
    return template.format(**template_values)
