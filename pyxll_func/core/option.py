# -*- coding: utf-8 -*-
"""
期权定价核心模块

提供期权相关的Excel函数，包括：
- 香草期权定价
- 期权价格计算
- 期权希腊字母计算
- 期权波动率计算
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from pyxll import xl_func, xl_arg, xl_return

from mcp.forward.fwd_wrapper import payoff_generate_spots
import mcp.mcp_wrapper
from mcp.tool.args_def import tool_def
import mcp.wrapper
from mcp.mcp import MVanillaOption
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
    创建香草期权对象
    
    参数:
        args1: 参数数组1
        args2: 参数数组2
        args3: 参数数组3
        args4: 参数数组4
        args5: 参数数组5
        fmt: 格式化字符串，默认为'VP'
        
    返回:
        object: 香草期权对象，如果创建失败则返回错误信息
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpVanillaOption')
    except Exception as e:
        s = f"McpVanillaOption except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("strikes", "float[]")
@xl_arg("format", "var")
@xl_arg("pricingMethod", "var")
def McpPricesFromStrikes(obj, strikes, fmt="V", pricingMethod=None):
    """
    根据执行价格计算期权价格
    
    参数:
        obj: 期权对象
        strikes: 执行价格数组
        fmt: 格式化方式，默认为"V"
        pricingMethod: 定价方法，可选
        
    返回:
        array: 期权价格数组
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


# isAmount作为参数
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def McpPrice(obj, isAmount=True):
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
    return obj.PV(isAmount)


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
        # 捕获异常类型和描述
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOVolImpliedFromPrice exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromPrice(obj, price, isAmount=True):
    args = [obj, price, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromPrice')
    except Exception as e:
        # 捕获异常类型和描述
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOStrikeImpliedFromPrice exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VODeltaImpliedFromStrike(obj, strike):
    args = [obj, strike]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='DeltaImpliedFromStrike')
    except Exception as e:
        # 捕获异常类型和描述
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VODeltaImpliedFromStrike exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromDelta(obj, delta, deltaRHS=True, isAmount=True):
    args = [obj, delta, deltaRHS, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromDelta')
    except Exception as e:
        # 捕获异常类型和描述
        error_message = f"{type(e).__name__}: {str(e)}"
        logging.warning(f"VOStrikeImpliedFromDelta exception: {args}. Error: {error_message}", exc_info=True)
        return error_message


@xl_func(macro=False, recalc_on_open=True)
def VOStrikeImpliedFromForwardDelta(obj, delta, deltaRHS=True, isAmount=True):
    args = [obj, delta, deltaRHS, isAmount]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='StrikeImpliedFromForwardDelta')
    except Exception as e:
        # 捕获异常类型和描述
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
    # 检查参数是否为空
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
    # 检查参数是否为空
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
    # 检查参数是否为空
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
    # 检查参数是否为空
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
@xl_func(macro=False, recalc_on_open=True)
def VOGetSpot(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetSpot')
    except Exception as e:
        s = f"VOGetSpot except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetForward(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetForward')
    except Exception as e:
        s = f"VOGetForward except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetVol(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetVol')
    except Exception as e:
        s = f"VOGetVol except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetStrike(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetStrike')
    except Exception as e:
        s = f"VOGetStrike except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s

@xl_func(macro=False, recalc_on_open=True)
def VOGetAccRate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetAccRate')
    except Exception as e:
        s = f"VOGetAccRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VOGetUndRate(obj):
    args = [obj]
    try:
        return tool_def.xls_call(*args, key='McpVanillaOption', method='GetUndRate')
    except Exception as e:
        s = f"VOGetUndRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)


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