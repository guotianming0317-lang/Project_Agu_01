"""Notification helpers for console-based phase one alerts."""

from __future__ import annotations

from typing import Any


def notify_console(alert: dict[str, Any]) -> None:
    """Print a formatted alert payload to the console."""
    print("【预警】")
    for key, value in alert.items():
        print(f"{key}: {value}")
