# -*- coding: utf-8 -*-
"""
MCP 单文件 JSON / LiveMarketDataStore Excel UDF

设计原则（与 rawmd 目录模式一致）：
  1) McpLiveMarketDataStore(路径) → Store 对象句柄
  2) mdlsGetYieldCurve2(Store, curve_id) → McpYieldCurve2@n 对象
  3) 零息/折现/即期/波动率等用 curve.py / volatility.py 已有 UDF 对 **对象** 计算
     例如 =YieldCurve2ZeroRate(C5, 日期, "MID")

PyXLL：pyxll.cfg [modules] 增加 mcp_market_data_live

与 rawmd 对称命名：rawmdGetYieldCurve2(Manager, id, 估值日) ↔ mdlsGetYieldCurve2(Store, id)
"""

from __future__ import absolute_import

import glob
import logging
import os
import re
from typing import List, Tuple

from pyxll import xl_arg, xl_func, xl_return

try:
    from mcp.wrapper import McpLiveMarketDataStore as McpLiveStoreWrapper
    from mcp.wrapper import McpMarketDataJsonReader as McpJsonReaderWrapper
    import mcp.mcp as _mcp

    _has_mcp = True
except ImportError:
    _mcp = None
    McpLiveStoreWrapper = None
    McpJsonReaderWrapper = None
    _has_mcp = False

from pyxll_func.custom.mcp_market_data_curve_get import (
    market_data_source_get_curve,
    market_data_source_get_curve_by_section,
)
from pyxll_func.custom.mcp_raw_market_data import (
    _coerce_swig_string_vector_to_str_list,
    rawmdHistVolFromPriceData,
)
from mcp.utils.workbook_path import get_active_workbook_dir, resolve_data_path

_log = logging.getLogger(__name__)

_DEFAULT_SNAPSHOT_DIR = (
    r"E:\work\mcp\mathema-git\mcp-valuation-engine\market_data\snapshots_fx"
)
_DEFAULT_BASELINE = os.path.join(
    _DEFAULT_SNAPSHOT_DIR, "MCP_MARKET_DATA_20260311.json"
)

# Excel 全量重算会反复求值 McpLiveMarketDataStore；同路径+mtime 复用，避免
# 多次 loadSnapshot 打乱进程级 SwapCurve 缓存（表现为仅第一条曲线成功）。
_LIVE_STORE_CACHE = {}  # path -> (mtime, wrapper)


def _ensure_path() -> None:
    import sys

    here = os.path.dirname(os.path.abspath(__file__))
    proj = os.path.normpath(os.path.join(here, "..", ".."))
    lib_x64 = os.path.join(proj, "lib", "X64")
    for p in (proj, lib_x64):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def _unwrap_store(store):
    if store is None:
        return None
    if hasattr(store, "getInstance"):
        return store.getInstance()
    return store


def _swig_string_list(obj) -> List[str]:
    return _coerce_swig_string_vector_to_str_list(obj)


def _excel_cell_str(v) -> str:
    """PyXLL 动态数组：None 会变成 #N/A，统一为字符串。"""
    if v is None:
        return ""
    if isinstance(v, float) and v != v:
        return ""
    return str(v)


def _impact_rows_for_excel_spill(rows: List[List[str]]) -> List[List[str]]:
    """
    PyXLL auto_resize 横向铺表：需返回「每列一列向量」，而非行优先矩阵。
    与 PortMetrics(HL) / _transpose_flattened_data 一致；行优先时 Excel 常只显示 [0][0]=kind。
    """
    if not rows or len(rows) <= 1:
        return rows
    header = rows[0]
    data_rows = rows[1:]
    ncol = len(header)
    out = []
    for col_idx in range(ncol):
        col = [_excel_cell_str(header[col_idx])]
        for row in data_rows:
            col.append(
                _excel_cell_str(row[col_idx]) if col_idx < len(row) else ""
            )
        out.append(col)
    return out


# Impact 的 section（与 C++ curveTypeToString）→ Excel 包装类名，勿在溢出公式里再 get 曲线
_SECTION_TO_MCP_TYPE = {
    "YieldCurve": "McpYieldCurve",
    "YieldCurve2": "McpYieldCurve2",
    "SwapCurve": "McpSwapCurve",
    "BondCurve": "McpBondCurve",
    "FXForwardPointsCurve": "McpFXForwardPointsCurve",
    "FXForwardPointsCurve2": "McpFXForwardPointsCurve2",
    "FXVolSurface": "McpFXVolSurface",
    "FXVolSurface2": "McpFXVolSurface2",
}


