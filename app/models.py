"""Core data models used by the project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StockRecord:
    """A stock in the observation universe."""

    code: str
    name: str
    market: str
    sector: str
    sub_sector: str
    priority: int
    chain_group: str = ""
    pool_type: str = "core"
    notes: str = ""


@dataclass(slots=True)
class AlertRecord:
    """A normalized alert payload."""

    level: str
    direction: str
    message: str
