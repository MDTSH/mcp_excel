# -*- coding: utf-8 -*-
"""
本模块封装了与波动率相关的 Excel/PyXLL 接口函数：
- FXVolSurface：外汇波动率曲面（单边）
- FXVolSurface2 / VolSurface2：支持双边（bid/ask）报价的接口
- 通用股指/商品 VolSurface 接口
- 历史波动率、掉期期权（swaption）立方体、SVI/SABR 辅助计算等

约定：
- 大多数构造/查询函数通过 tool_def.xls_create 或 tool_def.xls_call 代理到底层实现。
- 日期转换统一使用 mcp.utils.excel_utils 中的 pf_date / pf_date_time 或 mcp_dt 工具。
- 解析矩阵类输入时，默认首行是列标签，首列是行标签。
"""

# =========================
# 标准库
# =========================
import json
import logging

# =========================
# 第三方库
# =========================
import numpy as np
import pandas as pd
from pyxll import xl_arg, xl_func, xl_return

# =========================
# 项目内
# =========================
import mcp.mcp
import mcp.wrapper
from mcp.forward.compound import MOptVolSurface, is_vol_surface
from mcp.tool.args_def import tool_def
from mcp.utils.mcp_utils import as_2d_array, is_float, as_array
from mcp.utils.svi import MSurfaceVol
from mcp.utils.excel_utils import *
from mcp_calendar import date_to_string

# =========================
# 工具函数
# =========================
def parse_matrix(data):
    """
    将二维区域解析为 (列标签, 行标签, 数据矩阵)
    假定 data 结构为：
        [ [None, c1, c2, ...],
          [r1,    d11, d12, ...],
          [r2,    d21, d22, ...],
          ...
        ]
    """
    arr = np.array(data)
    cols = arr[0, 1:]
    rows = arr[1:, 0]
    d = arr[1:, 1:]
    return cols, rows, d


# =========================
# Cap Vol Stripping
# =========================
@xl_func(macro=False, recalc_on_open=False)
@xl_arg("MarketQuotes", "var[][]")
@xl_arg("args", "var[][]")
def McpCapVolStripping(MarketQuotes, args):
    """
    构建 Cap Vol Stripping 对象。
    MarketQuotes：二维区域，首行列头为 tenor，首列行为 strike，主体为报价。
    args：额外参数区域。
    """
    MarketQuotes = [list(row) for row in zip(*MarketQuotes)]  # 转置为列优先
    cols, rows, d = parse_matrix(MarketQuotes)
    args1 = [
        ["Terms", cols.tolist()],
        ["Strikes", rows.astype(np.float64).tolist()],
        ["MarketQuotes", d.astype(np.float64).tolist()],
    ]
    args_list = [args1, args, None, None, None, "VP"]
    item = tool_def.xls_create(*args_list, key="McpCapVolStripping")
    return item


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("capletExpiry", "datetime")
@xl_arg("strike", "float")
def CvsSpreadAtTAndK(cvs, capletExpiry, strike):
    """
    返回给定到期与行权下的 Spread（价格维度）。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    capletExpiry = mcp_dt.to_date1(capletExpiry)
    return cvs.SpreadAtTAndK(capletExpiry, strike)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("capletExpiry", "datetime")
def CvsPriceATMVolAtT(cvs, capletExpiry):
    """
    返回价格维度的 ATM 波动率（按到期）。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    capletExpiry = mcp_dt.to_date1(capletExpiry)
    return cvs.PriceATMVolAtT(capletExpiry)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("capletExpiry", "datetime")
@xl_arg("strike", "float")
def CvsPriceVolAtTandK(cvs, capletExpiry, strike):
    """
    返回价格维度给定到期与行权下的波动率。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    capletExpiry = mcp_dt.to_date1(capletExpiry)
    return cvs.PriceVolAtTandK(capletExpiry, strike)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("capletExpiry", "datetime")
def CvsYieldATMVolAtT(cvs, capletExpiry):
    """
    返回收益率维度的 ATM 波动率（按到期）。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    capletExpiry = mcp_dt.to_date1(capletExpiry)
    return cvs.YieldATMVolAtT(capletExpiry)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("capletExpiry", "datetime")