def _resolve_snapshot_path(path_or_dir: str) -> Tuple[bool, str, str]:
    p = (path_or_dir or "").strip()
    if not p:
        wb_dir = get_active_workbook_dir()
        if wb_dir:
            data_dir = os.path.join(wb_dir, "data")
            if os.path.isdir(data_dir):
                files = glob.glob(os.path.join(data_dir, "MCP_MARKET_DATA_*.json"))
                if files:
                    files.sort(key=lambda x: os.path.basename(x), reverse=True)
                    return True, os.path.normpath(files[0]), ""
        if os.path.isfile(_DEFAULT_BASELINE):
            return True, _DEFAULT_BASELINE, ""
        p = _DEFAULT_SNAPSHOT_DIR

    ok, resolved, err = resolve_data_path(p, must_exist=True, allow_dir=True)
    if not ok:
        return False, "", err

    if os.path.isfile(resolved):
        if not resolved.lower().endswith(".json"):
            return False, "", "Not a JSON file: %s" % resolved
        return True, resolved, ""

    if os.path.isdir(resolved):
        files = glob.glob(os.path.join(resolved, "MCP_MARKET_DATA_*.json"))
        if not files:
            return False, "", "No MCP_MARKET_DATA_*.json under: %s" % resolved
        files.sort(key=lambda x: os.path.basename(x), reverse=True)
        return True, os.path.normpath(files[0]), ""

    return False, "", "Path not found: %s" % p


def _resolve_json_file(path: str) -> Tuple[bool, str, str]:
    p = (path or "").strip()
    if not p:
        ok, resolved, err = _resolve_snapshot_path("")
        return ok, resolved, err
    ok, resolved, err = resolve_data_path(p, must_exist=True, allow_dir=False)
    if not ok:
        return False, "", err
    if not resolved.lower().endswith(".json"):
        return False, "", "Not a JSON file: %s" % resolved
    return True, resolved, ""


@xl_func(macro=True, recalc_on_open=False)
def McpWorkbookDir():
    """Return the directory of the calling workbook (GET.DOCUMENT 2 / xlfGetDocument)."""
    return get_active_workbook_dir() or "(workbook path unavailable)"


@xl_func(macro=True, recalc_on_open=False)
@xl_arg("relative_or_absolute_path", "str", "相对工作簿目录或绝对路径")
def McpResolvePath(relative_or_absolute_path: str = ""):
    """Resolve a data/yaml/json path against the calling workbook directory."""
    ok, resolved, err = resolve_data_path(relative_or_absolute_path, must_exist=True)
    if ok:
        return resolved
    return err


def _mdls_get(store, curve_id: str, curve_kind: str):
    return market_data_source_get_curve(store, curve_id, curve_kind, "mdlsGet")


def _mdjson_get(reader, curve_id: str, curve_kind: str):
    return market_data_source_get_curve(reader, curve_id, curve_kind, "mdjsonGet")


# ========== LiveStore ==========


def _prewarm_swap_curves(store) -> None:
    """预先构建常用 SwapCurve。

    USD_EFFR 必须尽早、带重试构建：它在 SOFR 等全局求解之后偶发失败，
    Excel 表现为首次打开 Curve not found、反复 F9 才恢复。
    """
    # 短端 EFFR 优先，降低被 SOFR NewtonGlobal 污染后的失败率
    ids = (
        "USD_EFFR",
        "CNY_SWAP",
        "CNY_SWAP_FR007_BGN",
        "CNY_LPR1Y",
        "USD_SOFR",
    )
    for cid in ids:
        ok = False
        for _attempt in range(5):
            try:
                cur = store.getSwapCurve(cid)
                if cur is not None:
                    ok = True
                    break
            except Exception as e:
                _log.debug("prewarm %s attempt failed: %s", cid, e)
        if not ok:
            _log.warning("prewarm SwapCurve failed after retries: %s", cid)


