"""Shared rule helpers for report context building."""

from __future__ import annotations

from typing import Any, TypeVar

import pandas as pd

from app.reports.shared import join_report_items
from app.sectors import (
    A_SHARE_MAPPING_RULES,
    INDUSTRY_CHAIN_MAPPING_RULES,
    POSITION_BIAS_RULES,
    REASON_SCORE_LABELS,
    REASON_SCORE_WEIGHTS,
    STRENGTH_LABEL_RULES,
    TOMORROW_PLAN_RULES,
)
from app.universe.stock_pool import get_chain_groups_by_sector

T = TypeVar("T")


def rank_sectors_by_pct_chg(frame: pd.DataFrame, *, limit: int | None = None) -> list[str]:
    """Return sectors ranked by average percentage change."""
    if frame.empty or "sector" not in frame or "pct_chg" not in frame:
        return []
    ranked = (
        frame.groupby("sector")["pct_chg"].mean().sort_values(ascending=False).index.tolist()
    )
    return ranked if limit is None else ranked[:limit]


def pick_top_stock_names(
    frame: pd.DataFrame,
    *,
    sort_by: str = "pct_chg",
    limit: int = 3,
) -> list[str]:
    """Return top stock names from a frame using one sortable metric."""
    if frame.empty or "name" not in frame or sort_by not in frame:
        return []
    return frame.sort_values(by=sort_by, ascending=False)["name"].head(limit).tolist()


def get_top_sector_average_pct_chg(frame: pd.DataFrame) -> float:
    """Return the average percentage change of the strongest sector."""
    if frame.empty or "sector" not in frame or "pct_chg" not in frame:
        return 0.0
    sector_strength = frame.groupby("sector")["pct_chg"].mean().sort_values(ascending=False)
    if sector_strength.empty:
        return 0.0
    return float(sector_strength.iloc[0])


def classify_strength_label(strongest_avg: float) -> str:
    """Map sector strength into a maintained label rule."""
    for threshold, label in STRENGTH_LABEL_RULES:
        if strongest_avg >= threshold:
            return label
    return "偏弱"


def build_position_bias_hint(strongest_avg: float, risk_count: int) -> str:
    """Build a position-bias hint from maintained rule entries."""
    for minimum_strength, maximum_risk_count, label in POSITION_BIAS_RULES:
        if strongest_avg >= minimum_strength and risk_count <= maximum_risk_count:
            return label
    return "谨慎观察"


def build_tomorrow_plan(
    strongest_sector: str,
    secondary_sector: str,
    *,
    risk_count: int,
) -> str:
    """Build a next-session observation plan from maintained templates."""
    normalized_strongest = str(strongest_sector or "").strip() or "待确认"
    normalized_secondary = str(secondary_sector or "").strip() or normalized_strongest
    for minimum_risk_count, template in TOMORROW_PLAN_RULES:
        if risk_count >= minimum_risk_count:
            return template.format(
                strongest_sector=normalized_strongest,
                secondary_sector=normalized_secondary,
            )
    return TOMORROW_PLAN_RULES[-1][1].format(
        strongest_sector=normalized_strongest,
        secondary_sector=normalized_secondary,
    )


def build_a_share_mapping(sector: str) -> str:
    """Build an A-share mapping hint from maintained keyword rules."""
    normalized = str(sector or "").strip()
    if not normalized:
        return "待判断"
    for keywords, suffix in A_SHARE_MAPPING_RULES:
        if any(keyword in normalized for keyword in keywords):
            return f"{normalized}{suffix}"
    return f"{normalized}优先观察"


def build_industry_chain_mapping(sector: str) -> str:
    """Build an editable industry-chain summary using stock-pool chain groups."""
    normalized = str(sector or "").strip()
    if not normalized:
        return "待判断"

    chain_groups = get_chain_groups_by_sector(normalized)
    if not chain_groups:
        return build_a_share_mapping(normalized)

    chain_groups_text = "、".join(chain_groups)
    primary_chain_group = chain_groups[0]
    for keywords, template in INDUSTRY_CHAIN_MAPPING_RULES:
        if any(keyword in normalized for keyword in keywords):
            return template.format(
                sector=normalized,
                chain_groups=chain_groups_text,
                primary_chain_group=primary_chain_group,
            )
    return f"{normalized}优先观察，可重点映射{chain_groups_text}链条"


