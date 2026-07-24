"""Replaceable presentation metadata for the local dashboard."""

from __future__ import annotations


def build_theme_spec() -> dict[str, str]:
    """Return replaceable theme metadata for page-level presentation."""
    return {
        "page_title": "AI Semiconductor Monitor",
        "app_title": "AI Semiconductor Monitor",
        "layout": "wide",
        "panel_density": "comfortable",
        "view_selector_label": "Dashboard View",
        "time_phase_selector_label": "Time Phase",
        "time_phase_auto_label": "Auto",
        "batch_selector_label": "Snapshot Batch",
        "caption_template": "Database: {database_url}",
    }


def build_summary_panel_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable card-wrapper metadata for grouped summary panels."""
    intro_spec = build_intro_panel_style_spec(copy_variant)
    base_spec = {
        "summary_label": "summary",
        "details_label": "details",
        "health_label": "health",
        "status_label": "status",
        "readiness_label": "readiness",
        "empty_state_label": "empty state",
        "chart_label": str(intro_spec.get("chart_intro_label", "chart")),
        "axes_label": "axes",
        "x_axis_prefix": "X",
        "y_axis_prefix": "Y",
        "supporting_copy": "Metrics first, details below",
        "compact_supporting_copy": "Metrics + details",
        "health_supporting_copy": "Status first, health details below",
        "health_supporting_copy_clean": "Pool is structurally ready for monitoring.",
        "health_supporting_copy_warning": "Review drift signals before relying on the pool.",
        "health_supporting_copy_blocking": "Fix blocking stock-pool issues before monitoring.",
        "readiness_supporting_copy_clean": "No action needed before the next monitor cycle.",
        "readiness_supporting_copy_warning": "A quick validation review is recommended now.",
        "readiness_supporting_copy_blocking": "Resolve blocking issues before using this pool.",
        "chart_supporting_copy": str(
            intro_spec.get("chart_supporting_copy", "Data table and chart follow")
        ),
        "compact_chart_supporting_copy": str(
            intro_spec.get("compact_chart_supporting_copy", "Chart + data table")
        ),
        "empty_state_supporting_copy": "No data available yet",
        "default_tone": "neutral",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "summary_label": "\u6458\u8981",
            "details_label": "\u660e\u7ec6",
            "health_label": "\u5065\u5eb7",
            "status_label": "\u72b6\u6001",
            "readiness_label": "\u5c31\u7eea\u5ea6",
            "empty_state_label": "\u6682\u65e0\u5185\u5bb9",
            "axes_label": "\u5750\u6807",
            "x_axis_prefix": "\u6a2a\u8f74",
            "y_axis_prefix": "\u7eb5\u8f74",
            "supporting_copy": "\u5148\u770b\u6307\u6807\uff0c\u518d\u770b\u660e\u7ec6",
            "compact_supporting_copy": "\u6307\u6807 + \u660e\u7ec6",
            "health_supporting_copy": "\u5148\u770b\u72b6\u6001\uff0c\u518d\u770b\u5065\u5eb7\u660e\u7ec6",
            "health_supporting_copy_clean": "\u80a1\u7968\u6c60\u7ed3\u6784\u5df2\u5c31\u7eea\uff0c\u53ef\u76f4\u63a5\u7528\u4e8e\u76d1\u63a7\u3002",
            "health_supporting_copy_warning": "\u5efa\u8bae\u5148\u590d\u6838\u7ed3\u6784\u504f\u79fb\u4fe1\u53f7\uff0c\u518d\u4f9d\u8d56\u5f53\u524d\u76d1\u63a7\u6c60\u3002",
            "health_supporting_copy_blocking": "\u8bf7\u5148\u4fee\u590d\u963b\u65ad\u6027\u80a1\u7968\u6c60\u95ee\u9898\uff0c\u518d\u5f00\u59cb\u76d1\u63a7\u3002",
            "readiness_supporting_copy_clean": "\u4e0b\u4e00\u8f6e\u76d1\u63a7\u524d\u6682\u65f6\u4e0d\u9700\u989d\u5916\u5904\u7406\u3002",
            "readiness_supporting_copy_warning": "\u5f53\u4e0b\u5efa\u8bae\u5148\u505a\u4e00\u6b21\u5feb\u901f\u6821\u9a8c\u590d\u6838\u3002",
            "readiness_supporting_copy_blocking": "\u8bf7\u5148\u89e3\u51b3\u963b\u65ad\u9879\uff0c\u518d\u4f7f\u7528\u8fd9\u4e2a\u76d1\u63a7\u6c60\u3002",
            "compact_chart_supporting_copy": "\u56fe\u8868 + \u6570\u636e\u8868",
            "empty_state_supporting_copy": "\u6682\u65f6\u8fd8\u6ca1\u6709\u53ef\u5c55\u793a\u7684\u6570\u636e",
        }
    )
    return localized_spec


def build_kpi_panel_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable wrapper metadata for the KPI section and KPI cards."""
    base_spec = {
        "section_label": "kpi section",
        "metric_label": "kpi",
        "section_body": "Latest snapshot and alert counters",
        "section_supporting_copy": "Primary monitor snapshot",
        "metric_group_body": "KPI values",
        "compact_section_supporting_copy": "Top-line monitor metrics",
        "metric_supporting_copy": "Primary dashboard counter",
        "default_tone": "neutral",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "section_label": "\u6307\u6807\u533a",
            "metric_label": "\u6307\u6807\u5361",
            "section_body": "\u5f53\u524d\u6279\u6b21\u4e0e\u63d0\u9192\u6982\u89c8",
            "section_supporting_copy": "\u5f53\u524d\u76d1\u63a7\u9876\u5c42\u6982\u89c8",
            "metric_group_body": "\u5173\u952e\u6307\u6807",
            "compact_section_supporting_copy": "\u6838\u5fc3\u76d1\u63a7\u6307\u6807",
            "metric_supporting_copy": "\u9876\u90e8\u5173\u952e\u8ba1\u6570\u5361",
        }
    )
    return localized_spec


def build_control_band_specs(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable copy for the first-screen control band."""
    base_spec = {
        "batch_label": "batch focus",
        "batch_body_template": "Current batch | {selected_batch}",
        "batch_empty_body": "Current batch | Latest available snapshot",
        "batch_supporting_copy": "Use the batch selector above to switch monitor snapshots.",
        "source_label": "data source",
        "source_body_template": "Database | {database_caption}",
        "source_with_quote_body_template": "Database | {database_caption} | Quote source: {quote_source}",
        "source_supporting_copy": "Source path stays visible here so the selected context is easy to confirm.",
        "time_phase_source_label": "Phase source",
        "time_phase_source_auto": "Automatic",
        "time_phase_source_manual": "Manual override",
        "time_phase_source_auto_template": "Phase source: {source_label}",
        "time_phase_source_manual_template": "Phase source: {source_label} | Active mode: {phase_label}",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "batch_label": "\u6279\u6b21\u7126\u70b9",
            "batch_body_template": "\u5f53\u524d\u6279\u6b21 | {selected_batch}",
            "batch_empty_body": "\u5f53\u524d\u6279\u6b21 | \u6700\u65b0\u53ef\u7528\u5feb\u7167",
            "batch_supporting_copy": "\u53ef\u901a\u8fc7\u4e0a\u65b9\u6279\u6b21\u9009\u62e9\u5668\u5207\u6362\u76d1\u63a7\u5feb\u7167\u3002",
            "source_label": "\u6570\u636e\u6765\u6e90",
            "source_body_template": "\u6570\u636e\u5e93 | {database_caption}",
            "source_with_quote_body_template": "\u6570\u636e\u5e93 | {database_caption} | \u884c\u60c5\u6765\u6e90\uff1a{quote_source}",
            "source_supporting_copy": "\u8fd9\u91cc\u4f1a\u4fdd\u6301\u663e\u793a\u5f53\u524d\u6570\u636e\u4e0a\u4e0b\u6587\uff0c\u4fbf\u4e8e\u5feb\u901f\u786e\u8ba4\u3002",
            "time_phase_source_label": "\u65f6\u6bb5\u6765\u6e90",
            "time_phase_source_auto": "\u81ea\u52a8\u5224\u65ad",
            "time_phase_source_manual": "\u624b\u52a8\u8986\u76d6",
            "time_phase_source_auto_template": "\u65f6\u6bb5\u6765\u6e90\uff1a{source_label}",
            "time_phase_source_manual_template": "\u65f6\u6bb5\u6765\u6e90\uff1a{source_label} | \u5f53\u524d\u6a21\u5f0f\uff1a{phase_label}",
        }
    )
    return localized_spec


def build_priority_action_module_copy_specs(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable copy templates for action-summary module mapping lines."""
    base_spec = {
        "step_1_line_template": "Step 1: Open {label}",
        "step_1_location_template": "Step 1 location: {location}",
        "step_1_jump_template": "Step 1 jump: {link}",
        "step_2_line_template": "Step 2: Then review {label}",
        "step_2_location_template": "Step 2 location: {location}",
        "step_2_jump_template": "Step 2 jump: {link}",
        "jump_link_label": "Jump to section",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "step_1_line_template": "第 1 步：先看 {label}",
            "step_1_location_template": "第 1 步位置：{location}",
            "step_1_jump_template": "第 1 步跳转：{link}",
            "step_2_line_template": "第 2 步：再看 {label}",
            "step_2_location_template": "第 2 步位置：{location}",
            "step_2_jump_template": "第 2 步跳转：{link}",
            "jump_link_label": "跳到对应模块",
        }
    )
    return localized_spec


def build_priority_action_focus_copy_specs(copy_variant: str = "default") -> dict[str, object]:
    """Return replaceable copy templates for first-read focus guidance lines."""
    base_spec: dict[str, object] = {
        "hint_line_template": "In the first module, look for: {value}",
        "field_line_template": "First field: {value}",
        "group_line_template": "First group: {value}",
        "conclusion_line_template": "First conclusion: {value}",
        "strip_prefixes": [
            "First field: ",
            "First group: ",
            "First conclusion: ",
        ],
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "hint_line_template": "模块先看：{value}",
            "field_line_template": "首看字段：{value}",
            "group_line_template": "首看分组：{value}",
            "conclusion_line_template": "首看结论：{value}",
            "strip_prefixes": [
                "首看字段：",
                "首看分组：",
                "首看结论：",
                "先看字段：",
                "先看分组：",
                "先看结论：",
            ],
        }
    )
    return localized_spec


def build_priority_action_topline_copy_specs(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable copy templates for top-line context lines."""
    base_spec = {
        "context_line_template": "{prefix}: {value}",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "context_line_template": "{prefix}：{value}",
        }
    )
    return localized_spec


def build_priority_action_phase_copy_specs(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable copy templates for time-phase guidance inside action summary."""
    base_spec = {
        "phase_source_auto_line_template": "Phase source: Automatic",
        "phase_source_manual_line_template": "Phase source: Manual override | Active mode: {label}",
        "phase_line_template": "Current phase: {label}",
        "phase_focus_line_template": "Phase focus: {value}",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "phase_source_auto_line_template": "时段来源：自动判断",
            "phase_source_manual_line_template": "时段来源：手动覆盖 | 当前模式：{label}",
            "phase_line_template": "当前时段：{label}",
            "phase_focus_line_template": "时段重点：{value}",
        }
    )
    return localized_spec


def build_priority_action_phase_override_specs() -> dict[str, dict[str, object]]:
    """Return explicit time-phase override rules for homepage action-summary ordering."""
    return {
        "default": {
            "scenario_sections": {
                "baseline_review": ["strongest_sector", "leader_summary", "next_session_action"],
                "midday_baseline_review": ["strongest_sector", "leader_summary", "stock_pool_health"],
                "stock_pool_drift_review": ["stock_pool_health", "saved_batches", "next_session_action"],
                "daily_priority_review": ["today_priority_summary", "next_session_action", "stock_pool_health"],
                "daily_priority_risk_review": ["today_priority_summary", "latest_alerts", "next_session_action"],
            }
        },
        "compact": {
            "scenario_sections": {
                "alert_scan": ["latest_alerts", "next_session_action", "stock_pool_health"],
                "risk_alert_scan": ["latest_alerts", "next_session_action", "stock_pool_health"],
                "intraday_alert_review": ["latest_alerts", "strongest_sector", "next_session_action"],
                "daily_priority_review": ["today_priority_summary", "latest_alerts", "next_session_action"],
                "stock_pool_blocking_review": ["stock_pool_health", "latest_alerts", "next_session_action"],
                "stock_pool_health_review": ["stock_pool_health", "next_session_action", "latest_alerts"],
            }
        },
        "business_cn": {
            "scenario_sections": {
                "batch_review": ["saved_batches", "stock_pool_health", "next_session_action"],
                "close_review": ["saved_batches", "stock_pool_health", "next_session_action"],
                "stock_pool_drift_review": ["stock_pool_health", "saved_batches", "next_session_action"],
                "stock_pool_health_review": ["stock_pool_health", "next_session_action", "latest_alerts"],
                "daily_priority_review": ["today_priority_summary", "stock_pool_health", "next_session_action"],
                "daily_priority_risk_review": ["today_priority_summary", "latest_alerts", "next_session_action"],
            }
        },
    }


def build_priority_action_phase_profile_override_specs(
    copy_variant: str = "default",
) -> dict[str, dict[str, dict[str, str]]]:
    """Return explicit time-phase overrides for action-summary scenario profile copy."""
    base_specs: dict[str, dict[str, dict[str, str]]] = {
        "default": {
            "baseline_review": {
                "focus_points": "strongest sector / leader continuity / next-session action",
                "reading_order": "strongest sector -> leader summary -> next-session action",
                "second_step_note": "Second step: compare the next-session action summary after confirming whether leadership is still aligned with the strongest sector.",
            },
        },
        "compact": {
            "daily_priority_review": {
                "focus_points": "core summary / fresh alerts / first-pass watchlist",
                "reading_order": "today priority summary -> latest alerts -> next-session action",
                "second_step_note": "Second step: after the alert pass, return to the next-session action summary and lock the first-pass watchlist.",
            },
        },
        "business_cn": {
            "batch_review": {
                "focus_points": "快照变化 / 结构确认 / 跟踪候选",
                "reading_order": "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
                "second_step_note": "第二步：先确认结构是否稳定，再回到下一交易时段动作摘要，锁定哪些变化值得继续跟踪。",
            },
            "close_review": {
                "focus_points": "批次回放 / 结构确认 / 延续名单",
                "reading_order": "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
                "second_step_note": "第二步：先确认股票池结构是否稳定，再回到下一交易时段动作摘要，锁定明日延续名单。",
            },
        },
    }
    return base_specs


def build_priority_action_phase_profile_override_specs(
    copy_variant: str = "default",
) -> dict[str, dict[str, dict[str, str]]]:
    """Return explicit time-phase overrides for action-summary scenario profile copy."""
    if copy_variant == "business_cn":
        return {
            "default": {
                "baseline_review": {
                    "focus_points": "最强板块 / 龙头延续 / 下一交易时段动作",
                    "reading_order": "最强板块 -> 龙头摘要 -> 下一交易时段动作摘要",
                    "second_step_note": "第二步：先确认龙头是否仍与最强板块同向延续，再回到下一交易时段动作摘要补全主线判断。",
                },
            },
            "compact": {
                "daily_priority_review": {
                    "focus_points": "核心摘要 / 最新提醒 / 第一轮观察名单",
                    "reading_order": "当日优先摘要 -> 最新提醒 -> 下一交易时段动作摘要",
                    "second_step_note": "第二步：完成提醒核对后，回到下一交易时段动作摘要，锁定第一轮观察名单。",
                },
            },
            "business_cn": {
                "batch_review": {
                    "focus_points": "快照变化 / 结构确认 / 跟踪候选",
                    "reading_order": "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
                    "second_step_note": "第二步：先确认结构是否稳定，再回到下一交易时段动作摘要，锁定哪些变化值得继续跟踪。",
                },
                "close_review": {
                    "focus_points": "批次回放 / 结构确认 / 延续名单",
                    "reading_order": "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
                    "second_step_note": "第二步：先确认股票池结构是否稳定，再回到下一交易时段动作摘要，锁定明日延续名单。",
                },
            },
        }
    return {
        "default": {
            "baseline_review": {
                "focus_points": "strongest sector / leader continuity / next-session action",
                "reading_order": "strongest sector -> leader summary -> next-session action",
                "second_step_note": "Second step: compare the next-session action summary after confirming whether leadership is still aligned with the strongest sector.",
            },
        },
        "compact": {
            "daily_priority_review": {
                "focus_points": "core summary / fresh alerts / first-pass watchlist",
                "reading_order": "today priority summary -> latest alerts -> next-session action",
                "second_step_note": "Second step: after the alert pass, return to the next-session action summary and lock the first-pass watchlist.",
            },
        },
        "business_cn": {
            "batch_review": {
                "focus_points": "snapshot changes / structure confirmation / follow-through candidates",
                "reading_order": "saved batches -> stock-pool health -> next-session action",
                "second_step_note": "Second step: confirm whether structure is stable first, then return to the next-session action summary and lock which changes deserve follow-through.",
            },
            "close_review": {
                "focus_points": "snapshot replay / structure confirmation / continuity names",
                "reading_order": "saved batches -> stock-pool health -> next-session action",
                "second_step_note": "Second step: confirm whether stock-pool structure is stable first, then return to the next-session action summary and lock tomorrow's continuity names.",
            },
        },
    }