@xl_func(macro=True, recalc_on_open=False)
@xl_arg("snapshot_file_or_dir", "str", "快照 JSON 文件或含 MCP_MARKET_DATA_*.json 的目录")
def McpLiveMarketDataStore(snapshot_file_or_dir: str = ""):
    """
    加载全量 MCP 市场 JSON，返回 LiveStore 句柄（McpLiveMarketDataStore@n）。
    下游用 mdlsGetYieldCurve2 等取 Mcp* 曲线对象，再用 YieldCurve2ZeroRate 等读数。
    """
    if not _has_mcp:
        return "mcp.mcp not loaded"
    try:
        _ensure_path()
        ok, path, err = _resolve_snapshot_path(snapshot_file_or_dir)
        if not ok:
            return err
        path = os.path.normpath(path)
        # C++ parentPath 旧版只认 '/'；正斜杠可避免 Windows 把 base_path 判成 "."
        path_for_load = path.replace("\\", "/")
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = None
        cache_key = (path_for_load, 2)
        cached = _LIVE_STORE_CACHE.get(cache_key)
        if cached is not None and cached[0] == mtime and cached[1] is not None:
            return cached[1]

        inner = _mcp.MLiveMarketDataStore()
        if not inner.loadSnapshot(path_for_load):
            return f"loadSnapshot failed: {inner.lastError()}"
        _prewarm_swap_curves(inner)
        if McpLiveStoreWrapper is None:
            _LIVE_STORE_CACHE[cache_key] = (mtime, inner)
            return inner
        w = McpLiveStoreWrapper(inner)
        w._mdls_snapshot_path = path  # noqa: SLF001
        _LIVE_STORE_CACHE[cache_key] = (mtime, w)
        return w
    except Exception as e:
        _log.warning("McpLiveMarketDataStore: %s", e, exc_info=True)
        return f"McpLiveMarketDataStore except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore 返回值")
def mdlsLastError(store):
    s = _unwrap_store(store)
    if s is None:
        return "store is empty"
    try:
        return s.lastError() or ""
    except Exception as e:
        return str(e)


