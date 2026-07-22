"""Central task-profile configuration for scheduler-facing monitor flows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.sectors import (
    CONSOLE_OVERVIEW_DISPLAY,
    DETAILED_ALERT_DISPLAY,
    MARKET_FOCUS_SNAPSHOT_DISPLAY,
    MONITOR_UNIVERSE_DISPLAY,
    TASK_RESULT_SUMMARY_RULES,
)


TASK_PROFILE_CONFIG_PATH = Path(__file__).with_name("task_profile_config.json")


def _load_task_profile_config() -> dict[str, Any]:
    """Load maintained task-profile entries from a local JSON file."""
    config = json.loads(TASK_PROFILE_CONFIG_PATH.read_text(encoding="utf-8"))
    validate_task_profile_config(config, TASK_RESULT_SUMMARY_RULES)
    return config


def _resolve_bundle_items(bundle_value: object) -> list[str]:
    """Normalize one bundle value into a simple ordered string list."""
    if isinstance(bundle_value, dict):
        items = list(bundle_value.get("items", []))
    else:
        items = list(bundle_value if isinstance(bundle_value, list) else [])
    return [str(item) for item in items if str(item).strip()]


def _resolve_bundle_meta_map(
    bundle_config: dict[str, object],
    *,
    extra_meta_config: dict[str, object] | None = None,
) -> dict[str, dict[str, str]]:
    """Build one metadata map for either inline-object or sidecar bundle entries."""
    meta_map: dict[str, dict[str, str]] = {}
    sidecar_meta = dict(extra_meta_config or {})
    for bundle_key, bundle_value in bundle_config.items():
        inline_meta = dict(bundle_value) if isinstance(bundle_value, dict) else {}
        sidecar_entry = dict(sidecar_meta.get(bundle_key, {}))
        label = str(
            inline_meta.get(
                "label",
                sidecar_entry.get("label", bundle_key),
            )
        ).strip() or bundle_key
        summary = str(
            inline_meta.get(
                "summary",
                sidecar_entry.get("summary", ""),
            )
        ).strip()
        meta_map[str(bundle_key)] = {"label": label, "summary": summary}
    return meta_map


def validate_task_profile_config(
    config: dict[str, Any],
    result_summary_rules: dict[str, dict[str, str]],
) -> None:
    """Validate cross-references inside the task-profile config."""
    supported_overview_field_keys = {
        "scheduled_job_count",
        "scheduled_jobs",
        "scheduled_job_labels",
        "scheduled_timings",
        "result_summary_styles",
        "manual_preview_jobs",
        "scheduled_day_flow_jobs",
    }
    supported_output_profile_block_keys = {
        "include_morning_report",
        "include_market_focus_snapshot",
        "include_monitor_universe_observation",
        "include_intraday_digest",
        "include_detailed_alerts",
        "include_evening_report",
        "include_close_digest",
    }
    scheduled_job_ids = [
        str(entry["id"])
        for entry in list(config.get("scheduled_jobs", []))
    ]
    output_job_ids = {
        str(job_id) for job_id in dict(config.get("job_output_strategies", {})).keys()
    }
    view_templates = {
        str(template_key): dict(template_config)
        for template_key, template_config in dict(config.get("view_templates", {})).items()
    }
    intent_strategies = {
        str(job_id): dict(strategy)
        for job_id, strategy in dict(config.get("job_intent_strategies", {})).items()
    }
    intent_job_ids = set(intent_strategies.keys())
    alert_type_bundles = {
        str(bundle_key): _resolve_bundle_items(bundle_types)
        for bundle_key, bundle_types in dict(config.get("alert_type_bundles", {})).items()
    }
    chain_group_bundles = {
        str(bundle_key): _resolve_bundle_items(bundle_values)
        for bundle_key, bundle_values in dict(config.get("chain_group_bundles", {})).items()
    }

    duplicate_scheduled_job_ids = _find_duplicate_items(scheduled_job_ids)
    if duplicate_scheduled_job_ids:
        raise ValueError(
            "Duplicate scheduled job ids: " + ", ".join(duplicate_scheduled_job_ids)
        )

    missing_output_job_ids = sorted(set(scheduled_job_ids) - output_job_ids)
    if missing_output_job_ids:
        raise ValueError(
            "Scheduled jobs missing output strategies: "
            + ", ".join(missing_output_job_ids)
        )

    missing_intent_job_ids = sorted(set(scheduled_job_ids) - intent_job_ids)
    if missing_intent_job_ids:
        raise ValueError(
            "Scheduled jobs missing intent strategies: "
            + ", ".join(missing_intent_job_ids)
        )

    display_job_ids = [
        str(job_id)
        for group in list(config.get("task_display_groups", []))
        for job_id in list(dict(group).get("job_ids", []))
    ]
    duplicate_display_job_ids = _find_duplicate_items(display_job_ids)
    if duplicate_display_job_ids:
        raise ValueError(
            "Duplicate task display job ids: " + ", ".join(duplicate_display_job_ids)
        )

    unknown_display_job_ids = sorted(
        set(display_job_ids) - (output_job_ids & intent_job_ids)
    )
    if unknown_display_job_ids:
        raise ValueError(
            "Task display groups reference unknown job ids: "
            + ", ".join(unknown_display_job_ids)
        )

    task_overview_display = dict(config.get("task_overview_display", {}))
    overview_field_keys = [
        str(field["key"])
        for field in list(task_overview_display.get("fields", []))
    ]
    duplicate_overview_field_keys = _find_duplicate_items(overview_field_keys)
    if duplicate_overview_field_keys:
        raise ValueError(
            "Duplicate task overview field keys: "
            + ", ".join(duplicate_overview_field_keys)
        )
    unknown_overview_field_keys = sorted(
        set(overview_field_keys) - supported_overview_field_keys
    )
    if unknown_overview_field_keys:
        raise ValueError(
            "Task overview display references unknown field keys: "
            + ", ".join(unknown_overview_field_keys)
        )

    output_profiles_display = dict(config.get("output_profiles_display", {}))
    output_profile_block_keys = {
        str(block_key)
        for block_key in dict(output_profiles_display.get("block_labels", {})).keys()
    }
    unknown_output_profile_block_keys = sorted(
        output_profile_block_keys - supported_output_profile_block_keys
    )
    if unknown_output_profile_block_keys:
        raise ValueError(
            "Output profiles display references unknown block keys: "
            + ", ".join(unknown_output_profile_block_keys)
        )

    decision_rules = {
        str(style_key): list(style_rules)
        for style_key, style_rules in dict(
            config.get("task_result_summary_decision_rules", {})
        ).items()
    }
    decision_style_keys = set(decision_rules.keys())
    result_summary_style_keys = set(result_summary_rules.keys())
    detailed_alert_style_variant_keys = set(
        dict(DETAILED_ALERT_DISPLAY.get("style_variants", {})).keys()
    )
    market_focus_style_variant_keys = set(
        dict(MARKET_FOCUS_SNAPSHOT_DISPLAY.get("style_variants", {})).keys()
    )
    monitor_universe_style_variant_keys = set(
        dict(MONITOR_UNIVERSE_DISPLAY.get("style_variants", {})).keys()
    )
    console_overview_style_variant_keys = set(
        dict(CONSOLE_OVERVIEW_DISPLAY.get("style_variants", {})).keys()
    )
    supported_output_strategy_flags = {
        "include_morning_report",
        "include_market_focus_snapshot",
        "include_monitor_universe_observation",
        "include_intraday_digest",
        "include_detailed_alerts",
        "include_evening_report",
        "include_close_digest",
        "include_latest_review",
    }

    for template_key, template_config in view_templates.items():
        template_output_strategy = dict(template_config.get("output_strategy", {}))
        unknown_template_flags = sorted(
            set(str(flag) for flag in template_output_strategy.keys())
            - supported_output_strategy_flags
        )
        if unknown_template_flags:
            raise ValueError(
                f"View template '{template_key}' references unknown output flags: "
                + ", ".join(unknown_template_flags)
            )
        template_display_variant = str(template_config.get("display_variant", "")).strip()
        if template_display_variant and (
            template_display_variant not in console_overview_style_variant_keys
            or template_display_variant not in detailed_alert_style_variant_keys
            or template_display_variant not in market_focus_style_variant_keys
            or template_display_variant not in monitor_universe_style_variant_keys
        ):
            raise ValueError(
                f"View template '{template_key}' references incomplete shared display "
                f"variant: {template_display_variant}"
            )

    for job_id, strategy in intent_strategies.items():
        summary_style = str(strategy.get("result_summary_style", "")).strip()
        if summary_style not in decision_style_keys:
            raise ValueError(
                f"Job intent strategy '{job_id}' references unknown summary style: "
                f"{summary_style}"
            )
        if summary_style not in result_summary_style_keys:
            raise ValueError(
                f"Job intent strategy '{job_id}' references summary style without "
                f"wording rules: {summary_style}"
            )
        for digest_key in ("intraday_digest", "close_digest"):
            digest_strategy = dict(strategy.get(digest_key, {}))
            bundle_key = str(digest_strategy.get("preferred_alert_type_bundle", "")).strip()
            if bundle_key and bundle_key not in alert_type_bundles:
                raise ValueError(
                    f"Job intent strategy '{job_id}.{digest_key}' references unknown "
                    f"alert-type bundle: {bundle_key}"
                )
        chain_bundle_key = str(strategy.get("preferred_chain_group_bundle", "")).strip()
        if chain_bundle_key and chain_bundle_key not in chain_group_bundles:
            raise ValueError(
                f"Job intent strategy '{job_id}' references unknown chain-group "
                f"bundle: {chain_bundle_key}"
            )
        detailed_alert_style_variant = str(
            strategy.get("detailed_alert_style_variant", "")
        ).strip()
        if (
            detailed_alert_style_variant
            and detailed_alert_style_variant not in detailed_alert_style_variant_keys
        ):
            raise ValueError(
                f"Job intent strategy '{job_id}' references unknown detailed-alert "
                f"style variant: {detailed_alert_style_variant}"
            )
        display_variant = str(strategy.get("display_variant", "")).strip()
        if display_variant:
            if (
                display_variant not in console_overview_style_variant_keys
                or display_variant not in detailed_alert_style_variant_keys
                or display_variant not in market_focus_style_variant_keys
                or display_variant not in monitor_universe_style_variant_keys
            ):
                raise ValueError(
                    f"Job intent strategy '{job_id}' references incomplete shared "
                    f"display variant: {display_variant}"
                )
        view_template_key = str(strategy.get("view_template", "")).strip()
        if view_template_key and view_template_key not in view_templates:
            raise ValueError(
                f"Job intent strategy '{job_id}' references unknown view template: "
                f"{view_template_key}"
            )

    for job_id, strategy in dict(config.get("job_output_strategies", {})).items():
        view_template_key = str(dict(strategy).get("view_template", "")).strip()
        if view_template_key and view_template_key not in view_templates:
            raise ValueError(
                f"Job output strategy '{job_id}' references unknown view template: "
                f"{view_template_key}"
            )

    for style_key, rules in decision_rules.items():
        available_cases = set(result_summary_rules.get(style_key, {}).keys())
        for rule in rules:
            case_key = str(dict(rule).get("case", "")).strip()
            if not case_key:
                raise ValueError(
                    f"Summary decision rule under '{style_key}' is missing a case key."
                )
            if case_key not in available_cases:
                raise ValueError(
                    f"Summary decision rule '{style_key}.{case_key}' has no matching "
                    "wording template."
                )


def _find_duplicate_items(items: list[str]) -> list[str]:
    """Return duplicate string items while preserving first duplicate order."""
    seen: set[str] = set()
    duplicates: list[str] = []
    duplicate_seen: set[str] = set()
    for item in items:
        if item in seen and item not in duplicate_seen:
            duplicates.append(item)
            duplicate_seen.add(item)
        seen.add(item)
    return duplicates


_TASK_PROFILE_CONFIG = _load_task_profile_config()


def _resolve_digest_strategy(
    digest_strategy: dict[str, object],
    alert_type_bundles: dict[str, list[str]],
) -> dict[str, object]:
    """Resolve one digest strategy so bundle references become explicit lists."""
    resolved_strategy = dict(digest_strategy)
    if "preferred_alert_types" in resolved_strategy:
        resolved_strategy["preferred_alert_types"] = [
            str(alert_type)
            for alert_type in list(resolved_strategy.get("preferred_alert_types", []))
            if str(alert_type).strip()
        ]
        return resolved_strategy

    bundle_key = str(resolved_strategy.get("preferred_alert_type_bundle", "")).strip()
    if bundle_key:
        resolved_strategy["preferred_alert_types"] = list(alert_type_bundles.get(bundle_key, []))
    return resolved_strategy


def _resolve_output_strategy(
    strategy: dict[str, object],
    *,
    view_templates: dict[str, dict[str, object]],
) -> dict[str, bool]:
    """Resolve one job output strategy with optional view-template defaults."""
    resolved_strategy: dict[str, bool] = {}
    view_template_key = str(strategy.get("view_template", "")).strip()
    if view_template_key:
        template_config = dict(view_templates.get(view_template_key, {}))
        resolved_strategy.update(
            {
                str(flag): bool(enabled)
                for flag, enabled in dict(template_config.get("output_strategy", {})).items()
            }
        )
    resolved_strategy.update(
        {
            str(flag): bool(enabled)
            for flag, enabled in dict(strategy).items()
            if flag != "view_template"
        }
    )
    return resolved_strategy


def _resolve_intent_strategy(
    strategy: dict[str, object],
    *,
    alert_type_bundles: dict[str, list[str]],
    chain_group_bundles: dict[str, list[str]],
    view_templates: dict[str, dict[str, object]],
) -> dict[str, dict[str, object] | str | list[str]]:
    """Resolve one task intent strategy into explicit digest and chain-group lists."""
    view_template_key = str(strategy.get("view_template", "")).strip()
    template_config = dict(view_templates.get(view_template_key, {}))
    resolved_strategy: dict[str, dict[str, object] | str | list[str]] = {
        str(field_key): value
        for field_key, value in template_config.items()
        if field_key != "output_strategy"
    }
    resolved_strategy.update(
        {
        str(field_key): value
        for field_key, value in dict(strategy).items()
        if field_key
        not in {
            "intraday_digest",
            "close_digest",
            "preferred_chain_group_bundle",
            "view_template",
        }
    }
    )
    resolved_strategy["intraday_digest"] = _resolve_digest_strategy(
        dict(strategy.get("intraday_digest", {})),
        alert_type_bundles,
    )
    resolved_strategy["close_digest"] = _resolve_digest_strategy(
        dict(strategy.get("close_digest", {})),
        alert_type_bundles,
    )
    if "preferred_chain_groups" in strategy:
        resolved_strategy["preferred_chain_groups"] = [
            str(chain_group)
            for chain_group in list(strategy.get("preferred_chain_groups", []))
            if str(chain_group).strip()
        ]
    else:
        bundle_key = str(strategy.get("preferred_chain_group_bundle", "")).strip()
        if bundle_key:
            resolved_strategy["preferred_chain_group_bundle"] = bundle_key
        resolved_strategy["preferred_chain_groups"] = list(
            chain_group_bundles.get(bundle_key, [])
        )
    return resolved_strategy


ALERT_TYPE_BUNDLES: dict[str, list[str]] = {
    str(bundle_key): _resolve_bundle_items(bundle_types)
    for bundle_key, bundle_types in dict(_TASK_PROFILE_CONFIG.get("alert_type_bundles", {})).items()
}

CHAIN_GROUP_BUNDLES: dict[str, list[str]] = {
    str(bundle_key): _resolve_bundle_items(bundle_values)
    for bundle_key, bundle_values in dict(_TASK_PROFILE_CONFIG.get("chain_group_bundles", {})).items()
}

ALERT_TYPE_BUNDLE_META: dict[str, dict[str, str]] = _resolve_bundle_meta_map(
    dict(_TASK_PROFILE_CONFIG.get("alert_type_bundles", {})),
)

CHAIN_GROUP_BUNDLE_META: dict[str, dict[str, str]] = _resolve_bundle_meta_map(
    dict(_TASK_PROFILE_CONFIG.get("chain_group_bundles", {})),
    extra_meta_config=dict(_TASK_PROFILE_CONFIG.get("chain_group_bundle_meta", {})),
)

VIEW_TEMPLATES: dict[str, dict[str, object]] = {
    str(template_key): dict(template_config)
    for template_key, template_config in dict(_TASK_PROFILE_CONFIG.get("view_templates", {})).items()
}

VIEW_TEMPLATE_META: dict[str, dict[str, str]] = {
    template_key: {
        "label": str(template_config.get("label", template_key)).strip() or template_key,
        "summary": str(template_config.get("summary", "")).strip(),
    }
    for template_key, template_config in VIEW_TEMPLATES.items()
}

DEFAULT_SCHEDULED_JOBS: list[dict[str, int | str]] = [
    {
        "id": str(entry["id"]),
        "label": str(entry.get("label", entry["id"])).strip() or str(entry["id"]),
        "summary": str(entry.get("summary", "")).strip(),
        "hour": int(entry["hour"]),
        "minute": int(entry["minute"]),
    }
    for entry in _TASK_PROFILE_CONFIG["scheduled_jobs"]
]

TASK_DISPLAY_GROUPS: list[dict[str, object]] = [
    {
        "key": str(entry["key"]),
        "label": str(entry["label"]),
        "job_ids": [str(job_id) for job_id in list(entry["job_ids"])],
    }
    for entry in _TASK_PROFILE_CONFIG["task_display_groups"]
]

TASK_OVERVIEW_DISPLAY: dict[str, object] = {
    "heading": str(_TASK_PROFILE_CONFIG["task_overview_display"]["heading"]),
    "display_groups_heading": str(
        _TASK_PROFILE_CONFIG["task_overview_display"]["display_groups_heading"]
    ),
    "fields": [
        {
            "key": str(field["key"]),
            "label": str(field["label"]),
        }
        for field in list(_TASK_PROFILE_CONFIG["task_overview_display"]["fields"])
    ],
}

OUTPUT_PROFILES_DISPLAY: dict[str, object] = {
    "heading": str(_TASK_PROFILE_CONFIG["output_profiles_display"]["heading"]),
    "intent_label_prefix": str(
        _TASK_PROFILE_CONFIG["output_profiles_display"]["intent_label_prefix"]
    ),
    "block_labels": {
        str(block_key): str(display_label)
        for block_key, display_label in dict(
            _TASK_PROFILE_CONFIG["output_profiles_display"]["block_labels"]
        ).items()
    },
}

JOB_VIEW_TEMPLATE_KEYS: dict[str, str] = {
    str(job_id): str(dict(strategy).get("view_template", "")).strip()
    for job_id, strategy in _TASK_PROFILE_CONFIG["job_output_strategies"].items()
    if str(dict(strategy).get("view_template", "")).strip()
}

JOB_OUTPUT_STRATEGIES: dict[str, dict[str, bool]] = {
    str(job_id): _resolve_output_strategy(
        dict(strategy),
        view_templates=VIEW_TEMPLATES,
    )
    for job_id, strategy in _TASK_PROFILE_CONFIG["job_output_strategies"].items()
}

JOB_INTENT_STRATEGIES: dict[str, dict[str, dict[str, object] | str]] = {
    str(job_id): _resolve_intent_strategy(
        dict(strategy),
        alert_type_bundles=ALERT_TYPE_BUNDLES,
        chain_group_bundles=CHAIN_GROUP_BUNDLES,
        view_templates=VIEW_TEMPLATES,
    )
    for job_id, strategy in _TASK_PROFILE_CONFIG["job_intent_strategies"].items()
}

TASK_RESULT_SUMMARY_DECISION_RULES: dict[str, list[dict[str, int | str]]] = {
    str(style_key): [dict(rule) for rule in list(style_rules)]
    for style_key, style_rules in _TASK_PROFILE_CONFIG[
        "task_result_summary_decision_rules"
    ].items()
}


def get_task_display_job_ids(*, group_key: str | None = None) -> list[str]:
    """Return configured task ids in display order, optionally by group key."""
    if group_key is None:
        return [
            job_id
            for group in TASK_DISPLAY_GROUPS
            for job_id in list(group["job_ids"])
        ]

    for group in TASK_DISPLAY_GROUPS:
        if str(group["key"]) == group_key:
            return [str(job_id) for job_id in list(group["job_ids"])]
    return []


def get_task_display_group_summaries() -> list[tuple[str, list[str]]]:
    """Return configured display-group labels with their ordered task ids."""
    return [
        (
            str(group.get("label", "")).strip() or str(group.get("key", "")).strip(),
            [str(job_id) for job_id in list(group.get("job_ids", []))],
        )
        for group in TASK_DISPLAY_GROUPS
    ]


def get_task_result_summary_styles() -> list[str]:
    """Return configured result-summary styles in stable order."""
    styles: list[str] = []
    for strategy in JOB_INTENT_STRATEGIES.values():
        summary_style = str(strategy.get("result_summary_style", "")).strip()
        if summary_style and summary_style not in styles:
            styles.append(summary_style)
    return styles


def get_job_display_meta(job_id: str) -> dict[str, str]:
    """Return readable label and summary for one configured job id."""
    for job in DEFAULT_SCHEDULED_JOBS:
        if str(job["id"]) == job_id:
            return {
                "label": str(job.get("label", job_id)).strip() or job_id,
                "summary": str(job.get("summary", "")).strip(),
            }
    intent_strategy = dict(JOB_INTENT_STRATEGIES.get(job_id, {}))
    return {
        "label": str(intent_strategy.get("console_title", job_id)).strip() or job_id,
        "summary": str(intent_strategy.get("console_subtitle", "")).strip(),
    }


def build_task_overview_lines() -> list[str]:
    """Build one shared task-overview summary block for CLI surfaces."""
    scheduled_job_ids = [str(job["id"]) for job in DEFAULT_SCHEDULED_JOBS]
    scheduled_job_label_pairs = [
        f"{job['id']} = {job['label']}"
        for job in DEFAULT_SCHEDULED_JOBS
    ]
    scheduled_job_timings = [
        f"{job['id']} ({job['hour']:02d}:{job['minute']:02d})"
        for job in DEFAULT_SCHEDULED_JOBS
    ]
    summary_styles = get_task_result_summary_styles()
    display_group_summaries = get_task_display_group_summaries()
    manual_preview_jobs: list[str] = []
    scheduled_day_flow_jobs: list[str] = []
    for group_label, job_ids in display_group_summaries:
        if group_label == "Manual Preview":
            manual_preview_jobs = job_ids
        if group_label == "Scheduled Day Flow":
            scheduled_day_flow_jobs = job_ids

    overview_values: dict[str, str] = {
        "scheduled_job_count": str(len(DEFAULT_SCHEDULED_JOBS)),
        "scheduled_jobs": ", ".join(scheduled_job_ids),
        "scheduled_job_labels": ", ".join(scheduled_job_label_pairs),
        "scheduled_timings": ", ".join(scheduled_job_timings),
        "result_summary_styles": ", ".join(summary_styles),
        "manual_preview_jobs": ", ".join(manual_preview_jobs),
        "scheduled_day_flow_jobs": ", ".join(scheduled_day_flow_jobs),
    }

    lines = [str(TASK_OVERVIEW_DISPLAY["heading"])]
    for field in list(TASK_OVERVIEW_DISPLAY["fields"]):
        field_key = str(field["key"])
        field_label = str(field["label"])
        lines.append(f"{field_label}: {overview_values.get(field_key, '')}")
    lines.append(str(TASK_OVERVIEW_DISPLAY["display_groups_heading"]))
    for group_label, job_ids in display_group_summaries:
        lines.append(f"- {group_label}: {', '.join(job_ids)}")
    return lines


def get_scheduler_output_group_summaries() -> list[tuple[str, list[str]]]:
    """Return scheduler-facing task groups with non-manual jobs only."""
    return [
        (group_label, [job_id for job_id in job_ids if job_id != "manual"])
        for group_label, job_ids in get_task_display_group_summaries()
        if any(job_id != "manual" for job_id in job_ids)
    ]


def build_output_profiles_lines() -> list[str]:
    """Build one shared output-profiles summary block for scheduler surfaces."""
    lines = [str(OUTPUT_PROFILES_DISPLAY["heading"])]
    block_labels = dict(OUTPUT_PROFILES_DISPLAY["block_labels"])
    intent_label_prefix = str(OUTPUT_PROFILES_DISPLAY["intent_label_prefix"])
    for group_label, group_job_ids in get_scheduler_output_group_summaries():
        if not group_job_ids:
            continue
        lines.append(f"{group_label}:")
        for job_id in group_job_ids:
            profile = dict(JOB_OUTPUT_STRATEGIES.get(job_id, {}))
            intent_strategy = dict(JOB_INTENT_STRATEGIES.get(job_id, {}))
            view_template_key = str(JOB_VIEW_TEMPLATE_KEYS.get(job_id, "")).strip()
            job_meta = get_job_display_meta(job_id)
            enabled_blocks = [
                str(display_label)
                for block_key, display_label in block_labels.items()
                if profile.get(block_key, False)
            ]
            lines.append(
                f"- {job_id} / {job_meta['label']}: {', '.join(enabled_blocks)}"
            )
            if job_meta["summary"]:
                lines.append("  task-summary: " + job_meta["summary"])
            if view_template_key:
                template_meta = get_view_template_meta(view_template_key)
                lines.append(
                    "  view-mode: "
                    + template_meta["label"]
                    + f" ({view_template_key})"
                )
                if template_meta["summary"]:
                    lines.append("  view-summary: " + template_meta["summary"])
            lines.append(
                intent_label_prefix
                + str(intent_strategy.get("intent_label", "manual"))
            )
            focus_tags = [
                str(tag).strip()
                for tag in list(intent_strategy.get("focus_tags", []))
                if str(tag).strip()
            ]
            if focus_tags:
                lines.append("  focus-tags: " + ", ".join(focus_tags))
            alert_bundle_keys = []
            for digest_key in ("intraday_digest", "close_digest"):
                digest_strategy = dict(intent_strategy.get(digest_key, {}))
                bundle_key = str(
                    digest_strategy.get("preferred_alert_type_bundle", "")
                ).strip()
                if bundle_key and bundle_key not in alert_bundle_keys:
                    alert_bundle_keys.append(bundle_key)
            if alert_bundle_keys:
                alert_bundle_labels = [
                    get_alert_type_bundle_meta(bundle_key)["label"]
                    + f" ({bundle_key})"
                    for bundle_key in alert_bundle_keys
                ]
                lines.append("  alert-bundles: " + ", ".join(alert_bundle_labels))
                alert_bundle_summaries = [
                    get_alert_type_bundle_meta(bundle_key)["summary"]
                    for bundle_key in alert_bundle_keys
                    if get_alert_type_bundle_meta(bundle_key)["summary"]
                ]
                if alert_bundle_summaries:
                    lines.append(
                        "  alert-bundle-summary: "
                        + " | ".join(alert_bundle_summaries)
                    )
            chain_bundle_key = str(
                intent_strategy.get("preferred_chain_group_bundle", "")
            ).strip()
            if chain_bundle_key:
                chain_bundle_meta = get_chain_group_bundle_meta(chain_bundle_key)
                lines.append(
                    "  chain-bundle: "
                    + chain_bundle_meta["label"]
                    + f" ({chain_bundle_key})"
                )
                if chain_bundle_meta["summary"]:
                    lines.append(
                        "  chain-bundle-summary: " + chain_bundle_meta["summary"]
                    )
            preferred_chain_groups = [
                str(chain_group).strip()
                for chain_group in list(intent_strategy.get("preferred_chain_groups", []))
                if str(chain_group).strip()
            ]
            if preferred_chain_groups:
                lines.append("  focus-chains: " + ", ".join(preferred_chain_groups))
            strategy_note = str(intent_strategy.get("strategy_note", "")).strip()
            if strategy_note:
                lines.append("  strategy-note: " + strategy_note)
    return lines


def get_view_template_meta(template_key: str) -> dict[str, str]:
    """Return one small label/summary bundle for a configured view template."""
    return dict(
        VIEW_TEMPLATE_META.get(
            template_key,
            {
                "label": template_key,
                "summary": "",
            },
        )
    )


def get_alert_type_bundle_meta(bundle_key: str) -> dict[str, str]:
    """Return one readable label/summary bundle for an alert-type bundle."""
    return dict(
        ALERT_TYPE_BUNDLE_META.get(
            bundle_key,
            {
                "label": bundle_key,
                "summary": "",
            },
        )
    )


def get_chain_group_bundle_meta(bundle_key: str) -> dict[str, str]:
    """Return one readable label/summary bundle for a chain-group bundle."""
    return dict(
        CHAIN_GROUP_BUNDLE_META.get(
            bundle_key,
            {
                "label": bundle_key,
                "summary": "",
            },
        )
    )


def build_job_view_mode_lines(job_id: str) -> list[str]:
    """Build one concise view-mode summary for a specific job."""
    view_template_key = str(JOB_VIEW_TEMPLATE_KEYS.get(job_id, "")).strip()
    if not view_template_key:
        return []
    template_meta = get_view_template_meta(view_template_key)
    lines = [f"View mode: {template_meta['label']} ({view_template_key})"]
    if template_meta["summary"]:
        lines.append("View summary: " + template_meta["summary"])
    return lines
