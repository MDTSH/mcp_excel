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
import math
import os
import copy

# =========================
# Third Party Library Imports (alphabetical order)
# =========================
from mcp.optional_deps import numpy as np
from mcp.optional_deps import pandas as pd
import pyxll
from pyxll import RTD, xl_arg, xl_app, xl_func, xl_return, xlfCaller  # noqa: F401

# =========================
# Project Internal Module Imports (alphabetical order, subpackages first)
# =========================
import mcp.mcp  # Reserved: may be referenced by Excel side activation
import mcp.xscript.greeks_diff  # noqa: F401  patch SDP DeltaDiff1Pct / GammaDiff1Pct
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
    normalize_sdp_schedule_dates_json,
    pf_array,
    pf_array_date_json,
    pf_array_json,
    pf_date,
    to_excel_ordinal,
)
from mcp.utils.workbook_path import resolve_data_path
from mcp.utils.mcp_utils import (
    as_2d_array,
    as_array,
    debug_args_info,
    mcp_dt,
    trans_2d_array,
)
from mcp.xscript.xs_tools import XssLVPlot, XssMCPlot


def _resolve_trace_file_name(trace_file_name):
    """Resolve relative trace paths returned by xScript/LocalVol into an existing file."""
    if not trace_file_name:
        return "", []
    trace_file_name = str(trace_file_name).replace("\\", os.sep).replace("/", os.sep)
    if trace_file_name.startswith("file:" + os.sep + os.sep + os.sep):
        trace_file_name = trace_file_name[8:]
    elif trace_file_name.startswith("file:" + os.sep + os.sep):
        trace_file_name = trace_file_name[7:]

    candidates = []
    if os.path.isabs(trace_file_name):
        candidates.append(trace_file_name)
    else:
        module_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        candidates.extend([
            os.path.abspath(trace_file_name),
            os.path.join(os.getcwd(), trace_file_name),
            os.path.join(os.path.expanduser("~"), "Documents", trace_file_name),
            os.path.join(module_root, trace_file_name),
        ])

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        normalized = os.path.normpath(candidate)
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(normalized)
        if os.path.isfile(normalized):
            return normalized, unique_candidates
    return os.path.normpath(trace_file_name), unique_candidates


def _xss_result_by_variable(obj, variable):
    raw_variable = "" if variable is None else str(variable).strip()
    if not raw_variable:
        return "XssResultByVariable error: variable name is empty."
    result = obj.ResultByVariable(raw_variable)
    if isinstance(result, float) and math.isnan(result):
        return (
            f"XssResultByVariable error: variable '{raw_variable}' was not found in pricing results. "
            "Please use the exact xScript output variable name, for example 'UpperProb', "
            "'MiddleProb', or 'LowerProb'."
        )
    return result


# 期权费/Premium 的"约定字段名"——按优先级查找：
# - fee_var_names:   YAML 中通过 `fee pays ...` 等收集的现值变量名
# - amount_field:    显式金额字段（OptionFee / Premium），方向通过 sign_field 调整
# - sign_field:      方向字段（OptionFeePayRcv / PayRcv，+1=Receive, -1=Pay）
_NPV_FEE_VAR_NAMES = ("fee", "Fee", "FEE", "OptionFee", "OPTIONFEE", "Premium", "PREMIUM")
_NPV_AMOUNT_FIELDS = ("OptionFee", "Premium")
_NPV_SIGN_FIELDS = ("OptionFeePayRcv", "PremiumPayRcv", "PayRcv")


def _safe_result_by_variable(obj, name):
    """容错版 ResultByVariable：找不到/NaN 返回 None。"""
    try:
        val = obj.ResultByVariable(name)
    except Exception:
        return None
    if isinstance(val, float) and (val != val):  # NaN
        return None
    return val


