#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LiveStore patch DoD 示例：applyUpdate 后 ZeroRate 变化与 Impact 列表。

数据：
  excel/data/market_data/MCP_MARKET_DATA_20260810.json
  excel/data/market_data/MCP_PATCH_CNHDEPO.json
运行：python example/market_data/patch_dod_demo.py
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


def _to_str_list(obj) -> list:
    if obj is None:
        return []
    try:
        return [str(obj[i]) for i in range(len(obj))]
    except Exception:
        pass
    try:
        return list(obj)
    except Exception:
        return [str(obj)]


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260810.json").replace("\\", "/")
    patch_path = os.path.join(md_dir, "MCP_PATCH_CNHDEPO.json")
    rate_date = "2026/08/10"

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    yc2 = store.getYieldCurve2("CNHDEPO_2")
    z_before = yc2.ZeroRate(rate_date, "MID")
    print(f"Before patch ZeroRate MID: {z_before:.6f}")

    if not store.applyUpdate(patch_path):
        print("applyUpdate failed:", store.lastError())
        return 1

    yc2_after = store.getYieldCurve2("CNHDEPO_2")
    z_after = yc2_after.ZeroRate(rate_date, "MID")
    print(f"After patch  ZeroRate MID: {z_after:.6f}")
    print(f"Delta (bp): {(z_after - z_before) * 10000:.2f}")

    updated = _to_str_list(store.getLastUpdateImpactUpdatedIds())
    affected = _to_str_list(store.getLastUpdateImpactAffectedIds())
    print("Updated ids:", updated)
    print("Affected ids:", affected)

    if abs(z_after - z_before) < 1e-8:
        print("Expected ZeroRate change after patch")
        return 1

    print("Patch DoD demo OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
