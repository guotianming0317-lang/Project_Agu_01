"""Shared sector labels and lightweight grouping helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SEMICONDUCTOR_EQUIPMENT_SECTOR = "半导体设备"
SEMICONDUCTOR_MATERIAL_SECTOR = "半导体材料"
SEMICONDUCTOR_GAS_SECTOR = "半导体气体"
LEGACY_SEMICONDUCTOR_MATERIAL_GAS_SECTOR = "半导体材料气体"

AI_CPO_SECTOR = "AI光模块/CPO"
AI_SERVER_SECTOR = "AI服务器/算力硬件"
PCB_SECTOR = "PCB/高速板"
COOLING_SECTOR = "液冷/数据中心散热"
HBM_SECTOR = "存储/HBM"
CHIPLET_SECTOR = "先进封装/Chiplet"

MATERIAL_RELATED_SECTORS = frozenset(
    {
        SEMICONDUCTOR_MATERIAL_SECTOR,
        SEMICONDUCTOR_GAS_SECTOR,
    }
)
MATERIAL_CHAIN_LABEL = "半导体材料、半导体气体"

DEFAULT_FOCUS_SECTORS = (
    MATERIAL_CHAIN_LABEL,
    SEMICONDUCTOR_EQUIPMENT_SECTOR,
)
DEFAULT_FOCUS_SECTORS_TEXT = "、".join(DEFAULT_FOCUS_SECTORS)

KNOWN_MONITOR_SECTORS = frozenset(
    {
        AI_CPO_SECTOR,
        AI_SERVER_SECTOR,
        PCB_SECTOR,
        COOLING_SECTOR,
        SEMICONDUCTOR_EQUIPMENT_SECTOR,
        SEMICONDUCTOR_MATERIAL_SECTOR,
        SEMICONDUCTOR_GAS_SECTOR,
        HBM_SECTOR,
        CHIPLET_SECTOR,
        LEGACY_SEMICONDUCTOR_MATERIAL_GAS_SECTOR,
        "半导体材料/气体",
    }
)

KNOWN_CHAIN_GROUPS = frozenset(
    {
        "光模块",
        "服务器",
        "服务器/系统集成",
        "服务器/网络设备",
        "PCB",
        "PCB材料",
        "液冷",
        "设备",
        "材料",
        "气体",
        "存储",
        "封测",
    }
)

KNOWN_MARKETS = frozenset(
    {
        "沪A",
        "深A",
        "创业板",
        "科创板",
    }
)

KNOWN_POOL_TYPES = frozenset(
    {
        "core",
        "extended",
    }
)

REPORT_RULE_CONFIG_PATH = Path(__file__).with_name("report_rule_config.json")


def _load_report_rule_config() -> dict[str, Any]:
    """Load maintained report-rule entries from a local JSON file."""
    return json.loads(REPORT_RULE_CONFIG_PATH.read_text(encoding="utf-8"))


_REPORT_RULE_CONFIG = _load_report_rule_config()

A_SHARE_MAPPING_RULES: tuple[tuple[tuple[str, ...], str], ...] = tuple(
    (
        tuple(entry["keywords"]),
        str(entry["suffix"]),
    )
    for entry in _REPORT_RULE_CONFIG["a_share_mapping_rules"]
)

INDUSTRY_CHAIN_MAPPING_RULES: tuple[tuple[tuple[str, ...], str], ...] = tuple(
    (
        tuple(entry["keywords"]),
        str(entry["template"]),
    )
    for entry in _REPORT_RULE_CONFIG["industry_chain_mapping_rules"]
)

TOMORROW_PLAN_RULES: tuple[tuple[int, str], ...] = tuple(
    (
        int(entry["minimum_risk_count"]),
        str(entry["template"]),
    )
    for entry in _REPORT_RULE_CONFIG["tomorrow_plan_rules"]
)

STRENGTH_LABEL_RULES: tuple[tuple[float, str], ...] = tuple(
    (
        float(entry["minimum_strength"]),
        str(entry["label"]),
    )
    for entry in _REPORT_RULE_CONFIG["strength_label_rules"]
)

POSITION_BIAS_RULES: tuple[tuple[float, int, str], ...] = tuple(
    (
        float(entry["minimum_strength"]),
        int(entry["maximum_risk_count"]),
        str(entry["label"]),
    )
    for entry in _REPORT_RULE_CONFIG["position_bias_rules"]
)

REASON_SCORE_WEIGHTS: dict[str, int] = {
    str(tag): int(weight)
    for tag, weight in _REPORT_RULE_CONFIG["reason_score_weights"].items()
}

REASON_SCORE_LABELS: dict[str, str] = {
    str(tag): str(label)
    for tag, label in _REPORT_RULE_CONFIG["reason_score_labels"].items()
}

HIGH_VALUE_ALERT_TYPES: frozenset[str] = frozenset(
    str(alert_type)
    for alert_type in _REPORT_RULE_CONFIG["high_value_alert_types"]
)

ALERT_TYPE_PRIORITY: dict[str, int] = {
    str(alert_type): int(priority)
    for alert_type, priority in _REPORT_RULE_CONFIG["alert_type_priority"].items()
}

MARKET_FOCUS_STATE_RULES: tuple[dict[str, float | int | str], ...] = tuple(
    {
        "state": str(entry["state"]),
        "minimum_red_count": int(entry["minimum_red_count"]),
        "minimum_strongest_avg": float(entry["minimum_strongest_avg"]),
        "minimum_secondary_avg": float(entry["minimum_secondary_avg"]),
        "minimum_high_value_count": int(entry["minimum_high_value_count"]),
        "minimum_strongest_gap": float(entry.get("minimum_strongest_gap", 0.0)),
    }
    for entry in _REPORT_RULE_CONFIG["market_focus_state_rules"]
)

MARKET_FOCUS_OBSERVATION_TEMPLATES: dict[str, dict[str, str]] = {
    str(state_key): {
        str(template_key): str(template)
        for template_key, template in dict(template_group).items()
    }
    for state_key, template_group in _REPORT_RULE_CONFIG[
        "market_focus_observation_templates"
    ].items()
}

STOCK_POOL_STRUCTURE_SUMMARY_RULES: dict[str, str] = {
    "empty_template": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["empty_template"]),
    "balanced_template": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["balanced_template"]),
    "chain_group_template": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["chain_group_template"]),
    "pool_type_template": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["pool_type_template"]),
    "separator": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["separator"]),
    "suffix": str(_REPORT_RULE_CONFIG["stock_pool_structure_summary"]["suffix"]),
}

STOCK_POOL_COMPARISON_TAG_DISPLAY: dict[str, str] = {
    str(tag_key): str(display_name)
    for tag_key, display_name in _REPORT_RULE_CONFIG["stock_pool_comparison_tags"].items()
}

STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY: dict[str, str] = {
    str(group_key): str(display_name)
    for group_key, display_name in _REPORT_RULE_CONFIG[
        "stock_pool_comparison_tag_groups"
    ].items()
}

TASK_RESULT_SUMMARY_RULES: dict[str, dict[str, str]] = {
    str(style_key): {
        str(case_key): str(template)
        for case_key, template in dict(style_rules).items()
    }
    for style_key, style_rules in _REPORT_RULE_CONFIG[
        "task_result_summary_rules"
    ].items()
}

STAGE_ALIGNMENT_TEMPLATES: dict[str, str] = {
    str(template_key): str(template)
    for template_key, template in _REPORT_RULE_CONFIG[
        "stage_alignment_templates"
    ].items()
}

DETAILED_ALERT_DISPLAY: dict[str, object] = {
    "title_template": str(_REPORT_RULE_CONFIG["detailed_alert_display"]["title_template"]),
    "block_title": str(
        _REPORT_RULE_CONFIG["detailed_alert_display"].get(
            "block_title",
            "Detailed Alerts",
        )
    ),
    "empty_message": str(
        _REPORT_RULE_CONFIG["detailed_alert_display"].get(
            "empty_message",
            "",
        )
    ),
    "priority_labels": {
        str(label_key): str(label_value)
        for label_key, label_value in dict(
            _REPORT_RULE_CONFIG["detailed_alert_display"].get("priority_labels", {})
        ).items()
    },
    "fields": [
        {
            "key": str(field["key"]),
            "label": str(field["label"]),
            "default": str(field.get("default", "")),
            "enabled": bool(field.get("enabled", True)),
        }
        for field in list(_REPORT_RULE_CONFIG["detailed_alert_display"]["fields"])
    ],
    "field_sets": {
        str(field_set_key): [
            {
                "key": str(field["key"]),
                "label": str(field["label"]),
                "default": str(field.get("default", "")),
                "enabled": bool(field.get("enabled", True)),
            }
            for field in list(field_specs)
        ]
        for field_set_key, field_specs in dict(
            _REPORT_RULE_CONFIG["detailed_alert_display"].get("field_sets", {})
        ).items()
    },
    "style_variants": {
        str(variant_key): {
            "block_title": str(variant_config.get("block_title", "")),
            "empty_message": str(variant_config.get("empty_message", "")),
            "title_template": str(variant_config.get("title_template", "")),
            "field_sets": {
                str(field_set_key): [
                    {
                        "key": str(field["key"]),
                        "label": str(field["label"]),
                        "default": str(field.get("default", "")),
                        "enabled": bool(field.get("enabled", True)),
                    }
                    for field in list(field_specs)
                ]
                for field_set_key, field_specs in dict(
                    variant_config.get("field_sets", {})
                ).items()
            },
        }
        for variant_key, variant_config in dict(
            _REPORT_RULE_CONFIG["detailed_alert_display"].get("style_variants", {})
        ).items()
    },
}

MARKET_FOCUS_SNAPSHOT_DISPLAY: dict[str, object] = {
    "block_title": str(_REPORT_RULE_CONFIG["market_focus_snapshot_display"]["block_title"]),
    "fields": [
        {
            "key": str(field["key"]),
            "label": str(field["label"]),
            "default": str(field.get("default", "")),
            "enabled": bool(field.get("enabled", True)),
        }
        for field in list(_REPORT_RULE_CONFIG["market_focus_snapshot_display"]["fields"])
    ],
    "style_variants": {
        str(variant_key): {
            "block_title": str(variant_config.get("block_title", "")),
            "fields": [
                {
                    "key": str(field["key"]),
                    "label": str(field["label"]),
                    "default": str(field.get("default", "")),
                    "enabled": bool(field.get("enabled", True)),
                }
                for field in list(variant_config.get("fields", []))
            ],
        }
        for variant_key, variant_config in dict(
            _REPORT_RULE_CONFIG["market_focus_snapshot_display"].get("style_variants", {})
        ).items()
    },
}

MONITOR_UNIVERSE_DISPLAY: dict[str, object] = {
    "block_title": str(_REPORT_RULE_CONFIG["monitor_universe_display"]["block_title"]),
    "stage_chain_fields": [
        {
            "key": str(field["key"]),
            "label": str(field["label"]),
            "default": str(field.get("default", "")),
            "enabled": bool(field.get("enabled", True)),
        }
        for field in list(_REPORT_RULE_CONFIG["monitor_universe_display"]["stage_chain_fields"])
    ],
    "style_variants": {
        str(variant_key): {
            "block_title": str(variant_config.get("block_title", "")),
            "stage_chain_fields": [
                {
                    "key": str(field["key"]),
                    "label": str(field["label"]),
                    "default": str(field.get("default", "")),
                    "enabled": bool(field.get("enabled", True)),
                }
                for field in list(variant_config.get("stage_chain_fields", []))
            ],
        }
        for variant_key, variant_config in dict(
            _REPORT_RULE_CONFIG["monitor_universe_display"].get("style_variants", {})
        ).items()
    },
}

CONSOLE_OVERVIEW_DISPLAY: dict[str, object] = {
    "fields": [
        {
            "key": str(field["key"]),
            "label": str(field["label"]),
            "default": str(field.get("default", "")),
            "enabled": bool(field.get("enabled", True)),
        }
        for field in list(_REPORT_RULE_CONFIG["console_overview_display"]["fields"])
    ],
    "style_variants": {
        str(variant_key): {
            "fields": [
                {
                    "key": str(field["key"]),
                    "label": str(field["label"]),
                    "default": str(field.get("default", "")),
                    "enabled": bool(field.get("enabled", True)),
                }
                for field in list(variant_config.get("fields", []))
            ],
        }
        for variant_key, variant_config in dict(
            _REPORT_RULE_CONFIG["console_overview_display"].get("style_variants", {})
        ).items()
    },
}


def is_material_related_sector(sector: str) -> bool:
    """Return whether a sector belongs to the material-gas linked chain."""
    return sector in MATERIAL_RELATED_SECTORS


def is_high_value_alert_type(alert_type: str) -> bool:
    """Return whether one alert type belongs to the shared high-value set."""
    return str(alert_type).strip() in HIGH_VALUE_ALERT_TYPES


def is_known_monitor_sector(sector: str) -> bool:
    """Return whether a sector belongs to the registered monitor-sector list."""
    return sector in KNOWN_MONITOR_SECTORS


def is_known_chain_group(chain_group: str) -> bool:
    """Return whether a chain group belongs to the registered chain-group list."""
    return chain_group in KNOWN_CHAIN_GROUPS


def is_known_market(market: str) -> bool:
    """Return whether a market belongs to the registered market list."""
    return market in KNOWN_MARKETS


def is_known_pool_type(pool_type: str) -> bool:
    """Return whether a pool type belongs to the registered pool-type list."""
    return pool_type in KNOWN_POOL_TYPES


def build_default_focus_sectors(top_sector: str | None = None) -> list[str]:
    """Build the default focus-sector order for morning observation."""
    normalized_sector = str(top_sector or "")
    focus_sectors = list(DEFAULT_FOCUS_SECTORS)
    if (
        normalized_sector
        and normalized_sector not in MATERIAL_RELATED_SECTORS
        and normalized_sector != SEMICONDUCTOR_EQUIPMENT_SECTOR
    ):
        focus_sectors.insert(0, normalized_sector)
    return focus_sectors
