#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HistVol from CSV：price_data_index + HIST CSV → getHistVolFromPriceData → GetVol。

数据：
  excel/data/market_data/MCP_MARKET_DATA_20260810.json
  excel/data/market_data/FX_SPOT_PRICES_HIST.csv
运行：python example/market_data/histvol_csv_demo.py
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


def _print_hv(label, hv, err=""):
    if hv is None:
        print(f"{label}: None  {err}")
        return False
    sig = hv.GetVol("2026/08/10", 60)
    print(f"{label}: GetVol(2026/08/10,60)={sig:.8f}")
    return True


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260810.json").replace("\\", "/")
    root = md_dir.replace("\\", "/")

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1
    ok = True
    for code in ("USDCNH", "EURUSD"):
        hv = store.getHistVolFromPriceData("FXSPOT", code, "2026-08-10", 60, "EWMA")
        if not _print_hv(f"LiveStore {code}", hv, store.lastError()):
            ok = False

    mgr = mcp.MRawMarketManager(root)
    for code in ("USDCNH", "EURUSD"):
        hv = mgr.getHistVolFromPriceData("FXSPOT", code, "2026-08-10", 60, "EWMA")
        if not _print_hv(f"RawMD {code}", hv, mgr.lastError() if hasattr(mgr, "lastError") else ""):
            ok = False

    if not ok:
        print("HistVol demo incomplete")
        return 1
    print("HistVol from CSV demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
