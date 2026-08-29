# -*- coding: utf-8 -*-
"""
Raw Market Data 加载器

从 MCP_MARKET_DATA_YYYYMMDD.json 主索引加载市场数据，构建 MCP 曲线/曲面对象。
对应 RAW_MARKET_DATA_JSON_DESIGN.md 第 14 节设计。

支持：
- RawMarketDataIndex：解析主索引 JSON，提供只读访问
- RawMarketDataLoader：从 JSON 构建 MCP 对象（YieldCurve、SwapCurve 等）
- RawMarketDataManager：目录管理、按 curve_id + 日期查询

参考：NEW_ASSET_CHECKLIST.md、EXCEL_INTEGRATION_PITFALLS.md
"""

from __future__ import absolute_import

import json
import os
import csv
import math
from typing import Any, Dict, List, Optional, Tuple

# 顶层曲线/曲面类型键
_CURVE_KEYS = (
    "SwapCurve", "YieldCurve", "YieldCurve2", "BondCurve",
    "FXForwardPointsCurve", "FXForwardPointsCurve2",
    "ForwardCurve", "VolSurface", "FXVolSurface", "FXVolSurface2",
    "LocalVol", "HistVol",
)

# 主索引 JSON 顶层元数据键（非曲线块）
_RAWMD_INDEX_META_KEYS = frozenset(
    {"valuation_date", "_metadata", "price_data_index", "instrument_classification_index"}
)


def _norm_date(d: str) -> str:
    """将日期统一为 YYYY-MM-DD"""
    if not d:
        return ""
    s = str(d).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def _hist_vol_date_cell_to_yyyymmdd(ds: str) -> str:
    """与 C++ histVolDateCellToYyyymmdd 一致：单元格日期 -> YYYYMMDD，用于与 ReferenceDate 比较。"""
    s = (ds or "").strip()
    if not s:
        return ""
    if len(s) == 8 and s.isdigit():
        return s
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s[:4] + s[5:7] + s[8:10]
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3 and len(parts[0]) == 4:
            try:
                y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
                return f"{y:04d}{mo:02d}{d:02d}"
            except (ValueError, IndexError):
                return ""
    return ""


def _normalize_equity_spot_instrument(s: str) -> str:
    """与 C++ normalizeEquitySpotInstrument 一致：历史 CSV 多为裸代码，索引可能带 .SZ / 000333SZ。"""
    t = (s or "").strip()
    if not t:
        return t
    dot = t.rfind(".")
    if dot != -1 and len(t) == dot + 3:
        suf = t[dot + 1 : dot + 3].upper()
        if suf in ("SZ", "SH", "BJ"):
            return t[:dot]
    if len(t) >= 8:
        suf2 = t[-2:].upper()
        if suf2 in ("SZ", "SH", "BJ"):
            return t[:-2]
    return t


