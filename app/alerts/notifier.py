"""Notification helpers for console-based phase one alerts."""

from __future__ import annotations

from typing import Any
import os
import json
from urllib.request import Request, urlopen

from app.reports.shared import build_stock_pool_observation_lines
from app.sectors import ALERT_TYPE_PRIORITY, is_high_value_alert_type

CHAIN_GROUP_ALIASES: dict[str, tuple[str, ...]] = {
    "材料": ("材料", "半导体材料", "材料气体"),
    "气体": ("气体", "半导体气体", "材料气体"),
    "设备": ("设备", "半导体设备"),
    "光模块": ("光模块", "CPO"),
    "服务器": ("服务器", "算力"),
    "存储": ("存储", "HBM"),
    "封测": ("封测", "Chiplet"),
}

ALERT_LEVEL_PRIORITY = {"高优先级": 3, "中优先级": 2, "低优先级": 1, "观察级": 0}


def build_notification_channel_status() -> dict[str, str]:
    """Build a compact status summary for optional push notification channels."""
    webhook_url = str(
        os.environ.get("MONITOR_FEISHU_WEBHOOK_URL", "")
        or os.environ.get("MONITOR_WEBHOOK_URL", "")
    ).strip()
    channel_name = str(os.environ.get("MONITOR_NOTIFICATION_CHANNEL", "")).strip()
    if webhook_url:
        return {
            "status": "webhook-ready",
            "channel": channel_name or "feishu",
            "reason": "Webhook URL is configured.",
            "next_step": "send a test digest before enabling scheduled push",
        }
    return {
        "status": "console-only",
        "channel": "console",
        "reason": "No webhook URL configured; notifications stay local.",
        "next_step": "set MONITOR_WEBHOOK_URL when push delivery is needed",
    }


