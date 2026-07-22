"""Application entry point for the AI semiconductor monitor demo."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

from app.alerts.alert_rules import evaluate_alerts
from app.alerts.notifier import build_notification_channel_status
from app.analysis.news_classifier import classify_news
from app.config import AppConfig, load_config
from app.data_sources.akshare_client import (
    AKSHARE_SOURCE,
    EASTMONEY_DIRECT_SOURCE,
    LOCAL_SNAPSHOT_SOURCE,
    build_quote_source_display_text,
    detect_local_quote_snapshot_shape,
    fetch_realtime_quotes,
    filter_to_universe,
    get_fetch_path,
    get_local_quote_snapshot_path,
    get_quote_source,
    load_local_quote_snapshot,
    _default_akshare_fetcher,
    _default_eastmoney_fetcher,
)
from app.data_sources.news_client import (
    build_news_source_status,
    fetch_daily_news_candidates,
    fetch_remote_news_items,
)
from app.data_sources.announcement_client import (
    build_announcement_source_status,
    fetch_remote_announcement_items,
    load_announcement_feed_items,
)
from app.database import fetch_latest_market_snapshots, initialize_database
from app.history import build_history_summary
from app.pipeline import build_cycle_console_output, run_monitor_cycle
from app.reports.shared import build_stock_pool_drift_summary_text
from app.reports.evening_report import build_evening_report_from_database
from app.reports.morning_report import build_morning_report_from_database
from app.sectors import (
    AI_CPO_SECTOR,
    AI_SERVER_SECTOR,
    CHIPLET_SECTOR,
    COOLING_SECTOR,
    HBM_SECTOR,
    PCB_SECTOR,
    SEMICONDUCTOR_EQUIPMENT_SECTOR,
    SEMICONDUCTOR_GAS_SECTOR,
    SEMICONDUCTOR_MATERIAL_SECTOR,
)
from app.scheduler import (
    build_job_console_output,
    build_registered_jobs_summary,
    build_scheduler,
    build_scheduler_status_text,
    register_default_jobs,
    run_monitor_job,
    run_scheduler_loop,
)
from app.task_profiles import (
    build_output_profiles_lines,
    build_task_overview_lines,
    TASK_PROFILE_CONFIG_PATH,
)
from app.universe.stock_pool import (
    build_stock_pool_health_summary,
    get_all_stocks,
    get_stocks_by_sector,
)
from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    save_stock_pool_health_snapshot,
)

LOCAL_QUOTE_TEMPLATE_EXAMPLE_PATH = Path("data/examples/real_quote_sample.json")
EMPTY_REVIEW_SENTINEL = "暂无已保存的监控批次。"

NEWS_CHAIN_HINTS: dict[str, str] = {
    SEMICONDUCTOR_EQUIPMENT_SECTOR: "偏半导体设备链，重点看刻蚀、薄膜沉积、清洗、量测等工艺环节。",
    SEMICONDUCTOR_MATERIAL_SECTOR: "偏半导体材料链，重点看硅片、光刻胶、靶材、前驱体等材料环节。",
    SEMICONDUCTOR_GAS_SECTOR: "偏半导体气体链，重点看电子特气、载气和高纯气体供应环节。",
    AI_CPO_SECTOR: "偏AI光模块链，重点看CPO、光模块和高速互连环节。",
    AI_SERVER_SECTOR: "偏AI算力链，重点看服务器、交换机和算力硬件环节。",
    PCB_SECTOR: "偏PCB链，重点看高速板和配套材料环节。",
    COOLING_SECTOR: "偏液冷散热链，重点看液冷、散热和数据中心热管理环节。",
    HBM_SECTOR: "偏存储链，重点看HBM、内存与存储器件环节。",
    CHIPLET_SECTOR: "偏先进封装链，重点看封装、封测和Chiplet环节。",
}
NEWS_BATCH_FILTER_MODES = frozenset(
    {
        "high-priority-only",
        "summary-only",
    }
)
NEWS_BATCH_TEMPLATE_ITEMS: tuple[dict[str, str], ...] = (
    {
        "title": "半导体设备出口管制升级",
        "content": "刻蚀设备与薄膜沉积环节承压。",
    },
    {
        "title": "中巨芯U批量供货推进",
        "content": "中巨芯U与华特气体协同改善，电子特气景气度提升。",
    },
    {
        "title": "AI服务器需求延续",
        "content": "算力链订单预期改善，液冷与高速互连方向继续活跃。",
    },
)
LOCAL_NEWS_FEED_TEMPLATE_ITEMS: tuple[dict[str, str], ...] = (
    {
        "title": "本地源：先进封装订单改善",
        "content": "Chiplet和先进封装订单预期改善，关注封装链是否获得板块扩散。",
        "source": "local-feed-template",
    },
    {
        "title": "本地源：HBM订单继续改善",
        "content": "存储和HBM方向订单预期改善，关注核心池是否跟随。",
        "source": "local-feed-template",
    },
)
LOCAL_ANNOUNCEMENT_FEED_TEMPLATE_ITEMS: tuple[dict[str, str], ...] = (
    {
        "title": "公告源：AI服务器订单进展",
        "content": "公司公告披露AI服务器相关订单或交付进展，关注算力硬件链是否获得确认。",
        "source": "local-announcement-template",
    },
    {
        "title": "公告源：半导体材料扩产进展",
        "content": "公司公告披露半导体材料产能或客户验证进展，关注材料链是否形成扩散。",
        "source": "local-announcement-template",
    },
)


def run_demo(config: AppConfig) -> None:
    """Run a minimal demo that proves the project wiring works."""
    result = run_monitor_cycle(config)
    print(_build_command_banner("demo", config, include_database=False))
    print(build_cycle_console_output(config, result))


def print_latest_database_review(database_path: Path) -> None:
    """Print the latest database-backed evening review."""
    print(_build_latest_database_review_text(database_path))


def print_latest_database_morning_review(database_path: Path) -> None:
    """Print the latest database-backed morning review."""
    print(_build_latest_database_morning_review_text(database_path))


def print_history_review(database_path: Path, timestamp: str) -> None:
    """Print a summary for a selected historical timestamp batch."""
    print(build_history_summary(database_path, timestamp))


def _build_latest_database_review_text(database_path: Path) -> str:
    """Build the latest evening review with one top-line stock-pool drift cue."""
    review_hint = _build_latest_review_use_hint()
    if not fetch_latest_market_snapshots(database_path):
        return "\n".join([review_hint, "", _build_empty_database_review_text()])
    review_body = build_evening_report_from_database(database_path)
    drift_summary = _build_stock_pool_drift_summary_for_review()
    if not drift_summary:
        return "\n".join([review_hint, "", review_body])
    return "\n".join([review_hint, "", drift_summary, "", review_body])


def _build_latest_database_morning_review_text(database_path: Path) -> str:
    """Build the latest morning review with one top-line stock-pool drift cue."""
    review_hint = _build_latest_review_use_hint()
    if not fetch_latest_market_snapshots(database_path):
        return "\n".join(
            [review_hint, "", _build_empty_database_review_text(label="Latest Morning Review")]
        )
    review_body = build_morning_report_from_database(database_path)
    drift_summary = _build_stock_pool_drift_summary_for_review()
    if not drift_summary:
        return "\n".join([review_hint, "", review_body])
    return "\n".join([review_hint, "", drift_summary, "", review_body])


def _build_stock_pool_drift_summary_for_review() -> str:
    """Build one compact shared stock-pool drift cue for read-only review modes."""
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)
    return build_stock_pool_drift_summary_text(
        structure_summary=str(stock_pool_summary.get("structure_summary", "")).strip(),
        comparison_tag_groups=list(stock_pool_comparison.get("comparison_tag_groups", [])),
        highlight_summary=str(stock_pool_comparison.get("highlight_summary", "")).strip(),
    )


def _build_latest_review_use_hint() -> str:
    """Build one compact hint for when the stored review is most useful."""
    return "\n".join(
        [
            "复盘阅读提示",
            "最佳阅读时机：先运行 python -m app.main start-daily-news-workflow",
            "用途：把这里的数据库复盘作为每日新闻筛选后的市场总结。",
        ]
    )


def main(argv: list[str] | None = None) -> None:
    """Bootstrap the application or dispatch a lightweight read mode."""
    argv = list(argv) if argv is not None else []
    config = load_config()
    initialize_database(config.database_path)

    if argv and argv[0] == "run-scheduler":
        _run_scheduler_mode(config)
        return

    if not argv:
        run_demo(config)
        return

    command = argv[0]
    if command in {"help", "--help", "-h"}:
        print(_build_command_help_text())
        return
    if command == "latest-morning-review":
        print_latest_database_morning_review(config.database_path)
        return
    if command == "classify-news":
        title = argv[1] if len(argv) > 1 else ""
        content = argv[2] if len(argv) > 2 else ""
        print(_build_news_classification_text(title, content))
        return
    if command == "classify-news-batch":
        batch_path = argv[1] if len(argv) > 1 else ""
        filter_mode = argv[2] if len(argv) > 2 else ""
        print(_build_news_batch_classification_text(batch_path, filter_mode=filter_mode))
        return
    if command == "validate-news-batch":
        batch_path = argv[1] if len(argv) > 1 else ""
        print(_build_news_batch_validation_text(batch_path))
        return
    if command == "news-batch-first-pass":
        batch_path = argv[1] if len(argv) > 1 else ""
        print(_build_news_batch_first_pass_text(batch_path))
        return
    if command == "news-batch-priority-pass":
        batch_path = argv[1] if len(argv) > 1 else ""
        print(_build_news_batch_priority_pass_text(batch_path))
        return
    if command == "news-batch-priority-export":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_news_batch_priority_export_text(batch_path, export_path))
        return
    if command == "batch-news-daily-flow":
        batch_path = argv[1] if len(argv) > 1 else ""
        print(_build_batch_news_daily_flow_text(batch_path))
        return
    if command == "batch-news-daily-export":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_batch_news_daily_export_text(batch_path, export_path))
        return
    if command == "create-daily-news-batch":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_daily_news_batch_template_text(target_path))
        return
    if command == "refresh-daily-news-batch":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_refresh_daily_news_batch_text(target_path))
        return
    if command == "refresh-external-feeds-pass-check":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_refresh_external_feeds_pass_check_text(batch_path, export_path))
        return
    if command == "external-feeds-status":
        print(_build_external_feeds_status_text())
        return
    if command == "news-source-status":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_news_source_status_text(target_path))
        return
    if command == "announcement-source-status":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_announcement_source_status_text(target_path))
        return
    if command == "create-local-announcement-feed-template":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_announcement_feed_template_text(target_path))
        return
    if command == "validate-local-announcement-feed":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_announcement_feed_validation_text(target_path))
        return
    if command == "refresh-local-announcement-feed":
        target_path = argv[1] if len(argv) > 1 else ""
        feed_url = argv[2] if len(argv) > 2 else ""
        print(_build_refresh_local_announcement_feed_text(target_path, feed_url))
        return
    if command == "notification-status":
        print(_build_notification_status_text())
        return
    if command == "create-local-news-feed-template":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_news_feed_template_text(target_path))
        return
    if command == "validate-local-news-feed":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_news_feed_validation_text(target_path))
        return
    if command == "append-local-news-feed":
        title = argv[1] if len(argv) > 1 else ""
        content = argv[2] if len(argv) > 2 else ""
        target_path = argv[3] if len(argv) > 3 else ""
        print(_build_append_local_news_feed_text(title, content, target_path))
        return
    if command == "refresh-local-news-feed":
        target_path = argv[1] if len(argv) > 1 else ""
        feed_url = argv[2] if len(argv) > 2 else ""
        print(_build_refresh_local_news_feed_text(target_path, feed_url))
        return
    if command == "local-news-feed-daily-pass-check":
        feed_path = argv[1] if len(argv) > 1 else ""
        batch_path = argv[2] if len(argv) > 2 else ""
        export_path = argv[3] if len(argv) > 3 else ""
        print(_build_local_news_feed_daily_pass_check_text(feed_path, batch_path, export_path))
        return
    if command == "create-local-quote-template":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_quote_template_text(target_path))
        return
    if command == "refresh-local-quote-snapshot":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_refresh_local_quote_snapshot_text(target_path))
        return
    if command == "refresh-local-quote-pass-check":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_refresh_local_quote_pass_check_text(config, target_path))
        return
    if command == "import-local-quote":
        source_path = argv[1] if len(argv) > 1 else ""
        target_path = argv[2] if len(argv) > 2 else ""
        print(_build_import_local_quote_text(source_path, target_path))
        return
    if command == "import-local-quote-pass-check":
        source_path = argv[1] if len(argv) > 1 else ""
        target_path = argv[2] if len(argv) > 2 else ""
        print(_build_import_local_quote_pass_check_text(config, source_path, target_path))
        return
    if command == "start-daily-news-workflow":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_start_daily_news_workflow_text(batch_path, export_path))
        return
    if command == "mainline-smoke-test":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_mainline_smoke_test_text(config, batch_path, export_path))
        return
    if command == "phase-one-ready-check":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_phase_one_ready_check_text(config, batch_path, export_path))
        return
    if command == "phase-two-ready-check":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_phase_two_ready_check_text(config, batch_path, export_path))
        return
    if command == "phase-three-ready-check":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        print(_build_phase_three_ready_check_text(config, batch_path, export_path))
        return
    if command == "create-news-batch-template":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_news_batch_template_text(target_path))
        return
    if command == "export-news-batch":
        batch_path = argv[1] if len(argv) > 1 else ""
        export_path = argv[2] if len(argv) > 2 else ""
        filter_mode = argv[3] if len(argv) > 3 else ""
        export_path, filter_mode = _normalize_export_news_batch_args(export_path, filter_mode)
        print(
            _export_news_batch_summary_text(
                batch_path,
                export_path,
                filter_mode=filter_mode,
            )
        )
        return
    if command == "self-check":
        print(_build_self_check_text(config))
        return
    if command == "latest-review":
        print_latest_database_review(config.database_path)
        return
    if command == "history-review":
        timestamp = argv[1] if len(argv) > 1 else ""
        print_history_review(config.database_path, timestamp)
        return
    if command == "scheduler-status":
        print(build_scheduler_status_text(config, build_scheduler()))
        return
    if command == "daily-automation-status":
        print(_build_daily_automation_status_text(config))
        return
    if command == "validate-task-profiles":
        print(_build_task_profile_validation_text())
        return
    if command == "full-regression-check":
        print(_build_full_regression_check_text())
        return
    if command == "quote-connectivity-check":
        print(_build_quote_connectivity_check_text())
        return
    if command == "validate-local-quote":
        target_path = argv[1] if len(argv) > 1 else ""
        print(_build_local_quote_validation_text(target_path))
        return
    if command == "run-job-now":
        _run_job_now(config, argv)
        return
    if command == "validate-stock-pool":
        summary = build_stock_pool_health_summary()
        comparison = build_stock_pool_health_comparison(summary)
        print(_build_stock_pool_validation_text(summary, comparison))
        save_stock_pool_health_snapshot(summary)
        return

    print(f"Unknown command: {command}")
    print("")
    print(_build_command_help_text())


def _run_scheduler_mode(config: AppConfig) -> None:
    """Start scheduler mode only when explicitly enabled."""
    if not config.enable_scheduler:
        print("Scheduler mode is disabled. Set MONITOR_ENABLE_SCHEDULER=true to enable it.")
        return

    scheduler = build_scheduler()
    print(_build_command_banner("run-scheduler", config))
    print("\n".join(build_task_overview_lines()))
    print("")
    print(build_scheduler_status_text(config, scheduler))
    register_default_jobs(scheduler, config)
    print("Scheduler mode enabled.")
    print(run_scheduler_loop(scheduler))


def _run_job_now(config: AppConfig, argv: list[str]) -> None:
    """Run one scheduler-style monitor job immediately."""
    job_id = argv[1] if len(argv) > 1 else "manual"
    result = run_monitor_job(config, job_id=job_id)
    print(_build_command_banner("run-job-now", config))
    print(build_job_console_output(config, result, job_id=job_id))
    print("Manual scheduler job completed.")


def _build_command_banner(
    mode: str,
    config: AppConfig,
    *,
    include_database: bool = True,
) -> str:
    """Build a small shared startup banner for manual command modes."""
    lines = [
        "监控命令",
        f"模式：{mode}",
        f"运行环境：{config.environment}",
    ]
    if include_database:
        lines.append(f"数据库：{config.database_url}")
    return "\n".join(lines)


def _build_command_help_text() -> str:
    """Build a small command guide for local phase-one usage."""
    lines = [
        "AI 半导体监控命令",
        "",
        "日常使用：",
        "- python -m app.main self-check",
        "- 先确认本地主线是否可用",
        "- python -m app.main mainline-smoke-test",
        "- 跑一次压缩版每日主线检查",
        "- python -m app.main phase-one-ready-check",
        "- 汇总判断阶段一可运行版本是否就绪",
        "- python -m app.main phase-two-ready-check",
        "- 汇总判断阶段二增强版是否就绪",
        "- python -m app.main phase-three-ready-check",
        "- 汇总判断阶段三外部集成框架是否就绪",
        "- python -m app.main daily-automation-status",
        "- 查看每日自动化、调度和新闻源状态",
        "- python -m app.main full-regression-check",
        "- 跑完整回归测试集合",
        "- python -m app.main quote-connectivity-check",
        "- 检查实时行情是依赖可用还是网络受阻",
        "- python -m app.main create-local-quote-template",
        "- 创建本地真实行情快照模板",
        "- python -m app.main refresh-local-quote-snapshot",
        "- 刷新一份本地实时行情快照",
        "- python -m app.main refresh-local-quote-pass-check",
        "- 一次完成刷新 -> 校验 -> 自检",
        "- python -m app.main import-local-quote",
        "- 导入外部行情 JSON 到本地快照路径",
        "- python -m app.main import-local-quote-pass-check",
        "- 一次完成导入 -> 校验 -> 自检",
        "- python -m app.main validate-local-quote",
        "- 校验本地真实行情快照是否可用",
        "- python -m app.main start-daily-news-workflow",
        "- 启动当日新闻优先级流程",
        "- python -m app.main refresh-daily-news-batch",
        "- 刷新当日自动新闻候选源",
        "- python -m app.main refresh-external-feeds-pass-check",
        "- 一次完成远程新闻/公告刷新 -> 每日新闻源刷新 -> 优先摘要导出",
        "- python -m app.main external-feeds-status",
        "- 只读检查远程新闻/公告 URL 与本地源状态",
        "- python -m app.main news-source-status",
        "- python -m app.main announcement-source-status",
        "- python -m app.main notification-status",
        "- 查看当前新闻源模式和下一步",
        "- python -m app.main create-local-announcement-feed-template",
        "- 创建可接入 MONITOR_ANNOUNCEMENT_FEED_PATH 的本地公告源模板",
        "- python -m app.main validate-local-announcement-feed",
        "- 校验本地公告源 JSON 是否可用",
        "- python -m app.main refresh-local-announcement-feed",
        "- 从 MONITOR_ANNOUNCEMENT_FEED_URL 刷新本地公告源 JSON",
        "- python -m app.main create-local-news-feed-template",
        "- 创建可接入 MONITOR_NEWS_FEED_PATH 的本地新闻源模板",
        "- python -m app.main validate-local-news-feed",
        "- 校验本地新闻源 JSON 是否可用",
        "- python -m app.main append-local-news-feed",
        "- 追加单条新闻到本地新闻源 JSON",
        "- python -m app.main refresh-local-news-feed",
        "- 从 MONITOR_NEWS_FEED_URL 刷新本地新闻源 JSON",
        "- python -m app.main local-news-feed-daily-pass-check",
        "- 一次完成本地新闻源校验 -> 每日新闻源刷新 -> 优先摘要导出",
        "- python -m app.main latest-review",
        "- 读取最新市场复盘",
        "- 可选可视化页面：streamlit run app/dashboard/streamlit_app.py",
        "- 如需单独准备今日新闻源文件：",
        "- python -m app.main create-daily-news-batch",
        "- python -m app.main refresh-daily-news-batch",
        "- python -m app.main refresh-external-feeds-pass-check",
        "- python -m app.main external-feeds-status",
        "- python -m app.main news-source-status",
        "- python -m app.main create-local-news-feed-template",
        "- python -m app.main validate-local-news-feed",
        "- python -m app.main append-local-news-feed",
        "- python -m app.main refresh-local-news-feed",
        "- python -m app.main local-news-feed-daily-pass-check",
        "- python -m app.main create-local-announcement-feed-template",
        "- python -m app.main validate-local-announcement-feed",
        "- python -m app.main refresh-local-announcement-feed",
        "- 每日归档默认写入 data/news/news_batch_priority_summary_YYYYMMDD.md",
        "",
        "成功信号：",
        "- self-check 后看：主流程：ok",
        "- self-check 后看：真实数据状态：live-pass 或 snapshot-pass",
        "- self-check 后看：股票池校验：valid",
        "- start-daily-news-workflow 后看：今日摘要文件：data/news/news_batch_priority_summary_YYYYMMDD.md",
        "- start-daily-news-workflow 后看：已保存优先级摘要到：data/news/news_batch_priority_summary_YYYYMMDD.md",
        "- 每日运行后优先打开：data/news/news_batch_priority_summary_YYYYMMDD.md",
        "",
        "最小可运行检查：",
        "- python -m app.main",
        "- python -m app.main latest-review",
        "- python -m app.main validate-stock-pool",
        "- streamlit run app/dashboard/streamlit_app.py",
        "",
        "批量新闻速查：",
        '- python -m app.main create-news-batch-template "news_batch.json"',
        "- 可把 news_batch.example.json 复制为 news_batch.json",
        "- 首次运行时，把 news_batch.json 放在项目根目录最省事",
        "- 如果文件在其他位置，直接传完整路径",
        '- python -m app.main validate-news-batch "news_batch.json"',
        '- python -m app.main news-batch-first-pass "news_batch.json"',
        '- python -m app.main news-batch-priority-pass "news_batch.json"',
        '- python -m app.main news-batch-priority-export "news_batch.json"',
        '- python -m app.main batch-news-daily-flow "news_batch.json"',
        '- python -m app.main batch-news-daily-export "news_batch.json"',
        "- python -m app.main create-daily-news-batch",
        "- python -m app.main refresh-daily-news-batch",
        "- python -m app.main refresh-external-feeds-pass-check",
        "- python -m app.main external-feeds-status",
        "- python -m app.main news-source-status",
        "- python -m app.main create-local-news-feed-template",
        "- python -m app.main validate-local-news-feed",
        "- python -m app.main append-local-news-feed",
        "- python -m app.main refresh-local-news-feed",
        "- python -m app.main local-news-feed-daily-pass-check",
        "- python -m app.main create-local-announcement-feed-template",
        "- python -m app.main validate-local-announcement-feed",
        "- python -m app.main refresh-local-announcement-feed",
        "- python -m app.main create-local-quote-template",
        "- python -m app.main refresh-local-quote-snapshot",
        "- python -m app.main refresh-local-quote-pass-check",
        "- python -m app.main import-local-quote",
        "- python -m app.main import-local-quote-pass-check",
        "- python -m app.main validate-local-quote",
        "- python -m app.main mainline-smoke-test",
        "- python -m app.main phase-one-ready-check",
        "- python -m app.main phase-two-ready-check",
        "- python -m app.main phase-three-ready-check",
        "- python -m app.main full-regression-check",
        "- python -m app.main daily-automation-status",
        "- python -m app.main quote-connectivity-check",
        "- python -m app.main start-daily-news-workflow",
        "- python -m app.main news-source-status",
        "- python -m app.main announcement-source-status",
        "- python -m app.main notification-status",
        "- 每日流程默认归档到 data/news/news_batch_priority_summary_YYYYMMDD.md",
        '- python -m app.main classify-news-batch "news_batch.json" summary-only',
        '- python -m app.main export-news-batch "news_batch.json"',
        "- 通用 export-news-batch 默认保存到源文件旁边",
        "",
        "完整命令目录：",
        "- python -m app.main",
        '- python -m app.main classify-news "title" "content"',
        '- python -m app.main create-news-batch-template "news_batch.json"',
        '- python -m app.main validate-news-batch "news_batch.json"',
        '- python -m app.main news-batch-first-pass "news_batch.json"',
        '- python -m app.main news-batch-priority-pass "news_batch.json"',
        '- python -m app.main news-batch-priority-export "news_batch.json"',
        '- python -m app.main batch-news-daily-flow "news_batch.json"',
        '- python -m app.main batch-news-daily-export "news_batch.json"',
        "- python -m app.main create-daily-news-batch",
        "- python -m app.main refresh-daily-news-batch",
        "- python -m app.main refresh-external-feeds-pass-check",
        "- python -m app.main external-feeds-status",
        "- python -m app.main create-local-news-feed-template",
        "- python -m app.main validate-local-news-feed",
        "- python -m app.main append-local-news-feed",
        "- python -m app.main refresh-local-news-feed",
        "- python -m app.main local-news-feed-daily-pass-check",
        "- python -m app.main create-local-announcement-feed-template",
        "- python -m app.main validate-local-announcement-feed",
        "- python -m app.main refresh-local-announcement-feed",
        "- python -m app.main create-local-quote-template",
        "- python -m app.main import-local-quote",
        "- python -m app.main import-local-quote-pass-check",
        "- python -m app.main validate-local-quote",
        "- python -m app.main mainline-smoke-test",
        "- python -m app.main phase-one-ready-check",
        "- python -m app.main phase-two-ready-check",
        "- python -m app.main full-regression-check",
        "- python -m app.main daily-automation-status",
        "- python -m app.main quote-connectivity-check",
        "- python -m app.main start-daily-news-workflow",
        '- python -m app.main classify-news-batch "news_batch.json"',
        '- python -m app.main classify-news-batch "news_batch.json" high-priority-only',
        '- python -m app.main classify-news-batch "news_batch.json" summary-only',
        '- python -m app.main export-news-batch "news_batch.json" "news_batch_summary.md"',
        '- python -m app.main export-news-batch "news_batch.json"',
        "- python -m app.main self-check",
        "- python -m app.main latest-review",
        "- python -m app.main latest-morning-review",
        '- python -m app.main history-review "YYYY-MM-DD HH:MM:SS"',
        "- python -m app.main scheduler-status",
        "- python -m app.main daily-automation-status",
        "- python -m app.main validate-task-profiles",
        "- python -m app.main run-job-now [job-id]",
        "- python -m app.main run-scheduler",
        "- python -m app.main validate-stock-pool",
    ]
    return "\n".join(lines)


def _build_empty_database_review_text(*, label: str = "Latest Database Review") -> str:
    """Build a first-run hint when no persisted monitor batch exists yet."""
    return "\n".join(
        [
            "最新数据库复盘" if label == "Latest Database Review" else label,
            "",
            EMPTY_REVIEW_SENTINEL,
            "请先运行 `python -m app.main` 生成第一批本地监控数据。",
        ]
    )


def _build_self_check_text(config: AppConfig) -> str:
    """Build one compact minimal-runnable acceptance summary."""
    cycle_result = run_monitor_cycle(config)
    latest_review_text = _build_latest_database_review_text(config.database_path)
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_comparison = build_stock_pool_health_comparison(stock_pool_summary)
    save_stock_pool_health_snapshot(stock_pool_summary)

    latest_review_ok = EMPTY_REVIEW_SENTINEL not in latest_review_text
    stock_pool_status = str(stock_pool_summary.get("status", "unknown"))
    quote_runtime_status = _build_quote_runtime_status(cycle_result.quote_source)
    lines = [
        "最小可运行自检",
        "",
        f"主流程：ok ({cycle_result.snapshot_time})",
        f"行情来源：{build_quote_source_display_text(cycle_result.quote_source)}",
        *([f"直连路径：{cycle_result.fetch_path}"] if str(cycle_result.fetch_path).strip() else []),
        f"真实数据状态：{quote_runtime_status['status_line']}",
        f"写入快照：{len(cycle_result.market_rows)}",
        f"生成预警：{len(cycle_result.alerts)}",
        f"最新复盘：{'ok' if latest_review_ok else 'needs data'}",
        f"股票池校验：{stock_pool_status}",
    ]
    structure_summary = str(stock_pool_summary.get("structure_summary", "")).strip()
    if structure_summary:
        lines.append(f"股票池结构：{structure_summary}")
    highlight_summary = str(stock_pool_comparison.get("highlight_summary", "")).strip()
    if highlight_summary:
        lines.append(f"股票池变化提示：{highlight_summary}")
    lines.extend(
        [
            "",
            f"建议诊断：{_build_self_check_recommended_diagnosis(quote_runtime_status['status_line'])}",
            f"下一步：{quote_runtime_status['next_step']}",
            "可选可视化页面：streamlit run app/dashboard/streamlit_app.py",
        ]
    )
    return "\n".join(lines)


def _build_self_check_recommended_diagnosis(status_line: str) -> str:
    """Return one short recommendation for the next most useful diagnosis step."""
    normalized_status = str(status_line).strip()
    if normalized_status == "snapshot-pass":
        return (
            "本地真实行情快照路径已通过，继续运行 python -m app.main "
            "start-daily-news-workflow。"
        )
    if normalized_status == "live-pass":
        return (
            "实时行情直连路径已通过，继续运行 python -m app.main "
            "start-daily-news-workflow。"
        )
    return (
        "先运行 python -m app.main validate-local-quote。若本地快照有效，"
        "再运行 python -m app.main quote-connectivity-check。"
    )


def _build_mainline_smoke_test_text(
    config: AppConfig,
    batch_path: str,
    export_path: str,
) -> str:
    """Run the compact daily mainline and return one short acceptance summary."""
    self_check_text = _build_self_check_text(config)
    normalized_batch_path = str(batch_path or "").strip()
    normalized_export_path = str(export_path or "").strip()
    resolved_batch_path = (
        Path(normalized_batch_path)
        if normalized_batch_path
        else _build_default_daily_news_batch_path()
    )
    resolved_export_path = (
        Path(normalized_export_path)
        if normalized_export_path
        else _build_default_daily_news_export_path()
    )
    default_feed_path = _build_default_local_news_feed_path()
    local_feed_available = (
        not normalized_batch_path
        and default_feed_path.exists()
    )
    if local_feed_available:
        _build_local_news_feed_daily_pass_check_text(
            str(default_feed_path),
            str(resolved_batch_path),
            str(resolved_export_path),
        )
    else:
        _build_start_daily_news_workflow_text(
            normalized_batch_path,
            normalized_export_path,
        )
    latest_review_text = _build_latest_database_review_text(config.database_path)

    self_check_ok = (
        "主流程：ok" in self_check_text
        and "股票池校验：valid" in self_check_text
    )
    real_data_ok = "真实数据状态：live-pass" in self_check_text
    real_data_backup_ok = "真实数据状态：snapshot-pass" in self_check_text
    workflow_ok = resolved_batch_path.exists() and resolved_export_path.exists()
    latest_review_ok = EMPTY_REVIEW_SENTINEL not in latest_review_text

    lines = [
        "每日主线烟雾测试",
        "",
        f"自检：{'通过' if self_check_ok else '需要检查'}",
        (
            "真实数据：live-pass"
            if real_data_ok
            else "真实数据：snapshot-pass"
            if real_data_backup_ok
            else "真实数据：not-passed"
        ),
        f"每日工作流：{'通过' if workflow_ok else '需要检查'}",
        f"最新复盘：{'通过' if latest_review_ok else '需要检查'}",
        f"新闻源模式：{'本地新闻源' if local_feed_available else '自动候选'}",
        *([f"本地新闻源：{default_feed_path}"] if local_feed_available else []),
        f"新闻源文件：{resolved_batch_path}",
        f"摘要文件：{resolved_export_path}",
        "优先打开文件：data/news/news_batch_priority_summary_YYYYMMDD.md",
        "",
        "这条命令会压缩执行每日主线：",
        "self-check -> start-daily-news-workflow -> latest-review",
    ]
    return "\n".join(lines)


def _build_phase_one_ready_check_text(
    config: AppConfig,
    batch_path: str,
    export_path: str,
) -> str:
    """Build one final local-runnable readiness check for phase one."""
    self_check_text = _build_self_check_text(config)
    smoke_text = _build_mainline_smoke_test_text(config, batch_path, export_path)
    stock_pool_summary = build_stock_pool_health_summary()
    stock_pool_status = str(stock_pool_summary.get("status", "unknown")).strip()
    self_check_ok = "主流程：ok" in self_check_text and "股票池校验：valid" in self_check_text
    smoke_ok = (
        "每日工作流：通过" in smoke_text
        and "最新复盘：通过" in smoke_text
    )
    ready = self_check_ok and stock_pool_status == "valid" and smoke_ok
    lines = [
        "阶段一就绪检查",
        "",
        f"自检：{'通过' if self_check_ok else '需要检查'}",
        f"股票池：{stock_pool_status}",
        f"每日主线：{'通过' if '每日工作流：通过' in smoke_text else '需要检查'}",
        f"最新复盘：{'通过' if '最新复盘：通过' in smoke_text else '需要检查'}",
        (
            "结果：阶段一可运行版本已就绪。"
            if ready
            else "结果：阶段一可运行版本仍需检查。"
        ),
        "",
        smoke_text,
    ]
    return "\n".join(lines)


def _build_phase_two_ready_check_text(
    config: AppConfig,
    batch_path: str,
    export_path: str,
) -> str:
    """Build the phase-two enhanced local readiness summary."""
    phase_one_text = _build_phase_one_ready_check_text(config, batch_path, export_path)
    feed_path = _get_daily_news_feed_path() or _build_default_local_news_feed_path()
    news_status = build_news_source_status(feed_path if feed_path.exists() else None)
    scheduler_status_text = build_scheduler_status_text(config, build_scheduler())
    enhanced_news_ready = (
        "每日工作流：通过" in phase_one_text
        and "最新复盘：通过" in phase_one_text
    )
    scheduler_checkable = "Runtime mode:" in scheduler_status_text
    phase_one_ready = "结果：阶段一可运行版本已就绪。" in phase_one_text
    ready = phase_one_ready and enhanced_news_ready and scheduler_checkable
    lines = [
        "阶段二就绪检查",
        "",
        f"阶段一：{'通过' if phase_one_ready else '需要检查'}",
        f"新闻源状态：{news_status['status']}",
        f"新闻源下一步：{news_status['next_step']}",
        f"调度入口：{'可检查' if scheduler_checkable else '需要检查'}",
        f"每日新闻增强链路：{'通过' if enhanced_news_ready else '需要检查'}",
        (
            "结果：阶段二增强版已就绪。"
            if ready
            else "结果：阶段二增强版仍需检查。"
        ),
        "",
        phase_one_text,
    ]
    return "\n".join(lines)


def _build_phase_three_ready_check_text(
    config: AppConfig,
    batch_path: str,
    export_path: str,
) -> str:
    """Build the phase-three external-integration readiness summary."""
    phase_two_text = _build_phase_two_ready_check_text(config, batch_path, export_path)
    announcement_status = build_announcement_source_status(_get_announcement_feed_path())
    notification_status = build_notification_channel_status()
    automation_text = _build_daily_automation_status_text(config)
    phase_two_ready = "结果：阶段二增强版已就绪。" in phase_two_text
    announcement_checkable = announcement_status["status"] in {
        "not-configured",
        "missing",
        "invalid",
        "ready",
    }
    notification_checkable = notification_status["status"] in {
        "console-only",
        "webhook-ready",
    }
    automation_checkable = "每日自动化状态" in automation_text
    ready = (
        phase_two_ready
        and announcement_checkable
        and notification_checkable
        and automation_checkable
    )
    return "\n".join(
        [
            "阶段三就绪检查",
            "",
            f"阶段二：{'通过' if phase_two_ready else '需要检查'}",
            f"公告源状态：{announcement_status['status']}",
            f"推送状态：{notification_status['status']}",
            f"自动化状态：{'可检查' if automation_checkable else '需要检查'}",
            (
                "结果：阶段三外部集成框架已就绪。"
                if ready
                else "结果：阶段三外部集成框架仍需检查。"
            ),
            "",
            "公告源下一步：" + announcement_status["next_step"],
            "推送下一步：" + notification_status["next_step"],
            "",
            phase_two_text,
        ]
    )


def _build_daily_automation_status_text(config: AppConfig) -> str:
    """Build one compact daily automation status summary."""
    scheduler = build_scheduler()
    scheduler_status_text = build_scheduler_status_text(config, scheduler)
    runtime_mode = _extract_prefixed_value(scheduler_status_text, "Runtime mode:")
    news_status = build_news_source_status(_get_daily_news_feed_path())
    next_step = _extract_prefixed_value(scheduler_status_text, "Next recommended command:")
    return "\n".join(
        [
            "每日自动化状态",
            "",
            f"调度运行时：{runtime_mode or 'unknown'}",
            f"注册任务：{build_registered_jobs_summary()}",
            f"新闻源状态：{news_status['status']}",
            f"新闻源下一步：{news_status['next_step']}",
            f"下一步：{next_step or 'python -m app.main scheduler-status'}",
        ]
    )


def _extract_prefixed_value(text: str, prefix: str) -> str:
    """Extract the first line value after a fixed prefix."""
    for line in str(text or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _build_full_regression_check_text() -> str:
    """Run the full discovered regression suite and return one compact summary."""
    suite = unittest.TestLoader().discover("tests", pattern="test_*.py")
    previous_disable_level = logging.root.manager.disable
    with open(os.devnull, "w", encoding="utf-8") as quiet_stream:
        runner = unittest.TextTestRunner(stream=quiet_stream, verbosity=0)
        logging.disable(logging.CRITICAL)
        try:
            result = runner.run(suite)
        finally:
            logging.disable(previous_disable_level)

    status = "ok" if result.wasSuccessful() else "failed"
    total = getattr(result, "testsRun", 0)
    failure_count = len(getattr(result, "failures", []))
    error_count = len(getattr(result, "errors", []))
    skipped_count = len(getattr(result, "skipped", []))

    lines = [
        "Full Regression Check",
        "",
        f"Status: {status}",
        f"Tests run: {total}",
        f"Failures: {failure_count}",
        f"Errors: {error_count}",
        f"Skipped: {skipped_count}",
        "Runner mode: unittest discover -s tests -p \"test_*.py\"",
    ]
    if result.wasSuccessful():
        lines.append("Result: the full discovered regression suite passed.")
    else:
        lines.append("Result: review the failing test details from the full runner output.")
    return "\n".join(lines)


def _build_quote_connectivity_check_text() -> str:
    """Check whether realtime quote access is dependency-ready and reachable."""
    akshare_spec = importlib.util.find_spec("akshare")
    dependency_status = "installed" if akshare_spec is not None else "missing"
    connectivity = _check_realtime_quote_connectivity(include_akshare=akshare_spec is not None)

    if connectivity["status"] != "ok":
        source_label = str(connectivity.get("source_label", "")).strip()
        result_line = "结果：实时行情仍不可达。"
        if dependency_status == "missing":
            result_line = (
                "结果：akshare 未安装，直连备用源也仍不可达。"
            )
        return "\n".join(
            [
                "实时行情连通性检查",
                "",
                f"依赖状态：{dependency_status}",
                "端点访问：blocked",
                result_line,
                f"失败类型：{connectivity['failure_type']}",
                f"诊断：{connectivity['diagnosis']}",
                (
                    f"受阻阶段：{source_label}"
                    if source_label
                    else "受阻阶段：realtime-fetch-chain"
                ),
                f"运行时诊断摘要：{_build_quote_connectivity_runtime_summary(connectivity)}",
                f"原始错误：{connectivity['error_text']}",
                (
                    f"受阻来源：{source_label}"
                    if source_label
                    else "受阻来源：realtime-fetch-chain"
                ),
                f"下一步：{connectivity['next_step']}",
            ]
        )

    row_count = int(connectivity["row_count"])
    quote_source = str(connectivity["source"])
    fetch_path = str(connectivity.get("fetch_path", "")).strip()
    return "\n".join(
        [
            "实时行情连通性检查",
            "",
            f"依赖状态：{dependency_status}",
            "端点访问：ok",
            "结果：实时行情访问可用。",
            f"获取行数：{row_count}",
            f"行情来源：{build_quote_source_display_text(quote_source)}",
            *([f"直连路径：{fetch_path}"] if fetch_path else []),
            f"真实数据状态：{_build_quote_runtime_status(quote_source)['status_line']}",
            "下一步：运行 python -m app.main self-check，并确认这里的行情来源也出现在自检结果中。",
        ]
    )


def _build_quote_runtime_status(quote_source: str) -> dict[str, str]:
    """Classify the current quote-source path into one short real-data status view."""
    normalized_source = str(quote_source).strip()
    if normalized_source in {EASTMONEY_DIRECT_SOURCE, AKSHARE_SOURCE}:
        return {
            "status_line": "live-pass",
            "next_step": "python -m app.main start-daily-news-workflow",
        }
    if normalized_source == LOCAL_SNAPSHOT_SOURCE:
        return {
            "status_line": "snapshot-pass",
            "next_step": "python -m app.main start-daily-news-workflow",
        }
    return {
        "status_line": "not-passed (still on demo fallback)",
        "next_step": "python -m app.main validate-local-quote",
    }


def _check_realtime_quote_connectivity(*, include_akshare: bool) -> dict[str, object]:
    """Probe the realtime quote chain in the same order used by the main flow."""
    fetch_steps: list[tuple[str, str, object]] = []
    if include_akshare:
        fetch_steps.append((AKSHARE_SOURCE, "AKShare adapter", _default_akshare_fetcher))
    fetch_steps.append((EASTMONEY_DIRECT_SOURCE, "Eastmoney direct fallback", _default_eastmoney_fetcher))

    last_error_text = ""
    last_source_label = ""
    for source_key, source_label, fetcher in fetch_steps:
        try:
            raw_result = fetcher()
        except Exception as exc:  # noqa: BLE001 - this command is explicitly diagnostic
            last_error_text = str(exc).strip() or exc.__class__.__name__
            last_source_label = source_label
            continue

        row_count = len(raw_result.index) if hasattr(raw_result, "index") else len(list(raw_result))
        fetch_path = ""
        if hasattr(raw_result, "attrs"):
            fetch_path = str(raw_result.attrs.get("fetch_path", "")).strip()
        return {
            "status": "ok",
            "source": source_key,
            "row_count": row_count,
            "fetch_path": fetch_path,
        }

    return {
        "status": "blocked",
        "source_label": last_source_label,
        "error_text": last_error_text or "Unknown realtime quote error.",
        **_build_quote_connectivity_failure_view(last_error_text),
    }


def _build_quote_connectivity_failure_view(error_text: str) -> dict[str, str]:
    """Map one raw realtime-quote error into a compact diagnostic view."""
    normalized = str(error_text or "")
    lowered = normalized.lower()
    if "10013" in normalized:
        return {
            "failure_type": "socket-permission-blocked",
            "diagnosis": "Local socket or network permission is blocking the Eastmoney quote endpoint.",
            "next_step": "Review Windows firewall, security software, or local socket permission rules.",
        }
    if "returned non-zero exit status 6" in lowered or "could not resolve host" in lowered:
        return {
            "failure_type": "dns-resolution-failed",
            "diagnosis": "The runtime could not resolve the quote endpoint domain name.",
            "next_step": "Check DNS availability, local resolver settings, or whether the current runtime can resolve the endpoint host.",
        }
    if "returned non-zero exit status 7" in lowered or "failed to connect" in lowered:
        return {
            "failure_type": "tcp-connect-failed",
            "diagnosis": "The runtime could resolve the quote endpoint but could not complete the TCP connection.",
            "next_step": "Check whether the current Python or Codex runtime is blocked from outbound HTTPS even though the browser or shell can connect.",
        }
    if "ssl" in lowered or "tls" in lowered or "certificate" in lowered:
        return {
            "failure_type": "tls-handshake-failed",
            "diagnosis": "The quote endpoint was reached, but the TLS handshake did not complete successfully.",
            "next_step": "Check local certificate handling, HTTPS inspection software, or TLS interception settings.",
        }
    if "HTTPSConnectionPool" in normalized or "Max retries exceeded" in normalized:
        return {
            "failure_type": "https-request-failed",
            "diagnosis": "The machine could not complete the outbound HTTPS quote request.",
            "next_step": "Check outbound HTTPS access, proxy behavior, or process-level network restrictions in the current runtime.",
        }
    if "timed out" in lowered:
        return {
            "failure_type": "request-timeout",
            "diagnosis": "The quote request timed out before the endpoint responded.",
            "next_step": "Retry on a more stable network and check whether the endpoint is being delayed or throttled.",
        }
    if "remotedisconnected" in lowered or "connection aborted" in lowered or "closed connection without response" in lowered:
        return {
            "failure_type": "remote-disconnected",
            "diagnosis": "The endpoint connection opened but was closed before usable market data was returned.",
            "next_step": "Check whether the current process is being filtered by upstream network rules or whether the endpoint is rejecting this runtime path.",
        }
    return {
        "failure_type": "unknown-runtime-network-failure",
        "diagnosis": "The realtime quote request failed before usable market data was returned.",
        "next_step": "Compare browser, shell, and Python runtime behavior to isolate whether the block is network-wide or process-specific.",
    }


def _build_quote_connectivity_runtime_summary(connectivity: dict[str, object]) -> str:
    """Build one concise runtime-facing summary for blocked quote connectivity checks."""
    failure_type = str(connectivity.get("failure_type", "")).strip()
    if failure_type == "tcp-connect-failed":
        return (
            "shell or browser access may still work, but the active Python runtime "
            "cannot complete the outbound quote request yet."
        )
    return (
        "the failure is still inside the realtime quote acquisition layer before "
        "stock-pool filtering or report generation."
    )


def _build_news_classification_text(title: str, content: str) -> str:
    """Build a local news-classification and alert-preview summary."""
    normalized_title = str(title or "").strip()
    normalized_content = str(content or "").strip()
    result = classify_news(normalized_title, normalized_content)
    alert_preview = evaluate_alerts(market_rows=[], news_event=result)
    impact_view = _build_news_impact_view(result)
    suggested_action = _build_news_observation_suggestion(result)

    lines = [
        "新闻分类",
        "",
        f"标题：{normalized_title or '(空)'}",
        f"正文：{normalized_content or '(空)'}",
        f"情绪：{result['sentiment']}",
        f"级别：{result['level']}",
        f"相关板块：{result['related_sector']}",
        f"相关股票：{result['related_stocks'] or '无'}",
        f"链条提示：{_build_news_chain_hint(result)}",
        f"影响判断：{impact_view}",
        f"置信度：{result['confidence']}",
        f"原因：{result['reason']}",
    ]

    if alert_preview:
        first_alert = alert_preview[0]
        lines.extend(
            [
                f"预警预览：{first_alert.get('alert_type', 'unknown')}",
                f"预警级别：{first_alert.get('level', 'unknown')}",
                f"预警关注点：{first_alert.get('focus', '')}",
            ]
        )
    else:
        lines.append("预警预览：无")

    if suggested_action:
        lines.append(f"建议动作：{suggested_action}")
    lines.append(f"结论：{_build_news_bottom_line(impact_view, suggested_action)}")

    lines.extend(
        [
            "",
            'Usage: python -m app.main classify-news "title" "content"',
        ]
    )
    return "\n".join(lines)


def _export_news_batch_summary_text(
    batch_path: str,
    export_path: str,
    *,
    filter_mode: str = "",
) -> str:
    """Export one batch-news summary into a local text or markdown file."""
    normalized_batch_path = str(batch_path or "").strip()
    normalized_export_path = str(export_path or "").strip()
    if not normalized_batch_path:
        return (
            "新闻批量导出\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main export-news-batch "news_batch.json" "news_batch_summary.md"'
        )

    batch_source = Path(normalized_batch_path)
    normalized_filter_mode = str(filter_mode or "").strip()
    filter_error = _build_news_batch_filter_error_text(
        normalized_filter_mode,
        label="新闻批量导出",
    )
    if filter_error:
        return filter_error
    batch_items, batch_error = _load_news_batch_items(batch_source, label="新闻批量导出")
    if batch_error:
        return batch_error
    export_target = (
        Path(normalized_export_path)
        if normalized_export_path
        else _build_default_news_batch_export_path(
            batch_source,
            filter_mode=normalized_filter_mode,
        )
    )
    summary_text = _build_news_batch_classification_text_from_items(
        batch_source,
        batch_items,
        filter_mode=normalized_filter_mode,
    )
    export_target.write_text(summary_text, encoding="utf-8")
    return "\n".join(
        [
            "新闻批量导出",
            "",
            f"新闻源文件：{batch_source}",
            f"保存到：{export_target}",
            f"筛选模式：{normalized_filter_mode or 'full'}",
        ]
    )


def _build_default_news_batch_export_path(
    batch_source: Path,
    *,
    filter_mode: str = "",
) -> Path:
    """Build one timestamped default export path next to the source batch file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    normalized_filter_mode = str(filter_mode or "").strip()
    filter_suffix = f"{normalized_filter_mode}_" if normalized_filter_mode else ""
    return batch_source.with_name(f"news_batch_summary_{filter_suffix}{timestamp}.md")


