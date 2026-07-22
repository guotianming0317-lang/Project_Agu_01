"""Shared helpers for report text rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True, slots=True)
class ReportSection:
    """A small text section used to assemble readable reports."""

    heading: str | None
    lines: tuple[str, ...]


def build_text_report(
    title: str,
    sections: Sequence[ReportSection],
    *,
    intro_lines: Iterable[str] | None = None,
) -> str:
    """Build a readable plain-text report from reusable section blocks."""
    lines = [title]
    intro_items = [line for line in (intro_lines or []) if line]
    if intro_items:
        lines.extend(intro_items)

    for index, section in enumerate(sections):
        if section.heading is not None or index > 0 or intro_items:
            lines.append("")
        if section.heading:
            lines.append(section.heading)
        lines.extend(section.lines)

    return "\n".join(lines)


def join_report_items(items: Any, *, default: str) -> str:
    """Join a list-like field for report rendering."""
    if not items:
        return default
    if isinstance(items, str):
        return items
    return "\u3001".join(str(item) for item in items)


def build_stock_pool_observation_lines(
    *,
    structure_summary: str,
    comparison_tag_groups: Sequence[dict[str, object]] | None = None,
    highlight_summary: str = "",
    change_rows: Sequence[str] | None = None,
    health_hints: Sequence[str] | None = None,
    empty_text: str = "\u6682\u65e0\u65b0\u589e\u7ed3\u6784\u89c2\u5bdf",
) -> tuple[str, ...]:
    """Build reusable stock-pool observation lines for report sections."""
    lines: list[str] = []

    normalized_structure_summary = str(structure_summary).strip()
    if normalized_structure_summary:
        lines.append(
            f"\u76d1\u63a7\u6c60\u7ed3\u6784\uff1a{normalized_structure_summary}"
        )

    group_summaries = [
        str(group.get("summary", "")).strip()
        for group in (comparison_tag_groups or [])
        if isinstance(group, dict) and str(group.get("summary", "")).strip()
    ]
    if group_summaries:
        lines.append(
            "\u7ed3\u6784\u53d8\u5316\u5206\u7ec4\uff1a" + " | ".join(group_summaries)
        )

    normalized_highlight_summary = str(highlight_summary).strip()
    if normalized_highlight_summary:
        lines.append(
            f"\u7ed3\u6784\u91cd\u70b9\u53d8\u5316\uff1a{normalized_highlight_summary}"
        )

    normalized_change_rows = [
        str(change_row).strip()
        for change_row in (change_rows or [])
        if str(change_row).strip()
    ]
    if normalized_change_rows:
        lines.append(
            "\u7ed3\u6784\u53d8\u52a8\u660e\u7ec6\uff1a"
            + " | ".join(normalized_change_rows[:2])
        )

    normalized_hints = [
        str(hint).strip() for hint in (health_hints or []) if str(hint).strip()
    ]
    if normalized_hints:
        lines.append(
            "\u7ed3\u6784\u63d0\u9192\uff1a" + "\uff1b".join(normalized_hints[:2])
        )

    if not lines:
        lines.append(empty_text)
    return tuple(lines)


def build_stock_pool_drift_summary_text(
    *,
    structure_summary: str,
    comparison_tag_groups: Sequence[dict[str, object]] | None = None,
    highlight_summary: str = "",
    empty_text: str = "",
) -> str:
    """Build one compact stock-pool drift summary line for review headers."""
    normalized_highlight_summary = str(highlight_summary).strip()
    if normalized_highlight_summary:
        return "\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a" + normalized_highlight_summary

    group_summaries = [
        str(group.get("summary", "")).strip()
        for group in (comparison_tag_groups or [])
        if isinstance(group, dict) and str(group.get("summary", "")).strip()
    ]
    if group_summaries:
        return "\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1a" + group_summaries[0]

    normalized_structure_summary = str(structure_summary).strip()
    if normalized_structure_summary:
        return "\u76d1\u63a7\u6c60\u7ed3\u6784\u72b6\u6001\uff1a" + normalized_structure_summary

    return str(empty_text).strip()