@xl_arg("strike", "float")
def CvsYieldVolAtTandK(cvs, capletExpiry, strike):
    """
    返回收益率维度给定到期与行权下的波动率。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    capletExpiry = mcp_dt.to_date1(capletExpiry)
    return cvs.YieldVolAtTandK(capletExpiry, strike)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("settlementDate", "datetime")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
def CvsFairSwapRate(cvs, settlementDate, startDate, endDate):
    """
    由 Cap Vol Stripping 结果推导的公平互换利率。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    settlementDate = mcp_dt.to_date1(settlementDate)
    startDate = mcp_dt.to_date1(startDate)
    endDate = mcp_dt.to_date1(endDate)
    return cvs.FairSwapRate(settlementDate, startDate, endDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cvs", "var")
@xl_arg("expiryDate", "datetime")
def CvsATMRate(cvs, expiryDate):
    """
    返回到期时的 ATM 利率。
    """
    if not isinstance(cvs, mcp.mcp.MCapVolStripping):
        return cvs
    expiryDate = mcp_dt.to_date1(expiryDate)
    return cvs.ATMRate(expiryDate)


# =========================
# Swaption Cube
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("StrikeOrSpreads", "var[][]")
@xl_arg("AtmVols", "var[][]")
@xl_arg("args", "var[][]")
def McpSwaptionCube1(StrikeOrSpreads, AtmVols, args):
    """
    构建 Swaption Cube（版本1）。输入为矩阵式的行列标签和报价。
    StrikeOrSpreads：行=ExpiryTenor，列=StrikeOrSpread，值=VolSpreadOrVols（百分数形式，内部转为小数）
    AtmVols：行=AtmExpiryPillars，列=AtmMaturityPillars，值=AtmVols（百分数形式，内部转为小数）
    """
    cols, rows, d = parse_matrix(StrikeOrSpreads)
    args1 = [
        ["StrikeOrSpreads", cols.astype(np.float64).tolist()],
        ["ExpiryTenorPillars", rows.tolist()],
        ["VolSpreadOrVols", (d.astype(np.float64) / 100).tolist()],
    ]
    cols, rows, d = parse_matrix(AtmVols)
    args2 = [
        ["AtmMaturityPillars", cols.tolist()],
        ["AtmExpiryPillars", rows.tolist()],
        ["AtmVols", (d.astype(np.float64) / 100).tolist()],
    ]
    args_list = [args1, args2, args, None, None, "VP"]
    sc = tool_def.xls_create(*args_list, key="McpSwaptionCube")
    return sc


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("StrikeOrSpreads", "var[][]")
@xl_arg("AtmVols", "var[][]")
@xl_arg("args", "var[][]")
def McpSwaptionCube(StrikeOrSpreads, AtmVols, args):
    """
    构建 Swaption Cube（主版本）。同 McpSwaptionCube1。
    """
    cols, rows, d = parse_matrix(StrikeOrSpreads)
    args1 = [
        ["StrikeOrSpreads", cols.astype(np.float64).tolist()],
        ["ExpiryTenorPillars", rows.tolist()],
        ["VolSpreadOrVols", (d.astype(np.float64) / 100).tolist()],
    ]
    cols, rows, d = parse_matrix(AtmVols)
    args2 = [
        ["AtmMaturityPillars", cols.tolist()],
        ["AtmExpiryPillars", rows.tolist()],
        ["AtmVols", (d.astype(np.float64) / 100).tolist()],
    ]
    args_list = [args1, args2, args, None, None, "VP"]
    sc = tool_def.xls_create(*args_list, key="McpSwaptionCube")
    return sc


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("sc", "object")
@xl_arg("strike", "float")
@xl_arg("expiryDate", "datetime")
@xl_arg("maturityDate", "datetime")
def ScGetVol(sc, strike, expiryDate, maturityDate):
    """
    从 Swaption Cube 取波动率（给定行权、到期、到期后互换期限）。
    """
    expiryDate = mcp_dt.to_date1(expiryDate)
    maturityDate = mcp_dt.to_date1(maturityDate)
    is_period = False
    return sc.getVol(strike, expiryDate, maturityDate, is_period)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("sc", "object")
@xl_arg("strike", "float")
@xl_arg("expiryDate", "datetime")
@xl_arg("maturityTenor", "str")
def ScGetVolByPeriod(sc, strike, expiryDate, maturityTenor):
    """
    从 Swaption Cube 取波动率（给定行权、到期、互换期限 Tenor）。
    """
    expiryDate = mcp_dt.to_date1(expiryDate)
    is_period = True
    return sc.getVol(strike, expiryDate, maturityTenor, is_period)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("sc", "object")
@xl_arg("expiryDate", "datetime")
@xl_arg("maturity", "var")
def ScAtmStrike(sc, expiryDate, maturity):
    """
    返回 ATM 行权价（maturity 支持日期或 Tenor 字符串）。
    """
    expiryDate = mcp_dt.to_date1(expiryDate)
    if is_float(maturity):
        is_period = False
        maturity = pf_date(maturity)
    else:
        is_period = True
    return sc.atmStrike(expiryDate, maturity, is_period)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("sc", "object")
@xl_arg("expiryDate", "datetime")
@xl_arg("maturity", "var")
def ScAtmVol(sc, expiryDate, maturity):
    """
    返回 ATM 波动率（maturity 支持日期或 Tenor 字符串）。
    """
    expiryDate = mcp_dt.to_date1(expiryDate)
    if is_float(maturity):
        is_period = False
        maturity = pf_date(maturity)
    else:
        is_period = True
    return sc.atmVol(expiryDate, maturity, is_period)


# =========================
# 历史波动率
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("data", "float[][]")
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpIROHistVols2(data, args1, args2, args3, args4, args5, fmt="VP"):
    """
    基于零息曲线历史数据构建 IR 历史波动率对象（直接传曲线点）。
    data: CurveZeroRates 矩阵
    """
    data_fields = [
        ("CurveRefDates", "date"),
        ("CurveDates", "date"),
    ]
    args6 = [["CurveZeroRates", json.dumps(data)]]
    args = [args1, args2, args3, args4, args5, args6]
    fmt = str(fmt).upper()
    args = tool_def.mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
    result, lack_keys = tool_def.mcp_kv_wrapper.parse_and_validate2(
        tool_def.MethodName.McpIROHistVols,
        args,
        [
            ("Label", "str"),
            ("ReferenceDate", "date"),
            ("ExpiryTenor", "str"),
            ("MaturityTenor", "str"),
            ("UnderlyingFrequency", "const"),
            ("Periods", "int"),
            ("Model", "const"),
            ("ReturnMethod", "const"),
            ("AnnualFactor", "float"),
            ("Lamda", "float"),
            ("InterpolationMethod", "const"),
            ("DayCounter", "const"),
            ("Calendar", "mcphandler"),
            ("CurveRefDates", "plainlist"),
            ("CompoundingFrequency", "const"),
            ("Variable", "const"),
            ("Method", "const"),
            ("CurveDates", "plainlist"),
            ("CurveZeroRates", "plainlist"),
        ],
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    vs = mcp.mcp.MIROHistVols(*vals)
    tool_def.mcp_method_args_cache.cache(str(vs), result)
    return vs


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("curves", "object[]")
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpIROHistVols(curves, args1, args2, args3, args4, args5, fmt="VP"):
    """
    基于曲线对象列表构建 IR 历史波动率对象（VectorWrapper）。
    """
    data_fields = []
    vector = mcp.mcp.VectorWrapper()
    for item in curves:
        vector.add(item.getHandler())
    args6 = [["CurveWrapper", vector.getHandler()]]
    args = [args1, args2, args3, args4, args5, args6]
    fmt = str(fmt).upper()
    args = tool_def.mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
    result, lack_keys = tool_def.mcp_kv_wrapper.parse_and_validate2(
        tool_def.MethodName.McpIROHistVols2,
        args,
        [
            ("Label", "str"),
            ("ReferenceDate", "date"),
            ("ExpiryTenor", "str"),
            ("MaturityTenor", "str"),
            ("CurveWrapper", "object"),
            ("UnderlyingFrequency", "const"),
            ("Periods", "int"),
            ("Model", "const"),
            ("ReturnMethod", "const"),
            ("AnnualFactor", "float"),
            ("Lamda", "float"),
            ("InterpolationMethod", "const"),
            ("DayCounter", "const"),
            ("Calendar", "mcphandler"),
        ],
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    vs = mcp.mcp.MIROHistVols(*vals)
    tool_def.mcp_method_args_cache.cache(str(vs), result)
    return vs


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("hv", "var")
@xl_arg("referenceDate", "datetime")
@xl_arg("sampleNum", "int")
def HvsGetVol(hv, referenceDate, sampleNum=0):
    """
    从历史波动率对象获取某日波动率（可选样本数）。
    """
    s = hv.GetVol(mcp_dt.to_date1(referenceDate), sampleNum)
    return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("hv", "var")
@xl_arg("referenceDates", "datetime[]")
@xl_arg("format", "str")
def HvsGetVols(hv, referenceDates, format="V"):
    """
    批量获取历史波动率。
    format='V' 返回列向量；否则返回行向量。
    """
    dates = mcp_dt.to_date_list(referenceDates, mcp_dt.to_date1)
    s = hv.GetVols(json.dumps(dates))
    arr = json.loads(s)
    if format == "V":
        arr = [[item] for item in arr]
    else:
        arr = [arr]
    return arr


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("hv", "object")
def HvsGetVolMap(hv):
    """
    返回日期到波动率的映射表（二维数组）。
    """
    s = hv.GetVolMap()
    d = as_2d_array(s, "H")
    result = [[mcp_dt.parse_date2(key), value] for key, value in d.items()]
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpHistVols(args1, args2, args3, args4, args5, fmt="VP|HD"):
    data_fields = [
        ("Dates", "date"),
        ("Quotes", "float"),
    ]
    args = [args1, args2, args3, args4, args5]
    print("McpHistVols raw args:", fmt, args)
    fmt = str(fmt).upper()
    args = mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
    print("McpHistVols std args:", args)
    result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpHistVols, args, [
        ("Label", "str"),
        ("ReferenceDate", "date"),
        ("Dates", "plainlist"),
        ("Quotes", "plainlist"),
        ("Periods", "int"),
        ("Model", "const"),
        ("ReturnMethod", "const"),
        ("AnnualFactor", "float"),
        ("Lamda", "float"),
        ("InterpolationMethod", "const"),
        ("DayCounter", "const"),
    ])
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    print("McpHistVols final args:")
    print(vals)
    vs = mcp.mcp.MHistVols(*vals)
    mcp_method_args_cache.cache(str(vs), result)
    return vs


# =========================
# 标的/商品 波动率曲面（SVI）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("prices", "float[][]")
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpSurfaceVol(prices, args1, args2, args3, args4, args5, fmt="VP"):
    """
    基于期权价格点构建标的波动率曲面（SVI）。
    prices: 价格矩阵；其余参数通过 argsX 传入。
    """
    args6 = [["Prices", prices]]
    args = [args1, args2, args3, args4, args5, args6]
    data_fields = [
        ("MaturityDates", "date"),
        ("Strikes", "float"),
        ("DividendDates", "date"),
        ("Dividends", "float"),
    ]
    kv1 = [
        ("ReferenceDate", "date"),
        ("SpotPx", "float"),
        ("CallPut", "const"),
        ("BuildMethod", "str"),
        ("MaturityDates", "jsonlist"),
        ("Strikes", "jsonlist"),
        ("RiskFreeCurve", "none"),
        ("Prices", "none"),
        ("DividendDates", "jsonlist"),
        ("Dividends", "jsonlist"),
        ("TermInterpType", "str"),
        ("DayCounter", "const"),
    ]
    kv2 = None
    result, lack_keys = tool_def.mcp_kv_wrapper.valid_parse(
        "McpSurfaceVol", args, fmt, data_fields, kv1, kv2
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    sv = MSurfaceVol(*vals)
    tool_def.mcp_method_args_cache.cache(str(sv), result)
    return sv


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("sv", "object")
@xl_arg("date", "datetime")
def SviStrikeVols(sv, date):
    """
    提取给定到期的 (strike, vol) 点对。
    """
    result = []
    d = mcp_dt.to_date1(date)
    obj = sv.get_data(d)
    if obj is not None:
        col1 = obj["strikes"]
        col2 = obj["strike_vols"]
        for i in range(len(col1)):
            result.append([col1[i], col2[i]])
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("sv", "object")
@xl_arg("date", "datetime")
def SviModelLin(sv, date):
    """
    提取给定到期的线性化模型变量与拟合结果（用于诊断/作图）。
    """
    result = []
    d = mcp_dt.to_date1(date)
    obj = sv.get_data(d)
    if obj is not None:
        col1 = obj["lin"]
        col2 = obj["model_lin"]
        for i in range(len(col1)):
            result.append([col1[i], col2[i]])
    return result


# =========================
# 期权波动率曲面封装（单边/双边）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpOptVolSurface(args1, args2, args3, args4, args5, fmt="VP"):
    """
    构建期权波动率曲面封装（可与历史波、收益曲线联动）。
    """
    args = [args1, args2, args3, args4, args5]
    data_fields = []
    kv1 = [
        ("HistVols", "none"),
        ("YieldCurve", "none"),
        ("UndRate", "float"),
    ]
    kv2 = [
        ("SurfaceVol", "none"),
        ("YieldCurve", "none"),
        ("UndRate", "float"),
    ]
    result, lack_keys = tool_def.mcp_kv_wrapper.valid_parse(
        "McpOptVolSurface", args, fmt, data_fields, kv1, kv2
    )
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    sv = MOptVolSurface(*vals)
    tool_def.mcp_method_args_cache.cache(str(sv), result)
    return sv


# =========================
# FX Vol Surface（单边）
# =========================
@xl_func(macro=False, recalc_on_open=False)
def FXVolSurfaceGetStrike(obj, deltaString, expiryDateOrTenor, forward=float("nan")):
    """
    通过 delta 字符串与到期（日期或 tenor）反推行权价。
    forward 可选，若为 NaN 由底层使用自己的 forward。
    """
    if isinstance(expiryDateOrTenor, float):
        maturity = pf_date_time(expiryDateOrTenor)
        maturity = mcp_dt.to_date2(maturity)
    else:
        maturity = expiryDateOrTenor
    return obj.GetStrike(deltaString, maturity, forward)


@xl_func("var vs,datetime expiryDate: var", macro=False, recalc_on_open=True)
def VolSurfaceGetATMVol(vs, expiryDate):
    if not is_vol_surface(vs):
        return vs
    expiryDate = pf_date(expiryDate)
    return vs.GetATMVol(expiryDate)


@xl_func("var vs", macro=False, recalc_on_open=True)
def FXVolSurfaceGetReferenceDate(vs):
    if not is_vol_surface(vs):
        return vs
    return vs.GetReferenceDate()


@xl_func("var vs", macro=False, recalc_on_open=True)
def FXVolSurfaceGetSpotDate(vs):
    if not is_vol_surface(vs):
        return vs
    return vs.GetSpotDate()


@xl_func("var vs", macro=False, recalc_on_open=True)
def FXVolSurfaceGetSpot(vs):
    if not is_vol_surface(vs):
        return vs
    return vs.GetSpot()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vs", "var")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def VolSurfaceGetForeignRate(vs, expiryOrDeliveryDate, isDeliveryDate):
    if not is_vol_surface(vs):
        return vs
    expiryOrDeliveryDate = pf_date(expiryOrDeliveryDate)
    return vs.GetForeignRate(expiryOrDeliveryDate, isDeliveryDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vs", "var")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def VolSurfaceGetDomesticRate(vs, expiryOrDeliveryDate, isDeliveryDate):
    if not is_vol_surface(vs):
        return vs
    expiryOrDeliveryDate = pf_date(expiryOrDeliveryDate)
    return vs.GetDomesticRate(expiryOrDeliveryDate, isDeliveryDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vs", "var")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def VolSurfaceGetForward(vs, expiryOrDeliveryDate, isDeliveryDate):
    if not is_vol_surface(vs):
        return vs
    expiryOrDeliveryDate = pf_date(expiryOrDeliveryDate)
    return vs.GetForward(expiryOrDeliveryDate, isDeliveryDate)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("vs", "var")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def VolSurfaceGetForwardPoint(vs, expiryOrDeliveryDate, isDeliveryDate):
    if not is_vol_surface(vs):
        return vs
    expiryOrDeliveryDate = pf_date(expiryOrDeliveryDate)
    return vs.GetForwardPoint(expiryOrDeliveryDate, isDeliveryDate)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("vs", "var")
@xl_arg("expiryDate", "datetime")
def VolSurfaceGetParams(vs, expiryDate, format="V"):
    """
    返回指定到期的参数数组（SVI/SABR 等），format='V' 返回列向量。
    """
    if not is_vol_surface(vs):
        return vs
    expiryDate = pf_date(expiryDate)
    s = vs.GetParams(expiryDate)
    arr = json.loads(s)
    if format == "V":
        arr = [[item] for item in arr]
    else:
        arr = [arr]
    return arr


# 下列 VolSurfaceGetXXX 函数为统一代理版本（通过 tool_def），保留用以兼容
@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetForward(vs, expiryOrDeliveryDate, isDeliveryDate):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetForward")
    except Exception:
        s = f"VolSurfaceGetForward except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetRiskFreeRate(vs, expiryOrDeliveryDate, isDeliveryDate):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetRiskFreeRate")
    except Exception:
        s = f"VolSurfaceGetRiskFreeRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceStrikeFromString(vs, s, callPut, expiryDate, spotPx, forwardPx):
    args = [vs, s, callPut, expiryDate, spotPx, forwardPx]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="StrikeFromString")
    except Exception:
        s = f"VolSurfaceStrikeFromString except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetSpot(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetSpot")
    except Exception:
        s = f"VolSurfaceGetSpot except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetReferenceDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetReferenceDate")
    except Exception:
        s = f"VolSurfaceGetReferenceDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetSpotDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetSpotDate")
    except Exception:
        s = f"VolSurfaceGetSpotDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurfaceExpiryDates(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="ExpiryDates")
    except Exception:
        s = f"VolSurfaceExpiryDates except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurfaceExpiryTimes(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="ExpiryTimes")
    except Exception:
        s = f"VolSurfaceExpiryTimes except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, transpose=True, auto_resize=True)
