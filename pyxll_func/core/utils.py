# -*- coding: utf-8 -*-
"""
Utility Functions Core Module

Provides common Excel functions, including:
- String processing functions
- Array operation functions
- Mathematical calculation functions
- Date processing functions
- Data conversion functions
"""

import json
import logging
from math import log, sqrt, exp
from typing import Any, Dict, List, Optional, Union

from mcp.optional_deps import numpy as np
from pyxll import xl_func, xl_arg, xl_return

from mcp.utils.excel_utils import mcp_kv_wrapper, mcp_method_args_cache
from mcp.tool.args_def import tool_def
from mcp.wrapper import *
from mcp.utils.mcp_utils import mcp_dt, as_2d_array, as_array, debug_args_info, trans_2d_array
from mcp.utils.enums import enum_wrapper, Frequency, DayCounter
from mcp_calendar import plain_date, date_to_string


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpHistoricalRates(args1, args2=None, args3=None, args4=None, args5=None, fmt="HD"):
    """
    创建历史利率对象 MHistoricalRates。
    输入格式（竖向排列，args1 区域）:
        date       rate
        2023/4/5   2.3
        2023/4/24  2.6
    用法: =McpHistoricalRates(G6:H8) 或 =McpHistoricalRates(G6:H8,,,,,"HD")
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpHistoricalRates")
    except Exception as e:
        s = f"McpHistoricalRates except: {e}"
        logging.warning(s, exc_info=True)
        return s


@xl_func("str: str")
def py_uppercase(x):
    """
    Convert string to uppercase
    
    Parameters:
        x: Input string
        
    Returns:
        str: String converted to uppercase
    """
    return x.upper()


@xl_func("var[][] values, function func: var[][]", auto_resize=True)
def py_apply_to_range(values, func):
    """
    Apply specified function to each value in array
    
    Parameters:
        values: Input array
        func: Function to apply
        
    Returns:
        var[][]: New array after applying function
    """
    # Iterate through input array and create new converted array
    new_array = []
    for row in values:
        new_row = []
        for value in row:
            # Call the passed function on each item in the input array
            new_value = func(value)
            new_row.append(new_value)

        # Add new value row to new array
        new_array.append(new_row)

    # Returned array is the result of calling 'func' on each item in the original input array
    return new_array


@xl_func(macro=False, transpose=True, auto_resize=True)
def py_tran(x):
    """
    Transpose array
    
    Parameters:
        x: Input array
        
    Returns:
        var: Transposed array
    """
    return x


from math import log, sqrt, exp
import math

"""
Black 76 Model Script (Futures European Option Pricing and Implied Volatility Calculation)

Example:
    # Option pricing
    F, K, T, r, sigma = 100, 95, 0.5, 0.03, 0.2
    # Implied volatility
    F2, K2, T2, r2, price2, option2 = 100, 95, 0.5, 0.03, 6.5, 'call'
