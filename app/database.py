"""Database bootstrap and persistence utilities."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


def initialize_database(database_path: Path) -> None:
    """Create the SQLite file, ensure the parent directory exists, and bootstrap tables."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode=DELETE;")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL,
                pct_chg REAL,
                turnover REAL,
                volume_ratio REAL,
                turnover_rate REAL,
                sector TEXT,
                quote_source TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                related_stocks TEXT,
                direction TEXT
            )
            """
        )
        _ensure_market_snapshot_quote_source_column(connection)
        connection.commit()


def save_market_snapshots(database_path: Path, rows: list[dict[str, Any]]) -> None:
    """Persist market snapshot rows into SQLite."""
    if not rows:
        return

    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO market_snapshot (
                timestamp, code, name, price, pct_chg, turnover,
                volume_ratio, turnover_rate, sector, quote_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(row.get("timestamp", "")),
                    str(row.get("code", "")),
                    str(row.get("name", "")),
                    _to_float_or_none(row.get("price")),
                    _to_float_or_none(row.get("pct_chg")),
                    _to_float_or_none(row.get("turnover")),
                    _to_float_or_none(row.get("volume_ratio")),
                    _to_float_or_none(row.get("turnover_rate")),
                    str(row.get("sector", "")),
                    str(row.get("quote_source", "")),
                )
                for row in rows
            ],
        )
        connection.commit()


def fetch_market_snapshots(database_path: Path) -> list[dict[str, Any]]:
    """Fetch persisted market snapshots in insert order."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT timestamp, code, name, price, pct_chg, turnover,
                   volume_ratio, turnover_rate, sector, quote_source
            FROM market_snapshot
            ORDER BY id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_latest_market_snapshots(database_path: Path) -> list[dict[str, Any]]:
    """Fetch only the latest timestamp batch of market snapshots."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        latest_timestamp_row = connection.execute(
            "SELECT MAX(timestamp) AS latest_timestamp FROM market_snapshot"
        ).fetchone()
        latest_timestamp = latest_timestamp_row["latest_timestamp"] if latest_timestamp_row else None
        if not latest_timestamp:
            return []
        rows = connection.execute(
            """
            SELECT timestamp, code, name, price, pct_chg, turnover,
                   volume_ratio, turnover_rate, sector, quote_source
            FROM market_snapshot
            WHERE timestamp = ?
            ORDER BY id ASC
            """,
            (latest_timestamp,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_alerts(database_path: Path, rows: list[dict[str, Any]]) -> None:
    """Persist alert rows into SQLite."""
    if not rows:
        return

    with sqlite3.connect(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO alerts (
                timestamp, alert_type, level, message, related_stocks, direction
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(row.get("timestamp", "")),
                    str(row.get("alert_type", "")),
                    str(row.get("level", "")),
                    str(row.get("message", "")),
                    str(row.get("related_stocks", "")),
                    str(row.get("direction", "")),
                )
                for row in rows
            ],
        )
        connection.commit()


def fetch_alerts(database_path: Path) -> list[dict[str, Any]]:
    """Fetch persisted alerts in insert order."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT timestamp, alert_type, level, message, related_stocks, direction
            FROM alerts
            ORDER BY id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_latest_alerts(database_path: Path) -> list[dict[str, Any]]:
    """Fetch only the latest timestamp batch of alerts."""
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        latest_timestamp_row = connection.execute(
            "SELECT MAX(timestamp) AS latest_timestamp FROM alerts"
        ).fetchone()
        latest_timestamp = latest_timestamp_row["latest_timestamp"] if latest_timestamp_row else None
        if not latest_timestamp:
            return []
        rows = connection.execute(
            """
            SELECT timestamp, alert_type, level, message, related_stocks, direction
            FROM alerts
            WHERE timestamp = ?
            ORDER BY id ASC
            """,
            (latest_timestamp,),
        ).fetchall()
    return [dict(row) for row in rows]


def _to_float_or_none(value: Any) -> float | None:
    """Convert values to float when possible, otherwise return None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ensure_market_snapshot_quote_source_column(connection: sqlite3.Connection) -> None:
    """Add the quote_source column for older local databases when missing."""
    existing_columns = {
        str(row[1]).strip()
        for row in connection.execute("PRAGMA table_info(market_snapshot)").fetchall()
    }
    if "quote_source" in existing_columns:
        return
    connection.execute("ALTER TABLE market_snapshot ADD COLUMN quote_source TEXT")