def build_priority_action_profile_specs(
    copy_variant: str = "default",
) -> dict[str, dict[str, str]]:
    """Return replaceable per-scenario action-summary copy for the homepage."""
    base_specs = {
        "daily_priority_review": {
            "first_step_note": "First step: read today's priority summary, then confirm the next-session action summary.",
            "scenario": "Daily Priority Review",
            "applicable_session": "Use when today's news-priority summary is ready and should anchor the first read.",
            "objective": "Lock the first reading order from today's saved priority summary before widening to other modules.",
            "focus_points": "core summary / read order / watchlist focus",
            "reading_order": "today priority summary -> next-session action -> stock-pool health",
            "reading_pace": "summary-first",
            "second_step_note": "Second step: review the next-session action summary and stock-pool health to confirm today's execution focus.",
        },
        "daily_priority_risk_review": {
            "first_step_note": "First step: read today's priority summary, then verify the latest risk alerts.",
            "scenario": "Daily Priority Risk Review",
            "applicable_session": "Use when today's priority summary is ready and risk alerts still need immediate confirmation.",
            "objective": "Use today's saved reading order as the anchor, then confirm whether fresh alerts intensify the risk side.",
            "focus_points": "daily priority order / risk alerts / avoid names",
            "reading_order": "today priority summary -> latest alerts -> next-session action",
            "reading_pace": "summary-first risk check",
            "second_step_note": "Second step: return to the next-session action summary and confirm which names should stay core, candidate, or avoided.",
        },
        "stock_pool_blocking_review": {
            "first_step_note": "First step: validate stock-pool health, field mappings, and registry hints before trusting signal conclusions.",
            "scenario": "Stock-pool Blocking Review",
            "applicable_session": "Use when stock-pool health is blocking and signal trust must be rebuilt first.",
            "objective": "Restore trust in pool structure and field mapping before reading signal conclusions.",
            "focus_points": "field validity / registry mapping / blocking items",
            "reading_order": "stock-pool health -> latest alerts -> next-session action",
            "reading_pace": "slow and confirm-first",
            "second_step_note": "Second step: compare the latest alerts and strongest sector before widening the research conclusion.",
        },
        "stock_pool_drift_review": {
            "first_step_note": "First step: review stock-pool drift and saved-batch comparison before expanding signal conclusions.",
            "scenario": "Stock-pool Drift Review",
            "applicable_session": "Use when pool structure has drifted and today's research scope may need recalibration.",
            "objective": "Confirm whether recent pool-structure drift changes today's research scope.",
            "focus_points": "drift tags / saved-batch comparison / research-scope change",
            "reading_order": "stock-pool health -> saved batches -> next-session action",
            "reading_pace": "compare-first",
            "second_step_note": "Second step: compare the latest alerts and strongest sector before widening the research conclusion.",
        },
        "stock_pool_health_review": {
            "first_step_note": "First step: review stock-pool readiness and health hints before expanding to other modules.",
            "scenario": "Stock-pool Health Review",
            "applicable_session": "Use when pool health is not fully clean and validation should stay ahead of expansion.",
            "objective": "Validate readiness and health hints before expanding into broader conclusions.",
            "focus_points": "readiness hints / warning signals / monitor readiness",
            "reading_order": "stock-pool health -> next-session action -> latest alerts",
            "reading_pace": "steady validation",
            "second_step_note": "Second step: compare the latest alerts and strongest sector before widening the research conclusion.",
        },
        "risk_alert_scan": {
            "first_step_note": "First step: scan the latest risk alerts, then compare them with the next-session action summary.",
            "scenario": "Risk Alert Scan",
            "applicable_session": "Use when negative alerts are active and downside risk needs immediate ranking.",
            "objective": "Surface the most urgent risk names first, then check the next-session action stack.",
            "focus_points": "negative alerts / avoid list / next-session risk names",
            "reading_order": "latest alerts -> next-session action -> stock-pool health",
            "reading_pace": "fast risk-first scan",
            "second_step_note": "Second step: review the next-session action summary to confirm core, candidate, and avoid names.",
        },
        "alert_scan": {
            "first_step_note": "First step: scan the latest alerts, then confirm the next-session action summary.",
            "scenario": "Opening Alert Scan",
            "applicable_session": "Use near the open when fresh alerts deserve a fast first-pass review.",
            "objective": "Quickly scan fresh alerts and lock the first pass of the next-session watchlist.",
            "focus_points": "fresh alerts / opening strength / first-pass watchlist",
            "reading_order": "latest alerts -> next-session action -> stock-pool health",
            "reading_pace": "quick first pass",
            "second_step_note": "Second step: review the next-session action summary to confirm core, candidate, and avoid names.",
        },
        "intraday_alert_review": {
            "first_step_note": "First step: rescan the latest alerts, then confirm whether leadership and next-session action still align.",
            "scenario": "Intraday Alert Review",
            "applicable_session": "Use mid-session when new alerts appear after the opening pass and alignment needs refreshing.",
            "objective": "Check whether fresh intraday alerts change the current main-line read or watchlist priority.",
            "focus_points": "fresh alerts / leader follow-through / watchlist alignment",
            "reading_order": "latest alerts -> strongest sector -> next-session action",
            "reading_pace": "targeted intraday refresh",
            "second_step_note": "Second step: compare the strongest sector and next-session action summary before widening the research conclusion.",
        },
        "batch_review": {
            "first_step_note": "First step: compare saved batches, then review the next-session action summary.",
            "scenario": "Saved Batch Review",
            "applicable_session": "Use later in the session when multiple saved snapshots are available for comparison.",
            "objective": "Compare recent snapshots and decide which changes deserve continued tracking.",
            "focus_points": "snapshot changes / continuation names / follow-through candidates",
            "reading_order": "saved batches -> next-session action -> stock-pool health",
            "reading_pace": "comparison and replay",
            "second_step_note": "Second step: return to the next-session action summary and confirm which changes deserve follow-through.",
        },
        "close_review": {
            "first_step_note": "First step: compare saved batches, then confirm the strongest sector and next-session action before wrapping the session read.",
            "scenario": "Close Review",
            "applicable_session": "Use into the close when multiple snapshots exist and the day needs a structured replay.",
            "objective": "Replay the day's structural changes and decide what deserves next-session continuity tracking.",
            "focus_points": "snapshot replay / strongest sector / next-session continuity",
            "reading_order": "saved batches -> strongest sector -> next-session action",
            "reading_pace": "slow replay",
            "second_step_note": "Second step: return to the stock-pool health and next-session action summary to lock tomorrow's carry-forward names.",
        },
        "baseline_review": {
            "first_step_note": "First step: confirm the strongest sector and stock-pool health, then expand into deeper analysis.",
            "scenario": "Baseline Main-line Review",
            "applicable_session": "Use when the session is relatively quiet and a balanced main-line read is enough.",
            "objective": "Confirm the strongest sector and pool health before expanding into deeper analysis.",
            "focus_points": "strongest sector / pool health / main-line continuity",
            "reading_order": "strongest sector -> stock-pool health -> next-session action",
            "reading_pace": "balanced read",
            "second_step_note": "Second step: review the next-session action summary and strongest sector to complete the main-line read.",
        },
        "midday_baseline_review": {
            "first_step_note": "First step: confirm the strongest sector and leader follow-through, then validate stock-pool health.",
            "scenario": "Midday Main-line Review",
            "applicable_session": "Use mid-session when the market is relatively calm but leadership continuity still needs checking.",
            "objective": "Confirm whether the main line is continuing cleanly before expanding into deeper analysis.",
            "focus_points": "strongest sector / leader continuity / pool health",
            "reading_order": "strongest sector -> leader summary -> stock-pool health",
            "reading_pace": "steady midday read",
            "second_step_note": "Second step: review the next-session action summary and latest alerts to confirm whether the main line is still intact.",
        },
    }
    if copy_variant != "business_cn":
        return base_specs

    localized_specs = {
        "daily_priority_review": {
            "first_step_note": "首步动作：先读当日优先摘要，再确认下一交易时段动作摘要。",
            "scenario": "当日优先摘要首读",
            "applicable_session": "适用于当天新闻优先级摘要已经生成，需要先按摘要顺序进入业务主线的时段。",
            "objective": "先锁定今天的首读顺序和重点观察名单，再扩展到其他模块。",
            "focus_points": "核心摘要 / 阅读顺序 / 重点观察名单",
            "reading_order": "当日优先摘要 -> 下一交易时段动作摘要 -> 股票池健康度",
            "reading_pace": "摘要优先",
            "second_step_note": "第二步：回到下一交易时段动作摘要和股票池健康度，确认今天的执行重点是否需要调整。",
        },
        "daily_priority_risk_review": {
            "first_step_note": "首步动作：先读当日优先摘要，再核对最新风险提醒。",
            "scenario": "当日优先摘要风险复核",
            "applicable_session": "适用于当天新闻优先级摘要已经生成，同时盘面仍有风险提醒需要马上确认的时段。",
            "objective": "先按当日摘要锁定首读顺序，再确认风险侧是否进一步强化。",
            "focus_points": "当日优先顺序 / 风险提醒 / 回避名单",
            "reading_order": "当日优先摘要 -> 最新提醒 -> 下一交易时段动作摘要",
            "reading_pace": "摘要先行、风险复核",
            "second_step_note": "第二步：回到下一交易时段动作摘要，确认哪些名字应继续放在核心、候选或回避层。",
        },
        "stock_pool_blocking_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u68c0\u67e5\u76d1\u63a7\u6c60\u5065\u5eb7\u72b6\u6001\u3001\u5b57\u6bb5\u5408\u6cd5\u6027\u548c\u6ce8\u518c\u8868\u6620\u5c04\uff0c\u518d\u53c2\u8003\u76d8\u9762\u7ed3\u8bba\u3002",
            "scenario": "\u76d1\u63a7\u6c60\u963b\u65ad\u590d\u6838",
            "applicable_session": "\u9002\u7528\u4e8e\u76d1\u63a7\u6c60\u963b\u65ad\u6216\u4fe1\u53f7\u53ef\u4fe1\u5ea6\u4e0d\u8db3\uff0c\u5fc5\u987b\u5148\u6062\u590d\u7ed3\u6784\u4fe1\u4efb\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u6062\u590d\u5bf9\u80a1\u7968\u6c60\u7ed3\u6784\u3001\u5b57\u6bb5\u4e0e\u6620\u5c04\u5173\u7cfb\u7684\u4fe1\u4efb\uff0c\u518d\u5224\u65ad\u76d8\u9762\u7ed3\u8bba\u3002",
            "focus_points": "\u5b57\u6bb5\u5408\u6cd5 / \u6620\u5c04\u5173\u7cfb / \u963b\u65ad\u9879",
            "reading_order": "\u76d1\u63a7\u6c60\u5065\u5eb7 -> \u6700\u65b0\u63d0\u9192 -> \u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c",
            "reading_pace": "\u6162\u901f\u786e\u8ba4",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u7ed3\u5408\u6700\u65b0\u63d0\u9192\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u786e\u8ba4\u4eca\u5929\u662f\u5426\u9700\u8981\u8c03\u6574\u7814\u7a76\u91cd\u70b9\u3002",
        },
        "stock_pool_drift_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u770b\u76d1\u63a7\u6c60\u6f02\u79fb\u6458\u8981\u548c\u6279\u6b21\u5bf9\u6bd4\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u6269\u5927\u7814\u7a76\u7ed3\u8bba\u3002",
            "scenario": "\u76d1\u63a7\u6c60\u6f02\u79fb\u590d\u6838",
            "applicable_session": "\u9002\u7528\u4e8e\u76d1\u63a7\u6c60\u7ed3\u6784\u51fa\u73b0\u504f\u79fb\uff0c\u4eca\u65e5\u7814\u7a76\u8303\u56f4\u53ef\u80fd\u9700\u8981\u91cd\u7b97\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u786e\u8ba4\u76d1\u63a7\u6c60\u7ed3\u6784\u53d8\u5316\u662f\u5426\u6539\u53d8\u4eca\u65e5\u7814\u7a76\u4e3b\u7ebf\u8303\u56f4\u3002",
            "focus_points": "\u504f\u79fb\u6807\u7b7e / \u6279\u6b21\u5bf9\u6bd4 / \u4e3b\u7ebf\u8303\u56f4",
            "reading_order": "\u76d1\u63a7\u6c60\u5065\u5eb7 -> \u5df2\u4fdd\u5b58\u6279\u6b21 -> \u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c",
            "reading_pace": "\u5bf9\u6bd4\u4f18\u5148",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u7ed3\u5408\u6700\u65b0\u63d0\u9192\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u786e\u8ba4\u4eca\u5929\u662f\u5426\u9700\u8981\u8c03\u6574\u7814\u7a76\u91cd\u70b9\u3002",
        },
        "stock_pool_health_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u770b\u76d1\u63a7\u6c60\u5c31\u7eea\u5ea6\u4e0e\u5065\u5eb7\u63d0\u793a\uff0c\u518d\u5c55\u5f00\u540e\u7eed\u52a8\u4f5c\u3002",
            "scenario": "\u76d1\u63a7\u6c60\u5065\u5eb7\u590d\u6838",
            "applicable_session": "\u9002\u7528\u4e8e\u76d1\u63a7\u6c60\u5c1a\u672a\u5b8c\u5168\u6e05\u6d01\uff0c\u9700\u8981\u5148\u505a\u5065\u5eb7\u6821\u9a8c\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u786e\u8ba4\u5c31\u7eea\u5ea6\u4e0e\u5065\u5eb7\u63d0\u793a\uff0c\u518d\u5c55\u5f00\u540e\u7eed\u7ed3\u8bba\u3002",
            "focus_points": "\u5c31\u7eea\u63d0\u793a / \u9884\u8b66\u4fe1\u53f7 / \u76d1\u63a7\u53ef\u7528\u6027",
            "reading_order": "\u76d1\u63a7\u6c60\u5065\u5eb7 -> \u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c -> \u6700\u65b0\u63d0\u9192",
            "reading_pace": "\u7a33\u6b65\u6821\u9a8c",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u7ed3\u5408\u6700\u65b0\u63d0\u9192\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u786e\u8ba4\u4eca\u5929\u662f\u5426\u9700\u8981\u8c03\u6574\u7814\u7a76\u91cd\u70b9\u3002",
        },
        "risk_alert_scan": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u770b\u6700\u65b0\u98ce\u9669\u63d0\u9192\uff0c\u518d\u5bf9\u7167\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            "scenario": "\u98ce\u9669\u63d0\u9192\u5feb\u626b",
            "applicable_session": "\u9002\u7528\u4e8e\u8d1f\u5411\u63d0\u9192\u6d3b\u8dc3\uff0c\u9700\u8981\u5148\u5bf9\u4e0b\u884c\u98ce\u9669\u505a\u6392\u5e8f\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u9501\u5b9a\u6700\u9700\u5904\u7406\u7684\u98ce\u9669\u6807\u7684\uff0c\u518d\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u6808\u3002",
            "focus_points": "\u8d1f\u5411\u63d0\u9192 / \u56de\u907f\u540d\u5355 / \u98ce\u9669\u6807\u7684",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u6838\u5fc3/\u5019\u9009/\u56de\u907f\u540d\u5355\u3002",
        },
        "alert_scan": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u626b\u6700\u65b0\u63d0\u9192\uff0c\u518d\u770b\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            "scenario": "\u76d8\u521d\u63d0\u9192\u5feb\u626b",
            "applicable_session": "\u9002\u7528\u4e8e\u76d8\u521d\u6216\u65b0\u63d0\u9192\u5bc6\u96c6\u7684\u65f6\u6bb5\uff0c\u9700\u8981\u5feb\u901f\u505a\u7b2c\u4e00\u8f6e\u626b\u63cf\u3002",
            "objective": "\u5148\u5feb\u901f\u626b\u63cf\u6700\u65b0\u63d0\u9192\uff0c\u518d\u5b8c\u6210\u7b2c\u4e00\u8f6e\u89c2\u5bdf\u540d\u5355\u5224\u65ad\u3002",
            "focus_points": "\u6700\u65b0\u63d0\u9195 / \u76d8\u521d\u5f3a\u5ea6 / \u7b2c\u4e00\u8f6e\u89c2\u5bdf\u540d\u5355",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u6838\u5fc3/\u5019\u9009/\u56de\u907f\u540d\u5355\u3002",
        },
        "batch_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21\uff0c\u518d\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            "scenario": "\u6279\u6b21\u5bf9\u6bd4\u590d\u76d8",
            "applicable_session": "\u9002\u7528\u4e8e\u5c3e\u76d8\u6216\u76d8\u540e\uff0c\u5df2\u7ecf\u79ef\u7d2f\u591a\u4e2a\u5feb\u7167\u53ef\u4ee5\u5bf9\u6bd4\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u5bf9\u6bd4\u6700\u8fd1\u5feb\u7167\u53d8\u5316\uff0c\u518d\u786e\u5b9a\u54ea\u4e9b\u6807\u7684\u503c\u5f97\u7ee7\u7eed\u8ddf\u8e2a\u3002",
            "focus_points": "\u5feb\u7167\u53d8\u5316 / \u5ef6\u7eed\u6807\u7684 / \u8ddf\u8e2a\u5019\u9009",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u54ea\u4e9b\u53d8\u5316\u503c\u5f97\u7ee7\u7eed\u8ddf\u8e2a\u3002",
        },
        "close_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21\uff0c\u518d\u786e\u8ba4\u6700\u5f3a\u677f\u5757\u4e0e\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            "scenario": "\u5c3e\u76d8\u590d\u76d8",
            "applicable_session": "\u9002\u7528\u4e8e\u5c3e\u76d8\uff0c\u5df2\u6709\u591a\u4e2a\u5feb\u7167\u53ef\u5bf9\u6bd4\uff0c\u9700\u8981\u5bf9\u5f53\u65e5\u4e3b\u7ebf\u505a\u5b8c\u6574\u56de\u653e\u3002",
            "objective": "\u56de\u653e\u5f53\u65e5\u7ed3\u6784\u53d8\u5316\uff0c\u786e\u8ba4\u54ea\u4e9b\u7ed3\u8bba\u503c\u5f97\u5e26\u5165\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u3002",
            "focus_points": "\u6279\u6b21\u56de\u653e / \u6700\u5f3a\u677f\u5757 / \u5ef6\u7eed\u540d\u5355",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u76d1\u63a7\u6c60\u5065\u5eb7\u4e0e\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u9501\u5b9a\u660e\u65e5\u8ddf\u8e2a\u6807\u7684\u3002",
        },
        "baseline_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u786e\u8ba4\u6700\u5f3a\u677f\u5757\u4e0e\u76d1\u63a7\u6c60\u5065\u5eb7\u72b6\u6001\uff0c\u518d\u5c55\u5f00\u6df1\u5ea6\u5206\u6790\u3002",
            "scenario": "\u4e3b\u7ebf\u57fa\u7ebf\u9605\u8bfb",
            "applicable_session": "\u9002\u7528\u4e8e\u76d8\u9762\u8f83\u5e73\u7a33\uff0c\u4e0d\u9700\u8981\u8fc7\u5ea6\u504f\u5411\u98ce\u9669\u6216\u590d\u76d8\u573a\u666f\u7684\u65f6\u6bb5\u3002",
            "objective": "\u5148\u786e\u8ba4\u6700\u5f3a\u677f\u5757\u548c\u76d1\u63a7\u6c60\u5065\u5eb7\u72b6\u6001\uff0c\u518d\u5c55\u5f00\u6df1\u5ea6\u5206\u6790\u3002",
            "focus_points": "\u6700\u5f3a\u677f\u5757 / \u76d1\u63a7\u6c60\u5065\u5eb7 / \u4e3b\u7ebf\u5ef6\u7eed",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u518d\u770b\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u8865\u5168\u4e3b\u7ebf\u5224\u65ad\u3002",
        },
        "midday_baseline_review": {
            "first_step_note": "\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u786e\u8ba4\u6700\u5f3a\u677f\u5757\u4e0e\u9f99\u5934\u5ef6\u7eed\uff0c\u518d\u56de\u770b\u76d1\u63a7\u6c60\u5065\u5eb7\u3002",
            "scenario": "\u5348\u95f4\u4e3b\u7ebf\u590d\u6838",
            "applicable_session": "\u9002\u7528\u4e8e\u76d8\u4e2d\u8f83\u5e73\u7a33\uff0c\u4f46\u4ecd\u9700\u8981\u786e\u8ba4\u9f99\u5934\u4e0e\u4e3b\u7ebf\u5ef6\u7eed\u6027\u7684\u65f6\u6bb5\u3002",
            "objective": "\u786e\u8ba4\u5f53\u524d\u4e3b\u7ebf\u662f\u5426\u4ecd\u5728\u5065\u5eb7\u5ef6\u7eed\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u6269\u5927\u5206\u6790\u3002",
            "focus_points": "\u6700\u5f3a\u677f\u5757 / \u9f99\u5934\u5ef6\u7eed / \u76d1\u63a7\u6c60\u5065\u5eb7",
            "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u770b\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u4e0e\u6700\u65b0\u63d0\u9192\uff0c\u786e\u8ba4\u4e3b\u7ebf\u662f\u5426\u4ecd\u7136\u8fde\u8d2f\u3002",
        },
    }
    return localized_specs