def pick_sector_stock_names(
    frame: pd.DataFrame,
    sectors: set[str],
    *,
    limit: int = 3,
    sort_by: str = "pct_chg",
) -> list[str]:
    """Return top stock names within a selected sector set."""
    if frame.empty or "sector" not in frame:
        return []
    filtered = frame[frame["sector"].isin(sectors)]
    if filtered.empty:
        return []
    return pick_top_stock_names(filtered, sort_by=sort_by, limit=limit)


def collect_positive_alert_messages(alerts: list[dict[str, Any]], *, limit: int = 3) -> list[str]:
    """Collect explicit positive alert messages using simple level-based rules."""
    return _collect_alert_messages(
        alerts,
        levels={"red", "orange", "红色", "橙色"},
        limit=limit,
    )


def collect_risk_alert_messages(alerts: list[dict[str, Any]], *, limit: int = 3) -> list[str]:
    """Collect explicit risk or weakness alert messages."""
    return _collect_alert_messages(
        alerts,
        levels={"yellow", "blue", "黄色", "蓝色"},
        keywords=("risk", "weak", "fall", "drop", "回落", "风险", "走弱"),
        limit=limit,
    )


def build_core_watchlist(
    frame: pd.DataFrame,
    *,
    strongest_sector: str,
    limit: int = 3,
) -> list[str]:
    """Build the core next-session watchlist from the strongest live sector."""
    if frame.empty or "name" not in frame:
        return []
    normalized_strongest = str(strongest_sector or "").strip()
    candidate_frame = frame
    if normalized_strongest and "sector" in frame:
        filtered = frame[frame["sector"] == normalized_strongest]
        if not filtered.empty:
            candidate_frame = filtered
    candidate_frame = _sort_frame(candidate_frame, ascending=False)
    return _pick_unique_names(candidate_frame, limit=limit)


def build_candidate_watchlist(
    frame: pd.DataFrame,
    *,
    strongest_sector: str,
    secondary_sector: str,
    excluded_names: list[str] | None = None,
    limit: int = 3,
) -> list[str]:
    """Build a candidate watchlist from the next confirming sector layer."""
    if frame.empty or "name" not in frame:
        return []
    excluded = {str(name).strip() for name in (excluded_names or []) if str(name).strip()}
    normalized_secondary = str(secondary_sector or "").strip()
    normalized_strongest = str(strongest_sector or "").strip()

    candidate_frame = frame
    if normalized_secondary and "sector" in frame:
        filtered = frame[frame["sector"] == normalized_secondary]
        if not filtered.empty:
            candidate_frame = filtered
    candidate_frame = _sort_frame(candidate_frame, ascending=False)
    names = _pick_unique_names(candidate_frame, limit=limit, excluded=excluded)
    if names:
        return names

    fallback_frame = frame
    preferred_sectors = [sector for sector in (normalized_secondary, normalized_strongest) if sector]
    if preferred_sectors and "sector" in frame:
        filtered = frame[frame["sector"].isin(preferred_sectors)]
        if not filtered.empty:
            fallback_frame = filtered
    fallback_frame = _sort_frame(fallback_frame, ascending=False)
    return _pick_unique_names(fallback_frame, limit=limit, excluded=excluded)


def build_avoid_list(
    frame: pd.DataFrame,
    alerts: list[dict[str, Any]],
    *,
    fading_sector: str,
    limit: int = 3,
) -> list[str]:
    """Build a same-day avoid list from risk alerts and weak sector laggards."""
    names: list[str] = []
    for alert in alerts:
        related_stocks = str(alert.get("related_stocks", "")).strip()
        if not related_stocks:
            continue
        for raw_name in related_stocks.replace("，", ",").split(","):
            normalized_name = str(raw_name).strip()
            if normalized_name and normalized_name not in names:
                names.append(normalized_name)
            if len(names) >= limit:
                return names

    if frame.empty or "name" not in frame:
        return names
    candidate_frame = frame
    normalized_fading_sector = str(fading_sector or "").strip()
    if normalized_fading_sector and "sector" in frame:
        filtered = frame[frame["sector"] == normalized_fading_sector]
        if not filtered.empty:
            candidate_frame = filtered
    candidate_frame = _sort_frame(candidate_frame, ascending=True)
    additional_names = _pick_unique_names(
        candidate_frame,
        limit=max(limit - len(names), 0),
        excluded=set(names),
    )
    return names + additional_names


