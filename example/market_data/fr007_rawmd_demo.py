#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FR007 SwapCurve RawMD 示例：CNY_SWAP_FR007_BGN。

JSON 为 CalibrationSet（非 fromJson 序列化）。Python RawMarketDataManager.fromJson
无法 bootstrap，须走 C++ MRawMarketManager（与 Excel rawmdGetSwapCurve 相同）。

数据：excel/data/market_data/MCP_MARKET_DATA_20260626.json
运行：python example/market_data/fr007_rawmd_demo.py
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

    root = os.path.join(proj, "excel", "data", "market_data").replace("\\", "/")
    mgr = mcp.MRawMarketManager(root)
    vd = "2026-06-26"
    sc = mgr.getSwapCurve("CNY_SWAP_FR007_BGN", vd)
    if sc is None:
        print("C++ MRawMarketManager.getSwapCurve returned None; try LiveStore")
        json_path = os.path.join(root, "MCP_MARKET_DATA_20260626.json")
        store = mcp.MLiveMarketDataStore()
        if not store.loadSnapshot(json_path):
            print("loadSnapshot failed:", store.lastError())
            return 1
        sc = store.getSwapCurve("CNY_SWAP_FR007_BGN")
    if sc is None:
        print("CNY_SWAP_FR007_BGN not found for", vd)
        return 1

    for d in ("2026/07/03", "2026/09/28", "2027/06/28"):
        z = sc.ZeroRate(d)
        df = sc.DiscountFactor(d)
        print(f"FR007 ZeroRate @ {d}: {z:.6f}  DF={df:.8f}")

    print("FR007 RawMD demo OK (C++ MRawMarketManager)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