def VolSurfaceStrikes(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="Strikes")
    except Exception:
        s = f"VolSurfaceStrikes except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurfaceVolatilities(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="Volatilities")
    except Exception:
        s = f"VolSurface2Volatilities except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurfaceGetForwards(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetForwards")
    except Exception:
        s = f"VolSurfaceGetForwards except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# SVI / SABR 公式
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("K", "float")
@xl_arg("f", "float")
@xl_arg("T", "float")
@xl_arg("alpha", "float")
@xl_arg("beta", "float")
@xl_arg("rho", "float")
@xl_arg("m", "float")
@xl_arg("sig", "float")
def SVIFormula(K, f, T, alpha, beta, rho, m, sig):
    vs = mcp.mcp.MMktVolSurface()
    return vs.SVIFormula(K, f, T, alpha, beta, rho, m, sig)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("K", "float")
@xl_arg("f", "float")
@xl_arg("T", "float")
@xl_arg("alpha", "float")
@xl_arg("rho", "float")
@xl_arg("nu", "float")
@xl_arg("beta", "float")
def SABRFormula(K, f, T, alpha, rho, nu, beta):
    vs = mcp.mcp.MMktVolSurface()
    return vs.SABRFormula(K, f, T, alpha, rho, nu, beta)


# =========================
# 包装器：曲线/点差曲线
# =========================
@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "var")
@xl_arg("bidMidAsk", "str")
def Fxfpc2GetCurve(obj, bidMidAsk="MID"):
    handler = obj.GetCurve(bidMidAsk)
    return mcp.wrapper.McpFXForwardPointsCurve(handler)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "var")
