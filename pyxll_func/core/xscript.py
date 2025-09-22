# -*- coding: utf-8 -*-

"""
This module provides function wrappers for constructing, pricing, and valuing complex structured derivatives in Excel/PyXLL environment.
Core concepts:
- McpStructureDef: Used to define structured products (such as range accruals) with required package names, structures, schedules, and payment terms.
- xScriptStructure (abbreviated as xss): Complex structured product object; xssXXXX represents specific method wrappers on this object for Excel calls.
"""

# =========================
# Standard Library Imports (alphabetical order)
# =========================
import json
import logging
import os

# =========================
# Third Party Library Imports (alphabetical order)
# =========================
import numpy as np
import pandas as pd
import pyxll
from pyxll import RTD, xl_arg, xl_app, xl_func, xl_return, xlfCaller  # noqa: F401

# =========================
# Project Internal Module Imports (alphabetical order, subpackages first)
# =========================
import mcp.mcp  # Reserved: may be referenced by Excel side activation
import mcp.xscript.structure as xsst
import mcp.xscript.utils as xsutils
from mcp.forward.compound import payoff_generate_spots  # noqa: F401 May be called in other paths
from mcp.tool.args_def import McpArgsException, McpException
from mcp.utils.enums import DateAdjusterRule, InterpolatedVariable, enum_wrapper  # noqa: F401
from mcp.utils.excel_utils import (
    data_cache,
    from_excel_ordinal,
    mcp_kv_wrapper,
    mcp_method_args_cache,
    pf_array,
    pf_array_date_json,
    pf_array_json,
    pf_date,
    to_excel_ordinal,
)
from mcp.utils.mcp_utils import (
    as_2d_array,
    as_array,
    debug_args_info,
    mcp_dt,
    trans_2d_array,
)
from mcp.xscript.xs_tools import XssLVPlot, XssMCPlot


# =========================
# Excel/PyXLL Binding Functions
# =========================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
def McpModelDef(args):
    """
    Define global model objects (such as curve, volatility and other model parameters).
    args: Key-value/table parameters passed from Excel as 2D region.
    Returns: xsst.McpModelDef object (for reference by other functions).
    """
    xl = xl_app()
    addr = xl.Caller.GetAddress(External=True)
    return xsst.McpModelDef(args, addr)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("packageName", "str")
@xl_arg("structure", "var[][]")
@xl_arg("schedule1", "var[][]")
@xl_arg("payoff", "var[][]")
@xl_arg("schedule2", "var[][]")
def McpStructureDef(packageName, structure, schedule1, payoff, schedule2):
    """
    Define static information and terms for structured products.
    packageName: Product package name/template name
    structure/scheduleX/payoff: 2D parameter regions from Excel
    Returns: Structure definition object for subsequent product instantiation.
    """
    xl = xl_app()
    addr = xl.Caller.GetAddress(External=True)
    stt_def = xsst.McpStructureDef(packageName, structure, [schedule1, schedule2], payoff, addr)
    return stt_def


@xl_func(macro=False, recalc_on_open=True)
def McpModelClear():
    """
    清除当前单元格地址对应的模型缓存（便于刷新）。
    """
    xl = xl_app()
    addr = xl.Caller.GetAddress(External=True)
    arr = xsst.stt_def_manager.model().clear(addr)
    return f"Clear: {arr}"


