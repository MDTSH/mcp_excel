#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CreditCurve：JSON → LiveStore / C++ RawMD / JsonReader → HazardRate / DefaultProbability。

Python RawMarketDataManager 也能构建，但数值以 C++ Manager / LiveStore 为准。

数据：excel/data/market_data/MCP_MARKET_DATA_20260827.json
运行：python example/market_data/creditcurve_demo.py
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


def _print_cc(label, cc, err=""):
    if cc is None:
        print(f"{label}: None  {err}")
        return False
    hr = cc.HazardRate("2027/08/27")
    pd = cc.DefaultProbability("2027/08/27")
    print(f"{label}: HazardRate(1Y)={hr:.8f}  DefaultProbability(1Y)={pd:.8f}")
    return True


def _retry_get(fn, n=3):
    last = None
    for _ in range(n):
        last = fn()
        if last is not None:
            return last
    return last


def main() -> int:
    proj = _setup_paths()
    import mcp.mcp as mcp

    md_dir = os.path.join(proj, "excel", "data", "market_data")
    json_path = os.path.join(md_dir, "MCP_MARKET_DATA_20260827.json").replace("\\", "/")
    root = md_dir.replace("\\", "/")
    vd = "2026-08-27"
    cid = "CNY_CREDIT_CFETS"

    from excel.raw_market_data.raw_market_data_loader import RawMarketDataManager

    # Python 结构化构建较稳；先跑通再对照 C++（C++ 校准偶发 unknown exception）
    py_mgr = RawMarketDataManager(root=root)
    py_cc = py_mgr.get_credit_curve(cid, vd)
    if py_cc is None:
        print("Python RawMD last_error:", py_mgr._loader.get_last_error())
    py_ok = _print_cc("Python RawMD", py_cc)

    store = mcp.MLiveMarketDataStore()
    if not store.loadSnapshot(json_path):
        print("loadSnapshot failed:", store.lastError())
        return 1 if not py_ok else 0
    store.getYieldCurve("CNYDEPO")  # 预热日历
    cpp_ok = _print_cc(
        "LiveStore",
        _retry_get(lambda: store.getCreditCurve(cid)),
        store.lastError(),
    )

    reader = mcp.MMarketDataJsonReader()
    if reader.loadFromFile(json_path):
        cpp_ok = _print_cc(
            "JsonReader",
            _retry_get(lambda: reader.getCreditCurve(cid)),
            reader.lastError(),
        ) or cpp_ok

    mgr = mcp.MRawMarketManager(root)
    cpp_ok = _print_cc(
        "C++ RawMD",
        _retry_get(lambda: mgr.getCreditCurve(cid, vd)),
        getattr(mgr, "lastError", lambda: "")(),
    ) or cpp_ok

    if py_ok:
        if not cpp_ok:
            print("CreditCurve demo OK via Python RawMD (C++ 校准偶发失败；Excel rawmdGet 会重试并兜底)")
        else:
            print("CreditCurve demo OK (Excel TC43)")
        return 0
    print("CreditCurve demo incomplete")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