@xl_arg("bidMidAsk", "str")
def Yc2GetCurve(obj, bidMidAsk="MID"):
    handler = obj.GetCurve(bidMidAsk)
    return mcp.wrapper.McpYieldCurve(handler)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_return("var[][]")
def FXVolSurface2GetVolatilities(vs, bidMidAsk="MID", fmt="V"):
    """
    获取双边曲面的波动率矩阵，按 fmt（V/H）返回。
    """
    arr = vs.GetVolatilities(bidMidAsk)
    return as_2d_array(arr, fmt, False)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "var")
@xl_arg("bidMidAsk", "str")
def FXVolSurface2GetSurface(obj, bidMidAsk="MID"):
    handler = obj.GetFXVolSurface(bidMidAsk)
    return mcp.wrapper.McpFXVolSurface(handler)


# =========================
# VolSurface/FxVolSurface 构造与查询（单边）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVolSurface(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpVolSurface")
    except Exception as e:
        s = f"McpVolSurface except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceGetVolatility(vs, strike, expiryDate, forward):
    args = [vs, strike, expiryDate, forward]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="GetVolatility")
    except Exception:
        s = f"VolSurfaceGetVolatility except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurfaceInterpolateRate(obj, expiryDate, foreignRate, getDiscountFactor):
    args = [obj, expiryDate, foreignRate, getDiscountFactor]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface", method="InterpolateRate")
    except Exception:
        s = f"VolSurfaceInterpolateRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXVolSurface(args1, args2, args3, args4, args5, fmt="DT|VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpFXVolSurface")
    except Exception as e:
        s = f"McpMktVolSurface except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetVolatility(vs, strike, expiryDate, forward=0.0, inputDeltaVolPair=""):
    """
    根据行权价/到期获取（单边）波动率；可额外输入自定义 delta-vol 对。
    """
    args = [vs, strike, expiryDate, forward, json.dumps(inputDeltaVolPair)]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetVolatility")
    except Exception:
        s = f"FXVolSurfaceGetVolatility except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetVolatilityByDeltaStr(vs, deltaString, expiryDate, midForward=0.0, inputDeltaVolPair=""):
    args = [vs, deltaString, expiryDate, midForward, json.dumps(inputDeltaVolPair)]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetVolatilityByDeltaStr")
    except Exception:
        s = f"FXVolSurfaceGetVolatility except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetDomesticRate(vs, expiryOrDeliveryDate, isDeliveryDate, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetDomesticRate")
    except Exception:
        s = f"FXVolSurfaceGetDomesticRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetForeignRate(vs, expiryOrDeliveryDate, isDeliveryDate, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetForeignRate")
    except Exception:
        s = f"FXVolSurfaceGetForeignRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetForward(vs, expiryOrDeliveryDate, isDeliveryDate, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetForward")
    except Exception:
        s = f"FXVolSurfaceGetForward except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetForwardPoint(vs, expiryOrDeliveryDate, isDeliveryDate, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetForwardPoint")
    except Exception:
        s = f"FXVolSurfaceGetForwardPoint except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurfaceGetATMVol(vs, expiryDate):
    args = [vs, expiryDate]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface", method="GetATMVol")
    except Exception:
        s = f"FXVolSurfaceGetATMVol except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# FXVolSurface2（双边）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpMktVolSurface2(args1, args2, args3, args4, args5, fmt="VP"):
    """
    兼容别名：构造 FXVolSurface2。
    """
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpFXVolSurface2")
    except Exception as e:
        s = f"McpMktVolSurface2 except: {e}"
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
def McpFXVolSurface2(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpFXVolSurface2")
    except Exception as e:
        s = f"McpFXVolSurface2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetVolatility(
    vs,
    strike,
    expiryDate,
    bidMidAsk,
    midForward=0.0,
    bidInputDeltaVolPair="",
    asknputDeltaVolPair="",
):
    args = [
        vs,
        strike,
        expiryDate,
        bidMidAsk,
        midForward,
        json.dumps(bidInputDeltaVolPair),
        json.dumps(asknputDeltaVolPair),
    ]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetVolatility")
    except Exception:
        s = f"FXVolSurface2GetVolatility except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetVolatilityByDeltaStr(
    vs,
    deltaString,
    expiryDate,
    bidMidAsk,
    midForward=0.0,
    bidInputDeltaVolPair="",
    asknputDeltaVolPair="",
):
    args = [
        vs,
        deltaString,
        expiryDate,
        bidMidAsk,
        midForward,
        json.dumps(bidInputDeltaVolPair),
        json.dumps(asknputDeltaVolPair),
    ]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetVolatilityByDeltaStr")
    except Exception:
        s = f"FXVolSurface2GetVolatility except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetForward(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetForward")
    except Exception:
        s = f"FXVolSurface2GetForward except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetForwardPoint(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetForwardPoint")
    except Exception:
        s = f"FXVolSurface2GetForwardPoint except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetForeignRate(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetForeignRate")
    except Exception:
        s = f"FXVolSurface2GetForeignRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetDomesticRate(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect=False):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk, isDirect]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetDomesticRate")
    except Exception:
        s = f"FXVolSurface2GetDomesticRate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2StrikeFromString(vs, strikeString, bidMidAsk, callPut, expiryDate, spotPx, forwardPx):
    args = [vs, strikeString, bidMidAsk, callPut, expiryDate, spotPx, forwardPx]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="StrikeFromString")
    except Exception:
        s = f"FXVolSurface2StrikeFromString except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetStrike(vs, deltaString, tenor, bidMidAsk):
    args = [vs, deltaString, tenor, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetStrike")
    except Exception:
        s = f"FXVolSurface2GetStrike except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetATMVol(vs, expiryDate, bidMidAsk):
    args = [vs, expiryDate, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetATMVol")
    except Exception:
        s = f"FXVolSurface2GetATMVol except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetSpot(vs, bidMidAsk):
    args = [vs, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetSpot")
    except Exception:
        s = f"FXVolSurface2GetSpot except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetReferenceDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetReferenceDate")
    except Exception:
        s = f"FXVolSurface2GetReferenceDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def FXVolSurface2GetSpotDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetSpotDate")
    except Exception:
        s = f"FXVolSurface2GetSpotDate except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def FXVolSurface2GetParams(vs, expiryDate, bidMidAsk, fmt="V"):
    args = [vs, expiryDate, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetParams")
    except Exception:
        s = f"FXVolSurface2GetParams except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def FXVolSurface2GetDeltaStrings(vs, fmt="H"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetDeltaStrings")
    except Exception:
        s = f"FXVolSurface2GetDeltaStrings except: {args}"
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def FXVolSurface2GetTenors(vs, fmt="V"):
    args = [vs, fmt]
    try:
        return tool_def.xls_call(*args, key="McpFXVolSurface2", method="GetTenors")
    except Exception:
        s = f"FXVolSurface2GetTenors except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# VolSurface2（通用双边）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVolSurface2(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpVolSurface2")
    except Exception as e:
        s = f"McpVolSurface2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetVolatility(vs, interpVariable, maturityDate, bidMidAsk):
    args = [vs, interpVariable, maturityDate, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetVolatility")
    except Exception as e:
        s = f"VolSurface2GetVolatility except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetForward(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetForward")
    except Exception as e:
        s = f"VolSurface2GetForward except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetRiskFreeRate(vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk):
    args = [vs, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetRiskFreeRate")
    except Exception as e:
        s = f"VolSurface2GetRiskFreeRate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2StrikeFromString(vs, s, bidMidAsk, callPut, expiryDate, spotPx, forwardPx):
    args = [vs, s, bidMidAsk, callPut, expiryDate, spotPx, forwardPx]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="StrikeFromString")
    except Exception as e:
        s = f"VolSurface2StrikeFromString except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetSpot(vs, bidMidAsk):
    args = [vs, bidMidAsk]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetSpot")
    except Exception as e:
        s = f"VolSurface2GetSpot except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetReferenceDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetReferenceDate")
    except Exception as e:
        s = f"VolSurface2GetReferenceDate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def VolSurface2GetSpotDate(vs):
    args = [vs]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetSpotDate")
    except Exception as e:
        s = f"VolSurface2GetSpotDate except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurface2ExpiryDates(vs, bidMidAsk, fmt="V"):
    args = [vs, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="ExpiryDates")
    except Exception as e:
        s = f"VolSurface2ExpiryDates except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurface2ExpiryTimes(vs, bidMidAsk, fmt="V"):
    args = [vs, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="ExpiryTimes")
    except Exception as e:
        s = f"VolSurface2ExpiryTimes except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, transpose=True, auto_resize=True)
