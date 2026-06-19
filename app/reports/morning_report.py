"""Morning report builder."""

from __future__ import annotations


def build_morning_report() -> str:
    """Build a minimal morning report template."""
    return "\n".join(
        [
            "【今日主线判断】",
            "1. 海外AI半导体强弱：待接入",
            "2. A股可能映射方向：待判断",
            "3. 今日重点观察板块：半导体材料/气体",
            "4. 今日重点观察个股：中巨芯-U、华特气体、沪硅产业",
            "5. 主要风险：待接入",
            "6. 仓位倾向：观察",
        ]
    )
