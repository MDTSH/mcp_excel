# -*- coding: utf-8 -*-
"""
Raw Market Data Excel UDF

从 MCP_MARKET_DATA_YYYYMMDD.json 加载市场数据，供 Excel 使用。
参考：EXCEL_INTEGRATION_PITFALLS、curve.py、RAW_MARKET_DATA_JSON_DESIGN.md 14.6–14.7

UDF 命名：rawmd 前缀（Raw Market Data）
- McpRawMarketManager(root)：单例 Manager，返回 McpRawMarketManager@0
- rawmdYieldCurve / rawmdGetYieldCurve、rawmdYieldCurve2 / rawmdGetYieldCurve2、…：
  返回对应 mcp.wrapper.Mcp* 对象（如 McpYieldCurve2@0）；读数用 curve.py 的 YieldCurve2ZeroRate 等。
  估值日可选，省略或空单元格时使用目录下**最新**主索引日（与 C++ getLatestAvailableDate 一致）。
- mdlsGetYieldCurve2(Store, id) 与 rawmdGetYieldCurve2 对称，但数据源为 McpLiveMarketDataStore（单文件快照，无估值日参数）。
- rawmdBondSpreadCurve / rawmdGetBondSpreadCurve 返回的 McpBondSpreadCurve 支持 **setBenchmarkCurve / getBenchmarkCurve**（与 C++ BondSpreadCurve 一致）；基准冲击可用 **rawmdBondSpreadSetBenchmark**。
- rawmdLatestValuationDate(manager)：返回当前使用的「最新主索引日」字符串（YYYY-MM-DD）。
- rawmdAvailableDates / rawmdMarketDataSnapshot：日期列表、快照摘要（快照的估值日亦可省略，用最新日）

PyXLL 配置：pyxll.cfg [modules] mcp_raw_market_data
MCP_MD_PATH  或 scenario_config market_data.rawmd_market_data_root
"""

from __future__ import absolute_import

import json
import logging
import math
import os
import sys
from typing import Any, Dict, List, Optional

from pyxll import xl_arg, xl_func, xl_return

try:
    from mcp_calendar import date_to_string
except ImportError:
    from pyxll_func.core.mcp_calendar import date_to_string

# 项目导入（McpRawMarketManagerWrapper 避免与 UDF 函数 McpRawMarketManager 同名冲突）
try:
    import mcp.mcp as _mcp
    from mcp.wrapper import (
        McpRawMarketManager as McpRawMarketManagerWrapper,
        McpBondCurve,
        McpBondSpreadCurve,
        McpCreditCurve,
        McpForwardCurve,
        McpFXForwardPointsCurve,
        McpFXForwardPointsCurve2,
        McpFXVolSurface,
        McpFXVolSurface2,
        McpHistVols,
        McpLocalVol,
        McpSwapCurve,
        McpVolSurface,
        McpYieldCurve,
        McpYieldCurve2,
    )
    _has_mcp = True
except ImportError:
    _mcp = None
    McpRawMarketManagerWrapper = None
    McpBondCurve = None
    McpBondSpreadCurve = None
    McpCreditCurve = None
    McpForwardCurve = None
    McpFXForwardPointsCurve = None
    McpFXForwardPointsCurve2 = None
    McpFXVolSurface = None
    McpFXVolSurface2 = None
    McpHistVols = None
    McpLocalVol = None
    McpSwapCurve = None
    McpVolSurface = None
    McpYieldCurve = None
    McpYieldCurve2 = None
    _has_mcp = False

_log = logging.getLogger(__name__)

# Manager 单例缓存：resolved_root -> McpRawMarketManager
_rawmd_manager_cache: Dict[str, Any] = {}

# getXxx -> RawMarketDataLoader.build_curve 的 curve_type（构建失败时解析原因）
_CPP_NAME_TO_CURVE_TYPE: Dict[str, str] = {
    "getYieldCurve": "YieldCurve",
    "getYieldCurve2": "YieldCurve2",
    "getSwapCurve": "SwapCurve",
    "getBondCurve": "BondCurve",
    "getCreditCurve": "CreditCurve",
    "getBondSpreadCurve": "BondSpreadCurve",
    "getFXForwardPointsCurve": "FXForwardPointsCurve",
    "getFXForwardPointsCurve2": "FXForwardPointsCurve2",
    "getForwardCurve": "ForwardCurve",
    "getVolSurface": "VolSurface",
    "getFXVolSurface": "FXVolSurface",
    "getFXVolSurface2": "FXVolSurface2",
    "getLocalVol": "LocalVol",
    "getHistVol": "HistVol",
}

# These *2 M-layer classes returned by MRawMarketManager are already complete
# Python SWIG objects. Their wrapper classes cannot be recreated from a raw
# getHandler() pointer because the exposed C++ overloads do not include a
# single-handler constructor.
# *2 曲面/曲线：C++ 返回 M*；勿 Mcp*(getHandler())；用 excel_mcp_object_handle 显示 Mcp*@n。
_RAWMD_RETURN_AS_IS_BASES = {
    "MYieldCurve",
    "MYieldCurve2",
    "MFXForwardPointsCurve2",
    "MFXVolSurface2",
    "MVolSurface2",
}


def _ensure_path():
    """确保 excel 模块可导入"""
    here = os.path.dirname(os.path.abspath(__file__))
    proj = os.path.normpath(os.path.join(here, "..", ".."))
    if proj not in sys.path:
        sys.path.insert(0, proj)