def build_priority_action_topline_specs(
    copy_variant: str = "default",
) -> dict[str, dict[str, str]]:
    """Return replaceable top-line context labels for the action-summary card."""
    base_specs = {
        "today_priority_summary": {
            "context_prefix": "Top-line daily priority conclusion",
        },
        "latest_alerts": {
            "context_prefix": "Top-line risk view",
        },
        "strongest_sector": {
            "context_prefix": "Top-line main-line view",
        },
        "leader_summary": {
            "context_prefix": "Top-line main-line view",
        },
        "next_session_action": {
            "context_prefix": "Top-line main-line view",
        },
        "stock_pool_health": {
            "context_prefix": "Top-line stock-pool drift view",
        },
    }
    if copy_variant != "business_cn":
        return base_specs
    return {
        "today_priority_summary": {
            "context_prefix": "顶层当日优先结论",
        },
        "latest_alerts": {
            "context_prefix": "\u9876\u5c42\u98ce\u9669\u7ed3\u8bba",
        },
        "strongest_sector": {
            "context_prefix": "\u9876\u5c42\u4e3b\u7ebf\u7ed3\u8bba",
        },
        "leader_summary": {
            "context_prefix": "\u9876\u5c42\u4e3b\u7ebf\u7ed3\u8bba",
        },
        "next_session_action": {
            "context_prefix": "\u9876\u5c42\u4e3b\u7ebf\u7ed3\u8bba",
        },
        "stock_pool_health": {
            "context_prefix": "\u9876\u5c42\u76d1\u63a7\u6c60\u7ed3\u6784\u7ed3\u8bba",
        },
    }


