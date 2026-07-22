"""Leader detection rules for sector leaders."""

from __future__ import annotations

import pandas as pd

LEADER_COLUMNS = ["sector", "code", "name", "leader_score", "leader_type", "reason"]


def detect_sector_leaders(quotes: pd.DataFrame) -> pd.DataFrame:
    """Detect top leader candidates within each sector.

    Phase-one logic uses explainable rule-based scoring built from:

    - pct_chg
    - turnover
    - relative sector strength
    - turnover_rate
    - volume_ratio
    - priority
    """
    if quotes.empty:
        return pd.DataFrame(columns=LEADER_COLUMNS)

    working = quotes.copy()
    for column in ("pct_chg", "turnover", "turnover_rate", "volume_ratio", "priority"):
        if column not in working.columns:
            working[column] = 0.0
        working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0.0)

    results: list[dict[str, str | float]] = []

    for sector, group in working.groupby("sector", sort=False):
        scored_group = _score_sector_group(group.reset_index(drop=True))
        top_group = scored_group.sort_values(
            by=["leader_score", "pct_chg", "turnover"],
            ascending=[False, False, False],
        ).head(3)

        for _, row in top_group.iterrows():
            leader_type = _classify_leader_type(row, scored_group)
            reason = _build_reason(row)
            results.append(
                {
                    "sector": sector,
                    "code": row["code"],
                    "name": row["name"],
                    "leader_score": round(float(row["leader_score"]), 4),
                    "leader_type": leader_type,
                    "reason": reason,
                }
            )

    return pd.DataFrame(results, columns=LEADER_COLUMNS)


def _score_sector_group(group: pd.DataFrame) -> pd.DataFrame:
    """Score one sector group with rank-based normalized factors."""
    scored = group.copy()
    scored["pct_rank"] = _normalized_rank(scored["pct_chg"])
    scored["turnover_rank"] = _normalized_rank(scored["turnover"])
    sector_mean = scored["pct_chg"].mean()
    scored["relative_strength"] = scored["pct_chg"] - sector_mean
    scored["relative_strength_rank"] = _normalized_rank(scored["relative_strength"])
    scored["turnover_rate_rank"] = _normalized_rank(scored["turnover_rate"])
    scored["volume_ratio_rank"] = _normalized_rank(scored["volume_ratio"])

    max_priority = max(float(scored["priority"].max()), 1.0)
    scored["priority_score"] = ((max_priority + 1.0) - scored["priority"]) / max_priority

    scored["leader_score"] = (
        scored["pct_rank"] * 0.25
        + scored["turnover_rank"] * 0.25
        + scored["relative_strength_rank"] * 0.20
        + scored["turnover_rate_rank"] * 0.10
        + scored["volume_ratio_rank"] * 0.10
        + scored["priority_score"] * 0.10
    )
    return scored


def _normalized_rank(series: pd.Series) -> pd.Series:
    """Convert a numeric series into 0..1 rank scores."""
    if len(series) == 1:
        return pd.Series([1.0], index=series.index, dtype=float)
    ranks = series.rank(method="average", ascending=True)
    return ((ranks - 1) / (len(series) - 1)).astype(float)


def _classify_leader_type(row: pd.Series, group: pd.DataFrame) -> str:
    """Assign an explainable leader type."""
    max_pct = float(group["pct_chg"].max())
    max_turnover = float(group["turnover"].max())
    pct_mean = float(group["pct_chg"].mean())
    turnover_rate_median = float(group["turnover_rate"].median())
    volume_ratio_median = float(group["volume_ratio"].median())

    if float(row["pct_chg"]) >= 8.0 and float(row["volume_ratio"]) >= 2.0:
        return "情绪龙头"
    if float(row["turnover"]) == max_turnover and float(row["pct_chg"]) < max_pct:
        return "成交额龙头"
    if (
        float(row["pct_chg"]) >= max(pct_mean * 0.9, 0.0)
        and float(row["turnover_rate"]) >= turnover_rate_median
        and float(row["volume_ratio"]) >= volume_ratio_median
    ):
        return "趋势龙头"
    return "涨幅龙头"


def _build_reason(row: pd.Series) -> str:
    """Build a short reason string for explainability."""
    return (
        f"涨跌幅={float(row['pct_chg']):.2f}, "
        f"成交额={float(row['turnover']):.2f}, "
        f"换手率={float(row['turnover_rate']):.2f}, "
        f"量比={float(row['volume_ratio']):.2f}, "
        f"优先级={int(row['priority'])}"
    )