def _xss_npv(obj, isAmount=True):
    """
    NPV = PV + 期权费现值。

    优先级：
      1) C++ 已实现 `NPV(isAmount)` → 直接调用（最准确，期权费按 EndDate 折现）；
      2) YAML 中存在 `fee pays ...` collector → PV + ResultByVariable('fee')；
         （fee 已通过 `pays` 自动折现到 AsOfDate）
      3) 退化方案：PV + OptionFeePayRcv * OptionFee（不折现，仅适合短期产品）。
    """
    if hasattr(obj, "NPV"):
        try:
            return obj.NPV(isAmount)
        except Exception:
            pass

    try:
        pv = obj.PV(isAmount)
    except Exception as e:
        return f"XssNPV error: PV failed: {e}"

    # 方案 2：从 collector 取 fee
    for name in _NPV_FEE_VAR_NAMES:
        fee_pv = _safe_result_by_variable(obj, name)
        if fee_pv is not None:
            if isAmount:
                return pv + fee_pv
            notional = getattr(obj, "_npv_notional", None)
            if notional:
                return pv + fee_pv / notional
            return pv + fee_pv

    # 方案 3：用对象属性退化（需用户挂载 _npv_option_fee / _npv_option_fee_pay_rcv）
    amt = getattr(obj, "_npv_option_fee", None)
    sgn = getattr(obj, "_npv_option_fee_pay_rcv", 1)
    if amt is not None:
        return pv + float(sgn) * float(amt)

    return ("XssNPV warning: no 'fee'/'OptionFee' collector found in pricing results; "
            "returning PV unchanged. Either rebuild C++ with NPV() exposed, "
            "or add `fee pays OptionFeePayRcv * OptionFee` in YAML payoff.")


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
    return _xss_result_by_variable(obj, variable)


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
@xl_arg("isAmount", "bool")
def XssNPV(obj, isAmount=True):
    """
    NPV（Net Present Value） = PV + 期权费现值。

    与 Price-It 的 NPV 列对齐：客户真实净现金流的现值（PV 不含期权费时）。
    实现优先级：
      1) C++ 端 `obj.NPV(isAmount)`（重新编译 _mcp 后可用，最准确）；
      2) 从 YAML 的 collector 取 `fee` 现值（fee pays 已自动折现）；
      3) 若以上都没有，返回提示文本。

    Excel 示例：
      =XssNPV(SDP, TRUE)
    """
    return _xss_npv(obj, isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssPremium(obj, isAmount=True):
    """
    权利金（可指定货币边 isCCY2、返回形式 isAmount）。
    """
    return obj.Premium(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssDelta(obj, isAmount=True):
    """
    Delta（价格对标的的一阶敏感）。
    """
    return obj.Delta(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssGamma(obj, isAmount=True):
    """
    Gamma（价格对标的的二阶敏感）。
    """
    return obj.Gamma(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssTheta(obj, isAmount=True):
    """
    Theta（时间敏感）。
    """
    return obj.Theta(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssVega(obj, isAmount=True):
    """
    Vega（对波动的敏感）。
    """
    return obj.Vega(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssRho(obj, isAmount=True):
    """
    Rho（对利率的敏感）。
    """
    return obj.Rho(isAmount)


# ========== Equity Greeks（Equity 标准 Greeks，单位与 pricelib 一致）==========

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityDelta(obj, isAmount=True):
    """
    Equity Delta（spot 变化 1 个货币单位，单位 Delta = EquityDeltaCash / Spot）。
    """
    try:
        if hasattr(obj, 'EquityDelta'):
            return obj.EquityDelta(isAmount)
        return f"Object does not have EquityDelta method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityDelta except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityDeltaCash(obj, isAmount=True):
    """
    Equity Delta Cash（Delta * Spot）。
    """
    try:
        if hasattr(obj, 'EquityDeltaCash'):
            return obj.EquityDeltaCash(isAmount)
        return f"Object does not have EquityDeltaCash method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityDeltaCash except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityGamma(obj, isAmount=True):
    """
    Equity Gamma（spot 变化 1 个货币单位）。
    """
    try:
        if hasattr(obj, 'EquityGamma'):
            return obj.EquityGamma(isAmount)
        return f"Object does not have EquityGamma method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityGamma except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityGammaCash(obj, isAmount=True):
    """
    Equity Gamma Cash（Gamma * Spot）。
    """
    try:
        if hasattr(obj, 'EquityGammaCash'):
            return obj.EquityGammaCash(isAmount)
        return f"Object does not have EquityGammaCash method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityGammaCash except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssDeltaDiff1Pct(obj, isAmount=True):
    """
    前向差分 Delta，ε = spot × 1%。
    返回单位 Delta = DeltaDiff1PctCash / Spot。
    C++ 未重编译时由 EquityDelta + Gamma 近似。
    """
    try:
        if hasattr(obj, 'DeltaDiff1Pct'):
            return obj.DeltaDiff1Pct(isAmount)
        if hasattr(obj, 'EquityDelta') and hasattr(obj, 'EquityGamma'):
            spot = float(obj.getUnderlyingPrice())
            eps = spot * 0.01
            return obj.EquityDelta(isAmount) + obj.EquityGamma(isAmount) * (eps / 2.0)
        return f"Object does not have DeltaDiff1Pct method: {type(obj).__name__}"
    except Exception as e:
        return f"XssDeltaDiff1Pct except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssDeltaDiff1PctCash(obj, isAmount=True):
    """
    前向差分 Delta Cash，ε = spot × 1%。
    C++ 未重编译时由 EquityDeltaCash + Gamma×ε/2×Spot 近似。
    """
    try:
        if hasattr(obj, 'DeltaDiff1PctCash'):
            return obj.DeltaDiff1PctCash(isAmount)
        if hasattr(obj, 'EquityDeltaCash') and hasattr(obj, 'EquityGamma'):
            spot = float(obj.getUnderlyingPrice())
            eps = spot * 0.01
            return obj.EquityDeltaCash(isAmount) + obj.EquityGamma(isAmount) * (eps / 2.0) * spot
        return f"Object does not have DeltaDiff1PctCash method: {type(obj).__name__}"
    except Exception as e:
        return f"XssDeltaDiff1PctCash except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssGammaDiff1Pct(obj, isAmount=True):
    """
    中心差分 Gamma，ε = spot × 1%。
    """
    try:
        if hasattr(obj, 'GammaDiff1Pct'):
            return obj.GammaDiff1Pct(isAmount)
        return f"Object does not have GammaDiff1Pct method: {type(obj).__name__}（请重新编译 _mcp）"
    except Exception as e:
        return f"XssGammaDiff1Pct except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssGammaDiff1PctCash(obj, isAmount=True):
    """
    中心差分 Gamma Cash，ε = spot × 1%。
    """
    try:
        if hasattr(obj, 'GammaDiff1PctCash'):
            return obj.GammaDiff1PctCash(isAmount)
        return f"Object does not have GammaDiff1PctCash method: {type(obj).__name__}（请重新编译 _mcp）"
    except Exception as e:
        return f"XssGammaDiff1PctCash except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityVega(obj, isAmount=True):
    """
    Equity Vega：隐含波动率曲面各点绝对 +1 vol point（+0.01）后 Recalibrate。
    """
    try:
        if hasattr(obj, 'EquityVega'):
            return obj.EquityVega(isAmount)
        return f"Object does not have EquityVega method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityVega except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityTheta(obj, isAmount=True):
    """
    Equity Theta（时间流逝 1 天）。
    """
    try:
        if hasattr(obj, 'EquityTheta'):
            return obj.EquityTheta(isAmount)
        return f"Object does not have EquityTheta method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityTheta except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityRho(obj, isAmount=True):
    """
    Equity Rho：discount curve 各 tenor +1bp（+0.0001）；无曲线时 rate 绝对 +100bp。
    """
    try:
        if hasattr(obj, 'EquityRho'):
            return obj.EquityRho(isAmount)
        return f"Object does not have EquityRho method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityRho except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssEquityRhoQ(obj, isAmount=True):
    """
    Equity RhoQ / Phi：股息率 q 绝对 +100bp（+0.01），仅 rate2；r 与 discount 不变。
    """
    try:
        if hasattr(obj, 'EquityRhoQ'):
            return obj.EquityRhoQ(isAmount)
        return f"Object does not have EquityRhoQ method: {type(obj).__name__}"
    except Exception as e:
        return f"XssEquityRhoQ except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssVanna(obj, isAmount=True):
    """
    Vanna（对标的与波动的混合二阶敏感）。
    """
    return obj.Vanna(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssVolga(obj, isAmount=True):
    """
    Volga（又称 Vomma，对波动的二阶敏感）。
    """
    return obj.Volga(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssForwardDelta(obj, isAmount=True):
    """
    远期 Delta（某些产品的远期合约维度的敏感度）。
    """
    return obj.ForwardDelta(isAmount)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssCharm(obj, isAmount=True):
    """
    Charm（Delta对时间的敏感度，也称为Delta衰减）。
    """
    try:
        if hasattr(obj, 'Charm'):
            return obj.Charm(isAmount)
        else:
            return f"Object does not have Charm method: {type(obj).__name__}"
    except Exception as e:
        return f"XssCharm except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssColor(obj, isAmount=True):
    """
    Color（Gamma对时间的敏感度，也称为Gamma衰减）。
    """
    try:
        if hasattr(obj, 'Color'):
            return obj.Color(isAmount)
        else:
            return f"Object does not have Color method: {type(obj).__name__}"
    except Exception as e:
        return f"XssColor except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssSpeed(obj, isAmount=True):
    """
    Speed（Gamma对标的资产价格的三阶敏感度）。
    """
    try:
        if hasattr(obj, 'Speed'):
            return obj.Speed(isAmount)
        else:
            return f"Object does not have Speed method: {type(obj).__name__}"
    except Exception as e:
        return f"XssSpeed except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssUltima(obj, isAmount=True):
    """
    Ultima（Vega对波动率的三阶敏感度）。
    """
    try:
        if hasattr(obj, 'Ultima'):
            return obj.Ultima(isAmount)
        else:
            return f"Object does not have Ultima method: {type(obj).__name__}"
    except Exception as e:
        return f"XssUltima except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def XssGetTraceFileName(obj):
    """
    获取计算产生的 Trace/Report 文件名（供可视化/诊断）。
    """
    return obj.GetTraceFileName()


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def XssGetConfigFilePath(obj):
    """
    获取结构化产品配置文件的路径（YAML文件路径）。
    参数：McpStructuredDerivativeProduct对象
    返回：配置文件路径字符串
    """
    try:
        if hasattr(obj, 'getConfigFilePath'):
            return obj.getConfigFilePath()
        elif hasattr(obj, '_config_path'):
            # 如果C++方法不存在，尝试从Python属性获取
            return obj._config_path
        else:
            return "Config file path not available"
    except Exception as e:
        return f"XssGetConfigFilePath except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
def XssDistanceToBarrierSigma(obj):
    """
    计算到障碍价的标准差距离（Distance to Barrier in Sigma）。
    参数：McpStructuredDerivativeProduct对象
    返回：到障碍价的标准差距离
    """
    try:
        if hasattr(obj, 'DistanceToBarrierSigma'):
            return obj.DistanceToBarrierSigma()
        else:
            return f"Object does not have DistanceToBarrierSigma method: {type(obj).__name__}"
    except Exception as e:
        return f"XssDistanceToBarrierSigma except: {e}"


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssAllGreeks(obj, isAmount=True):
    """
    获取所有 Greeks（包括基础和高阶 Greeks）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - isAmount: 是否返回金额形式（默认 True）
    返回：包含所有 Greeks 的数组
    """
    try:
        if hasattr(obj, 'AllGreeks'):
            result_str = obj.AllGreeks(isAmount)
            if result_str:
                result_dict = json.loads(result_str)
                return [[greek, value] for greek, value in result_dict.items()]
            else:
                return []
        else:
            return f"Object does not have AllGreeks method: {type(obj).__name__}"
    except Exception as e:
        return f"XssAllGreeks except: {e}"


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("isAmount", "bool")
def XssBasicGreeks(obj, isAmount=True):
    """
    获取基础 Greeks（Delta, Gamma, Vega, Theta, Rho）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - isAmount: 是否返回金额形式（默认 True）
    返回：包含基础 Greeks 的数组
    """
    try:
        if hasattr(obj, 'BasicGreeks'):
            result_str = obj.BasicGreeks(isAmount)
            if result_str:
                result_dict = json.loads(result_str)
                return [[greek, value] for greek, value in result_dict.items()]
            else:
                return []
        else:
            return f"Object does not have BasicGreeks method: {type(obj).__name__}"
    except Exception as e:
        return f"XssBasicGreeks except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("horizonStr", "str")
@xl_arg("confidenceLevel", "float")
def XssVaR(obj, horizonStr, confidenceLevel=0.95):
    """
    计算 VaR（单个 horizon）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - horizonStr: horizon 字符串（如 "1D", "1M", "3M"）
    - confidenceLevel: 置信水平（默认 0.95）
    返回：VaR 值，如果 horizon 不存在则返回 NaN
    """
    try:
        if hasattr(obj, 'VaR'):
            return obj.VaR(horizonStr, confidenceLevel)
        else:
            return f"Object does not have VaR method: {type(obj).__name__}"
    except Exception as e:
        return f"XssVaR except: {e}"


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("confidenceLevel", "float")
def XssVaRCurve(obj, confidenceLevel=0.95):
    """
    计算 VaR 曲线（所有配置的 horizons）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - confidenceLevel: 置信水平（默认 0.95）
    返回：二维数组，每行为 [horizon, VaR值]，方便 Excel 展示
    """
    try:
        if hasattr(obj, 'VaRCurve'):
            result_str = obj.VaRCurve(confidenceLevel)
            if result_str:
                result_dict = json.loads(result_str)
                # 将字典转换为二维数组，每行为 [horizon, value]
                return [[horizon, value] for horizon, value in result_dict.items()]
            else:
                return []
        else:
            return f"Object does not have VaRCurve method: {type(obj).__name__}"
    except Exception as e:
        return f"XssVaRCurve except: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("horizonStr", "str")
@xl_arg("confidenceLevel", "float")
def XssPFE(obj, horizonStr, confidenceLevel=0.95):
    """
    计算 PFE（单个 horizon）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - horizonStr: horizon 字符串（如 "1D", "1M", "3M"）
    - confidenceLevel: 置信水平（默认 0.95）
    返回：PFE 值，如果 horizon 不存在则返回 NaN
    """
    try:
        if hasattr(obj, 'PFE'):
            return obj.PFE(horizonStr, confidenceLevel)
        else:
            return f"Object does not have PFE method: {type(obj).__name__}"
    except Exception as e:
        return f"XssPFE except: {e}"


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("confidenceLevel", "float")
def XssPFECurve(obj, confidenceLevel=0.95):
    """
    计算 PFE 曲线（所有配置的 horizons）。
    参数：
    - obj: McpStructuredDerivativeProduct对象
    - confidenceLevel: 置信水平（默认 0.95）
    返回：二维数组，每行为 [horizon, PFE值]，方便 Excel 展示
    """
    try:
        if hasattr(obj, 'PFECurve'):
            result_str = obj.PFECurve(confidenceLevel)
            if result_str:
                result_dict = json.loads(result_str)
                # 将字典转换为二维数组，每行为 [horizon, value]
                return [[horizon, value] for horizon, value in result_dict.items()]
            else:
                return []
        else:
            return f"Object does not have PFECurve method: {type(obj).__name__}"
    except Exception as e:
        return f"XssPFECurve except: {e}"


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
@xl_arg("dependency", "var")
def HmReport(obj, dependency=None):
    """
    根据 Trace 文件类型，生成 LocalVol 或 MC 的 HTML 报告。
    注意：此函数返回 HTML 字符串，供前端嵌入渲染。
    支持中文内容的Markdown文件。
    dependency 可传入 XssPrice/XssPV 单元格，强制 Excel 先完成定价再生成报告。
    """
    traceFileName = obj.GetTraceFileName()
    if not traceFileName:
        return ""
    try:
        resolvedTraceFileName, candidates = _resolve_trace_file_name(traceFileName)
        if not os.path.isfile(resolvedTraceFileName):
            return (
                f"HmReport file not generated: {traceFileName}. "
                "如果这是 StructuredProduct/xScript 报告，请先计算 XssPrice 或 XssPV，"
                "并可使用 =HmReport(productCell, priceCell) 让报告依赖价格单元格。"
                f" Checked: {candidates}"
            )
        if "LocalVol" in resolvedTraceFileName:
            return XssLVPlot.gen_html(resolvedTraceFileName)
        return XssMCPlot.gen_html(resolvedTraceFileName)
    except UnicodeDecodeError as e:
        msg = f"HmReport UnicodeDecodeError: {traceFileName}, error: {e}"
        logging.warning(msg, exc_info=True)
        return msg
    except Exception as e:
        msg = f"HmReport exception: {traceFileName}, error: {type(e).__name__}: {e}"
        logging.warning(msg, exc_info=True)
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


def _normalize_discount_curve_for_vol_ctor(curve_obj):
    if curve_obj is None:
        return None
    if isinstance(curve_obj, mcp.mcp.MYieldCurve):
        return curve_obj
    if hasattr(curve_obj, "getHandler"):
        try:
            return mcp.mcp.MYieldCurve(curve_obj.getHandler())
        except Exception:
            return curve_obj
    return curve_obj


def _normalize_bracket(bracket):
    """解析 Excel float[]、竖向区域或 McpList JSON 为 (start, end)。"""
    if bracket is None:
        raise ValueError("bracket must contain at least two values")

    if isinstance(bracket, str):
        text = bracket.strip()
        if not text:
            raise ValueError("bracket must contain at least two values")
        try:
            bracket = json.loads(text)
        except json.JSONDecodeError:
            parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
            if len(parts) >= 2:
                return float(parts[0]), float(parts[1])
            raise ValueError("bracket must contain at least two values")

    def _flatten(value):
        out = []
        if isinstance(value, (list, tuple)):
            for item in value:
                out.extend(_flatten(item))
        elif value is not None and value != "":
            out.append(value)
        return out

    if isinstance(bracket, (list, tuple)):
        flat = _flatten(bracket)
        if len(flat) < 2:
            raise ValueError("bracket must contain at least two values")
        start, end = float(flat[0]), float(flat[1])
        if start >= end:
            raise ValueError("bracket range invalid: start must be less than end")
        return start, end

    raise ValueError("bracket must be a list or tuple")


def _build_sdp_from_context(ctx):
    """从 McpStructuredDerivativeProduct 保存的上下文重建实例（供 DeltaPlot 扫参）。"""
    add_var_json = json.dumps(ctx.get("additional_variable_values") or {})
    add_date_json = json.dumps(ctx.get("additional_date_values") or {})
    add_str_json = json.dumps(ctx.get("additional_string_values") or {})

    if ctx.get("use_volatility"):
        discount_curve_for_vol = _normalize_discount_curve_for_vol_ctor(ctx["discount_curve"])
        return mcp.mcp.MStructuredDerivativeProduct(
            ctx["product_name"],
            ctx["reference_date"],
            ctx["start_date"],
            ctx["expiry_date"],
            ctx["end_date"],
            float(ctx["initial_price"]),
            float(ctx["notional"]),
            float(ctx["volatility"]),
            int(ctx["model_type"]),
            float(ctx.get("underlying_rate") or 0.0),
            ctx["calendar"],
            discount_curve_for_vol,
            float(ctx.get("discount_rate") or 0.0),
            int(ctx.get("day_counter") or 0),
            int(ctx.get("asset_class") or 2),
            int(ctx["buy_sell"]),
            int(ctx["num_simulation"]),
            add_var_json,
            add_date_json,
            add_str_json,
            int(ctx["log_level"]),
        )

    local_vol = ctx["local_vol"]
    local_vol_handler = local_vol.getHandler() if hasattr(local_vol, "getHandler") else local_vol
    calendar = ctx["calendar"]
    calendar_handler = calendar.getHandler() if hasattr(calendar, "getHandler") else calendar
    discount_curve = ctx["discount_curve"]
    discount_curve_handler = (
        discount_curve.getHandler() if hasattr(discount_curve, "getHandler") else discount_curve
    )

    sdp = mcp.mcp.MStructuredDerivativeProduct(
        ctx["product_name"],
        ctx["reference_date"],
        ctx["start_date"],
        ctx["expiry_date"],
        ctx["end_date"],
        float(ctx["notional"]),
        local_vol_handler,
        float(ctx["initial_price"]),
        calendar_handler,
        discount_curve_handler,
        int(ctx["buy_sell"]),
        int(ctx["num_simulation"]),
        add_var_json,
        add_date_json,
        add_str_json,
        int(ctx["log_level"]),
        int(ctx.get("day_counter") or 0),
        int(ctx.get("asset_class") or 2),
    )
    if ctx.get("config_path"):
        sdp._config_path = ctx["config_path"]
    return sdp


def _clone_sdp_context(ctx):
    """浅拷贝 SDP 上下文（保留 LocalVol/Calendar 等对象引用）。"""
    return {
        **ctx,
        "additional_variable_values": dict(ctx.get("additional_variable_values") or {}),
        "additional_date_values": dict(ctx.get("additional_date_values") or {}),
        "additional_string_values": dict(ctx.get("additional_string_values") or {}),
    }


def _apply_sdp_target_field(ctx, target_field, value):
    """复制上下文并写入扫参目标字段。"""
    new_ctx = _clone_sdp_context(ctx)
    key_norm = str(target_field).replace("_", "").lower()
    if key_norm in ("initialprice", "spot"):
        new_ctx["initial_price"] = float(value)
        return new_ctx

    add_vars = dict(new_ctx.get("additional_variable_values") or {})
    for k in list(add_vars.keys()):
        if str(k).replace("_", "").lower() == key_norm:
            add_vars[k] = float(value)
            new_ctx["additional_variable_values"] = add_vars
            return new_ctx

    raise ValueError(
        f"SDP DeltaPlot: targetField '{target_field}' not found in creation context "
        f"(supported: InitialPrice/Spot or additional float fields)."
    )


def _sdp_delta_at(sdp_obj, is_amount=True):
    if hasattr(sdp_obj, "EquityDelta"):
        try:
            return sdp_obj.EquityDelta(is_amount)
        except Exception:
            pass
    return sdp_obj.Delta(is_amount)


def _sdp_delta_plot(price_obj, target_field, bracket, num_points, is_amount=True):
    ctx = getattr(price_obj, "_sdp_creation_context", None)
    if ctx is None:
        raise AttributeError(
            "MStructuredDerivativeProduct has no _sdp_creation_context; "
            "please recreate via McpStructuredDerivativeProduct()."
        )

    num_points = int(num_points)
    if num_points <= 0:
        raise ValueError("num_points must be a positive integer")

    start, end = _normalize_bracket(bracket)

    step = (end - start) / (num_points - 1) if num_points > 1 else 0.0
    x_values = []
    y_values = []
    for i in range(num_points):
        x = start + i * step
        x_values.append(x)
        bumped_ctx = _apply_sdp_target_field(ctx, target_field, x)
        new_sdp = _build_sdp_from_context(bumped_ctx)
        y_values.append(_sdp_delta_at(new_sdp, is_amount))
    return x_values, y_values


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("priceObj", "object")
@xl_arg("targetField", "str")
@xl_arg("bracket", "var")
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
    支持 McpXScriptStructure（Solver）与 MStructuredDerivativeProduct（SDP 扫参重建）。
    """
    if not isinstance(targetField, str):
        raise ValueError("targetField not valid!")
    bracket_pair = _normalize_bracket(bracket)
    if hasattr(priceObj, "_sdp_creation_context"):
        result = _sdp_delta_plot(priceObj, targetField, bracket_pair, num_points, isAmount)
    elif hasattr(priceObj, "get_rawargs"):
        rf = xsst.Solver(priceObj)
        result = rf.DeltaPlot(targetField, bracket_pair, num_points, isCCY2, isAmount)
    else:
        raise AttributeError(
            f"{type(priceObj).__name__} does not support xssDeltaPlot "
            "(need get_rawargs or _sdp_creation_context)."
        )
    array_data = np.array(result)
    transposed = array_data.transpose()
    return transposed


def _resolve_sdp_mc_spot(initial_price, additional_variable_values):
    """MC 模拟起点：优先 ValuationSpot（估值日市价），与 MVE ProductFactory 一致。"""
    if additional_variable_values:
        for key, val in additional_variable_values.items():
            if key.lower() == "valuationspot":
                try:
                    spot = float(val)
                except (TypeError, ValueError):
                    continue
                if spot > 0 and math.isfinite(spot):
                    return spot
    try:
        base = float(initial_price)
    except (TypeError, ValueError):
        return initial_price
    return base


@xl_func(macro=True, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpStructuredDerivativeProduct(args1, args2, args3, args4, args5, fmt='VP|HD'):
    """
    创建MStructuredDerivativeProduct实例
    
    固定参数：
    - ProductName: 产品名称
    - ReferenceDate: 参考日期
    - StartDate: 开始日期
    - ExpiryDate: 到期日期
    - EndDate: 结束日期
    - Notional: 名义本金
    - LocalVol 或 Volatility: 二选一
      * LocalVol: 局部波动率对象（如果提供，使用 LocalVol 构造）
      * Volatility: 可以是以下两种类型之一：
        - float 类型的直接波动率数值（如果提供，使用 double volatility 构造，需要配合 ModelType）
        - LocalVol 对象（如果提供，使用 LocalVol 构造）
    - ModelType: 模型类型（可选，缺省=1，BlackScholes），仅在提供 float 类型的 Volatility 时使用
    - UnderlyingRate: 标的资产利率（可选，缺省=0.0，股指为dividend，商品为仓储费）
    - DiscountRate: 折现率（可选，缺省=0.0）
    - DayCounter: 日计数规则（可选，缺省="Act365Fixed"，与 MVE SDP 一致）
    - InitialPrice: 初始价格
    - Calendar: 日历对象
    - DiscountCurve: 贴现曲线对象
    - BuySell: 买卖方向 (Buy/Sell 或 1/-1)
    - NumSimulation: 模拟次数
    
    其他参数会根据MStructuredDerivativeProductDef的字段类型自动分类到：
    - additionalVariableValues: 浮点数类型参数
    - additionalDateValues: 日期类型参数
    - additionalStringValues: 字符串类型参数
    """
    args = [args1, args2, args3, args4, args5]
    
    # 定义固定参数字段
    # 注意：Spot 和 DiscountRateCurve 是同义词，会在解析后映射到 InitialPrice 和 DiscountCurve
    # LocalVol 和 Volatility 二选一：如果提供了 Volatility，则使用 double volatility 构造；否则使用 LocalVol 构造
    fixed_data_fields = [
        ("PackageName", "str"),
        ("ReferenceDate", "date"),
        ("StartDate", "date"),
        ("ExpiryDate", "date"),
        ("EndDate", "date"),
        ("Notional", "float"),
        ("LocalVol", "object"),
        ("Volatility", "float"),  # 可选：如果提供，则使用 double volatility 构造
        ("ModelType", "const"),  # 可选：模型类型，缺省=1 (BlackScholes)
        ("InitialPrice", "float"),
        ("Spot", "float"),  # 同义词：对应到 InitialPrice
        ("UnderlyingRate", "float"),  # 可选：标的资产利率（股指为dividend，商品为仓储费），缺省=0.0
        ("DiscountRate", "float"),  # 可选：折现率，缺省=0.0
        ("DayCounter", "str"),  # 可选：日计数规则，缺省="Act365Fixed"
        ("AssetClass", "str"),  # 可选：资产类别，缺省="Equity"
        ("Calendar", "object"),
        ("DiscountCurve", "object"),
        ("DiscountRateCurve", "object"),  # 同义词：对应到 DiscountCurve
        ("BuySell", "const"),
        ("NumSimulation", "int"),
        ("ConfigPath", "str"),  # 可选：配置文件路径
        ("LogLevel", "const"),  # 可选：日志级别，使用LogLevel枚举
        ("FixingDates", "date"),   # 可选：历史 fixing 日期列表
        ("FixingRates", "float"),  # 可选：历史 fixing 价格列表（与 FixingDates 一一对应）
    ]
    
    try:
        # 解析所有参数
        d = mcp_kv_wrapper.args_parser.parse_all(args, fmt, fixed_data_fields, True)
        d = {k.lower(): v for k, v in d.items()}
        
        # 处理同义词映射
        # Spot -> InitialPrice
        if 'spot' in d and 'initialprice' not in d:
            d['initialprice'] = d['spot']
        elif 'spot' in d and 'initialprice' in d:
            # 如果两个都存在，优先使用 InitialPrice，但也可以选择使用 Spot
            # 这里我们优先使用 InitialPrice，忽略 Spot
            pass
        
        # DiscountRateCurve -> DiscountCurve
        if 'discountratecurve' in d and 'discountcurve' not in d:
            d['discountcurve'] = d['discountratecurve']
        elif 'discountratecurve' in d and 'discountcurve' in d:
            # 如果两个都存在，优先使用 DiscountCurve，忽略 DiscountRateCurve
            pass
        
        # 提取固定参数
        product_name = d.get('packagename')
        if not product_name:
            return "Missing required field: PackageName"
        
        reference_date = d.get('referencedate')
        start_date = d.get('startdate')
        expiry_date = d.get('expirydate')
        end_date = d.get('enddate')
        notional = d.get('notional')
        local_vol = d.get('localvol')
        volatility = d.get('volatility')  # 可选：如果提供，则使用 double volatility 构造
        model_type = d.get('modeltype')  # 可选：模型类型，缺省=1 (BlackScholes)
        if model_type is None:
            model_type = 1  # 缺省值：BlackScholes
        initial_price = d.get('initialprice')
        underlying_rate = d.get('underlyingrate')  # 可选：标的资产利率（股指为dividend，商品为仓储费）
        if underlying_rate is None:
            underlying_rate = 0.0  # 缺省值：0.0
        else:
            try:
                underlying_rate = float(underlying_rate)
            except (ValueError, TypeError):
                underlying_rate = 0.0
        
        discount_rate = d.get('discountrate')  # 可选：折现率
        if discount_rate is None:
            discount_rate = 0.0  # 缺省值：0.0
        else:
            try:
                discount_rate = float(discount_rate)
            except (ValueError, TypeError):
                discount_rate = 0.0
        
        day_counter = d.get('daycounter')  # 可选：日计数规则
        # 注意：根据实际C++签名，dayCounter应该是int类型，而不是char*
        if day_counter is None:
            day_counter = 1  # 缺省值：DayCounter.Act365Fixed = 1（与 MVE ProductFactory 一致）
        elif isinstance(day_counter, str):
            try:
                day_counter = enum_wrapper.parse2(day_counter, 'DayCounter')
            except:
                day_counter = 1  # 默认 Act365Fixed
        else:
            try:
                day_counter = int(day_counter)
            except (ValueError, TypeError):
                day_counter = 1  # 默认 Act365Fixed
        
        asset_class = d.get('assetclass')  # 可选：资产类别
        if asset_class is None:
            asset_class = 2  # 缺省值：AssetClass.Equity = 2
        elif isinstance(asset_class, str):
            try:
                asset_class = enum_wrapper.parse2(asset_class, 'AssetClass')
            except:
                asset_class = 2  # 默认 Equity
        else:
            try:
                asset_class = int(asset_class)
            except (ValueError, TypeError):
                asset_class = 2  # 默认 Equity 
        calendar = d.get('calendar')
        discount_curve = d.get('discountcurve')
        buy_sell = d.get('buysell')
        num_simulation = d.get('numsimulation', 10000)
        config_path = d.get('configpath')
        log_level = d.get('loglevel')
        fixing_dates_raw = d.get('fixingdates', []) or []
        fixing_rates_raw = d.get('fixingrates', []) or []
        
        # 判断使用哪种构造方式：volatility 或 LocalVol
        # volatility 可能是 float 类型的直接波动率，也可能是 LocalVol 对象
        use_volatility_float = False
        use_volatility_localvol = False
        use_localvol = False
        
        # 检查 volatility 参数
        if volatility is not None:
            if isinstance(volatility, (int, float)):
                # volatility 是 float 类型的直接波动率值
                use_volatility_float = True
            elif hasattr(volatility, 'getHandler') or hasattr(volatility, 'GetVolatility'):
                # volatility 是 LocalVol 对象（通过检查是否有 getHandler 或 GetVolatility 方法）
                use_volatility_localvol = True
                # 将 volatility 对象赋值给 local_vol，以便后续使用
                local_vol = volatility
        
        # 检查 local_vol 参数
        if local_vol is not None:
            use_localvol = True
        
        # 验证必需参数
        required_fields = {
            'referencedate': reference_date,
            'startdate': start_date,
            'expirydate': expiry_date,
            'enddate': end_date,
            'notional': notional,
            'initialprice': initial_price,
            'calendar': calendar,
            'discountcurve': discount_curve,
            'buysell': buy_sell,
        }
        
        # LocalVol 和 Volatility（float 或 LocalVol 对象）必须提供其中一个
        if not use_volatility_float and not use_volatility_localvol and not use_localvol:
            return "Missing required field: either LocalVol or Volatility (float or LocalVol object) must be provided"
        
        # 确定最终使用的构造方式
        if use_volatility_float:
            # 使用 float volatility 构造
            use_volatility = True
            use_localvol = False
        elif use_volatility_localvol or use_localvol:
            # 使用 LocalVol 构造
            use_volatility = False
            use_localvol = True
            # 确保 local_vol 有值
            if use_volatility_localvol:
                # volatility 已经是 LocalVol 对象，已经在上面赋值给 local_vol
                pass
            elif not local_vol:
                return "LocalVol object is required but not provided"
        
        missing_fields = [k for k, v in required_fields.items() if v is None]
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"
        
        # 处理 ModelType（仅在 use_volatility 时使用）
        if use_volatility:
            if model_type is None:
                model_type = 1  # 缺省值：ModelType.BlackSchole = 1
            elif isinstance(model_type, str):
                try:
                    # 尝试解析为枚举
                    model_type = enum_wrapper.parse2(model_type, 'ModelType')
                except:
                    # 如果解析失败，尝试作为数字
                    try:
                        model_type = int(model_type)
                    except (ValueError, TypeError):
                        model_type = 1  # 默认 BlackSchole
            else:
                try:
                    model_type = int(model_type)
                except (ValueError, TypeError):
                    model_type = 1  # 默认 BlackSchole
        
        # 处理BuySell枚举
        if isinstance(buy_sell, str):
            buy_sell = enum_wrapper.parse2(buy_sell, 'BuySell')
        elif buy_sell is None:
            buy_sell = -1  # 默认Sell
        
        # 处理LogLevel枚举
        if log_level is None:
            log_level = 4  # 默认Error
        elif isinstance(log_level, str):
            try:
                log_level = enum_wrapper.parse2(log_level, 'LogLevel')
            except:
                # 如果解析失败，尝试作为数字
                try:
                    log_level = int(log_level)
                except:
                    log_level = 4  # 默认Error
        elif isinstance(log_level, (int, float)):
            log_level = int(log_level)
        else:
            log_level = 4  # 默认Error
        
        # 获取配置文件路径
        if not config_path:
            # 尝试从环境变量或默认路径获取
            mcp_path = os.environ.get('MCP_PATH')
            if mcp_path:
                config_base_path = os.path.join(mcp_path, 'config', 'structured_products')
            else:
                # 使用默认路径（需要根据实际情况调整）
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
                config_base_path = os.path.join(
                    project_root,
                    "config/structured_products"
                )
            config_path = os.path.join(config_base_path, f"{product_name.lower()}.yaml")

        ok_cfg, resolved_cfg, err_cfg = resolve_data_path(config_path, must_exist=True)
        if ok_cfg:
            config_path = resolved_cfg
        elif not os.path.exists(config_path):
            return err_cfg or f"Product definition file not found: {config_path}"
        
        if not os.path.exists(config_path):
            return f"Product definition file not found: {config_path}"
        
        # 创建产品定义以获取字段类型信息
        product_def = mcp.mcp.MStructuredDerivativeProductDef(product_name, config_path)
        
        # 获取字段类型列表
        try:
            float_fields = json.loads(product_def.getFloatFields()) if hasattr(product_def, 'getFloatFields') else []
        except:
            float_fields = []
        
        try:
            date_fields = json.loads(product_def.getDateFields()) if hasattr(product_def, 'getDateFields') else []
        except:
            date_fields = []
        
        try:
            string_fields = json.loads(product_def.getStringFields()) if hasattr(product_def, 'getStringFields') else []
        except:
            string_fields = []

        # 转换为小写集合以便快速查找
        float_fields_set = {f.lower() for f in float_fields}
        date_fields_set = {f.lower() for f in date_fields}
        string_fields_set = {f.lower() for f in string_fields}
        
        # 分类其他参数到三个字典
        additional_variable_values = {}
        additional_date_values = {}
        additional_string_values = {}
        
        # 固定参数字段名（不包含在additional中）
        # 包括同义词：Spot -> InitialPrice, DiscountRateCurve -> DiscountCurve
        fixed_field_names = {
            'packagename', 'referencedate', 'startdate', 'expirydate', 'enddate',
            'notional', 'localvol', 'volatility', 'modeltype',  # volatility 和 modeltype 是固定参数
            'initialprice', 'spot',  # spot 是同义词
            'underlyingrate', 'discountrate', 'daycounter',  # 新增参数
            'calendar', 'discountcurve', 'discountratecurve',  # discountratecurve 是同义词
            'buysell', 'numsimulation', 'configpath', 'loglevel',
            'fixingdates', 'fixingrates',  # 历史 fixing（单独序列化为 additionalStringValues）
        }
        
        # 遍历所有参数，分类到对应的字典
        for key, value in d.items():
            if key.lower() in fixed_field_names:
                continue  # 跳过固定参数
            
            key_lower = key.lower()

            # 显式观察日列表：统一为 JSON 日期数组字符串，且固定写入 additionalStringValues（不进 additionalDateValues）
            if key_lower.endswith('/dates'):
                try:
                    norm = normalize_sdp_schedule_dates_json(value)
                except ValueError as e:
                    return f"Invalid schedule dates field '{key}': {e}"
                if norm is not None:
                    additional_string_values[key] = norm
                continue

            # 根据字段类型分类
            if key_lower in float_fields_set:
                # 浮点数类型
                try:
                    additional_variable_values[key] = float(value)
                except (ValueError, TypeError):
                    return f"Invalid float value for field '{key}': {value}"
            elif key_lower in date_fields_set:
                # 日期类型 - 转换为YYYYMMDD格式
                try:
                    if isinstance(value, str):
                        # 如果是字符串，尝试解析
                        if '-' in value:
                            date_str = value.replace('-', '')
                        else:
                            date_str = value
                    else:
                        # 如果是Excel日期数字，转换为日期字符串
                        # pf_date 返回的是字符串格式的日期（如 '2025-12-01'），不是日期对象
                        date_result = pf_date(value)
                        if isinstance(date_result, str):
                            # 如果返回的是字符串，直接处理
                            if '-' in date_result:
                                date_str = date_result.replace('-', '')
                            else:
                                date_str = date_result
                        else:
                            # 如果返回的是日期对象，使用strftime格式化
                            date_str = date_result.strftime('%Y%m%d')
                    additional_date_values[key] = date_str
                except Exception as e:
                    return f"Invalid date value for field '{key}': {value}, error: {e}"
            elif key_lower in string_fields_set:
                # 字符串类型
                additional_string_values[key] = str(value)
            else:
                # 如果不在任何类型列表中，尝试根据值类型推断
                if isinstance(value, (int, float)):
                    additional_variable_values[key] = float(value)
                elif isinstance(value, str):
                    # 尝试判断是否为日期格式
                    try:
                        if '-' in value and len(value) >= 8:
                            # 可能是日期
                            date_str = value.replace('-', '')
                            additional_date_values[key] = date_str
                        else:
                            additional_string_values[key] = value
                    except:
                        additional_string_values[key] = value
                else:
                    # 默认作为字符串
                    additional_string_values[key] = str(value)
        
        # 将历史 fixing 序列化为 JSON 并注入 additionalStringValues
        # C++ StructuredDerivativeProduct 构造函数从此处读取 FixingDates/FixingRates
        # 注意：VP 格式下 fixing_dates_raw / fixing_rates_raw 是 JSON 字符串（McpList 产出），
        # 需要用 normalize_sdp_schedule_dates_json 转换 Excel 序列日期；
        # HD/DT 格式下是 Python list，走原有路径。
        if fixing_dates_raw:
            if isinstance(fixing_dates_raw, str):
                additional_string_values['FixingDates'] = normalize_sdp_schedule_dates_json(fixing_dates_raw)
            else:
                additional_string_values['FixingDates'] = pf_array_date_json(fixing_dates_raw)
        if fixing_rates_raw:
            if isinstance(fixing_rates_raw, str):
                try:
                    json.loads(fixing_rates_raw)
                    additional_string_values['FixingRates'] = fixing_rates_raw
                except json.JSONDecodeError:
                    additional_string_values['FixingRates'] = pf_array_json([fixing_rates_raw])
            else:
                additional_string_values['FixingRates'] = pf_array_json(fixing_rates_raw)

        # 转换为JSON字符串
        additional_variable_values_json = json.dumps(additional_variable_values) if additional_variable_values else "{}"
        additional_date_values_json = json.dumps(additional_date_values) if additional_date_values else "{}"
        additional_string_values_json = json.dumps(additional_string_values) if additional_string_values else "{}"
        
        # 获取handler - Calendar, DiscountCurve 需要调用getHandler()
        # LocalVol 只在 use_localvol 为 True 时需要
        try:
            calendar_handler = calendar.getHandler()
        except AttributeError:
            return f"Calendar object does not have getHandler() method: {type(calendar).__name__}"
        
        try:
            discount_curve_handler = discount_curve.getHandler()
        except AttributeError:
            return f"DiscountCurve object does not have getHandler() method: {type(discount_curve).__name__}"
        
        # 如果使用 LocalVol 构造，获取 LocalVol handler
        if use_localvol:
            try:
                local_vol_handler = local_vol.getHandler()
            except AttributeError:
                return f"LocalVol object does not have getHandler() method: {type(local_vol).__name__}"
        
        # 确保日期格式正确（转换为字符串格式 YYYY-MM-DD）
        # pf_date 返回的是字符串格式的日期（如 '2025-12-01'），不是日期对象
        def normalize_date(date_val):
            """统一日期格式为 YYYY-MM-DD"""
            if isinstance(date_val, str):
                # 如果已经是字符串，统一格式
                # 处理 MM/DD/YYYY 或 YYYY/MM/DD 格式
                if '/' in date_val:
                    parts = date_val.split('/')
                    if len(parts) == 3:
                        # 判断是 MM/DD/YYYY 还是 YYYY/MM/DD
                        if len(parts[0]) == 4:  # YYYY/MM/DD
                            return f"{parts[0]}-{parts[1]}-{parts[2]}"
                        else:  # MM/DD/YYYY
                            return f"{parts[2]}-{parts[0]}-{parts[1]}"
                # 如果已经是 YYYY-MM-DD 格式，直接返回
                if '-' in date_val and len(date_val) >= 10:
                    return date_val
                return date_val
            else:
                date_result = pf_date(date_val)
                if isinstance(date_result, str):
                    # 统一格式为 YYYY-MM-DD
                    if '/' in date_result:
                        parts = date_result.split('/')
                        if len(parts) == 3:
                            if len(parts[0]) == 4:  # YYYY/MM/DD
                                return f"{parts[0]}-{parts[1]}-{parts[2]}"
                            else:  # MM/DD/YYYY
                                return f"{parts[2]}-{parts[0]}-{parts[1]}"
                    return date_result
                else:
                    return date_result.strftime('%Y-%m-%d')
        
        ref_date = normalize_date(reference_date)
        start_dt = normalize_date(start_date)
        expiry_dt = normalize_date(expiry_date)
        end_dt = normalize_date(end_date)

        mc_spot = _resolve_sdp_mc_spot(initial_price, additional_variable_values)

        sdp_creation_context = {
            "product_name": product_name,
            "reference_date": ref_date,
            "start_date": start_dt,
            "expiry_date": expiry_dt,
            "end_date": end_dt,
            "notional": float(notional),
            "initial_price": float(mc_spot),
            "observation_initial_price": float(initial_price),
            "calendar": calendar,
            "discount_curve": discount_curve,
            "buy_sell": int(buy_sell),
            "num_simulation": int(num_simulation),
            "additional_variable_values": dict(additional_variable_values),
            "additional_date_values": dict(additional_date_values),
            "additional_string_values": dict(additional_string_values),
            "log_level": int(log_level),
            "day_counter": int(day_counter) if day_counter is not None else 0,
            "asset_class": int(asset_class) if asset_class is not None else 2,
            "config_path": config_path,
            "use_localvol": use_localvol,
            "use_volatility": use_volatility,
            "volatility": float(volatility) if use_volatility and volatility is not None else None,
            "model_type": int(model_type) if use_volatility and model_type is not None else None,
            "underlying_rate": float(underlying_rate) if underlying_rate is not None else 0.0,
            "discount_rate": float(discount_rate) if discount_rate is not None else 0.0,
            "local_vol": local_vol if use_localvol else None,
        }

        # 对 volatility(float) 构造分支，C++ 重载要求 MCalendar* + MYieldCurve*。
        # Excel 里 DiscountCurve 可能是 McpYieldCurve / McpSwapCurve / McpBondCurve，
        # 这里统一尝试归一到 MYieldCurve，避免 SWIG 重载匹配失败。
        def normalize_discount_curve_for_vol_ctor(curve_obj):
            if curve_obj is None:
                return None
            if isinstance(curve_obj, mcp.mcp.MYieldCurve):
                return curve_obj
            if hasattr(curve_obj, "getHandler"):
                try:
                    return mcp.mcp.MYieldCurve(curve_obj.getHandler())
                except Exception:
                    return curve_obj
            return curve_obj
        
        # 创建MStructuredDerivativeProduct实例
        # 根据是否提供了 volatility 选择不同的构造函数
        if use_volatility:
            discount_curve_for_vol = normalize_discount_curve_for_vol_ctor(discount_curve)
            # 使用 product_def（含 Excel ConfigPath 解析结果），勿用 product_name 触发 findProductConfigFile
            structured_product = mcp.mcp.MStructuredDerivativeProduct(
                product_def,  # MStructuredDerivativeProductDef*（Constructor 4 M-type）
                ref_date,
                start_dt,
                expiry_dt,
                end_dt,
                float(mc_spot),
                float(notional),
                float(volatility),
                int(model_type),
                float(underlying_rate),
                calendar,
                discount_curve_for_vol,
                float(discount_rate),
                int(day_counter),
                int(asset_class),
                int(buy_sell),
                int(num_simulation),
                additional_variable_values_json,
                additional_date_values_json,
                additional_string_values_json,
                int(log_level),
            )
        else:
            # 使用 product_def（含 Excel ConfigPath 解析结果），勿用 product_name 触发 findProductConfigFile
            structured_product = mcp.mcp.MStructuredDerivativeProduct(
                product_def,  # MStructuredDerivativeProductDef* / void* productDef（Constructor 2）
                ref_date,
                start_dt,
                expiry_dt,
                end_dt,
                float(notional),
                local_vol_handler,
                float(mc_spot),
                calendar_handler,
                discount_curve_handler,
                int(buy_sell),
                int(num_simulation),
                additional_variable_values_json,
                additional_date_values_json,
                additional_string_values_json,
                int(log_level),
                int(day_counter),
                int(asset_class),
            )
        
        # 将配置路径保存为对象属性，以便后续获取
        structured_product._config_path = config_path
        structured_product._sdp_creation_context = sdp_creation_context
        
        # 直接返回MStructuredDerivativeProduct对象
        # 注意：C++端的StructuredDerivativeProduct需要实现所有XScriptStructure的方法
        # 这样MStructuredDerivativeProduct就可以直接使用xssXXX函数
        return structured_product
        
    except Exception as e:
        s = f"McpStructuredDerivativeProduct except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s