def build_next_session_action_lines(
    frame: pd.DataFrame,
    alerts: list[dict[str, Any]],
    *,
    strongest_sector: str,
    secondary_sector: str,
    fading_sector: str,
) -> tuple[str, ...]:
    """Build one explainable next-session tiered action summary block."""
    summary = build_next_session_action_summary(
        frame,
        alerts,
        strongest_sector=strongest_sector,
        secondary_sector=secondary_sector,
        fading_sector=fading_sector,
    )
    return render_next_session_action_summary_lines(summary)


def build_next_session_action_summary(
    frame: pd.DataFrame,
    alerts: list[dict[str, Any]],
    *,
    strongest_sector: str,
    secondary_sector: str,
    fading_sector: str,
) -> dict[str, object]:
    """Build one structured next-session action summary for reuse across outputs."""
    core_watchlist = build_core_watchlist(
        frame,
        strongest_sector=strongest_sector,
    )
    candidate_watchlist = build_candidate_watchlist(
        frame,
        strongest_sector=strongest_sector,
        secondary_sector=secondary_sector,
        excluded_names=core_watchlist,
    )
    avoid_list = build_avoid_list(
        frame,
        alerts,
        fading_sector=fading_sector,
    )
    normalized_strongest = str(strongest_sector or "").strip() or "n/a"
    normalized_secondary = str(secondary_sector or "").strip() or normalized_strongest
    normalized_fading = str(fading_sector or "").strip() or "n/a"

    core_tags = build_watchlist_reason_tags(
        frame,
        core_watchlist,
        main_sector=normalized_strongest,
        fallback_tag="core-priority",
    )
    candidate_tags = build_watchlist_reason_tags(
        frame,
        candidate_watchlist,
        main_sector=normalized_secondary,
        fallback_tag="candidate-confirmation",
    )
    avoid_tags = build_avoid_reason_tags(
        frame,
        alerts,
        avoid_list,
        fading_sector=normalized_fading,
    )
    core_scores = build_reason_scores(core_tags)
    candidate_scores = build_reason_scores(candidate_tags)
    avoid_scores = build_reason_scores(avoid_tags, invert=True)
    reason_score_summary_lines = build_reason_score_summary_lines()
    core_watchlist = rank_names_by_scores(core_watchlist, core_scores)
    candidate_watchlist = rank_names_by_scores(candidate_watchlist, candidate_scores)
    avoid_list = rank_names_by_scores(avoid_list, avoid_scores)
    core_tags = reorder_mapping_by_names(core_tags, core_watchlist)
    candidate_tags = reorder_mapping_by_names(candidate_tags, candidate_watchlist)
    avoid_tags = reorder_mapping_by_names(avoid_tags, avoid_list)
    core_scores = reorder_mapping_by_names(core_scores, core_watchlist)
    candidate_scores = reorder_mapping_by_names(candidate_scores, candidate_watchlist)
    avoid_scores = reorder_mapping_by_names(avoid_scores, avoid_list)

    return {
        "rule_summary_lines": reason_score_summary_lines,
        "core": {
            "watchlist": core_watchlist,
            "tags": core_tags,
            "scores": core_scores,
            "reason": (
                "优先跟踪"
                + normalized_strongest
                + "，明日重点关注已经在该主线中领先的标的。"
            ),
        },
        "candidate": {
            "watchlist": candidate_watchlist,
            "tags": candidate_tags,
            "scores": candidate_scores,
            "reason": (
                "将"
                + normalized_secondary
                + "作为强势板块之外的第一层确认。"
            ),
        },
        "avoid": {
            "watchlist": avoid_list,
            "tags": avoid_tags,
            "scores": avoid_scores,
            "reason": (
                "减少与风险预警或板块走弱相关的"
                + normalized_fading
                + "标的。"
            ),
        },
    }


