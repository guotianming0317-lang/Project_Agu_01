"""Tests for local-first announcement source status helpers."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from app.data_sources.announcement_client import (
    build_announcement_source_status,
    fetch_remote_announcement_items,
    load_announcement_feed_items,
)


class AnnouncementClientTests(unittest.TestCase):
    """Verify announcement source status remains safe and local-first."""

    def test_build_announcement_source_status_reports_ready_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "announcements.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [{"title": "公司公告：订单改善", "content": "AI服务器订单推进。"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            status = build_announcement_source_status(feed_path)

            self.assertEqual("ready", status["status"])
            self.assertEqual("1", status["item_count"])
            self.assertEqual("公司公告：订单改善", status["first_title"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_announcement_source_status_reports_not_configured(self) -> None:
        status = build_announcement_source_status(None)

        self.assertEqual("not-configured", status["status"])
        self.assertEqual("prepare data/news/local_announcement_feed.json", status["next_step"])

    def test_load_announcement_feed_items_returns_normalized_valid_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "announcements.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "公告源：AI服务器订单进展",
                            "content": "公司公告披露AI服务器相关订单进展。",
                            "source": "company-announcement",
                        },
                        {"title": "缺正文"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            items = load_announcement_feed_items(feed_path)

            self.assertEqual(
                [
                    {
                        "title": "公告源：AI服务器订单进展",
                        "content": "公司公告披露AI服务器相关订单进展。",
                        "source": "company-announcement",
                    }
                ],
                items,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_remote_announcement_items_normalizes_common_json_envelope(self) -> None:
        payload = json.dumps(
            {
                "data": [
                    {
                        "notice_title": "公告源：AI服务器订单进展",
                        "summary": "公司公告披露AI服务器订单进展。",
                    },
                    {"notice_title": "缺摘要"},
                ]
            },
            ensure_ascii=False,
        )

        items, status = fetch_remote_announcement_items(
            "https://example.test/announcements.json",
            fetch_text=lambda _url: payload,
        )

        self.assertEqual("ok", status["status"])
        self.assertEqual(
            [
                {
                    "title": "公告源：AI服务器订单进展",
                    "content": "公司公告披露AI服务器订单进展。",
                    "source": "remote-announcement-feed",
                }
            ],
            items,
        )

    def test_fetch_remote_announcement_items_reports_invalid_json(self) -> None:
        items, status = fetch_remote_announcement_items(
            "https://example.test/announcements.json",
            fetch_text=lambda _url: "{broken",
        )

        self.assertEqual([], items)
        self.assertEqual("invalid", status["status"])

    def test_fetch_remote_announcement_items_supports_eastmoney_notice_list(self) -> None:
        payload = json.dumps(
            {
                "data": {
                    "list": [
                        {
                            "title_ch": "半导体公司回购股份公告",
                            "notice_date": "2026-07-23",
                            "art_code": "AN202607230001",
                            "codes": [{"short_name": "示例股份"}],
                        }
                    ]
                }
            },
            ensure_ascii=False,
        )

        items, status = fetch_remote_announcement_items(
            "https://example.test/eastmoney-announcements",
            fetch_text=lambda _url: payload,
        )

        self.assertEqual("ok", status["status"])
        self.assertEqual("半导体公司回购股份公告", items[0]["title"])
        self.assertEqual("半导体公司回购股份公告", items[0]["content"])
        self.assertEqual("示例股份", items[0]["related_stocks"])
        self.assertIn("AN202607230001", items[0]["source_url"])


if __name__ == "__main__":
    unittest.main()