@xl_func(macro=True, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("patch_file", "str", "增量 patch JSON 文件路径")
def mdlsApplyUpdateFile(store, patch_file: str):
    """
    对 Store 原地 applyUpdate，返回同一 Store 句柄。
    Excel：patch 后的 mdlsGet* / mdlsLastUpdateImpact 应引用**本函数所在单元格**（如 $B$14），
    不要只引用初始 $B$3，否则依赖图可能先算读数、后 patch，导致 patch 后数值不变。
    """
    s = _unwrap_store(store)
    if s is None:
        return "mdlsApplyUpdateFile: store is empty"
    p = (patch_file or "").strip()
    if p:
        ok, resolved, err = resolve_data_path(p, must_exist=True)
        p = resolved if ok else p
        if not ok:
            return err or f"patch file not found: {p}"
    if not p or not os.path.isfile(p):
        return f"patch file not found: {p}"
    try:
        if not s.applyUpdate(p):
            return f"applyUpdate failed: {s.lastError()}"
        return store
    except Exception as e:
        return f"mdlsApplyUpdateFile except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("patch_json", "str", "patch JSON 字符串")
def mdlsApplyUpdateJson(store, patch_json: str):
    s = _unwrap_store(store)
    if s is None:
        return "mdlsApplyUpdateJson: store is empty"
    text = (patch_json or "").strip()
    if not text:
        return "patch_json is empty"
    try:
        if not hasattr(s, "applyUpdateFromString"):
            return "applyUpdateFromString not in _mcp.pyd"
        if not s.applyUpdateFromString(text):
            return f"applyUpdateFromString failed: {s.lastError()}"
        return store
    except Exception as e:
        return f"mdlsApplyUpdateJson except: {e}"


def _mdls_build_last_update_impact_rows(store, with_objects: bool):
    if store is None or isinstance(store, str):
        return [["mdlsLastUpdateImpact: store is empty"]]
    s = _unwrap_store(store)
    if s is None:
        return [["mdlsLastUpdateImpact: store is empty"]]
    upd_s = _coerce_swig_string_vector_to_str_list(
        s.getLastUpdateImpactUpdatedSections()
    )
    upd_i = _coerce_swig_string_vector_to_str_list(
        s.getLastUpdateImpactUpdatedIds()
    )
    aff_s = _coerce_swig_string_vector_to_str_list(
        s.getLastUpdateImpactAffectedSections()
    )
    aff_i = _coerce_swig_string_vector_to_str_list(
        s.getLastUpdateImpactAffectedIds()
    )
    header = ["kind", "section", "curve_id"]
    if with_objects:
        header.append("McpType")
    if not upd_i and not aff_i:
        row = ["(empty)", "", "尚未 applyUpdate"]
        if with_objects:
            row.append("")
        return [header, row]
    rows = [header]

    def _append(kind, sec, cid):
        row = [
            _excel_cell_str(kind),
            _excel_cell_str(sec),
            _excel_cell_str(cid),
        ]
        if with_objects:
            # 第 4 列仅类型名（取对象用 mdlsGetCurveBySection，勿在溢出 UDF 内嵌对象）
            row.append(
                _SECTION_TO_MCP_TYPE.get((sec or "").strip(), _excel_cell_str(sec))
            )
        rows.append(row)

    for i, cid in enumerate(upd_i):
        _append("updated", upd_s[i] if i < len(upd_s) else "", cid)
    for i, cid in enumerate(aff_i):
        _append("affected", aff_s[i] if i < len(aff_s) else "", cid)
    return rows


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_return("var[][]")
def mdlsLastUpdateImpact(store):
    """
    最近一次 applyUpdate 的影响表（溢出）：kind / section / curve_id。
    须引用已 patch 的 Store（如 =mdlsApplyUpdateFile(...) 所在单元格 $B$14）。
    """
    try:
        rows = _mdls_build_last_update_impact_rows(store, False)
        return _impact_rows_for_excel_spill(rows)
    except Exception as e:
        return [[f"mdlsLastUpdateImpact except: {e}"]]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_return("var[][]")
def mdlsLastUpdateImpactWithObjects(store):
    """影响表 + 第 4 列 Mcp 包装类名（列向量溢出，与 mdlsLastUpdateImpact 同布局）。"""
    try:
        rows = _mdls_build_last_update_impact_rows(store, True)
        return _impact_rows_for_excel_spill(rows)
    except Exception as e:
        return [[f"mdlsLastUpdateImpactWithObjects except: {e}"]]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_return("var[][]")
def mdlsLastPatchCurveIds(store):
    """最近一次 patch 直接写入的 curve_id 列表（单列溢出）。"""
    s = _unwrap_store(store)
    if s is None:
        return [["mdlsLastPatchCurveIds: store is empty"]]
    try:
        ids = _coerce_swig_string_vector_to_str_list(s.getLastPatchCurveIds())
        if not ids:
            return [["(empty)"]]
        return [[x] for x in ids]
    except Exception as e:
        return [[f"mdlsLastPatchCurveIds except: {e}"]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("section", "str", "JSON 节名，如 YieldCurve2 / FXVolSurface2")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetCurveBySection(store, section: str, curve_id: str):
    """按 Impact 行的 section + curve_id 取 Mcp* 对象。例：=mdlsGetCurveBySection($B$14,\"YieldCurve2\",\"CNHDEPO_2\")"""
    return market_data_source_get_curve_by_section(store, section, curve_id, "mdlsGet")


# ----- 取曲线对象（与 rawmdGet* 对称；读数请用 curve.py / volatility.py） -----


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetYieldCurve(store, curve_id: str):
    """返回 McpYieldCurve@n。示例：=YieldCurveZeroRate(mdlsGetYieldCurve($B$3,\"CNY_DEPO\"),日期,\"MID\")"""
    return _mdls_get(store, curve_id, "YieldCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 CNHDEPO_2")
def mdlsGetYieldCurve2(store, curve_id: str):
    """返回 McpYieldCurve2@n。示例：=YieldCurve2ZeroRate(mdlsGetYieldCurve2($B$3,\"CNHDEPO_2\"),$B$6,\"MID\")"""
    return _mdls_get(store, curve_id, "YieldCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，对应 JSON 节 FXForwardPointsCurve")
def mdlsGetFXForwardPointsCurve(store, curve_id: str):
    """返回 McpFXForwardPointsCurve@n。示例：=FxfpcFXForwardPoints(mdlsGetFXForwardPointsCurve($B$3,\"USDCNH_FXFP_BGN\"),日期)"""
    return _mdls_get(store, curve_id, "FXForwardPointsCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetFXForwardPointsCurve2(store, curve_id: str):
    """返回 McpFXForwardPointsCurve2@n。示例：=Fxfpc2FXSpotRate(mdlsGetFXForwardPointsCurve2(...),...,\"MID\")"""
    return _mdls_get(store, curve_id, "FXForwardPointsCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetFXVolSurface2(store, curve_id: str):
    """返回 McpFXVolSurface2@n。示例：=FXVolSurface2GetVolatility(曲面, \"25C\", 到期日, \"MID\")"""
    return _mdls_get(store, curve_id, "FXVolSurface2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 SCM_LOCALVOL")
def mdlsGetLocalVol(store, curve_id: str):
    """返回 McpLocalVol@n。示例：=LocalVolGetCalendar(mdlsGetLocalVol($B$3,\"SCM_LOCALVOL\"))"""
    return _mdls_get(store, curve_id, "LocalVol")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetSwapCurve(store, curve_id: str):
    return _mdls_get(store, curve_id, "SwapCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID")
def mdlsGetBondCurve(store, curve_id: str):
    return _mdls_get(store, curve_id, "BondCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 CNY_CREDIT_CFETS")
def mdlsGetCreditCurve(store, curve_id: str):
    """返回 McpCreditCurve@n。读数：CreditCurveHazardRate / CreditCurveDefaultProbability。"""
    return _mdls_get(store, curve_id, "CreditCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 CNY_BOND_POLICY_SPREAD")
def mdlsGetBondSpreadCurve(store, curve_id: str):
    """返回 McpBondSpreadCurve@n。读数：BondSpreadCurveZeroSpread；基准冲击：rawmdBondSpreadSetBenchmark。"""
    return _mdls_get(store, curve_id, "BondSpreadCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 EQ_FORWARD")
def mdlsGetForwardCurve(store, curve_id: str):
    """返回 McpForwardCurve@n（非 FX）。读数：ForwardCurveForwardRate。"""
    return _mdls_get(store, curve_id, "ForwardCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "曲线 ID，如 EQ_VOL_SAMPLE")
def mdlsGetVolSurface(store, curve_id: str):
    """返回 McpVolSurface@n（非 FX）。读数：VolSurfaceGetVolatility。"""
    return _mdls_get(store, curve_id, "VolSurface")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "object", "McpLiveMarketDataStore")
@xl_arg("product_type", "str", "price_data_index 节名，如 FXSPOT / EQUITYSPOT")
@xl_arg("instrument_code", "str", "标的代码，如 EURUSD / 600000.SH")
@xl_arg("valuation_date", "var", "可选；空则用快照日")
@xl_arg("sample_num", "int", "窗口长度，默认 252")
@xl_arg("model", "str", "CLOSE_TO_CLOSE / EWMA / LINXIAO / RISKMETRICS，默认 EWMA")
def mdlsHistVolFromPriceData(
    store,
    product_type: str,
    instrument_code: str,
    valuation_date=None,
    sample_num=252,
    model="EWMA",
):
    """从 HIST CSV 动态构建 McpHistVols，无需 JSON HistVol 节点。读数：HvsGetVol(对象, 日期, sampleNum)。"""
    return rawmdHistVolFromPriceData(
        store, product_type, instrument_code, valuation_date, sample_num, model
    )


# ========== JsonReader（只读，同样先取对象再读数） ==========


@xl_func(macro=True, recalc_on_open=True)
@xl_arg("json_file", "str", "MCP_MARKET_DATA JSON 文件")
def McpMarketDataJsonReader(json_file: str = ""):
    if not _has_mcp:
        return "mcp.mcp not loaded"
    try:
        _ensure_path()
        ok, path, err = _resolve_json_file(json_file)
        if not ok:
            return err
        inner = _mcp.MMarketDataJsonReader()
        if not inner.loadFromFile(path):
            return f"loadFromFile failed: {inner.lastError()}"
        return McpJsonReaderWrapper(inner) if McpJsonReaderWrapper else inner
    except Exception as e:
        return f"McpMarketDataJsonReader except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetYieldCurve2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "YieldCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID，对应 JSON 节 FXForwardPointsCurve")
def mdjsonGetFXForwardPointsCurve(reader, curve_id: str):
    """返回 McpFXForwardPointsCurve@n。读数：FxfpcFXForwardPoints。"""
    return _mdjson_get(reader, curve_id, "FXForwardPointsCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetFXForwardPointsCurve2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "FXForwardPointsCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetFXVolSurface2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "FXVolSurface2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID，如 SCM_LOCALVOL")
def mdjsonGetLocalVol(reader, curve_id: str):
    """返回 McpLocalVol@n。示例：=LocalVolGetCalendar(mdjsonGetLocalVol($B$3,\"SCM_LOCALVOL\"))"""
    return _mdjson_get(reader, curve_id, "LocalVol")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetCreditCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "CreditCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetBondSpreadCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "BondSpreadCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetForwardCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "ForwardCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "曲线 ID")
def mdjsonGetVolSurface(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "VolSurface")


@xl_func(macro=True, recalc_on_open=True, auto_resize=True)
@xl_arg("snapshot_file_or_dir", "str", "快照文件或目录")
@xl_return("var[][]")
def mdlsSnapshotPathResolve(snapshot_file_or_dir: str = ""):
    ok, path, err = _resolve_snapshot_path(snapshot_file_or_dir)
    if ok:
        return [["resolved_path", path]]
    return [["error", err]]
