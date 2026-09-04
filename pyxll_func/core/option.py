# -*- coding: utf-8 -*-
"""
Option Pricing Core Module

Provides Excel functions related to options, including:
- Vanilla option pricing
- Option price calculation
- Option Greeks calculation
- Option volatility calculation
- Target Redemption Forward (TARF / Pivot TARF)
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pyxll import xl_func, xl_arg, xl_return

from mcp.forward.fwd_wrapper import payoff_generate_spots
import mcp.mcp_wrapper
from mcp.tool.args_def import tool_def
import mcp.wrapper
from mcp.mcp import MVanillaOption
import mcp.mcp as mcp_mod
import mcp.forward.compound
from mcp.utils.excel_utils import *
from mcp.utils.mcp_utils import *
from mcp.wrapper import McpForwardCurveImpliedFwdPoints, McpForwardCurveForward2ImpliedTermRate, \
    McpForwardCurveImpliedForward, McpForwardCurveForward2ImpliedBaseRate


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaOption(args1, args2, args3, args4, args5, fmt='VP'):
    """
    Create vanilla option object
    
    Parameters:
        args1: Parameter array 1
        args2: Parameter array 2
        args3: Parameter array 3
        args4: Parameter array 4
        args5: Parameter array 5
        fmt: Format string, default is 'VP'
        
    Returns:
        object: Vanilla option object, returns error message if creation fails
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpVanillaOption')
    except Exception as e:
        s = f"McpVanillaOption except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("kv_range", "var[][]")
def McpDigitalOption(kv_range):
    """数字期权构造函数，等价于 McpEuropeanDigital。支持 KV 范围或 xls_create 格式。"""
    try:
        return tool_def.tool_create('McpEuropeanDigital', (kv_range,))
    except Exception as e:
        s = f"McpDigitalOption except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("kv_range", "var[][]")
def McpDoubleDigitalOption(kv_range):
    """双障碍数字期权构造函数，从 KV 范围创建 MDoubleDigitalOption。"""
    try:
        return tool_def.tool_create('McpDoubleDigitalOption', (kv_range,))
    except Exception as e:
        s = f"McpDoubleDigitalOption except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("strikes", "float[]")
@xl_arg("format", "var")
@xl_arg("pricingMethod", "var")
def McpPricesFromStrikes(obj, strikes, fmt="V", pricingMethod=None):
    """
    Calculate option prices based on strike prices
    
    Parameters:
        obj: Option object
        strikes: Strike price array
        fmt: Format method, default is "V"
        pricingMethod: Pricing method, optional
        
    Returns:
        array: Option price array
    """
    if pricingMethod is None:
        prices = obj.prices_from_strikes(strikes)
    else:
        prices = obj.prices_from_strikes(strikes, enum_wrapper.parse2(pricingMethod))
    return as_array(prices, fmt, False)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("pricingMethod", "var")