def VolSurface2Strikes(vs, bidMidAsk, fmt="V"):
    args = [vs, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="Strikes")
    except Exception as e:
        s = f"VolSurface2Strikes except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurface2Volatilities(vs, bidMidAsk, fmt="V"):
    args = [vs, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="Volatilities")
    except Exception as e:
        s = f"VolSurface2Volatilities except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def VolSurface2GetForwards(vs, bidMidAsk, fmt="V"):
    args = [vs, bidMidAsk, fmt]
    try:
        return tool_def.xls_call(*args, key="McpVolSurface2", method="GetForwards")
    except Exception as e:
        s = f"VolSurface2GetForwards except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


# =========================
# 市场波动率表面（翼比率）
# =========================
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def MktVolSurfaceGetWingRatios(vs, expiryDate, isCall, fmt="V"):
    args = [vs, expiryDate, isCall, fmt]
    try:
        return tool_def.xls_call(*args, key="McpMktVolSurface", method="GetWingRatios")
    except Exception as e:
        s = f"MktVolSurfaceGetWingRatios except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def MktVolSurfaceGetWingRatio(vs, expiryDate, isCall):
    args = [vs, expiryDate, isCall]
    try:
        return tool_def.xls_call(*args, key="McpMktVolSurface", method="GetWingRatio")
    except Exception as e:
        s = f"MktVolSurfaceGetWingRatio except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def MktVolSurface2GetWingRatios(vs, expiryDate, isCall, fmt="V"):
    args = [vs, expiryDate, isCall, fmt]
    try:
        return tool_def.xls_call(*args, key="McpMktVolSurface2", method="GetWingRatios")
    except Exception as e:
        s = f"MktVolSurface2GetWingRatios except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def MktVolSurface2GetWingRatio(vs, expiryDate, isCall):
    args = [vs, expiryDate, isCall]
    try:
        return tool_def.xls_call(*args, key="McpMktVolSurface2", method="GetWingRatio")
    except Exception as e:
        s = f"MktVolSurface2GetWingRatio except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


