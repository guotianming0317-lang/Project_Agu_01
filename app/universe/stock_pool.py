"""Observation universe for AI and semiconductor A-share stocks."""

from __future__ import annotations

from typing import Iterable

from app.models import StockRecord


STOCK_POOL: list[StockRecord] = [
    StockRecord("300308", "中际旭创", "AI光模块/CPO", "光模块", 1),
    StockRecord("300502", "新易盛", "AI光模块/CPO", "光模块", 1),
    StockRecord("300394", "天孚通信", "AI光模块/CPO", "光模块", 1),
    StockRecord("002281", "光迅科技", "AI光模块/CPO", "光模块", 2),
    StockRecord("603083", "剑桥科技", "AI光模块/CPO", "光模块", 2),
    StockRecord("000988", "华工科技", "AI光模块/CPO", "光模块", 2),
    StockRecord("601138", "工业富联", "AI服务器/算力硬件", "服务器", 1),
    StockRecord("000977", "浪潮信息", "AI服务器/算力硬件", "服务器", 1),
    StockRecord("603019", "中科曙光", "AI服务器/算力硬件", "服务器", 1),
    StockRecord("000938", "紫光股份", "AI服务器/算力硬件", "服务器", 2),
    StockRecord("002463", "沪电股份", "PCB/高速板", "PCB", 1),
    StockRecord("300476", "胜宏科技", "PCB/高速板", "PCB", 1),
    StockRecord("002916", "深南电路", "PCB/高速板", "PCB", 1),
    StockRecord("600183", "生益科技", "PCB/高速板", "PCB", 2),
    StockRecord("002837", "英维克", "液冷/数据中心散热", "液冷", 1),
    StockRecord("300499", "高澜股份", "液冷/数据中心散热", "液冷", 2),
    StockRecord("301018", "申菱环境", "液冷/数据中心散热", "液冷", 2),
    StockRecord("002371", "北方华创", "半导体设备", "设备", 1),
    StockRecord("688012", "中微公司", "半导体设备", "设备", 1),
    StockRecord("688072", "拓荆科技", "半导体设备", "设备", 1),
    StockRecord("688120", "华海清科", "半导体设备", "设备", 2),
    StockRecord("688126", "沪硅产业", "半导体材料/气体", "硅片", 1),
    StockRecord("688549", "中巨芯-U", "半导体材料/气体", "电子特气", 1),
    StockRecord("688268", "华特气体", "半导体材料/气体", "电子特气", 1),
    StockRecord("688106", "金宏气体", "半导体材料/气体", "电子特气", 1),
    StockRecord("688019", "安集科技", "半导体材料/气体", "CMP抛光液", 1),
    StockRecord("300054", "鼎龙股份", "半导体材料/气体", "CMP抛光垫/光刻胶", 1),
    StockRecord("300666", "江丰电子", "半导体材料/气体", "靶材", 1),
    StockRecord("300346", "南大光电", "半导体材料/气体", "前驱体/光刻胶", 1),
    StockRecord("603650", "彤程新材", "半导体材料/气体", "光刻胶", 2),
    StockRecord("300655", "晶瑞电材", "半导体材料/气体", "电子化学品", 2),
    StockRecord("300236", "上海新阳", "半导体材料/气体", "电子化学品", 2),
    StockRecord("002409", "雅克科技", "半导体材料/气体", "前驱体", 2),
    StockRecord("600206", "有研新材", "半导体材料/气体", "靶材/材料", 2),
    StockRecord("688233", "神工股份", "半导体材料/气体", "硅材料", 2),
    StockRecord("603986", "兆易创新", "存储/HBM", "存储", 1),
    StockRecord("688525", "佰维存储", "存储/HBM", "存储模组", 1),
    StockRecord("301308", "江波龙", "存储/HBM", "存储模组", 1),
    StockRecord("688008", "澜起科技", "存储/HBM", "互连/内存接口", 1),
    StockRecord("600584", "长电科技", "先进封装/Chiplet", "先进封装", 1),
    StockRecord("002156", "通富微电", "先进封装/Chiplet", "先进封装", 1),
    StockRecord("002185", "华天科技", "先进封装/Chiplet", "先进封装", 2),
    StockRecord("688362", "甬矽电子", "先进封装/Chiplet", "先进封装", 2),
]


def _to_dicts(records: Iterable[StockRecord]) -> list[dict[str, str | int]]:
    """Convert stock records into plain dictionaries."""
    return [
        {
            "code": record.code,
            "name": record.name,
            "sector": record.sector,
            "sub_sector": record.sub_sector,
            "priority": record.priority,
            "notes": record.notes,
        }
        for record in records
    ]


def get_all_stocks() -> list[dict[str, str | int]]:
    """Return the full observation universe."""
    return _to_dicts(STOCK_POOL)


def get_stocks_by_sector(sector: str) -> list[dict[str, str | int]]:
    """Return stocks belonging to a specific sector."""
    return _to_dicts(record for record in STOCK_POOL if record.sector == sector)


def get_high_priority_stocks() -> list[dict[str, str | int]]:
    """Return high priority names for focused monitoring."""
    return _to_dicts(record for record in STOCK_POOL if record.priority == 1)