def _build_default_daily_news_export_path() -> Path:
    """Build one stable default archive path for the daily priority summary."""
    configured_dir = str(os.environ.get("MONITOR_NEWS_DAILY_EXPORT_DIR", "")).strip()
    export_dir = Path(configured_dir) if configured_dir else Path("data/news")
    dated_name = f"news_batch_priority_summary_{datetime.now().strftime('%Y%m%d')}.md"
    return export_dir / dated_name


def _build_default_daily_news_batch_path() -> Path:
    """Build one stable default source path for the daily batch-news template."""
    configured_dir = str(os.environ.get("MONITOR_NEWS_DAILY_EXPORT_DIR", "")).strip()
    batch_dir = Path(configured_dir) if configured_dir else Path("data/news")
    dated_name = f"news_batch_{datetime.now().strftime('%Y%m%d')}.json"
    return batch_dir / dated_name


def _build_default_local_news_feed_path() -> Path:
    """Build the default editable local news feed path."""
    configured_dir = str(os.environ.get("MONITOR_NEWS_DAILY_EXPORT_DIR", "")).strip()
    feed_dir = Path(configured_dir) if configured_dir else Path("data/news")
    return feed_dir / "local_news_feed.json"


def _build_default_local_announcement_feed_path() -> Path:
    """Build the default editable local announcement feed path."""
    configured_dir = str(os.environ.get("MONITOR_NEWS_DAILY_EXPORT_DIR", "")).strip()
    feed_dir = Path(configured_dir) if configured_dir else Path("data/news")
    return feed_dir / "local_announcement_feed.json"


