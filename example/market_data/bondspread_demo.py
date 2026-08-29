#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BondSpreadCurve：two_curves（国债 + 政策债 BondCurve）→ zeroSpread，再 setBenchmark(YieldCurve)。

须走 C++ LiveStore / MRawMarketManager / JsonReader。
Python RawMarketDataManager.fromJson 无法构建 two_curves（返回 None）。

setBenchmarkCurve 参数类型是 MYieldCurve（不能传 MBondCurve）。

数据：excel/data/market_data/MCP_MARKET_DATA_20260827.json
运行：python example/market_data/bondspread_demo.py
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

    json_path = os.path.join(
        proj, "excel", "data", "market_data", "MCP_MARKET_DATA_20260827.json"
    ).replace("\\", "/")
    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1

    sp = store.getBondSpreadCurve("CNY_BOND_POLICY_SPREAD")
    if sp is None:
        print("getBondSpreadCurve failed:", store.lastError())
        return 1
    d = "2027/08/27"
    print(f"before setBenchmark  zeroSpread={sp.zeroSpread(d):.6f}  ZeroRate={sp.ZeroRate(d):.8f}")

    bump = store.getYieldCurve("CNYDEPO_BUMP")
    if bump is None:
        print("CNYDEPO_BUMP missing:", store.lastError())
        return 1
    sp.setBenchmarkCurve(bump)
    print(f"after  setBenchmark  zeroSpread={sp.zeroSpread(d):.6f}  ZeroRate={sp.ZeroRate(d):.8f}")
    print("BondSpreadCurve demo OK (Excel TC44; C++ LiveStore)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
