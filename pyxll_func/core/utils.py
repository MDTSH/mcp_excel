# -*- coding: utf-8 -*-
"""
工具函数核心模块

提供通用的Excel函数，包括：
- 字符串处理函数
- 数组操作函数
- 数学计算函数
- 日期处理函数
- 数据转换函数
"""

import json
import logging
from math import log, sqrt, exp
from typing import Any, Dict, List, Optional, Union

import numpy as np
from pyxll import xl_func, xl_arg, xl_return

from mcp.utils.excel_utils import mcp_kv_wrapper, mcp_method_args_cache
from mcp.tool.args_def import tool_def
from mcp.wrapper import *
from mcp.utils.mcp_utils import mcp_dt, as_2d_array, as_array, debug_args_info, trans_2d_array
from mcp.utils.enums import enum_wrapper, Frequency, DayCounter
from mcp_calendar import plain_date, date_to_string


@xl_func("str: str")
def py_uppercase(x):
    """
    将字符串转换为大写
    
    参数:
        x: 输入字符串
        
    返回:
        str: 转换为大写的字符串
    """
    return x.upper()


@xl_func("var[][] values, function func: var[][]", auto_resize=True)
def py_apply_to_range(values, func):
    """
    对数组中的每个值应用指定函数
    
    参数:
        values: 输入数组
        func: 要应用的函数
        
    返回:
        var[][]: 应用函数后的新数组
    """
    # 遍历输入数组并创建新的转换数组
    new_array = []
    for row in values:
        new_row = []
        for value in row:
            # 对输入数组中的每个项目调用传入的函数
            new_value = func(value)
            new_row.append(new_value)

        # 将新值行添加到新数组
        new_array.append(new_row)

    # 返回的数组是对原始输入数组中的每个项目调用'func'的结果
    return new_array


@xl_func(macro=False, transpose=True, auto_resize=True)
def py_tran(x):
    """
    转置数组
    
    参数:
        x: 输入数组
        
    返回:
        var: 转置后的数组
    """
    return x


from math import log, sqrt, exp
from scipy.stats import norm
import math

"""
Black 76 模型（期货欧式期权定价与隐含波动率计算）脚本

示例：
    # 期权定价
    F, K, T, r, sigma = 100, 95, 0.5, 0.03, 0.2
    # 隐含波动率
    F2, K2, T2, r2, price2, option2 = 100, 95, 0.5, 0.03, 6.5, 'call'
"""

import math

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def future_black76_price(F: float, K: float, T: float, r: float, sigma: float, option: str = "call") -> float:
    if T <= 0 or sigma <= 0:
        raise ValueError("T 和 sigma 必须为正数")
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
        raise ValueError(f"未知的option类型: {option}")

def future_implied_volatility(market_price: float, F: float, K: float, T: float, r: float, option: str = "call", tol: float = 1e-6, max_iter: int = 100) -> float:
    low, high = 1e-6, 5.0
    price_low = future_black76_price(F, K, T, r, low, option)
    price_high = future_black76_price(F, K, T, r, high, option)
    if market_price < price_low or market_price > price_high:
        raise ValueError(f"市场价格 {market_price} 超出隐含波动率搜索范围对应的价格区间 "
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
        option_price = S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
        option_price = K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)
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
@xl_arg('precision', 'float')
@xl_arg('max_iterations', 'int')
# pyxll.ret('float')
def implied_volatility(S, K, r, T, option_price, option_type, precision=0.0001, max_iterations=100):
    """
    Calculates the implied volatility using the Black-Scholes formula.

    Args:
    S: float, underlying asset price
    K: float, strike price
    r: float, risk-free interest rate
    T: float, time to expiration (in years)
    option_price: float, option price
    option_type: str, option type: "call" or "put"
    precision: float, iteration precision, default is 0.0001
    max_iterations: int, maximum number of iterations, default is 100

    Returns:
    float, implied volatility
    """

    lower_volatility = 0.001  # Lower bound of volatility
    upper_volatility = 1.0  # Upper bound of volatility

    for _ in range(max_iterations):
        current_volatility = (lower_volatility + upper_volatility) / 2
        option_price_calculated = black_scholes(S, K, r, T, current_volatility, option_type)

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
    计算均方根误差 (RMSE)。
    
    :param actual: 实际值列表
    :param predicted: 预测值列表
    :return: RMSE 值
    """
    # 转换为 NumPy 数组以处理
    actual = np.array(actual)
    predicted = np.array(predicted)

    # 计算 RMSE
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    return rmse


@xl_func
def RRMSE(actual: list, predicted: list) -> float:
    """
    计算相对均方根误差 (RRMSE)。
    
    :param actual: 实际值列表
    :param predicted: 预测值列表
    :return: RRMSE 值（百分比）
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # 计算 RMSE
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    # 计算均值
    mean_value = np.mean(np.abs(actual))

    # 计算 RRMSE
    rrmse = (rmse / mean_value) * 100 if mean_value != 0 else np.nan

    return rrmse


@xl_func
def mape(actual: list, predicted: list) -> float:
    """
    计算平均绝对百分比误差（MAPE）。
    
    :param actual: 实际值列表
    :param predicted: 预测值列表
    :return: MAPE 值（百分比）
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # 计算相对偏差
    relative_deviation = np.abs(actual - predicted) / np.maximum(np.abs(actual), np.abs(predicted))

    # 计算 MAPE
    mape_value = np.mean(relative_deviation) * 100 if np.any(actual != 0) else np.nan

    return mape_value


@xl_func
def average_absolute_difference(actual: list, predicted: list) -> float:
    """
    计算两组数据差值的绝对值的平均值。
    
    :param actual: 实际值列表
    :param predicted: 预测值列表
    :return: 差值绝对值的平均值
    """
    actual = np.array(actual)
    predicted = np.array(predicted)

    # 计算差值的绝对值
    absolute_differences = np.abs(actual - predicted)

    # 计算平均值
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