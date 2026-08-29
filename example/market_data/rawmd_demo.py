#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RawMD 目录管理器示例：按估值日从 MCP_MARKET_DATA_YYYYMMDD.json 取曲线对象。

数据根目录：excel/data/market_data/
运行：python example/market_data/rawmd_demo.py
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
    from excel.raw_market_data.raw_market_data_loader import RawMarketDataManager

    root = os.path.join(proj, "excel", "data", "market_data")
    mgr = RawMarketDataManager(root=root)

    dates = mgr.get_available_dates()
    if not dates:
        print("no snapshot dates under", root)
        return 1
    print("available dates:", dates)

    vd = None
    yc2 = None
    for candidate in reversed(dates):
        got = mgr.get_yield_curve2("CNHDEPO_2", candidate)
        if got is not None:
            vd, yc2 = candidate, got
            break
    if yc2 is None:
        print("CNHDEPO_2 not found on any snapshot date")
        return 1

    inner = yc2.getInstance() if hasattr(yc2, "getInstance") else yc2
    zr_date = vd.replace("-", "/")
    z = inner.ZeroRate(zr_date, "MID")
    print(f"CNHDEPO_2 ZeroRate MID ({vd}): {z:.6f}")

    fx = mgr.get_fx_forward_points_curve2("USDCNH_FXFP_BGN_2", vd)
    if fx is None:
        print("USDCNH_FXFP_BGN_2 not found")
        return 1
    fx_inner = fx.getInstance() if hasattr(fx, "getInstance") else fx
    print(f"USDCNH spot MID: {fx_inner.FXSpotRate('MID'):.4f}")

    print("RawMD demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
