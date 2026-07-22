"""Tests for the local-first daily news candidate source."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from app.data_sources.news_client import (
    build_news_source_status,
    fetch_daily_news_candidates,
    fetch_remote_news_items,
)


class NewsClientTests(unittest.TestCase):
    """Verify the daily news source returns a stable batch shape."""

    def test_fetch_daily_news_candidates_returns_classifiable_items(self) -> None:
        items = fetch_daily_news_candidates(datetime(2026, 7, 22, 9, 30))

        self.assertGreaterEqual(len(items), 3)
        self.assertTrue(all(str(item.get("title", "")).strip() for item in items))
        self.assertTrue(all(str(item.get("content", "")).strip() for item in items))
        self.assertTrue(all(item.get("source") == "local-auto-candidate" for item in items))
        self.assertTrue(all(item.get("source_date") == "2026-07-22" for item in items))

    def test_fetch_daily_news_candidates_prefers_configured_feed_items(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "source_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "本地新闻源：先进封装订单改善",
                            "content": "Chiplet和先进封装订单预期改善，关注封装链是否扩散。",
                            "source": "manual-feed",
                        },
                        {
                            "title": "半导体设备出口管制升级",
                            "content": "重复标题应被去重，保留第一条本地源记录。",
                            "source": "manual-feed",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            items = fetch_daily_news_candidates(
                datetime(2026, 7, 22, 9, 30),
                feed_path=feed_path,
            )

            self.assertEqual("本地新闻源：先进封装订单改善", items[0]["title"])
            self.assertEqual("manual-feed", items[0]["source"])
            self.assertEqual("2026-07-22", items[0]["source_date"])
            self.assertEqual(
                1,
                sum(1 for item in items if item["title"] == "半导体设备出口管制升级"),
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_daily_news_candidates_ignores_invalid_feed_shape(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "source_feed.json"
        try:
            feed_path.write_text(
                json.dumps({"title": "not-a-list"}, ensure_ascii=False),
                encoding="utf-8",
            )

            items = fetch_daily_news_candidates(
                datetime(2026, 7, 22, 9, 30),
                feed_path=feed_path,
            )

            self.assertGreaterEqual(len(items), 3)
            self.assertTrue(all(item.get("source") == "local-auto-candidate" for item in items))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_news_source_status_reports_available_local_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "source_feed.json"
        try:
            feed_path.write_text(
                json.dumps(
                    [{"title": "本地源", "content": "本地新闻正文。", "source": "manual-feed"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            status = build_news_source_status(feed_path)

            self.assertEqual("local-feed-ready", status["status"])
            self.assertEqual("manual-feed 1", status["source_summary"])
            self.assertEqual("本地源", status["first_title"])
            self.assertEqual("python -m app.main local-news-feed-daily-pass-check", status["next_step"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_news_source_status_reports_invalid_local_feed(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        feed_path = temp_dir / "source_feed.json"
        try:
            feed_path.write_text(
                json.dumps({"title": "not-a-list"}, ensure_ascii=False),
                encoding="utf-8",
            )

            status = build_news_source_status(feed_path)

            self.assertEqual("local-feed-invalid", status["status"])
            self.assertIn("top-level JSON must be a list", status["reason"])
            self.assertEqual("python -m app.main validate-local-news-feed", status["next_step"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_news_source_status_reports_auto_candidate_mode_without_feed(self) -> None:
        status = build_news_source_status(None)

        self.assertEqual("auto-candidate-only", status["status"])
        self.assertEqual("python -m app.main create-local-news-feed-template", status["next_step"])

    def test_fetch_remote_news_items_normalizes_common_json_envelope(self) -> None:
        payload = json.dumps(
            {
                "articles": [
                    {
                        "headline": "远程源：AI服务器订单改善",
                        "summary": "算力硬件链订单预期改善。",
                    },
                    {"headline": "缺摘要"},
                ]
            },
            ensure_ascii=False,
        )

        items, status = fetch_remote_news_items(
            "https://example.test/news.json",
            fetch_text=lambda _url: payload,
        )

        self.assertEqual("ok", status["status"])
        self.assertEqual(
            [
                {
                    "title": "远程源：AI服务器订单改善",
                    "content": "算力硬件链订单预期改善。",
                    "source": "remote-news-feed",
                    "source_date": "",
                }
            ],
            items,
        )

    def test_fetch_remote_news_items_reports_invalid_json(self) -> None:
        items, status = fetch_remote_news_items(
            "https://example.test/news.json",
            fetch_text=lambda _url: "{broken",
        )

        self.assertEqual([], items)
        self.assertEqual("invalid", status["status"])


if __name__ == "__main__":
    unittest.main()
