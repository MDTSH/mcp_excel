#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TRC LocalVol：LiveStore.getLocalVol("EURUSD_LOCALVOL") 读数。

数据：excel/data/market_data/MCP_MARKET_DATA_P2_LOCALVOL_20260810.json
运行：python example/market_data/localvol_demo.py

Excel TC41 再把该对象交给 McpStructuredDerivativeProduct（TrippleRangesCall）。
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
    from mcp.wrapper import McpLocalVol

    json_path = os.path.join(
        proj, "excel", "data", "market_data", "MCP_MARKET_DATA_P2_LOCALVOL_20260810.json"
    ).replace("\\", "/")

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    lv = store.getLocalVol("EURUSD_LOCALVOL")
    if lv is None:
        print("getLocalVol EURUSD_LOCALVOL failed:", store.lastError())
        return 1
    spot = lv.GetSpot()
    sig = lv.GetVolatility(1.1553, "2026/11/09")
    print(f"EURUSD_LOCALVOL GetSpot={spot:.6f}  GetVolatility(1.1553,2026/11/09)={sig:.6f}")

    yc = store.getYieldCurve("CNYDEPO")
    if yc is None:
        print("CNYDEPO missing")
        return 1
    print(f"CNYDEPO ZeroRate @ 2026/11/12: {yc.ZeroRate('2026/11/12'):.6f}")

    fxv = store.getFXVolSurface("USDCNY_RVOL_BGN")
    if fxv is None:
        print("USDCNY_RVOL_BGN missing (fallback skip)")
    else:
        lv2 = McpLocalVol(fxv, 4, 6, "", 3, True)
        print(
            "McpLocalVol from FXVolSurface USDCNY_RVOL_BGN:",
            f"spot={lv2.GetSpot():.6f}",
            f"vol@6.85={lv2.GetVolatility(6.85, '2026/11/10'):.6f}",
        )

    print("LocalVol demo OK (SDP 定价见 Excel TC41)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