@xl_func(macro=False, recalc_on_open=True)
def McpStructureClear():
    """
    清除当前单元格地址对应的结构定义缓存。
    """
    xl = xl_app()
    addr = xl.Caller.GetAddress(External=True)
    arr = xsst.stt_def_manager.stt().clear(addr)
    return f"Clear: {arr}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpStructuredProd2(args1, args2, args3, args4, args5, fmt="VP|HD"):
    """
    根据多段 Excel 输入解析结构化产品参数，并构造产品对象（简化版）。
    返回：xsst.McpStructuredProd 或缺失字段提示。
    """
    args = [args1, args2, args3, args4, args5]
    data_fields = [
        ("ModelParam", "float"),
    ]
    d = mcp_kv_wrapper.args_parser.parse_all(args, fmt, data_fields, True)
    prod = xsst.McpStructuredProd(d)
    if len(prod.lack_keys) > 0:
        return f"Missing fields: {prod.lack_keys}"
    return prod


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("field_name", "str")
@xl_arg("greek_type", "str")
def XssGetData(obj, field_name, greek_type="Ccy1"):
    """
    通用数据拉取接口：从 xss 对象中取任意字段（含希腊值）。
    """
    try:
        return obj.get_field_value(field_name, greek_type=greek_type)
    except Exception as e:
        return f"XssGetData except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpXScriptStructure(args1, args2, args3, args4, args5, fmt="VP|HD"):
    """
    构建 xScript 结构化产品对象。
    - 输入为 5 段二维参数区域，配合 fmt 解析。
    - data_fields 中列出可能需要的历史 Fixing 信息等。
    """
    args = [args1, args2, args3, args4, args5]
    data_fields = [
        ("FixingDates", "date"),
        ("FixingRates", "float"),
    ]
    d = mcp_kv_wrapper.args_parser.parse_all(args, fmt, data_fields, True)
    try:
        prod = xsst.McpXScriptStructure(d)
        return prod
    except McpArgsException as e:
        return f"Missing fields: {e.lack_fields}"
    except McpException as me:
        logging.info(f"McpXScriptStructure McpException: {me.get_msg()}", exc_info=True)
        return me.get_msg()
    except Exception as e:
        # 兜底异常：避免调用不存在的 get_msg/get_mesg
        logging.info(f"McpXScriptStructure Exception: {e}", exc_info=True)
        return str(e)
    except:  # noqa: E722
        logging.info("McpXScriptStructure other exception", exc_info=True)
        return "McpXScriptStructure other exception"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def XssAnnualizedPrice(obj):
    """
    年化价格（若产品内部定义为年化收益/价格）。
    """
    return obj.AnnualizedPrice()


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssMarketValue(obj, isAmount=True):
    """
    市值（可返回金额或比率）。
    """
    return obj.MarketValue(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("variable", "str")
def XssResultByVariable(obj, variable):
    """
    按指定变量维度返回结果（如情景、曲线名等）。
    """
    return obj.ResultByVariable(variable)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssPV(obj, isAmount=True):
    """
    现值（Present Value）。
    """
    return obj.PV(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssPrice(obj, isAmount=True):
    """
    价格（与 PV 的区别由产品实现决定）。
    """
    return obj.Price(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssPremium(obj, isCCY2=True, isAmount=True):
    """
    权利金（可指定货币边 isCCY2、返回形式 isAmount）。
    """
    return obj.Premium(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssDelta(obj, isCCY2=False, isAmount=True):
    """
    Delta（价格对标的的一阶敏感）。
    """
    return obj.Delta(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssGamma(obj, isCCY2=False, isAmount=True):
    """
    Gamma（价格对标的的二阶敏感）。
    """
    return obj.Gamma(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssTheta(obj, isCCY2=True, isAmount=True):
    """
    Theta（时间敏感）。
    """
    return obj.Theta(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssVega(obj, isCCY2=True, isAmount=True):
    """
    Vega（对波动的敏感）。
    """
    return obj.Vega(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssRho(obj, isCCY2=True, isAmount=True):
    """
    Rho（对利率的敏感）。
    """
    return obj.Rho(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssVanna(obj, isCCY2=True, isAmount=True):
    """
    Vanna（对标的与波动的混合二阶敏感）。
    """
    return obj.Vanna(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssVolga(obj, isCCY2=True, isAmount=True):
    """
    Volga（又称 Vomma，对波动的二阶敏感）。
    """
    return obj.Volga(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def XssForwardDelta(obj, isCCY2=True, isAmount=True):
    """
    远期 Delta（某些产品的远期合约维度的敏感度）。
    """
    return obj.ForwardDelta(isCCY2, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def XssGetTraceFileName(obj):
    """
    获取计算产生的 Trace/Report 文件名（供可视化/诊断）。
    """
    return obj.GetTraceFileName()


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
def XssEvents(obj):
    """
    返回产品的事件序列（如观测、支付、敲入敲出等）。
    以二维数组形式回传，方便 Excel 展示。
    """
    events = obj.Events()
    arr_dict = as_2d_array(events, "H")
    items_list = [(key, value) for key, value in arr_dict.items()]
    return items_list


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
def XssEventDates(obj):
    """
    返回产品关键事件日期（JSON 数组形式解析）。
    """
    s = json.loads(obj.EventDates())
    return s


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def HmReport(obj):
    """
    根据 Trace 文件类型，生成 LocalVol 或 MC 的 HTML 报告。
    注意：此函数返回 HTML 字符串，供前端嵌入渲染。
    """
    traceFileName = obj.GetTraceFileName()
    if not traceFileName:
        return ""
    try:
        if "LocalVol" in traceFileName:
            return XssLVPlot.gen_html(traceFileName)
        return XssMCPlot.gen_html(traceFileName)
    except Exception:
        msg = f"HmReport exception: {traceFileName}"
        logging.info(msg, exc_info=True)
        return msg


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("prod", "object")
@xl_arg("fields", "str[]")
def McpProductPricingArgs(prod, fields):
    """
    执行产品脚本，按字段清单提取参数/结果，按列返回。
    """
    fields_static = []
    fs = []
    for item in fields:
        if item is not None:
            fs.append(str(item))
    fs.extend(fields_static)
    d = prod.exec_script()
    d = xsutils.SttUtils.to_lower_key(d)
    result = []
    for field in fs:
        item = field.lower()
        val = d.get(item, "")
        result.append([val])
    return result


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("prod", "object")
def McpProductPricing(prod):
    """
    执行产品脚本，直接返回 'opt' 字段（若存在）。
    """
    d = prod.exec_script()
    d = xsutils.SttUtils.to_lower_key(d)
    return d.get("opt", None)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("structure", "object")
def McpStructureName(structure):
    """
    读取结构定义对象的包名。
    """
    return structure.pkg_name


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("model", "object")
def McpModelName(model):
    """
    读取模型对象的名称。
    """
    return model.name


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("prod", "object")
def McpProductEvents(prod):
    """
    直接返回产品事件列表（假定已为二维数组或序列化可展开）。
    """
    events = prod.get_events()
    return events


# 预留：Heston 相关接口
# @xl_func(macro=False, recalc_on_open=False)
# @xl_arg("vs", "object")
# def McpHestonModel(vs):
#     return mcp.mcp.MHestonModel(vs.getHandler())
#
# @xl_func(macro=False, recalc_on_open=False, auto_resize=True)
# @xl_arg("hm", "object")
# @xl_arg("initParams", "float[]")
# @xl_arg("fmt", "str")
# def HmHestonCalibration(hm, initParams, fmt='V'):
#     s = hm.HestonCalibration(json.dumps(initParams))
#     return as_array(s, fmt)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("priceObj", "object")
@xl_arg("premium", "float")
@xl_arg("targetField", "str")
@xl_arg("x0", "float")
@xl_arg("bracket", "float[]")
@xl_arg("method", "str")
@xl_arg("options", "dict")
@xl_arg("isAnnualized", "bool")
def xssSolverFromPremium(
    priceObj,
    premium,
    targetField,
    x0=1.0,
    bracket=(-100, 100),
    method="bisect",
    options=None,
    isAnnualized=False,
):
    """
    通过目标权利金反解某参数（如波动、strike 等）。
    """
    if options is None:
        options = {"maxiter": 50, "xtol": 1e-6}
    if not isinstance(premium, float):
        raise ValueError("premium not valid!")
    if not isinstance(targetField, str):
        raise ValueError("targetField not valid!")
    rf = xsst.Solver(priceObj)
    result = rf.SoverFromPremium(premium, targetField, x0, tuple(bracket), method, options, isAnnualized)
    del rf
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("priceObj", "object")
@xl_arg("delta", "float")
@xl_arg("targetField", "str")
@xl_arg("x0", "float")
@xl_arg("bracket", "float[]")
@xl_arg("method", "str")
@xl_arg("options", "dict")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
@xl_arg("curveType", "str")
@xl_arg("interp_method", "str")
def xssSolverFromDelta(
    priceObj,
    delta,
    targetField,
    x0=1.0,
    bracket=(-100, 100),
    method="bisect",
    options=None,
    isCCY2=True,
    isAmount=True,
    curveType="monotonic",
    interp_method=None,
):
    """
    基于目标 Delta 求解目标参数。
    - method/选项参考 SciPy 根求解器习惯（如 bisect）。
    - interp_method 用于常规失败后的插值兜底（可能较慢）。
    """
    if options is None:
        options = {"maxiter": 50, "xtol": 1e-6}
    if not isinstance(delta, float):
        raise ValueError("delta not valid!")
    if not isinstance(targetField, str):
        raise ValueError("targetField not valid!")
    rf = xsst.Solver(priceObj)
    result = rf.SolverFromDelta(
        delta,
        targetField,
        x0,
        tuple(bracket),
        method,
        options,
        isCCY2,
        isAmount,
        curveType,
        interp_method,
    )
    del rf
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("priceObj", "object")
@xl_arg("targetField", "str")
@xl_arg("bracket", "float[]")
@xl_arg("isCCY2", "bool")
@xl_arg("isAmount", "bool")
def xssDeltaPlot(
    priceObj,
    targetField,
    bracket=(-100, 100),
    num_points=20,
    isCCY2=False,
    isAmount=True,
):
    """
    绘制目标参数与 Delta 的关系（返回二维数组，已转置以便 Excel 作图）。
    """
    if not isinstance(targetField, str):
        raise ValueError("targetField not valid!")
    rf = xsst.Solver(priceObj)
    result = rf.DeltaPlot(targetField, bracket, num_points, isCCY2, isAmount)
    array_data = np.array(result)
    transposed = array_data.transpose()
    return transposed