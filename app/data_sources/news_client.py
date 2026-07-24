"""Local-first news candidate source for the daily research workflow."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from app.sectors import (
    AI_CPO_SECTOR,
    AI_SERVER_SECTOR,
    SEMICONDUCTOR_EQUIPMENT_SECTOR,
    SEMICONDUCTOR_GAS_SECTOR,
)

RemoteTextFetcher = Callable[[str], str]


def fetch_daily_news_candidates(
    now: datetime | None = None,
    *,
    feed_path: Path | str | None = None,
) -> list[dict[str, str]]:
    """Return daily candidates from a local feed first, then deterministic fallbacks."""
    current_time = now or datetime.now()
    source_date = current_time.strftime("%Y-%m-%d")
    feed_items = _load_local_feed_items(feed_path, source_date=source_date)
    return _dedupe_news_items([*feed_items, *_build_default_news_candidates(source_date)])


def fetch_remote_news_items(
    feed_url: str,
    *,
    fetch_text: RemoteTextFetcher | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Fetch and normalize news items from a remote JSON endpoint."""
    normalized_url = str(feed_url or "").strip()
    if not normalized_url:
        return [], {
            "status": "not-configured",
            "reason": "No news feed URL configured.",
            "next_step": "set MONITOR_NEWS_FEED_URL",
        }

    text_fetcher = fetch_text or _fetch_remote_text
    try:
        payload_text = text_fetcher(normalized_url)
    except Exception as exc:  # noqa: BLE001 - keep CLI diagnosis readable
        return [], {
            "status": "fetch-failed",
            "reason": str(exc),
            "next_step": "check news URL or network access",
        }

    try:
        payload = json.loads(_strip_jsonp_wrapper(payload_text))
    except json.JSONDecodeError as exc:
        return [], {
            "status": "invalid",
            "reason": f"JSON error: {exc.msg}",
            "next_step": "check remote news JSON shape",
        }

    raw_items = _extract_remote_news_rows(payload)
    items = _normalize_local_feed_items(raw_items, source_date="")
    for item in items:
        if not item.get("source") or item.get("source") == "local-feed":
            item["source"] = "remote-news-feed"
    items = [
        {
            "title": item["title"],
            "content": item["content"],
            "source": item["source"],
            "source_date": item.get("source_date", ""),
            **(
                {"source_url": item["source_url"]}
                if str(item.get("source_url", "")).strip()
                else {}
            ),
        }
        for item in items
    ]
    if not items:
        return [], {
            "status": "empty",
            "reason": "No valid title/content items found.",
            "next_step": "check remote news field mapping",
        }

    return items, {
        "status": "ok",
        "reason": "Remote news feed is readable.",
        "next_step": "python -m app.main refresh-daily-news-batch",
    }


