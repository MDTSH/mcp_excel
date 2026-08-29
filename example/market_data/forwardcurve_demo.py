#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
非 FX ForwardCurve：JSON → LiveStore / C++ RawMD → ForwardRate。

数据：excel/data/market_data/MCP_MARKET_DATA_20260827.json
运行：python example/market_data/forwardcurve_demo.py
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


def _print_fwd(label, fc, err=""):
    if fc is None:
        print(f"{label}: None  {err}")
        return False
    print(f"{label}: ForwardRate(2026/09/28)={fc.ForwardRate('2026/09/28'):.4f}")
    return True


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260827.json").replace("\\", "/")
    root = md_dir.replace("\\", "/")
    cid = "EQ_FORWARD"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1
    ok = _print_fwd("LiveStore", store.getForwardCurve(cid), store.lastError())

    mgr = mcp.MRawMarketManager(root)
    ok = _print_fwd("C++ RawMD", mgr.getForwardCurve(cid, "2026-08-27")) and ok

    if not ok:
        print("ForwardCurve demo incomplete")
        return 1
    print("ForwardCurve demo OK (Excel TC45)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
