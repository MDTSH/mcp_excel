# -*- coding: utf-8 -*-
"""
MCP 单文件 JSON / LiveMarketDataStore Excel UDF

设计原则（与 rawmd 目录模式一致）：
  1) McpLiveMarketDataStore(JSON路径 [, 假日文件]) → Store 对象句柄
     假日文件空则用 JSON 同目录 calendar.txt / Holidays.txt
  2) mdlsGetYieldCurve2(Store, curve_id) → McpYieldCurve2@n 对象
  3) mdlsGetCalendar(Store, code) / mdlsCalendarCodes(Store) / mdlsHolidaysPath(Store)
  4) 零息/折现/即期/波动率等用 curve.py / volatility.py 已有 UDF 对 **对象** 计算
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
from mcp.utils.workbook_path import (
    bundled_market_data_dir,
    get_active_workbook_dir,
    latest_mcp_market_data_json,
    resolve_data_path,
    resolve_workbook_relative_file,
)

_log = logging.getLogger(__name__)

_UDF_TRACE_LOG = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs", "livestore_udf.log")
)


def _udf_trace(msg: str) -> None:
    """Append one line so Excel hangs leave a breadcrumb on disk."""
    try:
        folder = os.path.dirname(_UDF_TRACE_LOG)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        from datetime import datetime

        line = "%s %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], msg)
        with open(_UDF_TRACE_LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass

# 不要写本机盘符。别人 clone 后只有仓库内 excel/data/market_data。
_DEFAULT_SNAPSHOT_DIR = bundled_market_data_dir()
_DEFAULT_BASELINE = os.path.join(
    _DEFAULT_SNAPSHOT_DIR, "MCP_MARKET_DATA_20260810.json"
)

# Excel 全量重算会反复求值 McpLiveMarketDataStore；同路径+mtime 复用，避免
# 多次 loadSnapshot 打乱进程级 SwapCurve 缓存（表现为仅第一条曲线成功）。
_LIVE_STORE_CACHE = {}  # (wb_dir, json, holidays, ver) -> (json_mtime, hol_mtime, wrapper)
_LIVE_STORE_CACHE_VER = 4
_HOLIDAYS_SIBLING_NAMES = ("calendar.txt", "Holidays.txt", "Holiday.txt")


def _detect_sibling_holidays(directory: str) -> str:
    if not directory:
        return ""
    for name in _HOLIDAYS_SIBLING_NAMES:
        cand = os.path.normpath(os.path.join(directory, name))
        if os.path.isfile(cand):
            return cand
    return ""


def _resolve_holidays_for_store(holidays_file: str, json_path: str):
    """显式路径优先（相对路径先对工作簿目录）；否则 JSON 同目录 calendar.txt / Holidays.txt。"""
    p = (holidays_file or "").strip()
    json_dir = os.path.dirname(json_path or "")
    if p:
        ok, resolved, err = resolve_workbook_relative_file(p, extra_dirs=[json_dir])
        if ok and resolved:
            return os.path.normpath(resolved), ""
        return "", err or ("holidays file not found: %s" % p)
    return _detect_sibling_holidays(json_dir), ""


def _file_mtime(path: str):
    if not path:
        return None
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _store_holidays_path(store) -> str:
    """取 Store 绑定的假日文件。优先 wrapper 属性，其次 C++ holidaysPath()，再探测 JSON 旁文件。"""
    if store is None:
        return ""
    p = getattr(store, "_mdls_holidays_path", None)
    if p:
        return str(p)
    inner = _unwrap_store(store)
    if inner is not None:
        try:
            hp = inner.holidaysPath()
            if hp:
                return str(hp)
        except Exception:
            pass
    snap = getattr(store, "_mdls_snapshot_path", None)
    if snap:
        return _detect_sibling_holidays(os.path.dirname(str(snap)))
    return ""


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
        latest = latest_mcp_market_data_json()
        if latest:
            return True, latest, ""
        if os.path.isfile(_DEFAULT_BASELINE):
            return True, _DEFAULT_BASELINE, ""
        p = _DEFAULT_SNAPSHOT_DIR

    ok, resolved, err = resolve_data_path(p, must_exist=True, allow_dir=True)
    wb = get_active_workbook_dir(allow_get_document=False)
    if wb:
        local = os.path.normpath(os.path.join(wb, p.replace("/", os.sep)))
        if os.path.isfile(local) or (os.path.isdir(local) and p):
            return True, local, ""
        local_data = os.path.normpath(os.path.join(wb, "data", os.path.basename(p)))
        if os.path.isfile(local_data):
            return True, local_data, ""
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
    return get_active_workbook_dir(allow_get_document=True) or "(workbook path unavailable)"


@xl_func(macro=True, recalc_on_open=False)
@xl_arg("relative_or_absolute_path", "str", "path relative to the workbook or absolute")
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


@xl_func("str snapshot, str holidays_file: var", macro=False, recalc_on_open=True, lru_cache=False)
@xl_arg("snapshot", "str", "JSON file or folder")
@xl_arg("holidays_file", "str", "calendar.txt path (blank=JSON folder)")
def McpLiveMarketDataStore(snapshot: str = "", holidays_file: str = ""):
    """
    加载全量 MCP 市场 JSON，返回 LiveStore 句柄（McpLiveMarketDataStore@n）。

    snapshot：JSON 文件，或含 MCP_MARKET_DATA_*.json 的目录（取该目录下最新一份）。
    holidays_file：假日文件路径，不是目录；留空则用 JSON 同目录 calendar.txt / Holidays.txt。
    """
    snapshot_file_or_dir = snapshot
    if not _has_mcp:
        return "mcp.mcp not loaded"
    try:
        from mcp.utils.excel_open_gate import gate

        g = gate("McpLiveMarketDataStore")
        if g is not None:
            return g
    except Exception:
        pass
    try:
        _udf_trace("ENTER arg=%r holidays=%r" % (snapshot_file_or_dir, holidays_file))
        _ensure_path()
        _udf_trace("after _ensure_path")
        ok, path, err = _resolve_snapshot_path(snapshot_file_or_dir)
        _udf_trace("after resolve ok=%s path=%s err=%s" % (ok, path, err))
        if not ok:
            return err
        path = os.path.normpath(path)
        hol_path, hol_err = _resolve_holidays_for_store(holidays_file, path)
        if hol_err:
            return hol_err
        # C++ parentPath 旧版只认 '/'；正斜杠可避免 Windows 把 base_path 判成 "."
        path_for_load = path.replace("\\", "/")
        hol_for_key = hol_path.replace("\\", "/") if hol_path else ""
        mtime = _file_mtime(path)
        hol_mtime = _file_mtime(hol_path)
        wb_dir = (get_active_workbook_dir(allow_get_document=False) or "").replace("\\", "/")
        wb_name = ""
        try:
            from mcp.utils.excel_open_gate import caller_workbook_name

            wb_name = caller_workbook_name() or ""
        except Exception:
            wb_name = ""
        cache_key = (wb_name, wb_dir, path_for_load, hol_for_key, _LIVE_STORE_CACHE_VER)
        _udf_trace("resolve wb=%s dir=%s path=%s" % (wb_name, wb_dir, path_for_load))
        cached = _LIVE_STORE_CACHE.get(cache_key)
        if (
            cached is not None
            and cached[0] == mtime
            and cached[1] == hol_mtime
            and cached[2] is not None
        ):
            _udf_trace("cache hit, return")
            return cached[2]

        inner = _mcp.MLiveMarketDataStore()
        if hol_path:
            hol_cpp = hol_path.replace("\\", "/")
            try:
                inner.setHolidaysPath(hol_cpp)
            except Exception as e:
                _udf_trace("setHolidaysPath skip: %s" % e)
            # 未重编 SWIG 时 C++ 仍可能走 Calendar(string)；绝对路径须配合 Calendar.cpp 修复
            os.environ["MCP_HOLIDAYS_PATH"] = hol_cpp
        _udf_trace("before loadSnapshot %s holidays=%s" % (path_for_load, hol_path))
        if not inner.loadSnapshot(path_for_load):
            _udf_trace("loadSnapshot failed: %s" % inner.lastError())
            return f"loadSnapshot failed: {inner.lastError()}"
        _udf_trace("after loadSnapshot")
        try:
            cpp_hol = inner.holidaysPath()
            if cpp_hol:
                hol_path = os.path.normpath(str(cpp_hol))
        except Exception:
            pass
        do_prewarm = True
        try:
            if hasattr(inner, "listCurveIds"):
                ids = " ".join(str(x).upper() for x in (inner.listCurveIds() or []))
                if ids and not any(k in ids for k in ("SWAP", "SOFR", "EFFR", "LPR", "FR007")):
                    do_prewarm = False
                _udf_trace("listCurveIds n=%s prewarm=%s" % (len(ids.split()) if ids else 0, do_prewarm))
        except Exception as e:
            do_prewarm = True
            _udf_trace("listCurveIds except: %s" % e)
        if do_prewarm:
            _udf_trace("before prewarm")
            _prewarm_swap_curves(inner)
            _udf_trace("after prewarm")
        if McpLiveStoreWrapper is None:
            try:
                inner._mdls_snapshot_path = path  # noqa: SLF001
                inner._mdls_holidays_path = hol_path  # noqa: SLF001
            except Exception:
                pass
            _LIVE_STORE_CACHE[cache_key] = (mtime, hol_mtime, inner)
            _udf_trace("return inner")
            return inner
        w = McpLiveStoreWrapper(inner)
        w._mdls_snapshot_path = path  # noqa: SLF001
        w._mdls_holidays_path = hol_path  # noqa: SLF001
        _LIVE_STORE_CACHE[cache_key] = (mtime, hol_mtime, w)
        _udf_trace("return wrapper")
        return w
    except Exception as e:
        _udf_trace("except: %s" % e)
        _log.warning("McpLiveMarketDataStore: %s", e, exc_info=True)
        return f"McpLiveMarketDataStore except: {e}"


@xl_func("var store, str code: var", macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore handle")
@xl_arg("code", "str", "calendar code e.g. USDMXN")
def mdlsGetCalendar(store, code: str = ""):
    """从 Store 绑定的假日文件切出日历，与建曲线同源。例：=mdlsGetCalendar($B$4,\"USDMXN\")"""
    if store is None or isinstance(store, str):
        return "mdlsGetCalendar: store is empty"
    hol = _store_holidays_path(store)
    if not hol:
        return "mdlsGetCalendar: no holidays file (pass 2nd arg to McpLiveMarketDataStore or put calendar.txt next to JSON)"
    cc = (code or "").strip()
    if not cc:
        return "mdlsGetCalendar: code is empty"
    try:
        from pyxll_func.core.mcp_calendar import McpCalendarOf

        return McpCalendarOf(cc, hol)
    except Exception as e:
        _log.warning("mdlsGetCalendar: %s", e, exc_info=True)
        return "mdlsGetCalendar except: %s" % e


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("store", "var", "value returned by McpLiveMarketDataStore")
def mdlsCalendarCodes(store):
    """返回 Store 假日文件中的全部 calendar code。例：=mdlsCalendarCodes($B$4)"""
    if store is None or isinstance(store, str):
        return [["mdlsCalendarCodes: store is empty"]]
    hol = _store_holidays_path(store)
    if not hol:
        return [["mdlsCalendarCodes: no holidays file"]]
    try:
        from pyxll_func.core.mcp_calendar import McpHolidaysCodes

        codes = McpHolidaysCodes(hol)
        if codes is None:
            return [[""]]
        if isinstance(codes, str):
            return [[codes]]
        return [[str(x)] for x in codes]
    except Exception as e:
        _log.warning("mdlsCalendarCodes: %s", e, exc_info=True)
        return [["mdlsCalendarCodes except: %s" % e]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "value returned by McpLiveMarketDataStore")
def mdlsSnapshotPath(store):
    """返回 Store 实际 loadSnapshot 的 JSON 绝对路径。"""
    if store is None or isinstance(store, str):
        return "mdlsSnapshotPath: store is empty"
    p = getattr(store, "_mdls_snapshot_path", None)
    if p:
        return str(p)
    inner = _unwrap_store(store)
    if inner is not None:
        p = getattr(inner, "_mdls_snapshot_path", None)
        if p:
            return str(p)
    return ""


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "value returned by McpLiveMarketDataStore")
def mdlsHolidaysPath(store):
    """返回 Store 实际使用的假日文件绝对路径。"""
    if store is None or isinstance(store, str):
        return "mdlsHolidaysPath: store is empty"
    hol = _store_holidays_path(store)
    return hol or ""


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "value returned by McpLiveMarketDataStore")
def mdlsLastError(store):
    s = _unwrap_store(store)
    if s is None:
        return "store is empty"
    try:
        return s.lastError() or ""
    except Exception as e:
        return str(e)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("patch_file", "str", "incremental patch JSON file path")
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
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("patch_json", "str", "patch JSON string")
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
        row = ["(empty)", "", "applyUpdate not yet called"]
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
@xl_arg("store", "var", "McpLiveMarketDataStore")
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
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_return("var[][]")
def mdlsLastUpdateImpactWithObjects(store):
    "影响表 + Row 4 列 Mcp 包装类名（列向量溢出，与 mdlsLastUpdateImpact 同布局）。"
    try:
        rows = _mdls_build_last_update_impact_rows(store, True)
        return _impact_rows_for_excel_spill(rows)
    except Exception as e:
        return [[f"mdlsLastUpdateImpactWithObjects except: {e}"]]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
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
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("section", "str", "JSON section name e.g. YieldCurve2 / FXVolSurface2")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetCurveBySection(store, section: str, curve_id: str):
    """按 Impact 行的 section + curve_id 取 Mcp* 对象。例：=mdlsGetCurveBySection($B$14,\"YieldCurve2\",\"CNHDEPO_2\")"""
    return market_data_source_get_curve_by_section(store, section, curve_id, "mdlsGet")


