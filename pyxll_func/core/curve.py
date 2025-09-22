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
from pyxll import xl_arg, xl_func

# =========================
# Project Internal
# =========================
from mcp import mcp
from mcp.utils.enums import DayCounter, Frequency, enum_wrapper
from mcp.utils.excel_utils import (
    MethodName,
    mcp_kv_wrapper,
    mcp_method_args_cache,
    pf_mcp_date_list,  # noqa: F401 May be used in templates
)
from mcp.mcp import MVanillaSwap  # noqa: F401 Reserved
from mcp.utils.mcp_utils import mcp_dt
from mcp.tool.args_def import tool_def
from mcp.wrapper import McpSwapCurve, trace_args
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
@xl_arg("conventionName", "str")
def McpRateConvention(conventionName):
    try:
        return mcp.wrapper.McpRateConvention(conventionName)
    except Exception as e:
        s = f"McpRateConvention except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def McpName(obj):
    try:
        return obj.toString()
    except Exception as e:
        s = f"McpName except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcSwapStartLag(obj):
    try:
        return obj.swapStartLag()
    except Exception as e:
        s = f"rcSwapStartLag except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcPaymentDateAdjuster(obj):
    try:
        return obj.paymentDateAdjuster()
    except Exception as e:
        s = f"rcPaymentDateAdjuster except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcAccrualDateAdjuster(obj):
    try:
        return obj.accrualDateAdjuster()
    except Exception as e:
        s = f"rcAccrualDateAdjuster except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcFixedDayCounter(obj):
    try:
        return obj.fixedDayCounter()
    except Exception as e:
        s = f"rcFixedDayCounter except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcFloatDayCounter(obj):
    try:
        return obj.floatDayCounter()
    except Exception as e:
        s = f"rcFloatDayCounter except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcFixingMethod(obj):
    try:
        return obj.fixingMethod()
    except Exception as e:
        s = f"rcFixingMethod except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcUseIndexEstimation(obj):
    try:
        return obj.useIndexEstimation()
    except Exception as e:
        s = f"rcUseIndexEstimation except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcFixInAdvance(obj):
    try:
        return obj.fixInAdvance()
    except Exception as e:
        s = f"rcFixInAdvance except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcMargin(obj):
    try:
        return obj.margin()
    except Exception as e:
        s = f"rcMargin except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def rcFixDaysBackward(obj):
    try:
        return obj.fixDaysBackward()
    except Exception as e:
        s = f"rcFixDaysBackward except: {e}"
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
@xl_arg("curve", "object")
@xl_arg("date", "datetime")
def YieldCurveZeroRate(curve, date):
    if isinstance(curve, str):
        return curve
    date_str = date_to_string(date)
    return curve.ZeroRate(date_str)


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
    dayCounter=DayCounter.Act365Fixed,
    compounding=False,
    frequency=Frequency.NoFrequency,
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
        return tool_def.xls_call(*args, key="McpYieldCurve", method="GetRefDate")
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
def SwapCurveZeroRate(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpSwapCurve", method="ZeroRate")
    except Exception as e:
        s = f"SwapCurveZeroRate except: {e}"
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
    result, lack_keys = mcp_kv_wrapper.valid_parse(
        "McpFXForwardPointsCurve", args, fmt, data_fields, kv1, kv2
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)

    vals = result["vals"]
    mcp_item = mcp.wrapper.McpFXForwardPointsCurve(*vals)
    mcp_method_args_cache.cache(str(mcp_item), result)
    return mcp_item


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardPointsCurve2(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
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
def ParametricCurveZeroRate(curve, date):
    args = [curve, date]
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
def BondCurveZeroRate(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="ZeroRate")
    except Exception:
        s = f"BondCurveZeroRate except: {args}"
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
def BondCurveParRate(curve, date):
    args = [curve, date]
    try:
        return tool_def.xls_call(*args, key="McpBondCurve", method="ParRate")
    except Exception:
        s = f"BondCurveParRate except: {args}"
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