def notify_feishu_text(
    text: str,
    *,
    webhook_url: str | None = None,
    timeout: float = 10.0,
) -> dict[str, str]:
    """Send one text message to a Feishu bot without breaking the main flow."""
    resolved_url = str(
        webhook_url
        or os.environ.get("MONITOR_FEISHU_WEBHOOK_URL", "")
        or os.environ.get("MONITOR_WEBHOOK_URL", "")
    ).strip()
    if not resolved_url:
        return {"status": "not-configured", "reason": "Feishu webhook is not configured."}
    message = str(text or "").strip()
    if not message:
        return {"status": "skipped", "reason": "Empty notification text."}
    payload = json.dumps(
        {"msg_type": "text", "content": {"text": message[:3800]}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        resolved_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "ProjectAgu01/1.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured webhook
            response_text = response.read().decode("utf-8", errors="replace")
        response_payload = json.loads(response_text or "{}")
        if response_payload.get("code", 0) not in (0, "0", None):
            return {"status": "failed", "reason": str(response_payload)}
        return {"status": "sent", "reason": "Feishu message delivered."}
    except Exception as exc:  # noqa: BLE001 - notification must not stop monitoring
        return {"status": "failed", "reason": str(exc)}


def notify_feishu_card(
    markdown: str,
    *,
    title: str = "Project Agu 01 每日优先摘要",
    webhook_url: str | None = None,
    timeout: float = 10.0,
) -> dict[str, str]:
    """Send a colored Feishu interactive card."""
    resolved_url = str(
        webhook_url
        or os.environ.get("MONITOR_FEISHU_WEBHOOK_URL", "")
        or os.environ.get("MONITOR_WEBHOOK_URL", "")
    ).strip()
    if not resolved_url:
        return {"status": "not-configured", "reason": "Feishu webhook is not configured."}
    payload = json.dumps(
        {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": [{"tag": "markdown", "content": str(markdown)[:3800]}],
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        resolved_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "ProjectAgu01/1.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured webhook
            response_payload = json.loads(response.read().decode("utf-8", errors="replace") or "{}")
        if response_payload.get("code", 0) not in (0, "0", None):
            return {"status": "failed", "reason": str(response_payload)}
        return {"status": "sent", "reason": "Feishu card delivered."}
    except Exception as exc:  # noqa: BLE001 - notification must not stop monitoring
        return {"status": "failed", "reason": str(exc)}


def format_alert_message(alert: dict[str, Any]) -> str:
    """Format an alert payload into a human-readable console block."""
    lines = _build_alert_message_lines(alert)
    return "\n".join(lines)


def notify_console(alert: dict[str, Any]) -> None:
    """Print a formatted alert payload to the console."""
    print(format_alert_message(alert))


def select_alerts_for_digest(
    alerts: list[dict[str, Any]],
    *,
    stage: str,
    digest_strategy: dict[str, object] | None = None,
) -> list[dict[str, Any]]:
    """Select the most useful alerts for one notification digest stage."""
    normalized_stage = str(stage).strip().lower()
    digest_strategy = dict(digest_strategy or {})
    sorted_alerts = sorted(
        alerts,
        key=lambda alert: _digest_sort_key(
            alert,
            preferred_alert_types=list(digest_strategy.get("preferred_alert_types", [])),
            preferred_chain_groups=list(
                digest_strategy.get("preferred_chain_groups", [])
            ),
        ),
        reverse=True,
    )
    max_items = int(digest_strategy.get("max_items", 0) or 0)
    if max_items <= 0:
        max_items = (
            3 if normalized_stage == "intraday" else 5 if normalized_stage == "close" else 3
        )

    if digest_strategy.get("high_value_only", False):
        filtered_alerts = [alert for alert in sorted_alerts if _is_high_value_alert(alert)]
        return filtered_alerts[:max_items]

    preferred_types = {
        str(alert_type).strip()
        for alert_type in list(digest_strategy.get("preferred_alert_types", []))
        if str(alert_type).strip()
    }
    if preferred_types:
        preferred_alerts = [
            alert
            for alert in sorted_alerts
            if str(alert.get("alert_type", "")).strip() in preferred_types
        ]
        other_alerts = [
            alert
            for alert in sorted_alerts
            if str(alert.get("alert_type", "")).strip() not in preferred_types
        ]
        return (preferred_alerts + other_alerts)[:max_items]

    if normalized_stage == "intraday":
        high_value = [alert for alert in sorted_alerts if _is_high_value_alert(alert)]
        if high_value:
            return high_value[:max_items]
        return sorted_alerts[: min(max_items, 2)]
    if normalized_stage == "close":
        high_value = [alert for alert in sorted_alerts if _is_high_value_alert(alert)]
        other_alerts = [alert for alert in sorted_alerts if not _is_high_value_alert(alert)]
        return (high_value[:max_items] + other_alerts[:2])[:max_items]
    return sorted_alerts[:max_items]


def build_alert_digest_text(
    alerts: list[dict[str, Any]],
    *,
    stage: str,
    digest_strategy: dict[str, object] | None = None,
) -> str:
    """Build one compact digest text from selected alerts."""
    selected_alerts = select_alerts_for_digest(
        alerts,
        stage=stage,
        digest_strategy=digest_strategy,
    )
    if not selected_alerts:
        return ""

    normalized_stage = str(stage).strip().lower()
    title = "Intraday Alert Digest" if normalized_stage == "intraday" else "Close Alert Digest"
    lines = [title]
    for alert in selected_alerts:
        lines.append(_build_digest_line(alert))
    return "\n".join(lines)


def _build_alert_message_lines(alert: dict[str, Any]) -> list[str]:
    """Build reusable console notification lines for one alert payload."""
    level = str(alert.get("level", "观察级"))
    timestamp = str(alert.get("timestamp", "n/a"))
    direction = str(alert.get("direction", "n/a"))
    related_stocks = str(alert.get("related_stocks", "n/a"))
    message = str(alert.get("message", "n/a"))
    trend_state = str(alert.get("trend_state", "n/a"))
    focus = str(alert.get("focus", "n/a"))
    lines = [
        f"[{level}] Alert",
        f"Time: {timestamp}",
        f"Direction: {direction}",
        f"Related stocks: {related_stocks}",
        f"Reason: {message}",
        f"Trend: {trend_state}",
        f"Focus: {focus}",
    ]
    stock_pool_observation_lines = build_stock_pool_observation_lines(
        structure_summary=str(alert.get("stock_pool_structure_summary", "")).strip(),
        comparison_tag_groups=list(alert.get("stock_pool_comparison_tag_groups", [])),
        highlight_summary=str(
            alert.get("stock_pool_comparison_highlight_summary", "")
        ).strip(),
        health_hints=list(alert.get("stock_pool_health_hints", [])),
        empty_text="",
    )
    stock_pool_observation_lines = [
        line for line in stock_pool_observation_lines if line.strip()
    ]
    if stock_pool_observation_lines:
        lines.append("Stock pool observation:")
        lines.extend(f"- {line}" for line in stock_pool_observation_lines)
    return lines


def _build_digest_line(alert: dict[str, Any]) -> str:
    """Build one single-line digest entry for one selected alert."""
    level = str(alert.get("level", "观察级")).strip()
    direction = str(alert.get("direction", "n/a")).strip()
    message = str(alert.get("message", "n/a")).strip()
    highlight_summary = str(
        alert.get("stock_pool_comparison_highlight_summary", "")
    ).strip()
    comparison_groups = [
        str(group.get("summary", "")).strip()
        for group in list(alert.get("stock_pool_comparison_tag_groups", []))
        if isinstance(group, dict) and str(group.get("summary", "")).strip()
    ]
    if highlight_summary:
        return f"- [{level}] {direction}: {message} | {highlight_summary}"
    if comparison_groups:
        return f"- [{level}] {direction}: {message} | {comparison_groups[0]}"
    return f"- [{level}] {direction}: {message}"


def _is_high_value_alert(alert: dict[str, Any]) -> bool:
    """Return whether one alert should be prioritized in digest selection."""
    return is_high_value_alert_type(str(alert.get("alert_type", "")).strip())


def _digest_sort_key(
    alert: dict[str, Any],
    *,
    preferred_alert_types: list[str] | None = None,
    preferred_chain_groups: list[str] | None = None,
) -> tuple[int, int, int, int, int, str]:
    """Sort alerts by business value before digest truncation."""
    preferred_alert_types = preferred_alert_types or []
    preferred_chain_groups = preferred_chain_groups or []
    alert_type = str(alert.get("alert_type", "")).strip()
    return (
        int(_alert_matches_any_chain_group(alert, preferred_chain_groups)),
        int(alert_type in preferred_alert_types),
        int(_is_high_value_alert(alert)),
        ALERT_LEVEL_PRIORITY.get(str(alert.get("level", "")).strip(), 0),
        ALERT_TYPE_PRIORITY.get(alert_type, 0),
        alert_type,
    )


def _alert_matches_any_chain_group(
    alert: dict[str, Any],
    preferred_chain_groups: list[str],
) -> bool:
    """Return whether one alert text aligns with any preferred chain group."""
    alert_text = " ".join(
        [
            str(alert.get("direction", "")).strip(),
            str(alert.get("message", "")).strip(),
            str(alert.get("focus", "")).strip(),
        ]
    )
    if not alert_text:
        return False

    for chain_group in preferred_chain_groups:
        normalized_chain_group = str(chain_group).strip()
        if not normalized_chain_group:
            continue
        aliases = CHAIN_GROUP_ALIASES.get(
            normalized_chain_group,
            (normalized_chain_group,),
        )
        if any(alias and alias in alert_text for alias in aliases):
            return True
    return False
