#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implied YieldCurve 示例：USDDEPO_IMPLIED（CNHDEPO + USDCNH_FXFP_BGN, IsCCY2=false）。

LiveStore 与 RawMD 两条入口对照。

数据：excel/data/market_data/MCP_MARKET_DATA_20260626.json
运行：python example/market_data/implied_yc_demo.py
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


def _zr(curve, d: str) -> float:
    inner = curve.getInstance() if hasattr(curve, "getInstance") else curve
    return inner.ZeroRate(d)


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp
    from excel.raw_market_data.raw_market_data_loader import RawMarketDataManager

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260626.json").replace("\\", "/")
    vd = "2026-06-26"
    rate_date = "2026/12/28"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    implied_ls = store.getYieldCurve("USDDEPO_IMPLIED")
    usd_ls = store.getYieldCurve("USDDEPO")
    if implied_ls is None or usd_ls is None:
        print("LiveStore implied/USDDEPO missing")
        return 1
    z_imp_ls = implied_ls.ZeroRate(rate_date)
    z_usd_ls = usd_ls.ZeroRate(rate_date)
    print(f"LiveStore USDDEPO_IMPLIED ZR @ {rate_date}: {z_imp_ls:.6f}")
    print(f"LiveStore USDDEPO          ZR @ {rate_date}: {z_usd_ls:.6f}")
    print(f"  Diff(bp): {(z_imp_ls - z_usd_ls) * 10000:.2f}")

    mgr = RawMarketDataManager(root=md_dir)
    implied_rm = mgr.get_yield_curve("USDDEPO_IMPLIED", vd)
    if implied_rm is None:
        print("RawMD USDDEPO_IMPLIED missing")
        return 1
    z_imp_rm = _zr(implied_rm, rate_date)
    print(f"RawMD    USDDEPO_IMPLIED ZR @ {rate_date}: {z_imp_rm:.6f}")
    print(f"  LiveStore vs RawMD (bp): {(z_imp_ls - z_imp_rm) * 10000:.2f}")

    print("Implied YC demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