"""

import math

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def future_black76_price(F: float, K: float, T: float, r: float, sigma: float, option: str = "call") -> float:
    if T <= 0 or sigma <= 0:
        raise ValueError("T and sigma must be positive numbers")
    sqrtT = math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    N_d1 = norm_cdf(d1)
    N_d2 = norm_cdf(d2)
    N_m_d1 = norm_cdf(-d1)
    N_m_d2 = norm_cdf(-d2)
    df = math.exp(-r * T)
    opt = option.strip().lower()
    if opt in ["call", "c"]:
        return df * (F * N_d1 - K * N_d2)
    elif opt in ["put", "p"]:
        return df * (K * N_m_d2 - F * N_m_d1)
    else:
        raise ValueError(f"Unknown option type: {option}")

def future_implied_volatility(market_price: float, F: float, K: float, T: float, r: float, option: str = "call", tol: float = 1e-6, max_iter: int = 100) -> float:
    low, high = 1e-6, 5.0
    price_low = future_black76_price(F, K, T, r, low, option)
    price_high = future_black76_price(F, K, T, r, high, option)
    if market_price < price_low or market_price > price_high:
        raise ValueError(f"Market price {market_price} is outside the price range corresponding to implied volatility search range "
                         f"[{price_low:.4f}, {price_high:.4f}]")
    for i in range(max_iter):
        mid = 0.5 * (low + high)
        price_mid = future_black76_price(F, K, T, r, mid, option)
        if abs(price_mid - market_price) < tol:
            return mid
        if price_mid > market_price:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg('market_price', 'float')
@xl_arg('F', 'float')
@xl_arg('K', 'float')
@xl_arg('r', 'float')
@xl_arg('T', 'float')
@xl_arg('option_type', 'str')
# @xl_return('float')
def future_implied_vol(market_price,F, K, r, T, option_type):
    tol: float = 1e-6
    max_iter: int = 100
    return future_implied_volatility(market_price,F,K,T,r,option_type,tol,max_iter)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg('F', 'float')
@xl_arg('K', 'float')
@xl_arg('r', 'float')
@xl_arg('T', 'float')
@xl_arg('sigma', 'float')
@xl_arg('option_type', 'str')
# @xl_return('float')
def future_black_scholes(F, K, r, q, T, sigma, option_type):
    return future_black76_price(F,K,T,r,sigma,option_type)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg('S', 'float')
@xl_arg('K', 'float')
@xl_arg('r', 'float')
@xl_arg('q', 'float')
@xl_arg('T', 'float')
@xl_arg('sigma', 'float')
@xl_arg('option_type', 'str')
# @xl_return('float')
def black_scholes(S, K, r, q, T, sigma, option_type):
    """
    Calculates the option price using the Black-Scholes formula with dividend yield.

    Args:
        S (float): underlying asset price
        K (float): strike price
        r (float): risk-free interest rate (continuous compounding)
        q (float): dividend yield (continuous compounding)
        T (float): time to expiration (in years)
        sigma (float): volatility of the underlying asset
        option_type (str): option type - "call" or "put" (case-insensitive)

    Returns:
        float: option price

    Raises:
        ValueError: if option_type is neither 'call' nor 'put'
    """
    # Input validation
    if sigma <= 0:
        sigma = 1e-10  # Avoid division by zero
    if T <= 0:
        T = 1e-10  # Avoid division by zero

    # Calculate d1 and d2 with dividend yield adjustment
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    # Calculate option price based on type
    option_type = option_type.lower()
    if option_type == 'call':
        option_price = S * exp(-q * T) * norm_cdf(d1) - K * exp(-r * T) * norm_cdf(d2)
    elif option_type == 'put':
        option_price = K * exp(-r * T) * norm_cdf(-d2) - S * exp(-q * T) * norm_cdf(-d1)
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")

    return option_price


@xl_func
@xl_arg('S', 'float')
@xl_arg('K', 'float')
@xl_arg('r', 'float')
@xl_arg('T', 'float')
@xl_arg('option_price', 'float')
@xl_arg('option_type', 'str')
@xl_arg('q', 'float')
@xl_arg('precision', 'float')
@xl_arg('max_iterations', 'int')
# pyxll.ret('float')
def implied_volatility(S, K, r, T, option_price, option_type, q=0.0, precision=0.0001, max_iterations=100):
    """
    Calculates the implied volatility using the Black-Scholes formula.

    Args:
    S: float, underlying asset price
    K: float, strike price
    r: float, risk-free interest rate
    T: float, time to expiration (in years)
    option_price: float, option price
    option_type: str, option type: "call" or "put"
    q: float, dividend yield (continuous compounding), default 0
    precision: float, iteration precision, default is 0.0001
    max_iterations: int, maximum number of iterations, default is 100

    Returns:
    float, implied volatility
    """

    lower_volatility = 0.001  # Lower bound of volatility
    upper_volatility = 1.0  # Upper bound of volatility

    for _ in range(max_iterations):
        current_volatility = (lower_volatility + upper_volatility) / 2
        option_price_calculated = black_scholes(S, K, r, q, T, current_volatility, option_type)

        if abs(option_price_calculated - option_price) < precision:
            return current_volatility
        elif option_price_calculated < option_price:
            lower_volatility = current_volatility
        else:
            upper_volatility = current_volatility

    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('S', 'float')
@xl_arg('r', 'float')
@xl_arg('q', 'float')
@xl_arg('T', 'float')
# @xl_return('float')
def impliedF(S, r, q, T):
    return S * exp((r - q) * T)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('S', 'float')
@xl_arg('F', 'float')
@xl_arg('q', 'float')
@xl_arg('T', 'float')
def impliedR(S, F, q, T):
    return (math.log(F / S) + q * T) / T


@xl_func(macro=False, recalc_on_open=True)
@xl_arg('S', 'float')
@xl_arg('F', 'float')
@xl_arg('r', 'float')
@xl_arg('T', 'float')
def impliedQ(S, F, r, T):
    return - (math.log(F / S) - r * T) / T


@xl_func
def abc():
    return "xuy"


@xl_func
def RMSE(actual: list, predicted: list) -> float:
    """
    Calculate Root Mean Square Error (RMSE).
    
    :param actual: List of actual values
    :param predicted: List of predicted values
    :return: RMSE value
    """
    # Convert to NumPy arrays for processing
    actual = np.array(actual)
    predicted = np.array(predicted)

    # Calculate RMSE
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    return rmse


@xl_func
def RRMSE(actual: list, predicted: list) -> float:
    """
    Calculate Relative Root Mean Square Error (RRMSE).
    
    :param actual: List of actual values
    :param predicted: List of predicted values
    :return: RRMSE value (percentage)
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # Calculate RMSE
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    # Calculate mean
    mean_value = np.mean(np.abs(actual))

    # Calculate RRMSE
    rrmse = (rmse / mean_value) * 100 if mean_value != 0 else np.nan

    return rrmse