def _build_news_batch_template_text(target_path: str) -> str:
    """Create one local batch-news template file for first-run usage."""
    normalized_target_path = str(target_path or "").strip()
    if not normalized_target_path:
        return (
            "新闻批量模板\n\n"
            '未提供目标文件。\n用法：python -m app.main create-news-batch-template "news_batch.json"'
        )

    resolved_target = Path(normalized_target_path)
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(list(NEWS_BATCH_TEMPLATE_ITEMS), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "新闻批量模板",
        "",
        f"保存到：{resolved_target}",
        f"新闻条数：{len(NEWS_BATCH_TEMPLATE_ITEMS)}",
        "",
        '下一步：python -m app.main validate-news-batch "news_batch.json"',
        "",
        '用法：python -m app.main create-news-batch-template "news_batch.json"',
    ]
    return "\n".join(lines)


def _build_local_news_feed_template_text(target_path: str) -> str:
    """Create an editable local news feed template for MONITOR_NEWS_FEED_PATH."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_news_feed_path()
    )
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(list(LOCAL_NEWS_FEED_TEMPLATE_ITEMS), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "本地新闻源模板",
        "",
        f"保存到：{resolved_target}",
        f"新闻条数：{len(LOCAL_NEWS_FEED_TEMPLATE_ITEMS)}",
        "环境变量：MONITOR_NEWS_FEED_PATH",
        "",
        "下一步：设置 MONITOR_NEWS_FEED_PATH 后运行 python -m app.main refresh-daily-news-batch",
        "",
        '用法：python -m app.main create-local-news-feed-template "data/news/local_news_feed.json"',
    ]
    return "\n".join(lines)


def _build_local_announcement_feed_template_text(target_path: str) -> str:
    """Create an editable local announcement feed template."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_announcement_feed_path()
    )
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(list(LOCAL_ANNOUNCEMENT_FEED_TEMPLATE_ITEMS), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "本地公告源模板",
        "",
        f"保存到：{resolved_target}",
        f"公告条数：{len(LOCAL_ANNOUNCEMENT_FEED_TEMPLATE_ITEMS)}",
        "环境变量：MONITOR_ANNOUNCEMENT_FEED_PATH",
        "",
        "下一步：设置 MONITOR_ANNOUNCEMENT_FEED_PATH 后运行 python -m app.main validate-local-announcement-feed",
        "",
        '用法：python -m app.main create-local-announcement-feed-template "data/news/local_announcement_feed.json"',
    ]
    return "\n".join(lines)


