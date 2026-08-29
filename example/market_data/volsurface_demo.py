#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
非 FX VolSurface：小网格 JSON → LiveStore / C++ RawMD → GetVolatility。

数据：excel/data/market_data/MCP_MARKET_DATA_20260827.json
运行：python example/market_data/volsurface_demo.py
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


def _print_vs(label, vs, err=""):
    if vs is None:
        print(f"{label}: None  {err}")
        return False
    vol = vs.GetVolatility(100.0, "2026/09/28", 0.0)
    print(f"{label}: GetVolatility(100, 2026/09/28)={vol:.6f}")
    return True


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260827.json").replace("\\", "/")
    root = md_dir.replace("\\", "/")
    cid = "EQ_VOL_SAMPLE"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1
    ok = _print_vs("LiveStore", store.getVolSurface(cid), store.lastError())

    mgr = mcp.MRawMarketManager(root)
    ok = _print_vs("C++ RawMD", mgr.getVolSurface(cid, "2026-08-27")) and ok

    if not ok:
        print("VolSurface demo incomplete")
        return 1
    print("VolSurface demo OK (Excel TC46)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