def _norm_date(val) -> str:
    """将非 datetime 的输入（字符串、YYYYMMDD 数字串等）规范为 YYYY-MM-DD；UDF 入口优先用 _valuation_date_to_string。"""
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return date_to_string(val)
    s = str(val).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def _valuation_date_to_string(val) -> str:
    """与 curve.py YieldCurveDiscountFactor 一致：datetime → date_to_string，再传入 getYieldCurve / load_daily_index。"""
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return date_to_string(val)
    # Excel 序列号（单元格为日期格式时 PyXLL 以 float 传入）
    try:
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            x = float(val)
            if 20000.0 < x < 120000.0:
                import datetime as _dt

                base = _dt.datetime(1899, 12, 30)
                d = base + _dt.timedelta(days=x)
                return date_to_string(d)
    except Exception:
        pass
    s = str(val).strip()
    # YYYY-MM-DD 文本（@xl_arg 用 datetime 时 PyXLL 会误走 float 转换，故 UDF 改用 var）
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return _norm_date(val)


def _is_valuation_date_empty(val) -> bool:
    """未指定估值日：None、空字符串、Excel 空单元格常表现为 0。"""
    if val is None:
        return True
    if isinstance(val, (int, float)) and val == 0:
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False


def _is_product_type_empty(val) -> bool:
    """未指定 product_type：None 或空串。"""
    if val is None:
        return True
    if isinstance(val, str) and not val.strip():
        return True
    return False


def _manager_get_latest_available_date_from_mgr(mgr: Any) -> str:
    """优先 C++ getLatestAvailableDate()，否则用可用日期列表最后一项（已排序）。"""
    gl = getattr(mgr, "getLatestAvailableDate", None)
    if callable(gl):
        try:
            s = gl()
            if s is not None:
                t = str(s).strip()
                if t:
                    return t
        except Exception:
            pass
    dates = _manager_get_available_dates(mgr)
    return dates[-1] if dates else ""


def _resolve_valuation_date_for_curve(manager, valuation_date) -> str:
    """若未指定估值日则使用目录下最新主索引日。"""
    if not _is_valuation_date_empty(valuation_date):
        return _valuation_date_to_string(valuation_date)
    mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
    return _manager_get_latest_available_date_from_mgr(mgr)


def _resolve_snapshot_valuation_date(root: str, valuation_date) -> str:
    """rawmdMarketDataSnapshot：未指定日期时用 root 下最新主索引日。"""
    if not _is_valuation_date_empty(valuation_date):
        return _valuation_date_to_string(valuation_date)
    _ensure_path()
    from excel.raw_market_data import RawMarketDataManager

    return RawMarketDataManager(root=root).getLatestAvailableDate()


def _get_pyd_dir() -> str:
    """返回 _mcp.pyd 所在的绝对目录（如 C:\\mcp\\mcpexcel1.4\\python\\lib\\X64）。"""
    if not _has_mcp:
        return ""
    try:
        ext = getattr(_mcp, "_mcp", _mcp)
        pyd_path = getattr(ext, "__file__", "") or getattr(_mcp, "__file__", "")
        if pyd_path:
            return os.path.dirname(os.path.abspath(pyd_path))
    except Exception:
        pass
    return ""


def _get_pyd_based_default_root() -> str:
    """pyd 所在目录的 ../../market_data；无 pyd 时用 mcp 包所在目录的 ../market_data"""
    pyd_dir = _get_pyd_dir()
    if pyd_dir:
        return os.path.normpath(os.path.join(pyd_dir, "..", "..", "market_data"))
    return ""


def _resolve_env_path(env_val: str) -> str:
    """解析来自 pyxll.cfg [ENVIRONMENT] 的路径值。
    绝对路径原样返回；相对路径以 .pyd 所在目录为基准（与 C++ MRawMarketManager 构造逻辑一致）。
    若取不到 pyd 目录，回落到 os.getcwd()。
    """
    p = env_val.strip()
    if not p:
        return ""
    if os.path.isabs(p) or (len(p) >= 2 and p[1] == ":") or p.startswith("\\\\"):
        return os.path.normpath(p)
    base = _get_pyd_dir() or os.getcwd()
    return os.path.normpath(os.path.join(base, p))


def _get_rawmd_default_root() -> str:
    """默认 market_data_root 优先级：
    1. 环境变量 MCP_MD_PATH（pyxll.cfg [ENVIRONMENT] 推荐用此名）
    2. 环境变量 RAWMD_MARKET_DATA_ROOT（兼容旧配置）
    3. scenario_config.json 中的 market_data.rawmd_market_data_root
    4. pyd 目录的 ../../market_data（回落）
    相对路径均以 .pyd 所在目录为基准（与 C++ 侧一致）。
    """
    for env_name in ("MCP_MD_PATH", "RAWMD_MARKET_DATA_ROOT"):
        env_val = os.environ.get(env_name, "").strip()
        if env_val:
            return _resolve_env_path(env_val)
    try:
        _ensure_path()
        for search in [os.getcwd(), os.path.dirname(os.path.abspath(__file__)), "."]:
            cfg_path = os.path.join(search, "market_data", "snapshots", "scenario_config.json")
            if not os.path.isfile(cfg_path):
                cfg_path = os.path.join(search, "scenario_config.json")
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                val = cfg.get("market_data", {}).get("rawmd_market_data_root", "").strip()
                if val:
                    return _resolve_env_path(val)
                break
    except Exception:
        pass
    pyd_root = _get_pyd_based_default_root()
    if pyd_root:
        return os.path.normpath(pyd_root)
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "market_data"))