def _build_news_source_status_text(target_path: str) -> str:
    """Build a user-facing status report for the current news source layer."""
    normalized_target_path = str(target_path or "").strip()
    feed_path = (
        Path(normalized_target_path)
        if normalized_target_path
        else _get_daily_news_feed_path()
    )
    status = build_news_source_status(feed_path)
    lines = [
        "新闻源状态",
        "",
        f"状态：{status['status']}",
        f"本地新闻源：{status['feed_path'] or '未配置'}",
        f"新闻条数：{status['item_count']}",
        f"来源分布：{status['source_summary'] or '无'}",
    ]
    if status.get("first_title"):
        lines.append(f"第一条标题：{status['first_title']}")
    lines.extend(
        [
            f"说明：{status['reason']}",
            f"下一步：{status['next_step']}",
            "",
            '用法：python -m app.main news-source-status "data/news/local_news_feed.json"',
        ]
    )
    return "\n".join(lines)


def _build_announcement_source_status_text(target_path: str) -> str:
    """Build a user-facing status report for the optional announcement source."""
    normalized_target_path = str(target_path or "").strip()
    feed_path = (
        Path(normalized_target_path)
        if normalized_target_path
        else _get_announcement_feed_path()
    )
    status = build_announcement_source_status(feed_path)
    lines = [
        "公告源状态",
        "",
        f"状态：{status['status']}",
        f"公告源文件：{status['feed_path'] or '未配置'}",
        f"公告条数：{status['item_count']}",
    ]
    if status.get("first_title"):
        lines.append(f"第一条标题：{status['first_title']}")
    lines.extend(
        [
            f"说明：{status['reason']}",
            f"下一步：{status['next_step']}",
            "",
            '用法：python -m app.main announcement-source-status "data/news/local_announcement_feed.json"',
        ]
    )
    return "\n".join(lines)


def _build_local_announcement_feed_validation_text(target_path: str) -> str:
    """Validate one editable local announcement feed file before daily merge."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_announcement_feed_path()
    )
    status = build_announcement_source_status(resolved_target)
    lines = [
        "本地公告源校验",
        "",
        f"来源文件：{resolved_target}",
        f"状态：{_translate_local_source_status(status['status'])}",
        f"有效公告条数：{status['item_count']}",
    ]
    if status.get("first_title"):
        lines.append(f"第一条标题：{status['first_title']}")
    lines.extend(
        [
            f"说明：{status['reason']}",
            f"下一步：{status['next_step']}",
            "",
            '用法：python -m app.main validate-local-announcement-feed "data/news/local_announcement_feed.json"',
        ]
    )
    return "\n".join(lines)


def _build_refresh_local_announcement_feed_text(target_path: str, feed_url: str) -> str:
    """Refresh the local announcement feed from a configured remote JSON URL."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_announcement_feed_path()
    )
    resolved_url = str(feed_url or "").strip() or _get_announcement_feed_url()
    items, status = fetch_remote_announcement_items(resolved_url)
    lines = [
        "刷新本地公告源",
        "",
        f"远程源：{resolved_url or '未配置'}",
        f"目标文件：{resolved_target}",
        f"状态：{_translate_remote_announcement_status(status['status'])}",
        f"说明：{status['reason']}",
    ]
    if status["status"] != "ok":
        lines.extend(
            [
                f"下一步：{status['next_step']}",
                "",
                '用法：python -m app.main refresh-local-announcement-feed "data/news/local_announcement_feed.json"',
            ]
        )
        return "\n".join(lines)

    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines.extend(
        [
            f"写入公告条数：{len(items)}",
            f"第一条标题：{items[0]['title']}",
            "",
            "下一步：设置 MONITOR_ANNOUNCEMENT_FEED_PATH 后运行 python -m app.main start-daily-news-workflow",
            "",
            '用法：python -m app.main refresh-local-announcement-feed "data/news/local_announcement_feed.json"',
        ]
    )
    return "\n".join(lines)


def _translate_remote_announcement_status(status: str) -> str:
    """Translate remote announcement fetch status for command output."""
    if status == "ok":
        return "成功"
    if status == "not-configured":
        return "未配置"
    if status == "fetch-failed":
        return "抓取失败"
    if status == "invalid":
        return "无效"
    if status == "empty":
        return "空结果"
    return status


def _translate_local_source_status(status: str) -> str:
    """Translate local feed status labels for user-facing validation output."""
    if status == "ready":
        return "有效"
    if status == "missing":
        return "缺失"
    if status == "invalid":
        return "无效"
    if status == "not-configured":
        return "未配置"
    return status


def _get_announcement_feed_path() -> Path | None:
    """Resolve the optional local announcement feed path."""
    configured_path = str(os.environ.get("MONITOR_ANNOUNCEMENT_FEED_PATH", "")).strip()
    return Path(configured_path) if configured_path else None


def _get_announcement_feed_url() -> str:
    """Resolve the optional remote announcement feed URL."""
    return str(os.environ.get("MONITOR_ANNOUNCEMENT_FEED_URL", "")).strip()


def _build_notification_status_text() -> str:
    """Build a user-facing push notification status summary."""
    status = build_notification_channel_status()
    return "\n".join(
        [
            "推送通知状态",
            "",
            f"状态：{status['status']}",
            f"通道：{status['channel']}",
            f"说明：{status['reason']}",
            f"下一步：{status['next_step']}",
        ]
    )


def _build_local_news_feed_validation_text(target_path: str) -> str:
    """Validate one editable local news feed file before daily refresh."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_news_feed_path()
    )
    if not resolved_target.exists():
        return "\n".join(
            [
                "本地新闻源校验",
                "",
                f"来源文件：{resolved_target}",
                "状态：缺失",
                "",
                f'下一步：python -m app.main create-local-news-feed-template "{resolved_target}"',
                "",
                '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
            ]
        )

    try:
        raw_items = json.loads(resolved_target.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return "\n".join(
            [
                "本地新闻源校验",
                "",
                f"来源文件：{resolved_target}",
                "状态：无效",
                f"JSON 错误：{exc.msg}",
                "",
                '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
            ]
        )

    if not isinstance(raw_items, list):
        return "\n".join(
            [
                "本地新闻源校验",
                "",
                f"来源文件：{resolved_target}",
                "状态：无效",
                "结构错误：顶层 JSON 必须是列表。",
                "",
                '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
            ]
        )

    valid_items: list[dict[str, str]] = []
    issues: list[str] = []
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            issues.append(f"第 {index} 条：必须是包含 title/content 字段的对象。")
            continue
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title:
            issues.append(f"第 {index} 条：缺少 title。")
        if not content:
            issues.append(f"第 {index} 条：缺少 content。")
        if title and content:
            valid_items.append(
                {
                    "title": title,
                    "content": content,
                    "source": str(item.get("source", "local-feed")).strip() or "local-feed",
                }
            )

    if issues:
        return "\n".join(
            [
                "本地新闻源校验",
                "",
                f"来源文件：{resolved_target}",
                "状态：无效",
                *issues,
                "",
                '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
            ]
        )

    lines = [
        "本地新闻源校验",
        "",
        f"来源文件：{resolved_target}",
        "状态：有效",
        f"有效新闻条数：{len(valid_items)}",
        f"来源分布：{_build_local_news_feed_source_summary(valid_items)}",
        f"重复标题：{_build_local_news_feed_duplicate_title_summary(valid_items)}",
    ]
    if valid_items:
        lines.append(f"第一条标题：{valid_items[0]['title']}")
    lines.extend(
        [
            "",
            "下一步：设置 MONITOR_NEWS_FEED_PATH 后运行 python -m app.main refresh-daily-news-batch",
            "",
            '用法：python -m app.main validate-local-news-feed "data/news/local_news_feed.json"',
        ]
    )
    return "\n".join(lines)


def _build_local_news_feed_source_summary(items: list[dict[str, str]]) -> str:
    """Build a compact source distribution summary for local news feed validation."""
    counts: dict[str, int] = {}
    for item in items:
        source = str(item.get("source", "")).strip() or "local-feed"
        counts[source] = counts.get(source, 0) + 1
    if not counts:
        return "无"
    return " | ".join(f"{source} {count}" for source, count in counts.items())


def _build_local_news_feed_duplicate_title_summary(items: list[dict[str, str]]) -> str:
    """Build a compact duplicate-title summary for local news feed validation."""
    counts: dict[str, int] = {}
    for item in items:
        title = str(item.get("title", "")).strip()
        if title:
            counts[title] = counts.get(title, 0) + 1
    duplicates = [
        f"{title} ({count})"
        for title, count in counts.items()
        if count > 1
    ]
    return " | ".join(duplicates) if duplicates else "无"


def _build_append_local_news_feed_text(title: str, content: str, target_path: str) -> str:
    """Append one manual news item into the editable local news feed."""
    normalized_title = str(title or "").strip()
    normalized_content = str(content or "").strip()
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_news_feed_path()
    )
    if not normalized_title or not normalized_content:
        return "\n".join(
            [
                "追加本地新闻源",
                "",
                "状态：缺少标题或正文",
                "",
                '用法：python -m app.main append-local-news-feed "title" "content" "data/news/local_news_feed.json"',
            ]
        )

    existing_items: list[dict[str, str]] = []
    if resolved_target.exists():
        try:
            raw_items = json.loads(resolved_target.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            return "\n".join(
                [
                    "追加本地新闻源",
                    "",
                    f"来源文件：{resolved_target}",
                    "状态：无效",
                    f"JSON 错误：{exc.msg}",
                    "",
                    f'下一步：python -m app.main validate-local-news-feed "{resolved_target}"',
                ]
            )
        if not isinstance(raw_items, list):
            return "\n".join(
                [
                    "追加本地新闻源",
                    "",
                    f"来源文件：{resolved_target}",
                    "状态：无效",
                    "结构错误：顶层 JSON 必须是列表。",
                    "",
                    f'下一步：python -m app.main validate-local-news-feed "{resolved_target}"',
                ]
            )
        existing_items = [
            dict(item)
            for item in raw_items
            if isinstance(item, dict)
        ]

    if any(str(item.get("title", "")).strip() == normalized_title for item in existing_items):
        return "\n".join(
            [
                "追加本地新闻源",
                "",
                f"保存到：{resolved_target}",
                "状态：已存在，未重复追加",
                f"新闻条数：{len(existing_items)}",
                "",
                f'下一步：python -m app.main local-news-feed-daily-pass-check "{resolved_target}"',
            ]
        )

    existing_items.append(
        {
            "title": normalized_title,
            "content": normalized_content,
            "source": "local-feed-manual",
        }
    )
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(existing_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return "\n".join(
        [
            "追加本地新闻源",
            "",
            f"保存到：{resolved_target}",
            "状态：已追加",
            f"新闻条数：{len(existing_items)}",
            "",
            f'下一步：python -m app.main local-news-feed-daily-pass-check "{resolved_target}"',
        ]
    )


def _build_refresh_local_news_feed_text(target_path: str, feed_url: str) -> str:
    """Refresh the local news feed from a configured remote JSON URL."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_local_news_feed_path()
    )
    resolved_url = str(feed_url or "").strip() or _get_news_feed_url()
    items, status = fetch_remote_news_items(resolved_url)
    lines = [
        "刷新本地新闻源",
        "",
        f"远程源：{resolved_url or '未配置'}",
        f"目标文件：{resolved_target}",
        f"状态：{_translate_remote_news_status(status['status'])}",
        f"说明：{status['reason']}",
    ]
    if status["status"] != "ok":
        lines.extend(
            [
                f"下一步：{status['next_step']}",
                "",
                '用法：python -m app.main refresh-local-news-feed "data/news/local_news_feed.json"',
            ]
        )
        return "\n".join(lines)

    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines.extend(
        [
            f"写入新闻条数：{len(items)}",
            f"第一条标题：{items[0]['title']}",
            "",
            "下一步：设置 MONITOR_NEWS_FEED_PATH 后运行 python -m app.main refresh-daily-news-batch",
            "",
            '用法：python -m app.main refresh-local-news-feed "data/news/local_news_feed.json"',
        ]
    )
    return "\n".join(lines)


def _translate_remote_news_status(status: str) -> str:
    """Translate remote news fetch status for command output."""
    if status == "ok":
        return "成功"
    if status == "not-configured":
        return "未配置"
    if status == "fetch-failed":
        return "抓取失败"
    if status == "invalid":
        return "无效"
    if status == "empty":
        return "空结果"
    return status


def _build_daily_news_batch_template_text(target_path: str) -> str:
    """Create one daily batch-news template in the fixed project-local work area."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_daily_news_batch_path()
    )
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(list(NEWS_BATCH_TEMPLATE_ITEMS), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "每日新闻批量模板",
        "",
        f"保存到：{resolved_target}",
        f"新闻条数：{len(NEWS_BATCH_TEMPLATE_ITEMS)}",
        "默认源文件规则：data/news/news_batch_YYYYMMDD.json",
        "",
        f'下一步：python -m app.main batch-news-daily-export "{resolved_target}"',
        "",
        "用法：python -m app.main create-daily-news-batch",
    ]
    return "\n".join(lines)


def _build_refresh_daily_news_batch_text(target_path: str) -> str:
    """Refresh the daily batch-news source from the current local-auto source layer."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else _build_default_daily_news_batch_path()
    )
    feed_path = _get_daily_news_feed_path()
    announcement_path = _get_announcement_feed_path()
    items = _build_daily_news_items(feed_path, announcement_path)
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    resolved_target.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "刷新每日新闻批量源",
        "",
        f"保存到：{resolved_target}",
        f"来源模式：{_build_daily_news_source_mode(feed_path, announcement_path)}",
        f"新闻条数：{len(items)}",
        "",
        f'下一步：python -m app.main batch-news-daily-export "{resolved_target}"',
        "",
        '用法：python -m app.main refresh-daily-news-batch',
    ]
    return "\n".join(lines)


