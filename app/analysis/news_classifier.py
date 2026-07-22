"""Keyword-based classifier for AI and semiconductor news."""

from __future__ import annotations

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
from app.universe.stock_pool import get_all_stocks

NEGATIVE_NEWS_KEYWORDS = ("出口管制", "实体清单", "关税")
POSITIVE_NEWS_KEYWORDS = ("客户认证", "批量供货", "国产替代")
SECTOR_KEYWORD_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (SEMICONDUCTOR_EQUIPMENT_SECTOR, ("设备", "刻蚀", "薄膜", "清洗", "量测")),
    (SEMICONDUCTOR_MATERIAL_SECTOR, ("材料", "硅片", "光刻胶", "抛光液", "靶材", "前驱体")),
    (SEMICONDUCTOR_GAS_SECTOR, ("气体", "特气", "电子气", "电子特气")),
    (AI_CPO_SECTOR, ("CPO", "光模块")),
    (AI_SERVER_SECTOR, ("算力", "服务器", "交换机")),
    (PCB_SECTOR, ("PCB", "高速板")),
    (COOLING_SECTOR, ("液冷", "散热", "数据中心")),
    (HBM_SECTOR, ("HBM", "存储", "内存")),
    (CHIPLET_SECTOR, ("封装", "封测", "Chiplet", "chiplet")),
)


def classify_news(title: str, content: str) -> dict[str, str]:
    """Classify a news item with lightweight keyword and mapping rules."""
    normalized_title = str(title or "").strip()
    normalized_content = str(content or "").strip()
    text = f"{normalized_title}\n{normalized_content}"
    sentiment = "neutral"
    level = "C"
    reason = "No keyword rules configured yet."

    if any(keyword in text for keyword in NEGATIVE_NEWS_KEYWORDS):
        sentiment = "negative"
        level = "S"
        reason = "Matched high-impact risk keyword."
    elif any(keyword in text for keyword in POSITIVE_NEWS_KEYWORDS):
        sentiment = "positive"
        level = "A"
        reason = "Matched industry positive keyword."

    return {
        "related_sector": _infer_related_sector(text),
        "related_stocks": _infer_related_stocks(text),
        "sentiment": sentiment,
        "level": level,
        "confidence": "medium",
        "reason": reason,
    }


def _infer_related_sector(text: str) -> str:
    """Infer one related monitored sector from lightweight keyword rules."""
    normalized_text = str(text or "").strip()
    if not normalized_text:
        return "待确认"
    for sector, keywords in SECTOR_KEYWORD_RULES:
        if any(keyword in normalized_text for keyword in keywords):
            return sector
    return "待确认"


def _infer_related_stocks(text: str) -> str:
    """Infer related monitored stock names if they appear directly in the text."""
    normalized_text = str(text or "").strip()
    if not normalized_text:
        return ""
    comparable_text = _normalize_stock_name_for_match(normalized_text)

    matched_names: list[str] = []
    for stock in get_all_stocks():
        name = str(stock.get("name", "")).strip()
        if not name or name in matched_names:
            continue
        comparable_name = _normalize_stock_name_for_match(name)
        if name in normalized_text or (comparable_name and comparable_name in comparable_text):
            matched_names.append(name)
    return ", ".join(matched_names)


def _normalize_stock_name_for_match(value: str) -> str:
    """Normalize stock-name punctuation so news text can match common aliases."""
    return (
        str(value)
        .replace("-", "")
        .replace("－", "")
        .replace("—", "")
        .replace(" ", "")
        .strip()
    )