def _resolve_market_data_root(path) -> str:
    """解析路径：绝对路径原样；相对路径以 .pyd 目录为基准（与 C++ 一致）。
    path 可能是 Excel 传入的字符串或 Manager 对象引用。
    """
    if path is None:
        return _get_rawmd_default_root()
    if not isinstance(path, str):
        if hasattr(path, "getRoot"):
            path = path.getRoot() or ""
        elif hasattr(path, "getInstance"):
            inner = path.getInstance()
            path = getattr(inner, "getRoot", lambda: "")() or ""
        else:
            path = str(path) if path else ""
    p = (path or "").strip()
    if not p:
        return _get_rawmd_default_root()
    if os.path.isabs(p) or (len(p) >= 2 and p[1] == ":") or p.startswith("\\\\"):
        return os.path.normpath(p)
    # 相对路径：与 C++ 侧统一用 pyd 目录为基准
    base = _get_pyd_dir() or os.getcwd()
    return os.path.normpath(os.path.join(base, p))


def _is_valid_rawmd_directory(root: str) -> tuple:
    """返回 (valid: bool, error_msg: str)"""
    if not root or not os.path.isdir(root):
        return False, f"Directory not found: {root}"
    import glob
    files = glob.glob(os.path.join(root, "MCP_MARKET_DATA_*.json"))
    if not files:
        return False, f"No MCP_MARKET_DATA_*.json found in directory: {root}"
    return True, ""


def _get_or_create_manager(root: str) -> Any:
    """优先 C++ MRawMarketManager，fallback Python RawMarketDataManager；均返回 McpRawMarketManager"""
    if root not in _rawmd_manager_cache:
        _ensure_path()
        try:
            if _has_mcp and _mcp is not None:
                mgr = _mcp.MRawMarketManager(root)
                mgr.setRoot(root)
            else:
                raise AttributeError("mcp not loaded")
        except (ImportError, AttributeError):
            from excel.raw_market_data import RawMarketDataManager

            mgr = RawMarketDataManager(root=root)
        if McpRawMarketManagerWrapper is not None:
            w = McpRawMarketManagerWrapper(mgr)
            # 与 rawmdSwapCurve 一致：C++ 构造时已带 root；若 SWIG getRoot() 偶发空，仍可用此字段 + 缓存反查做 Python 兜底
            setattr(w, "_rawmd_root", os.path.normpath(root))
            _rawmd_manager_cache[root] = w
        else:
            _rawmd_manager_cache[root] = mgr
    return _rawmd_manager_cache[root]


def _python_rawmd_try(root: str, curve_id: str, vd: str, snake_name: str) -> Optional[Any]:
    """
    C++ MRawMarketManager::get* 返回 None 时，用同一 JSON 走 Python RawMarketDataManager 构建
    （build_curve 与 C++ 路径可能不一致，作兜底）。
    """
    if not root or not os.path.isdir(root) or not snake_name:
        return None
    try:
        _ensure_path()
        from excel.raw_market_data import RawMarketDataManager

        mcp_mod = _mcp if _has_mcp else None
        rdm = RawMarketDataManager(root=root, mcp_module=mcp_mod)
        fn = getattr(rdm, snake_name, None)
        if not callable(fn):
            return None
        return fn(curve_id, vd)
    except Exception as e:
        _log.debug("_python_rawmd_try %s: %s", snake_name, e, exc_info=True)
        return None


def _manager_get_by_cpp_or_snake(
    mgr: Any,
    curve_id: str,
    vd: str,
    cpp_name: str,
    snake_name: str,
    root: str = "",
) -> Optional[Any]:
    """优先 C++ 风格 getXxx；若返回 None 则用 Python RawMarketDataManager 的 snake_case 兜底。"""
    gc = getattr(mgr, cpp_name, None)
    gs = getattr(mgr, snake_name, None)
    attempts = 3 if cpp_name == "getCreditCurve" else 1
    if callable(gc):
        out = None
        for _ in range(attempts):
            out = gc(curve_id, vd)
            if out is not None:
                return out
        return _python_rawmd_try(root, curve_id, vd, snake_name)
    if callable(gs):
        out = None
        for _ in range(attempts):
            out = gs(curve_id, vd)
            if out is not None:
                return out
        return _python_rawmd_try(root, curve_id, vd, snake_name)
    return None


def _wrap_mcp_if_needed(curve: Any, wrapper_cls: Any, udf_label: str = "") -> Any:
    if curve is None:
        return None
    if wrapper_cls is not None:
        try:
            base_cls = wrapper_cls.__mro__[1]
            base_name = getattr(base_cls, "__name__", "")
            if base_name in _RAWMD_RETURN_AS_IS_BASES and isinstance(curve, base_cls):
                try:
                    from mcp.wrapper import excel_mcp_object_handle

                    return excel_mcp_object_handle(curve, wrapper_cls.__name__)
                except Exception:
                    return curve
        except Exception:
            pass
    if wrapper_cls is not None and hasattr(curve, "getHandler"):
        h = curve.getHandler()
        if h is None:
            # getHandler() 为 None 时仍调用 Mcp*(None) 会在 slot_tp_init / _mcp.pyd 内崩溃
            return (
                f"{udf_label}: getHandler() 返回 null，无法构造 Mcp 包装（底层 C++/SWIG 指针缺失）。"
                f" 曲线对象类型: {type(curve).__name__}"
            )
        return wrapper_cls(h)
    return curve