def _refresh_daily_news_batch_file(
    target_path: Path,
    *,
    feed_path: Path | None,
    announcement_path: Path | None = None,
) -> list[dict[str, str]]:
    """Write one daily news batch from the provided feed plus fallback candidates."""
    resolved_announcement_path = (
        announcement_path
        if announcement_path is not None
        else _get_announcement_feed_path()
    )
    items = _build_daily_news_items(feed_path, resolved_announcement_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return items


def _build_refresh_external_feeds_pass_check_text(batch_path: str, export_path: str) -> str:
    """Refresh configured remote feeds, then run the daily news export path."""
    resolved_news_feed_path = _build_default_local_news_feed_path()
    resolved_announcement_feed_path = _build_default_local_announcement_feed_path()
    resolved_batch_path = (
        Path(str(batch_path or "").strip())
        if str(batch_path or "").strip()
        else _build_default_daily_news_batch_path()
    )
    resolved_export_path = (
        Path(str(export_path or "").strip())
        if str(export_path or "").strip()
        else _build_default_daily_news_export_path()
    )

    news_refresh_text = _build_refresh_local_news_feed_text(str(resolved_news_feed_path), "")
    announcement_refresh_text = _build_refresh_local_announcement_feed_text(
        str(resolved_announcement_feed_path),
        "",
    )
    effective_news_feed_path = (
        resolved_news_feed_path
        if resolved_news_feed_path.exists()
        else _get_daily_news_feed_path()
    )
    effective_announcement_feed_path = (
        resolved_announcement_feed_path
        if resolved_announcement_feed_path.exists()
        else _get_announcement_feed_path()
    )
    items = _refresh_daily_news_batch_file(
        resolved_batch_path,
        feed_path=effective_news_feed_path,
        announcement_path=effective_announcement_feed_path,
    )
    export_text = _build_batch_news_daily_export_text(
        str(resolved_batch_path),
        str(resolved_export_path),
    )
    export_passed = "已保存优先级摘要到：" in export_text
    lines = [
        "外部输入源每日一体化检查",
        "",
        "步骤 1：刷新远程新闻源到本地",
        news_refresh_text,
        "",
        "步骤 2：刷新远程公告源到本地",
        announcement_refresh_text,
        "",
        "步骤 3：生成每日新闻批量源",
        f"新闻批量文件：{resolved_batch_path}",
        f"来源模式：{_build_daily_news_source_mode(effective_news_feed_path, effective_announcement_feed_path)}",
        f"新闻条数：{len(items)}",
        "",
        "步骤 4：导出每日优先摘要",
        export_text,
        "",
        (
            "结果：外部输入源每日流程已通过。"
            if export_passed
            else "结果：外部输入源每日流程仍需检查。"
        ),
        f"摘要文件：{resolved_export_path}",
        "下一步：python -m app.main latest-review",
        "",
        "用法：python -m app.main refresh-external-feeds-pass-check",
    ]
    return "\n".join(lines)


def _build_external_feeds_status_text() -> str:
    """Build a read-only status view for remote/local external feed readiness."""
    news_url = _get_news_feed_url()
    announcement_url = _get_announcement_feed_url()
    default_news_feed_path = _build_default_local_news_feed_path()
    default_announcement_feed_path = _build_default_local_announcement_feed_path()
    configured_news_feed_path = _get_daily_news_feed_path()
    configured_announcement_feed_path = _get_announcement_feed_path()
    effective_news_feed_path = configured_news_feed_path or default_news_feed_path
    effective_announcement_feed_path = (
        configured_announcement_feed_path or default_announcement_feed_path
    )
    news_status = build_news_source_status(effective_news_feed_path)
    announcement_status = build_announcement_source_status(effective_announcement_feed_path)
    remote_configured = bool(news_url or announcement_url)
    local_feed_ready = news_status["status"] == "local-feed-ready"
    announcement_ready = announcement_status["status"] == "ready"
    can_run_daily = (
        remote_configured
        or local_feed_ready
        or announcement_ready
        or news_status["status"] in {"auto-candidate-only", "local-feed-missing"}
    )
    if remote_configured:
        next_step = "python -m app.main refresh-external-feeds-pass-check"
    elif local_feed_ready or announcement_ready:
        next_step = "python -m app.main start-daily-news-workflow"
    else:
        next_step = "python -m app.main refresh-external-feeds-pass-check"
    return "\n".join(
        [
            "外部输入源状态",
            "",
            f"远程新闻 URL：{'已配置' if news_url else '未配置'}",
            f"远程公告 URL：{'已配置' if announcement_url else '未配置'}",
            f"本地新闻源：{effective_news_feed_path}",
            f"本地新闻源状态：{news_status['status']}",
            f"本地公告源：{effective_announcement_feed_path}",
            f"本地公告源状态：{announcement_status['status']}",
            f"每日流程：{'可运行' if can_run_daily else '需要检查'}",
            (
                "配置结论：外部输入源已具备自动刷新入口。"
                if remote_configured
                else "配置结论：远程源未配置，但每日流程可用本地源或自动候选兜底。"
            ),
            f"下一步：{next_step}",
            "",
            "用法：python -m app.main external-feeds-status",
        ]
    )


def _build_local_news_feed_daily_pass_check_text(
    feed_path: str,
    batch_path: str,
    export_path: str,
) -> str:
    """Run validate -> refresh batch -> export summary for an editable local news feed."""
    resolved_feed_path = Path(str(feed_path or "").strip()) if str(feed_path or "").strip() else _build_default_local_news_feed_path()
    resolved_batch_path = (
        Path(str(batch_path or "").strip())
        if str(batch_path or "").strip()
        else _build_default_daily_news_batch_path()
    )
    resolved_export_path = (
        Path(str(export_path or "").strip())
        if str(export_path or "").strip()
        else _build_default_daily_news_export_path()
    )
    validation_text = _build_local_news_feed_validation_text(str(resolved_feed_path))
    if "状态：有效" not in validation_text:
        return "\n".join(
            [
                "本地新闻源每日一体化检查",
                "",
                "步骤 1：校验本地新闻源",
                validation_text,
                "",
                "结果：本地新闻源校验未通过。",
                f'下一步：python -m app.main validate-local-news-feed "{resolved_feed_path}"',
                "",
                '用法：python -m app.main local-news-feed-daily-pass-check "data/news/local_news_feed.json"',
            ]
        )

    items = _refresh_daily_news_batch_file(resolved_batch_path, feed_path=resolved_feed_path)
    refresh_lines = [
        "刷新每日新闻批量源",
        "",
        f"保存到：{resolved_batch_path}",
        f"来源模式：{_build_daily_news_source_mode(resolved_feed_path, _get_announcement_feed_path())}",
        f"新闻条数：{len(items)}",
    ]
    export_text = _build_batch_news_daily_export_text(
        str(resolved_batch_path),
        str(resolved_export_path),
    )
    export_passed = "已保存优先级摘要到：" in export_text
    return "\n".join(
        [
            "本地新闻源每日一体化检查",
            "",
            "步骤 1：校验本地新闻源",
            validation_text,
            "",
            "步骤 2：刷新每日新闻批量源",
            "\n".join(refresh_lines),
            "",
            "步骤 3：导出每日优先摘要",
            export_text,
            "",
            (
                "结果：本地新闻源每日流程已通过。"
                if export_passed
                else "结果：每日优先摘要导出未通过。"
            ),
            f"新闻批量文件：{resolved_batch_path}",
            f"摘要文件：{resolved_export_path}",
            "下一步：python -m app.main latest-review",
            "",
            '用法：python -m app.main local-news-feed-daily-pass-check "data/news/local_news_feed.json"',
        ]
    )


def _get_daily_news_feed_path() -> Path | None:
    """Resolve the optional local news feed path for daily candidate refreshes."""
    configured_path = str(os.environ.get("MONITOR_NEWS_FEED_PATH", "")).strip()
    return Path(configured_path) if configured_path else None


def _get_news_feed_url() -> str:
    """Resolve the optional remote news feed URL."""
    return str(os.environ.get("MONITOR_NEWS_FEED_URL", "")).strip()


def _build_daily_news_source_mode(
    feed_path: Path | None,
    announcement_path: Path | None = None,
) -> str:
    """Build a concise display label for the current daily news source mode."""
    if feed_path and feed_path.exists() and not (announcement_path and announcement_path.exists()):
        return f"本地新闻源 + 自动候选（{feed_path}）"

    parts: list[str] = []
    if feed_path and feed_path.exists():
        parts.append(f"本地新闻源（{feed_path}）")
    if announcement_path and announcement_path.exists():
        parts.append(f"本地公告源（{announcement_path}）")
    parts.append("自动候选")
    return " + ".join(parts)


def _build_daily_news_items(
    feed_path: Path | None,
    announcement_path: Path | None,
) -> list[dict[str, str]]:
    """Build the daily news list from local feeds plus automatic candidates."""
    items = fetch_daily_news_candidates(feed_path=feed_path)
    announcement_items = load_announcement_feed_items(announcement_path)
    return _dedupe_daily_news_items([*announcement_items, *items])


def _dedupe_daily_news_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the first item for each title so announcement-confirmed items win."""
    seen_titles: set[str] = set()
    deduped_items: list[dict[str, str]] = []
    for item in items:
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title or not content or title in seen_titles:
            continue
        seen_titles.add(title)
        deduped_items.append(
            {
                "title": title,
                "content": content,
                "source": str(item.get("source", "")).strip() or "daily-news",
            }
        )
    return deduped_items


def _load_authoritative_local_quote_template_payload() -> dict[str, object]:
    """Load the single authoritative local quote template payload from the repo example."""
    payload = json.loads(LOCAL_QUOTE_TEMPLATE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("Local quote template example must be a JSON object with a rows list.")
    return payload


def _build_default_local_quote_template_payload() -> dict[str, object]:
    """Return the single authoritative local quote template payload."""
    return _load_authoritative_local_quote_template_payload()


def _build_local_quote_template_text(target_path: str) -> str:
    """Create one local realtime-quote snapshot template file."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )
    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    template_payload = _build_default_local_quote_template_payload()
    resolved_target.write_text(
        json.dumps(template_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "本地行情快照模板",
        "",
        f"保存到：{resolved_target}",
        "结构：rows-array",
        "来源角色：local-json-snapshot",
        "",
        f'下一步：python -m app.main validate-local-quote "{resolved_target}"',
        "",
        '用法：python -m app.main create-local-quote-template "data/runtime/latest_quotes.json"',
    ]
    return "\n".join(lines)


def _build_local_quote_validation_text(target_path: str) -> str:
    """Validate one local realtime-quote snapshot file."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )
    if not resolved_target.exists():
        return "\n".join(
            [
                "本地行情快照校验",
                "",
                f"来源文件：{resolved_target}",
                "状态：缺失",
                "",
                f'下一步：python -m app.main create-local-quote-template "{resolved_target}"',
                "",
                '用法：python -m app.main validate-local-quote "data/runtime/latest_quotes.json"',
            ]
        )

    payload = json.loads(resolved_target.read_text(encoding="utf-8"))
    shape_label = detect_local_quote_snapshot_shape(payload)
    try:
        quotes = load_local_quote_snapshot(resolved_target)
    except Exception as exc:  # noqa: BLE001 - user-facing validation path
        return "\n".join(
            [
                "本地行情快照校验",
                "",
                f"来源文件：{resolved_target}",
                f"结构：{shape_label}",
                "状态：无效",
                f"错误：{exc}",
                "",
                '用法：python -m app.main validate-local-quote "data/runtime/latest_quotes.json"',
            ]
        )

    lines = [
        "本地行情快照校验",
        "",
        f"来源文件：{resolved_target}",
        f"结构：{shape_label}",
        "状态：有效",
        f"行数：{len(quotes.index)}",
    ]
    if not quotes.empty:
        lines.append(f"第一只代码：{quotes.iloc[0]['code']}")
    lines.extend(
        [
            "",
            "下一步：python -m app.main self-check",
            "",
            '用法：python -m app.main validate-local-quote "data/runtime/latest_quotes.json"',
        ]
    )
    return "\n".join(lines)


def _build_refresh_local_quote_snapshot_text(target_path: str) -> str:
    """Fetch one fresh live quote snapshot and save it into the runtime path."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )
    live_quotes = fetch_realtime_quotes(
        raw_fetcher=_default_akshare_fetcher,
        backup_fetcher=_default_eastmoney_fetcher,
    )
    if live_quotes.empty:
        return "\n".join(
            [
                "刷新本地行情快照",
                "",
                f"目标文件：{resolved_target}",
                "状态：受阻",
                "结果：实时行情刷新未通过。",
                "失败原因：实时抓取链路没有返回可用行情行。",
                "下一步：python -m app.main quote-connectivity-check",
                "",
                '用法：python -m app.main refresh-local-quote-snapshot "data/runtime/latest_quotes.json"',
            ]
        )

    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rows": live_quotes.to_dict(orient="records")}
    resolved_target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    quote_source = get_quote_source(live_quotes)
    fetch_path = get_fetch_path(live_quotes)
    runtime_status = _build_quote_runtime_status(quote_source)
    lines = [
        "刷新本地行情快照",
        "",
        f"保存到：{resolved_target}",
        "保存结构：rows-array",
        f"行数：{len(live_quotes.index)}",
        f"行情来源：{build_quote_source_display_text(quote_source)}",
    ]
    if fetch_path:
        lines.append(f"直连路径：{fetch_path}")
    lines.extend(
        [
            f"真实数据状态：{runtime_status['status_line']}",
            "",
            f'下一步：python -m app.main validate-local-quote "{resolved_target}"',
            "",
            '用法：python -m app.main refresh-local-quote-snapshot "data/runtime/latest_quotes.json"',
        ]
    )
    return "\n".join(lines)


def _build_refresh_local_quote_pass_check_text(
    config: AppConfig,
    target_path: str,
) -> str:
    """Run one compact refresh -> validate -> self-check chain for local real quote snapshots."""
    normalized_target_path = str(target_path or "").strip()
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )

    refresh_text = _build_refresh_local_quote_snapshot_text(normalized_target_path)
    if "保存到：" not in refresh_text:
        return "\n".join(
            [
                "刷新本地行情一体化检查",
                "",
                "步骤 1：刷新",
                refresh_text,
                "",
                "结果：实时刷新未通过。",
                "失败原因：实时行情刷新没有返回可用行",
                "下一步：python -m app.main quote-connectivity-check",
                "",
                '用法：python -m app.main refresh-local-quote-pass-check "data/runtime/latest_quotes.json"',
            ]
        )

    validation_text = _build_local_quote_validation_text(str(resolved_target))
    if "状态：有效" not in validation_text:
        return "\n".join(
            [
                "刷新本地行情一体化检查",
                "",
                "步骤 1：刷新",
                refresh_text,
                "",
                "步骤 2：校验",
                validation_text,
                "",
                "结果：本地快照校验未通过。",
                f"失败原因：{_build_local_quote_pass_check_failure_reason(validation_text)}",
                f'下一步：python -m app.main validate-local-quote "{resolved_target}"',
                "",
                '用法：python -m app.main refresh-local-quote-pass-check "data/runtime/latest_quotes.json"',
            ]
        )

    self_check_text = _build_self_check_text(config)
    real_data_passed = (
        "真实数据状态：live-pass" in self_check_text
        or "真实数据状态：snapshot-pass" in self_check_text
    )
    return "\n".join(
        [
            "刷新本地行情一体化检查",
            "",
            "步骤 1：刷新",
            refresh_text,
            "",
            "步骤 2：校验",
            validation_text,
            "",
            "步骤 3：自检",
            self_check_text,
            "",
            (
                "结果：本地真实行情刷新路径已通过。"
                if real_data_passed
                else "结果：刷新和校验已通过，但自检仍未通过。"
            ),
            (
                "失败原因：导入成功，但自检仍回落到演示数据"
                if not real_data_passed
                else "失败原因：无"
            ),
            (
                "下一步：python -m app.main start-daily-news-workflow"
                if real_data_passed
                else f'下一步：python -m app.main validate-local-quote "{resolved_target}"'
            ),
            "",
            '用法：python -m app.main refresh-local-quote-pass-check "data/runtime/latest_quotes.json"',
        ]
    )


def _build_import_local_quote_text(source_path: str, target_path: str) -> str:
    """Import one external local quote JSON file into the project's runtime snapshot path."""
    normalized_source_path = str(source_path or "").strip()
    normalized_target_path = str(target_path or "").strip()
    if not normalized_source_path:
        return "\n".join(
            [
                "导入本地行情快照",
                "",
                '未提供源文件。\n用法：python -m app.main import-local-quote "external_quotes.json"',
            ]
        )

    resolved_source = Path(normalized_source_path)
    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )
    try:
        quotes = load_local_quote_snapshot(resolved_source)
    except Exception as exc:  # noqa: BLE001 - user-facing import path
        return "\n".join(
            [
                "导入本地行情快照",
                "",
                f"源文件：{resolved_source}",
                "状态：源文件无效",
                f"错误：{exc}",
                "",
                '用法：python -m app.main import-local-quote "external_quotes.json"',
            ]
        )

    resolved_target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rows": quotes.to_dict(orient="records")}
    resolved_target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "导入本地行情快照",
        "",
        f"源文件：{resolved_source}",
        f"保存到：{resolved_target}",
        "保存结构：rows-array",
        f"行数：{len(quotes.index)}",
    ]
    if not quotes.empty:
        lines.append(f"第一只代码：{quotes.iloc[0]['code']}")
    lines.extend(
        [
            "",
            f'下一步：python -m app.main validate-local-quote "{resolved_target}"',
            "",
            '用法：python -m app.main import-local-quote "external_quotes.json"',
        ]
    )
    return "\n".join(lines)


