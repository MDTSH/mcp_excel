# -*- coding: utf-8 -*-
"""
Yield Curve Core Module

Provides Excel functions related to yield curves, including:
- Yield curve construction and interpolation
- Forward rate calculation
- Zero rate calculation
- Curve data formatting
"""

# =========================
# Standard Library
# =========================
import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Union

# =========================
# Third Party
# =========================
from pyxll import xl_arg, xl_func, xl_return

# =========================
# Project Internal
# =========================
from mcp import mcp
from mcp.utils.enums import DayCounter, Frequency, enum_wrapper
from mcp.utils.excel_utils import (
    MethodName,
    hydrate_vp_args_blocks,
    mcp_kv_wrapper,
    mcp_method_args_cache,
    pf_mcp_date_list,  # noqa: F401 May be used in templates
)
from mcp.mcp import MVanillaSwap  # noqa: F401 Reserved
from mcp.utils.mcp_utils import (
    excel_date_to_string,
    mcp_dt,
    normalize_yield_curve_ref_date_str,
    parse_excel_date,
)
from mcp.tool.args_def import tool_def
from mcp.wrapper import McpSwapCurve, trace_args, McpCalendar
from mcp_calendar import date_to_string, plain_date
import mcp.wrapper


# =========================
# Utility Functions
# =========================
def fmt_dt_array(dts):
    """
    Format date array to [["YYYYMMDD"...], ["YYYYMMDD"...]] format.
    Supports two types of input:
    - 2D array of length 2 (two columns), format each column directly
    - Date pair array of arbitrary length (each item is [start, end])
    """
    result = []
    if len(dts) == 2:
        for sub_dts in dts:
            sub_list = []
            result.append(sub_list)
            for dt in sub_dts:
                sub_list.append(plain_date(dt))
    else:
        result = [[], []]
        for dt2 in dts:
            result[0].append(plain_date(dt2[0]))
            result[1].append(plain_date(dt2[1]))
    return result