def build_dynamic_action_focus_specs(
    copy_variant: str = "default",
) -> dict[str, dict[str, object]]:
    """Return replaceable dynamic action-focus rules for first-screen reading anchors."""
    base_specs: dict[str, dict[str, object]] = {
        "today_priority_summary": {
            "rule_order": [
                "broad_watch_state",
                "available_state",
            ],
            "broad_watch_state": {
                "conditions": [
                    {
                        "field": "shown_items",
                        "op": "gte",
                        "value": 2,
                    },
                    {
                        "field": "watch_group_count",
                        "op": "gte",
                        "value": 2,
                    },
                ],
                "hint": "Check today's core summary, reading order, and grouped watchlist first.",
                "field_hint": "summary date, priority count, and watch-group count.",
                "group_hint": "core summary and watchlist sections.",
                "conclusion_hint": "what deserves the first read today before widening the research scope.",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "Check today's core summary and one-line advice first.",
                "field_hint": "summary date, priority count, and source batch.",
                "group_hint": "core summary and reading-order sections.",
                "conclusion_hint": "what should be read first today.",
            },
        },
        "latest_alerts": {
            "rule_order": [
                "news_flash_risk_state",
                "negative_alert_state",
                "materials_focus_reinforcement_state",
                "sector_move_state",
                "materials_focus_state",
                "news_flash_state",
                "price_spike_state",
                "active_alert_state",
            ],
            "negative_alert_state": {
                "min_negative_alert_count": 1,
                "conditions": [
                    {
                        "field": "negative_alert_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest negative alert timestamp, type, and risk message first.",
                "field_hint": "newest negative alert timestamp, alert type, and risk message.",
                "group_hint": "negative alert detail rows.",
                "conclusion_hint": "whether these negative alerts change today's first-read priority.",
            },
            "materials_focus_reinforcement_state": {
                "conditions": [
                    {
                        "field": "materials_focus_count",
                        "op": "gte",
                        "value": 1,
                    },
                    {
                        "field": "sector_move_count",
                        "op": "gte",
                        "value": 1,
                    },
                ],
                "hint": "Check the newest materials-focus alert first.",
                "field_hint": "materials-focus timestamp, alert type, and message.",
                "group_hint": "materials-focus alert rows.",
                "conclusion_hint": "whether materials-chain strength is now reinforcing and broadening into a larger main-line read.",
            },
            "sector_move_state": {
                "conditions": [
                    {
                        "field": "sector_move_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest sector-move alert first.",
                "field_hint": "sector-move timestamp, alert type, and message.",
                "group_hint": "sector-move alert rows.",
                "conclusion_hint": "whether sector strength is broadening enough to change today's main-line read.",
            },
            "materials_focus_state": {
                "conditions": [
                    {
                        "field": "materials_focus_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest materials-focus alert first.",
                "field_hint": "materials-focus timestamp, alert type, and message.",
                "group_hint": "materials-focus alert rows.",
                "conclusion_hint": "whether materials-chain follow-through deserves a higher place in today's read.",
            },
            "news_flash_risk_state": {
                "conditions": [
                    {
                        "field": "news_flash_count",
                        "op": "gte",
                        "value": 1,
                    },
                    {
                        "field": "negative_alert_count",
                        "op": "gte",
                        "value": 1,
                    },
                ],
                "hint": "Check the newest risk-driven news-flash alert first.",
                "field_hint": "news-flash timestamp, alert type, and risk message.",
                "group_hint": "news-flash alert rows.",
                "conclusion_hint": "whether fresh news is disrupting today's sector or name priority.",
            },
            "news_flash_state": {
                "conditions": [
                    {
                        "field": "news_flash_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest news-flash alert first.",
                "field_hint": "news-flash timestamp, alert type, and message.",
                "group_hint": "news-flash alert rows.",
                "conclusion_hint": "whether fresh news changes today's sector or name priority.",
            },
            "price_spike_state": {
                "conditions": [
                    {
                        "field": "price_spike_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest price-spike alert first.",
                "field_hint": "price-spike timestamp, alert type, and message.",
                "group_hint": "price-spike alert rows.",
                "conclusion_hint": "whether a single-stock move deserves promotion into the main read.",
            },
            "active_alert_state": {
                "min_alert_count": 1,
                "conditions": [
                    {
                        "field": "alert_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "Check the newest alert timestamp, type, and message first.",
                "field_hint": "newest alert timestamp, alert type, and message.",
                "group_hint": "latest alert detail rows.",
                "conclusion_hint": "whether the newest alerts change today's first-read main line.",
            },
        },
        "stock_pool_health": {
            "rule_order": [
                "blocking_state",
                "warning_state",
                "available_state",
            ],
            "blocking_state": {
                "statuses": ["invalid"],
                "risk_levels": ["blocking"],
                "match": "any",
                "conditions": [
                    {
                        "field": "status",
                        "op": "in",
                        "value": ["invalid"],
                    },
                    {
                        "field": "risk_level",
                        "op": "in",
                        "value": ["blocking"],
                    },
                ],
                "hint": "Check blocking issues, duplicate codes, and validation hints first.",
                "field_hint": "risk level, duplicate codes, and validation hints.",
                "group_hint": "validation issue groups.",
                "conclusion_hint": "whether the stock pool must be fixed before you rely on it today.",
            },
            "warning_state": {
                "risk_levels": ["warning"],
                "conditions": [
                    {
                        "field": "risk_level",
                        "op": "in",
                        "value": ["warning"],
                    }
                ],
                "hint": "Check warning-level issues and structure-change tags first.",
                "field_hint": "risk level, structure-change tags, and health hints.",
                "group_hint": "warning issue and suggestion groups.",
                "conclusion_hint": "whether the stock pool is still usable now or needs a structure review first.",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "Check the health level, structure summary, and comparison tags first.",
                "field_hint": "health level, structure summary, and comparison tags.",
                "group_hint": "readiness and structure-comparison groups.",
                "conclusion_hint": "whether the stock pool is stable enough to support today's main-line read.",
            },
        },
        "strongest_sector": {
            "rule_order": [
                "broad_strength_state",
                "clear_strength_state",
                "available_state",
            ],
            "broad_strength_state": {
                "min_avg_pct_chg": 5.0,
                "min_stock_count": 3,
                "conditions": [
                    {
                        "field": "avg_pct_chg",
                        "op": "gte",
                        "value": 5.0,
                    },
                    {
                        "field": "stock_count",
                        "op": "gte",
                        "value": 3,
                    },
                ],
                "hint": "Check the leading sector name, average change, and member count first.",
                "field_hint": "leading sector name, average change, and member count.",
                "group_hint": "sector detail rows.",
                "conclusion_hint": "whether this main line has both strong momentum and enough breadth today.",
            },
            "clear_strength_state": {
                "min_avg_pct_chg": 3.0,
                "conditions": [
                    {
                        "field": "avg_pct_chg",
                        "op": "gte",
                        "value": 3.0,
                    }
                ],
                "hint": "Check the leading sector name and average change first.",
                "field_hint": "leading sector name, average change, and member count.",
                "group_hint": "sector detail rows.",
                "conclusion_hint": "whether this is a clear main line or only a narrow strength pocket.",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "Check the leading sector name and average change first.",
                "field_hint": "leading sector name, average change, and member count.",
                "group_hint": "sector detail rows.",
                "conclusion_hint": "whether today's strongest sector is still clear enough to anchor the read.",
            },
        },
        "leader_summary": {
            "rule_order": [
                "coherent_dual_leader_state",
                "concentrated_state",
                "narrow_state",
                "available_state",
            ],
            "coherent_dual_leader_state": {
                "conditions": [
                    {
                        "field": "has_trend_leader",
                        "op": "truthy",
                    },
                    {
                        "field": "has_emotion_leader",
                        "op": "truthy",
                    },
                ],
                "hint": "Check whether trend and emotion leaders are both still active first.",
                "field_hint": "trend leader, emotion leader, and active slot count.",
                "group_hint": "leader detail rows.",
                "conclusion_hint": "whether leadership is still aligned enough to confirm the current main line.",
            },
            "concentrated_state": {
                "conditions": [
                    {
                        "field": "leader_count",
                        "op": "gte",
                        "value": 2,
                    }
                ],
                "hint": "Check the active leader names and slot count first.",
                "field_hint": "active leader names and slot count.",
                "group_hint": "leader detail rows.",
                "conclusion_hint": "whether leadership is still concentrated enough to support the current main line.",
            },
            "narrow_state": {
                "conditions": [
                    {
                        "field": "leader_count",
                        "op": "eq",
                        "value": 1,
                    }
                ],
                "hint": "Check the remaining active leader name first.",
                "field_hint": "remaining leader name and slot count.",
                "group_hint": "leader detail rows.",
                "conclusion_hint": "whether leadership has narrowed enough that the main line now needs extra confirmation.",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "Check the leader map and how many leader slots are still active.",
                "field_hint": "active leader names and slot count.",
                "group_hint": "leader detail rows.",
                "conclusion_hint": "whether leadership is still concentrated and intact.",
            },
        },
        "next_session_action": {
            "rule_order": [
                "avoid_reduce_state",
                "avoid_first_state",
                "core_stay_with_state",
                "core_first_state",
                "available_state",
            ],
            "avoid_reduce_state": {
                "conditions": [
                    {
                        "field": "avoid_reason_text",
                        "op": "startswith",
                        "value": "reduce names tied to ",
                    }
                ],
                "hint": "Check the avoid list and the reduction reason first.",
                "field_hint": "avoid names, reduction focus, and score rows.",
                "group_hint": "avoid section.",
                "conclusion_hint": "which linked names should be cut back before tomorrow's follow-through read.",
            },
            "avoid_first_state": {
                "require_avoid_priority": True,
                "conditions": [
                    {
                        "field": "avoid_count",
                        "op": "gt",
                        "value": 0,
                    },
                    {
                        "field": "avoid_count",
                        "op": "gte_field",
                        "value_field": "core_count",
                    },
                ],
                "hint": "Check the avoid list and risk reasons first.",
                "field_hint": "avoid names, risk tags, and score rows.",
                "group_hint": "avoid section.",
                "conclusion_hint": "which names should be reduced or avoided before widening tomorrow's read.",
            },
            "core_stay_with_state": {
                "conditions": [
                    {
                        "field": "core_reason_text",
                        "op": "startswith",
                        "value": "stay with ",
                    }
                ],
                "hint": "Check the core watchlist and stay-with reason first.",
                "field_hint": "core names, stay-with focus, and score rows.",
                "group_hint": "core section.",
                "conclusion_hint": "which leaders should remain at the front of tomorrow's core watchlist.",
            },
            "core_first_state": {
                "require_core_priority": True,
                "conditions": [
                    {
                        "field": "core_count",
                        "op": "gt",
                        "value": 0,
                    },
                    {
                        "field": "candidate_count",
                        "op": "lte_field",
                        "value_field": "core_count",
                    },
                ],
                "hint": "Check the core watchlist and focus rows first.",
                "field_hint": "core names, focus rows, and score rows.",
                "group_hint": "core section.",
                "conclusion_hint": "which names should stay at the front of tomorrow's core watchlist.",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "Check the core, candidate, and avoid balance first.",
                "field_hint": "core/candidate/avoid counts and focus rows.",
                "group_hint": "core / candidate / avoid sections.",
                "conclusion_hint": "whether tomorrow's action tiers need to be rebalanced.",
            },
        },
    }
    if copy_variant != "business_cn":
        return base_specs
    return _build_business_cn_dynamic_action_focus_specs()


def build_dynamic_action_focus_fact_specs() -> dict[str, dict[str, object]]:
    """Return replaceable fact-build specs for dynamic action-focus rule matching."""
    return {
        "today_priority_summary": {
            "source_key": "today_priority_summary",
            "container_transform": "normalize_dict",
            "fields": [
                {
                    "fact_key": "shown_items",
                    "source_key": "shown_items",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "watch_group_count",
                    "source_key": "watch_group_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "has_data",
                    "derive_from": "container",
                    "transform": "bool",
                    "fallback": False,
                },
            ],
        },
        "latest_alerts": {
            "source_key": "latest_alerts",
            "container_transform": "normalize_list",
            "fields": [
                {
                    "fact_key": "negative_alert_count",
                    "source_key": "negative_alert_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "alert_count",
                    "source_key": "alert_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "newest_alert_type",
                    "derive_from": "container",
                    "transform": "first_item_field_lower",
                    "field_key": "alert_type",
                    "fallback": "",
                },
                {
                    "fact_key": "sector_move_count",
                    "derive_from": "container",
                    "transform": "count_items_with_field_value",
                    "field_key": "alert_type",
                    "match_value": "sector_move",
                    "fallback": 0,
                },
                {
                    "fact_key": "materials_focus_count",
                    "derive_from": "container",
                    "transform": "count_items_with_field_value",
                    "field_key": "alert_type",
                    "match_value": "materials_focus",
                    "fallback": 0,
                },
                {
                    "fact_key": "news_flash_count",
                    "derive_from": "container",
                    "transform": "count_items_with_field_value",
                    "field_key": "alert_type",
                    "match_value": "news_flash",
                    "fallback": 0,
                },
                {
                    "fact_key": "price_spike_count",
                    "derive_from": "container",
                    "transform": "count_items_with_field_value",
                    "field_key": "alert_type",
                    "match_value": "price_spike",
                    "fallback": 0,
                },
            ],
        },
        "stock_pool_health": {
            "source_key": "stock_pool_health",
            "container_transform": "normalize_dict",
            "fields": [
                {
                    "fact_key": "status",
                    "source_key": "status",
                    "transform": "normalized_lower_str",
                    "fallback": "",
                },
                {
                    "fact_key": "risk_level",
                    "source_key": "risk_level",
                    "transform": "normalized_lower_str",
                    "fallback": "",
                },
                {
                    "fact_key": "has_data",
                    "derive_from": "container",
                    "transform": "bool",
                    "fallback": False,
                },
            ],
        },
        "strongest_sector": {
            "source_key": "strongest_sector_summary",
            "container_transform": "normalize_dict",
            "fields": [
                {
                    "fact_key": "avg_pct_chg",
                    "source_key": "avg_pct_chg",
                    "transform": "safe_float",
                    "fallback": 0.0,
                },
                {
                    "fact_key": "stock_count",
                    "source_key": "stock_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "has_data",
                    "derive_from": "container",
                    "transform": "bool",
                    "fallback": False,
                },
            ],
        },
        "leader_summary": {
            "source_key": "leader_summary",
            "container_transform": "normalize_dict",
            "fields": [
                {
                    "fact_key": "leader_count",
                    "derive_from": "container",
                    "transform": "len",
                    "fallback": 0,
                },
                {
                    "fact_key": "has_data",
                    "derive_from": "container",
                    "transform": "bool",
                    "fallback": False,
                },
                {
                    "fact_key": "has_trend_leader",
                    "source_key": "Trend Leader",
                    "transform": "bool",
                    "fallback": False,
                },
                {
                    "fact_key": "has_emotion_leader",
                    "source_key": "Emotion Leader",
                    "transform": "bool",
                    "fallback": False,
                },
            ],
        },
        "next_session_action": {
            "source_key": "next_session_action_summary",
            "container_transform": "normalize_dict",
            "fields": [
                {
                    "fact_key": "core_count",
                    "source_key": "core_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "candidate_count",
                    "source_key": "candidate_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "avoid_count",
                    "source_key": "avoid_count",
                    "transform": "safe_int",
                    "fallback": 0,
                },
                {
                    "fact_key": "core_reason_text",
                    "path": ["core", "reason"],
                    "transform": "normalized_lower_str",
                    "fallback": "",
                },
                {
                    "fact_key": "avoid_reason_text",
                    "path": ["avoid", "reason"],
                    "transform": "normalized_lower_str",
                    "fallback": "",
                },
                {
                    "fact_key": "has_data",
                    "derive_from": "container",
                    "transform": "bool",
                    "fallback": False,
                },
            ],
        },
    }


def _build_business_cn_dynamic_action_focus_specs() -> dict[str, dict[str, object]]:
    """Return localized dynamic action-focus rules for the Chinese business view."""
    return {
        "today_priority_summary": {
            "rule_order": [
                "broad_watch_state",
                "available_state",
            ],
            "broad_watch_state": {
                "conditions": [
                    {
                        "field": "shown_items",
                        "op": "gte",
                        "value": 2,
                    },
                    {
                        "field": "watch_group_count",
                        "op": "gte",
                        "value": 2,
                    },
                ],
                "hint": "先看当日核心摘要、阅读顺序和分组后的重点观察名单。",
                "field_hint": "日期、高优先级条数和观察分组数。",
                "group_hint": "核心摘要与重点观察名单分组。",
                "conclusion_hint": "今天最应该先读什么，再决定是否扩展研究范围。",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "先看当日核心摘要和一句话建议。",
                "field_hint": "日期、高优先级条数和来源批次。",
                "group_hint": "核心摘要和阅读顺序分组。",
                "conclusion_hint": "今天应该先从哪条线开始阅读。",
            },
        },
        "latest_alerts": {
            "rule_order": [
                "negative_alert_state",
                "active_alert_state",
            ],
            "negative_alert_state": {
                "min_negative_alert_count": 1,
                "conditions": [
                    {
                        "field": "negative_alert_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "先看最新负向提醒的时间、类型和风险信息，再判断今天是否需要先收缩关注范围。",
                "field_hint": "最新负向提醒时间、提醒类型和风险信息。",
                "group_hint": "负向提醒明细行。",
                "conclusion_hint": "这些负向提醒是否已经改变今天的优先阅读顺序。",
            },
            "active_alert_state": {
                "min_alert_count": 1,
                "conditions": [
                    {
                        "field": "alert_count",
                        "op": "gte",
                        "value": 1,
                    }
                ],
                "hint": "先看最新提醒时间、类型和消息，再判断是否需要切换今天的首看主线。",
                "field_hint": "最新提醒时间、提醒类型和消息。",
                "group_hint": "最新提醒明细行。",
                "conclusion_hint": "新提醒是否已经改变今天的首看重点。",
            },
        },
        "stock_pool_health": {
            "rule_order": [
                "blocking_state",
                "warning_state",
                "available_state",
            ],
            "blocking_state": {
                "statuses": ["invalid"],
                "risk_levels": ["blocking"],
                "match": "any",
                "conditions": [
                    {
                        "field": "status",
                        "op": "in",
                        "value": ["invalid"],
                    },
                    {
                        "field": "risk_level",
                        "op": "in",
                        "value": ["blocking"],
                    },
                ],
                "hint": "先看阻塞级问题、重复代码和校验提示，再决定今天的监控池是否能继续直接使用。",
                "field_hint": "风险级别、重复代码和主要校验提示。",
                "group_hint": "校验问题分组。",
                "conclusion_hint": "当前监控池是否需要先修复，再继续依赖它做监控。",
            },
            "warning_state": {
                "risk_levels": ["warning"],
                "conditions": [
                    {
                        "field": "risk_level",
                        "op": "in",
                        "value": ["warning"],
                    }
                ],
                "hint": "先看预警级校验问题和结构变化标签，再判断今天是否需要先做结构复核。",
                "field_hint": "风险级别、结构变化标签和健康提示。",
                "group_hint": "预警问题与建议分组。",
                "conclusion_hint": "当前监控池是否还能直接使用，还是应先做结构复核。",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "先看健康级别、结构摘要和变化标签，再确认今天可以按当前监控池继续阅读。",
                "field_hint": "健康级别、结构摘要和变化标签。",
                "group_hint": "就绪状态与结构对比分组。",
                "conclusion_hint": "当前监控池是否足够稳定，可以直接进入主线阅读。",
            },
        },
        "strongest_sector": {
            "rule_order": [
                "broad_strength_state",
                "clear_strength_state",
                "available_state",
            ],
            "broad_strength_state": {
                "min_avg_pct_chg": 5.0,
                "min_stock_count": 3,
                "conditions": [
                    {
                        "field": "avg_pct_chg",
                        "op": "gte",
                        "value": 5.0,
                    },
                    {
                        "field": "stock_count",
                        "op": "gte",
                        "value": 3,
                    },
                ],
                "hint": "先看领涨板块名称、平均涨跌和成分股数，再确认这条主线是否既强又有扩散。",
                "field_hint": "领涨板块名称、平均涨跌和成分股数。",
                "group_hint": "板块明细行。",
                "conclusion_hint": "这条主线是否已经形成强度和扩散同时成立的优势。",
            },
            "clear_strength_state": {
                "min_avg_pct_chg": 3.0,
                "conditions": [
                    {
                        "field": "avg_pct_chg",
                        "op": "gte",
                        "value": 3.0,
                    }
                ],
                "hint": "先看领涨板块名称和平均涨跌，再判断这是清晰主线还是偏单点强势。",
                "field_hint": "领涨板块名称、平均涨跌和成分股数。",
                "group_hint": "板块明细行。",
                "conclusion_hint": "这条主线是否足够清晰，值得继续放在今天前排。",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "先看领涨板块名称和平均涨跌，再确认今天是否仍有足够清晰的主线。",
                "field_hint": "领涨板块名称、平均涨跌和成分股数。",
                "group_hint": "板块明细行。",
                "conclusion_hint": "今天的最强板块是否仍然足以支撑主线判断。",
            },
        },
        "leader_summary": {
            "rule_order": [
                "coherent_dual_leader_state",
                "concentrated_state",
                "narrow_state",
                "available_state",
            ],
            "coherent_dual_leader_state": {
                "conditions": [
                    {
                        "field": "has_trend_leader",
                        "op": "truthy",
                    },
                    {
                        "field": "has_emotion_leader",
                        "op": "truthy",
                    },
                ],
                "hint": "先看趋势龙头和情绪龙头是否仍同时在线，再确认主线龙头是否还保持同向延续。",
                "field_hint": "趋势龙头、情绪龙头和当前槽位数。",
                "group_hint": "龙头明细行。",
                "conclusion_hint": "龙头是否仍足够同向一致，可以继续确认当前主线。",
            },
            "concentrated_state": {
                "conditions": [
                    {
                        "field": "leader_count",
                        "op": "gte",
                        "value": 2,
                    }
                ],
                "hint": "先看仍在延续的龙头名单和槽位数量，再确认主线龙头是否还保持集中。",
                "field_hint": "龙头名单和槽位数量。",
                "group_hint": "龙头明细行。",
                "conclusion_hint": "龙头是否仍然足够集中，足以支撑当前主线判断。",
            },
            "narrow_state": {
                "conditions": [
                    {
                        "field": "leader_count",
                        "op": "eq",
                        "value": 1,
                    }
                ],
                "hint": "先看剩余仍在延续的龙头名字，再判断主线是否已经收窄到需要额外确认。",
                "field_hint": "剩余龙头名字和槽位数量。",
                "group_hint": "龙头明细行。",
                "conclusion_hint": "龙头是否已经明显收窄，导致主线需要更多确认层。",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "先看龙头映射和仍在延续的龙头槽位数。",
                "field_hint": "龙头名单和槽位数。",
                "group_hint": "龙头明细行。",
                "conclusion_hint": "龙头是否仍在集中延续。",
            },
        },
        "next_session_action": {
            "rule_order": [
                "avoid_reduce_state",
                "avoid_first_state",
                "core_stay_with_state",
                "core_first_state",
                "available_state",
            ],
            "avoid_reduce_state": {
                "conditions": [
                    {
                        "field": "avoid_reason_text",
                        "op": "startswith",
                        "value": "reduce names tied to ",
                    }
                ],
                "hint": "先看回避名单和收缩理由，再确认明天应该先缩哪些关联名字。",
                "field_hint": "回避名单、收缩重点和对应分数。",
                "group_hint": "回避分组。",
                "conclusion_hint": "下一交易时段哪些关联名字应先降权或收缩。",
            },
            "avoid_first_state": {
                "require_avoid_priority": True,
                "conditions": [
                    {
                        "field": "avoid_count",
                        "op": "gt",
                        "value": 0,
                    },
                    {
                        "field": "avoid_count",
                        "op": "gte_field",
                        "value_field": "core_count",
                    },
                ],
                "hint": "先看回避名单和风险原因，再确认明天哪些名字需要先降权或回避。",
                "field_hint": "回避名单、风险标签和对应分数。",
                "group_hint": "回避分组。",
                "conclusion_hint": "下一交易时段应先收缩哪些名字，而不是先扩展关注范围。",
            },
            "core_stay_with_state": {
                "conditions": [
                    {
                        "field": "core_reason_text",
                        "op": "startswith",
                        "value": "stay with ",
                    }
                ],
                "hint": "先看核心名单和继续盯住的理由，再确认明天前排核心应聚焦哪些龙头。",
                "field_hint": "核心名单、继续盯住的重点和对应分数。",
                "group_hint": "核心分组。",
                "conclusion_hint": "下一交易时段哪些龙头应继续留在最前排核心观察位。",
            },
            "core_first_state": {
                "require_core_priority": True,
                "conditions": [
                    {
                        "field": "core_count",
                        "op": "gt",
                        "value": 0,
                    },
                    {
                        "field": "candidate_count",
                        "op": "lte_field",
                        "value_field": "core_count",
                    },
                ],
                "hint": "先看核心名单和操作重点，再确认明天优先盯住哪些主线名字。",
                "field_hint": "核心名单、操作重点和对应分数。",
                "group_hint": "核心分组。",
                "conclusion_hint": "下一交易时段哪些名字应继续留在最前排核心观察位。",
            },
            "available_state": {
                "conditions": [
                    {
                        "field": "has_data",
                        "op": "truthy",
                    }
                ],
                "hint": "先看核心、候选、回避三组数量和重点，再确认明天的优先级排布。",
                "field_hint": "核心/候选/回避数量与重点分数。",
                "group_hint": "核心 / 候选 / 回避分组。",
                "conclusion_hint": "下一交易时段的核心、候选、回避层级是否需要调整。",
            },
        },
    }


def build_control_band_layout_specs() -> dict[str, list[str]]:
    """Return replaceable slot order for the first-screen control band."""
    return {
        "default": ["view_mode", "action_summary", "batch_focus", "data_source"],
        "quick_scan": ["action_summary", "batch_focus", "view_mode", "data_source"],
        "business_cn": ["view_mode", "action_summary", "data_source", "batch_focus"],
    }


def build_home_header_layout_specs() -> dict[str, list[str]]:
    """Return replaceable slot order for the full home-header framework."""
    return {
        "default": ["control_band", "kpi"],
        "quick_scan": ["kpi", "control_band"],
        "business_cn": ["control_band", "kpi"],
    }


def build_home_header_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable copy for the unified homepage header framework."""
    intro_spec = build_intro_panel_style_spec(copy_variant)
    return {
        "header_label": str(intro_spec.get("header_intro_label", "home header")),
        "detail_label": str(intro_spec.get("header_detail_label", "header details")),
        "header_body": str(
            intro_spec.get("header_intro_body", "First-screen workspace entry")
        ),
        "supporting_copy": str(
            intro_spec.get(
                "header_supporting_copy",
                "Mode context, batch focus, data source, and KPI stay grouped here.",
            )
        ),
        "compact_supporting_copy": str(
            intro_spec.get("compact_header_supporting_copy", "Header context + KPI")
        ),
        "default_tone": str(intro_spec.get("default_tone", "neutral")),
    }


def build_intro_panel_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return shared style metadata for header/group/section intro containers."""
    base_spec = {
        "detail_label": "details",
        "header_detail_label": "header details",
        "content_detail_label": "content details",
        "header_intro_label": "home header",
        "header_intro_body": "First-screen workspace entry",
        "header_supporting_copy": "Mode context, batch focus, data source, and KPI stay grouped here.",
        "compact_header_supporting_copy": "Header context + KPI",
        "group_intro_label": "content group",
        "group_supporting_copy": "Related homepage sections stay grouped here",
        "compact_group_supporting_copy": "Grouped homepage sections",
        "segment_intro_label": "page segment",
        "segment_supporting_copy": "Related homepage groups stay together in this segment",
        "compact_segment_supporting_copy": "Homepage segment",
        "section_intro_label": "content section",
        "section_supporting_copy": "Structured monitor summary",
        "compact_section_supporting_copy": "Content summary",
        "chart_intro_label": "chart",
        "chart_supporting_copy": "Data table and chart follow",
        "compact_chart_supporting_copy": "Chart + data table",
        "default_tone": "neutral",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "detail_label": "\u7ec6\u8282\u8bf4\u660e",
            "header_detail_label": "\u5934\u90e8\u8bf4\u660e",
            "content_detail_label": "\u5185\u5bb9\u660e\u7ec6",
            "header_intro_label": "\u9996\u5c4f\u5934\u90e8",
            "header_intro_body": "\u9996\u5c4f\u5de5\u4f5c\u53f0\u5165\u53e3",
            "header_supporting_copy": "\u89c6\u56fe\u4e0a\u4e0b\u6587\u3001\u6279\u6b21\u7126\u70b9\u3001\u6570\u636e\u6765\u6e90\u548c KPI \u4f1a\u5728\u8fd9\u91cc\u7ec4\u5408\u663e\u793a\u3002",
            "compact_header_supporting_copy": "\u5934\u90e8\u4e0a\u4e0b\u6587 + KPI",
            "group_intro_label": "\u5185\u5bb9\u5206\u7ec4",
            "group_supporting_copy": "\u76f8\u5173\u9996\u5c4f\u6a21\u5757\u4f1a\u5728\u8fd9\u91cc\u6309\u7ec4\u5c55\u793a",
            "compact_group_supporting_copy": "\u9996\u5c4f\u5206\u7ec4\u6a21\u5757",
            "segment_intro_label": "\u9875\u9762\u6bb5\u843d",
            "segment_supporting_copy": "\u76f8\u5173\u9996\u9875\u5206\u7ec4\u4f1a\u5728\u8fd9\u4e2a\u6bb5\u843d\u91cc\u7ec4\u5408\u663e\u793a",
            "compact_segment_supporting_copy": "\u9996\u9875\u6bb5\u843d",
            "section_intro_label": "\u5185\u5bb9\u533a",
            "section_supporting_copy": "\u7ed3\u6784\u5316\u76d1\u63a7\u6458\u8981",
            "compact_section_supporting_copy": "\u5185\u5bb9\u6458\u8981",
            "chart_intro_label": "\u56fe\u8868",
            "chart_supporting_copy": "\u4e0b\u65b9\u5c55\u793a\u6570\u636e\u8868\u4e0e\u56fe\u8868",
            "compact_chart_supporting_copy": "\u56fe\u8868 + \u6570\u636e\u8868",
        }
    )
    return localized_spec


def build_home_priority_content_layout_specs() -> dict[str, list[str]]:
    """Return replaceable slot order for the first-screen body-priority content cluster."""
    return {
        "default": ["today_priority_summary", "stock_pool_health", "next_session_action"],
        "quick_scan": ["today_priority_summary", "next_session_action", "stock_pool_health"],
        "business_cn": ["today_priority_summary", "stock_pool_health", "next_session_action"],
    }


def build_business_role_specs() -> dict[str, dict[str, str]]:
    """Return shared business-role labels for homepage layout layers."""
    return {
        "context": {
            "label": "Context",
            "supporting_copy": "Provides entry context for the current monitor view.",
        },
        "decision": {
            "label": "Decision",
            "supporting_copy": "Highlights items that drive the next action or priority choice.",
        },
        "validation": {
            "label": "Validation",
            "supporting_copy": "Checks whether the current stock-pool structure is trustworthy.",
        },
        "analysis": {
            "label": "Analysis",
            "supporting_copy": "Explains leadership, strength, and market follow-through.",
        },
        "archive": {
            "label": "Archive",
            "supporting_copy": "Preserves snapshots for later comparison and review.",
        },
        "business_cn:context": {
            "label": "\u4e0a\u4e0b\u6587",
            "supporting_copy": "\u7528\u4e8e\u8bf4\u660e\u5f53\u524d\u76d1\u63a7\u89c6\u56fe\u5165\u53e3\u4e0a\u4e0b\u6587\u3002",
        },
        "business_cn:decision": {
            "label": "\u51b3\u7b56",
            "supporting_copy": "\u7528\u4e8e\u7a81\u51fa\u4e0b\u4e00\u6b65\u52a8\u4f5c\u548c\u4f18\u5148\u9009\u62e9\u3002",
        },
        "business_cn:validation": {
            "label": "\u6821\u9a8c",
            "supporting_copy": "\u7528\u4e8e\u786e\u8ba4\u5f53\u524d\u80a1\u7968\u6c60\u7ed3\u6784\u662f\u5426\u53ef\u9760\u3002",
        },
        "business_cn:analysis": {
            "label": "\u5206\u6790",
            "supporting_copy": "\u7528\u4e8e\u8bf4\u660e\u9f99\u5934\u3001\u5f3a\u5ea6\u548c\u540e\u7eed\u6f14\u7ece\u3002",
        },
        "business_cn:archive": {
            "label": "\u5f52\u6863",
            "supporting_copy": "\u7528\u4e8e\u4fdd\u5b58\u5feb\u7167\uff0c\u65b9\u4fbf\u540e\u7eed\u5bf9\u6bd4\u548c\u590d\u76d8\u3002",
        },
    }


def build_page_segment_template_specs() -> dict[str, list[dict[str, object]]]:
    """Return replaceable homepage segment templates above group-level layout."""
    return {
        "default": [
            {
                "segment_key": "header_segment",
                "segment_title": "Home Header Segment",
                "segment_tone": "neutral",
                "role_key": "context",
                "group_keys": [],
            },
            {
                "segment_key": "priority_segment",
                "segment_title": "Priority Segment",
                "segment_tone": "accent",
                "role_key": "decision",
                "group_keys": ["priority_cluster"],
            },
            {
                "segment_key": "analysis_segment",
                "segment_title": "Analysis Segment",
                "segment_tone": "neutral",
                "role_key": "analysis",
                "group_keys": ["followup_cluster", "chart_cluster"],
            },
            {
                "segment_key": "archive_segment",
                "segment_title": "Archive Segment",
                "segment_tone": "neutral",
                "role_key": "archive",
                "group_keys": ["archive_cluster"],
            },
        ],
        "quick_scan": [
            {
                "segment_key": "header_segment",
                "segment_title": "Quick Header Segment",
                "segment_tone": "neutral",
                "role_key": "context",
                "group_keys": [],
            },
            {
                "segment_key": "action_segment",
                "segment_title": "Action Segment",
                "segment_tone": "accent",
                "role_key": "decision",
                "group_keys": ["priority_cluster"],
            },
            {
                "segment_key": "archive_segment",
                "segment_title": "Snapshot Segment",
                "segment_tone": "neutral",
                "role_key": "archive",
                "group_keys": ["archive_cluster"],
            },
        ],
        "business_cn": [
            {
                "segment_key": "header_segment",
                "segment_title": "\u9996\u5c4f\u6bb5\u843d",
                "segment_tone": "neutral",
                "role_key": "context",
                "group_keys": [],
            },
            {
                "segment_key": "priority_segment",
                "segment_title": "\u4f18\u5148\u6bb5\u843d",
                "segment_tone": "accent",
                "role_key": "decision",
                "group_keys": ["priority_cluster"],
            },
            {
                "segment_key": "followup_segment",
                "segment_title": "\u8ddf\u8fdb\u6bb5\u843d",
                "segment_tone": "neutral",
                "role_key": "analysis",
                "group_keys": ["followup_cluster"],
            },
            {
                "segment_key": "chart_segment",
                "segment_title": "\u56fe\u8868\u6bb5\u843d",
                "segment_tone": "accent",
                "role_key": "analysis",
                "group_keys": ["chart_cluster"],
            },
            {
                "segment_key": "archive_segment",
                "segment_title": "\u5f52\u6863\u6bb5\u843d",
                "segment_tone": "neutral",
                "role_key": "archive",
                "group_keys": ["archive_cluster"],
            },
        ],
    }


def build_home_content_group_layout_specs() -> dict[str, list[dict[str, object]]]:
    """Return replaceable grouped homepage body layout metadata."""
    return {
        "default": [
            {
                "group_key": "priority_cluster",
                "group_title": "Priority Cluster",
                "group_tone": "accent",
                "role_key": "decision",
                "sections": [
                    "today_priority_summary",
                    "stock_pool_health",
                    "next_session_action",
                ],
            },
            {
                "group_key": "followup_cluster",
                "group_title": "Follow-up Cluster",
                "group_tone": "neutral",
                "role_key": "analysis",
                "sections": [
                    "strongest_sector",
                    "leader_summary",
                    "latest_alerts",
                ],
            },
            {
                "group_key": "chart_cluster",
                "group_title": "Chart Cluster",
                "group_tone": "accent",
                "role_key": "analysis",
                "sections": [
                    "sector_strength",
                    "top_movers",
                ],
            },
            {
                "group_key": "archive_cluster",
                "group_title": "Archive Cluster",
                "group_tone": "neutral",
                "role_key": "archive",
                "sections": [
                    "saved_batches",
                ],
            },
        ],
        "quick_scan": [
            {
                "group_key": "priority_cluster",
                "group_title": "Quick Priority Cluster",
                "group_tone": "accent",
                "role_key": "decision",
                "sections": [
                    "today_priority_summary",
                    "next_session_action",
                    "stock_pool_health",
                ],
            },
            {
                "group_key": "archive_cluster",
                "group_title": "Snapshot Archive",
                "group_tone": "neutral",
                "role_key": "archive",
                "sections": [
                    "saved_batches",
                ],
            },
        ],
        "business_cn": [
            {
                "group_key": "priority_cluster",
                "group_title": "\u4f18\u5148\u5206\u7ec4",
                "group_tone": "accent",
                "role_key": "decision",
                "sections": [
                    "today_priority_summary",
                    "stock_pool_health",
                    "next_session_action",
                ],
            },
            {
                "group_key": "followup_cluster",
                "group_title": "\u8ddf\u8fdb\u5206\u7ec4",
                "group_tone": "neutral",
                "role_key": "analysis",
                "sections": [
                    "latest_alerts",
                    "strongest_sector",
                    "leader_summary",
                ],
            },
            {
                "group_key": "chart_cluster",
                "group_title": "\u56fe\u8868\u5206\u7ec4",
                "group_tone": "accent",
                "role_key": "analysis",
                "sections": [
                    "sector_strength",
                    "top_movers",
                ],
            },
            {
                "group_key": "archive_cluster",
                "group_title": "\u5feb\u7167\u5f52\u6863",
                "group_tone": "neutral",
                "role_key": "archive",
                "sections": [
                    "saved_batches",
                ],
            },
        ],
    }


def build_content_panel_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable wrapper metadata for content sections and detail areas."""
    intro_spec = build_intro_panel_style_spec(copy_variant)
    base_spec = {
        "section_label": str(intro_spec.get("section_intro_label", "content section")),
        "detail_label": str(intro_spec.get("content_detail_label", "content details")),
        "group_label": str(intro_spec.get("group_intro_label", "content group")),
        "segment_label": str(intro_spec.get("segment_intro_label", "page segment")),
        "section_title_label": "section",
        "section_supporting_copy": str(
            intro_spec.get("section_supporting_copy", "Structured monitor summary")
        ),
        "compact_section_supporting_copy": str(
            intro_spec.get("compact_section_supporting_copy", "Content summary")
        ),
        "group_supporting_copy": str(
            intro_spec.get("group_supporting_copy", "Related homepage sections stay grouped here")
        ),
        "compact_group_supporting_copy": str(
            intro_spec.get("compact_group_supporting_copy", "Grouped homepage sections")
        ),
        "role_label": "business role",
        "role_prefix": "Role",
        "segment_supporting_copy": str(
            intro_spec.get(
                "segment_supporting_copy",
                "Related homepage groups stay together in this segment",
            )
        ),
        "compact_segment_supporting_copy": str(
            intro_spec.get("compact_segment_supporting_copy", "Homepage segment")
        ),
        "grouped_detail_body": "Grouped detail rows",
        "table_detail_body": "Formatted content table",
        "detail_supporting_copy": "Review grouped details below",
        "compact_detail_supporting_copy": "Grouped details",
        "empty_state_supporting_copy": "Content rows will appear here when available.",
        "default_tone": str(intro_spec.get("default_tone", "neutral")),
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "section_title_label": "\u677f\u5757",
            "detail_label": "\u5185\u5bb9\u660e\u7ec6",
            "role_label": "\u4e1a\u52a1\u89d2\u8272",
            "role_prefix": "\u89d2\u8272",
            "grouped_detail_body": "\u5206\u7ec4\u660e\u7ec6",
            "table_detail_body": "\u683c\u5f0f\u5316\u5185\u5bb9\u8868",
            "detail_supporting_copy": "\u8bf7\u7ee7\u7eed\u67e5\u770b\u4e0b\u65b9\u5206\u7ec4\u660e\u7ec6",
            "compact_detail_supporting_copy": "\u5206\u7ec4\u660e\u7ec6",
            "empty_state_supporting_copy": "\u6709\u6548\u5185\u5bb9\u51fa\u73b0\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u3002",
        }
    )
    return localized_spec


def build_metric_group_style_spec(copy_variant: str = "default") -> dict[str, str]:
    """Return replaceable wrapper metadata for metric-group sections."""
    base_spec = {
        "default_label": "Metric Row",
        "health_metrics_body": "Health metrics",
        "summary_metrics_body": "Summary metrics",
        "default_supporting_copy": "Top-line values",
        "compact_supporting_copy": "Compact metric strip",
        "default_tone": "neutral",
    }
    if copy_variant != "business_cn":
        return base_spec
    localized_spec = dict(base_spec)
    localized_spec.update(
        {
            "default_label": "\u6307\u6807\u884c",
            "health_metrics_body": "\u5065\u5eb7\u6307\u6807",
            "summary_metrics_body": "\u6458\u8981\u6307\u6807",
            "default_supporting_copy": "\u9876\u5c42\u5173\u952e\u6570\u503c",
            "compact_supporting_copy": "\u7d27\u51d1\u6307\u6807\u6761",
        }
    )
    return localized_spec


def build_kpi_value_format_spec() -> dict[str, dict[str, object]]:
    """Return replaceable formatting rules for KPI metric values."""
    return {
        "timestamp": {
            "empty_value": "No data",
            "datetime_format": "%Y-%m-%d %H:%M",
        },
        "count": {
            "empty_value": "0",
            "thousands_separator": True,
        },
        "percent_1": {
            "empty_value": "0.0%",
            "decimals": 1,
            "suffix": "%",
        },
        "signed_percent_1": {
            "empty_value": "0.0%",
            "decimals": 1,
            "suffix": "%",
            "show_plus": True,
        },
        "default": {
            "empty_value": "-",
        },
    }


def build_display_field_registry() -> dict[str, list[dict[str, str]]]:
    """Return reusable display-field specs for tables and detail rows."""
    return {
        "sector_strength_table": [
            {
                "key": "sector",
                "label": "Sector",
            },
            {
                "key": "avg_pct_chg",
                "label": "Avg Change",
                "format_key": "signed_percent_1",
            },
            {
                "key": "stock_count",
                "label": "Stock Count",
                "format_key": "count",
            },
        ],
        "top_movers_table": [
            {
                "key": "name",
                "label": "Name",
            },
            {
                "key": "pct_chg",
                "label": "Change",
                "format_key": "signed_percent_1",
            },
            {
                "key": "sector",
                "label": "Sector",
            },
        ],
        "strongest_sector_detail": [
            {
                "key": "sector",
                "label": "Sector",
                "prefix": "Leading group: ",
            },
            {
                "key": "avg_pct_chg",
                "label": "Avg Change",
                "format_key": "signed_percent_1",
            },
        ],
        "leader_summary_detail": [
            {
                "key": "leader_type",
                "label": "Leader Type",
            },
            {
                "key": "name",
                "label": "Name",
            },
        ],
        "latest_alerts_detail": [
            {
                "key": "timestamp",
                "label": "Timestamp",
                "format_key": "timestamp",
            },
            {
                "key": "alert_type",
                "label": "Alert Type",
            },
            {
                "key": "message",
                "label": "Message",
            },
        ],
        "saved_batches_detail": [
            {
                "key": "timestamp",
                "label": "Timestamp",
                "format_key": "timestamp",
            },
        ],
        "next_session_action_metrics": [
            {
                "key": "core_count",
                "label": "Core Count",
                "format_key": "count",
            },
            {
                "key": "candidate_count",
                "label": "Candidate Count",
                "format_key": "count",
            },
            {
                "key": "avoid_count",
                "label": "Avoid Count",
                "format_key": "count",
            },
        ],
    }


def build_health_group_specs() -> dict[str, object]:
    """Return reusable group specs for stock-pool health detail sections."""
    return {
        "issue_groups": [
            {
                "value_key": "unknown_sectors",
                "label_key": "unknown_sectors",
                "fallback_label": "Unknown Sectors",
            },
            {
                "value_key": "unknown_chain_groups",
                "label_key": "unknown_chain_groups",
                "fallback_label": "Unknown Chain Groups",
            },
            {
                "value_key": "unknown_markets",
                "label_key": "unknown_markets",
                "fallback_label": "Unknown Markets",
            },
            {
                "value_key": "unknown_pool_types",
                "label_key": "unknown_pool_types",
                "fallback_label": "Unknown Pool Types",
            },
        ],
        "suggestion_groups": [
            {
                "value_key": "unknown_sector_suggestions",
                "item_label": "sector",
            },
            {
                "value_key": "unknown_chain_group_suggestions",
                "item_label": "chain-group",
            },
            {
                "value_key": "unknown_market_suggestions",
                "item_label": "market",
            },
            {
                "value_key": "unknown_pool_type_suggestions",
                "item_label": "pool-type",
            },
        ],
        "group_titles": {
            "duplicate_title": "Duplicate Codes",
            "issue_title": "Validation Issues",
            "suggestion_title": "Suggested Matches",
            "structure_title": "Structure Counts",
            "comparison_title": "Structure Comparison",
            "hint_title": "Health Hints",
        },
        "detail_sections": [
            {
                "title_key": "duplicate_title",
                "rows_key": "duplicate_rows",
            },
            {
                "title_key": "issue_title",
                "rows_key": "issue_rows",
            },
            {
                "title_key": "suggestion_title",
                "rows_key": "suggestion_rows",
            },
            {
                "title_key": "structure_title",
                "rows_key": "structure_rows",
            },
            {
                "title_key": "comparison_title",
                "rows_key": "comparison_rows",
            },
            {
                "title_key": "hint_title",
                "rows_key": "hint_rows",
            },
        ],
    }


def build_health_meta_specs() -> list[dict[str, str]]:
    """Return reusable meta-row specs for stock-pool health auxiliary fields."""
    return [
        {
            "value_key": "risk_label",
            "label_key": "risk_level",
            "fallback_label": "Risk Level",
        },
        {
            "value_key": "source_path",
            "label_key": "source_path",
            "fallback_label": "Source",
        },
        {
            "value_key": "registered_sectors",
            "label_key": "registered_sectors",
            "fallback_label": "Registered Sectors",
            "value_mode": "count",
        },
        {
            "value_key": "registered_chain_groups",
            "label_key": "registered_chain_groups",
            "fallback_label": "Registered Chain Groups",
            "value_mode": "count",
        },
        {
            "value_key": "registered_markets",
            "label_key": "registered_markets",
            "fallback_label": "Registered Markets",
            "value_mode": "count",
        },
        {
            "value_key": "registered_pool_types",
            "label_key": "registered_pool_types",
            "fallback_label": "Registered Pool Types",
            "value_mode": "count",
        },
    ]


def build_health_info_block_specs() -> list[dict[str, object]]:
    """Return reusable render-block specs for stock-pool health information areas."""
    return [
        {
            "block_key": "meta_rows",
            "block_type": "meta_grid",
        },
        {
            "block_key": "detail_sections",
            "block_type": "grouped_text_sections",
        },
    ]


def build_grouped_summary_info_block_specs() -> list[dict[str, object]]:
    """Return reusable render-block specs for grouped summary information areas."""
    return [
        {
            "block_key": "detail_sections",
            "block_type": "grouped_text_sections",
        },
    ]


def build_panel_container_style_spec() -> dict[str, str]:
    """Return replaceable surface styles for dashboard panel containers."""
    return {
        "background": "#f7f4ea",
        "border": "#1f1f1f",
        "text_color": "#1f1f1f",
        "muted_text_color": "#5b564d",
        "accent_background": "#efe4bf",
        "shadow": "4px 4px 0 #1f1f1f",
        "radius": "18px",
        "padding": "14px 16px",
        "tone_accent_border": "#c87b2a",
        "tone_warning_border": "#b24d3f",
        "tone_success_border": "#4f7a46",
        "tone_error_border": "#8f3b2f",
        "tone_info_border": "#3f6f88",
        "tone_neutral_border": "#1f1f1f",
    }


def build_semantic_signal_style_spec() -> dict[str, str]:
    """Return replaceable A-share semantic colors for sentiment display."""
    return {
        "positive": "#d93025",
        "negative": "#188038",
        "neutral": "#b06000",
    }


def build_view_mode_specs() -> dict[str, dict[str, str]]:
    """Return replaceable explanatory copy for dashboard view modes."""
    return {
        "default": {
            "title": "Research View",
            "tone": "neutral",
            "summary_label": "view mode",
            "body": "Balanced research layout for main line, structure health, sector context, and follow-up review.",
            "supporting_copy": "Use this mode when you want the fuller analysis path.",
        },
        "compact": {
            "title": "Quick Scan View",
            "tone": "accent",
            "summary_label": "view mode",
            "body": "Fast first-screen layout for KPI, next-session action, pool health, and latest alerts.",
            "supporting_copy": "Use this mode when you want a quicker decision-support scan.",
        },
        "business_cn": {
            "title": "\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe",
            "tone": "accent",
            "summary_label": "\u89c6\u56fe\u6a21\u5f0f",
            "body": "\u4f18\u5148\u663e\u793a\u76d1\u63a7\u6c60\u5065\u5eb7\u3001\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u548c\u6700\u65b0\u63d0\u9192\uff0c\u66f4\u9002\u5408\u4e2d\u6587\u4e1a\u52a1\u67e5\u770b\u8def\u5f84\u3002",
            "supporting_copy": "\u9002\u5408\u5148\u770b\u5c31\u7eea\u5ea6\u4e0e\u52a8\u4f5c\u7ed3\u8bba\uff0c\u518d\u5f80\u4e0b\u67e5\u770b\u677f\u5757\u4e0e\u56fe\u8868\u3002",
        },
    }


def build_task_template_specs() -> dict[str, dict[str, object]]:
    """Return explicit business task templates for dashboard modes."""
    return {
        "default": {
            "label": "Intraday Tracking",
            "summary_label": "task template",
            "body": "Best for following the evolving main line and validating whether strength is holding.",
            "focus_points": [
                "main line continuity",
                "leader follow-through",
                "alert change balance",
            ],
        },
        "compact": {
            "label": "Open Quick Scan",
            "summary_label": "task template",
            "body": "Best for deciding what deserves immediate attention near the open.",
            "focus_points": [
                "next-session action",
                "pool health check",
                "latest alerts first",
            ],
        },
        "business_cn": {
            "label": "\u6536\u76d8\u590d\u76d8",
            "summary_label": "\u4efb\u52a1\u6a21\u677f",
            "body": "\u66f4\u9002\u5408\u7528\u6765\u505a\u4e2d\u6587\u4e1a\u52a1\u590d\u76d8\uff0c\u5148\u786e\u8ba4\u6821\u9a8c\u4e0e\u52a8\u4f5c\uff0c\u518d\u56de\u770b\u677f\u5757\u4e0e\u56fe\u8868\u3002",
            "focus_points": [
                "\u6821\u9a8c\u72b6\u6001",
                "\u52a8\u4f5c\u7ed3\u8bba",
                "\u5f52\u6863\u5feb\u7167",
            ],
        },
    }


def build_time_phase_specs() -> dict[str, dict[str, object]]:
    """Return explicit market-time phase templates for dashboard modes."""
    return {
        "default": {
            "label": "Intraday Phase",
            "summary_label": "time phase",
            "body": "Designed for live-session tracking while sector leadership and alert balance are still evolving.",
            "focus_points": [
                "leadership continuity",
                "intraday drift",
                "follow-through confirmation",
            ],
            "pinned_sections": [],
            "deferred_sections": [],
            "hidden_sections": [],
        },
        "compact": {
            "label": "Post-open Scan",
            "summary_label": "time phase",
            "body": "Designed for the opening window when rapid prioritization matters most.",
            "focus_points": [
                "opening strength",
                "early alerts",
                "quick validation",
            ],
            "pinned_sections": ["latest_alerts", "next_session_action"],
            "deferred_sections": ["saved_batches"],
            "hidden_sections": [],
        },
        "business_cn": {
            "label": "\u6536\u76d8\u9636\u6bb5",
            "summary_label": "\u65f6\u6bb5\u6a21\u677f",
            "body": "\u9002\u5408\u6536\u76d8\u540e\u505a\u7ed3\u6784\u590d\u76d8\u4e0e\u52a8\u4f5c\u56de\u987e\u3002",
            "focus_points": [
                "\u5f53\u65e5\u7ed3\u8bba",
                "\u5feb\u7167\u5bf9\u7167",
                "\u4e0b\u4e00\u65f6\u6bb5\u51c6\u5907",
            ],
            "pinned_sections": ["saved_batches", "stock_pool_health"],
            "deferred_sections": ["sector_strength", "top_movers"],
            "hidden_sections": [],
        },
    }


def build_effective_time_phase_specs(copy_variant: str = "default") -> dict[str, dict[str, object]]:
    """Return localized time-phase specs keyed by real phase state."""
    if copy_variant == "business_cn":
        return {
            "default": {
                "label": "盘中阶段",
                "summary_label": "时段模板",
                "body": "适合盘中持续跟踪主线、龙头延续和提醒平衡。",
                "focus_points": [
                    "龙头延续",
                    "盘中漂移",
                    "跟随确认",
                ],
                "pinned_sections": [],
                "deferred_sections": [],
                "hidden_sections": [],
            },
            "compact": {
                "label": "盘前快扫",
                "summary_label": "时段模板",
                "body": "适合开盘初段先快速确认主线强度、最新提醒和第一轮校验。",
                "focus_points": [
                    "开盘强度",
                    "最新提醒",
                    "快速校验",
                ],
                "pinned_sections": ["latest_alerts", "next_session_action"],
                "deferred_sections": ["saved_batches"],
                "hidden_sections": [],
            },
            "business_cn": {
                "label": "收盘阶段",
                "summary_label": "时段模板",
                "body": "适合收盘后做结构复盘与动作回顾。",
                "focus_points": [
                    "当日结论",
                    "快照对照",
                    "下一时段准备",
                ],
                "pinned_sections": ["saved_batches", "stock_pool_health"],
                "deferred_sections": ["sector_strength", "top_movers"],
                "hidden_sections": [],
            },
        }
    return {
        "default": {
            "label": "Intraday Phase",
            "summary_label": "time phase",
            "body": "Designed for live-session tracking while sector leadership and alert balance are still evolving.",
            "focus_points": [
                "leadership continuity",
                "intraday drift",
                "follow-through confirmation",
            ],
            "pinned_sections": [],
            "deferred_sections": [],
            "hidden_sections": [],
        },
        "compact": {
            "label": "Post-open Scan",
            "summary_label": "time phase",
            "body": "Designed for the opening window when rapid prioritization matters most.",
            "focus_points": [
                "opening strength",
                "early alerts",
                "quick validation",
            ],
            "pinned_sections": ["latest_alerts", "next_session_action"],
            "deferred_sections": ["saved_batches"],
            "hidden_sections": [],
        },
        "business_cn": {
            "label": "Closing Review Phase",
            "summary_label": "time phase",
            "body": "Designed for the late-session replay when structure confirmation and next-session carry-forward matter most.",
            "focus_points": [
                "day-end conclusion",
                "snapshot comparison",
                "next-session preparation",
            ],
            "pinned_sections": ["saved_batches", "stock_pool_health"],
            "deferred_sections": ["sector_strength", "top_movers"],
            "hidden_sections": [],
        },
    }


def build_view_role_strategy_specs() -> dict[str, dict[str, object]]:
    """Return explicit role-emphasis strategies for dashboard view modes."""
    return {
        "default": {
            "primary_roles": ["analysis", "validation"],
            "secondary_roles": ["decision", "archive"],
            "deferred_roles": [],
            "hidden_roles": [],
            "pinned_sections": [],
            "deferred_sections": [],
            "hidden_sections": [],
            "summary_label": "role strategy",
            "body": "Balanced across analysis and validation, with decision and archive still visible.",
        },
        "compact": {
            "primary_roles": ["decision", "validation"],
            "secondary_roles": ["analysis"],
            "deferred_roles": ["analysis"],
            "hidden_roles": ["archive"],
            "pinned_sections": ["next_session_action", "stock_pool_health", "latest_alerts"],
            "deferred_sections": ["strongest_sector", "leader_summary", "sector_strength", "top_movers"],
            "hidden_sections": ["saved_batches"],
            "summary_label": "role strategy",
            "body": "Prioritizes fast decision support and stock-pool trust checks before deeper analysis, while hiding archive-first content.",
        },
        "business_cn": {
            "primary_roles": ["validation", "decision"],
            "secondary_roles": ["analysis", "archive"],
            "deferred_roles": ["archive"],
            "hidden_roles": [],
            "pinned_sections": ["stock_pool_health", "next_session_action", "latest_alerts"],
            "deferred_sections": ["saved_batches"],
            "hidden_sections": [],
            "summary_label": "\u89d2\u8272\u7b56\u7565",
            "body": "\u4f18\u5148\u7a81\u51fa\u6821\u9a8c\u4e0e\u51b3\u7b56\uff0c\u5176\u6b21\u518d\u5c55\u5f00\u5206\u6790\uff0c\u5f52\u6863\u89d2\u8272\u540e\u7f6e\u3002",
        },
    }


def build_view_variant_specs() -> dict[str, dict[str, object]]:
    """Return replaceable dashboard view-variant specs."""
    return {
        "default": {
            "label": "Research View",
            "theme_key": "default",
            "page_layout_key": "default",
            "page_layout": build_page_layout_specs("default"),
            "priority_content_layout_key": "default",
            "content_group_layout_key": "default",
            "page_segment_template_key": "default",
            "kpi_layout_key": "default",
            "view_mode_key": "default",
            "task_template_key": "default",
            "time_phase_key": "default",
            "role_strategy_key": "default",
            "control_band_layout_key": "default",
            "home_header_layout_key": "default",
            "home_header_copy_variant": "default",
            "kpi_copy_variant": "default",
            "surface_copy_variant": "default",
            "content_variant_overrides": {},
        },
        "compact": {
            "label": "Quick Scan View",
            "theme_key": "compact",
            "page_layout_key": "quick_scan",
            "page_layout": build_page_layout_specs("quick_scan"),
            "priority_content_layout_key": "quick_scan",
            "content_group_layout_key": "quick_scan",
            "page_segment_template_key": "quick_scan",
            "kpi_layout_key": "quick_scan",
            "view_mode_key": "compact",
            "task_template_key": "compact",
            "time_phase_key": "compact",
            "role_strategy_key": "compact",
            "control_band_layout_key": "quick_scan",
            "home_header_layout_key": "quick_scan",
            "home_header_copy_variant": "default",
            "kpi_copy_variant": "default",
            "surface_copy_variant": "default",
            "content_variant_overrides": {},
        },
        "business_cn": {
            "label": "\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe",
            "theme_key": "business_cn",
            "page_layout_key": "business_cn",
            "page_layout": build_page_layout_specs("business_cn"),
            "priority_content_layout_key": "business_cn",
            "content_group_layout_key": "business_cn",
            "page_segment_template_key": "business_cn",
            "kpi_layout_key": "business_cn",
            "view_mode_key": "business_cn",
            "task_template_key": "business_cn",
            "time_phase_key": "business_cn",
            "role_strategy_key": "business_cn",
            "control_band_layout_key": "business_cn",
            "home_header_layout_key": "business_cn",
            "home_header_copy_variant": "business_cn",
            "kpi_copy_variant": "business_cn",
            "surface_copy_variant": "business_cn",
            "content_variant_overrides": {
                "strongest_sector": "business_cn",
                "stock_pool_health": "business_cn",
                "leader_summary": "business_cn",
                "latest_alerts": "business_cn",
                "saved_batches": "business_cn",
                "next_session_action": "business_cn",
            },
        },
    }


def resolve_dashboard_view_spec(variant_key: str = "default") -> dict[str, object]:
    """Resolve one dashboard view variant into theme and layout metadata."""
    variants = build_view_variant_specs()
    variant = dict(variants.get(variant_key, variants["default"]))
    base_theme = build_theme_spec()
    theme_overrides = {
        "default": {},
        "compact": {
            "page_title": "AI Semi Monitor Compact",
            "app_title": "AI Semi Monitor Compact",
            "layout": "centered",
            "panel_density": "compact",
            "view_selector_label": "View Mode",
            "time_phase_selector_label": "Time Phase",
            "time_phase_auto_label": "Auto",
            "batch_selector_label": "Batch",
        },
        "business_cn": {
            "page_title": "A股AI半导体监控台",
            "app_title": "A股AI半导体监控台",
            "layout": "wide",
            "panel_density": "comfortable",
            "view_selector_label": "视图模式",
            "batch_selector_label": "快照批次",
            "caption_template": "数据库: {database_url}",
        },
    }
    theme_key = str(variant.get("theme_key", "default"))
    theme = dict(base_theme)
    theme.update(theme_overrides.get(theme_key, {}))
    if theme_key == "business_cn":
        theme["time_phase_selector_label"] = "时段模式"
        theme["time_phase_auto_label"] = "自动判断"
    return {
        "theme": theme,
        "page_layout_key": str(variant.get("page_layout_key", "default")),
        "priority_content_layout_key": str(
            variant.get("priority_content_layout_key", "default")
        ),
        "content_group_layout_key": str(
            variant.get("content_group_layout_key", "default")
        ),
        "page_segment_template_key": str(
            variant.get("page_segment_template_key", "default")
        ),
        "kpi_layout_key": str(variant.get("kpi_layout_key", "default")),
        "view_mode_key": str(variant.get("view_mode_key", variant_key)),
        "task_template_key": str(variant.get("task_template_key", variant_key)),
        "time_phase_key": str(variant.get("time_phase_key", variant_key)),
        "role_strategy_key": str(variant.get("role_strategy_key", variant_key)),
        "control_band_layout_key": str(variant.get("control_band_layout_key", "default")),
        "home_header_layout_key": str(variant.get("home_header_layout_key", "default")),
        "home_header_copy_variant": str(variant.get("home_header_copy_variant", "default")),
        "control_band_layout": list(
            build_control_band_layout_specs().get(
                str(variant.get("control_band_layout_key", "default")),
                build_control_band_layout_specs()["default"],
            )
        ),
        "home_header_layout": list(
            build_home_header_layout_specs().get(
                str(variant.get("home_header_layout_key", "default")),
                build_home_header_layout_specs()["default"],
            )
        ),
        "priority_content_layout": list(
            build_home_priority_content_layout_specs().get(
                str(variant.get("priority_content_layout_key", "default")),
                build_home_priority_content_layout_specs()["default"],
            )
        ),
        "content_group_layout": [
            {
                "group_key": str(group.get("group_key", "")).strip(),
                "sections": [str(section).strip() for section in list(group.get("sections", []))],
            }
            for group in build_home_content_group_layout_specs().get(
                str(variant.get("content_group_layout_key", "default")),
                build_home_content_group_layout_specs()["default"],
            )
        ],
        "page_segment_template": [
            {
                "segment_key": str(segment.get("segment_key", "")).strip(),
                "segment_title": str(segment.get("segment_title", "")).strip(),
                "segment_tone": str(segment.get("segment_tone", "neutral")).strip() or "neutral",
                "group_keys": [
                    str(group_key).strip()
                    for group_key in list(segment.get("group_keys", []))
                    if str(group_key).strip()
                ],
            }
            for segment in build_page_segment_template_specs().get(
                str(variant.get("page_segment_template_key", "default")),
                build_page_segment_template_specs()["default"],
            )
        ],
        "home_header_style": dict(
            build_home_header_style_spec(
                str(variant.get("home_header_copy_variant", "default"))
            )
        ),
        "view_mode_note": dict(
            build_view_mode_specs().get(
                str(variant.get("view_mode_key", variant_key)),
                build_view_mode_specs()["default"],
            )
        ),
        "task_template": dict(
            build_task_template_specs().get(
                str(variant.get("task_template_key", variant_key)),
                build_task_template_specs()["default"],
            )
        ),
        "time_phase": dict(
            build_time_phase_specs().get(
                str(variant.get("time_phase_key", variant_key)),
                build_time_phase_specs()["default"],
            )
        ),
        "role_strategy": dict(
            build_view_role_strategy_specs().get(
                str(variant.get("role_strategy_key", variant_key)),
                build_view_role_strategy_specs()["default"],
            )
        ),
        "kpi_summary_layout": dict(
            build_kpi_summary_layout_specs().get(
                str(variant.get("kpi_layout_key", "default")),
                build_kpi_summary_layout_specs()["default"],
            )
        ),
        "kpi_copy_variant": str(variant.get("kpi_copy_variant", "default")),
        "surface_copy_variant": str(variant.get("surface_copy_variant", "default")),
        "page_layout": list(variant["page_layout"]),
        "content_variant_overrides": dict(variant.get("content_variant_overrides", {})),
    }


def build_kpi_card_specs(copy_variant: str = "default") -> list[dict[str, object]]:
    """Return replaceable KPI card presentation specs."""
    specs = [
        {
            "label": "Latest Batch",
            "value_key": "latest_timestamp",
            "empty_value": "No data",
            "card_type": "text",
            "format_key": "timestamp",
            "style": "neutral",
            "tone": "neutral",
        },
        {
            "label": "Data Status",
            "value_key": "quote_status_summary",
            "empty_value": "Quote status: unavailable.",
            "card_type": "text",
            "format_key": "default",
            "style": "info",
            "tone": "info",
            "caption": "Current quote-source readiness state",
            "value_max_length": 38,
            "copy_variant": "default",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "label": "数据状态",
                    "caption": "当前行情来源就绪状态",
                    "value_max_length": 24,
                },
                "compact": {
                    "label": "Data Mode",
                    "caption": "Short quote-source status",
                    "value_max_length": 22,
                },
                "priority": {
                    "label": "Data Status",
                    "caption": "Priority quote-source status",
                    "tone": "warning",
                    "value_max_length": 30,
                },
            },
        },
        {
            "label": "Main-Line View",
            "value_key": "mainline_summary",
            "empty_value": "No main-line summary",
            "card_type": "text",
            "format_key": "default",
            "style": "accent",
            "tone": "accent",
            "caption": "Top-line market leadership conclusion",
            "value_max_length": 46,
            "copy_variant": "default",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "label": "\u4e3b\u7ebf\u7ed3\u8bba",
                    "caption": "\u9996\u5c4f\u5f53\u524d\u5e02\u573a\u4e3b\u7ebf\u6458\u8981",
                    "value_max_length": 30,
                },
                "compact": {
                    "label": "Main Line",
                    "caption": "Short main-line cue",
                    "value_max_length": 24,
                },
                "priority": {
                    "label": "Main-Line View",
                    "caption": "Priority main-line conclusion",
                    "tone": "warning",
                    "value_max_length": 38,
                },
            },
        },
        {
            "label": "Pool Drift",
            "value_key": "stock_pool_drift_summary",
            "empty_value": "No drift summary",
            "card_type": "text",
            "format_key": "default",
            "style": "info",
            "tone": "info",
            "caption": "Top-line stock-pool structure drift cue",
            "value_max_length": 42,
            "copy_variant": "default",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "label": "\u76d1\u63a7\u6c60\u6f02\u79fb",
                    "caption": "\u9996\u5c4f\u76d1\u63a7\u6c60\u7ed3\u6784\u504f\u79fb\u63d0\u793a",
                    "value_max_length": 28,
                },
                "compact": {
                    "label": "Pool Bias",
                    "caption": "Short drift cue",
                    "value_max_length": 24,
                },
                "priority": {
                    "label": "Pool Drift",
                    "caption": "Priority structure drift cue",
                    "tone": "warning",
                    "value_max_length": 36,
                },
            },
        },
        {
            "label": "Risk State",
            "value_key": "risk_summary",
            "empty_value": "No risk summary",
            "card_type": "text",
            "format_key": "default",
            "style": "warning",
            "tone": "warning",
            "caption": "Top-line risk balance conclusion",
            "value_max_length": 42,
            "copy_variant": "default",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "label": "\u98ce\u9669\u72b6\u6001",
                    "caption": "\u9996\u5c4f\u5f53\u524d\u98ce\u9669\u6982\u8981",
                    "value_max_length": 28,
                },
                "compact": {
                    "label": "Risk",
                    "caption": "Short risk cue",
                    "value_max_length": 22,
                },
                "priority": {
                    "label": "Risk State",
                    "caption": "Priority risk conclusion",
                    "tone": "error",
                    "value_max_length": 34,
                },
            },
        },
        {
            "label": "Positive Alerts",
            "value_key": "positive_alert_count",
            "empty_value": 0,
            "card_type": "numeric",
            "format_key": "count",
            "style": "accent",
            "tone": "accent",
        },
        {
            "label": "Negative Alerts",
            "value_key": "negative_alert_count",
            "empty_value": 0,
            "card_type": "numeric",
            "format_key": "count",
            "style": "warning",
            "tone": "warning",
        },
        {
            "label": "Alert Count",
            "value_key": "alert_count",
            "empty_value": 0,
            "card_type": "numeric",
            "format_key": "count",
            "style": "neutral",
            "tone": "neutral",
        },
    ]
    if copy_variant != "business_cn":
        return specs
    localized_labels = [
        "\u6700\u65b0\u6279\u6b21",
        "\u6570\u636e\u72b6\u6001",
        "\u4e3b\u7ebf\u7ed3\u8bba",
        "\u76d1\u63a7\u6c60\u6f02\u79fb",
        "\u98ce\u9669\u72b6\u6001",
        "\u6b63\u5411\u63d0\u9192",
        "\u8d1f\u5411\u63d0\u9192",
        "\u63d0\u9192\u603b\u6570",
    ]
    localized_specs: list[dict[str, object]] = []
    for spec, localized_label in zip(specs, localized_labels):
        localized_spec = dict(spec)
        localized_spec["label"] = localized_label
        localized_spec["copy_variant"] = (
            "business_cn"
            if str(spec.get("value_key", "")).strip()
            in {
                "quote_status_summary",
                "mainline_summary",
                "stock_pool_drift_summary",
                "risk_summary",
            }
            else str(spec.get("copy_variant", "default"))
        )
        localized_specs.append(localized_spec)
    return localized_specs


def build_kpi_summary_layout_specs() -> dict[str, dict[str, object]]:
    """Return replaceable homepage summary-card layout specs for KPI ordering."""
    return {
        "default": {
            "card_order": [
                "latest_timestamp",
                "quote_status_summary",
                "mainline_summary",
                "stock_pool_drift_summary",
                "risk_summary",
                "positive_alert_count",
                "negative_alert_count",
                "alert_count",
            ],
            "card_variant_overrides": {},
        },
        "quick_scan": {
            "card_order": [
                "mainline_summary",
                "quote_status_summary",
                "risk_summary",
                "stock_pool_drift_summary",
                "latest_timestamp",
                "positive_alert_count",
                "negative_alert_count",
                "alert_count",
            ],
            "card_variant_overrides": {
                "mainline_summary": "priority",
                "quote_status_summary": "compact",
                "risk_summary": "priority",
                "stock_pool_drift_summary": "compact",
            },
        },
        "business_cn": {
            "card_order": [
                "mainline_summary",
                "quote_status_summary",
                "stock_pool_drift_summary",
                "risk_summary",
                "latest_timestamp",
                "positive_alert_count",
                "negative_alert_count",
                "alert_count",
            ],
            "card_variant_overrides": {
                "mainline_summary": "business_cn",
                "quote_status_summary": "business_cn",
                "stock_pool_drift_summary": "business_cn",
                "risk_summary": "business_cn",
            },
        },
    }


def build_chart_specs() -> dict[str, dict[str, object]]:
    """Return replaceable chart presentation specs."""
    display_fields = build_display_field_registry()
    return {
        "sector_strength": {
            "title": "Sector Strength",
            "copy_variant": "default",
            "chart_type": "bar",
            "tone": "accent",
            "role_key": "analysis",
            "module_priority": 5,
            "data_key": "sector_chart",
            "table_key": "sector_cards",
            "display_fields": display_fields["sector_strength_table"],
            "x_key": "sector",
            "y_key": "avg_pct_chg",
            "x_axis_label": "Sector",
            "y_axis_label": "Avg Change",
            "palette": "accent",
            "empty_message": "No sector strength data available yet.",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u677f\u5757\u5f3a\u5ea6",
                    "display_fields": [
                        {
                            "key": "sector",
                            "label": "\u677f\u5757",
                        },
                        {
                            "key": "avg_pct_chg",
                            "label": "\u5e73\u5747\u6da8\u8dcc",
                            "format_key": "signed_percent_1",
                        },
                        {
                            "key": "stock_count",
                            "label": "\u80a1\u7968\u6570",
                            "format_key": "count",
                        },
                    ],
                    "x_axis_label": "\u677f\u5757",
                    "y_axis_label": "\u5e73\u5747\u6da8\u8dcc",
                    "empty_message": "\u6682\u65f6\u8fd8\u6ca1\u6709\u677f\u5757\u5f3a\u5ea6\u6570\u636e\u3002",
                },
            },
        },
        "top_movers": {
            "title": "Top Movers",
            "copy_variant": "default",
            "chart_type": "bar",
            "tone": "warning",
            "role_key": "analysis",
            "module_priority": 6,
            "data_key": "top_mover_chart",
            "table_key": "top_movers",
            "display_fields": display_fields["top_movers_table"],
            "x_key": "name",
            "y_key": "pct_chg",
            "x_axis_label": "Name",
            "y_axis_label": "Change",
            "palette": "warning",
            "empty_message": "No latest snapshot data available yet.",
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u9886\u6da8\u4e2a\u80a1",
                    "display_fields": [
                        {
                            "key": "name",
                            "label": "\u540d\u79f0",
                        },
                        {
                            "key": "pct_chg",
                            "label": "\u6da8\u8dcc\u5e45",
                            "format_key": "signed_percent_1",
                        },
                        {
                            "key": "sector",
                            "label": "\u677f\u5757",
                        },
                    ],
                    "x_axis_label": "\u540d\u79f0",
                    "y_axis_label": "\u6da8\u8dcc\u5e45",
                    "empty_message": "\u6682\u65f6\u8fd8\u6ca1\u6709\u6700\u65b0\u6279\u6b21\u6570\u636e\u3002",
                },
            },
        },
    }


def build_content_section_specs() -> dict[str, dict[str, object]]:
    """Return replaceable content-section presentation specs."""
    display_fields = build_display_field_registry()
    health_groups = build_health_group_specs()
    health_meta = build_health_meta_specs()
    health_info_blocks = build_health_info_block_specs()
    grouped_summary_info_blocks = build_grouped_summary_info_block_specs()
    return {
        "today_priority_summary": {
            "title": "Today Priority Summary",
            "data_key": "today_priority_summary",
            "action_focus_hint": "Check today's core summary, one-line advice, and watchlist first.",
            "action_focus_anchor_field": "First field: summary date, priority count, and watch groups.",
            "action_focus_anchor_group": "First group: core summary and watchlist rows.",
            "action_focus_anchor_conclusion": "First conclusion: what should be read first today.",
            "render_type": "today_priority_grouped",
            "tone": "accent",
            "role_key": "decision",
            "module_priority": 2,
            "copy_variant": "default",
            "empty_message": "No daily priority summary available yet.",
            "labels": {
                "shown_items": "Priority Items",
                "watch_group_count": "Watch Groups",
                "badge_template": "{date} | {shown}/{total} priority items",
                "core_section_title": "Core Summary",
                "advice_section_title": "One-line Advice",
                "conclusion_section_title": "Daily Conclusion",
                "tips_section_title": "Action Tips",
                "read_order_section_title": "Reading Order",
                "watch_section_title": "Watchlist",
                "action_section_title": "Suggested Actions",
                "channel_section_title": "Priority Channel",
                "source_batch_label": "Source Batch",
                "impact_summary_label": "Impact Mix",
                "filter_mode_label": "Filter Mode",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "当日优先摘要",
                    "action_focus_hint": "先看核心摘要、一句话建议和重点观察名单。",
                    "action_focus_anchor_field": "先看字段：日期、高优先级条数和观察分组数。",
                    "action_focus_anchor_group": "先看分组：核心摘要和重点观察名单。",
                    "action_focus_anchor_conclusion": "先看结论：今天最应该先读什么。",
                    "labels": {
                        "shown_items": "高优先级条数",
                        "watch_group_count": "观察分组数",
                        "badge_template": "{date} | 已筛出 {shown}/{total} 条高优先级",
                        "core_section_title": "核心摘要",
                        "advice_section_title": "一句话建议",
                        "conclusion_section_title": "当日结论",
                        "tips_section_title": "操作提示",
                        "read_order_section_title": "阅读顺序",
                        "watch_section_title": "重点观察名单",
                        "action_section_title": "建议动作",
                        "channel_section_title": "优先级通道",
                        "source_batch_label": "来源批次",
                        "impact_summary_label": "影响分布",
                        "filter_mode_label": "过滤模式",
                    },
                },
            },
            "info_block_specs": grouped_summary_info_blocks,
            "summary_metrics": [
                {
                    "label_key": "shown_items",
                    "value_key": "shown_items",
                    "format_key": "count",
                },
                {
                    "label_key": "watch_group_count",
                    "value_key": "watch_group_count",
                    "format_key": "count",
                },
            ],
        },
        "strongest_sector": {
            "title": "Strongest Sector",
            "data_key": "strongest_sector_summary",
            "action_focus_hint": "Check the leading sector name, average change, and member count first.",
            "action_focus_anchor_field": "First field: sector name and average change.",
            "action_focus_anchor_group": "First group: sector detail rows.",
            "action_focus_anchor_conclusion": "First conclusion: whether this sector is still the clearest main line.",
            "render_type": "spotlight_summary",
            "tone": "accent",
            "role_key": "analysis",
            "module_priority": 4,
            "copy_variant": "default",
            "empty_message": "No sector summary available yet.",
            "labels": {
                "avg_pct_chg": "Avg Change",
                "stock_count": "Stock Count",
                "detail_prefix": "Leading group",
                "detail_section_title": "Sector Details",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u6700\u5f3a\u677f\u5757",
                    "action_focus_hint": "\u5148\u770b\u9886\u6da8\u677f\u5757\u540d\u79f0\u3001\u5e73\u5747\u6da8\u8dcc\u548c\u6210\u5206\u80a1\u6570\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u677f\u5757\u540d\u79f0\u548c\u5e73\u5747\u6da8\u8dcc\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u677f\u5757\u660e\u7ec6\u884c\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u8fd9\u4e2a\u677f\u5757\u662f\u5426\u4ecd\u662f\u6700\u6e05\u6670\u7684\u4e3b\u7ebf\u3002",
                    "labels": {
                        "avg_pct_chg": "\u5e73\u5747\u6da8\u8dcc",
                        "stock_count": "\u6210\u5206\u80a1\u6570",
                        "detail_prefix": "\u9886\u6da8\u677f\u5757",
                        "detail_section_title": "\u677f\u5757\u660e\u7ec6",
                    },
                    "display_fields": [
                        {
                            "key": "sector",
                            "label": "\u677f\u5757",
                            "prefix": "\u9886\u6da8\u677f\u5757: ",
                        },
                        {
                            "key": "avg_pct_chg",
                            "label": "\u5e73\u5747\u6da8\u8dcc",
                            "format_key": "signed_percent_1",
                        },
                    ],
                },
            },
            "display_fields": display_fields["strongest_sector_detail"],
            "info_block_specs": grouped_summary_info_blocks,
            "detail_layout": {
                "item_prefix": "",
                "separator": " | ",
            },
            "summary_metrics": [
                {
                    "label_key": "avg_pct_chg",
                    "value_key": "avg_pct_chg",
                    "format_key": "signed_percent_1",
                },
                {
                    "label_key": "stock_count",
                    "value_key": "stock_count",
                    "format_key": "count",
                },
            ],
        },
        "stock_pool_health": {
            "title": "Stock Pool Health",
            "data_key": "stock_pool_health",
            "action_focus_hint": "Check risk level, change tags, and health hints first.",
            "action_focus_anchor_field": "First field: risk level and change tags.",
            "action_focus_anchor_group": "First group: health hints and structure comparison.",
            "action_focus_anchor_conclusion": "First conclusion: whether the pool is safe enough to trust today.",
            "render_type": "health_summary",
            "role_key": "validation",
            "module_priority": 1,
            "copy_variant": "default",
            "empty_message": "No stock-pool validation summary available yet.",
            "labels": {
                "record_count": "Tracked Stocks",
                "hint_count": "Hint Count",
                "duplicate_count": "Duplicate Count",
                "risk_level": "Risk Level",
                "source_path": "Source",
                "duplicate_codes": "Duplicate Codes",
                "unknown_sectors": "Unknown Sectors",
                "unknown_chain_groups": "Unknown Chain Groups",
                "unknown_markets": "Unknown Markets",
                "unknown_pool_types": "Unknown Pool Types",
                "registered_sectors": "Registered Sectors",
                "registered_chain_groups": "Registered Chain Groups",
                "registered_markets": "Registered Markets",
                "registered_pool_types": "Registered Pool Types",
                "suggested_matches": "Suggested Matches",
                "top_sector_counts": "Top Sectors",
                "top_chain_group_counts": "Top Chain Groups",
                "top_pool_type_counts": "Top Pool Types",
                "sector_counts": "Sector Counts",
                "chain_group_counts": "Chain-group Counts",
                "pool_type_counts": "Pool-type Counts",
                "priority_counts": "Priority Counts",
                "structure_comparison": "Structure Comparison",
                "comparison_tags": "Change Tags",
                "comparison_tag_groups": "Change Groups",
                "comparison_highlight_summary": "Change Highlight",
                "comparison_summary": "Comparison Summary",
                "comparison_snapshot_path": "Snapshot Path",
                "comparison_baseline_saved_at": "Baseline Saved At",
                "health_hints": "Health Hints",
                "status_line_template": "Status: {status_label} ({status}) | Risk: {risk_label}",
                "badge_text_template": "{status_label} | {risk_label}",
                "none": "none",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u80a1\u7968\u6c60\u5065\u5eb7\u5ea6",
                    "action_focus_hint": "\u5148\u770b\u98ce\u9669\u7b49\u7ea7\u3001\u53d8\u5316\u6807\u7b7e\u548c\u5065\u5eb7\u63d0\u793a\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u98ce\u9669\u7b49\u7ea7\u548c\u53d8\u5316\u6807\u7b7e\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u5065\u5eb7\u63d0\u793a\u4e0e\u7ed3\u6784\u5bf9\u6bd4\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u4eca\u5929\u80a1\u7968\u6c60\u662f\u5426\u8db3\u591f\u53ef\u4fe1\u3002",
                    "labels": {
                        "record_count": "监控股票数",
                        "hint_count": "提示数",
                        "duplicate_count": "重复代码数",
                        "risk_level": "风险等级",
                        "source_path": "来源文件",
                        "duplicate_codes": "重复代码",
                        "unknown_sectors": "未知板块",
                        "unknown_chain_groups": "未知链路分组",
                        "unknown_markets": "未知市场",
                        "unknown_pool_types": "未知池类型",
                        "registered_sectors": "已登记板块数",
                        "registered_chain_groups": "已登记链路分组数",
                        "registered_markets": "已登记市场数",
                        "registered_pool_types": "已登记池类型数",
                        "top_sector_counts": "板块头部统计",
                        "top_chain_group_counts": "链路头部统计",
                        "top_pool_type_counts": "池类型头部统计",
                        "sector_counts": "板块统计",
                        "chain_group_counts": "链路分组统计",
                        "pool_type_counts": "池类型统计",
                        "priority_counts": "优先级统计",
                        "comparison_tags": "变化标签",
                        "comparison_tag_groups": "变化分组",
                        "comparison_highlight_summary": "变化重点",
                        "comparison_summary": "对比摘要",
                        "comparison_snapshot_path": "快照路径",
                        "comparison_baseline_saved_at": "基线保存时间",
                        "health_hints": "健康提示",
                        "status_line_template": "状态：{status_label}（{status}） | 风险：{risk_label}",
                        "badge_text_template": "{status_label} | {risk_label}",
                    },
                    "health_groups": {
                        "group_titles": {
                            "duplicate_title": "重复代码",
                            "issue_title": "校验问题",
                            "suggestion_title": "建议匹配",
                            "structure_title": "结构统计",
                            "comparison_title": "结构对比",
                            "hint_title": "健康提示",
                        },
                    },
                    "status_variants": {
                        "valid": {
                            "status_label": "健康可用",
                            "hint_empty_text": "当前没有结构漂移提示。",
                        },
                        "invalid": {
                            "status_label": "需要处理",
                            "hint_empty_text": "校验问题未清理前，健康提示不会归零。",
                        },
                        "unknown": {
                            "status_label": "状态未知",
                            "hint_empty_text": "当前还没有可用的股票池健康提示。",
                        },
                    },
                    "risk_variants": {
                        "clean": {
                            "label": "正常",
                        },
                        "warning": {
                            "label": "警告",
                        },
                        "blocking": {
                            "label": "阻塞",
                        },
                        "unknown": {
                            "label": "未知",
                        },
                    },
                },
            },
            "summary_metrics": [
                {
                    "label_key": "record_count",
                    "value_key": "record_count",
                    "format_key": "count",
                },
                {
                    "label_key": "hint_count",
                    "value_key": "hint_count",
                    "format_key": "count",
                },
                {
                    "label_key": "duplicate_count",
                    "value_key": "duplicate_count",
                    "format_key": "count",
                },
            ],
            "status_variants": {
                "valid": {
                    "tone": "success",
                    "status_label": "Healthy",
                    "hint_empty_text": "No structural drift hints.",
                },
                "invalid": {
                    "tone": "error",
                    "status_label": "Needs Attention",
                    "hint_empty_text": "Validation failed before health hints were cleared.",
                },
                "unknown": {
                    "tone": "info",
                    "status_label": "Unknown",
                    "hint_empty_text": "No stock-pool health hints available yet.",
                },
            },
            "risk_variants": {
                "clean": {
                    "tone": "success",
                    "label": "CLEAN",
                },
                "warning": {
                    "tone": "warning",
                    "label": "WARNING",
                },
                "blocking": {
                    "tone": "error",
                    "label": "BLOCKING",
                },
                "unknown": {
                    "tone": "info",
                    "label": "UNKNOWN",
                },
            },
            "health_groups": health_groups,
            "health_meta": health_meta,
            "health_info_blocks": health_info_blocks,
        },
        "leader_summary": {
            "title": "Leader Summary",
            "data_key": "leader_summary",
            "action_focus_hint": "Check the leader map and how many leader slots are still active.",
            "action_focus_anchor_field": "First field: active leader names and slot count.",
            "action_focus_anchor_group": "First group: leader detail rows.",
            "action_focus_anchor_conclusion": "First conclusion: whether leadership is still concentrated and intact.",
            "render_type": "leader_grouped",
            "tone": "neutral",
            "role_key": "analysis",
            "module_priority": 5,
            "copy_variant": "default",
            "empty_message": "No leader summary available yet.",
            "labels": {
                "leader_count": "Leader Slots",
                "badge_unit": "leader slot(s)",
                "detail_prefix": "Leader Map",
                "detail_section_title": "Leader Details",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u9f99\u5934\u6458\u8981",
                    "action_focus_hint": "\u5148\u770b\u9f99\u5934\u6620\u5c04\u548c\u4ecd\u5728\u5ef6\u7eed\u7684\u9f99\u5934\u69fd\u4f4d\u6570\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u9f99\u5934\u540d\u5355\u548c\u69fd\u4f4d\u6570\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u9f99\u5934\u660e\u7ec6\u884c\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u9f99\u5934\u662f\u5426\u4ecd\u5728\u96c6\u4e2d\u5ef6\u7eed\u3002",
                    "labels": {
                        "leader_count": "龙头槽位数",
                        "badge_unit": "个龙头槽位",
                        "detail_prefix": "龙头映射",
                        "detail_section_title": "龙头明细",
                    },
                },
            },
            "display_fields": display_fields["leader_summary_detail"],
            "info_block_specs": grouped_summary_info_blocks,
            "detail_layout": {
                "item_prefix": "- ",
                "separator": ": ",
            },
            "summary_metrics": [
                {
                    "label_key": "leader_count",
                    "value_key": "leader_count",
                    "format_key": "count",
                },
            ],
        },
        "latest_alerts": {
            "title": "Latest Alerts",
            "data_key": "latest_alerts",
            "action_focus_hint": "Check the newest alert type, timestamp, and message first.",
            "action_focus_anchor_field": "First field: newest timestamp, alert type, and message.",
            "action_focus_anchor_group": "First group: alert detail rows.",
            "action_focus_anchor_conclusion": "First conclusion: whether the newest alerts change today's priority read.",
            "render_type": "alerts_grouped",
            "tone": "warning",
            "role_key": "analysis",
            "module_priority": 3,
            "copy_variant": "default",
            "columns": ["timestamp", "alert_type", "message"],
            "display_fields": display_fields["latest_alerts_detail"],
            "detail_layout": {
                "item_prefix": "- ",
                "separator": " | ",
            },
            "empty_message": "No latest alerts available yet.",
            "labels": {
                "alert_count": "Alert Rows",
                "badge_unit": "alert row(s)",
                "detail_section_title": "Alert Details",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u6700\u65b0\u63d0\u9192",
                    "action_focus_hint": "\u5148\u770b\u6700\u65b0\u63d0\u9192\u7684\u65f6\u95f4\u3001\u7c7b\u578b\u548c\u5185\u5bb9\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u6700\u65b0\u65f6\u95f4\u3001\u7c7b\u578b\u548c\u5185\u5bb9\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u63d0\u9192\u660e\u7ec6\u884c\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u65b0\u63d0\u9192\u662f\u5426\u6539\u53d8\u4eca\u5929\u7684\u4f18\u5148\u7ea7\u3002",
                    "labels": {
                        "alert_count": "\u63d0\u9192\u6761\u6570",
                        "badge_unit": "\u6761\u63d0\u9192",
                        "detail_section_title": "\u63d0\u9192\u660e\u7ec6",
                    },
                    "display_fields": [
                        {
                            "key": "timestamp",
                            "label": "\u65f6\u95f4",
                            "format_key": "timestamp",
                        },
                        {
                            "key": "alert_type",
                            "label": "\u63d0\u9192\u7c7b\u578b",
                        },
                        {
                            "key": "message",
                            "label": "\u63d0\u9192\u5185\u5bb9",
                        },
                    ],
                },
            },
            "info_block_specs": grouped_summary_info_blocks,
            "summary_metrics": [
                {
                    "label_key": "alert_count",
                    "value_key": "alert_count",
                    "format_key": "count",
                },
            ],
        },
        "saved_batches": {
            "title": "Saved Batches",
            "data_key": "available_batches",
            "action_focus_hint": "Check the latest two snapshot timestamps before comparing structure changes.",
            "action_focus_anchor_field": "First field: the latest two batch timestamps.",
            "action_focus_anchor_group": "First group: batch detail rows.",
            "action_focus_anchor_conclusion": "First conclusion: whether recent snapshots show meaningful structural change.",
            "render_type": "batch_list_grouped",
            "tone": "neutral",
            "role_key": "archive",
            "module_priority": 7,
            "copy_variant": "default",
            "empty_message": "No saved snapshot batches yet.",
            "display_fields": display_fields["saved_batches_detail"],
            "detail_layout": {
                "item_prefix": "- ",
                "separator": " | ",
            },
            "labels": {
                "batch_count": "Saved Batches",
                "badge_unit": "saved batch(es)",
                "detail_section_title": "Batch Details",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u5df2\u4fdd\u5b58\u6279\u6b21",
                    "action_focus_hint": "\u5148\u770b\u6700\u8fd1\u4e24\u4e2a\u5feb\u7167\u65f6\u95f4\uff0c\u518d\u5bf9\u6bd4\u7ed3\u6784\u53d8\u5316\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u6700\u8fd1\u4e24\u4e2a\u5feb\u7167\u65f6\u95f4\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u6279\u6b21\u660e\u7ec6\u884c\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u6700\u8fd1\u5feb\u7167\u662f\u5426\u51fa\u73b0\u5b9e\u8d28\u6027\u53d8\u5316\u3002",
                    "labels": {
                        "batch_count": "\u5df2\u4fdd\u5b58\u6279\u6b21\u6570",
                        "badge_unit": "\u4e2a\u5df2\u4fdd\u5b58\u6279\u6b21",
                        "detail_section_title": "\u6279\u6b21\u660e\u7ec6",
                    },
                    "display_fields": [
                        {
                            "key": "timestamp",
                            "label": "\u6279\u6b21\u65f6\u95f4",
                            "format_key": "timestamp",
                        },
                    ],
                },
            },
            "info_block_specs": grouped_summary_info_blocks,
            "summary_metrics": [
                {
                    "label_key": "batch_count",
                    "value_key": "batch_count",
                    "format_key": "count",
                },
            ],
        },
        "next_session_action": {
            "title": "Next-session Action Summary",
            "data_key": "next_session_action_summary",
            "action_focus_hint": "Check core names, avoid names, and the score-ranked focus rows first.",
            "action_focus_anchor_field": "First field: core names, avoid names, and score rows.",
            "action_focus_anchor_group": "First group: core / candidate / avoid sections.",
            "action_focus_anchor_conclusion": "First conclusion: which names should stay core, candidate, or avoided next session.",
            "render_type": "next_session_action_grouped",
            "tone": "accent",
            "role_key": "decision",
            "module_priority": 2,
            "copy_variant": "default",
            "empty_message": "No next-session action summary available yet.",
            "labels": {
                "core_count": "Core Count",
                "candidate_count": "Candidate Count",
                "avoid_count": "Avoid Count",
                "rule_section_title": "Weight Summary",
                "core_section_title": "Priority Core Watchlist (Score-ranked)",
                "candidate_section_title": "Secondary Candidate Watchlist (Score-ranked)",
                "avoid_section_title": "Risk Avoid List (Score-ranked)",
                "badge_template": "{total} action slot(s) | Core {core} / Candidate {candidate} / Avoid {avoid}",
                "names_row_label": "names",
                "tags_row_label": "tags",
                "scores_row_label": "scores",
                "focus_row_label": "focus",
                "focus_templates": {
                    "stay_with_first": "Stay with {target} leaders first.",
                    "use_as_confirmation": "Use {target} as first confirmation.",
                    "reduce_names_tied_to": "Reduce {target} names.",
                },
                "detail_section_title": "Action Details",
            },
            "copy_variants": {
                "default": {},
                "business_cn": {
                    "title": "\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u6458\u8981",
                    "action_focus_hint": "\u5148\u770b\u6838\u5fc3\u540d\u5355\u3001\u56de\u907f\u540d\u5355\u548c\u6309\u5206\u6570\u6392\u5e8f\u7684\u64cd\u4f5c\u91cd\u70b9\u3002",
                    "action_focus_anchor_field": "\u5148\u770b\u5b57\u6bb5\uff1a\u6838\u5fc3\u540d\u5355\u3001\u56de\u907f\u540d\u5355\u548c\u5206\u6570\u884c\u3002",
                    "action_focus_anchor_group": "\u5148\u770b\u5206\u7ec4\uff1a\u6838\u5fc3 / \u5019\u9009 / \u56de\u907f\u5206\u7ec4\u3002",
                    "action_focus_anchor_conclusion": "\u5148\u770b\u7ed3\u8bba\uff1a\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u8c01\u5e94\u7559\u5728\u6838\u5fc3\u3001\u5019\u9009\u6216\u56de\u907f\u3002",
                    "labels": {
                        "rule_section_title": "权重摘要",
                        "core_section_title": "核心优先观察池（按分数排序）",
                        "candidate_section_title": "次级候选观察池（按分数排序）",
                        "avoid_section_title": "风险回避名单（按分数排序）",
                        "badge_template": "共 {total} 个动作槽位 | 核心 {core} / 候选 {candidate} / 回避 {avoid}",
                        "names_row_label": "名单",
                        "tags_row_label": "信号标签",
                        "scores_row_label": "分数",
                        "focus_row_label": "操作重点",
                        "focus_templates": {
                            "stay_with_first": "先盯住 {target} 龙头。",
                            "use_as_confirmation": "把 {target} 作为第一确认层。",
                            "reduce_names_tied_to": "先收缩 {target} 相关个股。",
                        },
                    },
                },
            },
            "display_fields": display_fields["next_session_action_metrics"],
            "info_block_specs": grouped_summary_info_blocks,
            "summary_metrics": [
                {
                    "label_key": "core_count",
                    "value_key": "core_count",
                    "format_key": "count",
                },
                {
                    "label_key": "candidate_count",
                    "value_key": "candidate_count",
                    "format_key": "count",
                },
                {
                    "label_key": "avoid_count",
                    "value_key": "avoid_count",
                    "format_key": "count",
                },
            ],
        },
    }


def build_page_layout_specs(layout_key: str = "default") -> list[dict[str, str]]:
    """Return replaceable page-layout render order specs."""
    grouped_layouts = build_home_content_group_layout_specs()
    resolved_groups = grouped_layouts.get(layout_key, grouped_layouts["default"])
    segment_templates = build_page_segment_template_specs()
    resolved_segments = segment_templates.get(layout_key, segment_templates["default"])
    content_specs = build_content_section_specs()
    chart_specs = build_chart_specs()
    group_to_segment: dict[str, dict[str, str]] = {}
    for segment in resolved_segments:
        segment_key = str(segment.get("segment_key", "")).strip()
        if not segment_key:
            continue
        segment_title = str(segment.get("segment_title", "")).strip()
        segment_tone = str(segment.get("segment_tone", "neutral")).strip() or "neutral"
        segment_role_key = str(segment.get("role_key", "")).strip()
        for group_key in list(segment.get("group_keys", [])):
            normalized_group_key = str(group_key).strip()
            if not normalized_group_key:
                continue
            group_to_segment[normalized_group_key] = {
                "segment_key": segment_key,
                "segment_title": segment_title,
                "segment_tone": segment_tone,
                "segment_role_key": segment_role_key,
            }
    page_layout = [
        {
            "section_type": "kpi",
            "section_key": "kpi_cards",
            "segment_key": "header_segment",
            "segment_title": str(resolved_segments[0].get("segment_title", "")).strip()
            if resolved_segments
            else "Home Header Segment",
            "segment_tone": str(resolved_segments[0].get("segment_tone", "neutral")).strip()
            if resolved_segments
            else "neutral",
            "segment_role_key": str(resolved_segments[0].get("role_key", "context")).strip()
            if resolved_segments
            else "context",
            "section_role_key": "context",
            "module_priority": "0",
        }
    ]
    for group in resolved_groups:
        group_key = str(group.get("group_key", "")).strip()
        group_title = str(group.get("group_title", "")).strip()
        group_tone = str(group.get("group_tone", "neutral")).strip() or "neutral"
        group_role_key = str(group.get("role_key", "")).strip()
        segment_meta = group_to_segment.get(
            group_key,
            {
                "segment_key": "body_segment",
                "segment_title": "Body Segment",
                "segment_tone": "neutral",
                "segment_role_key": "analysis",
            },
        )
        for section_key in list(group.get("sections", [])):
            normalized_key = str(section_key).strip()
            if not normalized_key:
                continue
            section_type = "chart" if normalized_key in {"sector_strength", "top_movers"} else "content"
            section_specs = chart_specs if section_type == "chart" else content_specs
            section_role_key = str(
                section_specs.get(normalized_key, {}).get("role_key", group_role_key or "")
            ).strip()
            module_priority = str(
                section_specs.get(normalized_key, {}).get("module_priority", 99)
            ).strip()
            page_layout.append(
                {
                    "section_type": section_type,
                    "section_key": normalized_key,
                    "segment_key": str(segment_meta.get("segment_key", "")).strip(),
                    "segment_title": str(segment_meta.get("segment_title", "")).strip(),
                    "segment_tone": str(segment_meta.get("segment_tone", "neutral")).strip(),
                    "segment_role_key": str(segment_meta.get("segment_role_key", "")).strip(),
                    "group_key": group_key,
                    "group_title": group_title,
                    "group_tone": group_tone,
                    "group_role_key": group_role_key,
                    "section_role_key": section_role_key,
                    "module_priority": module_priority,
                }
            )
    return page_layout
