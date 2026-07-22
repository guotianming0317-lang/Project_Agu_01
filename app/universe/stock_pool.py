"""Observation universe for AI and semiconductor A-share stocks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
import csv
from datetime import datetime
from difflib import get_close_matches
import json
import os
from pathlib import Path

from app.models import StockRecord
from app.sectors import (
    KNOWN_CHAIN_GROUPS,
    KNOWN_MARKETS,
    KNOWN_MONITOR_SECTORS,
    KNOWN_POOL_TYPES,
    LEGACY_SEMICONDUCTOR_MATERIAL_GAS_SECTOR,
    STOCK_POOL_COMPARISON_TAG_DISPLAY,
    STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY,
    STOCK_POOL_STRUCTURE_SUMMARY_RULES,
    is_known_chain_group,
    is_known_market,
    is_known_monitor_sector,
    is_known_pool_type,
)


DEFAULT_STOCK_POOL_PATH = Path(__file__).with_suffix(".json")
DEFAULT_STOCK_POOL_HEALTH_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "stock_pool_health_snapshot.json"
)
REQUIRED_STOCK_COLUMNS = ("code", "name", "sub_sector", "priority")
MIN_SECTOR_DIVERSITY = 3
HIGH_CONCENTRATION_RATIO = 0.5
HIGH_CONCENTRATION_MIN_RECORDS = 6


def get_all_stocks() -> list[dict[str, str | int]]:
    """Return the full observation universe from the configured source file."""
    return _to_dicts(_load_stock_records())


def get_stocks_by_sector(sector: str) -> list[dict[str, str | int]]:
    """Return stocks belonging to a specific sector."""
    return _to_dicts(
        record for record in _load_stock_records() if record.sector == sector
    )


def get_high_priority_stocks() -> list[dict[str, str | int]]:
    """Return high priority names for focused monitoring."""
    return _to_dicts(
        record for record in _load_stock_records() if record.priority == 1
    )


def get_chain_groups_by_sector(sector: str) -> list[str]:
    """Return unique chain-group labels for one monitored sector."""
    normalized_sector = str(sector).strip()
    if not normalized_sector:
        return []

    chain_groups: list[str] = []
    for record in _load_stock_records():
        if record.sector != normalized_sector or not record.chain_group:
            continue
        if record.chain_group not in chain_groups:
            chain_groups.append(record.chain_group)
    return chain_groups


def validate_stock_pool() -> dict[str, object]:
    """Validate the configured stock-pool source file."""
    source_path = _resolve_stock_pool_path()
    records = _load_stock_records()
    duplicates = _find_duplicate_codes(records)
    unknown_sectors = _find_unknown_sectors(records)
    unknown_sector_suggestions = _build_unknown_sector_suggestions(unknown_sectors)
    unknown_chain_groups = _find_unknown_chain_groups(records)
    unknown_chain_group_suggestions = _build_unknown_chain_group_suggestions(
        unknown_chain_groups
    )
    unknown_markets = _find_unknown_markets(records)
    unknown_market_suggestions = _build_unknown_market_suggestions(unknown_markets)
    unknown_pool_types = _find_unknown_pool_types(records)
    unknown_pool_type_suggestions = _build_unknown_pool_type_suggestions(
        unknown_pool_types
    )
    sector_counts = dict(_count_sectors(records))
    chain_group_counts = dict(_count_chain_groups(records))
    pool_type_counts = dict(_count_pool_types(records))
    priority_counts = dict(_count_priorities(records))
    return {
        "source_path": str(source_path),
        "record_count": len(records),
        "duplicate_codes": duplicates,
        "unknown_sectors": unknown_sectors,
        "unknown_sector_suggestions": unknown_sector_suggestions,
        "registered_sectors": sorted(KNOWN_MONITOR_SECTORS),
        "unknown_chain_groups": unknown_chain_groups,
        "unknown_chain_group_suggestions": unknown_chain_group_suggestions,
        "registered_chain_groups": sorted(KNOWN_CHAIN_GROUPS),
        "unknown_markets": unknown_markets,
        "unknown_market_suggestions": unknown_market_suggestions,
        "registered_markets": sorted(KNOWN_MARKETS),
        "unknown_pool_types": unknown_pool_types,
        "unknown_pool_type_suggestions": unknown_pool_type_suggestions,
        "registered_pool_types": sorted(KNOWN_POOL_TYPES),
        "sector_counts": sector_counts,
        "chain_group_counts": chain_group_counts,
        "pool_type_counts": pool_type_counts,
        "priority_counts": priority_counts,
        "health_hints": _build_health_hints(
            record_count=len(records),
            unknown_sectors=unknown_sectors,
            unknown_sector_suggestions=unknown_sector_suggestions,
            unknown_chain_groups=unknown_chain_groups,
            unknown_chain_group_suggestions=unknown_chain_group_suggestions,
            unknown_markets=unknown_markets,
            unknown_market_suggestions=unknown_market_suggestions,
            unknown_pool_types=unknown_pool_types,
            unknown_pool_type_suggestions=unknown_pool_type_suggestions,
            sector_counts=sector_counts,
            chain_group_counts=chain_group_counts,
            priority_counts=priority_counts,
        ),
        "is_valid": not duplicates,
    }


def build_stock_pool_health_summary() -> dict[str, object]:
    """Build a reusable stock-pool health summary from validation output."""
    result = validate_stock_pool()
    risk_level, risk_text = _resolve_stock_pool_health_risk(result)
    structure_summary = _build_structure_summary(result)
    return {
        "status": "valid" if bool(result["is_valid"]) else "invalid",
        "risk_level": risk_level,
        "risk_text": risk_text,
        "structure_summary": structure_summary,
        "record_count": int(result["record_count"]),
        "duplicate_codes": list(result["duplicate_codes"]),
        "unknown_sectors": list(result.get("unknown_sectors", [])),
        "unknown_sector_suggestions": dict(result.get("unknown_sector_suggestions", {})),
        "registered_sectors": list(result.get("registered_sectors", [])),
        "unknown_chain_groups": list(result.get("unknown_chain_groups", [])),
        "unknown_chain_group_suggestions": dict(
            result.get("unknown_chain_group_suggestions", {})
        ),
        "registered_chain_groups": list(result.get("registered_chain_groups", [])),
        "unknown_markets": list(result.get("unknown_markets", [])),
        "unknown_market_suggestions": dict(result.get("unknown_market_suggestions", {})),
        "registered_markets": list(result.get("registered_markets", [])),
        "unknown_pool_types": list(result.get("unknown_pool_types", [])),
        "unknown_pool_type_suggestions": dict(
            result.get("unknown_pool_type_suggestions", {})
        ),
        "registered_pool_types": list(result.get("registered_pool_types", [])),
        "sector_counts": dict(result.get("sector_counts", {})),
        "chain_group_counts": dict(result.get("chain_group_counts", {})),
        "pool_type_counts": dict(result.get("pool_type_counts", {})),
        "priority_counts": dict(result.get("priority_counts", {})),
        "hint_count": len(list(result.get("health_hints", []))),
        "health_hints": list(result.get("health_hints", [])),
        "source_path": str(result["source_path"]),
    }


def build_stock_pool_health_comparison(
    summary: dict[str, object],
) -> dict[str, object]:
    """Compare one health summary against the last saved local baseline."""
    snapshot_path = _resolve_stock_pool_health_snapshot_path()
    previous_snapshot = _load_stock_pool_health_snapshot(snapshot_path)
    if not previous_snapshot:
        return {
            "snapshot_path": str(snapshot_path),
            "baseline_exists": False,
            "baseline_saved_at": "",
            "highlight_summary": (
                "\u6682\u65e0\u7ed3\u6784\u5bf9\u6bd4\u91cd\u70b9\uff0c\u672c\u6b21\u8fd0\u884c\u5c06\u5efa\u7acb\u9996\u4e2a\u57fa\u7ebf\u3002"
            ),
            "comparison_tags": ["Awaiting baseline"],
            "comparison_tag_labels": _resolve_comparison_tag_labels(["Awaiting baseline"]),
            "comparison_tag_groups": _build_comparison_tag_groups(["Awaiting baseline"]),
            "comparison_summary": (
                "\u672a\u627e\u5230\u5386\u53f2\u80a1\u7968\u6c60\u7ed3\u6784\u5feb\u7167\uff0c\u672c\u6b21\u8fd0\u884c\u5c06\u5efa\u7acb\u9996\u4e2a\u57fa\u7ebf\u3002"
            ),
            "change_rows": [],
        }

    change_rows = _build_structure_change_rows(summary, previous_snapshot)
    highlight_summary = _build_structure_change_highlight(summary, previous_snapshot)
    comparison_tags = _build_structure_change_tags(summary, previous_snapshot)
    baseline_saved_at = str(previous_snapshot.get("saved_at", "")).strip()
    if change_rows:
        comparison_summary = (
            f"\u4e0e {baseline_saved_at} \u7684\u57fa\u7ebf\u76f8\u6bd4\uff0c\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316\u3002"
        )
    else:
        comparison_summary = (
            f"\u4e0e {baseline_saved_at} \u7684\u57fa\u7ebf\u76f8\u6bd4\uff0c\u80a1\u7968\u6c60\u7ed3\u6784\u65e0\u53d8\u5316\u3002"
        )
    return {
        "snapshot_path": str(snapshot_path),
        "baseline_exists": True,
        "baseline_saved_at": baseline_saved_at,
        "highlight_summary": highlight_summary,
        "comparison_tags": comparison_tags,
        "comparison_tag_labels": _resolve_comparison_tag_labels(comparison_tags),
        "comparison_tag_groups": _build_comparison_tag_groups(comparison_tags),
        "comparison_summary": comparison_summary,
        "change_rows": change_rows,
    }


def save_stock_pool_health_snapshot(summary: dict[str, object]) -> Path:
    """Persist one stock-pool health snapshot for later local comparison."""
    snapshot_path = _resolve_stock_pool_health_snapshot_path()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_payload = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "record_count": int(summary.get("record_count", 0) or 0),
        "source_path": str(summary.get("source_path", "")),
        "sector_counts": dict(summary.get("sector_counts", {})),
        "chain_group_counts": dict(summary.get("chain_group_counts", {})),
        "pool_type_counts": dict(summary.get("pool_type_counts", {})),
        "priority_counts": dict(summary.get("priority_counts", {})),
        "structure_summary": str(summary.get("structure_summary", "")).strip(),
    }
    snapshot_path.write_text(
        json.dumps(snapshot_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return snapshot_path


def _load_stock_records() -> list[StockRecord]:
    """Load stock records from the configured JSON or CSV file."""
    source_path = _resolve_stock_pool_path()
    if source_path.suffix.lower() == ".json":
        raw_rows = json.loads(source_path.read_text(encoding="utf-8"))
    elif source_path.suffix.lower() == ".csv":
        with source_path.open("r", encoding="utf-8", newline="") as handle:
            raw_rows = list(csv.DictReader(handle))
    else:
        raise ValueError(
            "Stock pool file must use .json or .csv format: "
            f"{source_path}"
        )

    return [_build_stock_record(row) for row in raw_rows]


def _resolve_stock_pool_path() -> Path:
    """Resolve the active stock-pool source path."""
    configured_path = os.getenv("MONITOR_STOCK_POOL_PATH", "").strip()
    if configured_path:
        return Path(configured_path)
    return DEFAULT_STOCK_POOL_PATH


def _resolve_stock_pool_health_snapshot_path() -> Path:
    """Resolve the local stock-pool health snapshot path."""
    configured_path = os.getenv("MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH", "").strip()
    if configured_path:
        return Path(configured_path)
    return DEFAULT_STOCK_POOL_HEALTH_SNAPSHOT_PATH


def _build_stock_record(raw_row: dict[str, object]) -> StockRecord:
    """Normalize one raw file row into a stock record."""
    _validate_stock_row(raw_row)
    monitor_sector = _resolve_monitor_sector(raw_row)
    sub_sector = str(raw_row["sub_sector"]).strip()
    return StockRecord(
        code=str(raw_row["code"]).strip(),
        name=str(raw_row["name"]).strip(),
        market=str(raw_row.get("market", "")).strip(),
        sector=monitor_sector,
        sub_sector=sub_sector,
        priority=int(raw_row["priority"]),
        chain_group=_resolve_chain_group(monitor_sector, sub_sector, raw_row),
        pool_type=_resolve_pool_type(raw_row),
        notes=str(raw_row.get("notes", "")).strip(),
    )


def _validate_stock_row(raw_row: dict[str, object]) -> None:
    """Validate that a file row includes the required stock fields."""
    missing_columns = [
        column
        for column in REQUIRED_STOCK_COLUMNS
        if str(raw_row.get(column, "")).strip() == ""
    ]
    if missing_columns:
        raise ValueError(
            "Stock pool row is missing required columns: "
            + ", ".join(missing_columns)
        )
    if not _resolve_monitor_sector(raw_row):
        raise ValueError(
            "Stock pool row must include either sector or monitor_sector."
        )


def _resolve_monitor_sector(raw_row: dict[str, object]) -> str:
    """Resolve the primary monitored sector from legacy or new fields."""
    return str(
        raw_row.get("monitor_sector", raw_row.get("sector", "")),
    ).strip()


def _resolve_chain_group(
    monitor_sector: str,
    sub_sector: str,
    raw_row: dict[str, object],
) -> str:
    """Resolve chain-group metadata, with legacy fallback defaults."""
    configured_group = str(raw_row.get("chain_group", "")).strip()
    if configured_group:
        return configured_group

    legacy_material_gas_sectors = {
        LEGACY_SEMICONDUCTOR_MATERIAL_GAS_SECTOR,
        "\u534a\u5bfc\u4f53\u6750\u6599\u6c14\u4f53",
    }

    if monitor_sector in legacy_material_gas_sectors:
        gas_keywords = ("\u6c14", "\u7279\u6c14", "\u7535\u5b50\u6c14", "\u6c14\u4f53")
        if any(keyword in sub_sector for keyword in gas_keywords):
            return "\u6c14\u4f53"
        return "\u6750\u6599"

    default_chain_group_by_sector = {
        "AI\u5149\u6a21\u5757/CPO": "\u5149\u6a21\u5757",
        "AI\u670d\u52a1\u5668/\u7b97\u529b\u786c\u4ef6": "\u670d\u52a1\u5668",
        "PCB/楂橀€熸澘": "PCB",
        "\u6db2\u51b7/\u6570\u636e\u4e2d\u5fc3\u6563\u70ed": "\u6db2\u51b7",
        "\u534a\u5bfc\u4f53\u8bbe\u5907": "\u8bbe\u5907",
        "\u534a\u5bfc\u4f53\u6750\u6599": "\u6750\u6599",
        "\u534a\u5bfc\u4f53\u6c14\u4f53": "\u6c14\u4f53",
        "\u5b58\u50a8/HBM": "\u5b58\u50a8",
        "\u5148\u8fdb\u5c01\u88c5/Chiplet": "\u5c01\u6d4b",
    }
    return default_chain_group_by_sector.get(monitor_sector, "")


def _resolve_pool_type(raw_row: dict[str, object]) -> str:
    """Resolve pool-type metadata with a stable default."""
    pool_type = str(raw_row.get("pool_type", "core")).strip().lower()
    return pool_type or "core"


def _to_dicts(records: Iterable[StockRecord]) -> list[dict[str, str | int]]:
    """Convert stock records into plain dictionaries."""
    return [
        {
            "code": record.code,
            "name": record.name,
            "market": record.market,
            "sector": record.sector,
            "monitor_sector": record.sector,
            "sub_sector": record.sub_sector,
            "priority": record.priority,
            "chain_group": record.chain_group,
            "pool_type": record.pool_type,
            "notes": record.notes,
        }
        for record in records
    ]


def _find_duplicate_codes(records: Iterable[StockRecord]) -> list[str]:
    """Return duplicate stock codes in first-seen order."""
    seen_codes: set[str] = set()
    duplicate_codes: list[str] = []
    for record in records:
        if record.code in seen_codes and record.code not in duplicate_codes:
            duplicate_codes.append(record.code)
            continue
        seen_codes.add(record.code)
    return duplicate_codes


def _count_sectors(records: Iterable[StockRecord]) -> Counter[str]:
    """Count how many records belong to each sector."""
    return Counter(record.sector for record in records)


def _count_chain_groups(records: Iterable[StockRecord]) -> Counter[str]:
    """Count how many records belong to each chain group."""
    return Counter(record.chain_group for record in records if record.chain_group)


def _count_pool_types(records: Iterable[StockRecord]) -> Counter[str]:
    """Count how many records belong to each pool type."""
    return Counter(record.pool_type for record in records if record.pool_type)


def _count_priorities(records: Iterable[StockRecord]) -> Counter[int]:
    """Count how many records belong to each priority bucket."""
    return Counter(record.priority for record in records)


def _find_unknown_sectors(records: Iterable[StockRecord]) -> list[str]:
    """Return unregistered sectors in first-seen order."""
    unknown_sectors: list[str] = []
    for record in records:
        if is_known_monitor_sector(record.sector):
            continue
        if record.sector not in unknown_sectors:
            unknown_sectors.append(record.sector)
    return unknown_sectors


def _build_unknown_sector_suggestions(unknown_sectors: list[str]) -> dict[str, str]:
    """Suggest the closest registered sector label for unknown sectors."""
    suggestions: dict[str, str] = {}
    registered_sectors = sorted(KNOWN_MONITOR_SECTORS)
    for sector in unknown_sectors:
        matches = get_close_matches(sector, registered_sectors, n=1, cutoff=0.5)
        if matches:
            suggestions[sector] = matches[0]
    return suggestions


def _find_unknown_chain_groups(records: Iterable[StockRecord]) -> list[str]:
    """Return unregistered chain groups in first-seen order."""
    unknown_chain_groups: list[str] = []
    for record in records:
        if not record.chain_group:
            continue
        if is_known_chain_group(record.chain_group):
            continue
        if record.chain_group not in unknown_chain_groups:
            unknown_chain_groups.append(record.chain_group)
    return unknown_chain_groups


def _build_unknown_chain_group_suggestions(
    unknown_chain_groups: list[str],
) -> dict[str, str]:
    """Suggest the closest registered chain-group label for unknown groups."""
    suggestions: dict[str, str] = {}
    registered_chain_groups = sorted(KNOWN_CHAIN_GROUPS)
    for chain_group in unknown_chain_groups:
        matches = get_close_matches(
            chain_group,
            registered_chain_groups,
            n=1,
            cutoff=0.5,
        )
        if matches:
            suggestions[chain_group] = matches[0]
    return suggestions


def _find_unknown_markets(records: Iterable[StockRecord]) -> list[str]:
    """Return unregistered markets in first-seen order."""
    unknown_markets: list[str] = []
    for record in records:
        if not record.market:
            continue
        if is_known_market(record.market):
            continue
        if record.market not in unknown_markets:
            unknown_markets.append(record.market)
    return unknown_markets


def _build_unknown_market_suggestions(unknown_markets: list[str]) -> dict[str, str]:
    """Suggest the closest registered market label for unknown markets."""
    suggestions: dict[str, str] = {}
    registered_markets = sorted(KNOWN_MARKETS)
    for market in unknown_markets:
        matches = get_close_matches(market, registered_markets, n=1, cutoff=0.5)
        if matches:
            suggestions[market] = matches[0]
    return suggestions


def _find_unknown_pool_types(records: Iterable[StockRecord]) -> list[str]:
    """Return unregistered pool types in first-seen order."""
    unknown_pool_types: list[str] = []
    for record in records:
        if not record.pool_type:
            continue
        if is_known_pool_type(record.pool_type):
            continue
        if record.pool_type not in unknown_pool_types:
            unknown_pool_types.append(record.pool_type)
    return unknown_pool_types


def _build_unknown_pool_type_suggestions(
    unknown_pool_types: list[str],
) -> dict[str, str]:
    """Suggest the closest registered pool-type label for unknown pool types."""
    suggestions: dict[str, str] = {}
    registered_pool_types = sorted(KNOWN_POOL_TYPES)
    for pool_type in unknown_pool_types:
        matches = get_close_matches(pool_type, registered_pool_types, n=1, cutoff=0.5)
        if matches:
            suggestions[pool_type] = matches[0]
    return suggestions


def _build_health_hints(
    *,
    record_count: int,
    unknown_sectors: list[str],
    unknown_sector_suggestions: dict[str, str],
    unknown_chain_groups: list[str],
    unknown_chain_group_suggestions: dict[str, str],
    unknown_markets: list[str],
    unknown_market_suggestions: dict[str, str],
    unknown_pool_types: list[str],
    unknown_pool_type_suggestions: dict[str, str],
    sector_counts: dict[str, int],
    chain_group_counts: dict[str, int],
    priority_counts: dict[int, int],
) -> list[str]:
    """Build lightweight structure hints for quick stock-pool review."""
    hints: list[str] = []

    if unknown_sectors:
        hints.append(
            "Unknown monitor sectors detected: "
            + ", ".join(unknown_sectors)
            + ". Register new sector labels or check for typos."
        )
        for sector, suggestion in unknown_sector_suggestions.items():
            hints.append(f"Possible sector match for {sector}: {suggestion}")

    if unknown_chain_groups:
        hints.append(
            "Unknown chain groups detected: "
            + ", ".join(unknown_chain_groups)
            + ". Register new chain groups or check for typos."
        )
        for chain_group, suggestion in unknown_chain_group_suggestions.items():
            hints.append(
                f"Possible chain-group match for {chain_group}: {suggestion}"
            )

    if unknown_markets:
        hints.append(
            "Unknown markets detected: "
            + ", ".join(unknown_markets)
            + ". Register new markets or check for typos."
        )
        for market, suggestion in unknown_market_suggestions.items():
            hints.append(f"Possible market match for {market}: {suggestion}")

    if unknown_pool_types:
        hints.append(
            "Unknown pool types detected: "
            + ", ".join(unknown_pool_types)
            + ". Register new pool types or check for typos."
        )
        for pool_type, suggestion in unknown_pool_type_suggestions.items():
            hints.append(f"Possible pool-type match for {pool_type}: {suggestion}")

    if len(sector_counts) < MIN_SECTOR_DIVERSITY:
        hints.append(
            "Sector coverage is narrow: "
            f"only {len(sector_counts)} sector(s) configured."
        )

    if priority_counts.get(1, 0) == 0:
        hints.append("No priority-1 stocks are configured.")

    if record_count >= HIGH_CONCENTRATION_MIN_RECORDS and sector_counts:
        largest_sector, largest_count = max(
            sector_counts.items(),
            key=lambda item: item[1],
        )
        concentration_ratio = largest_count / record_count
        if concentration_ratio > HIGH_CONCENTRATION_RATIO:
            hints.append(
                "Sector concentration is high: "
                f"{largest_sector} holds {largest_count}/{record_count} stocks "
                f"({concentration_ratio:.0%})."
            )

    if record_count >= HIGH_CONCENTRATION_MIN_RECORDS and chain_group_counts:
        largest_chain_group, largest_chain_group_count = max(
            chain_group_counts.items(),
            key=lambda item: item[1],
        )
        chain_group_ratio = largest_chain_group_count / record_count
        if chain_group_ratio > HIGH_CONCENTRATION_RATIO:
            hints.append(
                "Chain-group concentration is high: "
                f"{largest_chain_group} holds "
                f"{largest_chain_group_count}/{record_count} stocks "
                f"({chain_group_ratio:.0%})."
            )

    return hints


def _resolve_stock_pool_health_risk(result: dict[str, object]) -> tuple[str, str]:
    """Resolve a reusable health risk summary from validation output."""
    duplicate_codes = list(result.get("duplicate_codes", []))
    if duplicate_codes:
        return "blocking", "Duplicate stock codes need to be fixed before monitoring."

    unknown_buckets = (
        list(result.get("unknown_sectors", []))
        + list(result.get("unknown_chain_groups", []))
        + list(result.get("unknown_markets", []))
        + list(result.get("unknown_pool_types", []))
    )
    if unknown_buckets:
        return "warning", "Unknown registry values were found and should be checked."

    health_hints = list(result.get("health_hints", []))
    if health_hints:
        return "warning", "Structure hints exist; review before relying on the pool."

    return "clean", "No blocking or warning signals were found."


def _build_structure_summary(result: dict[str, object]) -> str:
    """Build one concise business-facing summary of stock-pool structure."""
    chain_group_counts = dict(result.get("chain_group_counts", {}))
    pool_type_counts = dict(result.get("pool_type_counts", {}))
    record_count = int(result.get("record_count", 0) or 0)
    if record_count <= 0:
        return STOCK_POOL_STRUCTURE_SUMMARY_RULES["empty_template"]

    summary_parts: list[str] = []
    top_chain_group = _pick_top_count_label(chain_group_counts)
    if top_chain_group:
        chain_group, chain_group_count = top_chain_group
        summary_parts.append(
            STOCK_POOL_STRUCTURE_SUMMARY_RULES["chain_group_template"].format(
                top_chain_group=chain_group,
                top_chain_group_count=chain_group_count,
                record_count=record_count,
            )
        )

    top_pool_type = _pick_top_count_label(pool_type_counts)
    if top_pool_type:
        pool_type, pool_type_count = top_pool_type
        summary_parts.append(
            STOCK_POOL_STRUCTURE_SUMMARY_RULES["pool_type_template"].format(
                top_pool_type=pool_type,
                top_pool_type_count=pool_type_count,
                record_count=record_count,
            )
        )

    if not summary_parts:
        return STOCK_POOL_STRUCTURE_SUMMARY_RULES["balanced_template"]

    return (
        STOCK_POOL_STRUCTURE_SUMMARY_RULES["separator"].join(summary_parts)
        + STOCK_POOL_STRUCTURE_SUMMARY_RULES["suffix"]
    )


def _pick_top_count_label(counts: dict[object, object]) -> tuple[str, int] | None:
    """Return the top count item using count-desc, name-asc ordering."""
    if not counts:
        return None
    ranked_items = sorted(
        ((str(key), int(count)) for key, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return ranked_items[0] if ranked_items else None


def _load_stock_pool_health_snapshot(snapshot_path: Path) -> dict[str, object]:
    """Load the last local stock-pool health snapshot when available."""
    if not snapshot_path.exists():
        return {}
    try:
        loaded = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _build_structure_change_rows(
    current_summary: dict[str, object],
    previous_snapshot: dict[str, object],
) -> list[str]:
    """Build readable structure-delta rows across key stock-pool dimensions."""
    dimension_specs = (
        ("sector_counts", "\u677f\u5757"),
        ("chain_group_counts", "\u4ea7\u4e1a\u94fe\u5206\u7ec4"),
        ("pool_type_counts", "\u6c60\u7c7b\u578b"),
        ("priority_counts", "\u4f18\u5148\u7ea7"),
    )
    change_rows: list[str] = []
    for value_key, label in dimension_specs:
        current_counts = dict(current_summary.get(value_key, {}))
        previous_counts = dict(previous_snapshot.get(value_key, {}))
        deltas = _build_count_delta_rows(current_counts, previous_counts)
        for name, delta in deltas:
            change_rows.append(f"- {label} {name}: {delta:+d}")
    return change_rows


def _build_structure_change_highlight(
    current_summary: dict[str, object],
    previous_snapshot: dict[str, object],
) -> str:
    """Build one concise business-style highlight from stock-pool deltas."""
    highlight_specs = (
        ("sector_counts", "\u677f\u5757", ""),
        ("chain_group_counts", "\u4ea7\u4e1a\u94fe\u5206\u7ec4", ""),
        ("pool_type_counts", "\u6c60\u7c7b\u578b", ""),
    )
    highlight_parts: list[str] = []
    for value_key, label, suffix in highlight_specs:
        current_counts = dict(current_summary.get(value_key, {}))
        previous_counts = dict(previous_snapshot.get(value_key, {}))
        deltas = _build_count_delta_rows(current_counts, previous_counts)
        if not deltas:
            continue
        top_name, top_delta = deltas[0]
        direction = "\u589e\u52a0" if top_delta > 0 else "\u51cf\u5c11"
        highlight_parts.append(
            f"{label} {top_name}{suffix}{direction} ({top_delta:+d})"
        )

    priority_deltas = _build_count_delta_rows(
        dict(current_summary.get("priority_counts", {})),
        dict(previous_snapshot.get("priority_counts", {})),
    )
    if priority_deltas:
        top_priority, top_priority_delta = priority_deltas[0]
        direction = "\u589e\u52a0" if top_priority_delta > 0 else "\u51cf\u5c11"
        highlight_parts.append(
            f"\u4f18\u5148\u7ea7 P{top_priority} {direction} ({top_priority_delta:+d})"
        )

    if not highlight_parts:
        return "\u80a1\u7968\u6c60\u4e3b\u4f53\u7ed3\u6784\u4e0e\u4e0a\u4e00\u7248\u57fa\u7ebf\u4fdd\u6301\u4e00\u81f4\u3002"

    return "\u91cd\u70b9\u53d8\u5316\uff1a" + "\uff1b".join(highlight_parts[:3]) + "\u3002"


def _build_structure_change_tags(
    current_summary: dict[str, object],
    previous_snapshot: dict[str, object],
) -> list[str]:
    """Build compact business-facing tags from stock-pool structure deltas."""
    tags: list[str] = []
    record_delta = int(current_summary.get("record_count", 0) or 0) - int(
        previous_snapshot.get("record_count", 0) or 0
    )
    if record_delta > 0:
        tags.append("Watchlist Expanded")
    elif record_delta < 0:
        tags.append("Watchlist Trimmed")

    chain_group_tag_map = {
        "鏉愭枡": ("Materials Exposure Up", "Materials Exposure Down"),
        "姘斾綋": ("Gas Exposure Up", "Gas Exposure Down"),
        "璁惧": ("Equipment Exposure Up", "Equipment Exposure Down"),
        "灏佹祴": ("Packaging Exposure Up", "Packaging Exposure Down"),
        "瀛樺偍": ("Memory Exposure Up", "Memory Exposure Down"),
        "\u670d\u52a1\u5668": ("Server Exposure Up", "Server Exposure Down"),
        "\u5149\u6a21\u5757": ("Optics Exposure Up", "Optics Exposure Down"),
        "娑插喎": ("Cooling Exposure Up", "Cooling Exposure Down"),
        "PCB": ("PCB Exposure Up", "PCB Exposure Down"),
    }
    for name, delta in _build_count_delta_rows(
        dict(current_summary.get("chain_group_counts", {})),
        dict(previous_snapshot.get("chain_group_counts", {})),
    ):
        if name not in chain_group_tag_map:
            continue
        tags.append(
            chain_group_tag_map[name][0] if delta > 0 else chain_group_tag_map[name][1]
        )
        break

    pool_type_tag_map = {
        "core": ("Core Pool Weight Up", "Core Pool Weight Down"),
        "extended": ("Extended Pool Weight Up", "Extended Pool Weight Down"),
    }
    for name, delta in _build_count_delta_rows(
        dict(current_summary.get("pool_type_counts", {})),
        dict(previous_snapshot.get("pool_type_counts", {})),
    ):
        if name not in pool_type_tag_map:
            continue
        tags.append(pool_type_tag_map[name][0] if delta > 0 else pool_type_tag_map[name][1])
        break

    for name, delta in _build_count_delta_rows(
        dict(current_summary.get("priority_counts", {})),
        dict(previous_snapshot.get("priority_counts", {})),
    ):
        if name == "1":
            tags.append("Priority-1 Focus Up" if delta > 0 else "Priority-1 Focus Down")
            break

    if not tags:
        return ["Structure Stable"]
    return tags[:4]


def _resolve_comparison_tag_labels(tags: list[str]) -> list[str]:
    """Resolve configured display labels for stock-pool comparison tags."""
    return [
        STOCK_POOL_COMPARISON_TAG_DISPLAY.get(tag, tag)
        for tag in tags
    ]


def _build_comparison_tag_groups(tags: list[str]) -> list[dict[str, object]]:
    """Group compact comparison tags into reusable business categories."""
    grouped_labels: dict[str, list[str]] = {}
    for tag in tags:
        group_key = _resolve_comparison_tag_group_key(tag)
        grouped_labels.setdefault(group_key, []).append(
            STOCK_POOL_COMPARISON_TAG_DISPLAY.get(tag, tag)
        )

    group_order = (
        "baseline_state",
        "pool_scope",
        "chain_exposure",
        "pool_weight",
        "priority_focus",
        "other_changes",
    )
    grouped_rows: list[dict[str, object]] = []
    for group_key in group_order:
        tag_labels = grouped_labels.get(group_key, [])
        if not tag_labels:
            continue
        grouped_rows.append(
            {
                "group_key": group_key,
                "group_label": STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY.get(
                    group_key,
                    group_key,
                ),
                "tag_labels": tag_labels,
                "summary": (
                    f"{STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY.get(group_key, group_key)}: "
                    + "\u3001".join(tag_labels)
                ),
            }
        )
    return grouped_rows


def _resolve_comparison_tag_group_key(tag: str) -> str:
    """Map one comparison tag to a stable higher-level business group."""
    if tag in {"Awaiting baseline", "Structure Stable"}:
        return "baseline_state"
    if tag in {"Watchlist Expanded", "Watchlist Trimmed"}:
        return "pool_scope"
    if "Exposure" in tag:
        return "chain_exposure"
    if "Pool Weight" in tag:
        return "pool_weight"
    if "Priority-1 Focus" in tag:
        return "priority_focus"
    return "other_changes"


def _build_count_delta_rows(
    current_counts: dict[object, object],
    previous_counts: dict[object, object],
) -> list[tuple[str, int]]:
    """Build ordered count deltas for one structure dimension."""
    keys = {str(key) for key in current_counts} | {str(key) for key in previous_counts}
    deltas: list[tuple[str, int]] = []
    for key in keys:
        current_value = int(current_counts.get(key, 0) or 0)
        previous_value = int(previous_counts.get(key, 0) or 0)
        delta = current_value - previous_value
        if delta:
            deltas.append((key, delta))
    return sorted(
        deltas,
        key=lambda item: (-abs(item[1]), item[0]),
    )