def _build_import_local_quote_pass_check_text(
    config: AppConfig,
    source_path: str,
    target_path: str,
) -> str:
    """Run one compact import -> validate -> self-check chain for local real quote snapshots."""
    normalized_source_path = str(source_path or "").strip()
    normalized_target_path = str(target_path or "").strip()
    if not normalized_source_path:
        return "\n".join(
            [
                "导入本地行情一体化检查",
                "",
                '未提供源文件。\n用法：python -m app.main import-local-quote-pass-check "external_quotes.json"',
                "",
                "结果：源文件导入未通过。",
                "失败原因：缺少源文件",
            ]
        )

    import_text = _build_import_local_quote_text(
        normalized_source_path,
        normalized_target_path,
    )
    if "保存到：" not in import_text:
        return "\n".join(
            [
                "导入本地行情一体化检查",
                "",
                import_text,
                "",
                "结果：源文件导入未通过。",
                f"失败原因：{_build_local_quote_pass_check_failure_reason(import_text)}",
                '下一步：python -m app.main import-local-quote "external_quotes.json"',
                "",
                '用法：python -m app.main import-local-quote-pass-check "external_quotes.json"',
            ]
        )

    resolved_target = (
        Path(normalized_target_path)
        if normalized_target_path
        else get_local_quote_snapshot_path()
    )
    validation_text = _build_local_quote_validation_text(str(resolved_target))
    if "状态：有效" not in validation_text:
        return "\n".join(
            [
                "导入本地行情一体化检查",
                "",
                "步骤 1：导入",
                import_text,
                "",
                "步骤 2：校验",
                validation_text,
                "",
                "结果：本地快照校验未通过。",
                f"失败原因：{_build_local_quote_pass_check_failure_reason(validation_text)}",
                f'下一步：python -m app.main validate-local-quote "{resolved_target}"',
                "",
                '用法：python -m app.main import-local-quote-pass-check "external_quotes.json"',
            ]
        )

    self_check_text = _build_self_check_text(config)
    real_data_passed = (
        "真实数据状态：live-pass" in self_check_text
        or "真实数据状态：snapshot-pass" in self_check_text
    )

    lines = [
        "导入本地行情一体化检查",
        "",
        "步骤 1：导入",
        import_text,
        "",
        "步骤 2：校验",
        validation_text,
        "",
        "步骤 3：自检",
        self_check_text,
        "",
        (
            "结果：本地真实数据路径已就绪。"
            if real_data_passed
            else "结果：本地真实数据路径仍需检查。"
        ),
        (
            ""
            if real_data_passed
            else f"失败原因：{_build_local_quote_pass_check_failure_reason(self_check_text)}"
        ),
        (
            ""
            if real_data_passed
            else f"运行时诊断：{_build_local_quote_runtime_diagnosis(resolved_target)}"
        ),
        (
            "下一步：python -m app.main start-daily-news-workflow"
            if real_data_passed
            else f'下一步：python -m app.main validate-local-quote "{resolved_target}"'
        ),
        "",
        '用法：python -m app.main import-local-quote-pass-check "external_quotes.json"',
    ]
    return "\n".join(lines)


def _build_local_quote_pass_check_failure_reason(text: str) -> str:
    """Map one pass-check stage output into a clearer user-facing failure reason."""
    normalized_text = str(text)
    if "未提供源文件。" in normalized_text or "No source file was provided." in normalized_text:
        return "缺少源文件"
    if "状态：源文件无效" in normalized_text or "Status: invalid-source" in normalized_text:
        return "源 JSON 格式不符合支持的本地行情结构"
    if "状态：缺失" in normalized_text or "Status: missing" in normalized_text:
        return "运行时本地快照文件缺失"
    if "状态：无效" in normalized_text or "Status: invalid" in normalized_text:
        return "运行时本地快照内容无效或字段不完整"
    if (
        "真实数据状态：not-passed (still on demo fallback)" in normalized_text
        or "Real-data status: not-passed (still on demo fallback)" in normalized_text
    ):
        return "导入成功，但自检仍回落到演示数据"
    return "一体化检查未达到真实数据就绪状态"


def _build_local_quote_runtime_diagnosis(target_path: Path) -> str:
    """Explain why a valid imported snapshot still did not activate the real-data path."""
    resolved_target = Path(target_path)
    if not resolved_target.exists():
        return "runtime local snapshot file is missing."

    try:
        quotes = load_local_quote_snapshot(resolved_target)
    except Exception as exc:  # noqa: BLE001 - user-facing diagnosis path
        return f"runtime local snapshot could not be loaded: {exc}"

    if quotes.empty:
        return "runtime snapshot loaded, but it currently contains 0 rows."

    filtered_quotes = filter_to_universe(quotes, get_all_stocks())
    if filtered_quotes.empty:
        return "runtime snapshot loaded, but 0 rows matched the current monitored stock pool."

    return (
        "runtime snapshot is valid and matches the monitored stock pool, "
        "but the active quote fetch path still returned no rows."
    )


def _build_start_daily_news_workflow_text(batch_path: str, export_path: str) -> str:
    """Create or reuse today's batch source file, then run the daily export flow."""
    normalized_batch_path = str(batch_path or "").strip()
    normalized_export_path = str(export_path or "").strip()
    resolved_batch_path = (
        Path(normalized_batch_path)
        if normalized_batch_path
        else _build_default_daily_news_batch_path()
    )

    if resolved_batch_path.exists():
        source_status = "reused-existing"
    else:
        resolved_batch_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_batch_path.write_text(
            json.dumps(
                _build_daily_news_items(
                    _get_daily_news_feed_path(),
                    _get_announcement_feed_path(),
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        source_status = "auto-generated"

    daily_export_text = _build_batch_news_daily_export_text(
        str(resolved_batch_path),
        normalized_export_path,
    )
    resolved_export_path = (
        Path(normalized_export_path)
        if normalized_export_path
        else _build_default_daily_news_export_path()
    )
    lines = [
        "启动每日新闻工作流",
        "",
        "今日第一遍阅读",
        "",
        f"新闻源文件：{resolved_batch_path}",
        f"源文件状态：{_translate_daily_news_source_status(source_status)}",
        f"今日摘要文件：{resolved_export_path}",
        "",
        "建议阅读顺序：",
        "1. 先打开已保存的每日优先级摘要。",
        "2. 只有需要完整细节时，再阅读下面的优先级筛选过程。",
        "3. 新闻筛选后，如需市场复盘，再运行 latest-review。",
        "",
        daily_export_text,
    ]
    return "\n".join(lines)


def _translate_daily_news_source_status(source_status: str) -> str:
    """Translate daily-news source state into user-facing Chinese text."""
    if source_status == "created-new":
        return "已新建"
    if source_status == "auto-generated":
        return "自动生成"
    if source_status == "reused-existing":
        return "复用已有文件"
    return source_status


def _build_news_batch_validation_text(batch_path: str) -> str:
    """Build one standalone validation summary for the batch-news input file."""
    normalized_batch_path = str(batch_path or "").strip()
    if not normalized_batch_path:
        return (
            "新闻批量校验\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main validate-news-batch "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="新闻批量校验",
        usage_command='python -m app.main validate-news-batch "news_batch.json"',
    )
    if error_text:
        return error_text

    lines = [
        "新闻批量校验",
        "",
        f"新闻源文件：{resolved_path}",
        "状态：有效",
        f"新闻条数：{len(items)}",
    ]

    if items:
        lines.append(f"第一条标题：{items[0]['title']}")

    lines.extend(
        [
            "",
            '下一步：python -m app.main classify-news-batch "news_batch.json" summary-only',
            '可选导出：python -m app.main export-news-batch "news_batch.json"',
            "",
            '用法：python -m app.main validate-news-batch "news_batch.json"',
        ]
    )
    return "\n".join(lines)


def _build_news_batch_first_pass_text(batch_path: str) -> str:
    """Run one validate-then-summary-first-pass path for batch-news input."""
    normalized_batch_path = str(batch_path or "").strip()
    if not normalized_batch_path:
        return (
            "新闻批量初筛\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main news-batch-first-pass "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="新闻批量初筛",
        usage_command='python -m app.main news-batch-first-pass "news_batch.json"',
    )
    if error_text:
        return error_text

    validation_lines = [
        "新闻批量初筛",
        "",
        f"新闻源文件：{resolved_path}",
        "校验：通过",
        f"新闻条数：{len(items)}",
    ]
    classification_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="summary-only",
        include_usage=False,
    )
    return "\n".join(
        [
            *validation_lines,
            "",
            classification_text,
        ]
    )


def _build_news_batch_priority_pass_text(batch_path: str) -> str:
    """Run one validate-then-high-priority-pass path for batch-news input."""
    normalized_batch_path = str(batch_path or "").strip()
    if not normalized_batch_path:
        return (
            "新闻批量优先级筛选\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main news-batch-priority-pass "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="新闻批量优先级筛选",
        usage_command='python -m app.main news-batch-priority-pass "news_batch.json"',
    )
    if error_text:
        return error_text

    validation_lines = [
        "新闻批量优先级筛选",
        "",
        f"新闻源文件：{resolved_path}",
        "校验：通过",
        f"新闻条数：{len(items)}",
    ]
    classification_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="high-priority-only",
        include_usage=False,
    )
    return "\n".join(
        [
            *validation_lines,
            "",
            classification_text,
        ]
    )


def _build_news_batch_priority_export_text(batch_path: str, export_path: str) -> str:
    """Run one validate-then-high-priority-export path for batch-news input."""
    normalized_batch_path = str(batch_path or "").strip()
    normalized_export_path = str(export_path or "").strip()
    if not normalized_batch_path:
        return (
            "新闻批量优先级导出\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main news-batch-priority-export "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="新闻批量优先级导出",
        usage_command='python -m app.main news-batch-priority-export "news_batch.json"',
    )
    if error_text:
        return error_text

    export_target = (
        Path(normalized_export_path)
        if normalized_export_path
        else resolved_path.with_name("news_batch_priority_summary.md")
    )
    summary_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="high-priority-only",
        include_usage=False,
    )
    export_target.write_text(summary_text, encoding="utf-8")
    return "\n".join(
        [
            "新闻批量优先级导出",
            "",
            f"新闻源文件：{resolved_path}",
            "校验：通过",
            f"保存到：{export_target}",
            "筛选模式：high-priority-only",
            "",
            '用法：python -m app.main news-batch-priority-export "news_batch.json"',
        ]
    )


def _build_batch_news_daily_flow_text(batch_path: str) -> str:
    """Build one daily-use batch-news flow that chains validation and both read passes."""
    normalized_batch_path = str(batch_path or "").strip()
    if not normalized_batch_path:
        return (
            "批量新闻每日流程\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main batch-news-daily-flow "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="批量新闻每日流程",
        usage_command='python -m app.main batch-news-daily-flow "news_batch.json"',
    )
    if error_text:
        return error_text

    first_pass_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="summary-only",
        include_usage=False,
    )
    priority_pass_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="high-priority-only",
        include_usage=False,
    )
    lines = [
        "批量新闻每日流程",
        "",
        f"新闻源文件：{resolved_path}",
        "校验：通过",
        f"新闻条数：{len(items)}",
        "",
        "摘要初筛",
        "",
        first_pass_text,
        "",
        "优先级筛选",
        "",
        priority_pass_text,
        "",
        '下一步归档命令：python -m app.main news-batch-priority-export "news_batch.json"',
    ]
    return "\n".join(lines)


def _build_batch_news_daily_export_text(batch_path: str, export_path: str) -> str:
    """Build one daily-use batch-news flow and save the high-priority summary."""
    normalized_batch_path = str(batch_path or "").strip()
    normalized_export_path = str(export_path or "").strip()
    if not normalized_batch_path:
        return (
            "批量新闻每日导出\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main batch-news-daily-export "news_batch.json"'
        )

    resolved_path = Path(normalized_batch_path)
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="批量新闻每日导出",
        usage_command='python -m app.main batch-news-daily-export "news_batch.json"',
    )
    if error_text:
        return error_text

    export_target = (
        Path(normalized_export_path)
        if normalized_export_path
        else _build_default_daily_news_export_path()
    )
    first_pass_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="summary-only",
        include_usage=False,
    )
    priority_pass_text = _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode="high-priority-only",
        include_usage=False,
    )
    export_target.parent.mkdir(parents=True, exist_ok=True)
    export_target.write_text(
        _build_daily_priority_summary_markdown(
            source_path=resolved_path,
            items=items,
            priority_pass_text=priority_pass_text,
        ),
        encoding="utf-8",
    )
    lines = [
        "批量新闻每日导出",
        "",
        f"新闻源文件：{resolved_path}",
        "校验：通过",
        f"新闻条数：{len(items)}",
        "",
        "摘要初筛",
        "",
        first_pass_text,
        "",
        "优先级筛选",
        "",
        priority_pass_text,
        "",
        f"已保存优先级摘要到：{export_target}",
        "默认归档规则：data/news/news_batch_priority_summary_YYYYMMDD.md",
    ]
    return "\n".join(lines)


def _build_daily_priority_summary_markdown(
    *,
    source_path: Path,
    items: list[dict[str, str]],
    priority_pass_text: str,
) -> str:
    """Build a more readable daily markdown header above the saved priority summary."""
    report_date = datetime.now().strftime("%Y-%m-%d")
    impact_summary = _extract_news_batch_summary_value(
        priority_pass_text,
        label="Impact summary",
    ) or "none"
    items_shown = _extract_news_batch_summary_value(
        priority_pass_text,
        label="Items shown",
    ) or "0/0"
    daily_conclusion = _build_daily_priority_conclusion(
        impact_summary=impact_summary,
        items_shown=items_shown,
    )
    status_color = _build_daily_status_color(impact_summary)
    defense_status = _build_daily_defense_status(impact_summary)
    theme_tags = _build_daily_theme_tags(impact_summary)
    core_summary = _build_daily_core_summary(
        status_color=status_color,
        theme_tags=theme_tags,
        defense_status=defense_status,
    )
    one_line_advice = _build_daily_one_line_advice(impact_summary)
    watchlist_lines = _build_daily_watchlist(priority_pass_text)
    operation_tip = _build_daily_operation_tip(priority_pass_text)
    processing_order_lines = _build_daily_processing_order(priority_pass_text)
    suggested_actions = _build_daily_priority_actions(priority_pass_text)
    lines = [
        "# Daily News Priority Summary",
        "",
        "This note is the same-day high-priority news watch summary for quick research reading.",
        "",
        f"- Date: {report_date}",
        f"- Source batch: {source_path}",
        f"- Total batch items: {len(items)}",
        f"- Priority items shown: {items_shown}",
        f"- Impact summary: {impact_summary}",
        "",
        "## Core Summary",
        "",
        core_summary,
        "",
        "## One-Line Advice",
        "",
        one_line_advice,
        "",
        "## Daily Conclusion",
        "",
        daily_conclusion,
        "",
        "## Operation Tip",
        "",
        operation_tip,
        "",
        "## Processing Order",
        "",
        *processing_order_lines,
        "",
        "## Watchlist",
        "",
        *watchlist_lines,
        "",
        "## Suggested Actions",
        "",
        *suggested_actions,
        "",
        "## 优先级筛选",
        "",
        _build_priority_pass_markdown(priority_pass_text),
    ]
    return "\n".join(lines)