# ----- 取曲线对象（与 rawmdGet* 对称；读数请用 curve.py / volatility.py） -----


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetYieldCurve(store, curve_id: str):
    """返回 McpYieldCurve@n。示例：=YieldCurveZeroRate(mdlsGetYieldCurve($B$3,\"CNY_DEPO\"),日期,\"MID\")"""
    return _mdls_get(store, curve_id, "YieldCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. CNHDEPO_2")
def mdlsGetYieldCurve2(store, curve_id: str):
    """返回 McpYieldCurve2@n。示例：=YieldCurve2ZeroRate(mdlsGetYieldCurve2($B$3,\"CNHDEPO_2\"),$B$6,\"MID\")"""
    return _mdls_get(store, curve_id, "YieldCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID JSON section FXForwardPointsCurve")
def mdlsGetFXForwardPointsCurve(store, curve_id: str):
    """返回 McpFXForwardPointsCurve@n。示例：=FxfpcFXForwardPoints(mdlsGetFXForwardPointsCurve($B$3,\"USDCNH_FXFP_BGN\"),日期)"""
    return _mdls_get(store, curve_id, "FXForwardPointsCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetFXForwardPointsCurve2(store, curve_id: str):
    """返回 McpFXForwardPointsCurve2@n。示例：=Fxfpc2FXSpotRate(mdlsGetFXForwardPointsCurve2(...),...,\"MID\")"""
    return _mdls_get(store, curve_id, "FXForwardPointsCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetFXVolSurface2(store, curve_id: str):
    """返回 McpFXVolSurface2@n。示例：=FXVolSurface2GetVolatility(曲面, \"25C\", 到期日, \"MID\")"""
    return _mdls_get(store, curve_id, "FXVolSurface2")


@xl_func(macro=False, recalc_on_open=True, lru_cache=False)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. SCM_LOCALVOL")
def mdlsGetLocalVol(store, curve_id: str):
    """返回 McpLocalVol@n。示例：=LocalVolGetCalendar(mdlsGetLocalVol($B$3,\"SCM_LOCALVOL\"))"""
    _udf_trace("mdlsGetLocalVol enter %s" % curve_id)
    try:
        out = _mdls_get(store, curve_id, "LocalVol")
        _udf_trace("mdlsGetLocalVol leave %s -> %s" % (curve_id, type(out).__name__))
        return out
    except Exception as e:
        _udf_trace("mdlsGetLocalVol except %s: %s" % (curve_id, e))
        raise


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetSwapCurve(store, curve_id: str):
    return _mdls_get(store, curve_id, "SwapCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID")
def mdlsGetBondCurve(store, curve_id: str):
    _udf_trace("mdlsGetBondCurve enter %s" % curve_id)
    try:
        out = _mdls_get(store, curve_id, "BondCurve")
        _udf_trace("mdlsGetBondCurve leave %s -> %s" % (curve_id, type(out).__name__))
        return out
    except Exception as e:
        _udf_trace("mdlsGetBondCurve except %s: %s" % (curve_id, e))
        raise


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. CNY_CREDIT_CFETS")
def mdlsGetCreditCurve(store, curve_id: str):
    """返回 McpCreditCurve@n。读数：CreditCurveHazardRate / CreditCurveDefaultProbability。"""
    return _mdls_get(store, curve_id, "CreditCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. CNY_BOND_POLICY_SPREAD")
def mdlsGetBondSpreadCurve(store, curve_id: str):
    """返回 McpBondSpreadCurve@n。读数：BondSpreadCurveZeroSpread；基准冲击：rawmdBondSpreadSetBenchmark。"""
    return _mdls_get(store, curve_id, "BondSpreadCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. EQ_FORWARD")
def mdlsGetForwardCurve(store, curve_id: str):
    """返回 McpForwardCurve@n（非 FX）。读数：ForwardCurveForwardRate。"""
    return _mdls_get(store, curve_id, "ForwardCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("curve_id", "str", "curve ID e.g. EQ_VOL_SAMPLE")
def mdlsGetVolSurface(store, curve_id: str):
    """返回 McpVolSurface@n（非 FX）。读数：VolSurfaceGetVolatility。"""
    return _mdls_get(store, curve_id, "VolSurface")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("store", "var", "McpLiveMarketDataStore")
@xl_arg("product_type", "str", "price_data_index section e.g. FXSPOT / EQUITYSPOT")
@xl_arg("instrument_code", "str", "instrument code e.g. EURUSD / 600000.SH")
@xl_arg("valuation_date", "var", "optional empty uses snapshot date")
@xl_arg("sample_num", "int", "window length default 252")
@xl_arg("model", "str", "CLOSE_TO_CLOSE / EWMA / LINXIAO / RISKMETRICS default EWMA")
def mdlsHistVolFromPriceData(
    store,
    product_type: str,
    instrument_code: str,
    valuation_date=None,
    sample_num=252,
    model="EWMA",
):
    "从 HIST CSV 动态构建 McpHistVols，none需 JSON HistVol 节点。读数：HvsGetVol(对象, 日期, sampleNum)。"
    return rawmdHistVolFromPriceData(
        store, product_type, instrument_code, valuation_date, sample_num, model
    )


# ========== JsonReader（只读，同样先取对象再读数） ==========


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("json_file", "str", "MCP_MARKET_DATA JSON file")
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
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetYieldCurve2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "YieldCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID JSON section FXForwardPointsCurve")
def mdjsonGetFXForwardPointsCurve(reader, curve_id: str):
    """返回 McpFXForwardPointsCurve@n。读数：FxfpcFXForwardPoints。"""
    return _mdjson_get(reader, curve_id, "FXForwardPointsCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetFXForwardPointsCurve2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "FXForwardPointsCurve2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetFXVolSurface2(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "FXVolSurface2")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID e.g. SCM_LOCALVOL")
def mdjsonGetLocalVol(reader, curve_id: str):
    """返回 McpLocalVol@n。示例：=LocalVolGetCalendar(mdjsonGetLocalVol($B$3,\"SCM_LOCALVOL\"))"""
    return _mdjson_get(reader, curve_id, "LocalVol")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetCreditCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "CreditCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetBondSpreadCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "BondSpreadCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetForwardCurve(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "ForwardCurve")


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("reader", "object", "McpMarketDataJsonReader")
@xl_arg("curve_id", "str", "curve ID")
def mdjsonGetVolSurface(reader, curve_id: str):
    return _mdjson_get(reader, curve_id, "VolSurface")


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("snapshot_file_or_dir", "str", "snapshot file or directory")
@xl_return("var[][]")
def mdlsSnapshotPathResolve(snapshot_file_or_dir: str = ""):
    ok, path, err = _resolve_snapshot_path(snapshot_file_or_dir)
    if ok:
        return [["resolved_path", path]]
    return [["error", err]]
