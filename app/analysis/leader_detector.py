"""Leader detection rules for sector leaders."""

from __future__ import annotations

import pandas as pd


def detect_sector_leaders(quotes: pd.DataFrame) -> pd.DataFrame:
    """Return placeholder leader candidates for each sector."""
    if quotes.empty:
        return pd.DataFrame(
            columns=["sector", "code", "name", "leader_score", "leader_type", "reason"]
        )
    return quotes.head(0).assign(
        sector="",
        leader_score=0.0,
        leader_type="",
        reason="phase one placeholder",
    )