def _extract_news_batch_summary_value(text: str, *, label: str) -> str:
    """Extract one top summary field from the rendered batch-news text."""
    prefixes = [f"{label}: "]
    translated_label = _translate_news_batch_summary_label(label)
    if translated_label != label:
        prefixes.append(f"{translated_label}：")
    for raw_line in str(text).splitlines():
        line = str(raw_line).strip()
        for prefix in prefixes:
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip()
    return ""


def _translate_news_batch_summary_label(label: str) -> str:
    """Map internal batch summary labels to the current visible Chinese labels."""
    return {
        "Impact summary": "影响摘要",
        "Items shown": "显示条数",
        "Source": "新闻源文件",
        "Items": "新闻条数",
        "Filter": "筛选模式",
    }.get(label, label)






def _build_daily_priority_conclusion(*, impact_summary: str, items_shown: str) -> str:
    """Build one short daily takeaway from the saved priority-pass summary."""
    risk_count = _extract_impact_count(impact_summary, "风险扩散")
    mainline_count = _extract_impact_count(impact_summary, "主线强化")
    local_count = _extract_impact_count(impact_summary, "局部验证")

    if risk_count > mainline_count:
        return (
            f"今日重点偏风险扩散，优先处理风险项。当前高优先级显示 {items_shown}，"
            f"其中风险扩散 {risk_count} 条、主线强化 {mainline_count} 条。"
        )
    if mainline_count > risk_count:
        return (
            f"今日重点偏主线强化，优先确认板块跟随。当前高优先级显示 {items_shown}，"
            f"其中主线强化 {mainline_count} 条、风险扩散 {risk_count} 条。"
        )
    if risk_count == 0 and mainline_count == 0 and local_count > 0:
        return f"今日重点偏观察验证，暂未出现更高优先级信号。当前高优先级显示 {items_shown}。"
    return (
        f"今日重点在风险与强化之间相对均衡，建议并行跟踪。当前高优先级显示 {items_shown}，"
        f"风险扩散 {risk_count} 条、主线强化 {mainline_count} 条。"
    )


def _extract_impact_count(impact_summary: str, label: str) -> int:
    """Extract one impact count from the compact impact-summary line."""
    for segment in str(impact_summary or "").split("|"):
        normalized_segment = str(segment).strip()
        if not normalized_segment.startswith(label):
            continue
        suffix = normalized_segment.removeprefix(label).strip()
        try:
            return int(suffix)
        except ValueError:
            return 0
    return 0


def _build_daily_theme_tags(impact_summary: str) -> str:
    """Build one compact theme-tag line for the saved daily summary header."""
    risk_count = _extract_impact_count(impact_summary, "风险扩散")
    mainline_count = _extract_impact_count(impact_summary, "主线强化")
    local_count = _extract_impact_count(impact_summary, "局部验证")
    tags: list[str] = []

    if risk_count > mainline_count:
        tags.append("风险扩散")
    elif mainline_count > risk_count:
        tags.append("主线强化")
    elif risk_count > 0 or mainline_count > 0:
        tags.append("均衡跟踪")
    elif local_count > 0:
        tags.append("观察验证")
    else:
        tags.append("平稳观察")

    if risk_count > 0 and "风险扩散" not in tags:
        tags.append("风险扩散")
    if mainline_count > 0 and "主线强化" not in tags:
        tags.append("主线强化")
    if local_count > 0 and "观察验证" not in tags:
        tags.append("观察验证")

    return " | ".join(tags)


def _build_daily_status_color(impact_summary: str) -> str:
    """Build one compact textual status-color label for the daily summary."""
    risk_count = _extract_impact_count(impact_summary, "风险扩散")
    mainline_count = _extract_impact_count(impact_summary, "主线强化")
    local_count = _extract_impact_count(impact_summary, "局部验证")

    if risk_count > mainline_count:
        return "红色：偏风险扩散"
    if mainline_count > risk_count:
        return "绿色：偏主线强化"
    if risk_count > 0 or mainline_count > 0:
        return "橙色：偏均衡跟踪"
    if local_count > 0:
        return "蓝色：偏观察验证"
    return "灰色：偏平稳观察"


def _build_daily_defense_status(impact_summary: str) -> str:
    """Build one short defense-first judgment for the daily summary header."""
    risk_count = _extract_impact_count(impact_summary, "风险扩散")
    mainline_count = _extract_impact_count(impact_summary, "主线强化")
    local_count = _extract_impact_count(impact_summary, "局部验证")

    if risk_count > mainline_count:
        return "需要重点防守：先确认风险是否扩散，再决定是否处理强化跟踪。"
    if mainline_count > risk_count:
        return "需要优先跟踪强化：先确认主线是否获得板块跟随。"
    if risk_count > 0 or mainline_count > 0:
        return "需要边防守边跟踪：风险与强化信号同时存在。"
    if local_count > 0:
        return "当前以观察验证为主：暂未出现更高优先级信号。"
    return "当前以平稳观察为主：优先回看原始新闻与快照变化。"


def _build_daily_core_summary(
    *,
    status_color: str,
    theme_tags: str,
    defense_status: str,
) -> str:
    """Build one single-line top summary from status, theme tags, and defense cue."""
    return f"{status_color} | 主题: {theme_tags} | {defense_status}"


def _build_daily_one_line_advice(impact_summary: str) -> str:
    """Build one short non-technical daily advice sentence."""
    risk_count = _extract_impact_count(impact_summary, "风险扩散")
    mainline_count = _extract_impact_count(impact_summary, "主线强化")
    local_count = _extract_impact_count(impact_summary, "局部验证")

    if risk_count > mainline_count:
        return "今天先以防守为主，先确认风险名单是否扩散，再处理其他机会。"
    if mainline_count > risk_count:
        return "今天先顺着强化主线继续跟踪，确认是否有板块共振。"
    if risk_count > 0 or mainline_count > 0:
        return "今天防守和跟踪都要兼顾，先看风险，再看强化。"
    if local_count > 0:
        return "今天以观察验证为主，确认是否值得升级到主线或风险。"
    return "今天先回看原始新闻和快照变化，等待更明确的优先级信号。"


def _build_priority_pass_markdown(priority_pass_text: str) -> str:
    """Convert the rendered priority-pass block into a more markdown-like section."""
    lines: list[str] = []
    for raw_line in str(priority_pass_text or "").splitlines():
        line = str(raw_line).strip()
        if not line or line == "News Batch Classification":
            continue
        if line.startswith(
            (
                "Source: ",
                "Items: ",
                "Impact summary: ",
                "Filter: ",
                "Items shown: ",
                "新闻源文件：",
                "新闻条数：",
                "影响摘要：",
                "筛选模式：",
                "显示条数：",
            )
        ):
            lines.append(f"- {line}")
            continue
        if ". " in line:
            possible_index, possible_title = line.split(". ", 1)
            if possible_index.isdigit():
                lines.extend(["", f"### {possible_index}. {possible_title.strip()}"])
                continue
        if line.startswith(("Level: ", "Bottom line: ", "级别：", "结论：")):
            lines.append(f"- {line}")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _is_news_bottom_line(line: str) -> bool:
    """Return whether a rendered news line is the bottom-line/action line."""
    normalized_line = str(line).strip()
    return normalized_line.startswith("Bottom line: ") or normalized_line.startswith("结论：")


def _strip_news_bottom_line_prefix(line: str) -> str:
    """Strip either the legacy English or current Chinese bottom-line prefix."""
    normalized_line = str(line).strip()
    if normalized_line.startswith("结论："):
        return normalized_line.removeprefix("结论：").strip()
    return normalized_line.removeprefix("Bottom line: ").strip()


def _build_daily_priority_actions(priority_pass_text: str) -> list[str]:
    """Build one grouped action list from the rendered high-priority batch summary."""
    risk_actions: list[str] = []
    mainline_actions: list[str] = []
    watch_actions: list[str] = []
    current_title = ""
    for raw_line in str(priority_pass_text or "").splitlines():
        line = str(raw_line).strip()
        if not line:
            continue
        if ". " in line:
            possible_index, possible_title = line.split(". ", 1)
            if possible_index.isdigit():
                current_title = possible_title.strip()
                continue
        if not _is_news_bottom_line(line):
            continue
        action_text = _strip_news_bottom_line_prefix(line)
        bullet_text = (
            f"- {current_title}: {action_text}"
            if current_title
            else f"- {action_text}"
        )
        if "更偏风险扩散" in action_text:
            risk_actions.append(bullet_text)
            continue
        if "更偏主线强化" in action_text:
            mainline_actions.append(bullet_text)
            continue
        watch_actions.append(bullet_text)

    grouped_lines: list[str] = []
    if risk_actions:
        grouped_lines.extend(["### 风险优先动作", "", *risk_actions, ""])
    if mainline_actions:
        grouped_lines.extend(["### 强化跟踪动作", "", *mainline_actions, ""])
    if watch_actions:
        grouped_lines.extend(["### 观察验证动作", "", *watch_actions, ""])

    if grouped_lines:
        if grouped_lines[-1] == "":
            grouped_lines.pop()
        return grouped_lines

    return ["- 今天没有生成高优先级动作建议。"]


def _build_daily_watchlist(priority_pass_text: str) -> list[str]:
    """Build one short grouped watchlist from the high-priority action wording."""
    risk_names: list[str] = []
    mainline_names: list[str] = []
    watch_names: list[str] = []
    for raw_line in str(priority_pass_text or "").splitlines():
        line = str(raw_line).strip()
        if not _is_news_bottom_line(line):
            continue
        action_text = _strip_news_bottom_line_prefix(line)
        extracted_names = _extract_watchlist_names_from_action(action_text)
        if not extracted_names:
            continue
        if "更偏风险扩散" in action_text:
            risk_names.extend(extracted_names)
            continue
        if "更偏主线强化" in action_text:
            mainline_names.extend(extracted_names)
            continue
        watch_names.extend(extracted_names)

    lines: list[str] = []
    if risk_names:
        lines.extend(["### 风险优先名单", "", *_build_watchlist_bullets(risk_names), ""])
    if mainline_names:
        lines.extend(["### 强化跟踪名单", "", *_build_watchlist_bullets(mainline_names), ""])
    if watch_names:
        lines.extend(["### 观察验证名单", "", *_build_watchlist_bullets(watch_names), ""])
    if lines:
        if lines[-1] == "":
            lines.pop()
        return lines
    return ["- 今天没有提取到观察名单。"]


def _build_daily_operation_tip(priority_pass_text: str) -> str:
    """Build one short first-read operating tip from the current watchlist groups."""
    risk_names = _build_daily_watchlist_names(priority_pass_text, signal="risk")
    mainline_names = _build_daily_watchlist_names(priority_pass_text, signal="mainline")
    watch_names = _build_daily_watchlist_names(priority_pass_text, signal="watch")

    if risk_names:
        return "先看风险优先名单，再看强化跟踪名单；如果风险未扩散，再回到观察验证名单。"
    if mainline_names:
        return "先看强化跟踪名单，确认主线是否继续扩散；再回到观察验证名单。"
    if watch_names:
        return "先看观察验证名单，确认是否值得升级到主线或风险。"
    return "今天没有提取到明确名单，先回看优先级摘要和原始新闻。"


def _build_daily_processing_order(priority_pass_text: str) -> list[str]:
    """Build one short ordered reading sequence for the daily summary header."""
    risk_names = _build_daily_watchlist_names(priority_pass_text, signal="risk")
    mainline_names = _build_daily_watchlist_names(priority_pass_text, signal="mainline")
    watch_names = _build_daily_watchlist_names(priority_pass_text, signal="watch")

    lines: list[str] = []
    if risk_names:
        lines.append("1. 先看风险优先名单")
    if mainline_names:
        lines.append(f"{len(lines) + 1}. 再看强化跟踪名单")
    if watch_names:
        lines.append(f"{len(lines) + 1}. 最后看观察验证名单")
    if lines:
        return lines
    return ["1. 先回看原始新闻和优先级摘要"]


def _extract_watchlist_names_from_action(action_text: str) -> list[str]:
    """Extract watchlist stock names from one suggested-action sentence."""
    marker = "当前建议："
    normalized_text = str(action_text or "").strip()
    if marker not in normalized_text:
        return []
    suggestion_text = normalized_text.split(marker, 1)[1].strip()
    for prefix in ("优先盯核心池 ", "优先盯观察池 ", "优先盯 ", "优先关注 "):
        if suggestion_text.startswith(prefix):
            suggestion_text = suggestion_text.removeprefix(prefix).strip()
            break
    if " 是否" in suggestion_text:
        suggestion_text = suggestion_text.split(" 是否", 1)[0].strip()
    suggestion_text = suggestion_text.strip("。；;，, ")
    if not suggestion_text:
        return []
    normalized_names = suggestion_text.replace("、", ",").replace("，", ",")
    return [name.strip() for name in normalized_names.split(",") if name.strip()]


def _build_watchlist_bullets(names: list[str]) -> list[str]:
    """Build stable de-duplicated watchlist bullets."""
    seen: set[str] = set()
    bullets: list[str] = []
    for name in names:
        normalized_name = str(name).strip()
        if not normalized_name or normalized_name in seen:
            continue
        seen.add(normalized_name)
        bullets.append(f"- {normalized_name}")
    return bullets


def _build_daily_watchlist_names(priority_pass_text: str, *, signal: str) -> list[str]:
    """Collect de-duplicated watchlist names for one signal bucket."""
    names: list[str] = []
    for raw_line in str(priority_pass_text or "").splitlines():
        line = str(raw_line).strip()
        if not _is_news_bottom_line(line):
            continue
        action_text = _strip_news_bottom_line_prefix(line)
        extracted_names = _extract_watchlist_names_from_action(action_text)
        if not extracted_names:
            continue
        if signal == "risk" and "更偏风险扩散" in action_text:
            names.extend(extracted_names)
        elif signal == "mainline" and "更偏主线强化" in action_text:
            names.extend(extracted_names)
        elif (
            signal == "watch"
            and "更偏风险扩散" not in action_text
            and "更偏主线强化" not in action_text
        ):
            names.extend(extracted_names)
    deduplicated_bullets = _build_watchlist_bullets(names)
    return [bullet.removeprefix("- ").strip() for bullet in deduplicated_bullets]

def _build_news_batch_classification_text(batch_path: str, *, filter_mode: str = "") -> str:
    """Build one compact batch summary for multiple local news items."""
    resolved_path = Path(str(batch_path or "").strip())
    normalized_filter_mode = str(filter_mode or "").strip()
    if not str(batch_path or "").strip():
        return (
            "新闻批量分类\n\n"
            '未提供新闻批量文件。\n用法：python -m app.main classify-news-batch "news_batch.json"'
        )
    filter_error = _build_news_batch_filter_error_text(
        normalized_filter_mode,
        label="新闻批量分类",
    )
    if filter_error:
        return filter_error
    items, error_text = _load_news_batch_items(
        resolved_path,
        label="新闻批量分类",
        usage_command='python -m app.main classify-news-batch "news_batch.json"',
    )
    if error_text:
        return error_text
    return _build_news_batch_classification_text_from_items(
        resolved_path,
        items,
        filter_mode=normalized_filter_mode,
    )


def _build_news_batch_classification_text_from_items(
    source_path: Path,
    items: list[dict[str, str]],
    *,
    filter_mode: str = "",
    include_usage: bool = True,
) -> str:
    """Build one compact batch summary after the batch input is validated."""
    normalized_filter_mode = str(filter_mode or "").strip()
    impact_labels: list[str] = []
    entry_rows: list[dict[str, object]] = []
    lines = [
        "新闻批量分类",
        "",
        f"新闻源文件：{source_path}",
        f"新闻条数：{len(items)}",
    ]

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        result = classify_news(title, content)
        impact_view = _build_news_impact_view(result)
        suggested_action = _build_news_observation_suggestion(result)
        bottom_line = _build_news_bottom_line(impact_view, suggested_action)
        impact_label = _extract_news_impact_label(impact_view)
        impact_labels.append(impact_label)
        entry_rows.append(
            {
                "title": title or "(empty title)",
                "level": str(result["level"]),
                "sector": str(result["related_sector"]),
                "bottom_line": bottom_line,
                "impact_label": impact_label,
                "sort_key": _build_news_batch_sort_key(
                    impact_label=impact_label,
                    level=str(result["level"]),
                    original_index=index,
                ),
            }
        )

    lines.insert(4, f"影响摘要：{_build_news_batch_impact_summary(impact_labels)}")
    sorted_entry_rows = sorted(
        entry_rows,
        key=lambda row: tuple(row.get("sort_key", (99, 99, 99))),
    )
    filtered_entry_rows = _filter_news_batch_entry_rows(
        sorted_entry_rows,
        filter_mode=normalized_filter_mode,
    )
    if normalized_filter_mode:
        lines.append(f"筛选模式：{normalized_filter_mode}")
        lines.append(f"显示条数：{len(filtered_entry_rows)}/{len(sorted_entry_rows)}")
    for display_index, row in enumerate(filtered_entry_rows, start=1):
        lines.extend(
            _build_news_batch_entry_lines(
                display_index=display_index,
                row=row,
                filter_mode=normalized_filter_mode,
            )
        )

    if include_usage:
        lines.extend(
            [
                "",
                '用法：python -m app.main classify-news-batch "news_batch.json"',
            ]
        )
    return "\n".join(lines)