def _rawmd_curve_udfs(
    manager,
    curve_id: str,
    valuation_date,
    cpp_name: str,
    snake_name: str,
    wrapper_cls: Any,
    udf_label: str,
):
    """内部：按 Manager 取曲线/曲面并包一层 Mcp*；估值日未指定则用最新主索引日。"""
    if manager is None or isinstance(manager, str):
        return manager if isinstance(manager, str) else f"{udf_label}: manager 为空"
    try:
        date_str = _resolve_valuation_date_for_curve(manager, valuation_date)
        if not date_str:
            return f"{udf_label}: 无可用估值日（目录下无 MCP_MARKET_DATA_*.json）"
        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        root = _resolve_rawmd_root(manager, mgr)
        curve = _manager_get_by_cpp_or_snake(
            mgr, curve_id, date_str, cpp_name, snake_name, root
        )
        if curve is None:
            hint = _sections_hint_for_curve_id(root, date_str, (curve_id or "").strip())
            base = f"Curve not found: {curve_id} @ {date_str}"
            if hint:
                primary = _CPP_NAME_TO_CURVE_TYPE.get(cpp_name, "")
                if primary and _hint_matches_cpp_udf(primary, hint):
                    detail = _explain_python_build_failure(
                        root, date_str, (curve_id or "").strip(), cpp_name
                    )
                    if detail:
                        return f"Curve build failed: {curve_id} @ {date_str}: {detail}"
                    return (
                        f"{base} — JSON 中已有该 ID（节与 UDF 一致），但 C++/Python 构建均返回空；"
                        f"请检查历史行情 CSV、列名与 price_data_index 配置。"
                    )
                return (
                    f"{base} — JSON 中该 ID 出现在节: {hint}，与当前 UDF 期望不一致"
                    f"（例如 FX 曲面请用 rawmdFXVolSurface）。"
                )
            return base
        return _wrap_mcp_if_needed(curve, wrapper_cls, udf_label)
    except Exception as e:
        s = f"{udf_label} except: {e}"
        _log.warning(s, exc_info=True)
        return s


def _decode_swig_std_string_vector(obj: Any) -> List[str]:
    """
    SWIG 将 std::vector<std::string> 以 SwigPyObject(指针) 返回；用 MSVC ABI 解码（Win64 + _mcp.pyd）。
    """
    if obj is None:
        return []
    type_name = type(obj).__name__
    if type_name not in ("SwigPyObject",):
        return []
    try:
        import ctypes

        class _MSVCStdString(ctypes.Structure):
            _fields_ = [
                ("_Bx", ctypes.c_byte * 16),
                ("_Mysize", ctypes.c_size_t),
                ("_Myres", ctypes.c_size_t),
            ]

        def _read_str(addr: int) -> str:
            s = _MSVCStdString.from_address(addr)
            n = int(s._Mysize)
            if n <= 0:
                return ""
            if n < 16:
                return bytes(s._Bx[:n]).decode("utf-8", errors="replace")
            ptr = ctypes.c_void_p.from_buffer_copy(memoryview(s._Bx)[:8]).value
            if not ptr:
                return ""
            return ctypes.string_at(ptr, n).decode("utf-8", errors="replace")

        vec_ptr = int(obj)
        if not vec_ptr:
            return []
        slots = (ctypes.c_void_p * 3).from_address(vec_ptr)
        first, last = int(slots[0] or 0), int(slots[1] or 0)
        if not first or not last or last <= first:
            return []
        elem = ctypes.sizeof(_MSVCStdString)
        count = (last - first) // elem
        return [_read_str(first + i * elem) for i in range(count)]
    except Exception as e:
        _log.debug("_decode_swig_std_string_vector: %s", e, exc_info=True)
        return []


def _coerce_swig_string_vector_to_str_list(d: Any) -> List[str]:
    """MRawMarketManager / MLiveMarketDataStore 的 std::vector<string> SWIG 返回值。"""
    if d is None:
        return []
    if isinstance(d, (list, tuple)):
        return [str(x) for x in d]
    if type(d).__name__ == "SwigPyObject":
        decoded = _decode_swig_std_string_vector(d)
        if decoded:
            return decoded
    try:
        n = len(d)
        return [str(d[i]) for i in range(n)]
    except Exception:
        pass
    try:
        return [str(x) for x in iter(d)]
    except Exception:
        pass
    return []


def _manager_root_str(mgr: Any) -> str:
    gr = getattr(mgr, "getRoot", None)
    if not callable(gr):
        return ""
    try:
        r = gr()
        if r is None:
            return ""
        if isinstance(r, bytes):
            return r.decode("utf-8", errors="replace").strip()
        return str(r).strip()
    except Exception:
        return ""


def _resolve_rawmd_root(manager: Any, mgr: Any) -> str:
    """
    解析市场数据根目录：优先 C++ getRoot()；否则用 McpRawMarketManager 上保存的 _rawmd_root；
    再用 _rawmd_manager_cache 反查（与 rawmdSwapCurve 单例路径一致，避免 getRoot 空导致 Python 兜底跳过）。
    """
    r = _manager_root_str(mgr)
    if r:
        return os.path.normpath(r)
    w = manager
    if w is not None:
        tr = getattr(w, "_rawmd_root", None)
        if isinstance(tr, str) and tr.strip():
            return os.path.normpath(tr.strip())
    try:
        for cached_root, cached_m in _rawmd_manager_cache.items():
            if cached_m is w:
                return os.path.normpath(cached_root)
            if hasattr(cached_m, "getInstance") and cached_m.getInstance() is mgr:
                return os.path.normpath(cached_root)
    except Exception:
        pass
    return ""


