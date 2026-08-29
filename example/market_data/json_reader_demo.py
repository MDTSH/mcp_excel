#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JsonReader 只读示例：单文件加载，不支持 patch。

数据：excel/data/market_data/MCP_MARKET_DATA_20260810.json
运行：python example/market_data/json_reader_demo.py
"""

from __future__ import annotations

import os
import sys


def _setup_paths() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    proj = os.path.normpath(os.path.join(here, "..", ".."))
    lib = os.path.join(proj, "lib", "X64")
    for p in (proj, lib):
        if p not in sys.path:
            sys.path.insert(0, p)
    return proj


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    json_path = os.path.join(
        proj, "excel", "data", "market_data", "MCP_MARKET_DATA_20260810.json"
    ).replace("\\", "/")
    rate_date = "2026/08/10"

    reader = mcp.MMarketDataJsonReader()
    if not reader.loadFromFile(json_path):
        print("loadFromFile failed:", reader.lastError())
        return 1

    yc2 = reader.getYieldCurve2("CNHDEPO_2")
    if yc2 is None:
        print("CNHDEPO_2 not found")
        return 1
    z = yc2.ZeroRate(rate_date, "MID")
    print(f"JsonReader CNHDEPO_2 ZeroRate MID: {z:.6f}")

    fx = reader.getFXForwardPointsCurve2("USDCNH_FXFP_BGN_2")
    if fx is None:
        print("USDCNH_FXFP_BGN_2 not found")
        return 1
    print(f"JsonReader USDCNH spot MID: {fx.FXSpotRate('MID'):.4f}")

    vol = reader.getFXVolSurface2("USDCNH_RVOL_BGN_2")
    if vol is None:
        print("USDCNH_RVOL_BGN_2 not found")
        return 1
    print("JsonReader FXVolSurface2 loaded OK")

    print("JsonReader demo OK (read-only, no patch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