def render_next_session_action_summary_lines(summary: dict[str, object]) -> tuple[str, ...]:
    """Render one structured next-session action summary into compact report lines."""
    core = dict(summary.get("core", {}))
    candidate = dict(summary.get("candidate", {}))
    avoid = dict(summary.get("avoid", {}))
    rule_summary_lines = tuple(
        str(line).strip()
        for line in tuple(summary.get("rule_summary_lines", ()))
        if str(line).strip()
    )

    return (
        *rule_summary_lines,
        "核心观察名单："
        + join_names_for_display(list(core.get("watchlist", [])), default="暂无"),
        "核心观察标签："
        + join_reason_tags_for_display(dict(core.get("tags", {})), default="暂无"),
        "核心观察分数："
        + join_reason_scores_for_display(dict(core.get("scores", {})), default="暂无"),
        "核心观察原因：" + str(core.get("reason", "")).strip(),
        "候选观察名单："
        + join_names_for_display(list(candidate.get("watchlist", [])), default="暂无"),
        "候选观察标签："
        + join_reason_tags_for_display(dict(candidate.get("tags", {})), default="暂无"),
        "候选观察分数："
        + join_reason_scores_for_display(dict(candidate.get("scores", {})), default="暂无"),
        "候选观察原因：" + str(candidate.get("reason", "")).strip(),
        "规避名单："
        + join_names_for_display(list(avoid.get("watchlist", [])), default="暂无"),
        "规避标签："
        + join_reason_tags_for_display(dict(avoid.get("tags", {})), default="暂无"),
        "规避分数："
        + join_reason_scores_for_display(dict(avoid.get("scores", {})), default="暂无"),
        "规避原因：" + str(avoid.get("reason", "")).strip(),
    )


def render_compact_next_session_action_lines(summary: dict[str, object]) -> tuple[str, ...]:
    """Render the terminal report without repeating each stock name four times."""
    sections = (
        ("核心关注", "core", "优先跟踪"),
        ("候选确认", "candidate", "等待板块跟随确认"),
        ("风险规避", "avoid", "减少关注"),
    )
    lines: list[str] = []
    lines.extend(
        str(line).strip()
        for line in tuple(summary.get("rule_summary_lines", ()))
        if str(line).strip()
    )
    for title, key, default_action in sections:
        section = dict(summary.get(key, {}))
        names = list(section.get("watchlist", []))
        tags = dict(section.get("tags", {}))
        scores = dict(section.get("scores", {}))
        reason = str(section.get("reason", "")).strip()
        if not names:
            continue
        name_text = join_names_for_display(names, default="暂无")
        tag_text = "; ".join(
            f"{name}: {'/'.join(str(REASON_SCORE_LABELS.get(tag, tag)) for tag in tags.get(name, []))}"
            for name in names
            if tags.get(name)
        )
        score_text = "; ".join(
            f"{name}: {scores.get(name, 0)}分" for name in names if name in scores
        )
        lines.extend(
            (
                f"【{title}】{({'核心关注': '核心观察', '候选确认': '候选观察', '风险规避': '规避'}[title])}名单：{name_text}",
                f"评分：{score_text or '暂无'} | 触发因素：{tag_text or '待确认'}",
                f"提示：{default_action}。{reason}",
            )
        )
    return tuple(lines)
    return (
        *rule_summary_lines,
        "核心观察名单："
        + join_names_for_display(list(core.get("watchlist", [])), default="none"),
        "核心观察标签："
        + join_reason_tags_for_display(dict(core.get("tags", {})), default="none"),
        "核心观察分数："
        + join_reason_scores_for_display(dict(core.get("scores", {})), default="none"),
        "核心观察原因：" + str(core.get("reason", "")).strip(),
        "候选观察名单："
        + join_names_for_display(list(candidate.get("watchlist", [])), default="none"),
        "候选观察标签："
        + join_reason_tags_for_display(dict(candidate.get("tags", {})), default="none"),
        "候选观察分数："
        + join_reason_scores_for_display(dict(candidate.get("scores", {})), default="none"),
        "候选观察原因：" + str(candidate.get("reason", "")).strip(),
        "规避名单："
        + join_names_for_display(list(avoid.get("watchlist", [])), default="none"),
        "规避标签："
        + join_reason_tags_for_display(dict(avoid.get("tags", {})), default="none"),
        "规避分数："
        + join_reason_scores_for_display(dict(avoid.get("scores", {})), default="none"),
        "规避原因：" + str(avoid.get("reason", "")).strip(),
    )