def _sections_hint_for_curve_id(root: str, date_str: str, curve_id: str) -> str:
    """若主索引中存在该 curve_id，列出所在顶层节名，便于区分 VolSurface / FXVolSurface 等。"""
    if not root or not curve_id or not date_str:
        return ""
    try:
        _ensure_path()
        from excel.raw_market_data import RawMarketDataManager

        idx = RawMarketDataManager(root=root).load_daily_index(date_str)
        if idx is None:
            return ""
        by_sec = idx.list_curve_ids_by_section()
        hits = [sec for sec, ids in by_sec.items() if curve_id in ids]
        return ",".join(hits) if hits else ""
    except Exception:
        return ""


def _hint_matches_cpp_udf(primary: str, hint: str) -> bool:
    """hint 为逗号分隔节名；HistVol 与 HistVols 视为同类。"""
    if not primary or not hint:
        return False
    secs = [x.strip() for x in hint.split(",") if x.strip()]
    if primary in secs:
        return True
    if primary == "HistVol" and "HistVols" in secs:
        return True
    return False


def _explain_python_build_failure(
    root: str, date_str: str, curve_id: str, cpp_name: str
) -> str:
    """
    JSON 中已有 curve_id 且节名与 UDF 一致，但 get* 返回 None 时：用与兜底相同的 loader 调用 fromJson，返回异常信息。
    """
    ct = _CPP_NAME_TO_CURVE_TYPE.get(cpp_name)
    if not ct:
        return ""
    try:
        _ensure_path()
        from excel.raw_market_data import RawMarketDataManager

        mcp_mod = _mcp if _has_mcp else None
        rdm = RawMarketDataManager(root=root, mcp_module=mcp_mod)
        idx = rdm.load_daily_index(date_str)
        if idx is None:
            return "无法加载日索引文件"
        j = idx.get_curve_json(curve_id, ct)
        if j is None:
            return "索引 get_curve_json 无条目（与 list 扫描不一致时请检查大小写/空格）"
        err = rdm._loader.build_curve_explain(ct, j, idx)
        return err or ""
    except Exception as e:
        return str(e)


def _manager_get_available_dates(mgr: Any) -> List[str]:
    out: List[str] = []
    if hasattr(mgr, "getAvailableDates"):
        d = mgr.getAvailableDates()
        out = _coerce_swig_string_vector_to_str_list(d)
    elif hasattr(mgr, "get_available_dates"):
        r = mgr.get_available_dates()
        out = list(r) if r else []

    if out:
        return out

    # C++ 侧目录解析/扫描与 Python 不一致、或 SWIG 返回空向量时，用 getRoot + Python 扫描兜底（与 raw_market_data_loader 一致）
    root = _manager_root_str(mgr)
    if root:
        try:
            _ensure_path()
            from excel.raw_market_data import RawMarketDataManager

            out = RawMarketDataManager(root=root).get_available_dates()
        except Exception:
            out = []
    return out


# ========== UDF ==========


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("market_data_root", "str", "市场数据根目录，空则用默认")
def McpRawMarketManager(market_data_root: str = ""):
    """
    获取 Raw Market Data Manager（单例）。
    同一 root 复用同一 Manager。找不到目录时返回错误字符串。
    示例：=McpRawMarketManager() 或 =McpRawMarketManager("D:\\market_data")
    """
    try:
        root = _resolve_market_data_root(market_data_root)
        valid, err = _is_valid_rawmd_directory(root)
        if not valid:
            return err
        return _get_or_create_manager(root)
    except Exception as e:
        s = f"McpRawMarketManager except: {e}"
        _log.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID，如 CNY_ZERO")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用目录下最新主索引日")
