"""Core data models used by the project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StockRecord:
    """A stock in the observation universe."""

    code: str
    name: str
    sector: str
    sub_sector: str
    priority: int
    notes: str = ""


@dataclass(slots=True)
class AlertRecord:
    """A normalized alert payload."""

    level: str
    direction: str
    message: str