def _yymmdd_to_str(d: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD"""
    return _norm_date(d)


def _read_price_from_hist_csv(
    root: str,
    entry: Dict[str, Any],
    instrument_code: str,
    vd_yyyymmdd: str,
    product_type: Optional[str] = None,
) -> Optional[float]:
    """与 C++ readPriceFromHistCsvEntry 一致：按 instrument + 日期匹配一行价格。"""
    csv_path = (entry.get("current_file") or entry.get("hist_file") or "").strip()
    if not csv_path:
        return None
    full_path = os.path.join(root, csv_path)
    if not os.path.isfile(full_path):
        return None
    date_col = entry.get("date_column", "valuation_date")
    price_col = entry.get("price_column", "close")
    if price_col == "close" and entry.get("price_column"):
        price_col = entry["price_column"]
    inst_col = entry.get("instrument_column", "instrument_code")
    try:
        with open(full_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception:
        return None
    if not rows:
        return None
    headers = [str(h).strip() for h in rows[0]]
    try:
        idx_inst = headers.index(inst_col)
    except ValueError:
        return None
    idx_date = -1
    try:
        idx_date = headers.index(date_col)
    except ValueError:
        pass
    idx_price = -1
    for i, h in enumerate(headers):
        if h == price_col or (price_col == "close" and h == "price"):
            idx_price = i
            break
    if idx_price < 0:
        for i, h in enumerate(headers):
            if h in ("price", "close"):
                idx_price = i
                break
    if idx_price < 0:
        return None
    pt = (product_type or "").strip()
    # 标准化传入的 instrument_code：统一转为大写进行匹配
    instrument_code_upper = instrument_code.strip().upper()
    for cols in rows[1:]:
        if len(cols) <= max(idx_inst, idx_price):
            continue
        row_ic = cols[idx_inst].strip()
        if pt == "EQUITYSPOT":
            if _normalize_equity_spot_instrument(row_ic) != _normalize_equity_spot_instrument(instrument_code):
                continue
        elif row_ic.upper() != instrument_code_upper:
            continue
        if idx_date >= 0 and len(cols) > idx_date:
            d = _hist_vol_date_cell_to_yyyymmdd(cols[idx_date].strip())
            if len(d) != 8 or d != vd_yyyymmdd:
                continue
        try:
            return float(cols[idx_price].strip())
        except (ValueError, IndexError):
            continue
    return None


def _fmt_date_slash_for_mcp(s: Any) -> str:
    """主索引日期 -> M 类常用的 YYYY/MM/DD（与 mcplib StaticParse::Date 一致）。"""
    if s is None:
        return ""
    t = str(s).strip()
    if len(t) == 8 and t.isdigit():
        return f"{t[:4]}/{t[4:6]}/{t[6:8]}"
    if len(t) >= 10 and t[4] == "-" and t[7] == "-":
        return f"{t[:4]}/{t[5:7]}/{t[8:10]}"
    if "/" in t and len(t) >= 10:
        return t.replace("-", "/")[:10]
    return t


def _time_to_tenor(t: Any) -> Optional[str]:
    """将 year fraction（如 0.5, 1, 2）转换为 tenor（如 6M, 1Y, 2Y）。"""
    try:
        x = float(t)
    except Exception:
        return None
    if not math.isfinite(x) or x <= 0:
        return None
    months = int(round(x * 12.0))
    if abs(x * 12.0 - months) < 1e-8 and months > 0:
        if months % 12 == 0:
            return f"{months // 12}Y"
        return f"{months}M"
    days = int(round(x * 365.0))
    if days <= 0:
        return None
    return f"{days}D"


def _option_type_ints_for_vol(opt_list: Any) -> List[int]:
    """Call/Put -> 与 testCompareEquityVol 一致：0=Call, 1=Put。"""
    out: List[int] = []
    if not isinstance(opt_list, list):
        return out
    for x in opt_list:
        if isinstance(x, str):
            u = x.upper()
            if u in ("CALL", "C", "CALLOPTION", "0"):
                out.append(0)
            else:
                out.append(1)
        else:
            out.append(int(x))
    return out


def _smile_interp_int(name: str) -> int:
    n = (name or "CUBICSPLINE").upper()
    if n == "SVI":
        return 1
    return 2  # CUBICSPLINE，与 testCompareEquityVol 一致


def _date_adjuster_int(name: str) -> int:
    n = (name or "Following").strip()
    if n == "ModifiedFollowing":
        return 1
    return 0  # Following


def _calendar_code(cal_name: str) -> str:
    n = cal_name or "China.IB"
    if n in ("China.IB", "China", "CNY", "China.SSE"):
        return "CNY"
    if n in ("UnitedStates", "US", "USD"):
        return "USD"
    return n


def _mcp_handle(obj):
    """部分 SWIG 构造函数只接受底层 void*，这里统一取 handler。"""
    if obj is None:
        return None
    get_handler = getattr(obj, "getHandler", None)
    return get_handler() if callable(get_handler) else obj


def _matrix_spec(rows: Any) -> str:
    """XMatrix 字符串格式：行用分号分隔，列用逗号分隔。"""
    if not isinstance(rows, list):
        return ""
    out = []
    for row in rows:
        if isinstance(row, list):
            out.append(",".join(str(float(x)) for x in row))
        else:
            out.append(str(float(row)))
    return ";".join(out)


def _local_vol_model_int(name: str) -> int:
    n = (name or "Dupire").strip()
    if n == "Heston":
        return 3
    if n == "DupireNLSF":
        return 5
    return 4  # Dupire（与 mcp::LocalVol::Model 一致）


def _hist_vol_model_int(name: str) -> int:
    n = (name or "CLOSE_TO_CLOSE").upper()
    if n == "EWMA":
        return 1
    if n == "LINXIAO":
        return 2
    if n == "RISKMETRICS":
        return 3
    return 0


def _hist_vol_return_int(name: str) -> int:
    n = (name or "LOG_RETURN").upper()
    if n == "RETURN":
        return 0
    return 1  # LOG_RETURN，与 mcp::HistVols::ReturnMethod 一致


def _interpolation_method_int(name: str) -> int:
    n = (name or "LINEARINTERPOLATION").upper()
    if n == "LOGLINEARINTERPOLATION" or n == "LOGLINEAR":
        return 1
    if n == "CUBICSPLINE" or n == "CUBICSPLINES":
        return 2
    return 0


def _frequency_int(name: str) -> int:
    n = str(name or "NoFrequency").upper()
    if n in ("ANNUAL", "ANNUALLY", "1"):
        return 1
    if n in ("SEMIANNUAL", "SEMIANNUALLY", "2"):
        return 2
    if n in ("QUARTERLY", "4"):
        return 4
    if n in ("MONTHLY", "12"):
        return 12
    if n in ("CONTINUOUS",):
        return 366
    if n in ("ONCE", "0"):
        return 0
    return -1


def _interpolated_variable_int(name: str) -> int:
    n = str(name or "SIMPLERATES").upper()
    if n in ("ZERORATES", "ZERO_RATE"):
        return -1
    if n == "CONTINUOUSRATES":
        return 1
    return 0


def _day_counter_int(name: str) -> int:
    n = (name or "Act365Fixed").strip()
    if n == "Act360":
        return 1
    if n == "ActActISDA":
        return 2
    if n == "Thirty360":
        return 3
    return 0


def _local_vol_calc_target_int(name: str) -> int:
    n = (name or "CCY1").strip()
    if n == "FXForward":
        return 1
    if n == "CCY2":
        return 2
    return 0


def _credit_interpolated_variable_int(name: str) -> int:
    """与 mcp::InterpolatedVariable：HAZARDRATES=3, PND=4（mcplib MCreditCurve 注释）。"""
    n = (name or "HAZARDRATES").upper()
    if n in ("PND", "ND"):
        return 4
    return 3


def _cds_valuation_type_int(name: str) -> int:
    n = (name or "JPMISDA").upper()
    if n == "MUREX":
        return 2
    return 1


class RawMarketDataIndex:
    """
    单日主索引的解析与只读访问（对应 RAW_MARKET_DATA_JSON_DESIGN.md 14.2.2）
    不构建 MCP 对象，仅提供 JSON 访问。
    """

    def __init__(self, data: Dict[str, Any], base_path: str = ""):
        self._data = data
        self._base_path = base_path or ""

    @property
    def valuation_date(self) -> str:
        return _yymmdd_to_str(self._data.get("valuation_date", ""))

    @property
    def price_data_index(self) -> Dict[str, Any]:
        return self._data.get("price_data_index", {})

    @property
    def instrument_classification_index(self) -> Dict[str, Any]:
        return self._data.get("instrument_classification_index", {})

    def _get_curve_list(self, key: str) -> List[Dict]:
        val = self._data.get(key)
        # 与 C++ curveTypeToString(HistVol) 及常见草稿 JSON 对齐：部分文件使用顶层键 HistVols
        if val is None and key == "HistVol":
            val = self._data.get("HistVols")
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            return [val] if val.get("curve_id") or key == "SwapCurve" and val.get("SettlementDate") else []
        return []

    @staticmethod
    def _curve_matches_id(curve_obj: Dict[str, Any], curve_id: str) -> bool:
        """Return True if curve_obj's curve_id or any alias equals curve_id."""
        if curve_obj.get("curve_id") == curve_id:
            return True
        # Check aliases / alias / synonyms (mirrors C++ appendAliasList)
        for alias_key in ("aliases", "alias", "synonyms"):
            val = curve_obj.get(alias_key)
            if val is None:
                continue
            if isinstance(val, str):
                if val == curve_id:
                    return True
            elif isinstance(val, list):
                if curve_id in val:
                    return True
        return False

    def has_curve(self, curve_id: str, curve_type: str) -> bool:
        for c in self._get_curve_list(curve_type):
            if self._curve_matches_id(c, curve_id):
                return True
            if curve_type == "SwapCurve" and not c.get("curve_id") and c.get("SettlementDate"):
                return True
        return False

    def get_curve_json(self, curve_id: str, curve_type: str) -> Optional[Dict[str, Any]]:
        for c in self._get_curve_list(curve_type):
            if self._curve_matches_id(c, curve_id):
                return c
            if curve_type == "SwapCurve" and not c.get("curve_id"):
                return c
        return None

    def list_curve_ids(self, curve_type: str) -> List[str]:
        """Return canonical curve_id values; aliases are intentionally excluded."""
        ids = []
        for c in self._get_curve_list(curve_type):
            cid = c.get("curve_id")
            if cid:
                ids.append(cid)
        return ids

    def list_curve_ids_by_section(self) -> Dict[str, List[str]]:
        """
        扫描主索引 JSON 顶层各节（除 valuation_date / _metadata 等），
        返回每节下所有 curve_id。包含 CreditCurve、BondSpreadCurve、VolSurface 等，不仅 YieldCurve/SwapCurve。
        """
        out: Dict[str, List[str]] = {}
        for key in self._data:
            if key in _RAWMD_INDEX_META_KEYS:
                continue
            ids = self.list_curve_ids(key)
            if ids:
                out[key] = ids
        return out


class RawMarketDataLoader:
    """
    从 RAW JSON 构建 MCP 曲线/曲面对象（对应 RAW_MARKET_DATA_JSON_DESIGN.md 14.2.3）
    路径解析相对于 base_path。
    """

    def __init__(self, base_path: str = "", mcp_module=None):
        self._base_path = base_path or ""
        self._mcp = mcp_module
        self._last_error: str = ""

    def _set_last_error(self, message: str) -> None:
        self._last_error = str(message or "").strip()

    def _clear_last_error(self) -> None:
        self._last_error = ""

    def get_last_error(self) -> str:
        return self._last_error

    def _get_mcp(self):
        if self._mcp is not None:
            return self._mcp
        try:
            import mcp.mcp as m
            return m
        except ImportError:
            try:
                import mcp as m
                return m
            except ImportError:
                return None

    def build_yield_curve(self, j: Dict[str, Any]) -> Optional[Any]:
        """从 YieldCurve JSON（Tenors + ZeroRates）构建 MYieldCurve。兼容 Times+ZeroRates。"""
        mcp = self._get_mcp()
        if mcp is None:
            return None
        ref_raw = j.get("referenceDate") or j.get("ReferenceDate") or j.get("SettlementDate", "")
        ref_date = _yymmdd_to_str(ref_raw)
        tenors = j.get("Tenors", [])
        if (not isinstance(tenors, list) or not tenors) and isinstance(j.get("Times"), list):
            tenors = []
            for t in j.get("Times", []):
                tt = _time_to_tenor(t)
                if not tt:
                    tenors = []
                    break
                tenors.append(tt)
        zero_rates = j.get("ZeroRates", [])
        if not ref_date or not tenors or not zero_rates:
            return None
        try:
            # SWIG 构造签名要求 tenors/zeroRates 为 JSON 字符串，method/dayCounter 为 int
            method = _interpolation_method_int(str(j.get("InterpolationMethod", "LINEARINTERPOLATION")))
            day_counter = _day_counter_int(str(j.get("DayCounter", "Act365Fixed")))
            calendar_name = _calendar_code(str(j.get("calendar", "China.IB")))
            value_date = _yymmdd_to_str(j.get("valueDate") or ref_raw)
            tenors_json = json.dumps([str(x) for x in tenors])
            rates_json = json.dumps([float(x) for x in zero_rates])
            cal = mcp.MCalendar(calendar_name)
            return mcp.MYieldCurve(ref_date, tenors_json, rates_json, method, cal, day_counter, value_date)
        except Exception:
            return None

    @staticmethod
    def is_implied_fx_yield_curve_json(j: Dict[str, Any]) -> bool:
        fx = str(j.get("FXForwardPointsCurve") or j.get("fx_forward_points_curve") or "").strip()
        anchor = str(j.get("YieldCurve") or j.get("yield_curve") or "").strip()
        has_ccy2 = "IsCCY2" in j or "isCCY2" in j
        return bool(fx and anchor and has_ccy2)

    def build_implied_yield_curve(
        self, j: Dict[str, Any], index: "RawMarketDataIndex"
    ) -> Optional[Any]:
        """YieldCurve(FXForwardPointsCurve, YieldCurve, IsCCY2, Calendar) — args_def DefMcpYieldCurve 第 3 构造。"""
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        if not self.is_implied_fx_yield_curve_json(j):
            return None
        fx_id = str(j.get("FXForwardPointsCurve") or j.get("fx_forward_points_curve") or "").strip()
        anchor_id = str(j.get("YieldCurve") or j.get("yield_curve") or "").strip()
        is_ccy2 = bool(j.get("IsCCY2", j.get("isCCY2", False)))
        cal_str = str(j.get("Calendar") or j.get("calendar") or "USDCNH").strip()
        try:
            fx = self.resolve_fx_forward_points_curve(index, fx_id)
            if fx is None:
                return None
            anchor, _ = self.resolve_yield_curve(index, anchor_id)
            if anchor is None:
                return None
            cal = mcp.MCalendar(_calendar_code(cal_str))
            imp = mcp.MYieldCurve(
                _mcp_handle(fx),
                _mcp_handle(anchor),
                is_ccy2,
                _mcp_handle(cal),
            )
            # MYieldCurve implied 构造借用 anchor/fx 裸指针；须保持 M 层对象存活至 imp 释放
            try:
                object.__setattr__(imp, "_rawmd_implied_deps", (fx, anchor, cal))
            except Exception:
                pass
            return imp
        except Exception:
            return None

    def build_yield_curve2(self, j: Dict[str, Any]) -> Optional[Any]:
        """从 YieldCurve2 JSON（Tenors + Bid/AskZeroRates）构建 MYieldCurve2。"""
        mcp = self._get_mcp()
        if mcp is None:
            return None
        ref_raw = j.get("ReferenceDate") or j.get("referenceDate", "")
        ref_date = _yymmdd_to_str(ref_raw)
        tenors = j.get("Tenors", [])
        bid_rates = j.get("BidZeroRates", [])
        ask_rates = j.get("AskZeroRates", [])
        if not ref_date or not tenors or len(bid_rates) != len(tenors) or len(ask_rates) != len(tenors):
            return None
        try:
            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            value_date = _yymmdd_to_str(j.get("ValueDate") or j.get("valueDate") or ref_raw)
            return mcp.MYieldCurve2(
                ref_date,
                json.dumps([str(x) for x in tenors]),
                json.dumps([float(x) for x in bid_rates]),
                json.dumps([float(x) for x in ask_rates]),
                _frequency_int(str(j.get("CompoundingFrequency", "NoFrequency"))),
                _interpolated_variable_int(str(j.get("InterpolatedVariable", "SIMPLERATES"))),
                _interpolation_method_int(str(j.get("InterpolationMethod", "LINEARINTERPOLATION"))),
                _mcp_handle(cal),
                _day_counter_int(str(j.get("DayCounter", "Act365Fixed"))),
                value_date,
            )
        except Exception:
            return None

    def _strip_fx_currency_prefix(self, tenor: str) -> str:
        """与 C++ stripFxCurrencyPrefix 对齐：CNYON -> ON。"""
        t = str(tenor or "").strip()
        if len(t) > 3 and t[:3].isalpha() and t[3:].isalnum():
            return t[3:]
        return t

    def resolve_fx_forward_points_curve(
        self, index: Any, curve_id: str
    ) -> Optional[Any]:
        if not curve_id or index is None:
            return None
        j = index.get_curve_json(curve_id, "FXForwardPointsCurve")
        if j is None:
            return None
        return self.build_fx_forward_points_curve(j, index)

    def build_fx_forward_points_curve(
        self, j: Dict[str, Any], index: Optional[Any] = None
    ) -> Optional[Any]:
        """从 FXForwardPointsCurve JSON 构建 MFXForwardPointsCurve（Direct Pair 或 Cross Leg1/Leg2）。"""
        mcp = self._get_mcp()
        if mcp is None:
            return None
        try:
            leg1_id = str(j.get("Leg1") or j.get("leg1") or "").strip()
            leg2_id = str(j.get("Leg2") or j.get("leg2") or "").strip()
            construction = str(j.get("Construction") or j.get("construction") or "").strip()
            is_cross = (bool(leg1_id) and bool(leg2_id)) or construction.lower() == "cross"
            if is_cross:
                if not leg1_id or not leg2_id or index is None:
                    return None
                leg1 = self.resolve_fx_forward_points_curve(index, leg1_id)
                leg2 = self.resolve_fx_forward_points_curve(index, leg2_id)
                if leg1 is None or leg2 is None:
                    return None
                ref_raw = j.get("ReferenceDate") or j.get("referenceDate") or ""
                ref_date = _yymmdd_to_str(ref_raw) if ref_raw else ""
                cross_pair = str(
                    j.get("CrossPair") or j.get("Pair") or j.get("pair") or ""
                )
                scale_factor = float(j.get("ScaleFactor", 0) or 0)
                spot_rate = float(j.get("SpotRate", j.get("FXSpotRate", 0)) or 0)
                cal_str = str(j.get("calendar") or "").strip()
                cal_hdl = None
                if cal_str:
                    cal = mcp.MCalendar(_calendar_code(cal_str))
                    cal_hdl = _mcp_handle(cal)
                return mcp.MFXForwardPointsCurve(
                    _mcp_handle(leg1),
                    _mcp_handle(leg2),
                    cal_hdl,
                    ref_date,
                    cross_pair,
                    scale_factor,
                    spot_rate,
                )

            ref_raw = j.get("ReferenceDate") or j.get("referenceDate") or ""
            ref_date = _yymmdd_to_str(ref_raw)
            tenors_j = j.get("Tenors", [])
            fwd_pts_j = j.get("ForwardPoints", [])
            spot = float(j.get("FXSpotRate", 0) or 0)
            scale_factor = float(j.get("ScaleFactor", 10000) or 10000)
            if not ref_date or not tenors_j or len(fwd_pts_j) != len(tenors_j) or spot <= 0:
                return None

            tenors: List[str] = []
            fwd_pts: List[float] = []
            last_key = ""
            for ti, raw_t in enumerate(tenors_j):
                t = self._strip_fx_currency_prefix(str(raw_t))
                if t == last_key:
                    continue
                last_key = t
                tenors.append(t)
                fwd_pts.append(float(fwd_pts_j[ti]))
            if not tenors:
                return None

            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            method = _interpolation_method_int(
                str(j.get("InterpolationMethod", "LINEARINTERPOLATION"))
            )
            pair_str = str(j.get("Pair") or j.get("pair") or "").strip()
            if pair_str:
                return mcp.MFXForwardPointsCurve(
                    ref_date,
                    json.dumps(tenors),
                    json.dumps(fwd_pts),
                    spot,
                    method,
                    _mcp_handle(cal),
                    pair_str,
                    scale_factor,
                )
            return mcp.MFXForwardPointsCurve(
                ref_date,
                json.dumps(tenors),
                json.dumps(fwd_pts),
                spot,
                method,
                _mcp_handle(cal),
                scale_factor,
            )
        except Exception:
            return None

    def build_fx_forward_points_curve2(self, j: Dict[str, Any]) -> Optional[Any]:
        """从 FXForwardPointsCurve2 JSON 构建 MFXForwardPointsCurve2。"""
        mcp = self._get_mcp()
        if mcp is None:
            return None
        ref_raw = j.get("ReferenceDate") or j.get("referenceDate", "")
        ref_date = _yymmdd_to_str(ref_raw)
        tenors = j.get("Tenors", [])
        bid_points = j.get("BidForwardPoints", [])
        ask_points = j.get("AskForwardPoints", [])
        if (not ref_date or not tenors or len(bid_points) != len(tenors)
                or len(ask_points) != len(tenors)):
            return None
        try:
            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            pair = str(j.get("Pair", j.get("pair", "USD/CNY")))
            scale_factor = float(j.get("ScaleFactor", 0) or 0)
            quote_unit = float(j.get("QuoteUnit", 0) or 0)
            args = [
                ref_date,
                float(j.get("BidFXSpotRate", 0.0)),
                json.dumps([float(x) for x in bid_points]),
                float(j.get("AskFXSpotRate", 0.0)),
                json.dumps([float(x) for x in ask_points]),
                json.dumps([str(x) for x in tenors]),
                _interpolation_method_int(str(j.get("InterpolationMethod", "LINEARINTERPOLATION"))),
                _mcp_handle(cal),
                pair,
            ]
            try:
                return mcp.MFXForwardPointsCurve2(*args, scale_factor, quote_unit)
            except TypeError:
                return mcp.MFXForwardPointsCurve2(*args)
        except Exception:
            return None

    def build_swap_curve_from_json(self, j: Dict[str, Any]) -> Optional[Any]:
        """若 JSON 为 fromJson 可用的序列化格式，则使用 fromJson"""
        mcp = self._get_mcp()
        if mcp is None:
            return None
        try:
            s = json.dumps(j) if isinstance(j, dict) else str(j)
            return mcp.MSwapCurve.fromJson(s)
        except Exception:
            return None

    def build_forward_curve(self, j: Dict[str, Any]) -> Optional[Any]:
        mcp = self._get_mcp()
        if mcp is None:
            return None
        try:
            return mcp.MForwardCurve.fromJson(json.dumps(j))
        except Exception:
            return None

    def resolve_yield_curve(self, index: "RawMarketDataIndex", curve_id: str) -> Tuple[Optional[Any], Optional[str]]:
        """按 YieldCurve -> BondCurve -> SwapCurve 顺序解析收益率曲线引用。"""
        if index is None:
            return None, None
        cid = str(curve_id or "").strip()
        if not cid:
            return None, None
        for sec in ("YieldCurve", "BondCurve", "SwapCurve"):
            yj = index.get_curve_json(cid, sec)
            if yj is None:
                continue
            yc = self.build_curve(sec, yj, index)
            if yc is not None:
                return yc, sec
        return None, None

    def build_credit_curve_structural(
        self, j: Dict[str, Any], index: "RawMarketDataIndex"
    ) -> Optional[Any]:
        """
        与 C++ RawMarketDataLoader::buildCreditCurve 一致（data_source=spreads + yield_curve + Tenors/Spreads）。
        Python 绑定中 MCreditCurve 无 fromJson，须走 CFETS 风格构造函数。
        """
        self._clear_last_error()
        mcp = self._get_mcp()
        if mcp is None:
            self._set_last_error("mcp 模块未加载")
            return None
        if index is None:
            self._set_last_error("RawMarketDataIndex 为空")
            return None
        try:
            curve_id = str(j.get("curve_id", "") or "").strip()
            ds = str(j.get("data_source", "spreads")).strip()
            if ds != "spreads":
                self._set_last_error(f"仅支持 data_source=spreads，当前为 {ds or '(empty)'}")
                return None
            ref_str = j.get("referenceDate") or j.get("ReferenceDate", "")
            if not ref_str:
                self._set_last_error("缺少 referenceDate/ReferenceDate")
                return None
            ref_fmt = _fmt_date_slash_for_mcp(ref_str)
            yc_id = str(j.get("yield_curve", "")).strip()
            if not yc_id:
                self._set_last_error("缺少 yield_curve")
                return None
            yc, yc_sec = self.resolve_yield_curve(index, yc_id)
            if yc is None:
                self._set_last_error(
                    f"yield_curve={yc_id} 在 YieldCurve/BondCurve/SwapCurve 节均未找到"
                )
                return None
            tenors = j.get("Tenors", [])
            spreads = j.get("Spreads", [])
            if not isinstance(tenors, list) or not isinstance(spreads, list):
                self._set_last_error("Tenors/Spreads 不是数组")
                return None
            if not tenors or len(spreads) != len(tenors):
                self._set_last_error(
                    f"Tenors/Spreads 长度不一致或为空 (n_tenor={len(tenors) if isinstance(tenors, list) else '?'}, "
                    f"n_spread={len(spreads) if isinstance(spreads, list) else '?'})"
                )
                return None
            spreads_map = {str(tenors[i]): float(spreads[i]) for i in range(len(tenors))}
            cfts_json = json.dumps(spreads_map)
            recovery = float(j.get("RecoveryRate", 0.40))
            var = _credit_interpolated_variable_int(str(j.get("InterpolatedVariable", "HAZARDRATES")))
            method = _interpolation_method_int(str(j.get("InterpolationMethod", "LINEARINTERPOLATION")))
            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            # Python 绑定通常暴露 7 参构造：
            # MCreditCurve(referenceDate, cftsSpreads, yieldCurve, recoveryRate, variable, method, calendar)
            # DayCounter / CDSValuationType 由底层默认处理。
            out = mcp.MCreditCurve(
                ref_fmt,
                cfts_json,
                yc,
                recovery,
                var,
                method,
                cal,
            )
            self._clear_last_error()
            return out
        except Exception as e:
            raw_msg = str(e) if str(e) else type(e).__name__
            detail = (
                f"MCreditCurve 构建异常: {raw_msg}; "
                f"curve_id={curve_id or '(empty)'}, referenceDate={ref_str}, "
                f"yield_curve={yc_id}, section={yc_sec or 'N/A'}, "
                f"tenor_count={len(tenors) if isinstance(tenors, list) else '?'}, "
                f"spread_count={len(spreads) if isinstance(spreads, list) else '?'}"
            )
            if "Newton: can not calibrate" in raw_msg:
                detail += "；提示：这是数值校准不收敛，不是 JSON 结构缺字段。可尝试相邻估值日或检查该日曲线/利差组合。"
            self._set_last_error(detail)
            return None

    def build_vol_surface_structural(self, j: Dict[str, Any], index: "RawMarketDataIndex") -> Optional[Any]:
        """
        与 C++ RawMarketDataLoader::buildVolSurface 一致：
        支持股指、收益率+远期、固定利率+远期三种 MVolSurface 强类型构造。
        Python 绑定中 MVolSurface 无 fromJson，必须用此路径。
        """
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        try:
            ref_str = j.get("ReferenceDate") or j.get("referenceDate", "")
            if not ref_str:
                return None
            ref_fmt = _fmt_date_slash_for_mcp(ref_str)
            exp_j = j.get("ExpiryDates", [])
            opt_j = j.get("OptionTypes", [])
            strikes_j = j.get("Strikes", [])
            prem_j = j.get("Premiums", [])
            if not exp_j or len(opt_j) != len(strikes_j) or len(strikes_j) != len(prem_j):
                return None
            if len(exp_j) != len(strikes_j):
                if len(exp_j) <= 0 or len(strikes_j) % len(exp_j) != 0:
                    return None
                # 兼容常见布局：ExpiryDates 为分组轴，OptionTypes/Strikes/Premiums 为展开明细轴
                repeat_n = len(strikes_j) // len(exp_j)
                exp_j = [d for d in exp_j for _ in range(repeat_n)]
            expiry_fmt = [_fmt_date_slash_for_mcp(x) for x in exp_j]
            opt_ints = _option_type_ints_for_vol(opt_j)
            rf_id = str(j.get("risk_free_rate_curve", "") or "").strip()
            fwd_id = str(j.get("forward_curve", "") or "").strip()
            has_spot = j.get("Spot") is not None
            has_spot_px = j.get("SpotPx") is not None
            has_dividend = j.get("Dividend") is not None
            has_rf_scalar = j.get("RiskFreeRate") is not None
            smile = _smile_interp_int(str(j.get("SmileInterpolation", j.get("SmileInterp", "CUBICSPLINE"))))
            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            d_adj = _date_adjuster_int(str(j.get("DateAdjusterRule", j.get("dateAdjusterRule", "Following"))))
            spot_raw = j.get("SpotDate", ref_str)
            spot_fmt = _fmt_date_slash_for_mcp(spot_raw)
            imp = j.get("ImpVols", [])
            imp_str = json.dumps([float(x) for x in imp]) if isinstance(imp, list) else "[]"
            mini = int(j.get("MiniStrikeSize", j.get("miniStrikeSize", 3)))
            using_imp = bool(j.get("UsingImpVols", j.get("usingImpVols", False)))
            expiry_json = json.dumps(expiry_fmt)
            opt_json = json.dumps(opt_ints)
            strikes_json = json.dumps([float(x) for x in strikes_j])
            prem_json = json.dumps([float(x) for x in prem_j])

            # 1) 股指：risk_free_rate_curve + (Spot|SpotPx) + Dividend，且不带 forward_curve
            if rf_id and has_dividend and (has_spot or has_spot_px) and not fwd_id:
                yc, _ = self.resolve_yield_curve(index, rf_id)
                if yc is None:
                    return None
                spot = float(j.get("Spot", j.get("SpotPx", 0.0)))
                dividend = float(j.get("Dividend", 0.0))
                return mcp.MVolSurface(
                    ref_fmt,
                    spot,
                    expiry_json,
                    opt_json,
                    strikes_json,
                    prem_json,
                    yc,
                    dividend,
                    smile,
                    cal,
                    d_adj,
                    spot_fmt,
                    imp_str,
                    mini,
                    using_imp,
                )

            # 2) 收益率曲线 + 远期曲线
            if rf_id and fwd_id and not has_rf_scalar:
                yc, _ = self.resolve_yield_curve(index, rf_id)
                fwd_json = index.get_curve_json(fwd_id, "ForwardCurve")
                if yc is None or fwd_json is None:
                    return None
                fwd_curve = self.build_forward_curve(fwd_json)
                if fwd_curve is None:
                    return None
                return mcp.MVolSurface(
                    ref_fmt,
                    expiry_json,
                    opt_json,
                    strikes_json,
                    prem_json,
                    yc,
                    fwd_curve,
                    smile,
                    cal,
                    d_adj,
                    spot_fmt,
                    imp_str,
                    mini,
                    using_imp,
                )

            # 3) 固定利率 + 远期曲线
            if has_rf_scalar and fwd_id:
                fwd_json = index.get_curve_json(fwd_id, "ForwardCurve")
                if fwd_json is None:
                    return None
                fwd_curve = self.build_forward_curve(fwd_json)
                if fwd_curve is None:
                    return None
                risk_free = float(j.get("RiskFreeRate", 0.0))
                return mcp.MVolSurface(
                    ref_fmt,
                    expiry_json,
                    opt_json,
                    strikes_json,
                    prem_json,
                    risk_free,
                    fwd_curve,
                    smile,
                    cal,
                    d_adj,
                    spot_fmt,
                    imp_str,
                    mini,
                    using_imp,
                )
            return None
        except Exception:
            return None

    def build_fx_vol_surface_structural(self, j: Dict[str, Any], index: "RawMarketDataIndex") -> Optional[Any]:
        """
        FXVolSurface 结构化构建：
        先按引用解析 foreign/domestic_rate_curve，再走 MFXVolSurface 强类型构造（避免 fromJson 对字符串引用失败）。
        """
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        try:
            ref_str = j.get("ReferenceDate") or j.get("referenceDate", "")
            if not ref_str:
                return None
            ref_fmt = _fmt_date_slash_for_mcp(ref_str)
            spot = float(j.get("Spot", 0.0))
            if spot <= 0.0:
                return None

            tenors = j.get("Tenors", [])
            deltas = j.get("DeltaStrings", [])
            vols = j.get("Volatilities", [])
            if (not isinstance(tenors, list) or not isinstance(deltas, list) or not isinstance(vols, list) or
                    not tenors or not deltas or not vols):
                return None

            frn_id = str(j.get("foreign_rate_curve", "")).strip()
            dom_id = str(j.get("domestic_rate_curve", "")).strip()
            if not frn_id or not dom_id:
                return None
            frn, _ = self.resolve_yield_curve(index, frn_id)
            dom, _ = self.resolve_yield_curve(index, dom_id)
            if frn is None or dom is None:
                return None

            fxp_id = str(j.get("fx_forward_points_curve", "")).strip()
            fxp_json = index.get_curve_json(fxp_id, "FXForwardPointsCurve") if fxp_id else None
            fxp = self.build_curve("FXForwardPointsCurve", fxp_json) if fxp_json is not None else None
            if fxp is None:
                try:
                    fxp = mcp.MFXForwardPointsCurve()
                except Exception:
                    return None

            # 优先尝试 fromJson：先把字符串引用替换成内嵌对象，避免 "cannot use value() with string"。
            try:
                j2 = dict(j)
                j2["foreign_rate_curve"] = json.loads(frn.toJson()) if hasattr(frn, "toJson") else j2.get("foreign_rate_curve")
                j2["domestic_rate_curve"] = json.loads(dom.toJson()) if hasattr(dom, "toJson") else j2.get("domestic_rate_curve")
                if hasattr(fxp, "toJson"):
                    j2["fx_forward_points_curve"] = json.loads(fxp.toJson())
                r = mcp.MFXVolSurface.fromJson(json.dumps(j2))
                if r is not None:
                    return r
            except Exception:
                pass

            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            d_adj = _date_adjuster_int(str(j.get("DateAdjusterRule", "ModifiedFollowing")))
            smile = _smile_interp_int(str(j.get("SmileInterpolation", "CUBICSPLINE")))
            spot_dt = _fmt_date_slash_for_mcp(j.get("SpotDate", ref_str))
            calc_target = _local_vol_calc_target_int(str(j.get("CalculatedTarget", "CCY1")))
            pair = str(j.get("Pair", "USD/CNY"))
            premium_adjusted = bool(j.get("PremiumAdjusted", True))
            # 与 C++ Raw loader 对齐：FORWARD_DELTA
            delta_type = 0

            return mcp.MFXVolSurface(
                ref_fmt,
                spot,
                json.dumps(tenors),
                json.dumps(deltas),
                json.dumps(vols),
                frn,
                dom,
                cal,
                d_adj,
                delta_type,
                smile,
                fxp,
                premium_adjusted,
                False,
                spot_dt,
                calc_target,
                pair,
                0,
            )
        except Exception:
            return None

    def build_fx_vol_surface2_structural(self, j: Dict[str, Any], index: "RawMarketDataIndex") -> Optional[Any]:
        """FXVolSurface2 结构化构建：解析 *2 依赖后走 MFXVolSurface2 强类型构造。"""
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        try:
            ref_str = j.get("ReferenceDate") or j.get("referenceDate", "")
            if not ref_str:
                return None
            tenors = j.get("Tenors", [])
            deltas = j.get("DeltaStrings", [])
            bid_vols = j.get("BidVolatilities", [])
            ask_vols = j.get("AskVolatilities", [])
            if (not isinstance(tenors, list) or not isinstance(deltas, list) or
                    not isinstance(bid_vols, list) or not isinstance(ask_vols, list) or
                    not tenors or not deltas or len(bid_vols) != len(tenors) or len(ask_vols) != len(tenors)):
                return None

            fxp_id = str(j.get("fx_forward_points_curve2", "") or "").strip()
            frn_id = str(j.get("foreign_rate_curve2", "") or "").strip()
            dom_id = str(j.get("domestic_rate_curve2", "") or "").strip()
            fxp_json = index.get_curve_json(fxp_id, "FXForwardPointsCurve2") if fxp_id else None
            frn_json = index.get_curve_json(frn_id, "YieldCurve2") if frn_id else None
            dom_json = index.get_curve_json(dom_id, "YieldCurve2") if dom_id else None
            if fxp_json is None or frn_json is None or dom_json is None:
                return None

            fxp = self.build_fx_forward_points_curve2(fxp_json)
            frn = self.build_yield_curve2(frn_json)
            dom = self.build_yield_curve2(dom_json)
            if fxp is None or frn is None or dom is None:
                return None

            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            d_adj = _date_adjuster_int(str(j.get("DateAdjusterRule", "ModifiedFollowing")))
            smile = _smile_interp_int(str(j.get("SmileInterpolation", "CUBICSPLINE")))
            spot_dt = _fmt_date_slash_for_mcp(j.get("SpotDate", ref_str))
            calc_target = _local_vol_calc_target_int(str(j.get("CalculatedTarget", "CCY1")))
            pair = str(j.get("Pair", j.get("pair", "USD/CNY")))
            premium_adjusted = bool(j.get("PremiumAdjusted", j.get("premiumAdjusted", True)))
            delta_types = j.get("DeltaTypes") or ["FORWARD_DELTA"] * len(tenors)
            atm_types = j.get("ATMVolTypes") or ["FORWARD_STRIKE"] * len(tenors)

            return mcp.MFXVolSurface2(
                _fmt_date_slash_for_mcp(ref_str),
                json.dumps([str(x) for x in tenors]),
                json.dumps([str(x) for x in deltas]),
                _matrix_spec(bid_vols),
                _matrix_spec(ask_vols),
                fxp,
                frn,
                dom,
                calc_target,
                smile,
                json.dumps(delta_types),
                json.dumps(atm_types),
                cal,
                d_adj,
                premium_adjusted,
                spot_dt,
                pair,
                3,
            )
        except Exception:
            return None

    def build_hist_vol_structural(self, j: Dict[str, Any], index: "RawMarketDataIndex") -> Optional[Any]:
        """与 C++ buildHistVol 一致：读 price_data_index CSV，再 MHistVols（无 fromJson）。"""
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        try:
            label = j.get("label") or j.get("curve_id", "")
            ref_str = j.get("ReferenceDate") or j.get("referenceDate", "")
            if not label or not ref_str:
                return None
            ref_fmt = _fmt_date_slash_for_mcp(ref_str)
            ref_ymd = ref_str.replace("-", "").strip()[:8]
            if len(ref_ymd) != 8:
                return None
            ref_j = j.get("price_data_ref")
            if not isinstance(ref_j, dict):
                return None
            product_type = str(ref_j.get("product_type", "")).strip()
            instrument_code = str(ref_j.get("instrument_code", "")).strip()
            if not product_type or not instrument_code:
                return None
            pidx = index.price_data_index
            if not isinstance(pidx, dict) or product_type not in pidx:
                return None
            entry = pidx.get(product_type)
            if not isinstance(entry, dict):
                return None
            hist_file = str(entry.get("hist_file", "") or "").strip()
            if not hist_file:
                return None
            full_path = os.path.join(self._base_path, hist_file)
            if not os.path.isfile(full_path):
                return None
            inst_col = ref_j.get("instrument_column", "instrument_code")
            date_col = ref_j.get("date_column", "valuation_date")
            price_col = ref_j.get("price_column", "close")
            if price_col == "close" and entry.get("price_column"):
                price_col = entry["price_column"]
            rows: List[List[str]] = []
            with open(full_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            if len(rows) < 2:
                return None
            headers = [str(h).strip() for h in rows[0]]
            try:
                idx_inst = headers.index(inst_col)
            except ValueError:
                return None
            idx_date = -1
            try:
                idx_date = headers.index(date_col)
            except ValueError:
                pass
            idx_price = -1
            for i, h in enumerate(headers):
                if h == price_col or (price_col == "close" and h == "price"):
                    idx_price = i
                    break
            if idx_price < 0:
                return None
            matched: List[Tuple[str, float]] = []
            # 标准化传入的 instrument_code：统一转为大写进行匹配
            instrument_code_upper = instrument_code.strip().upper()
            for cols in rows[1:]:
                if len(cols) <= max(idx_inst, idx_price):
                    continue
                row_ic = cols[idx_inst].strip()
                if product_type == "EQUITYSPOT":
                    if _normalize_equity_spot_instrument(row_ic) != _normalize_equity_spot_instrument(instrument_code):
                        continue
                elif row_ic.upper() != instrument_code_upper:
                    continue
                ds_raw = ""
                if idx_date >= 0 and len(cols) > idx_date:
                    ds_raw = cols[idx_date].strip()
                ds_y = _hist_vol_date_cell_to_yyyymmdd(ds_raw)
                if len(ds_y) != 8:
                    continue
                if ds_y > ref_ymd:
                    continue
                try:
                    pr = float(cols[idx_price].strip())
                except (ValueError, IndexError):
                    continue
                matched.append((ds_y, pr))
            matched.sort(key=lambda x: x[0])
            sample_num = int(j.get("SampleNum", 100))
            if sample_num <= 0:
                sample_num = 100
            start = max(0, len(matched) - sample_num) if len(matched) > sample_num else 0
            sel = matched[start:]
            if not sel:
                return None
            dates_out: List[str] = []
            quotes_out: List[float] = []
            for ds_y, pr in sel:
                d_slash = f"{ds_y[:4]}/{ds_y[4:6]}/{ds_y[6:8]}"
                dates_out.append(d_slash)
                quotes_out.append(pr)
            dates_str = json.dumps(dates_out)
            quotes_str = json.dumps(quotes_out)
            periods = long(sample_num)  # type: ignore
            try:
                periods = int(sample_num)
            except Exception:
                periods = 100
            model = _hist_vol_model_int(str(j.get("Model", "CLOSE_TO_CLOSE")))
            ret_m = _hist_vol_return_int(str(j.get("ReturnMethod", "LOG_RETURN")))
            ann = float(j.get("AnnualFactor", 252.0))
            lam = float(j.get("Lamda", 0.94))
            interp = _interpolation_method_int(str(j.get("InterpolationMethod", "LINEARINTERPOLATION")))
            dc = _day_counter_int(str(j.get("DayCounter", "Act365Fixed")))
            return mcp.MHistVols(
                str(label),
                ref_fmt,
                dates_str,
                quotes_str,
                periods,
                model,
                ret_m,
                ann,
                lam,
                interp,
                dc,
            )
        except Exception:
            return None

    def build_local_vol_structural(self, j: Dict[str, Any], index: "RawMarketDataIndex") -> Optional[Any]:
        """与 C++ buildLocalVol 分支一致；Python 绑定无 MLocalVol.fromJson。"""
        mcp = self._get_mcp()
        if mcp is None or index is None:
            return None
        try:
            ref_str = j.get("ReferenceDate") or j.get("referenceDate", "")
            if not ref_str:
                return None
            ref_fmt = _fmt_date_slash_for_mcp(ref_str)
            exp_j = j.get("ExpiryDates", [])
            opt_j = j.get("OptionTypes", [])
            strikes_j = j.get("Strikes", [])
            prem_j = j.get("Premiums", [])
            if not exp_j or len(opt_j) != len(strikes_j) or len(strikes_j) != len(prem_j):
                return None
            if len(exp_j) != len(strikes_j):
                if len(exp_j) <= 0 or len(strikes_j) % len(exp_j) != 0:
                    return None
                repeat_n = len(strikes_j) // len(exp_j)
                exp_j = [d for d in exp_j for _ in range(repeat_n)]
            exp_s = json.dumps([_fmt_date_slash_for_mcp(x) for x in exp_j])
            opt_s = json.dumps(_option_type_ints_for_vol(opt_j))
            strikes_s = json.dumps([float(x) for x in strikes_j])
            prem_s = json.dumps([float(x) for x in prem_j])
            imp = j.get("ImpVols", [])
            imp_s = json.dumps([float(x) for x in imp]) if isinstance(imp, list) else "[]"
            mini = int(j.get("MiniStrikeSize", 3))
            using_imp = bool(j.get("UsingImpVols", True))
            spot_dt = _fmt_date_slash_for_mcp(j.get("SpotDate", ref_str))
            cal = mcp.MCalendar(_calendar_code(str(j.get("calendar", "China.IB"))))
            d_adj = _date_adjuster_int(str(j.get("DateAdjusterRule", "Following")))
            lv_model = _local_vol_model_int(str(j.get("Model", "Dupire")))
            log_level = 0
            trace_file = str(j.get("TraceFile", "") or "")
            lower_g = str(j.get("LowerGuessParams", "[]"))
            upper_g = str(j.get("UpperGuessParams", "[]"))

            # 1) 股指：Spot + Dividend + risk_free_rate_curve
            if j.get("Spot") is not None and "Dividend" in j and j.get("risk_free_rate_curve"):
                ycid = str(j.get("risk_free_rate_curve", "")).strip()
                yc, _ = self.resolve_yield_curve(index, ycid)
                if yc is None:
                    return None
                return mcp.MLocalVol(
                    ref_fmt,
                    float(j.get("Spot", 0.0)),
                    exp_s,
                    opt_s,
                    strikes_s,
                    prem_s,
                    yc,
                    float(j.get("Dividend", 0.0)),
                    lv_model,
                    log_level,
                    trace_file,
                    cal,
                    d_adj,
                    spot_dt,
                    imp_s,
                    mini,
                    using_imp,
                    bool(j.get("UsingImpDividend", False)),
                    lower_g,
                    upper_g,
                )

            # 2) Forex
            if j.get("domestic_rate_curve") and j.get("foreign_rate_curve") and j.get("fx_forward_points_curve"):
                dom_id = str(j.get("domestic_rate_curve", "")).strip()
                frn_id = str(j.get("foreign_rate_curve", "")).strip()
                fxj = index.get_curve_json(str(j.get("fx_forward_points_curve")), "FXForwardPointsCurve")
                if fxj is None:
                    return None
                dom, _ = self.resolve_yield_curve(index, dom_id)
                frn, _ = self.resolve_yield_curve(index, frn_id)
                fxp = self.build_curve("FXForwardPointsCurve", fxj)
                if dom is None or frn is None or fxp is None:
                    return None
                ct = _local_vol_calc_target_int(str(j.get("CalculatedTarget", "CCY1")))
                return mcp.MLocalVol(
                    ref_fmt,
                    float(j.get("Spot", 0.0)),
                    exp_s,
                    opt_s,
                    strikes_s,
                    prem_s,
                    bool(j.get("PremiumAdjusted", True)),
                    dom,
                    frn,
                    fxp,
                    ct,
                    lv_model,
                    log_level,
                    trace_file,
                    cal,
                    d_adj,
                    spot_dt,
                    imp_s,
                    mini,
                    using_imp,
                    lower_g,
                    upper_g,
                )

            # 3) YieldCurve + ForwardCurve（无 RiskFreeRate 标量）
            if (
                j.get("risk_free_rate_curve")
                and j.get("forward_curve")
                and "RiskFreeRate" not in j
            ):
                ycid = str(j.get("risk_free_rate_curve", "")).strip()
                fcid = str(j.get("forward_curve", "")).strip()
                fj = index.get_curve_json(fcid, "ForwardCurve") if fcid else None
                if fj is None:
                    return None
                yc, _ = self.resolve_yield_curve(index, ycid)
                fc = self.build_forward_curve(fj)
                if yc is None or fc is None:
                    return None
                return mcp.MLocalVol(
                    ref_fmt,
                    exp_s,
                    opt_s,
                    strikes_s,
                    prem_s,
                    yc,
                    fc,
                    lv_model,
                    log_level,
                    trace_file,
                    cal,
                    d_adj,
                    spot_dt,
                    imp_s,
                    mini,
                    using_imp,
                    lower_g,
                    upper_g,
                )

            # 4) 期货：固定利率 + ForwardCurve
            if j.get("RiskFreeRate") is not None and j.get("forward_curve"):
                fcid = str(j.get("forward_curve", "")).strip()
                fj = index.get_curve_json(fcid, "ForwardCurve") if fcid else None
                if fj is None:
                    return None
                fc = self.build_forward_curve(fj)
                if fc is None:
                    return None
                return mcp.MLocalVol(
                    ref_fmt,
                    0.0,
                    exp_s,
                    opt_s,
                    strikes_s,
                    prem_s,
                    float(j.get("RiskFreeRate", 0.0)),
                    fc,
                    lv_model,
                    log_level,
                    trace_file,
                    cal,
                    d_adj,
                    spot_dt,
                    imp_s,
                    mini,
                    using_imp,
                    lower_g,
                    upper_g,
                )
            return None
        except Exception:
            return None

    def build_curve(self, curve_type: str, j: Dict[str, Any], index: Optional[Any] = None) -> Optional[Any]:
        """根据类型构建曲线/曲面；VolSurface/FXVolSurface/LocalVol/HistVol 与 C++ 一致走结构化构造。"""
        if curve_type == "YieldCurve":
            if index is not None and self.is_implied_fx_yield_curve_json(j):
                return self.build_implied_yield_curve(j, index)
            return self.build_yield_curve(j)
        if curve_type == "YieldCurve2":
            return self.build_yield_curve2(j)
        if curve_type == "SwapCurve":
            return self.build_swap_curve_from_json(j)
        if curve_type == "VolSurface":
            if index is None:
                return None
            return self.build_vol_surface_structural(j, index)
        if curve_type == "LocalVol":
            if index is None:
                return None
            return self.build_local_vol_structural(j, index)
        if curve_type == "FXVolSurface":
            if index is None:
                return None
            return self.build_fx_vol_surface_structural(j, index)
        if curve_type == "FXVolSurface2":
            if index is None:
                return None
            return self.build_fx_vol_surface2_structural(j, index)
        if curve_type == "HistVol":
            if index is None:
                return None
            return self.build_hist_vol_structural(j, index)
        if curve_type == "CreditCurve":
            if index is None:
                return None
            return self.build_credit_curve_structural(j, index)
        if curve_type == "FXForwardPointsCurve2":
            return self.build_fx_forward_points_curve2(j)
        if curve_type == "FXForwardPointsCurve":
            return self.build_fx_forward_points_curve(j, index)
        mcp = self._get_mcp()
        if mcp is None:
            return None
        try:
            s = json.dumps(j) if isinstance(j, dict) else str(j)
            from_json = [
                ("BondCurve", "MBondCurve"),
                ("BondSpreadCurve", "MBondSpreadCurve"),
                ("FXForwardPointsCurve", "MFXForwardPointsCurve"),
                ("FXForwardPointsCurve2", "MFXForwardPointsCurve2"),
                ("ForwardCurve", "MForwardCurve"),
                ("FXVolSurface", "MFXVolSurface"),
            ]
            for key, cls_name in from_json:
                if curve_type == key:
                    cls = getattr(mcp, cls_name, None)
                    if cls is not None and hasattr(cls, "fromJson"):
                        return cls.fromJson(s)
                    return None
        except Exception:
            pass
        return None

    def build_curve_explain(
        self, curve_type: str, j: Dict[str, Any], index: Optional[Any] = None
    ) -> Optional[str]:
        """
        与 build_curve 同源，但返回失败原因：成功返回 None，失败返回短字符串（供 Excel 展示）。
        build_curve 内部吞掉异常时，此处会显式捕获 fromJson / 构造异常。
        """
        if not isinstance(j, dict):
            return "条目不是 JSON 对象"
        if curve_type == "YieldCurve":
            if index is not None and self.is_implied_fx_yield_curve_json(j):
                fx_id = str(j.get("FXForwardPointsCurve") or j.get("fx_forward_points_curve") or "").strip()
                anchor_id = str(j.get("YieldCurve") or j.get("yield_curve") or "").strip()
                if "IsCCY2" not in j and "isCCY2" not in j:
                    return "Implied YieldCurve 缺少 IsCCY2 (bool)"
                if not isinstance(j.get("IsCCY2", j.get("isCCY2")), bool):
                    return "Implied YieldCurve: IsCCY2 必须为 boolean"
                if not fx_id:
                    return "Implied YieldCurve 缺少 FXForwardPointsCurve"
                if not anchor_id:
                    return "Implied YieldCurve 缺少 YieldCurve (anchor)"
                if index.get_curve_json(fx_id, "FXForwardPointsCurve") is None:
                    return f"FXForwardPointsCurve={fx_id} 未找到"
                anchor_obj, anchor_sec = self.resolve_yield_curve(index, anchor_id)
                if anchor_obj is None:
                    return f"anchor YieldCurve={anchor_id} 在 YieldCurve/BondCurve/SwapCurve 节均未找到"
                try:
                    r = self.build_implied_yield_curve(j, index)
                    if r is None:
                        return (
                            f"MYieldCurve implied 构造返回 None（fx={fx_id}, anchor={anchor_id}, "
                            f"section={anchor_sec}）；请确认 MCP 已重新编译 MYieldCurve implied 构造"
                        )
                    return None
                except Exception as e:
                    return str(e)
            ref_date = _yymmdd_to_str(j.get("referenceDate", ""))
            tenors = j.get("Tenors", [])
            zero_rates = j.get("ZeroRates", [])
            if not ref_date or not tenors or not zero_rates:
                return (
                    f"缺少 referenceDate/Tenors/ZeroRates 或为空 "
                    f"(ref={bool(ref_date)}, n_tenor={len(tenors) if isinstance(tenors, list) else '?'}, "
                    f"n_zero={len(zero_rates) if isinstance(zero_rates, list) else '?'})"
                )
            try:
                r = self.build_yield_curve(j)
                return None if r is not None else "MYieldCurve 构造返回 None"
            except Exception as e:
                return str(e)
        if curve_type == "SwapCurve":
            mcp = self._get_mcp()
            if mcp is None:
                return "mcp 模块未加载"
            try:
                s = json.dumps(j)
                r = mcp.MSwapCurve.fromJson(s)
                if r is None:
                    return "MSwapCurve.fromJson 返回 None"
                return None
            except Exception as e:
                return str(e)
        if curve_type == "CreditCurve":
            if index is None:
                return "缺少日索引 RawMarketDataIndex（CreditCurve 需结构化构建）"
            ds = str(j.get("data_source", "spreads")).strip()
            if ds != "spreads":
                return f"CreditCurve 仅支持 data_source=spreads，当前为: {ds or '(empty)'}"
            yc_id = str(j.get("yield_curve", "")).strip()
            if not yc_id:
                return "CreditCurve 缺少 yield_curve"
            yc_obj, yc_section = self.resolve_yield_curve(index, yc_id)
            if yc_obj is None:
                return f"yield_curve={yc_id} 在 YieldCurve/BondCurve/SwapCurve 节均未找到"
            tenors = j.get("Tenors", [])
            spreads = j.get("Spreads", [])
            if (not isinstance(tenors, list) or not isinstance(spreads, list)
                    or not tenors or len(spreads) != len(tenors)):
                return ("CreditCurve 缺少有效 Tenors/Spreads（需非空且长度一致） "
                        f"(n_tenor={len(tenors) if isinstance(tenors, list) else '?'}, "
                        f"n_spread={len(spreads) if isinstance(spreads, list) else '?'})")
            try:
                r = self.build_credit_curve_structural(j, index)
                if r is None:
                    last_detail = self.get_last_error()
                    if last_detail:
                        return last_detail
                    return (f"MCreditCurve 结构化构建返回 None（yield_curve={yc_id}, section={yc_section}）；"
                            "请检查 yield_curve 曲线字段（referenceDate/Tenors/ZeroRates 或 fromJson 兼容）")
                return None
            except Exception as e:
                return str(e)
        if curve_type == "VolSurface":
            if index is None:
                return "缺少日索引 RawMarketDataIndex（VolSurface 需结构化构建）"
            exp_j = j.get("ExpiryDates", [])
            opt_j = j.get("OptionTypes", [])
            strikes_j = j.get("Strikes", [])
            prem_j = j.get("Premiums", [])
            if not isinstance(exp_j, list) or not exp_j:
                return "VolSurface 缺少 ExpiryDates"
            if not isinstance(opt_j, list) or not isinstance(strikes_j, list) or not isinstance(prem_j, list):
                return "VolSurface 的 OptionTypes/Strikes/Premiums 不是数组"
            if len(opt_j) != len(strikes_j) or len(strikes_j) != len(prem_j):
                return (f"VolSurface 维度不一致：len(OptionTypes)={len(opt_j)}, "
                        f"len(Strikes)={len(strikes_j)}, len(Premiums)={len(prem_j)}")
            if len(exp_j) != len(strikes_j) and (len(exp_j) <= 0 or len(strikes_j) % len(exp_j) != 0):
                return (f"VolSurface ExpiryDates 维度无法映射到明细轴："
                        f"len(ExpiryDates)={len(exp_j)}, len(Strikes)={len(strikes_j)}")
            fwd_id = str(j.get("forward_curve", "") or "").strip()
            if fwd_id and index.get_curve_json(fwd_id, "ForwardCurve") is None:
                return f"VolSurface forward_curve={fwd_id} 在 ForwardCurve 节未找到"
            rf_id = str(j.get("risk_free_rate_curve", "") or "").strip()
            if rf_id:
                yc, sec = self.resolve_yield_curve(index, rf_id)
                if yc is None:
                    return f"VolSurface risk_free_rate_curve={rf_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
                _ = sec
            try:
                r = self.build_vol_surface_structural(j, index)
                if r is None:
                    return (
                        "MVolSurface 结构化构建返回 None（检查 forward_curve、ForwardCurve 条目、"
                        "ExpiryDates/OptionTypes/Strikes/Premiums 等字段）"
                    )
                return None
            except Exception as e:
                return str(e)
        if curve_type == "LocalVol":
            if index is None:
                return "缺少日索引 RawMarketDataIndex（LocalVol 需结构化构建）"
            exp_j = j.get("ExpiryDates", [])
            opt_j = j.get("OptionTypes", [])
            strikes_j = j.get("Strikes", [])
            prem_j = j.get("Premiums", [])
            if not isinstance(exp_j, list) or not exp_j:
                return "LocalVol 缺少 ExpiryDates"
            if not isinstance(opt_j, list) or not isinstance(strikes_j, list) or not isinstance(prem_j, list):
                return "LocalVol 的 OptionTypes/Strikes/Premiums 不是数组"
            if len(opt_j) != len(strikes_j) or len(strikes_j) != len(prem_j):
                return (f"LocalVol 维度不一致：len(OptionTypes)={len(opt_j)}, "
                        f"len(Strikes)={len(strikes_j)}, len(Premiums)={len(prem_j)}")
            if len(exp_j) != len(strikes_j) and (len(exp_j) <= 0 or len(strikes_j) % len(exp_j) != 0):
                return (f"LocalVol ExpiryDates 维度无法映射到明细轴："
                        f"len(ExpiryDates)={len(exp_j)}, len(Strikes)={len(strikes_j)}")
            rf_id = str(j.get("risk_free_rate_curve", "") or "").strip()
            if rf_id:
                yc, _ = self.resolve_yield_curve(index, rf_id)
                if yc is None:
                    return f"LocalVol risk_free_rate_curve={rf_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
            dom_id = str(j.get("domestic_rate_curve", "") or "").strip()
            if dom_id:
                yc, _ = self.resolve_yield_curve(index, dom_id)
                if yc is None:
                    return f"LocalVol domestic_rate_curve={dom_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
            frn_id = str(j.get("foreign_rate_curve", "") or "").strip()
            if frn_id:
                yc, _ = self.resolve_yield_curve(index, frn_id)
                if yc is None:
                    return f"LocalVol foreign_rate_curve={frn_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
            fwd_id = str(j.get("forward_curve", "") or "").strip()
            if fwd_id and index.get_curve_json(fwd_id, "ForwardCurve") is None:
                return f"LocalVol forward_curve={fwd_id} 在 ForwardCurve 节未找到"
            fxp_id = str(j.get("fx_forward_points_curve", "") or "").strip()
            if fxp_id and index.get_curve_json(fxp_id, "FXForwardPointsCurve") is None:
                return f"LocalVol fx_forward_points_curve={fxp_id} 在 FXForwardPointsCurve 节未找到"
            try:
                r = self.build_local_vol_structural(j, index)
                if r is None:
                    return (
                        "MLocalVol 结构化构建返回 None（检查依赖 YieldCurve/ForwardCurve/FX 等及期权矩阵字段）"
                    )
                return None
            except Exception as e:
                return str(e)
        if curve_type == "FXVolSurface":
            if index is None:
                return "缺少日索引 RawMarketDataIndex（FXVolSurface 需结构化构建）"
            tenors = j.get("Tenors", [])
            deltas = j.get("DeltaStrings", [])
            vols = j.get("Volatilities", [])
            if not isinstance(tenors, list) or not isinstance(deltas, list) or not isinstance(vols, list):
                return "FXVolSurface 的 Tenors/DeltaStrings/Volatilities 不是数组"
            if not tenors or not deltas or not vols:
                return (f"FXVolSurface 缺少关键矩阵字段 "
                        f"(n_tenor={len(tenors) if isinstance(tenors,list) else '?'}, "
                        f"n_delta={len(deltas) if isinstance(deltas,list) else '?'}, "
                        f"n_vol_rows={len(vols) if isinstance(vols,list) else '?'})")
            if any((not isinstance(r, list) or len(r) != len(deltas)) for r in vols):
                row_lens = []
                for r in vols:
                    row_lens.append(len(r) if isinstance(r, list) else -1)
                return (f"FXVolSurface Volatilities 维度与 DeltaStrings 不匹配 "
                        f"(n_delta={len(deltas)}, row_lens={row_lens})")
            if len(vols) != len(tenors):
                return f"FXVolSurface Volatilities 行数与 Tenors 不匹配 (rows={len(vols)}, tenors={len(tenors)})"
            frn_id = str(j.get("foreign_rate_curve", "") or "").strip()
            dom_id = str(j.get("domestic_rate_curve", "") or "").strip()
            if not frn_id or not dom_id:
                return "FXVolSurface 缺少 foreign_rate_curve 或 domestic_rate_curve"
            frn, _ = self.resolve_yield_curve(index, frn_id)
            if frn is None:
                return f"FXVolSurface foreign_rate_curve={frn_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
            dom, _ = self.resolve_yield_curve(index, dom_id)
            if dom is None:
                return f"FXVolSurface domestic_rate_curve={dom_id} 在 YieldCurve/BondCurve/SwapCurve 节未找到"
            fxp_id = str(j.get("fx_forward_points_curve", "") or "").strip()
            if fxp_id and index.get_curve_json(fxp_id, "FXForwardPointsCurve") is None:
                return f"FXVolSurface fx_forward_points_curve={fxp_id} 在 FXForwardPointsCurve 节未找到"
            try:
                r = self.build_fx_vol_surface_structural(j, index)
                if r is None:
                    return (
                        "MFXVolSurface 结构化构建返回 None（检查 foreign/domestic_rate_curve、"
                        "FXForwardPointsCurve、Tenors/DeltaStrings/Volatilities）"
                    )
                return None
            except Exception as e:
                return str(e)
        if curve_type == "HistVol":
            if index is None:
                return "缺少日索引 RawMarketDataIndex（HistVol 需 price_data_index 与 CSV）"
            try:
                r = self.build_hist_vol_structural(j, index)
                if r is None:
                    return (
                        "MHistVols 结构化构建返回 None（检查 price_data_ref、hist_file、instrument 与日期过滤）"
                    )
                return None
            except Exception as e:
                return str(e)
        mcp = self._get_mcp()
        if mcp is None:
            return "mcp 模块未加载"
        from_json = [
            ("BondCurve", "MBondCurve"),
            ("BondSpreadCurve", "MBondSpreadCurve"),
            ("FXForwardPointsCurve", "MFXForwardPointsCurve"),
            ("ForwardCurve", "MForwardCurve"),
        ]
        for key, cls_name in from_json:
            if curve_type != key:
                continue
            cls = getattr(mcp, cls_name, None)
            if cls is None:
                return f"mcp 中无 {cls_name}"
            if not hasattr(cls, "fromJson"):
                return f"{cls_name} 无 fromJson"
            try:
                s = json.dumps(j)
                r = cls.fromJson(s)
                if r is None:
                    return (
                        f"{cls_name}.fromJson 返回 None（JSON 与引擎期望不一致，或依赖曲线/文件未解析）"
                    )
                return None
            except Exception as e:
                return f"{cls_name}.fromJson: {e}"
        return f"不支持的曲线类型: {curve_type}"


class RawMarketDataManager:
    """
    目录管理、按 curve_id 与日期查询（对应 RAW_MARKET_DATA_JSON_DESIGN.md 14.2.4）
    支持 MCP_MARKET_DATA_YYYYMMDD.json 一日一文件主索引。
    """

    def __init__(self, root: str = "", mcp_module=None):
        self._root = root or ""
        self._loader = RawMarketDataLoader(base_path=root, mcp_module=mcp_module)
        self._index_cache: Dict[str, RawMarketDataIndex] = {}

    def set_root(self, root: str) -> None:
        self._root = root or ""
        self._loader._base_path = self._root
        self._index_cache.clear()

    def _index_path(self, valuation_date: str) -> str:
        d = valuation_date.replace("-", "")[:8]
        return os.path.join(self._root, f"MCP_MARKET_DATA_{d}.json")

    def load_daily_index(self, valuation_date: str) -> Optional[RawMarketDataIndex]:
        """加载指定日期的日索引"""
        path = self._index_path(valuation_date)
        if not os.path.isfile(path):
            return None
        key = _yymmdd_to_str(valuation_date)
        if key in self._index_cache:
            return self._index_cache[key]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            idx = RawMarketDataIndex(data, base_path=os.path.dirname(path))
            self._index_cache[key] = idx
            return idx
        except Exception:
            return None

    def get_yield_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        """按 curve_id + 日期获取 MYieldCurve"""
        idx = self.load_daily_index(valuation_date)
        if idx is None:
            return None
        yc, _ = self._loader.resolve_yield_curve(idx, curve_id)
        return yc

    def get_yield_curve2(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "YieldCurve2")

    def get_swap_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        """按 curve_id + 日期获取 MSwapCurve（需 JSON 为 fromJson 兼容格式）"""
        idx = self.load_daily_index(valuation_date)
        if idx is None:
            return None
        j = idx.get_curve_json(curve_id, "SwapCurve")
        if j is None:
            lst = idx._get_curve_list("SwapCurve")
            j = lst[0] if lst else None
        if j is None:
            return None
        return self._loader.build_curve("SwapCurve", j)

    def _get_typed_curve(self, curve_id: str, valuation_date: str, section: str) -> Optional[Any]:
        idx = self.load_daily_index(valuation_date)
        if idx is None:
            return None
        j = idx.get_curve_json(curve_id, section)
        if j is None:
            return None
        return self._loader.build_curve(section, j, idx)

    def get_bond_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "BondCurve")

    def get_credit_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "CreditCurve")

    def get_bond_spread_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        """返回 MBondSpreadCurve；支持 setBenchmarkCurve / getBenchmarkCurve（与 C++ BondSpreadCurve 一致）。"""
        return self._get_typed_curve(curve_id, valuation_date, "BondSpreadCurve")

    def get_fx_forward_points_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "FXForwardPointsCurve")

    def get_fx_forward_points_curve2(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "FXForwardPointsCurve2")

    def get_forward_curve(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "ForwardCurve")

    def get_vol_surface(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "VolSurface")

    def get_fx_vol_surface(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "FXVolSurface")

    def get_fx_vol_surface2(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "FXVolSurface2")

    def get_local_vol(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "LocalVol")

    def get_hist_vol(self, curve_id: str, valuation_date: str) -> Optional[Any]:
        return self._get_typed_curve(curve_id, valuation_date, "HistVol")

    def get_hist_vol_from_price_data(
        self,
        product_type: str,
        instrument_code: str,
        valuation_date: str = "",
        sample_num: int = 252,
        model: str = "EWMA",
        return_method: str = "LOG_RETURN",
        annual_factor: float = 252.0,
        missing_history_fallback_mode: str = "error",
    ) -> Optional[Any]:
        """不依赖 HistVol 节点：从 price_data_index + HIST CSV 动态构建 MHistVols。"""
        del missing_history_fallback_mode
        pt = (product_type or "").strip()
        code = (instrument_code or "").strip()
        if not pt or not code:
            return None
        vd = (valuation_date or "").strip()
        if not vd:
            vd = self.getLatestAvailableDate()
        if not vd:
            return None
        idx = self.load_daily_index(vd)
        if idx is None:
            return None
        ref = vd.replace("-", "").replace("/", "")[:8]
        j = {
            "curve_id": f"GENERIC_HISTVOL_{pt}_{code}",
            "label": code,
            "ReferenceDate": ref,
            "SampleNum": max(2, int(sample_num)),
            "Model": model or "EWMA",
            "ReturnMethod": return_method or "LOG_RETURN",
            "AnnualFactor": float(annual_factor) if annual_factor else 252.0,
            "Lamda": 0.94,
            "InterpolationMethod": "LINEARINTERPOLATION",
            "DayCounter": "Act365Fixed",
            "price_data_ref": {
                "product_type": pt,
                "instrument_code": code,
                "date_column": "valuation_date",
                "price_column": "price",
            },
        }
        return self._loader.build_hist_vol_structural(j, idx)

    def getHistVolFromPriceData(
        self,
        product_type: str,
        instrument_code: str,
        valuation_date: str = "",
        sample_num: int = 252,
        model: str = "EWMA",
        return_method: str = "LOG_RETURN",
        annual_factor: float = 252.0,
        missing_history_fallback_mode: str = "error",
    ) -> Optional[Any]:
        return self.get_hist_vol_from_price_data(
            product_type,
            instrument_code,
            valuation_date,
            sample_num,
            model,
            return_method,
            annual_factor,
            missing_history_fallback_mode,
        )

    def getLatestAvailableDate(self) -> str:
        """与 C++ MRawMarketManager 一致：目录下主索引日期的最大者（YYYY-MM-DD）。"""
        dates = self.get_available_dates()
        return dates[-1] if dates else ""

    def get_price(
        self,
        instrument_code: str,
        valuation_date: str,
        product_type: Optional[str] = None,
    ) -> Optional[float]:
        """
        从 price_data_index 指向的 HIST/当前价 CSV 取价。
        product_type 为空时按键名字母序依次尝试，首次命中即返回（与 C++ 一致）。
        """
        if not instrument_code or not str(instrument_code).strip():
            return None
        idx = self.load_daily_index(valuation_date)
        if idx is None:
            return None
        pidx = idx.price_data_index
        if not isinstance(pidx, dict) or not pidx:
            return None
        vd = valuation_date.replace("-", "").strip()[:8]
        if len(vd) != 8:
            return None
        pt = (product_type or "").strip()
        if pt:
            entry = pidx.get(pt)
            if not isinstance(entry, dict):
                return None
            return _read_price_from_hist_csv(
                self._root, entry, instrument_code.strip(), vd, product_type=pt
            )
        for k in sorted(pidx.keys()):
            entry = pidx.get(k)
            if not isinstance(entry, dict):
                continue
            v = _read_price_from_hist_csv(
                self._root, entry, instrument_code.strip(), vd, product_type=k
            )
            if v is not None:
                return v
        return None

    def getPrice(self, instrument_code: str, product_type: str, valuation_date: str) -> Optional[float]:
        """与 C++/SWIG 参数顺序一致：(instrument_code, product_type, valuation_date)。"""
        pt = (product_type or "").strip() or None
        return self.get_price(instrument_code, valuation_date, pt)

    def get_available_dates(self) -> List[str]:
        """扫描根目录下可用的主索引日期"""
        if not self._root or not os.path.isdir(self._root):
            return []
        dates = []
        prefix = "MCP_MARKET_DATA_"
        suffix = ".json"
        for fn in os.listdir(self._root):
            if fn.startswith(prefix) and fn.endswith(suffix):
                d = fn[len(prefix):-len(suffix)]
                if len(d) == 8 and d.isdigit():
                    dates.append(_yymmdd_to_str(d))
        return sorted(dates)

    def get_missing_dependencies(
        self,
        valuation_date: str,
        sections: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """
        扫描指定估值日的曲线构建问题（重点是依赖缺失）。
        返回列表元素：
        {
          "section": "FXVolSurface",
          "curve_id": "USDCNY_VOL",
          "message": "...",
        }
        """
        idx = self.load_daily_index(valuation_date)
        if idx is None:
            return [{
                "section": "INDEX",
                "curve_id": "",
                "message": f"main index not found for valuation_date={valuation_date}",
            }]

        default_sections = [
            "CreditCurve",
            "VolSurface",
            "FXVolSurface",
            "LocalVol",
        ]
        sec_list = sections if sections else default_sections
        out: List[Dict[str, str]] = []

        for sec in sec_list:
            ids = idx.list_curve_ids(sec)
            for cid in ids:
                j = idx.get_curve_json(cid, sec)
                if not isinstance(j, dict):
                    out.append({
                        "section": sec,
                        "curve_id": str(cid),
                        "message": "index entry is not a JSON object",
                    })
                    continue
                err = self._loader.build_curve_explain(sec, j, idx)
                if err:
                    out.append({
                        "section": sec,
                        "curve_id": str(cid),
                        "message": str(err),
                    })
        return out

    def getMissingDependencies(
        self,
        valuation_date: str,
        sections: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """兼容 C++ 风格命名。"""
        return self.get_missing_dependencies(valuation_date, sections)