def rawmdYieldCurve(manager, curve_id: str, valuation_date=None):
    """
    从 Manager 获取收益率曲线，返回 McpYieldCurve（供 Adapter 使用）。
    示例：=rawmdYieldCurve(McpRawMarketManager(),"CNY_ZERO",A1) 或 =rawmdYieldCurve(McpRawMarketManager(),"CNY_ZERO") 用最新日
    """
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getYieldCurve", "get_yield_curve", McpYieldCurve, "rawmdYieldCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "双边曲线 ID，如 CNHDEPO_2")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用目录下最新主索引日")
def rawmdYieldCurve2(manager, curve_id: str, valuation_date=None):
    """从主索引 YieldCurve2 节获取双边收益率曲线，返回 McpYieldCurve2。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getYieldCurve2", "get_yield_curve2", McpYieldCurve2, "rawmdYieldCurve2",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID，如 CNY_SWAP_FR007")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdSwapCurve(manager, curve_id: str, valuation_date=None):
    """
    从 Manager 获取掉期曲线，返回 McpSwapCurve。
    示例：=rawmdSwapCurve(McpRawMarketManager(),"CNY_SWAP_FR007",A1) 或省略最后一格用最新日
    """
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getSwapCurve", "get_swap_curve", McpSwapCurve, "rawmdSwapCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdBondCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpBondCurve。示例：=rawmdBondCurve(McpRawMarketManager(),\"BOND_CURVE_ID\",A1)"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getBondCurve", "get_bond_curve", McpBondCurve, "rawmdBondCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdCreditCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpCreditCurve。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getCreditCurve", "get_credit_curve", McpCreditCurve, "rawmdCreditCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdBondSpreadCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpBondSpreadCurve（含 setBenchmarkCurve / getBenchmarkCurve，与 C++ BondSpreadCurve 一致）。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getBondSpreadCurve", "get_bond_spread_curve", McpBondSpreadCurve, "rawmdBondSpreadCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond_spread_curve", "object", "McpBondSpreadCurve（如 rawmdBondSpreadCurve 返回值）")
@xl_arg("benchmark_curve", "object", "McpYieldCurve 新基准曲线")
def rawmdBondSpreadSetBenchmark(bond_spread_curve, benchmark_curve):
    """将利差曲线的基准替换为 benchmark_curve（利率情景/基准冲击）；返回同一 McpBondSpreadCurve 便于链式引用。"""
    if not _has_mcp or bond_spread_curve is None or benchmark_curve is None:
        return None
    bond_spread_curve.setBenchmarkCurve(benchmark_curve)
    return bond_spread_curve


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdFXForwardPointsCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpFXForwardPointsCurve（对应主索引节 FXForwardPointsCurve）。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getFXForwardPointsCurve", "get_fx_forward_points_curve",
        McpFXForwardPointsCurve, "rawmdFXForwardPointsCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "双边 FX 远期点曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdFXForwardPointsCurve2(manager, curve_id: str, valuation_date=None):
    """返回 McpFXForwardPointsCurve2（对应主索引节 FXForwardPointsCurve2）。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getFXForwardPointsCurve2", "get_fx_forward_points_curve2",
        McpFXForwardPointsCurve2, "rawmdFXForwardPointsCurve2",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdForwardCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpForwardCurve。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getForwardCurve", "get_forward_curve", McpForwardCurve, "rawmdForwardCurve",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdVolSurface(manager, curve_id: str, valuation_date=None):
    """返回 McpVolSurface。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getVolSurface", "get_vol_surface", McpVolSurface, "rawmdVolSurface",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdFXVolSurface(manager, curve_id: str, valuation_date=None):
    """返回 McpFXVolSurface。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getFXVolSurface", "get_fx_vol_surface", McpFXVolSurface, "rawmdFXVolSurface",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "双边 FX 波动率曲面 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdFXVolSurface2(manager, curve_id: str, valuation_date=None):
    """返回 McpFXVolSurface2（对应主索引节 FXVolSurface2）。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getFXVolSurface2", "get_fx_vol_surface2", McpFXVolSurface2, "rawmdFXVolSurface2",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdLocalVol(manager, curve_id: str, valuation_date=None):
    """返回 McpLocalVol。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getLocalVol", "get_local_vol", McpLocalVol, "rawmdLocalVol",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