@xl_func
def mape(actual: list, predicted: list) -> float:
    """
    Calculate Mean Absolute Percentage Error (MAPE).
    
    :param actual: List of actual values
    :param predicted: List of predicted values
    :return: MAPE value (percentage)
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # Calculate relative deviation
    relative_deviation = np.abs(actual - predicted) / np.maximum(np.abs(actual), np.abs(predicted))

    # Calculate MAPE
    mape_value = np.mean(relative_deviation) * 100 if np.any(actual != 0) else np.nan

    return mape_value


@xl_func
def average_absolute_difference(actual: list, predicted: list) -> float:
    """
    Calculate the average of absolute differences between two sets of data.
    
    :param actual: List of actual values
    :param predicted: List of predicted values
    :return: Average of absolute differences
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # Calculate absolute differences
    absolute_differences = np.abs(actual - predicted)

    # Calculate mean value
    average_abs_diff = np.mean(absolute_differences)

    return average_abs_diff


"""不确定"""


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("funcName", "str")
def McpFunctionFields(funcName):
    sub_dict = mcp_kv_wrapper.get_method_dict(funcName)
    if sub_dict is None:
        return "Unknown function name"
    else:
        result = []
        keys = sub_dict["keys"]
        lower_keys = sub_dict["lower_keys"]
        for i in range(len(keys)):
            result.append([lower_keys[keys[i]]])
        return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("typeDirect", "int")
@xl_arg("precision", "int")
def McpRounder(typeDirect, precision):
    rounder = mcp.mcp.MRounder(typeDirect, precision)
    return rounder


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("data", "var[]")
# @xl_return("object")
def McpList(data):
    # mcp_list = McpListObject()
    # mcp_list.data = data
    # return mcp_list
    return json.dumps(data)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("data", "var[][]")
def McpMatrix(data):
    return json.dumps(data)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("object", "var")
def McpFunctionArgs(object):
    key = str(object)
    cache = mcp_method_args_cache.get_cache(key)
    if cache is None:
        return "No args"
    else:
        result = []
        keys = cache["keys"]
        vals = cache["vals"]
        for i in range(len(keys)):
            result.append([keys[i], vals[i]])
        return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("inputString", "str")
def McpEncryptString(inputString):
    return mcp.mcp.MMCP().encryptString(inputString)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("inputString", "str")
@xl_arg("encryptedStr", "str")
def McpVerifyEncryptedString(inputString,encryptedStr):
    return mcp.mcp.MMCP().verifyEncryptedString(inputString,encryptedStr)


# ---------------------------------------------------------------------------
# LSEG FX RIC parsing & USD-triangle cross (XXX/CNY) helpers
# ---------------------------------------------------------------------------

import re

_FX_TENOR_RE = re.compile(
    r"^(ON|TN|SN|SW|OVERNIGHT|SPOTNEXT|SPOT|1W|2W|3W|4W|5W|6W|7W|8W|9W|10W|"
    r"\d+D|\d+W|\d+M|\d+Y)$"
)
_FX_SKIP_CCY = frozenset({"ARS", "PEN"})
_FX_TENOR_SORT = {
    "ON": 0, "TN": 1, "SN": 2, "SW": 3, "1W": 4, "2W": 5, "3W": 6, "4W": 7,
    "5W": 8, "6W": 9, "7W": 10, "8W": 11, "9W": 12, "10W": 13,
}