def render_compact_next_session_action_lines(summary: dict[str, object]) -> tuple[str, ...]:
    """Render a compact, readable strategy block with stable Chinese labels."""
    labels = {
        "core": ("核心关注", "优先跟踪", "★"),
        "candidate": ("候选确认", "等待板块跟随确认", "候选"),
        "avoid": ("风险规避", "减少关注", "!"),
    }
    lines = [str(line).strip() for line in summary.get("rule_summary_lines", ()) if str(line).strip()]
    lines.append(
        "评分说明：主线+3=属于当前最强主线；强势+3=涨幅达到强势标准；"
        "跟随+2=出现板块跟随；流动性+1=成交活跃；"
        "风险预警-3=出现高风险信号；退潮板块-2=所属板块走弱；价格走弱-2=个股表现偏弱。"
    )
    for key in ("core", "candidate", "avoid"):
        section = dict(summary.get(key, {}))
        names = [
            str(name).strip()
            for name in section.get("watchlist", [])
            if str(name).strip()
            and not any(
                marker in str(name)
                for marker in ("Demo Gas", "Demo Material", "Demo Equipment")
            )
        ]
        names = [
            name.replace("Demo Gas 1", "演示气体标的1")
            .replace("Demo Gas 2", "演示气体标的2")
            .replace("Demo Material 1", "演示材料标的1")
            .replace("Demo Equipment 1", "演示设备标的1")
            for name in names
        ]
        if not names:
            continue
        title, action, marker = labels[key]
        tags = dict(section.get("tags", {}))
        scores = dict(section.get("scores", {}))
        score_parts = []
        factor_parts = []
        for name in names:
            if name in scores:
                score = int(scores[name])
                if score >= 6:
                    level = "核心"
                elif score >= 3:
                    level = "候选"
                elif score <= -3:
                    level = "风险"
                else:
                    level = "观察"
                score_parts.append(f"{name} {score}分({level})")
            raw_tags = [str(tag).strip() for tag in tags.get(name, []) if str(tag).strip()]
            translated = [str(REASON_SCORE_LABELS.get(tag, tag)).strip() for tag in raw_tags]
            if translated:
                factor_parts.append(f"{name}：{'、'.join(translated)}")
        reason = str(section.get("reason", "")).strip()
        lines.extend(
            (
                f"[{marker}]【{title}】股票：{'、'.join(names)}",
                f"评分：{'; '.join(score_parts) or '待确认'} | 触发因素：{'; '.join(factor_parts) or '待确认'}",
                f"提示：{action}" + (f"；{reason}" if reason else ""),
            )
        )
    return tuple(lines)


def join_names_for_display(names: list[str], *, default: str) -> str:
    """Join a simple stock-name list for compact report rendering."""
    return join_report_items(names, default=default)


def join_reason_tags_for_display(reason_tags: dict[str, list[str]], *, default: str) -> str:
    """Join one stock-to-tags mapping into a compact readable line."""
    if not reason_tags:
        return default
    items: list[str] = []
    for name, tags in reason_tags.items():
        normalized_tags = [
            str(REASON_SCORE_LABELS.get(str(tag).strip(), str(tag).strip())).strip()
            for tag in tags
            if str(tag).strip()
        ]
        if normalized_tags:
            items.append(f"{name} ({'/'.join(normalized_tags)})")
        else:
            items.append(str(name))
    return "; ".join(items)


def join_reason_scores_for_display(
    scores: dict[str, int],
    *,
    default: str,
) -> str:
    """Join one stock-to-score mapping into a compact readable line."""
    if not scores:
        return default
    return "; ".join(f"{name} ({score})" for name, score in scores.items())


def build_reason_score_summary_lines() -> tuple[str, str]:
    """Build compact report lines that explain the current score rules."""
    positive_tags = ("mainline", "strength", "follow-through", "liquidity")
    avoid_tags = ("risk-alert", "fading-sector", "price-weakness")
    fallback_tags = ("core-priority", "candidate-confirmation", "avoid-priority")
    return (
        "评分规则："
        + _join_weight_items(positive_tags),
        "兜底规则："
        + _join_weight_items(fallback_tags)
        + " | 规避规则："
        + _join_weight_items(avoid_tags),
    )


def rank_names_by_scores(names: list[str], scores: dict[str, int]) -> list[str]:
    """Rank stock names by explicit score while keeping stable fallback order."""
    indexed_names = {name: index for index, name in enumerate(names)}
    return sorted(
        names,
        key=lambda name: (-scores.get(name, 0), indexed_names.get(name, len(names)), name),
    )


def reorder_mapping_by_names(
    mapping: dict[str, T],
    names: list[str],
) -> dict[str, T]:
    """Reorder one name-keyed mapping to follow the selected display order."""
    return {name: mapping[name] for name in names if name in mapping}


