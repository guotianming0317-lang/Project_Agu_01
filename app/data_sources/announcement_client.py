"""Local-first announcement source status helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

RemoteTextFetcher = Callable[[str], str]


def fetch_remote_announcement_items(
    feed_url: str,
    *,
    fetch_text: RemoteTextFetcher | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Fetch and normalize announcement items from a remote JSON endpoint."""
    normalized_url = str(feed_url or "").strip()
    if not normalized_url:
        return [], {
            "status": "not-configured",
            "reason": "No announcement feed URL configured.",
            "next_step": "set MONITOR_ANNOUNCEMENT_FEED_URL",
        }

    text_fetcher = fetch_text or _fetch_remote_text
    try:
        payload_text = text_fetcher(normalized_url)
    except Exception as exc:  # noqa: BLE001 - keep CLI diagnosis readable
        return [], {
            "status": "fetch-failed",
            "reason": str(exc),
            "next_step": "check announcement URL or network access",
        }

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return [], {
            "status": "invalid",
            "reason": f"JSON error: {exc.msg}",
            "next_step": "check remote announcement JSON shape",
        }

    raw_items = _extract_remote_announcement_rows(payload)
    items = _normalize_announcement_rows(raw_items, default_source="remote-announcement-feed")
    if not items:
        return [], {
            "status": "empty",
            "reason": "No valid title/content items found.",
            "next_step": "check remote announcement field mapping",
        }

    return items, {
        "status": "ok",
        "reason": "Remote announcement feed is readable.",
        "next_step": "python -m app.main start-daily-news-workflow",
    }


def load_announcement_feed_items(feed_path: Path | str | None) -> list[dict[str, str]]:
    """Load valid announcement items from an optional local JSON feed."""
    if not feed_path:
        return []

    resolved_path = Path(feed_path)
    if not resolved_path.exists():
        return []

    try:
        raw_items = json.loads(resolved_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []

    if not isinstance(raw_items, list):
        return []

    return _normalize_announcement_rows(raw_items, default_source="local-announcement-feed")


def _fetch_remote_text(feed_url: str) -> str:
    """Fetch remote JSON text with a browser-like user agent."""
    request = Request(
        feed_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    with urlopen(request, timeout=15) as response:  # noqa: S310 - user-configured URL
        return response.read().decode("utf-8-sig")


def _extract_remote_announcement_rows(payload: object) -> list[object]:
    """Extract announcement rows from common JSON envelope shapes."""
    if isinstance(payload, list):
        return list(payload)
    if not isinstance(payload, dict):
        return []
    for key in ("items", "data", "list", "announcements", "result"):
        value = payload.get(key)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            nested_rows = _extract_remote_announcement_rows(value)
            if nested_rows:
                return nested_rows
    return []


def _normalize_announcement_rows(
    raw_items: list[object],
    *,
    default_source: str,
) -> list[dict[str, str]]:
    """Normalize local or remote announcement rows into daily-news items."""
    valid_items: list[dict[str, str]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title = _first_non_empty_value(
            item,
            ("title", "title_ch", "notice_title", "announcementTitle", "name"),
        )
        content = _first_non_empty_value(
            item,
            ("content", "summary", "notice_content", "announcementContent", "body"),
        )
        if not title:
            continue
        # Public announcement list endpoints often expose title metadata only;
        # keep the title as readable content instead of dropping the notice.
        if not content and not (item.get("title_ch") or item.get("art_code")):
            continue
        content = content or title
        normalized_item = {
            "title": title,
            "content": content,
            "source": str(item.get("source", default_source)).strip() or default_source,
        }
        notice_date = _first_non_empty_value(
            item, ("notice_date", "display_time", "sort_date")
        )
        if notice_date:
            normalized_item["published_at"] = notice_date
        codes = item.get("codes")
        if isinstance(codes, list):
            names = [
                str(code.get("short_name", "")).strip()
                for code in codes
                if isinstance(code, dict) and str(code.get("short_name", "")).strip()
            ]
            if names:
                normalized_item["related_stocks"] = "、".join(dict.fromkeys(names))
        source_url = str(
            item.get("source_url") or item.get("url") or item.get("link") or ""
        ).strip()
        if source_url:
            normalized_item["source_url"] = source_url
        elif str(item.get("art_code", "")).strip():
            normalized_item["source_url"] = (
                "https://data.eastmoney.com/notices/detail/"
                f"{str(item['art_code']).strip()}.html"
            )
        valid_items.append(normalized_item)
    return valid_items


def _first_non_empty_value(item: dict[str, object], keys: tuple[str, ...]) -> str:
    """Return the first non-empty string value from a row."""
    for key in keys:
        value = str(item.get(key, "")).strip()
        if value:
            return value
    return ""


def build_announcement_source_status(feed_path: Path | str | None) -> dict[str, str]:
    """Build a compact status summary for optional announcement input."""
    if not feed_path:
        return {
            "status": "not-configured",
            "feed_path": "",
            "item_count": "0",
            "first_title": "",
            "reason": "No announcement feed path configured.",
            "next_step": "prepare data/news/local_announcement_feed.json",
        }

    resolved_path = Path(feed_path)
    if not resolved_path.exists():
        return {
            "status": "missing",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "first_title": "",
            "reason": "Announcement feed file does not exist.",
            "next_step": "create an announcement JSON list with title/content fields",
        }

    try:
        raw_items = json.loads(resolved_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "first_title": "",
            "reason": f"JSON error: {exc.msg}",
            "next_step": "fix announcement feed JSON",
        }

    if not isinstance(raw_items, list):
        return {
            "status": "invalid",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "first_title": "",
            "reason": "top-level JSON must be a list",
            "next_step": "fix announcement feed JSON",
        }

    valid_items = load_announcement_feed_items(resolved_path)
    if not valid_items:
        return {
            "status": "invalid",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "first_title": "",
            "reason": "No valid title/content items found.",
            "next_step": "add announcement items with title/content",
        }

    return {
        "status": "ready",
        "feed_path": str(resolved_path),
        "item_count": str(len(valid_items)),
        "first_title": str(valid_items[0].get("title", "")).strip(),
        "reason": "Announcement feed is readable.",
        "next_step": "merge announcement feed into daily news workflow",
    }