def _build_news_batch_filter_error_text(filter_mode: str, *, label: str) -> str:
    """Build one clear error block when the batch-news filter mode is invalid."""
    normalized_filter_mode = str(filter_mode or "").strip()
    if not normalized_filter_mode or normalized_filter_mode in NEWS_BATCH_FILTER_MODES:
        return ""
    available_modes = ", ".join(sorted(NEWS_BATCH_FILTER_MODES))
    return "\n".join(
        [
            label,
            "",
            f"不支持的筛选模式：{normalized_filter_mode}",
            f"可用筛选模式：{available_modes}",
        ]
    )


def _load_news_batch_items(
    batch_path: Path,
    *,
    label: str,
    usage_command: str = 'python -m app.main classify-news-batch "news_batch.json"',
) -> tuple[list[dict[str, str]], str]:
    """Load and validate the batch-news JSON input before classification/export."""
    if not batch_path.exists():
        return [], "\n".join(
            [
                label,
                "",
                f"未找到新闻批量文件：{batch_path}",
                f"用法：{usage_command}",
            ]
        )

    try:
        raw_items = json.loads(batch_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return [], "\n".join(
            [
                label,
                "",
                f"新闻批量文件 JSON 格式错误：{batch_path}",
                f"JSON 错误：{exc.msg}",
                f"用法：{usage_command}",
            ]
        )

    if not isinstance(raw_items, list):
        return [], "\n".join(
            [
                label,
                "",
                f"新闻批量文件结构错误：{batch_path}",
                "顶层 JSON 必须是列表。",
                f"用法：{usage_command}",
            ]
        )

    validated_items: list[dict[str, str]] = []
    validation_issues: list[str] = []
    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            validation_issues.append(f"第 {index} 条：必须是包含 title/content 字段的对象。")
            continue
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title:
            validation_issues.append(f"第 {index} 条：缺少 title。")
        if not content:
            validation_issues.append(f"第 {index} 条：缺少 content。")
        if title and content:
            validated_items.append({"title": title, "content": content})

    if validation_issues:
        return [], "\n".join(
            [
                label,
                "",
                f"新闻批量条目错误：{batch_path}",
                *validation_issues,
                f"用法：{usage_command}",
            ]
        )

    return validated_items, ""






def _build_news_chain_hint(result: dict[str, str]) -> str:
    """Build one plain-language chain-positioning hint from the related sector."""
    related_sector = str(result.get("related_sector", "")).strip()
    if not related_sector:
        return "暂未识别到明确产业链位置，先结合原始新闻继续判断。"
    return NEWS_CHAIN_HINTS.get(
        related_sector,
        f"偏{related_sector}链，建议结合上下游联动继续观察。",
    )


def _build_news_impact_view(result: dict[str, str]) -> str:
    """Build one short same-day impact view from lightweight rules."""
    sentiment = str(result.get("sentiment", "")).strip()
    level = str(result.get("level", "")).strip()
    related_stocks = [
        item.strip()
        for item in str(result.get("related_stocks", "")).split(",")
        if item.strip()
    ]
    related_sector = str(result.get("related_sector", "")).strip()

    if sentiment == "negative" and level == "S":
        return "更偏风险扩散，优先检查相关板块是否同步承压。"
    if sentiment == "positive" and level == "A" and related_stocks:
        return "更偏主线强化，优先确认是否获得板块跟随。"
    if sentiment == "positive" and related_sector:
        return "更偏局部验证，先确认是否能从单点扩散到板块。"
    if sentiment == "neutral" and related_sector:
        return "更偏局部验证，建议继续观察验证。"
    return "更偏局部验证，暂时保持观察。"


def _build_news_bottom_line(impact_view: str, suggested_action: str) -> str:
    """Build one compact takeaway line from impact and action guidance."""
    normalized_impact = str(impact_view or "").strip()
    normalized_action = str(suggested_action or "").strip()
    if normalized_impact and normalized_action:
        return f"{normalized_impact} 当前建议：{normalized_action}"
    if normalized_impact:
        return normalized_impact
    if normalized_action:
        return normalized_action
    return "暂未形成明确底线结论。"


def _extract_news_impact_label(impact_view: str) -> str:
    """Extract the leading impact label from one impact-view sentence."""
    normalized = str(impact_view or "").strip()
    if not normalized:
        return "局部验证"
    for label in ("风险扩散", "主线强化", "局部验证"):
        if label in normalized:
            return label
    return "局部验证"


def _build_news_batch_impact_summary(impact_labels: list[str]) -> str:
    """Build one compact batch-level distribution summary."""
    risk_count = sum(1 for label in impact_labels if label == "风险扩散")
    mainline_count = sum(1 for label in impact_labels if label == "主线强化")
    local_count = sum(1 for label in impact_labels if label == "局部验证")
    return f"风险扩散 {risk_count} | 主线强化 {mainline_count} | 局部验证 {local_count}"


def _build_news_observation_suggestion(result: dict[str, str]) -> str:
    """Build one practical observation suggestion from classified news context."""
    related_sector = str(result.get("related_sector", "")).strip()
    related_stocks = [
        item.strip()
        for item in str(result.get("related_stocks", "")).split(",")
        if item.strip()
    ]
    sentiment = str(result.get("sentiment", "")).strip()
    level = str(result.get("level", "")).strip()
    stock_priorities = _resolve_stock_priorities(related_stocks)
    has_priority_one = any(priority == 1 for priority in stock_priorities.values())

    if related_stocks:
        joined = "、".join(related_stocks)
        if sentiment == "positive":
            prefix = "优先盯核心池 " if has_priority_one else "优先关注 "
            return prefix + joined + " 是否获得板块跟随确认。"
        if sentiment == "negative" and level == "S":
            prefix = "优先盯核心池 " if has_priority_one else "优先关注 "
            return prefix + joined + " 是否出现同步承压。"

    sector_watchlist, sector_has_priority_one = _build_sector_watchlist(
        related_sector,
        limit=3,
    )
    if related_sector and sector_watchlist:
        joined = "、".join(sector_watchlist)
        sector_prefix = "优先盯核心池 " if sector_has_priority_one else "优先关注板块池 "
        if sentiment == "negative" and level == "S":
            return sector_prefix + joined + " 是否出现同步承压。"
        return sector_prefix + joined + " 是否获得板块跟随确认。"
    if related_sector:
        return f"优先关注{related_sector}链是否出现板块联动。"
    return ""

def _resolve_stock_priorities(stock_names: list[str]) -> dict[str, int]:
    """Resolve monitor-pool priorities for directly matched stock names."""
    if not stock_names:
        return {}
    stock_name_set = {str(name).strip() for name in stock_names if str(name).strip()}
    priorities: dict[str, int] = {}
    for stock in get_all_stocks():
        name = str(stock.get("name", "")).strip()
        if name not in stock_name_set:
            continue
        priorities[name] = int(stock.get("priority", 99))
    return priorities


def _build_sector_watchlist(sector: str, *, limit: int = 3) -> tuple[list[str], bool]:
    """Build a small priority-first watchlist from one monitored sector."""
    sector_rows = get_stocks_by_sector(sector)
    if not sector_rows:
        return [], False
    sorted_rows = sorted(
        sector_rows,
        key=lambda row: (
            int(row.get("priority", 99)),
            str(row.get("name", "")),
        ),
    )
    watchlist = [
        str(row.get("name", "")).strip()
        for row in sorted_rows
        if str(row.get("name", "")).strip()
    ][:limit]
    watchlist_name_set = set(watchlist)
    has_priority_one = any(
        str(row.get("name", "")).strip() in watchlist_name_set
        and int(row.get("priority", 99)) == 1
        for row in sorted_rows
    )
    return watchlist, has_priority_one


def _normalize_export_news_batch_args(
    export_path: str,
    filter_mode: str,
) -> tuple[str, str]:
    """Normalize export args so filter-only CLI usage works reliably."""
    normalized_export_path = str(export_path or "").strip()
    normalized_filter_mode = str(filter_mode or "").strip()
    if (
        normalized_export_path in NEWS_BATCH_FILTER_MODES
        and not normalized_filter_mode
    ):
        return "", normalized_export_path
    return normalized_export_path, normalized_filter_mode


def _filter_news_batch_entry_rows(
    entry_rows: list[dict[str, object]],
    *,
    filter_mode: str,
) -> list[dict[str, object]]:
    """Filter batch-news rows using one minimal local mode."""
    normalized_filter_mode = str(filter_mode or "").strip()
    if normalized_filter_mode == "high-priority-only":
        return [
            row
            for row in entry_rows
            if str(row.get("impact_label", "")).strip() in {"风险扩散", "主线强化"}
        ]
    return list(entry_rows)


def _build_news_batch_entry_lines(
    *,
    display_index: int,
    row: dict[str, object],
    filter_mode: str,
) -> list[str]:
    """Build one compact visible block for a batch-news entry."""
    title = str(row.get("title", "")).strip() or "(empty title)"
    level = str(row.get("level", "")).strip()
    sector = str(row.get("sector", "")).strip()
    bottom_line = str(row.get("bottom_line", "")).strip()
    normalized_filter_mode = str(filter_mode or "").strip()

    lines = [
        "",
        f"{display_index}. {title}",
        f"级别：{level} | 板块：{sector}",
    ]
    if normalized_filter_mode != "summary-only" and bottom_line:
        lines.append(f"结论：{bottom_line}")
    return lines


def _build_news_batch_sort_key(
    *,
    impact_label: str,
    level: str,
    original_index: int,
) -> tuple[int, int, int]:
    """Build a stable sort key so risk first, then mainline, then local items."""
    impact_priority = {
        "风险扩散": 0,
        "主线强化": 1,
        "局部验证": 2,
    }.get(str(impact_label).strip(), 3)
    level_priority = {
        "S": 0,
        "A": 1,
        "B": 2,
        "C": 3,
    }.get(str(level).strip(), 4)
    return (impact_priority, level_priority, int(original_index))


def _build_stock_pool_validation_text(
    result: dict[str, object],
    comparison: dict[str, object],
) -> str:
    """Build a human-readable validation summary for the stock pool."""
    status = str(result.get("status", "unknown"))
    lines = ["Stock Pool Validation", "", "Status Summary"]
    lines.extend(
        [
            f"Status: {status}",
            f"Source: {result['source_path']}",
            f"Record count: {result['record_count']}",
        ]
    )
    structure_summary = str(result.get("structure_summary", "")).strip()
    if structure_summary:
        lines.append(f"Structure summary: {structure_summary}")
    lines.extend(["", "Structure Summary"])
    lines.append("Sector counts:")
    for sector, count in _sort_count_items(dict(result["sector_counts"])):
        lines.append(f"- {sector}: {count}")
    lines.append("Chain-group counts:")
    chain_group_counts = dict(result.get("chain_group_counts", {}))
    if chain_group_counts:
        for chain_group, count in _sort_count_items(chain_group_counts):
            lines.append(f"- {chain_group}: {count}")
    else:
        lines.append("- none")
    lines.append("Pool-type counts:")
    pool_type_counts = dict(result.get("pool_type_counts", {}))
    if pool_type_counts:
        for pool_type, count in _sort_count_items(pool_type_counts):
            lines.append(f"- {pool_type}: {count}")
    else:
        lines.append("- none")
    lines.append("Priority counts:")
    for priority, count in _sort_count_items(dict(result["priority_counts"])):
        lines.append(f"- P{priority}: {count}")
    lines.extend(["", "Structure Comparison"])
    lines.append(f"Snapshot path: {comparison['snapshot_path']}")
    comparison_tag_labels = list(comparison.get("comparison_tag_labels", []))
    if comparison_tag_labels:
        lines.append(
            "Change tags: " + ", ".join(str(tag_label) for tag_label in comparison_tag_labels)
        )
    comparison_tag_groups = [
        str(group.get("summary", "")).strip()
        for group in list(comparison.get("comparison_tag_groups", []))
        if isinstance(group, dict) and str(group.get("summary", "")).strip()
    ]
    if comparison_tag_groups:
        lines.append("Change groups: " + " | ".join(comparison_tag_groups))
    highlight_summary = str(comparison.get("highlight_summary", "")).strip()
    if highlight_summary:
        lines.append(f"Change highlight: {highlight_summary}")
    lines.append(str(comparison.get("comparison_summary", "")).strip())
    change_rows = list(comparison.get("change_rows", []))
    if change_rows:
        lines.append("Top structure changes:")
        lines.extend(change_rows)
    lines.extend(["", "Detailed Validation"])
    duplicate_codes = list(result["duplicate_codes"])
    if duplicate_codes:
        lines.append("Duplicate codes: " + ", ".join(duplicate_codes))
    else:
        lines.append("Duplicate codes: none")
    unknown_sectors = list(result.get("unknown_sectors", []))
    if unknown_sectors:
        lines.append("Unknown sectors: " + ", ".join(unknown_sectors))
    else:
        lines.append("Unknown sectors: none")
    unknown_sector_suggestions = dict(result.get("unknown_sector_suggestions", {}))
    if unknown_sector_suggestions:
        lines.append("Possible matches:")
        for sector, suggestion in unknown_sector_suggestions.items():
            lines.append(f"- {sector} -> {suggestion}")
    lines.append("Registered sectors:")
    for sector in list(result.get("registered_sectors", [])):
        lines.append(f"- {sector}")
    unknown_chain_groups = list(result.get("unknown_chain_groups", []))
    if unknown_chain_groups:
        lines.append("Unknown chain groups: " + ", ".join(unknown_chain_groups))
    else:
        lines.append("Unknown chain groups: none")
    unknown_chain_group_suggestions = dict(
        result.get("unknown_chain_group_suggestions", {})
    )
    if unknown_chain_group_suggestions:
        lines.append("Possible chain-group matches:")
        for chain_group, suggestion in unknown_chain_group_suggestions.items():
            lines.append(f"- {chain_group} -> {suggestion}")
    lines.append("Registered chain groups:")
    for chain_group in list(result.get("registered_chain_groups", [])):
        lines.append(f"- {chain_group}")
    unknown_markets = list(result.get("unknown_markets", []))
    if unknown_markets:
        lines.append("Unknown markets: " + ", ".join(unknown_markets))
    else:
        lines.append("Unknown markets: none")
    unknown_market_suggestions = dict(result.get("unknown_market_suggestions", {}))
    if unknown_market_suggestions:
        lines.append("Possible market matches:")
        for market, suggestion in unknown_market_suggestions.items():
            lines.append(f"- {market} -> {suggestion}")
    lines.append("Registered markets:")
    for market in list(result.get("registered_markets", [])):
        lines.append(f"- {market}")
    unknown_pool_types = list(result.get("unknown_pool_types", []))
    if unknown_pool_types:
        lines.append("Unknown pool types: " + ", ".join(unknown_pool_types))
    else:
        lines.append("Unknown pool types: none")
    unknown_pool_type_suggestions = dict(
        result.get("unknown_pool_type_suggestions", {})
    )
    if unknown_pool_type_suggestions:
        lines.append("Possible pool-type matches:")
        for pool_type, suggestion in unknown_pool_type_suggestions.items():
            lines.append(f"- {pool_type} -> {suggestion}")
    lines.append("Registered pool types:")
    for pool_type in list(result.get("registered_pool_types", [])):
        lines.append(f"- {pool_type}")
    lines.append("Health hints:")
    health_hints = list(result.get("health_hints", []))
    if health_hints:
        for hint in health_hints:
            lines.append(f"- {hint}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def _build_task_profile_validation_text() -> str:
    """Build a simple validation summary for the task-profile config."""
    lines = [
        "Task Profile Validation",
        "",
        "Status Summary",
        "Status: ok",
        f"Source: {TASK_PROFILE_CONFIG_PATH}",
        "",
    ]
    lines.extend(build_task_overview_lines())
    lines.extend(["", *build_output_profiles_lines()])
    return "\n".join(lines)


def _sort_count_items(counts: dict[object, object]) -> list[tuple[object, object]]:
    """Sort summary counts by count descending, then label ascending."""
    return sorted(
        counts.items(),
        key=lambda item: (-int(item[1]), str(item[0])),
    )


if __name__ == "__main__":
    main(sys.argv[1:])