def build_watchlist_reason_tags(
    frame: pd.DataFrame,
    names: list[str],
    *,
    main_sector: str,
    fallback_tag: str,
) -> dict[str, list[str]]:
    """Build readable reason tags for one watchlist tier."""
    reason_tags: dict[str, list[str]] = {}
    if not names:
        return reason_tags
    indexed_rows = {
        str(row.get("name", "")).strip(): row
        for _, row in frame.iterrows()
        if str(row.get("name", "")).strip()
    }
    for name in names:
        row = indexed_rows.get(name)
        tags: list[str] = []
        if row is not None:
            if str(row.get("sector", "")).strip() == str(main_sector).strip():
                tags.append("mainline")
            pct_chg = float(row.get("pct_chg", 0.0) or 0.0)
            if pct_chg >= 5.0:
                tags.append("strength")
            elif pct_chg >= 2.0:
                tags.append("follow-through")
            turnover = float(row.get("turnover", 0.0) or 0.0)
            if turnover >= 100.0:
                tags.append("liquidity")
        if not tags:
            tags.append(fallback_tag)
        reason_tags[name] = tags
    return reason_tags


def build_avoid_reason_tags(
    frame: pd.DataFrame,
    alerts: list[dict[str, Any]],
    names: list[str],
    *,
    fading_sector: str,
) -> dict[str, list[str]]:
    """Build readable reason tags for the avoid tier."""
    reason_tags: dict[str, list[str]] = {}
    if not names:
        return reason_tags
    indexed_rows = {
        str(row.get("name", "")).strip(): row
        for _, row in frame.iterrows()
        if str(row.get("name", "")).strip()
    }
    risk_names: set[str] = set()
    for alert in alerts:
        related_stocks = str(alert.get("related_stocks", "")).strip()
        if not related_stocks:
            continue
        for raw_name in related_stocks.replace("，", ",").split(","):
            normalized_name = str(raw_name).strip()
            if normalized_name:
                risk_names.add(normalized_name)
    for name in names:
        row = indexed_rows.get(name)
        tags: list[str] = []
        if name in risk_names:
            tags.append("risk-alert")
        if row is not None:
            if str(row.get("sector", "")).strip() == str(fading_sector).strip():
                tags.append("fading-sector")
            pct_chg = float(row.get("pct_chg", 0.0) or 0.0)
            if pct_chg < 0:
                tags.append("price-weakness")
        if not tags:
            tags.append("avoid-priority")
        reason_tags[name] = tags
    return reason_tags


def build_reason_scores(
    reason_tags: dict[str, list[str]],
    *,
    invert: bool = False,
) -> dict[str, int]:
    """Build lightweight transparent scores from readable reason tags."""
    scored_items: list[tuple[str, int]] = []
    for name, tags in reason_tags.items():
        score = sum(REASON_SCORE_WEIGHTS.get(str(tag).strip(), 0) for tag in tags)
        if invert:
            score = -score
        scored_items.append((name, score))
    scored_items.sort(key=lambda item: (-item[1], item[0]))
    return {name: score for name, score in scored_items}


def _join_weight_items(tags: tuple[str, ...]) -> str:
    """Join one ordered tag-weight list for compact rule display."""
    return ", ".join(
        f"{REASON_SCORE_LABELS.get(tag, tag)}={REASON_SCORE_WEIGHTS.get(tag, 0)}"
        for tag in tags
    )


def _sort_frame(frame: pd.DataFrame, *, ascending: bool) -> pd.DataFrame:
    """Sort a frame by the common ranking fields when available."""
    sort_fields = [field for field in ("pct_chg", "turnover") if field in frame]
    if not sort_fields:
        return frame
    return frame.sort_values(by=sort_fields, ascending=[ascending] * len(sort_fields))


def _pick_unique_names(
    frame: pd.DataFrame,
    *,
    limit: int,
    excluded: set[str] | None = None,
) -> list[str]:
    """Pick one stable unique stock-name list from a frame."""
    if frame.empty or "name" not in frame:
        return []
    excluded = excluded or set()
    names: list[str] = []
    for name in frame["name"].tolist():
        normalized_name = str(name).strip()
        if not normalized_name or normalized_name in excluded or normalized_name in names:
            continue
        names.append(normalized_name)
        if len(names) >= limit:
            break
    return names


def _collect_alert_messages(
    alerts: list[dict[str, Any]],
    *,
    levels: set[str],
    keywords: tuple[str, ...] = (),
    limit: int,
) -> list[str]:
    """Collect alert messages with simple level and keyword rules."""
    messages: list[str] = []
    normalized_levels = {level.lower() for level in levels}
    for alert in alerts:
        message = str(alert.get("message", ""))
        level = str(alert.get("level", "")).lower()
        if level in normalized_levels:
            messages.append(message)
            continue
        if keywords and any(keyword in message.lower() for keyword in keywords):
            messages.append(message)
    return messages[:limit]