# USD/XXX 掉期点 ScaleFactor（LSEG 原始报价单位 → 全价增量）
_FX_USD_LEG_SCALE = {
    "CNY": 10000.0,
    "CZK": 10000.0,
    "PHP": 1.0,
    "NGN": 1.0,
    "BDT": 10000.0,
    "KZT": 10000.0,
    "UGX": 1.0,
    "TZS": 1.0,
    "VND": 10000.0,
    "AOA": 10000.0,
    "CLP": 1.0,
}

# XXX/CNY 交叉盘掉期点 ScaleFactor（Pair 如 CZKCNY）
_FX_CROSS_SCALE = {
    "CZKCNY": 10000.0,
    "PHPCNY": 1000000.0,
    "NGNCNY": 1000000.0,
    "AOACNY": 1000000.0,
    "BDTCNY": 1000000.0,
    "KZTCNY": 1000000.0,
    "UGXCNY": 1000000.0,
    "TZSCNY": 1000000.0,
    "CLPCNY": 1000000.0,
    "VNDCNY": 1000000.0,
}

_FX_CROSS_CCYS = ["CZK", "PHP", "NGN", "AOA", "BDT", "KZT", "UGX", "TZS", "CLP", "VND"]
_FX_STD_TENORS = ["ON", "1W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y"]


def _fx_flat_rows(data):
    if data is None:
        return []
    if isinstance(data, (list, tuple)) and data and isinstance(data[0], (list, tuple)):
        return list(data)
    return [[data]]


def _fx_to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fx_normalize_tenor(tenor):
    t = str(tenor).strip().upper()
    if t in ("OVERNIGHT",):
        return "ON"
    if t in ("SPOTNEXT",):
        return "TN"
    if t in ("SPOT",):
        return "SN"
    return t


def _fx_tenor_sort_key(tenor):
    t = _fx_normalize_tenor(tenor)
    if t in _FX_TENOR_SORT:
        return (_FX_TENOR_SORT[t], 0)
    m = re.match(r"^(\d+)([DWMY])$", t)
    if not m:
        return (9999, 0)
    n, u = int(m.group(1)), m.group(2)
    unit_days = {"D": 1, "W": 7, "M": 30, "Y": 365}
    return (100 + n * unit_days.get(u, 0), n)


def _fx_cell_empty(v):
    if v is None:
        return True
    if isinstance(v, str) and str(v).strip() == "":
        return True
    return False


def _fx_parse_spot_ccy(ric):
    """即期 RIC：CNY= / CZK= / CNY"""
    s = str(ric).strip().upper()
    if re.match(r"^[A-Z]{3}=$", s):
        return s[:3]
    if re.match(r"^[A-Z]{3}$", s):
        return s
    if "=" in s:
        left, right = s.split("=", 1)
        if re.match(r"^[A-Z]{3}$", left) and right == "":
            return left
    return ""


def _fx_mid_from_cells(bid, ask, value):
    """bid/ask 中价；仅有 Value 时用 Value。兼容 Excel 空单元格传入 0。"""
    v = _fx_to_float(value) if not _fx_cell_empty(value) else None
    b = _fx_to_float(bid) if not _fx_cell_empty(bid) else None
    a = _fx_to_float(ask) if not _fx_cell_empty(ask) else None
    if v is not None and v != 0:
        if (b is None or b == 0) and (a is None or a == 0):
            return v
    if b is not None and a is not None and not (b == 0 and a == 0):
        return (b + a) / 2.0
    if b is not None and b != 0:
        return b
    if a is not None and a != 0:
        return a
    if v is not None:
        return v
    return 0.0


def _fx_parse_ric_core(ric):
    s = str(ric).strip().upper()
    if not s:
        return "", "", False, ""
    spot_ccy = _fx_parse_spot_ccy(ric)
    if spot_ccy:
        return spot_ccy, "SPOT", False, ""
    source = ""
    if "=" in s:
        left, right = s.split("=", 1)
        if right and re.match(r"^[A-Z]+$", right):
            source = right
        base = left
    else:
        base = s
    is_ndf = "NDF" in base
    base = base.replace("NDF", "")
    m = re.match(r"^([A-Z]{3})(.+)$", base)
    if not m:
        return "", "", is_ndf, source
    ccy, rest = m.group(1), m.group(2)
    if not _FX_TENOR_RE.match(rest):
        return "", "", is_ndf, source
    return ccy, _fx_normalize_tenor(rest), is_ndf, source


