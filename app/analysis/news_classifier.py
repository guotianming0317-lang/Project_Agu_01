"""Keyword-based classifier for AI and semiconductor news."""

from __future__ import annotations


def classify_news(title: str, content: str) -> dict[str, str]:
    """Classify a news item with a simple placeholder result."""
    text = f"{title}\n{content}"
    sentiment = "neutral"
    level = "C"
    reason = "No keyword rules configured yet."

    if any(keyword in text for keyword in ("出口管制", "实体清单", "关税")):
        sentiment = "negative"
        level = "S"
        reason = "Matched high-impact risk keyword."
    elif any(keyword in text for keyword in ("客户认证", "批量供货", "国产替代")):
        sentiment = "positive"
        level = "A"
        reason = "Matched industry positive keyword."

    return {
        "related_sector": "待补充",
        "related_stocks": "",
        "sentiment": sentiment,
        "level": level,
        "confidence": "medium",
        "reason": reason,
    }
