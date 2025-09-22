# -*- coding: utf-8 -*-
"""
Interest Rate Swap Core Module (Excel/PyXLL UDF Export)

Provides Excel functions related to interest rate swaps, including:
- Vanilla interest rate swap pricing
- Cross-currency swap pricing
- Swap cash flow analysis
- Swap risk metrics calculation
- Swaption / CapFloor / CapletFloorlet construction and risk metrics
"""

# =========================
# Standard Library
# =========================
import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Union

# =========================
# Third Party Library (PyXLL)
# =========================
from pyxll import RTD, xl_arg, xl_func, xl_return

# =========================
# 项目内模块
# =========================
from mcp import mcp
import mcp.wrapper
from mcp.tool.args_def import tool_def
from mcp.utils.excel_utils import *
from mcp.utils.mcp_utils import *

# 注意：如确需通配导入（部分符号运行时注入），可改回:
# from mcp.utils.mcp_utils import *
# 但建议尽量显式导入使用到的符号以降低命名污染。


# -------------- Vanilla / Cross Currency Swaps --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaSwap(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建香草利率互换对象
    参数:
        args1~args5: Excel 区域参数片段（键值/表格）
        fmt: 参数解析格式（例如 'VP'）
    返回:
        对象句柄或错误信息
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpVanillaSwap")
    except Exception as e:
        s = f"McpVanillaSwap except: {e}"
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
def McpXCurrencySwap(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建跨货币互换对象（XCCY Swap）
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpXCurrencySwap")
    except Exception as e:
        s = f"McpXCurrencySwap except: {e}"
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
def McpCurrencySwapLeg(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建（跨货币）互换的某一条腿对象，便于单腿分析。
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpCurrencySwapLeg")
    except Exception as e:
        s = f"McpCurrencySwapLeg except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("swap", "object")
@xl_arg("newStartDate", "datetime")
@xl_arg("newEndDate", "datetime")
def SwapClone(swap, newStartDate, newEndDate):
    """
    基于既有 VanillaSwap 克隆一个新期限的互换
    """
    try:
        handler = swap.Clone(newStartDate.strftime("%Y/%m/%d"), newEndDate.strftime("%Y/%m/%d"))
        return mcp.wrapper.McpVanillaSwap(handler)
    except Exception as e:
        s = f"SwapClone except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("swap", "object")
@xl_arg("ccyLocRate", "float")
@xl_arg("fmt", "str")
def SwapFrtbGirrDeltas(swap, ccyLocRate=1.0, fmt="V"):
    """
    返回 FRTB GIRR（一般利率风险）Delta 序列
    """
    s = swap.FrtbGirrDeltas(ccyLocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("swap", "object")
@xl_arg("ccyLocRate", "float")
def SwapFrtbFxDelta(swap, ccyLocRate):
    """
    返回 FRTB 外汇风险 Delta（折算系数 ccyLocRate）
    """
    return swap.FrtbFxDelta(ccyLocRate)


# -------------- Vanilla Swap 基本指标 --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapNPV(vanillaSwap):
    """
    互换净现值 NPV
    """
    val = vanillaSwap.NPV()
    print("call SwapNPV:", val, vanillaSwap)
    return val


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapMarketValue(vanillaSwap):
    return vanillaSwap.MarketValue()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapPremium(vanillaSwap):
    return vanillaSwap.Premium()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapAccrued(vanillaSwap):
    return vanillaSwap.Accrued()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapPVBP(vanillaSwap):
    return vanillaSwap.PVBP()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapAnnuity(vanillaSwap):
    return vanillaSwap.Annuity()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapMarketParRate(vanillaSwap):
    return vanillaSwap.MarketParRate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapDuration(vanillaSwap):
    return vanillaSwap.Duration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapMDuration(vanillaSwap):
    return vanillaSwap.MDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapPV01(vanillaSwap):
    return vanillaSwap.PV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapDV01(vanillaSwap):
    return vanillaSwap.DV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapCF(vanillaSwap):
    """
    全部现金流（可能以 JSON 或对象序列返回，取决于底层实现）
    """
    return vanillaSwap.CF()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapValuationDayCF(vanillaSwap):
    """
    估值日当日现金流（例如应计或支付）
    """
    return vanillaSwap.ValuationDayCF()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapSumDelta(vanillaSwap):
    """
    合计 Delta（按内部定义的聚合口径）
    """
    return vanillaSwap.SumDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("start", "datetime")
@xl_arg("end", "datetime")
def SwapPNL(vanillaSwap, start, end):
    """
    指定区间 PNL
    """
    start = mcp_dt.to_date1(start)
    end = mcp_dt.to_date1(end)
    result = vanillaSwap.PNL(start, end)
    print("SwapPNL", result, start, end)
    return result


# -------------- Vanilla Swap: Fixed/Floating Leg 细分指标 --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegCumCF(vanillaSwap):
    return vanillaSwap.FixedLegCumCF()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegCumCF(vanillaSwap):
    return vanillaSwap.FloatingLegCumCF()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("npv", "float")
def SwapCalculateSwapRateFromNPV(vanillaSwap, npv):
    """
    反解固定利率以匹配给定 NPV
    """
    val = vanillaSwap.CalculateSwapRateFromNPV(npv)
    print("call SwapCalculateSwapRateFromNPV:", npv, val, vanillaSwap)
    return val


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("npv", "float")
def SwapCalculateFloatingMarginFromNPV(vanillaSwap, npv):
    """
    反解浮动边际（Margin）以匹配给定 NPV
    """
    val = vanillaSwap.CalculateFloatingMarginFromNPV(npv)
    print("call SwapCalculateFloatingMarginFromNPV:", npv, val, vanillaSwap)
    return val


# Fixed Leg 单腿指标
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegAnnuity(vanillaSwap):
    return vanillaSwap.FixedLegAnnuity()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegAccrued(vanillaSwap):
    return vanillaSwap.FixedLegAccrued()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegMarketValue(vanillaSwap):
    return vanillaSwap.FixedLegMarketValue()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegNPV(vanillaSwap):
    return vanillaSwap.FixedLegNPV()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegPremium(vanillaSwap):
    return vanillaSwap.FixedLegPremium()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegPVBP(vanillaSwap):
    return vanillaSwap.FixedLegPVBP()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegPV01(vanillaSwap):
    return vanillaSwap.FixedLegPV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegDV01(vanillaSwap):
    return vanillaSwap.FixedLegDV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegDuration(vanillaSwap):
    return vanillaSwap.FixedLegDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegMDuration(vanillaSwap):
    return vanillaSwap.FixedLegMDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFixedLegCumPV(vanillaSwap):
    return vanillaSwap.FixedLegCumPV()


# Floating Leg 单腿指标
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegAnnuity(vanillaSwap):
    return vanillaSwap.FloatingLegAnnuity()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegAccrued(vanillaSwap):
    return vanillaSwap.FloatingLegAccrued()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegMarketValue(vanillaSwap):
    return vanillaSwap.FloatingLegMarketValue()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegNPV(vanillaSwap):
    return vanillaSwap.FloatingLegNPV()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegPremium(vanillaSwap):
    return vanillaSwap.FloatingLegPremium()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegPVBP(vanillaSwap):
    return vanillaSwap.FloatingLegPVBP()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegPV01(vanillaSwap):
    return vanillaSwap.FloatingLegPV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegDV01(vanillaSwap):
    return vanillaSwap.FloatingLegDV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegDuration(vanillaSwap):
    return vanillaSwap.FloatingLegDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegMDuration(vanillaSwap):
    return vanillaSwap.FloatingLegMDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaSwap", "object")
def SwapFloatingLegCumPV(vanillaSwap):
    return vanillaSwap.FloatingLegCumPV()


# -------------- Legs/Resets/Quotes 明细表（用于 Excel 展示） --------------

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFixedLegs(vanillaSwap, fields):
    """
    固定腿支付期明细（按 fields 指定的列顺序返回二维数组）
    """
    PaymentDates = json.loads(vanillaSwap.FixedLegPaymentDates())
    AccrStartDates = json.loads(vanillaSwap.FixedLegAccrStartDates())
    AccrEndDates = json.loads(vanillaSwap.FixedLegAccrEndDates())
    AccrDays = json.loads(vanillaSwap.FixedLegAccrDays())
    AccrYearFrac = json.loads(vanillaSwap.FixedLegAccrYearFrac())
    AccrRates = json.loads(vanillaSwap.FixedLegAccrRates())
    Payments = json.loads(vanillaSwap.FixedLegPayments())
    DiscountFactors = json.loads(vanillaSwap.FixedLegDiscountFactors())
    PVs = json.loads(vanillaSwap.FixedLegPVs())
    CumPVs = json.loads(vanillaSwap.FixedLegCumPVs())
    PaymentDateYearFracs = json.loads(vanillaSwap.FixedLegPaymentDateYearFracs())
    CFs = json.loads(vanillaSwap.FixedLegCFs())
    AmortAmounts = json.loads(vanillaSwap.FixedLegAmortAmounts())
    ResidualAmounts = json.loads(vanillaSwap.FixedLegResidualAmounts())
    Notionals = json.loads(vanillaSwap.FixedLegNotionals())

    # 有期初交换则期初（StartDate）也作为 payment，但无利息相关数据
    hasInitialPayment = vanillaSwap.FixedLegHasInitialExchange()
    if hasInitialPayment:
        AccrStartDates.insert(0, "N/A")
        AccrEndDates.insert(0, "N/A")
        AccrDays.insert(0, "N/A")
        AccrYearFrac.insert(0, "N/A")
        AccrRates.insert(0, "N/A")

    rows = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
            "AmortAmounts": AmortAmounts[i],
            "ResidualAmounts": ResidualAmounts[i],
            "Notionals": Notionals[i],
        }
        if i < len(CFs):
            po["CF"] = CFs[i]
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFixedResetLegs(vanillaSwap, fields):
    """
    固定腿 Reset 明细（某些实现中固定腿也存在重置逻辑，如折现基准/会计口径）
    """
    ResetDates = json.loads(vanillaSwap.FixedLegResetDates())
    ResetStartDates = json.loads(vanillaSwap.FixedLegResetStartDates())
    ResetEndDates = json.loads(vanillaSwap.FixedLegResetEndDates())
    ResetDays = json.loads(vanillaSwap.FixedLegResetDays())
    ResetYearFrac = json.loads(vanillaSwap.FixedLegResetYearFrac())
    ResetRates = json.loads(vanillaSwap.FixedLegResetRates())

    rows = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFloatingLegs(vanillaSwap, fields):
    """
    浮动腿支付期明细
    """
    PaymentDates = json.loads(vanillaSwap.FloatingLegPaymentDates())
    AccrStartDates = json.loads(vanillaSwap.FloatingLegAccrStartDates())
    AccrEndDates = json.loads(vanillaSwap.FloatingLegAccrEndDates())
    AccrDays = json.loads(vanillaSwap.FloatingLegAccrDays())
    AccrYearFrac = json.loads(vanillaSwap.FloatingLegAccrYearFrac())
    AccrRates = json.loads(vanillaSwap.FloatingLegAccrRates())
    Payments = json.loads(vanillaSwap.FloatingLegPayments())
    DiscountFactors = json.loads(vanillaSwap.FloatingLegDiscountFactors())
    PVs = json.loads(vanillaSwap.FloatingLegPVs())
    CumPVs = json.loads(vanillaSwap.FloatingLegCumPVs())
    PaymentDateYearFracs = json.loads(vanillaSwap.FloatingLegPaymentDateYearFracs())
    CFs = json.loads(vanillaSwap.FloatingLegCFs())
    AmortAmounts = json.loads(vanillaSwap.FloatingLegAmortAmounts())
    ResidualAmounts = json.loads(vanillaSwap.FloatingLegResidualAmounts())
    Notionals = json.loads(vanillaSwap.FloatingLegNotionals())

    # 有期初交换则期初（StartDate）也作为 payment，但无利息相关数据
    hasInitialPayment = vanillaSwap.FloatingLegHasInitialExchange()
    if hasInitialPayment:
        AccrStartDates.insert(0, "N/A")
        AccrEndDates.insert(0, "N/A")
        AccrDays.insert(0, "N/A")
        AccrYearFrac.insert(0, "N/A")
        AccrRates.insert(0, "N/A")

    rows = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
            "AmortAmounts": AmortAmounts[i],
            "ResidualAmounts": ResidualAmounts[i],
            "Notionals": Notionals[i],
        }
        if i < len(CFs):
            po["CF"] = CFs[i]
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFloatingResetLegs(vanillaSwap, fields):
    """
    浮动腿 Reset 明细（每期重置利率等）
    """
    ResetDates = json.loads(vanillaSwap.FloatingLegResetDates())
    ResetStartDates = json.loads(vanillaSwap.FloatingLegResetStartDates())
    ResetEndDates = json.loads(vanillaSwap.FloatingLegResetEndDates())
    ResetDays = json.loads(vanillaSwap.FloatingLegResetDays())
    ResetYearFrac = json.loads(vanillaSwap.FloatingLegResetYearFrac())
    ResetRates = json.loads(vanillaSwap.FloatingLegResetRates())

    rows = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFloatingQuoteLegs(vanillaSwap, fields):
    """
    浮动腿报价/观测序列（用于检查每期的报价日期、类型、利率等）
    """
    QuoteDates = json.loads(vanillaSwap.FloatingLegQuoteDates())
    QuoteValueDates = json.loads(vanillaSwap.FloatingLegQuoteValueDates())
    QuoteRates = json.loads(vanillaSwap.FloatingLegQuoteRates())
    QuoteTypes = json.loads(vanillaSwap.FloatingLegQuoteTypes())

    rows = []
    for i in range(len(QuoteDates)):
        po = {
            "QuoteDate": QuoteDates[i],
            "QuoteValueDate": QuoteValueDates[i],
            "QuoteRate": QuoteRates[i],
            "QuoteType": QuoteTypes[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


def copy_dict(dest, src):
    """
    浅拷贝字典键值，用于将重置/支付信息合并到同一条记录中
    """
    for key in src:
        dest[key] = src[key]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaSwap", "object")
@xl_arg("fields", "str[]")
def SwapFloatingQuotes(vanillaSwap, fields):
    """
    将浮动腿的报价、重置与支付信息关联到同一记录上返回（便于审计）
    - 如果报价数量多于重置数量：按报价列表驱动，并尽量填充匹配的 reset/payment 信息
    - 否则按 reset 列表驱动，并补充匹配的 quote/payment 信息
    """
    PaymentDates = json.loads(vanillaSwap.FloatingLegPaymentDates())
    AccrStartDates = json.loads(vanillaSwap.FloatingLegAccrStartDates())
    AccrEndDates = json.loads(vanillaSwap.FloatingLegAccrEndDates())
    AccrDays = json.loads(vanillaSwap.FloatingLegAccrDays())
    AccrYearFrac = json.loads(vanillaSwap.FloatingLegAccrYearFrac())
    AccrRates = json.loads(vanillaSwap.FloatingLegAccrRates())
    Payments = json.loads(vanillaSwap.FloatingLegPayments())
    DiscountFactors = json.loads(vanillaSwap.FloatingLegDiscountFactors())
    PVs = json.loads(vanillaSwap.FloatingLegPVs())
    CumPVs = json.loads(vanillaSwap.FloatingLegCumPVs())
    PaymentDateYearFracs = json.loads(vanillaSwap.FloatingLegPaymentDateYearFracs())
    CFs = json.loads(vanillaSwap.FloatingLegCFs())

    # 期初交换处理
    hasInitialPayment = vanillaSwap.FloatingLegHasInitialExchange()
    if hasInitialPayment:
        AccrStartDates.insert(0, "N/A")
        AccrEndDates.insert(0, "N/A")
        AccrDays.insert(0, "N/A")
        AccrYearFrac.insert(0, "N/A")
        AccrRates.insert(0, "N/A")

    payment_dict: Dict[Any, Dict[str, Any]] = {}
    payment_list: List[Dict[str, Any]] = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
            "CF": CFs[i],
        }
        payment_dict[po["AccrEndDate"]] = po
        payment_list.append(po)

    ResetDates = json.loads(vanillaSwap.FloatingLegResetDates())
    ResetStartDates = json.loads(vanillaSwap.FloatingLegResetStartDates())
    ResetEndDates = json.loads(vanillaSwap.FloatingLegResetEndDates())
    ResetDays = json.loads(vanillaSwap.FloatingLegResetDays())
    ResetYearFrac = json.loads(vanillaSwap.FloatingLegResetYearFrac())
    ResetRates = json.loads(vanillaSwap.FloatingLegResetRates())
    reset_dict: Dict[Any, Dict[str, Any]] = {}
    reset_list: List[Dict[str, Any]] = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
            "Index": i,
        }
        reset_list.append(po)
        reset_dict[po["ResetDate"]] = po  # 以 ResetDate 为键（与报价匹配）

    QuoteDates = json.loads(vanillaSwap.FloatingLegQuoteDates())
    QuoteValueDates = json.loads(vanillaSwap.FloatingLegQuoteValueDates())
    QuoteRates = json.loads(vanillaSwap.FloatingLegQuoteRates())
    QuoteTypes = json.loads(vanillaSwap.FloatingLegQuoteTypes())
    quote_list: List[Dict[str, Any]] = []
    quote_dict: Dict[Any, Dict[str, Any]] = {}
    for i in range(len(QuoteDates)):
        po = {
            "QuoteDate": QuoteDates[i],
            "QuoteValueDate": QuoteValueDates[i],
            "QuoteRate": QuoteRates[i],
            "QuoteType": QuoteTypes[i],
        }
        quote_list.append(po)
        quote_dict[po["QuoteValueDate"]] = po

    po_list: List[Dict[str, Any]] = []
    if len(quote_list) > len(reset_list):
        # 报价更多：以报价列表为主，尽量向前一条合并 reset/payment
        for i, po in enumerate(quote_list):
            po_list.append(po)
            if po["QuoteValueDate"] in reset_dict and i >= 0:
                prev_po = quote_list[i]  # 紧挨的这一条（与原逻辑保持一致）
                reset_po = reset_dict[po["QuoteValueDate"]]
                copy_dict(prev_po, reset_po)
                payment_po = payment_list[reset_po["Index"]]
                copy_dict(prev_po, payment_po)
    else:
        # Reset 更多或相等：以 Reset 列表为主，按 FixInAdvance 决定匹配键
        fixInAdvance = vanillaSwap.FloatingLegFixInAdvance()
        for i, po in enumerate(reset_list):
            po_list.append(po)
            key = po["ResetStartDate"] if fixInAdvance else po["ResetEndDate"]
            if key in quote_dict:
                quote_po = quote_dict[key]
                copy_dict(po, quote_po)
            payment_po = payment_list[i]
            copy_dict(po, payment_po)

    # 重排为二维数组返回
    result: List[List[Any]] = []
    for item in po_list:
        row = []
        for field in fields:
            row.append(item.get(field, ""))
        result.append(row)
    return result


# -------------- Black76 Swaption --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
def McpBlack76Swaption(args1, args2, args3, args4, args5):
    """
    通过键值解析创建 Black76 Swaption
    """
    args = [args1, args2, args3, args4, args5]
    result, lack_keys = mcp_kv_wrapper.parse_and_validate2(
        MethodName.McpBlack76Swaption,
        args,
        [
            ("UnderlyingSwap", "mcphandler"),
            ("SwaptionExpiry", "date"),
            ("Vol", "float"),
            ("HaveVol", "bool"),
            ("PayReceiveType", "const"),
            ("SettlementDate", "date"),
            ("SettlementMethod", "const"),
        ],
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    print("McpBlack76Swaption vals:", vals)
    forward = mcp.wrapper.MBlack76Swaption(*vals)
    mcp_method_args_cache.cache(str(forward), result)
    return forward


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bls", "object")
@xl_arg("estimationYieldCurveBaseLeg", "object")
@xl_arg("discountingYieldCurveBaseLeg", "object")
@xl_arg("estimationYieldCurveTermLeg", "object")
@xl_arg("discountingYieldCurveTermLeg", "object")
@xl_arg("fxRate", "float")
def BlsPrice(
    bls,
    estimationYieldCurveBaseLeg,
    discountingYieldCurveBaseLeg,
    estimationYieldCurveTermLeg,
    discountingYieldCurveTermLeg,
    fxRate,
):
    """
    计算跨曲线/跨币种环境下的 Black76 Swaption 价格
    """
    return bls.Price(
        estimationYieldCurveBaseLeg.getHandler(),
        discountingYieldCurveBaseLeg.getHandler(),
        estimationYieldCurveTermLeg.getHandler(),
        discountingYieldCurveTermLeg.getHandler(),
        fxRate,
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bls", "object")
@xl_arg("estimationYieldCurveBaseLeg", "object")
@xl_arg("discountingYieldCurveBaseLeg", "object")
@xl_arg("estimationYieldCurveTermLeg", "object")
@xl_arg("discountingYieldCurveTermLeg", "object")
def BlsVega(
    bls,
    estimationYieldCurveBaseLeg,
    discountingYieldCurveBaseLeg,
    estimationYieldCurveTermLeg,
    discountingYieldCurveTermLeg,
):
    return bls.Vega(
        estimationYieldCurveBaseLeg.getHandler(),
        discountingYieldCurveBaseLeg.getHandler(),
        estimationYieldCurveTermLeg.getHandler(),
        discountingYieldCurveTermLeg.getHandler(),
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bls", "object")
@xl_arg("estimationYieldCurveBaseLeg", "object")
@xl_arg("discountingYieldCurveBaseLeg", "object")
@xl_arg("estimationYieldCurveTermLeg", "object")
@xl_arg("discountingYieldCurveTermLeg", "object")
@xl_arg("upDown", "int")
def BlsVomma(
    bls,
    estimationYieldCurveBaseLeg,
    discountingYieldCurveBaseLeg,
    estimationYieldCurveTermLeg,
    discountingYieldCurveTermLeg,
    upDown,
):
    return bls.Vomma(
        estimationYieldCurveBaseLeg.getHandler(),
        discountingYieldCurveBaseLeg.getHandler(),
        estimationYieldCurveTermLeg.getHandler(),
        discountingYieldCurveTermLeg.getHandler(),
        upDown,
    )


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("bls", "object")
@xl_arg("bumpedCurves", "object")
def BlsPV01(bls, bumpedCurves):
    """
    在一组 bump 后的曲线集上计算 PV01（结果按列返回）
    """
    if not isinstance(bls, mcp.MBlack76Swaption):
        return "Parameter 1 is not MBlack76Swaption"
    if not isinstance(bumpedCurves, mcp.MPV01_Set):
        return "Parameter 2 is not MPV01_Set"
    s = bls.PV01(bumpedCurves.getHandler())
    arr = json.loads(s)
    result = [[item] for item in arr]
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("baseCurve", "object")
@xl_arg("bumps", "float[]")
@xl_arg("UseReverseCumulative", "bool")
def McpPV01_Set(baseCurve, bumps, UseReverseCumulative=False):
    """
    构建一组曲线 PV01 bump 设置（供 BlsPV01 使用）
    """
    return mcp.MPV01_Set(baseCurve.getHandler(), json.dumps(bumps), UseReverseCumulative)


# -------------- Cross Currency Swap 指标导出 --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapNPV(xCurrencySwap, isResultTermCurrency=True):
    val = xCurrencySwap.NPV(isResultTermCurrency)
    return val


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapPremium(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.Premium(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapAccrued(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.Accrued(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapMarketValue(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.MarketValue(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapMarketParRate(xCurrencySwap):
    return xCurrencySwap.MarketParRate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapDuration(xCurrencySwap):
    return xCurrencySwap.Duration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapMDuration(xCurrencySwap):
    return xCurrencySwap.MDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapPV01(xCurrencySwap):
    return xCurrencySwap.PV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapDV01(xCurrencySwap):
    return xCurrencySwap.DV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapCF(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.CF(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapValuationDayCF(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.ValuationDayCF(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapSumDelta(xCurrencySwap):
    return xCurrencySwap.SumDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("start", "datetime")
@xl_arg("end", "datetime")
def XCcySwapPNL(xCurrencySwap, start, end):
    start = mcp_dt.to_date1(start)
    end = mcp_dt.to_date1(end)
    result = xCurrencySwap.PNL(start, end)
    print("SwapPNL", result, start, end)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegNPV(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegNPV(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegMarketValue(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegMarketValue(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegAccrued(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegAccrued(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegCumCF(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegCumCF(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("npv", "float")
def XCcySwapCalculateSwapRateFromNPV(xCurrencySwap, npv):
    val = xCurrencySwap.CalculateSwapRateFromNPV(npv)
    print("call XCcySwapCalculateSwapRateFromNPV:", npv, val, xCurrencySwap)
    return val


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("npv", "float")
def XCcySwapCalculateTermMarginFromNPV(xCurrencySwap, npv):
    val = xCurrencySwap.CalculateTermMarginFromNPV(npv)
    print("call XCcySwapCalculateTermMarginFromNPV:", npv, val, xCurrencySwap)
    return val


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegAnnuity(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegAnnuity(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapBaseLegDuration(xCurrencySwap):
    return xCurrencySwap.BaseLegDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapBaseLegMDuration(xCurrencySwap):
    return xCurrencySwap.BaseLegMDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegCumPV(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegCumPV(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapBaseLegCumCF(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.BaseLegCumCF(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegNPV(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegNPV(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegMarketValue(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegMarketValue(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegAccrued(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegAccrued(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegAnnuity(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegAnnuity(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapTermLegDuration(xCurrencySwap):
    return xCurrencySwap.TermLegDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
def XCcySwapTermLegMDuration(xCurrencySwap):
    return xCurrencySwap.TermLegMDuration()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapTermLegCumPV(xCurrencySwap, isResultTermCurrency=True):
    return xCurrencySwap.TermLegCumPV(isResultTermCurrency)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapFixedLegs(xCurrencySwap, isBaseLeg, fields, isResultTermCurrency=True):
    """
    跨货币互换的固定腿支付明细（Base/Term 可选）
    """
    if isBaseLeg:
        PaymentDates = json.loads(xCurrencySwap.BaseLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.BaseLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.BaseLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.BaseLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.BaseLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.BaseLegAccrRates())
        Payments = json.loads(xCurrencySwap.BaseLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.BaseLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.BaseLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.BaseLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.BaseLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.BaseLegCFs(isResultTermCurrency))
    else:
        PaymentDates = json.loads(xCurrencySwap.TermLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.TermLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.TermLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.TermLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.TermLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.TermLegAccrRates())
        Payments = json.loads(xCurrencySwap.TermLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.TermLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.TermLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.TermLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.TermLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.TermLegCFs(isResultTermCurrency))

    rows = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
        }
        if i < len(CFs):
            po["CF"] = CFs[i]
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
def XCcySwapFixedResetLegs(xCurrencySwap, isBaseLeg, fields):
    """
    跨货币互换固定腿 Reset 明细
    """
    if isBaseLeg:
        ResetDates = json.loads(xCurrencySwap.BaseLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.BaseLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.BaseLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.BaseLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.BaseLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.BaseLegResetRates())
    else:
        ResetDates = json.loads(xCurrencySwap.TermLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.TermLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.TermLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.TermLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.TermLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.TermLegResetRates())

    rows = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapFloatingLegs(xCurrencySwap, isBaseLeg, fields, isResultTermCurrency=True):
    """
    跨货币互换浮动腿支付明细
    """
    if isBaseLeg:
        PaymentDates = json.loads(xCurrencySwap.BaseLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.BaseLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.BaseLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.BaseLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.BaseLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.BaseLegAccrRates())
        Payments = json.loads(xCurrencySwap.BaseLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.BaseLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.BaseLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.BaseLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.BaseLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.BaseLegCFs(isResultTermCurrency))
    else:
        PaymentDates = json.loads(xCurrencySwap.TermLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.TermLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.TermLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.TermLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.TermLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.TermLegAccrRates())
        Payments = json.loads(xCurrencySwap.TermLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.TermLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.TermLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.TermLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.TermLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.TermLegCFs(isResultTermCurrency))

    rows = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
        }
        if i < len(CFs):
            po["CF"] = CFs[i]
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
def XCcySwapFloatingResetLegs(xCurrencySwap, isBaseLeg, fields):
    """
    跨货币互换浮动腿 Reset 明细
    """
    if isBaseLeg:
        ResetDates = json.loads(xCurrencySwap.BaseLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.BaseLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.BaseLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.BaseLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.BaseLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.BaseLegResetRates())
    else:
        ResetDates = json.loads(xCurrencySwap.TermLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.TermLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.TermLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.TermLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.TermLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.TermLegResetRates())

    rows = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
def XCcySwapFloatingQuoteLegs(xCurrencySwap, isBaseLeg, fields):
    """
    跨货币互换浮动腿报价/观测序列
    """
    if isBaseLeg:
        QuoteDates = json.loads(xCurrencySwap.BaseLegQuoteDates())
        QuoteValueDates = json.loads(xCurrencySwap.BaseLegQuoteValueDates())
        QuoteRates = json.loads(xCurrencySwap.BaseLegQuoteRates())
        QuoteTypes = json.loads(xCurrencySwap.BaseLegQuoteTypes())
    else:
        QuoteDates = json.loads(xCurrencySwap.TermLegQuoteDates())
        QuoteValueDates = json.loads(xCurrencySwap.TermLegQuoteValueDates())
        QuoteRates = json.loads(xCurrencySwap.TermLegQuoteRates())
        QuoteTypes = json.loads(xCurrencySwap.TermLegQuoteTypes())

    rows = []
    for i in range(len(QuoteDates)):
        po = {
            "QuoteDate": QuoteDates[i],
            "QuoteValueDate": QuoteValueDates[i],
            "QuoteRate": QuoteRates[i],
            "QuoteType": QuoteTypes[i],
        }
        rows.append(po)

    result = []
    for i, row in enumerate(rows, start=1):
        obj = [f"Period{i}"]
        for field in fields:
            obj.append(row[field])
        result.append(obj)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("xCurrencySwap", "object")
@xl_arg("isBaseLeg", "bool")
@xl_arg("fields", "str[]")
@xl_arg("isResultTermCurrency", "bool")
def XCcySwapFloatingQuotes(xCurrencySwap, isBaseLeg, fields, isResultTermCurrency=True):
    """
    关联浮动腿报价、重置与支付信息（跨货币版本）
    """
    if isBaseLeg:
        PaymentDates = json.loads(xCurrencySwap.BaseLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.BaseLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.BaseLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.BaseLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.BaseLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.BaseLegAccrRates())
        Payments = json.loads(xCurrencySwap.BaseLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.BaseLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.BaseLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.BaseLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.BaseLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.BaseLegCFs(isResultTermCurrency))
    else:
        PaymentDates = json.loads(xCurrencySwap.TermLegPaymentDates())
        AccrStartDates = json.loads(xCurrencySwap.TermLegAccrStartDates())
        AccrEndDates = json.loads(xCurrencySwap.TermLegAccrEndDates())
        AccrDays = json.loads(xCurrencySwap.TermLegAccrDays())
        AccrYearFrac = json.loads(xCurrencySwap.TermLegAccrYearFrac())
        AccrRates = json.loads(xCurrencySwap.TermLegAccrRates())
        Payments = json.loads(xCurrencySwap.TermLegPayments(isResultTermCurrency))
        DiscountFactors = json.loads(xCurrencySwap.TermLegDiscountFactors())
        PVs = json.loads(xCurrencySwap.TermLegPVs(isResultTermCurrency))
        CumPVs = json.loads(xCurrencySwap.TermLegCumPVs(isResultTermCurrency))
        PaymentDateYearFracs = json.loads(xCurrencySwap.TermLegPaymentDateYearFracs())
        CFs = json.loads(xCurrencySwap.TermLegCFs(isResultTermCurrency))

    payment_dict: Dict[Any, Dict[str, Any]] = {}
    payment_list: List[Dict[str, Any]] = []
    for i in range(len(PaymentDates)):
        po = {
            "PaymentDate": PaymentDates[i],
            "AccrStartDate": AccrStartDates[i],
            "AccrEndDate": AccrEndDates[i],
            "AccrDay": AccrDays[i],
            "AccrYearFrac": AccrYearFrac[i],
            "AccrRate": AccrRates[i],
            "Payment": Payments[i],
            "DiscountFactor": DiscountFactors[i],
            "PV": PVs[i],
            "CumPV": CumPVs[i],
            "PaymentDateYearFrac": PaymentDateYearFracs[i],
            "CF": CFs[i],
        }
        payment_dict[po["AccrEndDate"]] = po
        payment_list.append(po)

    if isBaseLeg:
        ResetDates = json.loads(xCurrencySwap.BaseLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.BaseLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.BaseLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.BaseLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.BaseLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.BaseLegResetRates())
    else:
        ResetDates = json.loads(xCurrencySwap.TermLegResetDates())
        ResetStartDates = json.loads(xCurrencySwap.TermLegResetStartDates())
        ResetEndDates = json.loads(xCurrencySwap.TermLegResetEndDates())
        ResetDays = json.loads(xCurrencySwap.TermLegResetDays())
        ResetYearFrac = json.loads(xCurrencySwap.TermLegResetYearFrac())
        ResetRates = json.loads(xCurrencySwap.TermLegResetRates())

    reset_dict: Dict[Any, Dict[str, Any]] = {}
    reset_list: List[Dict[str, Any]] = []
    for i in range(len(ResetDates)):
        po = {
            "ResetDate": ResetDates[i],
            "ResetStartDate": ResetStartDates[i],
            "ResetEndDate": ResetEndDates[i],
            "ResetDay": ResetDays[i],
            "ResetYearFrac": ResetYearFrac[i],
            "ResetRate": ResetRates[i],
            "Index": i,
        }
        reset_list.append(po)
        reset_dict[po["ResetEndDate"]] = po

    if isBaseLeg:
        QuoteDates = json.loads(xCurrencySwap.BaseLegQuoteDates())
        QuoteValueDates = json.loads(xCurrencySwap.BaseLegQuoteValueDates())
        QuoteRates = json.loads(xCurrencySwap.BaseLegQuoteRates())
        QuoteTypes = json.loads(xCurrencySwap.BaseLegQuoteTypes())
    else:
        QuoteDates = json.loads(xCurrencySwap.TermLegQuoteDates())
        QuoteValueDates = json.loads(xCurrencySwap.TermLegQuoteValueDates())
        QuoteRates = json.loads(xCurrencySwap.TermLegQuoteRates())
        QuoteTypes = json.loads(xCurrencySwap.TermLegQuoteTypes())

    quote_list: List[Dict[str, Any]] = []
    quote_dict: Dict[Any, Dict[str, Any]] = {}
    for i in range(len(QuoteDates)):
        po = {
            "QuoteDate": QuoteDates[i],
            "QuoteValueDate": QuoteValueDates[i],
            "QuoteRate": QuoteRates[i],
            "QuoteType": QuoteTypes[i],
        }
        quote_list.append(po)
        quote_dict[po["QuoteValueDate"]] = po

    po_list: List[Dict[str, Any]] = []
    if len(quote_list) > len(reset_list):
        for i in range(len(quote_list)):
            po = quote_list[i]
            po_list.append(po)
            if po["QuoteValueDate"] in reset_dict and i - 1 >= 0:
                prev_po = quote_list[i - 1]
                reset_po = reset_dict[po["QuoteValueDate"]]
                copy_dict(prev_po, reset_po)
                payment_po = payment_list[reset_po["Index"]]
                copy_dict(prev_po, payment_po)
    else:
        for i, po in enumerate(reset_list):
            po_list.append(po)
            if po["ResetDate"] in quote_dict:
                quote_po = quote_dict[po["ResetDate"]]
                copy_dict(po, quote_po)
            payment_po = payment_list[i]
            copy_dict(po, payment_po)

    result: List[List[Any]] = []
    for item in po_list:
        row = []
        for field in fields:
            row.append(item.get(field, ""))
        result.append(row)

    return result


# -------------- Swaption（构造 & Greeks） --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpSwaption(args1, args2, args3, args4, args5, fmt="VP"):
    """
    通过工具统一入口创建 Swaption（Black76 版）
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpBlack76Swaption")
    except Exception as e:
        s = f"DefMcpBlack76Swaption except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionPrice1(obj):
    return obj.Price()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionNPV(obj):
    return obj.NPV()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionDV01(obj):
    return obj.DV01()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionDelta(obj):
    return obj.Delta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionGamma(obj):
    return obj.Gamma()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionVega(obj):
    return obj.Vega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionVanna(obj):
    return obj.Vanna()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def SwaptionTheta(obj):
    return obj.Theta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def McpGetReferenceDate(obj):
    return obj.GetReferenceDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def McpGetStartDate(obj):
    return obj.GetStartDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def McpGetEndDate(obj):
    return obj.GetEndDate()


# -------------- CapFloor（组合） --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCapFloor(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 Cap/Floor 组合
    Excel 模板可参考：
      IROptionType, ReferenceDate, StartDate, Maturity,
      PaymentFrequency, Strike, PaymentType,
      PriceVol, DiscountCurve, CapVolStripping,
      BuySellCap, DayCounter, Notional, Calendar
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpCapFloor")
    except Exception as e:
        return f"DefMcpCapFloor except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorPrice(obj):
    """=CapFloorPrice(obj)"""
    return obj.Price()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("idx", "int")
def CapFloorGetCaplet(obj, idx):
    """=CapFloorGetCaplet(obj, idx) -> 返回单个 Caplet/Floorlet 句柄"""
    handler = obj.GetCaplet(idx)
    return mcp.wrapper.McpCapletFloorlet(handler)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorGetNumCaplets(obj):
    """=CapFloorGetNumCaplets(obj)"""
    return obj.GetNumCaplets()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorExpiryDates(obj):
    """=CapFloorExpiryDates(obj) -> array of long"""
    return obj.ExpiryDates()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorMaturityDates(obj):
    """=CapFloorMaturityDates(obj) -> array of long"""
    return obj.MaturityDates()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorSpotDelta(obj):
    """=CapFloorSpotDelta(obj)"""
    return obj.SpotDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorFwdDelta(obj):
    """=CapFloorFwdDelta(obj)"""
    return obj.FwdDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorSpotVega(obj):
    """=CapFloorSpotVega(obj)"""
    return obj.SpotVega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorFwdVega(obj):
    """=CapFloorFwdVega(obj)"""
    return obj.FwdVega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorSpotGamma(obj):
    """=CapFloorSpotGamma(obj)"""
    return obj.SpotGamma()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapFloorFwdGamma(obj):
    """=CapFloorFwdGamma(obj)"""
    return obj.FwdGamma()


# -------------- Caplet/Floorlet（单期） --------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCapLetFloorLet(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建单期 Caplet/Floorlet
    典型字段：
      ReferenceDate (date), YieldCurve (object),
      CapFloorType (const), Strike (float), Volatility (float),
      ExpiryDate (date), MaturityDate (date),
      InAdvance (bool), PriceVol (bool), BuySellCap (int),
      DayCounter (const), Notional (float)
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpCapLetFloorLet")
    except Exception as e:
        return f"DefMcpCapLetFloorLet except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletPrice(obj):
    """=CapfloorletPrice(obj)"""
    return obj.Price()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletValueDate(obj):
    """=CapfloorletValueDate(obj)"""
    return obj.ValueDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletExpiryDate(obj):
    """=CapfloorletExpiryDate(obj)"""
    return obj.ExpiryDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletMaturityDate(obj):
    """=CapfloorletMaturityDate(obj)"""
    return obj.MaturityDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletFixingDate(obj):
    """=CapfloorletFixingDate(obj)"""
    return obj.FixingDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletCalcStartDate(obj):
    """=CapfloorletCalcStartDate(obj)"""
    return obj.CalcStartDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletCalcEndDate(obj):
    """=CapfloorletCalcEndDate(obj)"""
    return obj.CalcEndDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletRateStartDate(obj):
    """=CapfloorletRateStartDate(obj)"""
    return obj.RateStartDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletRateEndDate(obj):
    """=CapfloorletRateEndDate(obj)"""
    return obj.RateEndDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletPaymentDate(obj):
    """=CapfloorlePaymentDate(obj)"""
    return obj.PaymentDate()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletSpotDelta(obj):
    """=CapfloorletSpotDelta(obj)"""
    return obj.SpotDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletFwdDelta(obj):
    """=CapfloorletFwdDelta(obj)"""
    return obj.FwdDelta()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletSpotVega(obj):
    """=CapfloorletSpotVega(obj)"""
    return obj.SpotVega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletFwdVega(obj):
    """=CapfloorletFwdVega(obj)"""
    return obj.FwdVega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletSpotGamma(obj):
    """=CapfloorletSpotGamma(obj)"""
    return obj.SpotGamma()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def CapfloorletFwdGamma(obj):
    """=CapfloorletFwdGamma(obj)"""
    return obj.FwdGamma()