def _fx_cross_scale_for_spot(spot):
    if spot is None or spot <= 0:
        return 10000.0
    return 1000000.0 if spot < 1.0 else 10000.0


@xl_func("str ric: str[]", macro=False, recalc_on_open=True, auto_resize=True)
def py_parse_lseg_fx_ric(ric):
    """解析 LSEG FX RIC，返回 [ccy, tenor, is_ndf, source]（纵向溢出）。"""
    ccy, tenor, is_ndf, source = _fx_parse_ric_core(ric)
    return [ccy, tenor, "Y" if is_ndf else "N", source]


@xl_func("str ric: str", macro=False, recalc_on_open=True)
def py_parse_lseg_fx_ccy(ric):
    """解析 LSEG FX RIC 的币种（即期行 CNY= 返回 CNY）。"""
    ccy, _, _, _ = _fx_parse_ric_core(ric)
    return ccy


@xl_func("str ric: str", macro=False, recalc_on_open=True)
def py_parse_lseg_fx_tenor(ric):
    """解析 LSEG FX RIC 的期限（即期行返回 SPOT）。"""
    _, tenor, _, _ = _fx_parse_ric_core(ric)
    return tenor


@xl_func("str ric: str", macro=False, recalc_on_open=True)
def py_parse_lseg_fx_ndf(ric):
    """解析 LSEG FX RIC 是否 NDF（Y/N）。"""
    _, _, is_ndf, _ = _fx_parse_ric_core(ric)
    return "Y" if is_ndf else "N"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bid", "var")
@xl_arg("ask", "var")
@xl_arg("value", "var")
def py_fx_mid(bid, ask, value):
    """bid/ask 中价；若仅有 Value 则直接返回 Value。"""
    return _fx_mid_from_cells(bid, ask, value)


@xl_func("str ccy: float", macro=False, recalc_on_open=True)
def py_fx_usd_leg_scale(ccy):
    """USD/XXX 腿的 ScaleFactor。"""
    return _FX_USD_LEG_SCALE.get(str(ccy).strip().upper(), 10000.0)


@xl_func("str cross_pair: float", macro=False, recalc_on_open=True)
def py_fx_cross_scale(cross_pair):
    """XXX/CNY 交叉盘 ScaleFactor；cross_pair 如 CZKCNY。"""
    key = str(cross_pair).strip().upper().replace("/", "")
    if key in _FX_CROSS_SCALE:
        return _FX_CROSS_SCALE[key]
    if key.endswith("CNY") and len(key) == 6:
        return _fx_cross_scale_for_spot(None)
    return 10000.0


@xl_func("float cross_spot: float", macro=False, recalc_on_open=True)
def py_fx_cross_scale_from_spot(cross_spot):
    """按交叉即期大小建议 ScaleFactor（<1 用 1e6，否则 1e4）。"""
    return _fx_cross_scale_for_spot(_fx_to_float(cross_spot))


def _fx_valid_rate(v):
    x = _fx_to_float(v)
    if x is None or x == 0:
        return None
    return x


@xl_func("float usd_cny, float usd_xxx: float", macro=False, recalc_on_open=True)
def py_fx_xxx_cny_spot(usd_cny, usd_xxx):
    """XXX/CNY 即期（CNY per 1 XXX）= USD/CNY ÷ USD/XXX。"""
    num, den = _fx_valid_rate(usd_cny), _fx_valid_rate(usd_xxx)
    if num is None or den is None:
        return 0.0
    return num / den


@xl_func("float fwd_usd_cny, float fwd_usd_xxx: float", macro=False, recalc_on_open=True)
def py_fx_xxx_cny_forward_outright(fwd_usd_cny, fwd_usd_xxx):
    """XXX/CNY 远期全价 = F(USD/CNY) ÷ F(USD/XXX)。"""
    num, den = _fx_valid_rate(fwd_usd_cny), _fx_valid_rate(fwd_usd_xxx)
    if num is None or den is None:
        return 0.0
    return num / den


@xl_func("float usd_xxx, float usd_cny: float", macro=False, recalc_on_open=True)
def py_fx_cny_xxx_spot(usd_xxx, usd_cny):
    """CNY/XXX 即期（XXX per 1 CNY）= USD/XXX ÷ USD/CNY。"""
    num, den = _fx_valid_rate(usd_xxx), _fx_valid_rate(usd_cny)
    if num is None or den is None:
        return 0.0
    return num / den


