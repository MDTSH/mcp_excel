#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LiveStore 示例：loadSnapshot → getYieldCurve2 / FXFP2 / FXVol2 → 读数。

数据：excel/data/market_data/MCP_MARKET_DATA_20260810.json
运行：python example/market_data/livestore_demo.py
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

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260810.json").replace("\\", "/")
    rate_date = "2026/08/10"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    yc2 = store.getYieldCurve2("CNHDEPO_2")
    if yc2 is None:
        print("CNHDEPO_2 not found")
        return 1
    z = yc2.ZeroRate(rate_date, "MID")
    df = yc2.DiscountFactor(rate_date, "MID")
    print(f"CNHDEPO_2 ZeroRate MID @ {rate_date}: {z:.6f}")
    print(f"CNHDEPO_2 DiscountFactor MID: {df:.6f}")

    fx = store.getFXForwardPointsCurve2("USDCNH_FXFP_BGN_2")
    if fx is None:
        print("USDCNH_FXFP_BGN_2 not found")
        return 1
    spot = fx.FXSpotRate("MID")
    print(f"USDCNH spot MID: {spot:.4f}")

    vol = store.getFXVolSurface2("USDCNH_RVOL_BGN_2")
    if vol is None:
        print("USDCNH_RVOL_BGN_2 not found")
        return 1
    print("USDCNH_RVOL_BGN_2 loaded OK")

    print("LiveStore demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
