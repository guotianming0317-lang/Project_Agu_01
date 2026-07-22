"""Alert rule evaluation for market and news signals."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.sectors import HIGH_VALUE_ALERT_TYPES, MATERIAL_CHAIN_LABEL, is_material_related_sector


def evaluate_alerts(
    market_rows: list[dict[str, Any]],
    news_event: dict[str, Any] | None = None,
    *,
    stock_pool_summary: dict[str, Any] | None = None,
    stock_pool_comparison: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate market rows and optional news input for phase-one alerts."""
    alerts: list[dict[str, Any]] = []

    if market_rows:
        alerts.extend(_evaluate_market_alerts(market_rows))

    if news_event:
        news_alert = _evaluate_news_alert(news_event)
        if news_alert is not None:
            alerts.append(news_alert)

    return [
        _attach_stock_pool_context(
            alert,
            stock_pool_summary=stock_pool_summary,
            stock_pool_comparison=stock_pool_comparison,
        )
        for alert in alerts
    ]


def _evaluate_market_alerts(market_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Evaluate quote-driven alerts."""
    alerts: list[dict[str, Any]] = []
    sector_winners: dict[str, list[dict[str, Any]]] = defaultdict(list)
    materials_winners: list[dict[str, Any]] = []

    for row in market_rows:
        pct_chg = _to_float(row.get("pct_chg"))
        volume_ratio = _to_float(row.get("volume_ratio"))
        priority = int(row.get("priority", 99))
        sector = str(row.get("sector", ""))
        code = str(row.get("code", ""))
        name = str(row.get("name", ""))

        if priority == 1 and pct_chg > 8.0:
            alerts.append(
                {
                    "alert_type": "price_spike",
                    "level": "橙色",
                    "timestamp": "盘中",
                    "direction": sector,
                    "related_stocks": name,
                    "message": f"{name} 单日涨幅达到 {pct_chg:.1f}%",
                    "trend_state": "强趋势",
                    "focus": f"观察 {code} 是否继续放量领涨",
                }
            )

        if priority == 1 and volume_ratio > 2.0 and pct_chg > 5.0:
            alerts.append(
                {
                    "alert_type": "volume_spike",
                    "level": "橙色",
                    "timestamp": "盘中",
                    "direction": sector,
                    "related_stocks": name,
                    "message": f"{name} 量比 {volume_ratio:.1f} 且涨幅 {pct_chg:.1f}%",
                    "trend_state": "放量异动",
                    "focus": f"确认 {code} 是否获得板块跟随",
                }
            )

        if pct_chg > 5.0:
            sector_winners[sector].append(row)
            if is_material_related_sector(sector):
                materials_winners.append(row)

    for sector, winners in sector_winners.items():
        if len(winners) >= 3:
            alerts.append(
                {
                    "alert_type": "sector_move",
                    "level": "橙色",
                    "timestamp": "盘中",
                    "direction": sector,
                    "related_stocks": ", ".join(str(item.get("name", "")) for item in winners[:3]),
                    "message": f"{sector} 中至少 3 只股票涨幅超过 5%",
                    "trend_state": "板块异动",
                    "focus": f"观察 {sector} 是否扩散成市场主线",
                }
            )

    if len(materials_winners) >= 3:
        alerts.append(
            {
                "alert_type": "materials_focus",
                "level": "橙色",
                "timestamp": "盘中",
                "direction": MATERIAL_CHAIN_LABEL,
                "related_stocks": ", ".join(
                    str(item.get("name", "")) for item in materials_winners[:3]
                ),
                "message": f"{MATERIAL_CHAIN_LABEL}链至少 3 只股票涨幅超过 5%",
                "trend_state": "材料线强化",
                "focus": "观察材料与气体方向是否持续强于设备和算力方向",
            }
        )

    return alerts


def _evaluate_news_alert(news_event: dict[str, Any]) -> dict[str, Any] | None:
    """Evaluate a news-driven alert."""
    level = str(news_event.get("level", "")).upper()
    if level != "S":
        return None

    return {
        "alert_type": "news_flash",
        "level": "红色",
        "timestamp": "新闻",
        "direction": str(news_event.get("related_sector", "待确认")),
        "related_stocks": str(news_event.get("related_stocks", "")),
        "message": str(news_event.get("title", "S级新闻预警")),
        "trend_state": "消息冲击",
        "focus": "立即确认消息真实性及板块扩散范围",
    }


def _attach_stock_pool_context(
    alert: dict[str, Any],
    *,
    stock_pool_summary: dict[str, Any] | None,
    stock_pool_comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    """Attach reusable stock-pool context to high-value alerts only."""
    if str(alert.get("alert_type", "")).strip() not in HIGH_VALUE_ALERT_TYPES:
        return alert
    if not stock_pool_summary and not stock_pool_comparison:
        return alert

    alert_with_context = dict(alert)
    summary = stock_pool_summary or {}
    comparison = stock_pool_comparison or {}
    alert_with_context["stock_pool_structure_summary"] = str(
        summary.get("structure_summary", "")
    ).strip()
    alert_with_context["stock_pool_comparison_tag_groups"] = list(
        comparison.get("comparison_tag_groups", [])
    )
    alert_with_context["stock_pool_comparison_highlight_summary"] = str(
        comparison.get("highlight_summary", "")
    ).strip()
    alert_with_context["stock_pool_health_hints"] = list(
        summary.get("health_hints", [])
    )
    return alert_with_context


def _to_float(value: Any) -> float:
    """Convert raw numeric-like values into floats."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
