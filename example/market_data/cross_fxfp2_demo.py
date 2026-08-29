#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cross FXFP2 示例：LiveStore 加载 CNHTHB_FXFP_CROSS_2（JSON 无 Tenors，由 Leg1/Leg2 合成）。

注意：Python RawMarketDataManager.get_fx_forward_points_curve2 无法构建 Cross2；
须用 LiveStore / C++ Manager。

数据：excel/data/market_data/MCP_MARKET_DATA_20260626.json
运行：python example/market_data/cross_fxfp2_demo.py
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
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260626.json").replace("\\", "/")
    rate_date = "2026/07/27"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    for cid in ("USDCNH_FXFP_BGN_2", "USDTHB_FXFP_BGN_2", "CNHTHB_FXFP_CROSS_2"):
        fx = store.getFXForwardPointsCurve2(cid)
        if fx is None:
            print(cid, "not found")
            return 1
        spot = fx.FXSpotRate("MID")
        outright = fx.FXForwardOutright(rate_date, "MID")
        print(f"{cid} spot MID={spot:.6f}  outright@ {rate_date}={outright:.6f}")

    yc2 = store.getYieldCurve2("CNHDEPO_2")
    if yc2 is None:
        print("CNHDEPO_2 not found")
        return 1
    print(f"CNHDEPO_2 ZeroRate MID @ 2026/06/26: {yc2.ZeroRate('2026/06/26', 'MID'):.6f}")

    print("Cross FXFP2 demo OK (LiveStore)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