@xl_func("float fwd_usd_xxx, float fwd_usd_cny: float", macro=False, recalc_on_open=True)
def py_fx_cny_xxx_forward_outright(fwd_usd_xxx, fwd_usd_cny):
    """CNY/XXX 远期全价 = F(USD/XXX) ÷ F(USD/CNY)。"""
    num, den = _fx_valid_rate(fwd_usd_xxx), _fx_valid_rate(fwd_usd_cny)
    if num is None or den is None:
        return 0.0
    return num / den


@xl_func("float usd_cny, float usd_xxx: float", macro=False, recalc_on_open=True)
def py_fx_cross_spot(usd_cny, usd_xxx):
    """XXX/CNY 即期（默认套算方向）。"""
    return py_fx_xxx_cny_spot(usd_cny, usd_xxx)


@xl_func("float fwd_usd_cny, float fwd_usd_xxx: float", macro=False, recalc_on_open=True)
def py_fx_cross_forward_outright(fwd_usd_cny, fwd_usd_xxx):
    """XXX/CNY 远期全价（默认套算方向）。"""
    return py_fx_xxx_cny_forward_outright(fwd_usd_cny, fwd_usd_xxx)


@xl_func("float cross_spot, float cross_fwd, float scale_factor: float", macro=False, recalc_on_open=True)
def py_fx_cross_forward_points(cross_spot, cross_fwd, scale_factor):
    """XXX/CNY 掉期点 = (远期全价 - 即期) × ScaleFactor。"""
    s, f = _fx_to_float(cross_spot), _fx_to_float(cross_fwd)
    sf = _fx_to_float(scale_factor) or 10000.0
    if s is None or f is None:
        return 0.0
    return (f - s) * sf


@xl_func("var[][] raw_data, str ccy: var[][]", macro=False, recalc_on_open=True, auto_resize=True)
def py_fx_leg_curve_table(raw_data, ccy):
    """
    从 Raw_LSEG 表提取单条 USD/XXX 腿的 [tenor, swap_point]（已按期限排序）。
    raw_data 列: RIC | Bid | Ask | Value
    """
    return _fx_build_leg_curve_rows(raw_data, ccy)


def _fx_build_leg_curve_rows(raw_data, ccy):
    target = str(ccy).strip().upper()
    if target in _FX_SKIP_CCY:
        return []
    rows = _fx_flat_rows(raw_data)
    points = {}
    for row in rows:
        if not row:
            continue
        ric = row[0] if len(row) > 0 else None
        if ric is None or str(ric).strip() == "":
            continue
        ric_s = str(ric).strip().upper()
        if re.match(r"^[A-Z]{3}=$", ric_s) or re.match(r"^[A-Z]{3}$", ric_s):
            continue
        parsed_ccy, tenor, is_ndf, _ = _fx_parse_ric_core(ric)
        if not parsed_ccy or parsed_ccy != target or is_ndf or tenor == "SPOT":
            continue
        bid = row[1] if len(row) > 1 else None
        ask = row[2] if len(row) > 2 else None
        val = row[3] if len(row) > 3 else None
        if _fx_cell_empty(bid) and _fx_cell_empty(ask) and _fx_cell_empty(val):
            continue
        mid = _fx_mid_from_cells(bid, ask, val)
        points[tenor] = mid
    ordered = sorted(points.items(), key=lambda x: _fx_tenor_sort_key(x[0]))
    return [[t, p] for t, p in ordered]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("raw_data", "var[][]")
@xl_arg("ccy", "str")
def py_fx_leg_tenors_json(raw_data, ccy):
    """供 McpFXForwardPointsCurve 使用的 Tenors JSON（已过滤空期限）。"""
    rows = _fx_build_leg_curve_rows(raw_data, ccy)
    return json.dumps([t for t, _ in rows if t])


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("raw_data", "var[][]")
@xl_arg("ccy", "str")
def py_fx_leg_points_json(raw_data, ccy):
    """供 McpFXForwardPointsCurve 使用的 FXForwardPoints JSON（已过滤空项）。"""
    rows = _fx_build_leg_curve_rows(raw_data, ccy)
    return json.dumps([p for t, p in rows if t])


