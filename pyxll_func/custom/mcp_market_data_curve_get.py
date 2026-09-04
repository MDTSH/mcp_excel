# -*- coding: utf-8 -*-
"""
LiveStore / JsonReader 取曲线对象（返回 Mcp*@n），与 rawmd 的 _wrap_mcp_if_needed 一致。

供 mcp_market_data_live.py 与 mcp_raw_market_data.py（rawmdGet* 别名）复用。
"""

from __future__ import absolute_import

from typing import Any, Optional, Tuple

try:
    from pyxll_func.custom.mcp_raw_market_data import _wrap_mcp_if_needed
except ImportError:
    from mcp_raw_market_data import _wrap_mcp_if_needed

try:
    from mcp.wrapper import (
        McpYieldCurve,
        McpYieldCurve2,
        McpFXForwardPointsCurve2,
        McpFXVolSurface2,
        McpFXForwardPointsCurve,
        McpFXVolSurface,
        McpSwapCurve,
        McpBondCurve,
        McpBondSpreadCurve,
        McpCreditCurve,
        McpForwardCurve,
        McpLocalVol,
        McpVolSurface,
    )
except ImportError:
    McpYieldCurve = McpYieldCurve2 = None
    McpFXForwardPointsCurve2 = McpFXVolSurface2 = None
    McpFXForwardPointsCurve = McpFXVolSurface = None
    McpSwapCurve = McpBondCurve = None
    McpBondSpreadCurve = McpCreditCurve = None
    McpForwardCurve = None
    McpLocalVol = None
    McpVolSurface = None

# (store/reader 上的 getter 名, Mcp 包装类, UDF 标签)
_LIVE_CURVE_SPECS = {
    "YieldCurve": ("getYieldCurve", McpYieldCurve),
    "YieldCurve2": ("getYieldCurve2", McpYieldCurve2),
    "SwapCurve": ("getSwapCurve", McpSwapCurve),
    "BondCurve": ("getBondCurve", McpBondCurve),
    "CreditCurve": ("getCreditCurve", McpCreditCurve),
    "BondSpreadCurve": ("getBondSpreadCurve", McpBondSpreadCurve),
    "FXForwardPointsCurve": ("getFXForwardPointsCurve", McpFXForwardPointsCurve),
    "FXForwardPointsCurve2": ("getFXForwardPointsCurve2", McpFXForwardPointsCurve2),
    "ForwardCurve": ("getForwardCurve", McpForwardCurve),
    "FXVolSurface": ("getFXVolSurface", McpFXVolSurface),
    "FXVolSurface2": ("getFXVolSurface2", McpFXVolSurface2),
    "VolSurface": ("getVolSurface", McpVolSurface),
    "LocalVol": ("getLocalVol", McpLocalVol),
}


def _unwrap_mcp_source(source) -> Any:
    if source is None:
        return None
    if hasattr(source, "getInstance"):
        return source.getInstance()
    return source


def market_data_source_get_curve(
    source,
    curve_id: str,
    curve_kind: str,
    udf_prefix: str = "mdlsGet",
) -> Any:
    """
    从 MLiveMarketDataStore / MMarketDataJsonReader 取曲线并包装为 Mcp* 对象。
    成功返回 Excel 对象句柄（如 McpYieldCurve2@0）；失败返回错误字符串。
    """
    spec = _LIVE_CURVE_SPECS.get(curve_kind)
    if spec is None:
        return f"{udf_prefix}{curve_kind}: unknown curve_kind"
    getter_name, wrapper_cls = spec
    label = f"{udf_prefix}{curve_kind}"

    inner = _unwrap_mcp_source(source)
    if inner is None:
        return f"{label}: source is empty"

    cid = (curve_id or "").strip()
    if not cid:
        return f"{label}: curve_id is empty"

    fn = getattr(inner, getter_name, None)
    if not callable(fn):
        return f"{label}: {getter_name} not available on _mcp.pyd"

    try:
        # SwapCurve NewtonGlobal / CreditCurve 校准偶发失败：多试几次
        attempts = 3 if curve_kind in ("SwapCurve", "CreditCurve") else 1
        curve = None
        last_exc = None
        for _ in range(attempts):
            try:
                curve = fn(cid)
                if curve is not None:
                    break
            except Exception as e:
                last_exc = e
                curve = None
        if curve is None:
            if last_exc is not None:
                return f"{label} except: {last_exc}"
            hint = ""
            if curve_kind == "SwapCurve":
                hint = (
                    " — SwapCurve bootstrap may have failed earlier in this Excel process; "
                    "recalc Store (or restart Excel) and retry"
                )
            return f"Curve not found: {cid} ({curve_kind}){hint}"
        return _wrap_mcp_if_needed(curve, wrapper_cls, label)
    except Exception as e:
        return f"{label} except: {e}"


def market_data_source_get_curve_by_section(
    source,
    section: str,
    curve_id: str,
    udf_prefix: str = "mdlsGet",
) -> Any:
    """按 Impact 的 section 名（JSON 节）取 Mcp* 对象，如 YieldCurve2 + CNHDEPO_2。"""
    sec = (section or "").strip()
    if not sec:
        return f"{udf_prefix}BySection: section is empty"
    return market_data_source_get_curve(source, curve_id, sec, udf_prefix)
