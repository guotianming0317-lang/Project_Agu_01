"""Render the configurable US market close overview block."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path("data/market/us_market_summary.json")


def load_us_market_overview(path: str | Path | None = None) -> dict[str, Any]:
    """Load a local snapshot without inventing market values."""
    configured = str(path or os.getenv("MONITOR_US_MARKET_SUMMARY_PATH", "")).strip()
    snapshot_path = Path(configured) if configured else DEFAULT_PATH
    if not snapshot_path.exists():
        return {"status": "unavailable", "source": str(snapshot_path)}
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "invalid", "source": str(snapshot_path)}
    if not isinstance(payload, dict):
        return {"status": "invalid", "source": str(snapshot_path)}
    payload.setdefault("status", "ready")
    payload.setdefault("source", str(snapshot_path))
    return payload


def build_us_market_overview_text(payload: dict[str, Any] | None = None) -> str:
    """Build the top-of-report Chinese overview block."""
    data = payload or load_us_market_overview()
    lines = ["美股收盘概括", ""]
    if data.get("status") != "ready":
        lines.extend([
            "状态：暂无可用的美股收盘数据。",
            "待配置：纳斯达克综合指数、费城半导体指数的真实行情快照。",
            "说明：未使用演示值；配置数据源后会自动显示开盘、盘中、收盘和强弱板块。",
        ])
        return "\n".join(lines)

    lines.append(f"数据日期：{data.get('date', '未提供')}")
    lines.append(f"数据来源：{data.get('source_name', data.get('source', '未提供'))}")
    for key, label in (("nasdaq", "纳斯达克综合指数"), ("sox", "费城半导体指数")):
        index = data.get(key) if isinstance(data.get(key), dict) else {}
        lines.extend([
            f"{label}：开盘 {index.get('open', '暂无')} | 盘中 {index.get('intraday', '暂无')} | 收盘 {index.get('close', '暂无')} | 涨跌 {index.get('change', '暂无')}",
            f"趋势简述：{index.get('trend', '暂无趋势描述')}",
        ])
    lines.append(f"强势板块：{_join_sectors(data.get('strong_sectors'))}")
    lines.append(f"弱势板块：{_join_sectors(data.get('weak_sectors'))}")
    lines.append(f"简短分析：{data.get('sector_analysis', '暂无板块分析')}")
    focus = data.get("focus_sectors") if isinstance(data.get("focus_sectors"), dict) else {}
    lines.extend([
        "重点关注板块",
        "半导体：半导体设备、半导体材料、晶圆制造、封装测试、电子气体、光刻胶。",
        f"半导体相关ETF表现：{_join_sectors(focus.get('半导体'))}",
        "AI：AI芯片、服务器/算力硬件、液冷、CPO/光模块、PCB、HBM存储。",
        f"AI相关ETF表现：{_join_sectors(focus.get('AI'))}",
    ])
    return "\n".join(lines)


def _join_sectors(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "暂无"
    return str(value or "暂无")