# =========================
# Overnight / Bill / BillFuture Curve Data
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpOvernightRateCurveData(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpOvernightRateCurveData")
    except Exception as e:
        s = f"McpOvernightRateCurveData except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("data", "var[][]")
def McpBillCurveData(args, data):
    data_args = mcp_kv_wrapper.parse_data(
        data,
        [
            ("MaturityTenors", "str"),
            ("MaturityDates", "date"),
            ("Yields", "float"),
            ("BumpAmounts", "float"),
            ("BUses", "intbool"),
        ],
    )
    args = [args, data_args]

    result1, lack_keys1 = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBillCurveData,
        args,
        [
            ("DayCounter", "const"),
            ("StartDate", "date"),
            ("MaturityDates", "plainlist"),
            ("Yields", "plainlist"),
            ("BumpAmounts", "plainlist"),
            ("BUses", "plainlist"),
            ("Calendar", "object", McpCalendar("", "", "")),
        ],
    )
    result2, lack_keys2 = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBillCurveData2,
        args,
        [
            ("DayCounter", "const"),
            ("StartDate", "date"),
            ("MaturityTenors", "plainlist"),
            ("Yields", "plainlist"),
            ("BumpAmounts", "plainlist"),
            ("BUses", "plainlist"),
            ("Calendar", "object", McpCalendar("", "", "")),
        ],
    )

    if len(lack_keys1) > len(lack_keys2):
        lack_keys = lack_keys2
        result = result2
        mode = 2
    else:
        lack_keys = lack_keys1
        result = result1
        mode = 1

    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    vals = result["vals"]
    print("McpBillCurveData args:", vals)
    obj = mcp.wrapper.McpBillCurveData(mode, *vals)
    mcp_method_args_cache.cache(str(obj), result)
    return obj


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
@xl_arg("data", "var[][]")
def McpBillFutureCurveData(args, data):
    data_args = mcp_kv_wrapper.parse_data(
        data,
        [
            ("MaturityTenors", "str"),
            ("SettlementDates", "date"),
            ("MaturityDates", "date"),
            ("Yields", "float"),
            ("Convexities", "float"),
            ("BumpAmounts", "float"),
            ("BUses", "intbool"),
        ],
    )
    args = [args, data_args]

    result1, lack_keys1 = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBillFutureCurveData,
        args,
        [
            ("DayCounter", "const"),
            ("SettlementDates", "plainlist"),
            ("MaturityDates", "plainlist"),
            ("Yields", "plainlist"),
            ("Convexities", "plainlist"),
            ("BumpAmounts", "plainlist"),
            ("BUses", "plainlist"),
        ],
    )
    result2, lack_keys2 = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBillFutureCurveData2,
        args,
        [
            ("DayCounter", "const"),
            ("SettlementDates", "plainlist"),
            ("MaturityTenors", "plainlist"),
            ("Yields", "plainlist"),
            ("Convexities", "plainlist"),
            ("BumpAmounts", "plainlist"),
            ("BUses", "plainlist"),
        ],
    )

    if len(lack_keys1) > len(lack_keys2):
        lack_keys = lack_keys2
        result = result2
        mode = 2
    else:
        lack_keys = lack_keys1
        result = result1
        mode = 1

    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    vals = result["vals"]
    print("McpBillFutureCurveData args:", vals)
    obj = mcp.wrapper.McpBillFutureCurveData(mode, *vals)
    mcp_method_args_cache.cache(str(obj), result)
    return obj


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFRACurveData(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpFRACurveData")
    except Exception as e:
        s = f"McpFRACurveData except: {e}"
        return s



@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFixedRateBondCurveData(args1, args2, args3, args4, args5, fmt='VP|HD'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpFixedRateBondCurveData')
    except Exception as e:
        s = f"McpFixedRateBondCurveData except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

# =========================
# Swap Curve Data (Unified Entry)
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaSwapCurveData(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpVanillaSwapCurveData")
    except Exception as e:
        s = f"McpVanillaSwapCurveData except: {e}"
        return s


# =========================
# Rate Convention & Parameter Reading
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var")
def McpRateConvention(args):
    """
    Create RateConvention object. Supports:
    1) Single param: McpRateConvention("FR007")
    2) KV array: McpRateConvention(A1:B1) with ConventionName | FR007
    3) Modify params: McpRateConvention(A1:B2) with ConventionName|FR007, SwapStartLag|2
    4) New convention: ConventionName|FR007-NEW, SwapStartLag|2, FixedPaymentFrequency|Annual
    5) Temp convention (name not in registry): BaseConvention|FR007, SwapStartLag|7
       - Use BaseConvention when ConventionName (e.g. OH) is not predefined
    """
    if tool_def:
        try:
            # Normalize: single value must be wrapped in tuple for tool_create
            if isinstance(args, str):
                return tool_def.tool_create('McpRateConvention', (args,))
            # KV array from Excel range - pass as tuple so *args unpacks correctly
            return tool_def.tool_create('McpRateConvention', (args,) if not isinstance(args, tuple) else args)
        except Exception as e:
            s = f"McpRateConvention except: {e}"
            logging.warning(s, exc_info=True)
            return s
    try:
        name = args if isinstance(args, str) else (args[0][1] if isinstance(args, (list, tuple)) and args else "")
        return mcp.wrapper.McpRateConvention(name)
    except Exception as e:
        s = f"McpRateConvention except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_return("var[][]")
def rcGetAllPredefined():
    """Return all predefined RateConvention names as array [[name1],[name2],...]"""
    try:
        names = mcp.wrapper.get_all_predefined_rate_conventions()
        return [[n] for n in names]
    except Exception as e:
        s = f"rcGetAllPredefined except: {e}"
        logging.warning(s, exc_info=True)
        return [[s]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def McpName(obj):
    try:
        return obj.toString()
    except Exception as e:
        s = f"McpName except: {e}"
        return s


_RC_STRUCT_ENUM_FIELDS = {
    "fixedPaymentDateAdjuster": "DateAdjusterRule",
    "fixedResetDateAdjuster": "DateAdjusterRule",
    "floatPaymentDateAdjuster": "DateAdjusterRule",
    "floatResetDateAdjuster": "DateAdjusterRule",
    "fixingDateAdjuster": "DateAdjusterRule",
    "fixedFrequency": "Frequency",
    "floatFrequency": "Frequency",
    "fixedCompoundingFrequency": "Frequency",
    "floatCompoundingFrequency": "Frequency",
    "forwardRateCompoundingFrequency": "Frequency",
    "fixingFrequency": "Frequency",
    "fixedDayCount": "DayCounter",
    "fixedPaymentDayCount": "DayCounter",
    "fixedResetDayCount": "DayCounter",
    "floatDayCount": "DayCounter",
    "floatPaymentDayCount": "DayCounter",
    "floatResetDayCount": "DayCounter",
    "fixingDayCounter": "DayCounter",
    "fixingMethod": "ResetRateMethod",
}
_RC_STRUCT_BOOL_FIELDS = {
    "fixedCompounding",
    "floatCompounding",
    "forwardRateCompounding",
    "fixInAdvance",
    "useIndexEstimation",
}


def _resolve_rate_convention(obj):
    """Accept cached RateConvention object or predefined name such as 'HONIA'."""
    if obj is None:
        raise ValueError("RateConvention is empty")
    if isinstance(obj, str):
        name = obj.strip()
        if not name:
            raise ValueError("RateConvention name is empty")
        return mcp.wrapper.McpRateConvention(name)
    if hasattr(obj, "toStruct") or hasattr(obj, "toStructJson"):
        return obj
    raise TypeError(f"Expected RateConvention or name string, got {type(obj).__name__}")


def _rc_struct_from_kv(kv_str):
    """Parse toStructJson 'k=v;k=v' into the same string map as C++ toStruct()."""
    d = {}
    for part in str(kv_str or "").split(";"):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key, val = key.strip(), val.strip()
        if not key:
            continue
        if key in _RC_STRUCT_BOOL_FIELDS:
            d[key] = "true" if val in ("1", "true", "True") else "false"
        elif key in _RC_STRUCT_ENUM_FIELDS:
            try:
                name = enum_wrapper.key_of_value(int(float(val)), _RC_STRUCT_ENUM_FIELDS[key])
                d[key] = name if name else val
            except Exception:
                d[key] = val
        elif key == "marginBps":
            try:
                d[key] = f"{float(val):.6f}"
            except Exception:
                d[key] = val
        else:
            d[key] = val
    return d


def _rc_to_struct_dict(rc):
    try:
        s = rc.toStruct()
        d = json.loads(s) if isinstance(s, str) else s
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return _rc_struct_from_kv(rc.toStructJson())


def _rc_cast(val, as_type):
    if as_type == "int":
        return int(float(val))
    if as_type == "float":
        return float(val)
    if as_type == "bool":
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("1", "true", "yes", "y")
    return val


def _rc_get(obj, field_key=None, getter_name=None, as_type=None):
    """Read one RateConvention field. obj may be a cached object or a name string."""
    rc = _resolve_rate_convention(obj)
    last_err = None
    if getter_name and hasattr(rc, getter_name):
        try:
            return getattr(rc, getter_name)()
        except Exception as e:
            last_err = e
    if field_key:
        d = _rc_to_struct_dict(rc)
        if field_key in d:
            return _rc_cast(d[field_key], as_type)
    if last_err:
        raise last_err
    raise KeyError(f"RateConvention field not found: {field_key or getter_name}")


def _rc_excel_func(name, field_key=None, getter_name=None, as_type=None, doc=""):
    def _fn(obj):
        try:
            return _rc_get(obj, field_key=field_key, getter_name=getter_name, as_type=as_type)
        except Exception as e:
            return f"{name} except: {e}"

    _fn.__name__ = name
    _fn.__doc__ = doc or (
        f"Return RateConvention {field_key or getter_name}. "
        "obj: McpRateConvention object or predefined name such as 'HIBOR'."
    )
    return xl_func(macro=False, recalc_on_open=True)(xl_arg("obj", "var")(_fn))


# Existing field readers (now accept object or name string)
rcGetName = _rc_excel_func("rcGetName", "fixingIndexName", "getName")
rcSwapStartLag = _rc_excel_func("rcSwapStartLag", "swapStartLag", "swapStartLag", "int")
rcFixedPaymentDateAdjuster = _rc_excel_func(
    "rcFixedPaymentDateAdjuster", "fixedPaymentDateAdjuster", "fixedPaymentDateAdjuster"
)
rcFixedResetDateAdjuster = _rc_excel_func(
    "rcFixedResetDateAdjuster", "fixedResetDateAdjuster", "fixedResetDateAdjuster"
)
rcFloatPaymentDateAdjuster = _rc_excel_func(
    "rcFloatPaymentDateAdjuster", "floatPaymentDateAdjuster", "floatPaymentDateAdjuster"
)
rcFloatResetDateAdjuster = _rc_excel_func(
    "rcFloatResetDateAdjuster", "floatResetDateAdjuster", "floatResetDateAdjuster"
)
rcFixedDayCounter = _rc_excel_func("rcFixedDayCounter", "fixedDayCount", "fixedDayCounter")
rcFloatDayCounter = _rc_excel_func("rcFloatDayCounter", "floatDayCount", "floatDayCounter")
rcFixingMethod = _rc_excel_func("rcFixingMethod", "fixingMethod", "fixingMethod")
rcUseIndexEstimation = _rc_excel_func(
    "rcUseIndexEstimation", "useIndexEstimation", "useIndexEstimation", "bool"
)
rcFixInAdvance = _rc_excel_func("rcFixInAdvance", "fixInAdvance", "fixInAdvance", "bool")
rcMargin = _rc_excel_func("rcMargin", "marginBps", "margin", "float")
rcFixDaysBackward = _rc_excel_func("rcFixDaysBackward", "fixDaysBackward", "fixDaysBackward", "int")

# Previously missing field readers
rcFixedFrequency = _rc_excel_func("rcFixedFrequency", "fixedFrequency")
rcFloatFrequency = _rc_excel_func("rcFloatFrequency", "floatFrequency")
rcFixedPaymentDayCounter = _rc_excel_func("rcFixedPaymentDayCounter", "fixedPaymentDayCount")
rcFixedResetDayCounter = _rc_excel_func("rcFixedResetDayCounter", "fixedResetDayCount")
rcFloatPaymentDayCounter = _rc_excel_func("rcFloatPaymentDayCounter", "floatPaymentDayCount")
rcFloatResetDayCounter = _rc_excel_func("rcFloatResetDayCounter", "floatResetDayCount")
rcFixingDayCounter = _rc_excel_func("rcFixingDayCounter", "fixingDayCounter")
rcFixedCompounding = _rc_excel_func("rcFixedCompounding", "fixedCompounding", as_type="bool")
rcFixedCompoundingFrequency = _rc_excel_func("rcFixedCompoundingFrequency", "fixedCompoundingFrequency")
rcFloatCompounding = _rc_excel_func("rcFloatCompounding", "floatCompounding", as_type="bool")
rcFloatCompoundingFrequency = _rc_excel_func("rcFloatCompoundingFrequency", "floatCompoundingFrequency")
rcForwardRateCompounding = _rc_excel_func(
    "rcForwardRateCompounding", "forwardRateCompounding", as_type="bool"
)
rcForwardRateCompoundingFrequency = _rc_excel_func(
    "rcForwardRateCompoundingFrequency", "forwardRateCompoundingFrequency"
)
rcFixingFrequency = _rc_excel_func("rcFixingFrequency", "fixingFrequency")
rcFixingDateAdjuster = _rc_excel_func("rcFixingDateAdjuster", "fixingDateAdjuster")
rcFixedPaymentLag = _rc_excel_func("rcFixedPaymentLag", "fixedPaymentLag", as_type="int")
rcFloatPaymentLag = _rc_excel_func("rcFloatPaymentLag", "floatPaymentLag", as_type="int")
rcFixingIndexName = _rc_excel_func("rcFixingIndexName", "fixingIndexName")
rcFloatTenor = _rc_excel_func("rcFloatTenor", "fixingIndexTenor", "floatTenor")
rcConventionName = _rc_excel_func("rcConventionName", "fixingIndexName", "conventionName")


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "var")
def rcToStruct(obj):
    """Return RateConvention as struct array [[key, value], ...].
    obj: McpRateConvention object or predefined name such as 'HONIA' / 'FR007'.
    """
    try:
        rc = _resolve_rate_convention(obj)
        d = _rc_to_struct_dict(rc)
        return [[k, v] for k, v in d.items()]
    except Exception as e:
        s = f"rcToStruct except: {e}"
        return [[s]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "var")
def rcToStructJson(obj):
    """Return RateConvention as key=value string.
    obj: McpRateConvention object or predefined name such as 'HONIA' / 'FR007'.
    """
    try:
        rc = _resolve_rate_convention(obj)
        return rc.toStructJson()
    except Exception as e:
        s = f"rcToStructJson except: {e}"
        return s


# =========================
# Calibration Set（聚合多产品）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "object[]")
def McpCalibrationSet(args):
    print("McpCalibrationSet args:", args)
    obj = mcp.wrapper.McpCalibrationSet()
    for item in args:
        obj.addData(item.getHandler())
    obj.addEnd()
    return obj


class SwapCurveData:
    def __init__(self, dates1, dates2, rates):
        self.dates = json.dumps([dates1, dates2])
        self.rates = json.dumps(rates)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("dates1", "datetime[]")
@xl_arg("dates2", "datetime[]")
@xl_arg("rates", "float[]")
def McpSwapCurveData(dates1, dates2, rates):
    dt1 = mcp_dt.to_date_list(dates1, mcp_dt.to_date1)
    dt2 = mcp_dt.to_date_list(dates2, mcp_dt.to_date1)
    rt = json.dumps(rates)
    return SwapCurveData(dt1, dt2, rt)


# =========================
# Swap Curve（新版入口：kv + data）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpSwapCurve2(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5]

    kvs = [
        ("ReferenceDate", "date"),
        ("CalibrationSet", "mcphandler"),
        ("InterpolatedVariable", "const"),
        ("InterpolationMethod", "const"),
        ("DayCounter", "const"),
    ]
    data_fields = [
        ("SettlementDates", "date"),
        ("MaturityDates", "date"),
        ("Coupons", "float"),
        ("FixedFrequencies", "const"),
        ("FloatingFrequencies", "const"),
        ("BumpAmounts", "float"),
        ("BUses", "intbool"),
    ]
    kvs2 = [
        ("ReferenceDate", "date"),
        ("InterpolatedVariable", "const"),
        ("InterpolationMethod", "const"),
        ("FixedDayCounter", "const"),
        ("FloatDayCounter", "const"),
        ("DayCounter", "const"),
        ("Calendar", "mcphandler"),
        ("AdjustRule", "const"),
        ("SettlementDates", "plainlist"),
        ("MaturityDates", "plainlist"),
        ("Coupons", "plainlist"),
        ("FixedFrequencies", "plainlist"),
        ("FloatingFrequencies", "plainlist"),
        ("BumpAmounts", "plainlist"),
        ("BUses", "plainlist"),
    ]

    result, lack_keys = mcp_kv_wrapper.valid_parse_kv_list(
        "McpSwapCurve",
        args,
        fmt,
        data_fields,
        kvs,
        [kvs2],
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    vals = result["vals"]
    obj = McpSwapCurve(*vals)
    mcp_method_args_cache.cache(str(obj), result)
    return obj


# =========================
# Bond Curve（kv）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
def McpBondCurve2(args1, args2, args3, args4, args5):
    args = [args1, args2, args3, args4, args5]
    result, lack_keys = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBondCurve,
        args,
        [
            ("SettlementDate", "date"),
            ("CalibrationSet", "mcphandler"),
            ("InterpolatedVariable", "const"),
            ("InterpolationMethod", "const"),
            ("DayCounter", "const"),
        ],
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    vals = result["vals"]
    obj = mcp.wrapper.McpBondCurve(*vals)
    mcp_method_args_cache.cache(str(obj), result)
    return obj


# =========================
# Yield Curve（低层封装：单点/批量）
# =========================
@xl_func(macro=False, recalc_on_open=False)
@xl_arg("curve", "object")
@xl_arg("date", "datetime")
def YieldCurveDiscountFactor(curve, date):
    if isinstance(curve, str):
        return curve
    date_str = date_to_string(date)
    return curve.DiscountFactor(date_str)


@xl_func(macro=False, recalc_on_open=False)
def YieldCurveZeroRate(curve, date, dayCounter= DayCounter.NONE):
    args = [curve, date, dayCounter]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve", method="ZeroRate")
    except Exception as e:
        s = f"YieldCurveZeroRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s



@xl_func(macro=False, recalc_on_open=True, auto_resize=False)
@xl_arg("curve", "object")
@xl_arg("dates", "datetime[]")
def YieldCurveZeroRates(curve, dates):
    if isinstance(curve, str):
        return curve
    result = []
    for dt in dates:
        date_str = date_to_string(dt)
        result.append(curve.ZeroRate(date_str))
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("referenceDate", "datetime")
def YieldCurveCloneCurve(curve, referenceDate):
    try:
        handler = curve.CloneCurve(referenceDate.strftime("%Y/%m/%d"))
        return mcp.wrapper.McpYieldCurve(handler)
    except Exception as e:
        s = f"YieldCurveCloneCurve except: {e}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Yield Curve（工具入口：tool_def）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpYieldCurve2(args1, args2, args3, args4, args5, fmt="VP|HD"):
    """
    注意：原文件存在同名 McpYieldCurve2 的两个定义，此函数为后者（tool_def 版本）。
    若希望覆盖前者，请将本函数名改回 McpYieldCurve2 并移除前者。
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpYieldCurve2")
    except Exception as e:
        s = f"McpYieldCurve2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpYieldCurve(args1, args2, args3, args4, args5, fmt="VP|HD"):
    if args1 and args1[-1][0] is None:
        args1 = [row for row in args1 if not all(item is None for item in row)]
    if args2 and args2[-1][0] is None:
        args2 = [row for row in args2 if not all(item is None for item in row)]

    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpYieldCurve")
    except Exception as e:
        s = f"McpYieldCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurveForwardRate(
    curve,
    startDate,
    endDate,
    dayCounter=DayCounter.Act360,
    compounding=True,
    frequency=Frequency.Continuous,
):
    args = [curve, startDate, endDate, dayCounter, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve", method="ForwardRate")
    except Exception:
        s = f"YieldCurveForwardRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurveDiscountFactor(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve", method="DiscountFactor")
    except Exception:
        s = f"YieldCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def YieldCurveZeroRates(curve, dates, fmt="V"):
    args = [curve, dates, fmt]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve", method="ZeroRates")
    except Exception:
        s = f"YieldCurveZeroRates except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def YieldCurveDiscountFactors(curve, dates, fmt="V"):
    args = [curve, dates, fmt]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve", method="DiscountFactors")
    except Exception:
        s = f"YieldCurveDiscountFactors except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Yield Curve 2（B/M/A）单点方法
# =========================
@xl_func(macro=False, recalc_on_open=True)
def YieldCurve2ZeroRate(curve, date, bidMidAsk):
    args = [curve, date, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve2", method="ZeroRate")
    except Exception:
        s = f"YieldCurve2ZeroRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurve2DiscountFactor(curve, date, bidMidAsk):
    args = [curve, date, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve2", method="DiscountFactor")
    except Exception:
        s = f"YieldCurve2DiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurve2MaturityDate(curve, tenor):
    args = [curve, tenor]
    try:
        return tool_def.xls_call(*args, key="McpYieldCurve2", method="MaturityDate")
    except Exception:
        s = f"YieldCurve2MaturityDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Swap Curve（工具入口）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpSwapCurve(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpSwapCurve")
    except Exception as e:
        s = f"McpSwapCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurveRefDate(curve):
    args = [curve]
    try:
        ret = tool_def.xls_call(*args, key="McpYieldCurve", method="GetRefDate")
        return normalize_yield_curve_ref_date_str(ret)
    except Exception:
        s = f"YieldCurveRefDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def SwapCurveRefDate(curve):
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="GetRefDate")
    except Exception as e:
        s = f"SwapCurveRefDate except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("referenceDate", "datetime")
def SwapCurveCloneCurve(curve, referenceDate):
    try:
        handler = curve.CloneCurve(referenceDate.strftime("%Y/%m/%d"))
        return mcp.wrapper.McpSwapCurve(handler)
    except Exception as e:
        s = f"SwapCurveCloneCurve except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def SwapCurveZeroRate(curve, endDate, dayCounter=DayCounter.NONE, compounding=True, frequency=Frequency.Continuous):
    args = [curve, endDate, dayCounter, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="ZeroRate")
    except Exception:
        s = f"SwapCurveZeroRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def SwapCurveDiscountFactor(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="DiscountFactor")
    except Exception:
        s = f"SwapCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def SwapCurveZeroRates(curve, dates, fmt="V"):
    args = [curve, dates, fmt]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="ZeroRates")
    except Exception:
        s = f"SwapCurveZeroRates except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def SwapCurveDiscountFactors(curve, dates, fmt="V"):
    args = [curve, dates, fmt]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="DiscountFactors")
    except Exception:
        s = f"SwapCurveDiscountFactors except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def YieldCurveBumpCurve(curve, bumpSize=0.0001):
    try:
        handler = curve.BumpCurve(bumpSize)
        return mcp.wrapper.McpYieldCurve(handler)
    except Exception:
        s = f"YieldCurveBumpCurve except"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def SwapCurveParSwapRate(curve, start, end):
    start_str = start
    end_str = end
    if isinstance(start, float):
        start_str = mcp_dt.excel_date_to_string(start)
    if isinstance(end, float):
        end_str = mcp_dt.excel_date_to_string(end)
    args = [curve, start_str, end_str]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="ParSwapRate")
    except Exception as e:
        s = f"SwapCurveParSwapRate except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("maturityPeriod", "str")
def SwapCurveCarry(curve, horizon, maturityPeriod):
    horizon_str = horizon
    if isinstance(horizon, float):
        horizon_str = mcp_dt.excel_date_to_string(horizon)
    args = [curve, horizon_str, maturityPeriod]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="Carry")
    except Exception as e:
        s = f"SwapCurveCarry except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("maturityPeriod", "str")
def SwapCurveRoll(curve, horizon, maturityPeriod):
    horizon_str = horizon
    if isinstance(horizon, float):
        horizon_str = mcp_dt.excel_date_to_string(horizon)
    args = [curve, horizon_str, maturityPeriod]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="Roll")
    except Exception as e:
        s = f"SwapCurveRoll except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondCurveBumpCurve(curve, bumpSize=0.0001):
    try:
        handler = curve.BumpCurve(bumpSize)
        return mcp.wrapper.McpBondCurve(handler)
    except Exception:
        s = "BondCurveBumpCurve except"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("settlementDate", "datetime")
def BondCurveCloneCurve(curve, settlementDate):
    try:
        handler = curve.CloneCurve(settlementDate.strftime("%Y/%m/%d"))
        return mcp.wrapper.McpBondCurve(handler)
    except Exception as e:
        s = f"BondCurveCloneCurve except: {e}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# FX Forward Points Curve
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardPointsCurve(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5]
    data_fields = [
        ("Tenors", "str"),
        ("FXForwardPoints", "float"),
        ("FXOutright", "float"),
    ]
    kv1 = [
        ("ReferenceDate", "date"),
        ("Tenors", "plainlist"),
        ("FXForwardPoints", "plainlist"),
        ("FXSpotRate", "float"),
        ("Method", "const"),
        ("Calendar", "mcphandler"),
        ("ScaleFactor", "float"),
    ]
    kv2 = [
        ("ReferenceDate", "date"),
        ("Tenors", "plainlist"),
        ("FXForwardPoints", "plainlist"),
        ("FXSpotRate", "float"),
        ("Method", "const"),
        ("Calendar", "mcphandler"),
        ("Pair", "str"),
    ]
    kv2b = [
        ("ReferenceDate", "date"),
        ("Tenors", "plainlist"),
        ("FXForwardPoints", "plainlist"),
        ("FXSpotRate", "float"),
        ("Method", "const"),
        ("Calendar", "mcphandler"),
        ("Pair", "str"),
        ("ScaleFactor", "float"),
    ]
    # kv3: 支持 FXOutright 输入（用户提供 Tenors + FXOutright 时匹配）
    kv3 = [
        ("ReferenceDate", "date"),
        ("FXOutright", "plainlist"),
        ("Tenors", "plainlist"),
        ("Method", "const"),
        ("Calendar", "mcphandler"),
        ("FXSpotRate", "float"),
        ("ScaleFactor", "float"),
    ]
    kv4 = [
        ("Leg1", "object"),
        ("Leg2", "object"),
        ("ScaleFactor", "float", 0.0),
        ("SpotRate", "float", 0.0),
    ]
    kv5 = [
        ("Leg1", "object"),
        ("Leg2", "object"),
        ("Calendar", "mcphandler"),
        ("CrossPair", "str", ""),
        ("ScaleFactor", "float", 0.0),
        ("SpotRate", "float", 0.0),
    ]
    kv6 = [
        ("Leg1", "object"),
        ("Leg2", "object"),
        ("Calendar", "mcphandler"),
        ("ReferenceDate", "date", None),
        ("CrossPair", "str", ""),
        ("ScaleFactor", "float", 0.0),
        ("SpotRate", "float", 0.0),
    ]
    result, lack_keys = mcp_kv_wrapper.valid_parse_kv_list(
        "McpFXForwardPointsCurve", args, fmt, data_fields, kv1, [kv2b, kv2, kv3, kv4, kv5, kv6]
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    d = result["dict"]
    # VP 中若有 Pair，强制走 Pair 构造（避免 kv1 丢弃 Pair 字段）
    if "Pair" not in d and "Tenors" in d and "Leg1" not in d:
        args_std = mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
        raw = mcp_kv_wrapper.parse_raw_range_vals(args_std)
        if "pair" in raw:
            tag = "McpFXForwardPointsCurve_pair_sf"
            if tag not in mcp_kv_wrapper.kv_dict:
                mcp_kv_wrapper.add_method(tag, kv2b)
            pair_result = mcp_kv_wrapper.raw_to_std_result(tag, raw)
            for k, v in pair_result["dict"].items():
                d[k] = v

    if "Leg1" in d and "Leg2" in d and "Pair" not in d and "Tenors" not in d:
        leg1 = d["Leg1"]
        leg2 = d["Leg2"]
        calendar = d.get("Calendar")
        reference_date = d.get("ReferenceDate") or None
        cross_pair = d.get("CrossPair") or ""
        scale_factor = float(d.get("ScaleFactor", 0) or 0)
        spot_rate = float(d.get("SpotRate", 0) or 0)
        mcp_item = mcp.wrapper.McpFXForwardPointsCurve(
            leg1, leg2, calendar, reference_date, cross_pair, scale_factor, spot_rate
        )
    elif "Pair" in d and "Tenors" in d:
        scale_factor = float(d.get("ScaleFactor", 0) or 0)
        mcp_item = mcp.wrapper.McpFXForwardPointsCurve(
            d["ReferenceDate"],
            d["Tenors"],
            d["FXForwardPoints"],
            d["FXSpotRate"],
            d["Method"],
            d["Calendar"],
            d["Pair"],
            scale_factor,
        )
    else:
        vals = result["vals"]
        mcp_item = mcp.wrapper.McpFXForwardPointsCurve(*vals)
    mcp_method_args_cache.cache(str(mcp_item), result)
    return mcp_item


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("curve", "object")
def FxfpcGetPair(curve):
    """返回 FXForwardPointsCurve 的 Pair（如 CZK/CNY）"""
    try:
        return curve.GetPair()
    except Exception as e:
        s = f"FxfpcGetPair except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("curve", "object")
@xl_arg("bid_mid_ask", "str")
def FxfpcGetSpot(curve, bid_mid_ask="MID"):
    """返回 FXForwardPointsCurve 的 Spot 价格"""
    try:
        return curve.GetSpot(bid_mid_ask)
    except Exception as e:
        s = f"FxfpcGetSpot except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("curve", "object")
def FxfpcSpotDate(curve):
    """返回 FXForwardPointsCurve 的 SpotDate"""
    try:
        return curve.GetSpotDate()
    except Exception as e:
        s = f"FxfpcSpotDate except: {e}"
        logging.warning(s, exc_info=True)
        return s


_FXFP2_DATA_FIELDS = [
    ("Tenors", "str"),
    ("BidForwardPoints", "float"),
    ("AskForwardPoints", "float"),
]

_FXFP2_PAIR_KV = [
    ("ReferenceDate", "date"),
    ("BidFXSpotRate", "float"),
    ("BidForwardPoints", "plainlist"),
    ("AskFXSpotRate", "float"),
    ("AskForwardPoints", "plainlist"),
    ("Tenors", "plainlist"),
    ("Method", "const"),
    ("Calendar", "mcphandler"),
    ("Pair", "str"),
    ("ScaleFactor", "float", 0.0),
    ("QuoteUnit", "float", 0.0),
]


def _fxfp2_build_pair_curve(kv_dict: Dict[str, Any]):
    scale_factor = float(kv_dict.get("ScaleFactor", 0) or 0)
    quote_unit = float(kv_dict.get("QuoteUnit", 0) or 0)
    args = [
        kv_dict["ReferenceDate"],
        kv_dict["BidFXSpotRate"],
        kv_dict["BidForwardPoints"],
        kv_dict["AskFXSpotRate"],
        kv_dict["AskForwardPoints"],
        kv_dict["Tenors"],
        kv_dict["Method"],
        kv_dict["Calendar"],
        kv_dict["Pair"],
    ]
    try:
        return mcp.wrapper.McpFXForwardPointsCurve2(*args, scale_factor, quote_unit)
    except TypeError:
        return mcp.wrapper.McpFXForwardPointsCurve2(*args)


_FXFP2_CROSS_KV_WITH_LEGS = [
    ("ReferenceDate", "date"),
    ("Leg1", "object"),
    ("Leg2", "object"),
    ("IsCur1Direct", "bool", True),
    ("IsCur2Direct", "bool", True),
    ("BidFXSpotRate", "float", 0.0),
    ("AskFXSpotRate", "float", 0.0),
    ("CrossFXSpot", "bool", False),
    ("Calendar", "mcphandler"),
    ("SpotDate", "date", None),
    ("ScaleFactor", "float", 0.0),
    ("QuoteUnit", "float", 1.0),
    ("QuoteUnit1", "float", 1.0),
    ("QuoteUnit2", "float", 1.0),
]


def _fxfp2_build_cross_curve(leg1, leg2, kv_dict: Dict[str, Any]):
    if leg1 is None or leg2 is None:
        raise ValueError("Leg1/Leg2 为空")
    calendar = kv_dict.get("Calendar")
    reference_date = kv_dict.get("ReferenceDate") or None
    spot_date = kv_dict.get("SpotDate") or None
    is_cur1_direct = bool(kv_dict.get("IsCur1Direct", True))
    is_cur2_direct = bool(kv_dict.get("IsCur2Direct", True))
    bid_spot = float(kv_dict.get("BidFXSpotRate", 0) or 0)
    ask_spot = float(kv_dict.get("AskFXSpotRate", 0) or 0)
    cross_fx_spot = bool(kv_dict.get("CrossFXSpot", False))
    scale_factor = float(kv_dict.get("ScaleFactor", 0) or 0)
    quote_unit = float(kv_dict.get("QuoteUnit", 1) or 1)
    quote_unit1 = float(kv_dict.get("QuoteUnit1", 1) or 1)
    quote_unit2 = float(kv_dict.get("QuoteUnit2", 1) or 1)
    leg1_h = leg1.getHandler() if hasattr(leg1, "getHandler") else leg1
    leg2_h = leg2.getHandler() if hasattr(leg2, "getHandler") else leg2
    cal_h = (
        calendar.getHandler()
        if calendar is not None and hasattr(calendar, "getHandler")
        else calendar
    )
    return mcp.wrapper.McpFXForwardPointsCurve2(
        reference_date,
        leg1_h,
        leg2_h,
        is_cur1_direct,
        is_cur2_direct,
        bid_spot,
        ask_spot,
        cross_fx_spot,
        cal_h,
        spot_date,
        scale_factor,
        quote_unit,
        quote_unit1,
        quote_unit2,
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardPointsCurve2(args1, args2, args3, args4, args5, fmt="VP"):
    raw_blocks = hydrate_vp_args_blocks([args1, args2, args3, args4, args5])
    args = [*raw_blocks, fmt]
    cross_tag = "McpFXForwardPointsCurve2_cross"
    if cross_tag not in mcp_kv_wrapper.kv_dict:
        mcp_kv_wrapper.add_method(cross_tag, _FXFP2_CROSS_KV_WITH_LEGS)
    result, lack_keys = mcp_kv_wrapper.valid_parse_kv_list(
        cross_tag, args[:-1], args[-1], [], None, [_FXFP2_CROSS_KV_WITH_LEGS]
    )
    if len(lack_keys) == 0:
        d = result["dict"]
        try:
            mcp_item = _fxfp2_build_cross_curve(d["Leg1"], d["Leg2"], d)
            mcp_method_args_cache.cache(str(mcp_item), result)
            return mcp_item
        except Exception as e:
            logging.warning("McpFXForwardPointsCurve2 cross build: %s", e, exc_info=True)
    pair_tag = "McpFXForwardPointsCurve2_pair"
    if pair_tag not in mcp_kv_wrapper.kv_dict:
        mcp_kv_wrapper.add_method(pair_tag, _FXFP2_PAIR_KV)
    pair_result, pair_lack = mcp_kv_wrapper.valid_parse_kv_list(
        pair_tag, args[:-1], args[-1], _FXFP2_DATA_FIELDS, None, [_FXFP2_PAIR_KV]
    )
    if len(pair_lack) == 0 and "Pair" in pair_result["dict"]:
        try:
            mcp_item = _fxfp2_build_pair_curve(pair_result["dict"])
            mcp_method_args_cache.cache(str(mcp_item), pair_result)
            return mcp_item
        except Exception as e:
            logging.warning("McpFXForwardPointsCurve2 pair build: %s", e, exc_info=True)
    try:
        return tool_def.xls_create(*args, key="McpFXForwardPointsCurve2")
    except Exception as e:
        s = f"McpFXForwardPointsCurve2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2FXForwardPoints(curve, date, bidMidAsk):
    args = [curve, date, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="FXForwardPoints")
    except Exception:
        s = f"Fxfpc2FXForwardPoints except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2FXFwdPoint(curve, tenor, bidMidAsk):
    args = [curve, tenor, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="FXFwdPoint")
    except Exception:
        s = f"Fxfpc2FXFwdPoint except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2FXForwardOutright(curve, date, bidMidAsk):
    args = [curve, date, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="FXForwardOutright")
    except Exception:
        s = f"Fxfpc2FXForwardOutright except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2TOForwardPoint(curve, startDate, endDate, findMax, bidMidAsk):
    args = [curve, startDate, endDate, findMax, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="TOForwardPoint")
    except Exception:
        s = f"Fxfpc2TOForwardPoint except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2TOForwardOutright(curve, startDate, endDate, findMax, bidMidAsk):
    args = [curve, startDate, endDate, findMax, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="TOForwardOutright")
    except Exception:
        s = f"Fxfpc2TOForwardOutright except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2TimeOptionDate(curve, startDate, endDate, findMax, bidMidAsk):
    args = [curve, startDate, endDate, findMax, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="TimeOptionDate")
    except Exception:
        s = f"Fxfpc2TimeOptionDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2FXSpotRate(curve, bidMidAsk):
    args = [curve, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="FXSpotRate")
    except Exception:
        s = f"Fxfpc2FXSpotRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2ScaleFactor(curve, bidMidAsk):
    args = [curve, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="ScaleFactor")
    except Exception:
        s = f"Fxfpc2ScaleFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def Fxfpc2SpotDate(curve):
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpFXForwardPointsCurve2", method="SpotDate")
    except Exception:
        s = f"Fxfpc2SpotDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# 参数化曲线（工具入口）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpParametricCurve(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpParametricCurve")
    except Exception as e:
        s = f"McpParametricCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def ParametricCurveZeroRate(curve, date, dayCounter=DayCounter.NONE, compounding=True, frequency=Frequency.Continuous):
    args = [curve, date, dayCounter, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpParametricCurve", method="ZeroRate")
    except Exception:
        s = f"ParametricCurveZeroRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def ParametricCurveDiscountFactor(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpParametricCurve", method="DiscountFactor")
    except Exception:
        s = f"ParametricCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def ParametricCurveParameters(curve):
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpParametricCurve", method="Parameters")
    except Exception:
        s = f"ParametricCurveParameters except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Bond Curve（工具入口）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondCurve(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpBondCurve")
    except Exception as e:
        s = f"McpBondCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondCurveZeroRate(curve, date, dayCounter=DayCounter.NONE, compounding=True, frequency=Frequency.Continuous):
    args = [curve, date, dayCounter, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="ZeroRate")
    except Exception as e:
        s = f"BondCurveZeroRate except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondCurveDiscountFactor(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="DiscountFactor")
    except Exception:
        s = f"BondCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondCurveParRate(curve, date, compounding=True, frequency=Frequency.Semiannual):
    args = [curve, date, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="ParRate")
    except Exception:
        s = f"BondCurveParRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("maturityPeriod", "str")
def BondCurveCarry(curve, horizon, maturityPeriod):
    horizon_str = horizon
    if isinstance(horizon, float):
        horizon_str = mcp_dt.excel_date_to_string(horizon)
    args = [curve, horizon_str, maturityPeriod]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="Carry")
    except Exception as e:
        s = f"BondCurveCarry except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("maturityPeriod", "str")
def BondCurveRoll(curve, horizon, maturityPeriod):
    horizon_str = horizon
    if isinstance(horizon, float):
        horizon_str = mcp_dt.excel_date_to_string(horizon)
    args = [curve, horizon_str, maturityPeriod]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="Roll")
    except Exception as e:
        s = f"BondCurveRoll except: {e}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Bond Spread Curve（MBondSpreadCurve）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondSpreadCurve(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpBondSpreadCurve")
    except Exception as e:
        s = f"McpBondSpreadCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveZeroSpread(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="zeroSpread")
    except Exception:
        s = f"BondSpreadCurveZeroSpread except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveYieldSpread(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="yieldSpread")
    except Exception:
        s = f"BondSpreadCurveYieldSpread except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveZeroRate(curve, date, dayCounter=DayCounter.NONE, compounding=True, frequency=Frequency.Continuous):
    args = [curve, date, dayCounter, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="ZeroRate")
    except Exception:
        s = f"BondSpreadCurveZeroRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveDiscountFactor(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="DiscountFactor")
    except Exception:
        s = f"BondSpreadCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveParRate(curve, date, compounding=True, frequency=Frequency.Semiannual):
    args = [curve, date, compounding, frequency]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="ParRate")
    except Exception:
        s = f"BondSpreadCurveParRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveSetBenchmark(curve, benchmarkCurve):
    args = [curve, benchmarkCurve]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="setBenchmarkCurve")
    except Exception:
        s = f"BondSpreadCurveSetBenchmark except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def BondSpreadCurveGetBenchmark(curve):
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpBondSpreadCurve", method="getBenchmarkCurve")
    except Exception:
        s = f"BondSpreadCurveGetBenchmark except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Credit Curve（MCreditCurve）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCreditCurve(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpCreditCurve（信用曲线）对象

    参数（CFETS CDS Index 构造）:
        ReferenceDate: 定价日
        CftsSpreads: JSON 字符串，格式 {"3M": 62.15, "6M": 76.45, "1Y": 85.2, ...}
        YieldCurve: 无风险收益率曲线
        RecoveryRate: 回收率（默认 0.40）
        Variable: 插值变量（默认 HAZARDRATES）
        Method: 插值方法（默认 LINEARINTERPOLATION）
        Calendar: 日历（可选）
        DayCounter: 日计数规则（默认 Act365Fixed）
        ValuationType: CDS 估值类型（默认 JPMISDA）
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpCreditCurve")
    except Exception as e:
        s = f"McpCreditCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveNoDefaultProbability(curve, endDate):
    """生存概率（无违约概率）"""
    args = [curve, endDate]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="NoDefaultProbability")
    except Exception:
        s = f"CreditCurveNoDefaultProbability except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveHazardRate(curve, endDate):
    """风险率（违约强度）"""
    args = [curve, endDate]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="HazardRate")
    except Exception:
        s = f"CreditCurveHazardRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveForwardHazardRate(curve, startDate, endDate):
    """远期风险率"""
    args = [curve, startDate, endDate]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="ForwardHazardRate")
    except Exception:
        s = f"CreditCurveForwardHazardRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveDefaultProbability(curve, endDate, startDate=None):
    """违约概率。单参数：到 endDate 的违约概率；双参数：startDate 到 endDate 区间的违约概率"""
    if startDate is not None:
        args = [curve, startDate, endDate]
    else:
        args = [curve, endDate]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="DefaultProbability")
    except Exception:
        s = f"CreditCurveDefaultProbability except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveRecoveryRates(curve):
    """回收率（返回 JSON 字符串）"""
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="recoveryRates")
    except Exception:
        s = f"CreditCurveRecoveryRates except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveDiscountFactor(curve, endDate):
    """折现因子"""
    args = [curve, endDate]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="DiscountFactor")
    except Exception:
        s = f"CreditCurveDiscountFactor except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveZeroRate(curve, endDate, dayCounter=DayCounter.NONE):
    """零息利率"""
    args = [curve, endDate, dayCounter]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="ZeroRate")
    except Exception:
        s = f"CreditCurveZeroRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def CreditCurveYieldCurve(curve):
    """获取无风险收益率曲线"""
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpCreditCurve", method="YieldCurve")
    except Exception:
        s = f"CreditCurveYieldCurve except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpForwardCurve(args1, args2, args3, args4, args5, fmt='VP|HD'):
    if (args1[-1][0] is None):
        args1 = [row for row in args1 if not all(item is None for item in row)]
    if (args2[-1][0] is None):
        args2 = [row for row in args2 if not all(item is None for item in row)]

    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpForwardCurve')
    except Exception as e:
        s = f"McpForwardCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def ForwardCurveForwardRate(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key='McpForwardCurve', method='ForwardRate')
    except:
        s = f"ForwardCurveForwardRate except: {args}"
        logging.warning(s, exc_info=True)
        return s

############################################
### Forward Curve for Equity & Commodity ###
############################################

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpForwardCurve2(args1, args2, args3, args4, args5, fmt='VP|HD'):
    if (args1[-1][0] is None):
        args1 = [row for row in args1 if not all(item is None for item in row)]
    if (args2[-1][0] is None):
        args2 = [row for row in args2 if not all(item is None for item in row)]

    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpForwardCurve2')
    except Exception as e:
        s = f"McpForwardCurve2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def ForwardCurve2ForwardRate(curve, endDate, bidMidAsk):
    args = [curve, endDate, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key='McpForwardCurve2', method='ForwardRate')
    except:
        s = f"ForwardCurve2ForwardRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


try:
    import mcp_lifecycle  # noqa: F401
except ImportError:
    pass


############################################
### XCCY Basis Curve（交叉货币基差曲线） ###
############################################

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpXccyBasisCurve(args1, args2, args3, args4, args5, fmt="VP"):
    """创建交叉货币基差曲线对象（CrossCurrencySpreadCurve）。三种 KV 签名：

    Path A（FX 远期点报价）：
        ReferenceDate / SpotDate / EndDates(["3M","6M",...] 或日期) / ForwardPoints
        USDDiscountCurve / CNYCleanCurve / FXSpotRate / ScaleFactor(默认1e4)
        Variable(默认SPREADS) / Method(默认LINEARINTERPOLATION) / UseGlobalSolver(默认False)

    Path A2（引用既有 FXFP 曲线，报价零重复）：
        FXForwardPointsCurve(=McpFXForwardPointsCurve 对象) / USDDiscountCurve / CNYCleanCurve
        Variable / Method / UseGlobalSolver

    Path B（基差互换报价，spread 在 CNY/base 腿，decimal）：
        ReferenceDate / SpotDate / EndDates / BasisSpreads
        CNYEstimationCurve / USDEstimationCurve / USDDiscountCurve / CNYCleanCurve / FXSpotRate
        Variable / Method / UseGlobalSolver
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpXccyBasisCurve")
    except Exception as e:
        s = f"McpXccyBasisCurve except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("json_file", "str", "XCCY_BASIS_CURVE_SAMPLE.json 路径")
@xl_arg("curve_id", "str", "如 USDCNY_XCCY_BASIS / USDCNY_XCCY_BASIS_SWAP")
@xl_arg("usdDiscountCurve", "object", "TermLegDiscountingCurve / USD 折现")
@xl_arg("cnyCleanCurve", "object", "UnderlyingCurve / CNY clean")
@xl_arg("fxForwardPointsCurve", "object", "Path A2 必填：被引 FXFP 曲线对象")
@xl_arg("cnyEstimationCurve", "object", "Path B 可选，默认=cnyCleanCurve")
@xl_arg("usdEstimationCurve", "object", "Path B 可选，默认=usdDiscountCurve")
def McpXccyBasisCurveFromJson(json_file, curve_id, usdDiscountCurve, cnyCleanCurve,
                              fxForwardPointsCurve=None, cnyEstimationCurve=None,
                              usdEstimationCurve=None):
    """从 XCCYBasisCurve JSON 段加载基差曲线（依赖曲线由 Excel 对象传入，避免重复报价）。

    Path A2（QuoteType=FX_FORWARD_POINTS_CURVE）：
      需传入 fxForwardPointsCurve（=McpFXForwardPointsCurve 对象，对应 Quotes.FXForwardPointsCurve）
    Path B（QuoteType=BASIS_SWAP_SPREAD）：
      从 JSON 读 Tenors/Spreads/SpotDate/FXSpotRate；估计曲线缺省回退到 clean/usd
    """
    for c in (usdDiscountCurve, cnyCleanCurve):
        if isinstance(c, str):
            return c
    if fxForwardPointsCurve is not None and isinstance(fxForwardPointsCurve, str):
        # Path A2 缺对象时直接返回错误串（避免把错误对象传进 C++）
        if fxForwardPointsCurve.strip() != "":
            # 允许 Excel 空单元格为 None；非空字符串视为上游错误
            pass
    try:
        from excel.xccy_basis_json import build_xccy_basis_curve_from_json
        fxfp = None if (fxForwardPointsCurve is None or isinstance(fxForwardPointsCurve, str)) else fxForwardPointsCurve
        cny_est = None if (cnyEstimationCurve is None or isinstance(cnyEstimationCurve, str)) else cnyEstimationCurve
        usd_est = None if (usdEstimationCurve is None or isinstance(usdEstimationCurve, str)) else usdEstimationCurve
        # Path A2：若 JSON 要求 FXFP 但没传对象，给出明确错误
        if fxfp is None and isinstance(fxForwardPointsCurve, str) and fxForwardPointsCurve.strip():
            return fxForwardPointsCurve
        return build_xccy_basis_curve_from_json(
            json_file, curve_id, usdDiscountCurve, cnyCleanCurve,
            fxfp, cny_est, usd_est)
    except Exception as e:
        s = f"McpXccyBasisCurveFromJson except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def XccyBasisCurveDiscountFactor(curve, startDate, endDate):
    """基差曲线 DF(startDate -> endDate)（spot 锚定查询用 startDate=spotDate）"""
    args = [curve, startDate, endDate]
    try:
        return tool_def.xls_call(*args, key="McpXccyBasisCurve", method="DiscountFactor2")
    except Exception as e:
        s = f"XccyBasisCurveDiscountFactor except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def XccyBasisCurveZeroRate(curve, date):
    """基差曲线零息利率（连续复利，ActActISDA）"""
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpXccyBasisCurve", method="ZeroRate")
    except Exception as e:
        s = f"XccyBasisCurveZeroRate except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def XccyBasisCurveSpread(curve, date):
    """基差曲线 spread（连续零息差，相对 underlying；x10000 得 bp）"""
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpXccyBasisCurve", method="Spread")
    except Exception as e:
        s = f"XccyBasisCurveSpread except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def XccyBasisCurveSpreads(curve, dates, fmt="V"):
    """基差曲线在指定日期序列的 spread（auto_resize 溢出）"""
    args = [curve, dates, fmt]
    try:
        return tool_def.xls_call(*args, key="McpXccyBasisCurve", method="Spreads")
    except Exception as e:
        s = f"XccyBasisCurveSpreads except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def XccyBasisCurveFXSpot(curve):
    """基差曲线的 FX 即期（构造口径，Pair 以 USD 开头时为 1/报价）"""
    args = [curve]
    try:
        return tool_def.xls_call(*args, key="McpXccyBasisCurve", method="GetFXSpot")
    except Exception as e:
        s = f"XccyBasisCurveFXSpot except: {e}"
        logging.warning(s, exc_info=True)
        return s