@xl_func("var[][] raw_data, str ccy: float", macro=False, recalc_on_open=True)
def py_fx_leg_spot(raw_data, ccy):
    """从 Raw 表读取 {CCY}= 即期（如 CNY= / CZK=）。"""
    target = str(ccy).strip().upper()
    rows = _fx_flat_rows(raw_data)
    for row in rows:
        if not row:
            continue
        ric = str(row[0]).strip().upper() if row[0] is not None else ""
        if ric not in (f"{target}=", target):
            continue
        bid = row[1] if len(row) > 1 else None
        ask = row[2] if len(row) > 2 else None
        val = row[3] if len(row) > 3 else None
        if len(row) == 2 and _fx_to_float(row[1]) is not None and _fx_to_float(row[2]) is None:
            val = row[1]
        spot = _fx_mid_from_cells(bid, ask, val)
        if spot:
            return spot
    return 0.0


@xl_func(": str[]", macro=False, recalc_on_open=True, auto_resize=True)
def py_fx_std_tenors():
    """标准输出期限列表。"""
    return [[t] for t in _FX_STD_TENORS]


@xl_func(": str[]", macro=False, recalc_on_open=True, auto_resize=True)
def py_fx_cross_ccy_list():
    """待套算的外币列表（不含 ARS/PEN）。"""
    return [[c] for c in _FX_CROSS_CCYS]


import tkinter as tk
from tkinter import simpledialog, messagebox
from pyxll import xl_func

# 假设的用户名和密码
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"


def show_login_dialog():
    """弹出登录对话框，获取用户名和密码"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 弹出对话框获取用户名
    username = simpledialog.askstring("用户名", "请输入用户名:")
    if username is None:  # 用户点击取消
        return False

    # 弹出对话框获取密码
    password = simpledialog.askstring("密码", "请输入密码:", show='*')
    if password is None:  # 用户点击取消
        return False

    return check_credentials(username, password)


@xl_func
def check_credentials(username: str, password: str) -> bool:
    """
    检查用户名和密码是否正确。
    
    Args:
        username: 用户名
        password: 密码
    
    Returns:
        bool: 如果用户名和密码匹配返回 True，否则返回 False
    """
    return username == VALID_USERNAME and password == VALID_PASSWORD


@xl_func
def login() -> bool:
    """
    显示登录对话框并验证用户凭据。
    
    Returns:
        bool: 如果用户名和密码匹配返回 True，否则返回 False
    """
    return show_login_dialog()



import ast
from datetime import datetime, date

@xl_func("var list_in, bool parse_dates: var[][]", auto_resize=True)
def McpParseList(list_in, parse_dates=True):
    """
    将输入转成 Python list 并返回给 Excel（作为数组）。
    
    参数：
      list_in     : 可以是字符串形式的列表，也可以是 Excel 传过来的列表/二维数组
      parse_dates : True 时尝试把符合 'YYYY-MM-DD' 的字符串转成日期，否则保留字符串
    
    返回：
      一个二维列表 [[v1], [v2], …]，Excel 会自动把它展开成一列。
    """
    # 1. 如果是字符串，就用 ast.literal_eval 转成 list
    if isinstance(list_in, str):
        try:
            items = ast.literal_eval(list_in)
        except Exception as e:
            raise ValueError(f"不能解析的列表字符串: {e}")
    else:
        # 假如 Excel 传进来的是二维数组（list of list），则先拍平成一维
        if isinstance(list_in, (list, tuple)) and len(list_in) > 0 and isinstance(list_in[0], (list, tuple)):
            # 假设传进来是 [[a, b, c, ...]] 或 [[a],[b],[c],...]
            # 先拍平成一维
            flat = []
            for row in list_in:
                flat.extend(row)
            items = flat
        else:
            items = list(list_in)

    # 2. 对每个元素做类型转换
    result = []
    for item in items:
        # 数字 -> float
        if isinstance(item, (int, float)):
            result.append(float(item))
            continue

        # 字符串 -> 尝试日期
        if isinstance(item, str) and parse_dates:
            try:
                d = datetime.strptime(item, "%Y-%m-%d").date()
                result.append(d)
                continue
            except ValueError:
                # 不是标准日期格式就当普通字符串
                pass

        # 其他情况原样返回
        result.append(item)

    # 3. 返回二维列表，每个元素占一行一列
    #    Excel 会根据 auto_resize=True 自动展开
    return [[v] for v in result]


# utils 在 pyxll.cfg 中必加载；通过侧导入注册 Excel 关闭时的 MCP 资源清理
try:
    import mcp_lifecycle  # noqa: F401
except ImportError:
    pass