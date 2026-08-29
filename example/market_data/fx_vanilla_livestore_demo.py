#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FX Vanilla LiveStore：loadSnapshot → getFXVolSurface2 → MVanillaOption。

数据：excel/data/market_data/MCP_MARKET_DATA_20260810.json（P0，USDCNH_RVOL_BGN_2）
运行：python example/market_data/fx_vanilla_livestore_demo.py
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

    json_path = os.path.join(proj, "excel", "data", "market_data", "MCP_MARKET_DATA_20260810.json")
    json_path = json_path.replace("\\", "/")

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    vol2 = store.getFXVolSurface2("USDCNH_RVOL_BGN_2")
    if vol2 is None:
        print("USDCNH_RVOL_BGN_2 not found:", store.lastError())
        return 1

    # CallPut=1, Side=Client(-1), BuySell=Buy(1) — 与 Excel VoType=10 同一曲面对象
    opt = mcp.MVanillaOption(
        1, "2026/08/10", "2026/11/10", "2026/11/12", 6.85, vol2, -1, 1, "2026/08/10"
    )
    spot = opt.GetSpot()
    vol = opt.GetVol()
    pv = opt.PV(True)
    price = opt.Price(True)
    print(f"USD/CNH Call strike=6.85  Spot={spot:.6f}  Vol={vol:.6f}")
    print(f"Price={price:.8f}  PV={pv:.8f}")
    print("FX Vanilla LiveStore demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
