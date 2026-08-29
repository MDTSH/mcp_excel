# -*- coding: utf-8 -*-
"""
Raw Market Data 集成模块

从 MCP_MARKET_DATA_YYYYMMDD.json 格式加载市场数据，供 Python/Excel 使用。
格式规范见：mcp-valuation-engine/docs/RAW_MARKET_DATA_JSON_DESIGN.md

继承与测试参考：
- mcp-valuation-engine/docs/guide/NEW_ASSET_CHECKLIST.md 十一-A、十一-B
- mcp-valuation-engine/docs/guide/EXCEL_INTEGRATION_PITFALLS.md 五
"""

from .raw_market_data_loader import RawMarketDataIndex, RawMarketDataLoader, RawMarketDataManager

__all__ = [
    "RawMarketDataIndex",
    "RawMarketDataLoader",
    "RawMarketDataManager",
]