def _strip_jsonp_wrapper(payload_text: str) -> str:
    """Accept JSONP responses commonly returned by public finance feeds."""
    text = str(payload_text or "").strip()
    if text.startswith("{") or text.startswith("["):
        return text
    match = re.match(r"^[^(]+\((.*)\)\s*;?\s*$", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text


def build_news_source_status(feed_path: Path | str | None) -> dict[str, str]:
    """Build a compact status summary for the currently configured news source."""
    if not feed_path:
        return {
            "status": "auto-candidate-only",
            "feed_path": "",
            "item_count": "0",
            "source_summary": "local-auto-candidate fallback",
            "first_title": "",
            "reason": "No local feed path configured.",
            "next_step": "python -m app.main create-local-news-feed-template",
        }

    resolved_path = Path(feed_path)
    if not resolved_path.exists():
        return {
            "status": "local-feed-missing",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "source_summary": "",
            "first_title": "",
            "reason": "Local feed file does not exist.",
            "next_step": "python -m app.main create-local-news-feed-template",
        }

    raw_items, error = _load_raw_local_feed_items(resolved_path)
    if error:
        return {
            "status": "local-feed-invalid",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "source_summary": "",
            "first_title": "",
            "reason": error,
            "next_step": "python -m app.main validate-local-news-feed",
        }

    valid_items = _normalize_local_feed_items(raw_items, source_date="")
    if not valid_items:
        return {
            "status": "local-feed-invalid",
            "feed_path": str(resolved_path),
            "item_count": "0",
            "source_summary": "",
            "first_title": "",
            "reason": "No valid title/content items found.",
            "next_step": "python -m app.main validate-local-news-feed",
        }

    return {
        "status": "local-feed-ready",
        "feed_path": str(resolved_path),
        "item_count": str(len(valid_items)),
        "source_summary": _build_feed_source_summary(valid_items),
        "first_title": str(valid_items[0].get("title", "")),
        "reason": "Local feed is readable.",
        "next_step": "python -m app.main local-news-feed-daily-pass-check",
    }


def _build_default_news_candidates(source_date: str) -> list[dict[str, str]]:
    """Build the deterministic fallback candidate batch."""
    return [
        {
            "title": "半导体设备出口管制升级",
            "content": "刻蚀设备与薄膜沉积环节承压，需优先确认设备链核心股票是否同步承压。",
            "source": "local-auto-candidate",
            "source_date": source_date,
            "related_sector": SEMICONDUCTOR_EQUIPMENT_SECTOR,
        },
        {
            "title": "中巨芯U批量供货推进",
            "content": "中巨芯U与华特气体协同改善，电子特气景气度提升，关注气体链是否获得板块跟随。",
            "source": "local-auto-candidate",
            "source_date": source_date,
            "related_sector": SEMICONDUCTOR_GAS_SECTOR,
        },
        {
            "title": "AI服务器需求延续",
            "content": "算力链订单预期改善，服务器、液冷与高速互连方向继续活跃。",
            "source": "local-auto-candidate",
            "source_date": source_date,
            "related_sector": AI_SERVER_SECTOR,
        },
        {
            "title": "光模块链路景气度跟踪",
            "content": "CPO和高速光模块需求维持高关注，重点观察AI光模块方向是否继续保持强势。",
            "source": "local-auto-candidate",
            "source_date": source_date,
            "related_sector": AI_CPO_SECTOR,
        },
    ]


def _load_local_feed_items(
    feed_path: Path | str | None,
    *,
    source_date: str,
) -> list[dict[str, str]]:
    """Load optional local feed items without blocking the daily workflow."""
    if not feed_path:
        return []
    resolved_path = Path(feed_path)
    if not resolved_path.exists():
        return []

    raw_items, error = _load_raw_local_feed_items(resolved_path)
    if error:
        return []
    return _normalize_local_feed_items(raw_items, source_date=source_date)


def _load_raw_local_feed_items(feed_path: Path) -> tuple[list[object], str]:
    """Load raw local feed JSON and return a readable error instead of raising."""
    try:
        raw_items = json.loads(feed_path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        return [], str(exc)
    except json.JSONDecodeError as exc:
        return [], f"JSON error: {exc.msg}"
    if not isinstance(raw_items, list):
        return [], "top-level JSON must be a list"
    return list(raw_items), ""


def _fetch_remote_text(feed_url: str) -> str:
    """Fetch remote JSON text with a browser-like user agent."""
    request = Request(
        feed_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - user-configured URL
            return response.read().decode("utf-8-sig")
    except Exception as urllib_error:  # noqa: BLE001 - use the proven Windows fallback
        curl_executable = shutil.which("curl.exe") or shutil.which("curl")
        if not curl_executable:
            raise urllib_error
        result = subprocess.run(
            [
                curl_executable,
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                "20",
                "-H",
                "User-Agent: Mozilla/5.0",
                "-H",
                "Accept: application/json,text/plain,*/*",
                feed_url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise urllib_error
        return result.stdout.lstrip("\ufeff")


def _extract_remote_news_rows(payload: object) -> list[object]:
    """Extract news rows from common JSON envelope shapes."""
    if isinstance(payload, list):
        return list(payload)
    if not isinstance(payload, dict):
        return []
    for key in ("items", "data", "list", "news", "articles", "result", "fastNewsList", "roll_data"):
        value = payload.get(key)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            nested_rows = _extract_remote_news_rows(value)
            if nested_rows:
                return nested_rows
    return []


def _normalize_local_feed_items(
    raw_items: list[object],
    *,
    source_date: str,
) -> list[dict[str, str]]:
    """Normalize local feed rows into classifiable news items."""
    items: list[dict[str, str]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        title = _first_non_empty_value(raw_item, ("title", "headline", "name"))
        content = _first_non_empty_value(
            raw_item, ("content", "summary", "brief", "description", "body")
        )
        if not title or not content:
            continue
        item = {key: str(value).strip() for key, value in raw_item.items() if value is not None}
        item["title"] = title
        item["content"] = content
        item["source"] = item.get("source") or "local-feed"
        item["source_date"] = item.get("source_date") or source_date
        source_url = (
            item.get("source_url")
            or item.get("url")
            or item.get("link")
            or item.get("articleUrl")
            or item.get("newsUrl")
        )
        if source_url:
            item["source_url"] = str(source_url).strip()
        items.append(item)
    return items


def _first_non_empty_value(item: dict[str, object], keys: tuple[str, ...]) -> str:
    """Return the first non-empty string value from a row."""
    for key in keys:
        value = str(item.get(key, "")).strip()
        if value:
            return value
    return ""


def _build_feed_source_summary(items: list[dict[str, str]]) -> str:
    """Build a stable source-count summary for local feed status."""
    counts: dict[str, int] = {}
    for item in items:
        source = str(item.get("source", "")).strip() or "local-feed"
        counts[source] = counts.get(source, 0) + 1
    return " | ".join(f"{source} {count}" for source, count in counts.items()) if counts else ""


def _dedupe_news_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the first item for each title so local feed entries can override fallbacks."""
    deduped_items: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    for item in items:
        title = str(item.get("title", "")).strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        deduped_items.append(item)
    return deduped_items