# =========================
# 结构化产品构建（示例）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpSingleCumulative(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpSingleCumulative")
    except Exception as e:
        s = f"McpSingleCumulative except: {e}"
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
def McpDoubleCumulative(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpDoubleCumulative")
    except Exception as e:
        s = f"McpDoubleCumulative except: {e}"
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
def McpEFXForward(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpEFXForward")
    except Exception as e:
        s = f"McpEFXForward except: {e}"
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
def McpFXSwap(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpEFXSwap")
    except Exception as e:
        s = f"McpFXSwap except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True)
def McpScaleFactor(obj_or_pair):
    """
    返回对象或对象对的 ScaleFactor。
    注意：原实现中 isinstance(str) 分支无意义，保留结构不改逻辑。
    """
    if isinstance(obj_or_pair, str):
        return obj_or_pair.ScaleFactor()
    else:
        return obj_or_pair.ScaleFactor()


# =========================
# Heston 模型（桥接）
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpHestonModel(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpHestonModel")
    except Exception as e:
        s = f"McpHestonModel except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
def HmHestonCalibration(curve, initParams, fmt="V"):
    args = [curve, initParams, fmt]
    try:
        return tool_def.xls_call(*args, key="McpHestonModel", method="HestonCalibration")
    except Exception:
        s = f"HmHestonCalibration except: {args}"
        logging.warning(s, exc_info=True)
        return s


# =========================
# Local Volatility 模型
# =========================

@xl_func(macro=False,recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpLocalVol(args1, args2, args3, args4, args5, fmt='DT|VP|HD'):
    if(args1[-1][0] is None):
        args1 = [row for row in args1 if not all(item is None for item in row)]
    if(args2[-1][0] is None):   
        args2 = [row for row in args2 if not all(item is None for item in row)]

    args=[args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpLocalVol')
    except Exception as e:
        s = f"McpLocalVol except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s
    
@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
def LocalVolGetSpot(vs):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetSpot()
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def LocalVolGetForward(vs, expiryOrDeliveryDate,isDeliveryDate):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetForward(date_to_string(expiryOrDeliveryDate), isDeliveryDate=False)
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def LocalVolGetRiskFreeRate(vs, expiryOrDeliveryDate,isDeliveryDate):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetRiskFreeRate(date_to_string(expiryOrDeliveryDate), isDeliveryDate=False)
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
@xl_arg("expiryOrDeliveryDate", "datetime")
@xl_arg("isDeliveryDate", "bool")
def LocalVolGetUnderlyingRate(vs, expiryOrDeliveryDate,isDeliveryDate):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetUnderlyingRate(date_to_string(expiryOrDeliveryDate), isDeliveryDate=False)
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
def LocalVolGetDividend(vs):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetDividend()
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
def LocalVolGetModelType(vs):
    if not isinstance(vs, mcp.wrapper.McpLocalVol):
        return "Invalid McpLocalVol"
    result = vs.GetModelType()
    return result


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("vs", "object")
@xl_arg("fmt", "str")
def LocalVolParameters(vs):
    s = vs.Parameters()
    return as_array(s, "V")

@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("vs", "object")
@xl_arg("isLowerGuess", "bool")
@xl_arg("fmt", "str")
def LocalVolParamRanges(vs, isLowerGuess):
    s = vs.ParamRanges(isLowerGuess)
    return as_array(s, "V")

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
def LocalVolGetTraceFileName(vs):
    return vs.GetTraceFileName()
  
@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("vs", "object")
@xl_arg("fmt", "str")
def LocalVolExpiryDates(vs, fmt='H'):
    s = vs.ExpiryDates()
    return as_array(s, fmt)

  
@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("vs", "object")
@xl_arg("fmt", "str")
def LocalVolStrikes(vs, fmt='V'):
    s = vs.Strikes()
    return as_array(s, fmt)

  
@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("vs", "object")
@xl_arg("fmt", "str")
@xl_return("var[][]")
def LocalVolVolatilities(vs, fmt='V'):
    arr = vs.Volatilities()
    return as_2d_array(arr, fmt, False)

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("vs", "object")
@xl_arg("strike", "float")
@xl_arg("expiry", "datetime")
def LocalVolGetVolatility(vs, strike, expiry):
    s = vs.GetVolatility(strike, date_to_string(expiry))
    return s

# =========================
# 期权数据封装
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpOptionData(args1, args2, args3, args4, args5, fmt="VP|HD"):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpOptionData")
    except Exception as e:
        s = f"McpOptionData except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s