def rawmdHistVol(manager, curve_id: str, valuation_date=None):
    """返回 McpHistVols（主索引节 HistVol）。"""
    return _rawmd_curve_udfs(
        manager, curve_id, valuation_date,
        "getHistVol", "get_hist_vol", McpHistVols, "rawmdHistVol",
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager / McpLiveMarketDataStore")
@xl_arg("product_type", "str", "price_data_index 节名，如 EQUITYSPOT")
@xl_arg("instrument_code", "str", "标的代码，如 600000.SH")
@xl_arg("valuation_date", "var", "可选；空则 Raw 用最新主索引日，Live 用快照日")
@xl_arg("sample_num", "int", "窗口长度，默认 252")
@xl_arg("model", "str", "CLOSE_TO_CLOSE / EWMA / LINXIAO / RISKMETRICS，默认 EWMA")
def rawmdHistVolFromPriceData(
    manager,
    product_type: str,
    instrument_code: str,
    valuation_date=None,
    sample_num=252,
    model="EWMA",
):
    """从 HIST CSV 动态构建 McpHistVols，无需 JSON HistVol 节点。"""
    if manager is None or isinstance(manager, str):
        return manager if isinstance(manager, str) else "rawmdHistVolFromPriceData: manager 为空"
    pt = (product_type or "").strip()
    code = (instrument_code or "").strip()
    if not pt or not code:
        return "rawmdHistVolFromPriceData: product_type 或 instrument_code 为空"
    try:
        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        date_str = ""
        if valuation_date is not None and str(valuation_date).strip() not in ("", "None"):
            date_str = _resolve_valuation_date_for_curve(manager, valuation_date)
        fn = getattr(mgr, "getHistVolFromPriceData", None) or getattr(mgr, "get_hist_vol_from_price_data", None)
        if not callable(fn):
            return "rawmdHistVolFromPriceData: getHistVolFromPriceData not available"
        hv = fn(pt, code, date_str or "", int(sample_num or 252), str(model or "EWMA"))
        if hv is None:
            err = ""
            last_err = getattr(mgr, "lastError", None)
            if callable(last_err):
                err = last_err() or ""
            snap = getattr(manager, "_mdls_snapshot_path", None)
            if snap and _mcp is not None and hasattr(_mcp, "MMarketDataJsonReader"):
                posix = os.path.abspath(str(snap)).replace("\\", "/")
                try:
                    reader = _mcp.MMarketDataJsonReader()
                    if reader.loadFromFile(posix):
                        hv = reader.getHistVolFromPriceData(
                            pt, code, date_str or "", int(sample_num or 252), str(model or "EWMA")
                        )
                except Exception as retry_exc:
                    _log.debug("HistVol JsonReader retry failed: %s", retry_exc)
            if hv is None:
                hint = ""
                if snap:
                    hint = "；CSV 应与快照同目录: " + os.path.dirname(os.path.abspath(str(snap)))
                return f"rawmdHistVolFromPriceData: build failed{(': ' + err) if err else ''}{hint}"
        try:
            from mcp.wrapper import excel_mcp_object_handle
            return excel_mcp_object_handle(hv, "McpHistVols")
        except Exception:
            return hv
    except Exception as e:
        s = f"rawmdHistVolFromPriceData except: {e}"
        _log.warning(s, exc_info=True)
        return s


# ----- rawmdGet*：与 mdlsGet* 命名对称，等价于 rawmdYieldCurve / rawmdYieldCurve2 等 -----


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日；空=最新主索引日")
def rawmdGetYieldCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpYieldCurve@n（同 rawmdYieldCurve）。读数：YieldCurveZeroRate(曲线,日期,...)。"""
    return rawmdYieldCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日；空=最新主索引日")
def rawmdGetYieldCurve2(manager, curve_id: str, valuation_date=None):
    """返回 McpYieldCurve2@n（同 rawmdYieldCurve2）。读数：YieldCurve2ZeroRate(曲线,日期,\"MID\")。"""
    return rawmdYieldCurve2(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetSwapCurve(manager, curve_id: str, valuation_date=None):
    return rawmdSwapCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetBondCurve(manager, curve_id: str, valuation_date=None):
    return rawmdBondCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetCreditCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpCreditCurve@n（同 rawmdCreditCurve）。"""
    return rawmdCreditCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetBondSpreadCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpBondSpreadCurve@n（同 rawmdBondSpreadCurve）。读数：BondSpreadCurveZeroSpread 等。"""
    return rawmdBondSpreadCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetFXForwardPointsCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpFXForwardPointsCurve@n（同 rawmdFXForwardPointsCurve）。读数：FxfpcFXForwardPoints。"""
    return rawmdFXForwardPointsCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetFXForwardPointsCurve2(manager, curve_id: str, valuation_date=None):
    return rawmdFXForwardPointsCurve2(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetFXVolSurface2(manager, curve_id: str, valuation_date=None):
    return rawmdFXVolSurface2(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID，如 EURUSD_LOCALVOL")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetLocalVol(manager, curve_id: str, valuation_date=None):
    """返回 McpLocalVol@n（同 rawmdLocalVol）。读数：LocalVolGetVolatility。"""
    return rawmdLocalVol(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID，如 EQ_FORWARD")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetForwardCurve(manager, curve_id: str, valuation_date=None):
    """返回 McpForwardCurve@n（同 rawmdForwardCurve）。读数：ForwardCurveForwardRate。"""
    return rawmdForwardCurve(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID，如 EQ_VOL_SAMPLE")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetVolSurface(manager, curve_id: str, valuation_date=None):
    """返回 McpVolSurface@n（同 rawmdVolSurface）。读数：VolSurfaceGetVolatility。"""
    return rawmdVolSurface(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager")
@xl_arg("curve_id", "str", "曲线 ID")
@xl_arg("valuation_date", "var", "可选估值日")
def rawmdGetHistVol(manager, curve_id: str, valuation_date=None):
    """返回 McpHistVols@n（同 rawmdHistVol）。读数：HvsGetVol。"""
    return rawmdHistVol(manager, curve_id, valuation_date)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("instrument_code", "str", "instrument_code（与 CSV 中 instrument 列一致）")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
@xl_arg("product_type", "str", "可选；空则按主索引 price_data_index 各节依次尝试（代码通常唯一）")
def rawmdGetPrice(manager, instrument_code: str, valuation_date=None, product_type=None):
    """
    从 price_data_index 配置的 HIST/current CSV 读取价格（与 C++ RawMarketDataManager::getPrice 一致）。
    示例：=rawmdGetPrice(McpRawMarketManager(),\"019547\",) 使用最新日与自动 product_type；
    =rawmdGetPrice(McpRawMarketManager(),\"019547\",A1,\"BOND\") 指定日期与类型。
    """
    if manager is None or isinstance(manager, str):
        return manager if isinstance(manager, str) else "rawmdGetPrice: manager 为空"
    code = (instrument_code or "").strip()
    if not code:
        return "rawmdGetPrice: instrument_code 为空"
    try:
        date_str = _resolve_valuation_date_for_curve(manager, valuation_date)
        if not date_str:
            return "rawmdGetPrice: 无可用估值日（目录下无 MCP_MARKET_DATA_*.json）"
        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        pt = "" if _is_product_type_empty(product_type) else str(product_type).strip()
        gp = getattr(mgr, "getPrice", None)
        if callable(gp):
            r = gp(code, pt, date_str)
            if r is None:
                return "rawmdGetPrice: not found"
            if isinstance(r, float) and math.isnan(r):
                return "rawmdGetPrice: not found"
            if isinstance(r, float):
                return r
            return r
        gpv = getattr(mgr, "get_price", None)
        if callable(gpv):
            r = gpv(code, date_str, pt or None)
            if r is None:
                return "rawmdGetPrice: not found"
            return float(r)
        return "rawmdGetPrice: getPrice not available"
    except Exception as e:
        s = f"rawmdGetPrice except: {e}"
        _log.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
def rawmdLatestValuationDate(manager):
    """
    返回当前市场数据目录下主索引日期的**最大者**（YYYY-MM-DD），与 C++ getLatestAvailableDate 一致。
    示例：=rawmdLatestValuationDate(McpRawMarketManager())
    """
    if manager is None or isinstance(manager, str):
        return manager if isinstance(manager, str) else "rawmdLatestValuationDate: manager 为空"
    try:
        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        d = _manager_get_latest_available_date_from_mgr(mgr)
        if not d:
            return "rawmdLatestValuationDate: no MCP_MARKET_DATA_*.json dates"
        return d
    except Exception as e:
        s = f"rawmdLatestValuationDate except: {e}"
        _log.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_return("var[][]")
def rawmdAvailableDates(manager):
    """
    列出 Manager 目录下可用的主索引日期（YYYY-MM-DD），列向量。
    示例：=rawmdAvailableDates(McpRawMarketManager())
    """
    if manager is None or isinstance(manager, str):
        return [[manager if isinstance(manager, str) else "rawmdAvailableDates: manager 为空"]]
    try:
        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        dates = _manager_get_available_dates(mgr)
        return [[d] for d in dates]
    except Exception as e:
        return [[f"rawmdAvailableDates except: {e}"]]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("market_data_root", "str", "Market data root directory, empty for default")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用目录下最新主索引日")
@xl_return("var[][]")
def rawmdMarketDataSnapshot(market_data_root: str = "", valuation_date=None):
    """
    加载 Raw Market Data 快照摘要（调试）。
    返回多行：首行为 valuation_date；其后每行 [顶层节名, 该节下 curve_id 分号拼接]，覆盖 YieldCurve/SwapCurve/BondCurve/
    CreditCurve/VolSurface/LocalVol/HistVol 等主索引中出现的所有类型。
    示例：=rawmdMarketDataSnapshot() 用默认根目录与最新日；=rawmdMarketDataSnapshot(A1,B1) 指定根目录与估值日
    """
    try:
        _ensure_path()
        root = _resolve_market_data_root(market_data_root)
        valid, err = _is_valid_rawmd_directory(root)
        if not valid:
            return [[err]]
        date_str = _resolve_snapshot_valuation_date(root, valuation_date)
        if not date_str:
            return [["No available valuation dates (no MCP_MARKET_DATA_*.json)"]]
        from excel.raw_market_data import RawMarketDataManager
        py_mgr = RawMarketDataManager(root=root)
        idx = py_mgr.load_daily_index(date_str)
        if idx is None:
            return [[f"Main index file not found: {date_str}"]]
        by_sec = idx.list_curve_ids_by_section()
        rows = [["valuation_date", idx.valuation_date]]
        _priority = (
            "YieldCurve",
            "SwapCurve",
            "BondCurve",
            "CreditCurve",
            "BondSpreadCurve",
            "FXForwardPointsCurve",
            "ForwardCurve",
            "VolSurface",
            "FXVolSurface",
            "LocalVol",
            "HistVol",
        )
        _done = set()
        for k in _priority:
            if k in by_sec:
                rows.append([k, "; ".join(by_sec[k])])
                _done.add(k)
        for k in sorted(by_sec.keys()):
            if k not in _done:
                rows.append([k, "; ".join(by_sec[k])])
        return rows
    except Exception as e:
        return [[f"rawmdMarketDataSnapshot except: {e}"]]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("manager", "object", "McpRawMarketManager 返回的 Manager")
@xl_arg("valuation_date", "var", "可选；日期/文本 YYYY-MM-DD/YYYYMMDD 或 Excel 序列；空则使用最新主索引日")
@xl_arg("sections_csv", "str", "可选；逗号分隔节名，如 FXVolSurface,LocalVol；空则扫描默认关键节")
@xl_return("var[][]")
def rawmdMissingDependencies(manager, valuation_date=None, sections_csv: str = ""):
    """
    一次性扫描并返回“构建失败/依赖缺失”清单。

    示例：
    - =rawmdMissingDependencies(McpRawMarketManager())
    - =rawmdMissingDependencies(McpRawMarketManager(),A1,"CreditCurve,FXVolSurface,LocalVol")
    """
    if manager is None or isinstance(manager, str):
        return [[manager if isinstance(manager, str) else "rawmdMissingDependencies: manager 为空"]]
    try:
        date_str = _resolve_valuation_date_for_curve(manager, valuation_date)
        if not date_str:
            return [["rawmdMissingDependencies: 无可用估值日（目录下无 MCP_MARKET_DATA_*.json）"]]

        sections: Optional[List[str]] = None
        s = (sections_csv or "").strip()
        if s:
            sections = [x.strip() for x in s.split(",") if x.strip()]
            if not sections:
                sections = None

        mgr = manager.getInstance() if hasattr(manager, "getInstance") else manager
        rows = [["valuation_date", date_str], ["section", "curve_id", "message"]]

        issues = None
        fn = getattr(mgr, "getMissingDependencies", None)
        if callable(fn):
            try:
                issues = fn(date_str, sections) if sections is not None else fn(date_str)
            except TypeError:
                issues = fn(date_str)
        if issues is None:
            _ensure_path()
            from excel.raw_market_data import RawMarketDataManager
            root = _resolve_rawmd_root(manager, mgr)
            py_mgr = RawMarketDataManager(root=root, mcp_module=_mcp if _has_mcp else None)
            issues = py_mgr.get_missing_dependencies(date_str, sections)

        if not issues:
            rows.append(["OK", "", "no missing dependencies"])
            return rows

        for it in issues:
            if isinstance(it, dict):
                rows.append([
                    str(it.get("section", "")),
                    str(it.get("curve_id", "")),
                    str(it.get("message", "")),
                ])
            else:
                rows.append(["", "", str(it)])
        return rows
    except Exception as e:
        return [[f"rawmdMissingDependencies except: {e}"]]