# def McpPrice(obj, pricingMethod=None):
#     # return obj.Price(pricingMethod)
#     if pricingMethod is None:
#         return obj.Price()
#     else:
#         return obj.Price(enum_wrapper.parse2(pricingMethod))


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("pricingMethod", "var")
# def McpMarketValue(obj, pricingMethod=None):
#     if pricingMethod is None:
#         return obj.MarketValue()
#     else:
#         return obj.MarketValue(enum_wrapper.parse2(pricingMethod))


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("pricingMethod", "var")
# def McpPV(obj, pricingMethod=None):
#     if pricingMethod is None:
#         return obj.PV()
#     else:
#         return obj.PV(enum_wrapper.parse2(pricingMethod))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
@xl_arg("pricingMethod", "var")
def VoPrice(obj, isAmount=True, pricingMethod=None):
    # return obj.Price(pricingMethod)
    if pricingMethod is None:
        return obj.Price(isAmount)
    else:
        return obj.Price(enum_wrapper.parse2(pricingMethod), isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpDelta(obj, isCcy2=True, isAmount=True):
    return obj.Delta(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpGamma(obj, isCcy2=True, isAmount=True):
    return obj.Gamma(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpVega(obj, isCcy2=True, isAmount=True):
    return obj.Vega(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpTheta(obj, isCcy2=True, isAmount=True):
    return obj.Theta(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpVanna(obj, isCcy2=True, isAmount=True):
    return obj.Vanna(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpVolga(obj, isCcy2=True, isAmount=True):
    return obj.Volga(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpRho(obj, isCcy2=True, isAmount=True):
    return obj.Rho(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpPhi(obj, isCcy2=True, isAmount=True):
    return obj.Phi(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def McpForwardDelta(obj, isCcy2=True, isAmount=True):
    return obj.ForwardDelta(isCcy2, isAmount)


# isAmount as parameter
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def McpPrice(obj, isAmount=True):
    tn = type(obj).__name__
    if tn in ("MTargetRedemptionForward", "MPivotTargetRedemptionForward"):
        return obj.Price(-1)
    return obj.Price(isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def McpMarketValue(obj, isAmount=True):
    return obj.MarketValue(isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def McpDiscMarketValue(obj, isAmount=True):
    return obj.DiscMarketValue(isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
@xl_arg("tradePrice", "float")
def McpPnL(obj, isAmount=True, tradePrice=0.0):
    return obj.PnL(isAmount, tradePrice)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
@xl_arg("tradePrice", "float")
def McpDiscPnL(obj, isAmount=True, tradePrice=0.0):
    return obj.DiscPnL(isAmount, tradePrice)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def McpPV(obj, isAmount=True):
    """Excel 端统一 PV 入口，与估值引擎 fx_options_adapter.cpp 中
    PV = DiscMarketValue(true) 保持语义一致（多头有价值为正）。

    优先调用对象自身的 PV(isAmount)；若该对象/类暂未提供 PV（例如较旧的 SWIG
    构建中 MVanillaBarriers / MDigitalOption / MDoubleDigitalOption 等没有
    PV 接口），自动回退到 DiscMarketValue(isAmount)，确保 McpPV 在所有期权
    类型上立即可用且与跑批口径一致。
    """
    r = None
    pv_attr = getattr(obj, "PV", None)
    if callable(pv_attr):
        try:
            r = pv_attr(isAmount)
        except (AttributeError, TypeError, NotImplementedError):
            r = None
    if r is None:
        dmv_attr = getattr(obj, "DiscMarketValue", None)
        if callable(dmv_attr):
            r = dmv_attr(isAmount)
        else:
            raise AttributeError(
                f"{type(obj).__name__} 既未提供 PV 也未提供 DiscMarketValue，无法计算 McpPV"
            )
    return r


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpGamma(obj, isCCY2=True):
#     return obj.Gamma(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpTheta(obj, isCCY2=True):
#     return obj.Theta(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpVega(obj, isCCY2=True):
#     return obj.Vega(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpRho(obj, isCCY2=True):
#     return obj.Rho(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpPhi(obj, isCCY2=True):
#     return obj.Phi(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpVanna(obj, isCCY2=True):
#     return obj.Vanna(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpVolga(obj, isCCY2=True):
#     return obj.Volga(isCCY2)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("obj", "object")
# @xl_arg("isCCY2", "bool")
# def McpForwardDelta(obj, isCCY2=True):
#     return obj.ForwardDelta(isCCY2)

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("valueDates", "datetime[]")
@xl_arg("spots", "float[]")
@xl_arg("format", "var")
@xl_arg("pricingMethod", "var")
@xl_return("var[][]")
def McpPrices(obj, valueDates, spots, fmt="H", pricingMethod=None):
    dates = mcp_dt.to_date_list(valueDates, mcp_dt.to_pure_date)
    if debug_args_info:
        print("McpPrices valueDates: ", dates)
        print("McpPrices spots: ", spots)
    if pricingMethod is None:
        prices = obj.prices(dates, spots)
    else:
        prices = obj.prices(dates, spots, enum_wrapper.parse2(pricingMethod))
    return as_2d_array(prices, fmt, False)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("valueDate", "datetime")
@xl_arg("spots", "float[]")
@xl_return("var[][]")
def McpPayoffBySpots(obj, valueDate, spots):
    valueDate = date_to_string(valueDate)
    result = [[item] for item in payoffs]
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("valueDate", "datetime")
@xl_arg("spot", "var")
@xl_arg("range", "var")
@xl_return("var[][]")
def McpPayoff(obj, valueDate, spot=None, rg=0.03):
    # # print(f"McpPayoff: {obj}, {valueDate}")
    valueDate = date_to_string(valueDate)
    if isinstance(obj, mcp.forward.fwd_wrapper.McpFXForward):
        payoffs = obj.Payoff(valueDate, spot)
        result = as_2d_array(payoffs, "V")
        return result
    else:
        spots, payoffs = obj.payoff(valueDate, spot, rg)
        result = [[spots[i], payoffs[i]] for i in range(len(payoffs))]
        return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VOVegaDigital(vanillaOption):
    return vanillaOption.VegaDigital()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VOVegaIDDigital(vanillaOption):
    return vanillaOption.VegaIDDigital()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VODvegaDvol(vanillaOption):
    return vanillaOption.DvegaDvol()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VODvegaDvol2(vanillaOption):
    return vanillaOption.DvegaDvol2()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VODvegaDspot(vanillaOption):
    return vanillaOption.DvegaDspot()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
def VODd1Dvol(vanillaOption):
    return vanillaOption.Dd1Dvol()


@xl_func(macro=False, recalc_on_open=True)
def VOVolImpliedFromPrice(obj, price):
    args = [obj, price]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='VolImpliedFromPrice')
    except Exception as e:
        # Capture exception type and description
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOVolImpliedFromPrice exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromPrice(obj, price, isAmount=True):
    args = [obj, price, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromPrice')
    except Exception as e:
        # Capture exception type and description
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOStrikeImpliedFromPrice exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VODeltaImpliedFromStrike(obj, strike):
    args = [obj, strike]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='DeltaImpliedFromStrike')
    except Exception as e:
        # Capture exception type and description
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VODeltaImpliedFromStrike exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromDelta(obj, delta, deltaRHS=True, isAmount=True):
    args = [obj, delta, deltaRHS, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromDelta')
    except Exception as e:
        # Capture exception type and description
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOStrikeImpliedFromDelta exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromForwardDelta(obj, delta, deltaRHS=True, isAmount=True):
    args = [obj, delta, deltaRHS, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromForwardDelta')
    except Exception as e:
        # Capture exception type and description
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOStrikeImpliedFromDelta exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
@xl_arg("strike", "float")
def VODeltaImpliedFromStrike(vanillaOption, strike):
    return vanillaOption.DeltaImpliedFromStrike(strike)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("yieldCurve1", "object")
@xl_arg("yieldCurve2", "object")
@xl_arg("calendar", "object")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbGirrDeltas(vanillaOption, yieldCurve1, yieldCurve2, calendar, ccy2LocRate, fmt="V"):
    s = vanillaOption.FrtbGirrDeltas(yieldCurve1.getHandler(),
                                     yieldCurve2.getHandler(),
                                     calendar.getHandler(),
                                     ccy2LocRate)
    return as_2d_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
@xl_arg("ccyLocMarketSpot", "float")
@xl_arg("isLocCcy2", "bool")
@xl_arg("ccy2LocRate", "float")
def VOFrtbFxDelta(vanillaOption, ccyLocMarketSpot, isLocCcy2=True, ccy2LocRate=1.0):
    return vanillaOption.FrtbFxDelta(ccyLocMarketSpot,
                                     pf_bool(isLocCcy2),
                                     ccy2LocRate)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("ccy1LocMarketSpot", "float")
@xl_arg("ccy2LocMarketSpot", "float")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbFxDeltas(vanillaOption, ccy1LocMarketSpot, ccy2LocMarketSpot, ccy2LocRate=1.0, fmt="V"):
    s = vanillaOption.FrtbFxDeltas(ccy1LocMarketSpot,
                                   ccy2LocMarketSpot,
                                   ccy2LocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("volSurface", "object")
@xl_arg("calendar", "object")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbFxVegas(vanillaOption, volSurface, calendar, ccy2LocRate, fmt="V"):
    s = vanillaOption.FrtbFxVegas(volSurface.getHandler(),
                                  calendar.getHandler(),
                                  ccy2LocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("atmSmileCurve", "object")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbFxVegas2(vanillaOption, atmSmileCurve, ccy2LocRate, fmt="V"):
    s = vanillaOption.FrtbFxVegas(atmSmileCurve.getHandler(),
                                  ccy2LocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("yieldCurve1", "object")
@xl_arg("yieldCurve2", "object")
@xl_arg("calendar", "object")
@xl_arg("isUp", "bool")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbGirrCurvatures(vanillaOption, yieldCurve1, yieldCurve2, calendar, isUp, ccy2LocRate, fmt="V"):
    s = vanillaOption.FrtbGirrCurvatures(yieldCurve1.getHandler(),
                                         yieldCurve2.getHandler(),
                                         calendar.getHandler(),
                                         isUp,
                                         ccy2LocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vanillaOption", "object")
@xl_arg("ccyLocMarketSpot", "float")
@xl_arg("isLocCcy2", "bool")
@xl_arg("isUp", "bool")
@xl_arg("ccy2LocRate", "float")
def VOFrtbFxCurvature(vanillaOption, ccyLocMarketSpot, isLocCcy2, isUp, ccy2LocRate=1.0):
    return vanillaOption.FrtbFxCurvature(ccyLocMarketSpot,
                                         isLocCcy2,
                                         isUp,
                                         ccy2LocRate)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vanillaOption", "object")
@xl_arg("ccy1LocMarketSpot", "float")
@xl_arg("ccy2LocMarketSpot", "float")
@xl_arg("isUp", "bool")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def VOFrtbFxCurvatures(vanillaOption, ccy1LocMarketSpot, ccy2LocMarketSpot, isUp, ccy2LocRate=1.0, fmt="V"):
    s = vanillaOption.FrtbFxCurvatures(ccy1LocMarketSpot,
                                       ccy2LocMarketSpot,
                                       isUp,
                                       ccy2LocRate)
    return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("valueDate", "datetime")
@xl_return("var[][]")
def McpPayoffByDate(obj, valueDate):
    valueDate = date_to_string(valueDate)
    try:
        s = obj.Payoff(valueDate)
        arr = json.loads(s)
        spots, payoffs = arr[0], arr[1]
    except:
        spots, payoffs = [], []
    result = [[spots[i], payoffs[i]] for i in range(len(payoffs))]
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("spot", "float")
@xl_arg("range", "float")
@xl_arg("count", "int")
@xl_arg("format", "str")
@xl_return("var[][]")
def McpRange(spot, rg=0.03, count=30, fmt="V"):
    spots, d_step = payoff_generate_spots(spot, rg, count)
    return as_array(spots, fmt, False)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('pair', 'str')
@xl_arg('forward', 'float')
@xl_arg('spot', 'float')
@xl_arg('termRate', 'float')
@xl_arg('spotDate', 'datetime')
@xl_arg('deliveryDate', 'datetime')
def Forward2ImpliedBaseRate(pair, forward, spot, termRate, spotDate, deliveryDate):
    # Check if parameters are empty
    if pair is None or forward is None or spot is None or termRate is None or spotDate is None or deliveryDate is None:
        raise ValueError("no enough parameters!")
    return McpForwardCurveForward2ImpliedBaseRate(pair, forward, spot, termRate, spotDate.strftime("%Y/%m/%d"),
                                                  deliveryDate.strftime("%Y/%m/%d"));


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('pair', 'str')
@xl_arg('forward', 'float')
@xl_arg('spot', 'float')
@xl_arg('baseRate', 'float')
@xl_arg('spotDate', 'datetime')
@xl_arg('deliveryDate', 'datetime')
def Forward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate, deliveryDate):
    # Check if parameters are empty
    if pair is None or forward is None or spot is None or baseRate is None or spotDate is None or deliveryDate is None:
        raise ValueError("no enough parameters!")
    return McpForwardCurveForward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate.strftime("%Y/%m/%d"),
                                                  deliveryDate.strftime("%Y/%m/%d"));


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('pair', 'str')
@xl_arg('baseRate', 'float')
@xl_arg('termRate', 'float')
@xl_arg('spot', 'float')
@xl_arg('spotDate', 'datetime')
@xl_arg('deliveryDate', 'datetime')
def ImpliedForward(pair, baseRate, termRate, spot, spotDate, deliveryDate):
    # Check if parameters are empty
    if pair is None or baseRate is None or spot is None or termRate is None or spotDate is None or deliveryDate is None:
        raise ValueError("no enough parameters!")
    return McpForwardCurveImpliedForward(pair, baseRate, termRate, spot, spotDate.strftime("%Y/%m/%d"),
                                         deliveryDate.strftime("%Y/%m/%d"));


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('pair', 'str')
@xl_arg('baseRate', 'float')
@xl_arg('termRate', 'float')
@xl_arg('spot', 'float')
@xl_arg('spotDate', 'datetime')
@xl_arg('deliveryDate', 'datetime')
def ImpliedFwdPoints(pair, baseRate, termRate, spot, spotDate, deliveryDate):
    # Check if parameters are empty
    if pair is None or baseRate is None or spot is None or termRate is None or spotDate is None or deliveryDate is None:
        raise ValueError("no enough parameters!")
    return McpForwardCurveImpliedFwdPoints(pair, baseRate, termRate, spot, spotDate.strftime("%Y/%m/%d"),
                                           deliveryDate.strftime("%Y/%m/%d"));


# @xl_func(macro=False, recalc_on_open=True)
# def VOVegaDigital(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='VegaDigital')
#     except:
#         s = f"VOVegaDigital except: {args}"
#         logging.warning(s, exc_info=True)
#         return s


# @xl_func(macro=False, recalc_on_open=True)
# def VOVegaIDDigital(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='VegaIDDigital')
#     except:
#         s = f"VOVegaIDDigital except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VODvegaDvol(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='DvegaDvol')
#     except:
#         s = f"VODvegaDvol except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VODvegaDvol2(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='DvegaDvol2')
#     except:
#         s = f"VODvegaDvol2 except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VODvegaDspot(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='DvegaDspot')
#     except:
#         s = f"VODvegaDspot except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VODd1Dvol(obj):
#     args = [obj]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='Dd1Dvol')
#     except:
#         s = f"VODd1Dvol except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VOVolImpliedFromPrice(obj, price):
#     args = [obj, price]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='VolImpliedFromPrice')
#     except:
#         s = f"VOVolImpliedFromPrice except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VOStrikeImpliedFromPrice(obj, price):
#     args = [obj, price]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromPrice')
#     except:
#         s = f"VOStrikeImpliedFromPrice except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VODeltaImpliedFromStrike(obj, strike):
#     args = [obj, strike]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='DeltaImpliedFromStrike')
#     except:
#         s = f"VODeltaImpliedFromStrike except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
# @xl_func(macro=False, recalc_on_open=True)
# def VOStrikeImpliedFromDelta(obj, delta, deltaInUnderlyingCurrency):
#     args = [obj, delta, deltaInUnderlyingCurrency]
#     try:
#         return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromDelta')
#     except:
#         s = f"VOStrikeImpliedFromDelta except: {args}"
#         logging.warning(s, exc_info=True)
#         return s
#
#
def _vo_get_market(obj, method_name, attr_fallbacks=()):
    """VOGet* 共用：支持 Vanilla / Digital / Barrier。

    优先调对象自身的 getter（Vanilla 走 C++，Digital/Barrier 走
    Python wrapper）；再回退到 wrapper 缓存字段。
    """
    fn = getattr(obj, method_name, None)
    if callable(fn):
        try:
            return fn()
        except (AttributeError, TypeError, NotImplementedError):
            pass
    for attr in attr_fallbacks:
        if hasattr(obj, attr):
            return getattr(obj, attr)
    raise AttributeError(f"{type(obj).__name__} 不支持 {method_name}")


@xl_func(macro=False, recalc_on_open=True)
def VOGetSpot(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetSpot", ("spotPx",))
    except Exception as e:
        s = f"VOGetSpot except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetForward(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetForward", ("forward",))
    except Exception as e:
        s = f"VOGetForward except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetVol(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetVol", ("volatility",))
    except Exception as e:
        s = f"VOGetVol except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetStrike(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetStrike", ("strikePx",))
    except Exception as e:
        s = f"VOGetStrike except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetAccRate(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetAccRate", ("accRate",))
    except Exception as e:
        s = f"VOGetAccRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VOGetUndRate(obj):
    args = [obj]
    try:
        return _vo_get_market(obj, "GetUndRate", ("undRate",))
    except Exception as e:
        s = f"VOGetUndRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VOGetOptionType(obj):
    args = [obj]
    try:
        key = tool_def.xls_call(*args, key='McpVanillaOption', method='GetCallPutType')
        return enum_wrapper.key_of_value(key, "CallPut")
    except Exception as e:
        s = f"VOGetOptionType except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)

@xl_func(macro=False, recalc_on_open=True)
def VOGetBuySell(obj):
    args = [obj]
    try:
        key = tool_def.xls_call(*args, key='McpVanillaOption', method='GetBuySell')
        return enum_wrapper.key_of_value(key, "BuySell")
    except Exception as e:
        s = f"VOGetBuySell except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)



@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vo", "object")
def VOAmericanExerciseBoundaries(vo):
    s = vo.AmericanExerciseBoundaries()
    d = as_2d_array(s, "H")
    result = [[key, str(value)] for key, value in d.items()]
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaStrategy(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpVanillaStrategy')
    except Exception as e:
        s = f"McpVanillaStrategy except: {e}"
        return s
    
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetStrategyType(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetStrategyType')
    except  Exception as e:
        s = f"VSGetStrategyType except: {e}"
        return s

    
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetDeltaString(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetDeltaString')
    except  Exception as e:
        s = f"VSGetDeltaString except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetReferenceDate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetReferenceDate')
    except  Exception as e:
        s = f"VSGetReferenceDate except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetExpiryDate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetExpiryDate')
    except  Exception as e:
        s = f"VSGetExpiryDate except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetDeliveryDate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetDeliveryDate')
    except  Exception as e:
        s = f"VSGetDeliveryDate except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetSpot(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetSpot')
    except  Exception as e:
        s = f"VSGetSpot except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetForward(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetForward')
    except  Exception as e:
        s = f"VSGetForward except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSGetFwdPoints(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetFwdPoints')
    except  Exception as e:
        s = f"VSGetFwdPoints except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSPrice(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='Price')
    except  Exception as e:
        s = f"VSPrice except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSDelta(obj, isCcy2 = True, isAmount = True):
    args = [obj, isCcy2, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='Delta')
    except  Exception as e:
        s = f"VSDelta except: {e}"
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSGamma(obj, isCcy2=True, isAmount=True):
    return obj.Gamma(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSVega(obj, isCcy2=True, isAmount=True):
    return obj.Vega(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSTheta(obj, isCcy2=True, isAmount=True):
    return obj.Theta(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSVanna(obj, isCcy2=True, isAmount=True):
    return obj.Vanna(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSVolga(obj, isCcy2=True, isAmount=True):
    return obj.Volga(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSRho(obj, isCcy2=True, isAmount=True):
    return obj.Rho(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSPhi(obj, isCcy2=True, isAmount=True):
    return obj.Phi(isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def VSForwardDelta(obj, isCcy2 = True, isAmount = True):
    args = [obj, isCcy2, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='ForwardDelta')
    except  Exception as e:
        s = f"VSForwardDelta except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def VSVolatility(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaStrategy', method='Volatility')
    except  Exception as e:
        s = f"VSVolatility except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("fmt", "str")
def VSGetLegNames(obj, fmt="V"):
    args = [obj]
    try:
        str = tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetLegNames')
        return as_array(str, fmt)
    except  Exception as e:
        s = f"VSGetLegNames except: {e}"
        return s

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg('legName', 'str')
def VSGetLeg(obj, legName):
    args = [obj, legName]
    try:
        handler = tool_def.xls_call(*args, key='McpVanillaStrategy', method='GetLeg')
        #handler = obj.GetCurve(bidMidAsk)
        return mcp.wrapper.MVanillaOption(handler)
    except  Exception as e:
        s = f"VSVolatility except: {e}"
        return s

### Asian Option ###

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
@xl_arg("price", "float")
def AOVolImpliedFromPrice(asianOption, price):
    return asianOption.VolImpliedFromPrice(price)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
@xl_arg("price", "float")
def AOStrikeImpliedFromPrice(asianOption, price):
    return asianOption.StrikeImpliedFromPrice(price)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
@xl_arg("runMode", "int")
def AOMonteCarloPrice(asianOption, runMode):
    return asianOption.MonteCarloPrice(runMode)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
def AONumFixings(asianOption):
    return asianOption.GetNumFixings()


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
def AONumFixDone(asianOption):
    return asianOption.GetNumFixDone()


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("asianOption", "object")
def AOAveRate(asianOption):
    return asianOption.GetAveRate()


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("asianOption", "object")
@xl_arg("fmt", "str")
def AOFixingSchedule2(asianOption, fmt="V"):
    s = asianOption.GetFixingSchedule()
    return as_array(s, fmt)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpAsianOption(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpAsianOption')
    except Exception as e:
        s = f"McpAsianOption except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AOVolImpliedFromPrice(obj, price):
    args = [obj, price]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='VolImpliedFromPrice')
    except Exception as e:
        s = f"AOVolImpliedFromPrice except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AOStrikeImpliedFromPrice(obj, price):
    args = [obj, price]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='StrikeImpliedFromPrice')
    except Exception as e:
        s = f"AOStrikeImpliedFromPrice except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AOAveRate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='AveRate')
    except Exception as e:
        s = f"AOAveRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AONumFixDone(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='NumFixDone')
    except Exception as e:
        s = f"AONumFixDone except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AONumFixings(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='NumFixings')
    except Exception as e:
        s = f"AONumFixings except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def AOFixingSchedule(obj, fmt='V'):
    args = [obj, fmt]
    try:
        return tool_def.xls_call(*args, key='McpAsianOption', method='FixingSchedule')
    except Exception as e:
        s = f"AOFixingSchedule except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

### Vanilla Barrier Option ###

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaBarriers(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpVanillaBarriers')
    except Exception as e:
        s = f"McpVanillaBarriers except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


# =========================
# Target Redemption Forward (TARF / BONUS_TARF / Pivot TARF)
# 构造: McpTarf / McpPivotTarf (VP)
# 估值: McpPrice / McpTarfFixingSchedule
# Greeks: McpDelta / McpGamma / … (通用函数)
# =========================

_FX_VOL_TENORS = (
    "ON", "1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y", "3Y", "4Y", "5Y"
)


def _tarf_add_months(d, months):
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    mdays = [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(y, m, min(d.day, mdays[m - 1]))


def _tarf_tenor_date(ref, tenor):
    t = str(tenor).upper()
    if t == "ON":
        return ref + timedelta(days=1)
    if t == "TN":
        return ref + timedelta(days=2)
    if t in ("SW", "1W"):
        return ref + timedelta(days=7)
    if t.endswith("W"):
        return ref + timedelta(days=7 * int(t[:-1]))
    if t.endswith("M"):
        return _tarf_add_months(ref, int(t[:-1]))
    if t.endswith("Y"):
        return _tarf_add_months(ref, 12 * int(t[:-1]))
    return ref


def _tarf_parse_ref_date(reference_date):
    if reference_date is None or reference_date == "":
        return None
    if isinstance(reference_date, datetime):
        return reference_date.date()
    if isinstance(reference_date, date):
        return reference_date
    return mcp_dt.parse_date(str(reference_date)).date()


def _tarf_build_mvol_surface_from_fx(fx_vol, reference_date, spot):
    """MVE buildTarfVolSurfaceFromFx 的 Python 等价：FXVolSurface -> VolatilitySurface。"""
    ref_dt = _tarf_parse_ref_date(reference_date)
    if ref_dt is None:
        ref_dt = _tarf_parse_ref_date(fx_vol.GetReferenceDate())
    spot = float(spot or fx_vol.GetSpot())
    spot_date = ref_dt + timedelta(days=2)

    expiry_dates = []
    delivery_dates = []
    atm_vols = []
    dom_rates = []
    for_rates = []
    for tenor in _FX_VOL_TENORS:
        try:
            exp_dt = _tarf_tenor_date(ref_dt, tenor)
            exp_str = mcp_dt.to_date1(datetime.combine(exp_dt, datetime.min.time()))
            atm_vols.append(float(fx_vol.GetATMVol(exp_str)) / 100.0)
            dom_rates.append(float(fx_vol.GetDomesticRate(exp_str, False)))
            for_rates.append(float(fx_vol.GetForeignRate(exp_str, False)))
            expiry_dates.append(exp_str)
            del_dt = exp_dt + timedelta(days=2)
            delivery_dates.append(mcp_dt.to_date1(datetime.combine(del_dt, datetime.min.time())))
        except Exception:
            continue

    if not expiry_dates:
        exp_dt = ref_dt + timedelta(days=365)
        exp_str = mcp_dt.to_date1(datetime.combine(exp_dt, datetime.min.time()))
        del_str = mcp_dt.to_date1(datetime.combine(exp_dt + timedelta(days=2), datetime.min.time()))
        expiry_dates = [exp_str]
        delivery_dates = [del_str]
        atm_vols = [0.08]
        dom_rates = [0.02]
        for_rates = [0.04]

    zeros = [0.0] * len(expiry_dates)
    ref_str = mcp_dt.to_date1(datetime.combine(ref_dt, datetime.min.time()))
    spot_str = mcp_dt.to_date1(datetime.combine(spot_date, datetime.min.time()))
    return mcp_mod.MVolatilitySurface(
        ref_str,
        spot_str,
        spot,
        True,
        True,
        2,
        1,
        1,
        json.dumps(expiry_dates),
        json.dumps(delivery_dates),
        json.dumps(atm_vols),
        json.dumps(zeros),
        json.dumps(zeros),
        json.dumps(zeros),
        json.dumps(zeros),
        json.dumps(dom_rates),
        json.dumps(for_rates),
    )


def _tarf_mcp_wrapper_and_handler(obj, label="object"):
    """与 VanillaOption 一致：保留 Python wrapper，构造时再 getHandler()。"""
    if obj is None:
        raise ValueError("%s is required" % label)
    if isinstance(obj, str):
        raise ValueError("Invalid %s: %s" % (label, obj))
    if hasattr(obj, "getHandler"):
        return obj, obj.getHandler()
    raise ValueError("Unsupported %s type: %s" % (label, type(obj).__name__))


def _tarf_vol_surface_wrapper_and_handler(vol_obj, reference_date, spot):
    """MFXVolSurface -> MVolatilitySurface（MVE buildTarfVolSurfaceFromFx 等价），返回 (wrapper, handler)。"""
    if vol_obj is None:
        raise ValueError("VolSurface is required")
    if isinstance(vol_obj, str):
        raise ValueError("Invalid VolSurface: " + vol_obj)
    tn = type(vol_obj).__name__
    if tn in ("MFXVolSurface", "McpFXVolSurface"):
        mvol = _tarf_build_mvol_surface_from_fx(vol_obj, reference_date, spot)
        return mvol, mvol.getHandler()
    if tn in ("MVolatilitySurface", "McpVolatilitySurface"):
        return vol_obj, vol_obj.getHandler()
    if hasattr(vol_obj, "getHandler"):
        return vol_obj, vol_obj.getHandler()
    raise ValueError("Unsupported VolSurface type: " + tn)


_TARF_ARGS_KVS = [
    ("ReferenceDate", "date"),
    ("ExpiryDate", "date"),
    ("Frequency", "const"),
    ("Spot", "float"),
    ("Strike", "float"),
    ("Target", "float"),
    ("Leverage", "float"),
    ("BuySell", "const"),
    ("PayoffStyle", "const"),
    ("FaceValue", "float"),
    ("BonusAmount", "float", 0.0),
    ("Calendar", "object"),
    ("VolSurface", "object"),
    ("PrevSettlementDate", "date", ""),
    ("FirstSettlementDate", "date"),
    ("DateAdjuster", "const"),
    ("EndToEnd", "bool", True),
    ("LongStub", "bool", False),
    ("EndStub", "bool", False),
    ("DayCounter", "const"),
    ("ApplyDayCount", "bool", True),
    ("NumSimulation", "int", 8000),
    ("McSeed", "int", 0),
]

_PIVOT_TARF_EXTRA_KVS = [
    ("HighStrike", "float"),
    ("LowStrike", "float"),
    ("Pivot", "float"),
]


def _ensure_tarf_kv_method(method, kvs):
    if method not in mcp_kv_wrapper.kv_dict:
        mcp_kv_wrapper.add_method(method, kvs)


def _tarf_camel_attr(field_name):
    s = str(field_name)
    if not s:
        return s
    return s[0].lower() + s[1:]


def _parse_tarf_kv(method, args_list, fmt, kvs):
    _ensure_tarf_kv_method(method, kvs)
    result, lack_keys = mcp_kv_wrapper.valid_parse(method, args_list, fmt, [], kvs)
    if lack_keys:
        raise ValueError("%s missing fields: %s" % (method, ", ".join(lack_keys)))
    return result


def _build_tarf_object(result, args_cls, product_cls):
    mc_seed = 0
    field_map = {}
    keepalive = []
    for view, val in zip(result["keys"], result["vals"]):
        if view == "McSeed":
            mc_seed = int(val or 0)
            continue
        if val is None and view != "PrevSettlementDate":
            continue
        field_map[view] = val

    args = args_cls()
    ref_date = field_map.get("ReferenceDate", "")
    spot = field_map.get("Spot", 0.0)
    for view, val in field_map.items():
        if view == "VolSurface":
            wrapper, handler = _tarf_vol_surface_wrapper_and_handler(val, ref_date, spot)
            args.volSurface = handler
            keepalive.append(wrapper)
        elif view == "Calendar":
            wrapper, handler = _tarf_mcp_wrapper_and_handler(val, "Calendar")
            args.calendar = handler
            keepalive.append(wrapper)
        elif view == "PrevSettlementDate" and (val is None or val == ""):
            args.prevSettlementDate = ""
        else:
            setattr(args, _tarf_camel_attr(view), val)
    tarf = product_cls(args)
    if keepalive:
        tarf._mcp_keepalive = keepalive
    if mc_seed:
        tarf.SetMcSeed(mc_seed)
    return tarf


def _create_tarf(args1, args2, args3, args4, args5, fmt, method, kvs, args_cls, product_cls):
    args_list = [a for a in (args1, args2, args3, args4, args5) if a is not None]
    try:
        result = _parse_tarf_kv(method, args_list, fmt, kvs)
        return _build_tarf_object(result, args_cls, product_cls)
    except Exception as e:
        s = "%s except: %s" % (method, e)
        logging.exception("%s failed", method)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpTarf(args1, args2, args3, args4, args5, fmt="VP"):
    """从 VP 键值块直接构造 MTargetRedemptionForward（含可选 McSeed）。"""
    return _create_tarf(
        args1, args2, args3, args4, args5, fmt,
        "McpTarf", _TARF_ARGS_KVS,
        mcp_mod.TarfArgs, mcp_mod.MTargetRedemptionForward,
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpPivotTarf(args1, args2, args3, args4, args5, fmt="VP"):
    """从 VP 键值块直接构造 MPivotTargetRedemptionForward。"""
    kvs = _TARF_ARGS_KVS + _PIVOT_TARF_EXTRA_KVS
    return _create_tarf(
        args1, args2, args3, args4, args5, fmt,
        "McpPivotTarf", kvs,
        mcp_mod.PivotTarfArgs, mcp_mod.MPivotTargetRedemptionForward,
    )


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("tarf", "object")
@xl_arg("price", "float")
@xl_arg("tolerance", "float")
@xl_arg("max_iterations", "int")
def McpTarfTargetImplied(tarf, price, tolerance=1e-6, max_iterations=100):
    return tarf.TargetImpliedFromPrice(float(price), float(tolerance), int(max_iterations))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("tarf", "object")
@xl_arg("price", "float")
@xl_arg("tolerance", "float")
@xl_arg("max_iterations", "int")
def McpTarfStrikeImplied(tarf, price, tolerance=1e-6, max_iterations=100):
    return tarf.StrikeImpliedFromPrice(float(price), float(tolerance), int(max_iterations))


def _tarf_parse_fixing_dates(raw):
    """C++ vecDate2Str 逗号分隔，或 JSON 数组字符串 → 扁平 date 列表。"""
    if raw is None or raw == "":
        return []
    s = str(raw).strip()
    if s.startswith("["):
        try:
            arr = json.loads(s)
            return [str(d).strip() for d in arr if d is not None and str(d).strip()]
        except Exception:
            pass
    return [str(d).strip() for d in s.split(",") if str(d).strip()]


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("tarf", "object")
@xl_arg("fmt", "str")
@xl_arg("reserve", "int")
def McpTarfFixingSchedule(tarf, fmt="V", reserve=5):
    """TARF Fixing 日期列表（扁平 list，再按 fmt 铺表）。

    fmt: V=纵向一列，H=横向一行（与 AOFixingSchedule2 / as_array 一致）。
    reserve: 最少占用行(V)或列(H)数，不足补空串，避免 spill 覆盖下方内容。
    """
    dates = _tarf_parse_fixing_dates(tarf.FixingSchedule())
    fmt_u = str(fmt or "V").upper()
    min_slots = max(int(reserve or 0), len(dates))
    if min_slots > len(dates):
        dates = dates + [""] * (min_slots - len(dates))
    return as_array(dates, fmt_u, do_load=False)


### Digital Option ###

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEuropeanDigital(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpEuropeanDigital')
    except Exception as e:
        s = f"McpEuropeanDigital except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


# =========================
# Experimental FX Forward (EMFXForward / McpEFXForward)
# 对应 mcplib.h 中 Experimental::EMFXForward
# 说明：
#   - 构造函数支持 3 种重载：
#       (1) 直接给 SpotPx + ForwardPoints + 利率
#       (2) 通过单边 FXForwardPointsCurve + 双边利率曲线
#       (3) 通过双边 FXForwardPointsCurve2 + 双边利率曲线
#   - 通用 Greeks/PV/PnL 函数（McpPrice/McpDelta/McpGamma/McpVega/McpTheta/
#     McpRho/McpVanna/McpVolga/McpForwardDelta/McpMarketValue/
#     McpDiscMarketValue/McpPnL/McpDiscPnL）已经可以直接作用于 EFXForward 对象，
#     无需重复定义；这里仅补充 EFXForward 专属的 Getter 函数。
# =========================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEFXForward(args1, args2, args3, args4, args5, fmt="VP"):
    """构造 Experimental FX Forward 对象（McpEFXForward）。"""
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpEFXForward")
    except Exception as e:
        s = f"McpEFXForward except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


def _efxfwd_safe_call(name, fn, *args):
    try:
        return fn(*args)
    except Exception as e:
        s = f"EfxFwd{name} except: {e}"
        logging.warning(s, exc_info=True)
        return s


# ---- Getters ---------------------------------------------------------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetReferenceDate(obj):
    return _efxfwd_safe_call("GetReferenceDate", obj.GetReferenceDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetDeliveryDate(obj):
    return _efxfwd_safe_call("GetDeliveryDate", obj.GetDeliveryDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetBuySell(obj):
    return _efxfwd_safe_call("GetBuySell", obj.GetBuySell)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetFaceValue(obj):
    return _efxfwd_safe_call("GetFaceValue", obj.GetFaceValue)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetStrike(obj):
    return _efxfwd_safe_call("GetStrike", obj.GetStrike)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetTimeToDelivery(obj):
    return _efxfwd_safe_call("GetTimeToDelivery", obj.GetTimeToDelivery)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetSpot(obj):
    return _efxfwd_safe_call("GetSpot", obj.GetSpot)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetDomesticRate(obj):
    return _efxfwd_safe_call("GetDomesticRate", obj.GetDomesticRate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetForeignRate(obj):
    return _efxfwd_safe_call("GetForeignRate", obj.GetForeignRate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdGetForward(obj):
    return _efxfwd_safe_call("GetForward", obj.GetForward)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
def EfxFwdScaleFactor(obj):
    return _efxfwd_safe_call("ScaleFactor", obj.ScaleFactor)


# ---- Pricing / PnL ---------------------------------------------------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def EfxFwdPrice(obj, isAmount=True):
    return _efxfwd_safe_call("Price", obj.Price, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def EfxFwdMarketValue(obj, isAmount=True):
    return _efxfwd_safe_call("MarketValue", obj.MarketValue, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def EfxFwdDiscMarketValue(obj, isAmount=True):
    return _efxfwd_safe_call("DiscMarketValue", obj.DiscMarketValue, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
@xl_arg("tradePrice", "float")
def EfxFwdPnL(obj, isAmount=True, tradePrice=0.0):
    return _efxfwd_safe_call("PnL", obj.PnL, isAmount, tradePrice)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
@xl_arg("tradePrice", "float")
def EfxFwdDiscPnL(obj, isAmount=True, tradePrice=0.0):
    return _efxfwd_safe_call("DiscPnL", obj.DiscPnL, isAmount, tradePrice)


# ---- Greeks ----------------------------------------------------------------

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdDelta(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Delta", obj.Delta, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdGamma(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Gamma", obj.Gamma, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdVega(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Vega", obj.Vega, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdTheta(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Theta", obj.Theta, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdRho(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Rho", obj.Rho, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdForwardDelta(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("ForwardDelta", obj.ForwardDelta, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdVanna(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Vanna", obj.Vanna, isCcy2, isAmount)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isCcy2", "bool")
@xl_arg("isAmount", "bool")
def EfxFwdVolga(obj, isCcy2=False, isAmount=True):
    return _efxfwd_safe_call("Volga", obj.Volga, isCcy2, isAmount)