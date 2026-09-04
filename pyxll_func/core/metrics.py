# -*- coding: utf-8 -*-
"""
MCP 指标计算模块：所有 Adapter 及指标计算

定位：适用于所有资产类型（VanillaSwap、XCurrencySwap、Bond、FXOptions 等）的
估值与风险指标计算，提供纯 Python 接口及 PyXLL Excel UDF。

函数：
  - 通用：mcpNPV, mcpVAR, mcpES, mcpEE, mcpPFE, mcpCVA, mcpDFE
  - 通用 Adapter 指标：adapterMetric, adapterMetrics, adapterMetricsByCategory, adapterMetricMeta, bondAdapterSetPreviousCurve
  - 一站式：mcpVanillaSwapAdapterFull, mcpBuildCreditCurve
  - 别名：SwapNPV, SwapVaR, SwapES, SwapEE, SwapPFE, SwapCVA, SwapDFE（向后兼容）

PyXLL 配置：在 pyxll.cfg 的 [modules] 中加入 metrics
"""

from __future__ import absolute_import

try:
    from pyxll import xl_func
except ImportError:
    def xl_func(*args, **kwargs):
        def decorator(f):
            return f
        return decorator if not args else decorator(args[0])


def _get_mcp():
    """获取 mcp 模块，兼容多种导入路径"""
    for mod_name in ('mcp', 'mcp.mcp', 'mcpPortLib'):
        try:
            import importlib
            return importlib.import_module(mod_name)
        except ImportError:
            continue
    return None


def _build_credit_curve_safe(reference_date, yield_curve):
    """安全构建信用曲线，失败返回 None"""
    import sys
    import os
    # 尝试将 market_data_builders 所在目录加入路径
    _dir = os.path.dirname(os.path.abspath(__file__))
    for base in (_dir, os.path.join(_dir, ".."), os.path.join(_dir, "..", ".."), r"C:\mcp\mcpexcel1.4\python"):
        base = os.path.normpath(base) if base else ""
        if base and os.path.isdir(base) and base not in sys.path:
            sys.path.insert(0, base)
    try:
        from market_data_builders import build_credit_curve
        return build_credit_curve(reference_date, yield_curve)
    except Exception:
        return None


# Metric ID 映射（兼容 metrics_types.h 与 metric_enums）
_METRIC_IDS = {
    "CVA": (47, 142), "DFE": (143,), "EE": (167,), "PFE": (66, 166),
    "VAR": (64, 164), "ES": (65, 165)
}

# 蒙卡指标缓存：同一 adapter 的 VaR/ES 共用 calculateRiskMetrics，EE/PFE/DFE 共用 calculateCreditRiskMetrics
# 避免 Excel 多单元格重复调用导致多次蒙卡计算
_METRICS_CACHE_MAX = 32
_risk_metrics_cache = {}
_credit_risk_metrics_cache = {}


def _maybe_clear_metrics_cache():
    """缓存过大时清空，避免内存增长"""
    if len(_risk_metrics_cache) >= _METRICS_CACHE_MAX or len(_credit_risk_metrics_cache) >= _METRICS_CACHE_MAX:
        _risk_metrics_cache.clear()
        _credit_risk_metrics_cache.clear()


def _get_cached_risk_metrics(adapter):
    """获取或计算 RiskMetrics，带缓存（VaR/ES 共用，避免重复蒙卡）"""
    if adapter is None:
        return []
    tid = id(adapter)
    if tid not in _risk_metrics_cache:
        _maybe_clear_metrics_cache()
        _risk_metrics_cache[tid] = _safe_call(adapter, "calculateRiskMetrics", [])
    return _risk_metrics_cache.get(tid) or []


def _get_cached_credit_risk_metrics(adapter):
    """获取或计算 CreditRiskMetrics，带缓存（EE/PFE/DFE/CVA 共用，避免重复蒙卡）"""
    if adapter is None:
        return []
    tid = id(adapter)
    if tid not in _credit_risk_metrics_cache:
        _maybe_clear_metrics_cache()
        _credit_risk_metrics_cache[tid] = _safe_call(adapter, "calculateCreditRiskMetrics", [])
    return _credit_risk_metrics_cache.get(tid) or []


def _get_metric_value(metrics, metric_names, horizon=None, confidence=None):
    """从 metrics 中提取指标，可选按 horizon 过滤"""
    if not metrics:
        return None
    candidates = []
    for m in metrics:
        try:
            mid = getattr(m, 'metric_', getattr(m, 'metric', None))
            matched = False
            for name in metric_names:
                ids = _METRIC_IDS.get(name, ())
                if mid in (ids if isinstance(ids, tuple) else (ids,)):
                    bucket = getattr(m.bucket_spec, 'bucket_value', None) or getattr(
                        getattr(m, 'bucket_spec', None), 'bucket_value', None) or ""
                    if horizon and bucket and str(bucket).upper() != str(horizon).upper():
                        continue
                    candidates.append((m.value, bucket))
                    matched = True
                    break
            # 兼容：若 result 有 metric_name 属性
            if not matched:
                mname = getattr(m, 'metric_name', None) or getattr(m, 'name', None)
                if mname and str(mname) in metric_names:
                    candidates.append((m.value, ""))
        except Exception:
            pass
    if not candidates:
        return None
    # 若有多个，取第一个匹配 horizon 的，否则取第一个
    for v, b in candidates:
        if horizon and b and str(b).upper() == str(horizon).upper():
            return v
    return candidates[0][0]


def _safe_call(adapter, method_name, default=None):
    """安全调用 adapter 方法"""
    if adapter is None:
        return default
    try:
        m = getattr(adapter, method_name, None)
        if m and callable(m):
            try:
                return m()
            except Exception:
                return default
    except Exception:
        return default
    return default


def _is_adapter(obj):
    """判断是否为 Adapter（有 calculateValuationMetrics 方法）"""
    if obj is None:
        return False
    try:
        m = getattr(obj, "calculateValuationMetrics", None)
        return m is not None and callable(m)
    except Exception:
        return False


def _swap_npv_fallback(obj):
    """
    对 raw Swap 对象（如 McpXcurrencySwap）的 NPV 回退。
    McpXcurrencySwap 有 NPV(isResultTermCurrency) 方法，需传入 True/False。
    """
    if obj is None:
        return None
    try:
        npv_fn = getattr(obj, "NPV", None)
        if npv_fn and callable(npv_fn):
            # MXCurrencySwap.NPV(isResultTermCurrency): True=Term 货币, False=Base 货币
            try:
                return float(npv_fn(True))
            except TypeError:
                return float(npv_fn())
    except Exception:
        pass
    return None


# ==================== 纯 Python 接口（无 PyXLL 依赖） ====================

def calculate_npv(adapter):
    """
    估值，适用于 Adapter 或 raw Swap 对象。
    - Adapter（XCurrencySwapAdapter、VanillaSwapAdapter 等）：调用 calculateValuationMetrics
    - raw Swap（McpXcurrencySwap、McpVanillaSwap 等）：回退调用 NPV(True)
    注意：raw Swap 需已设置估值曲线，否则 NPV 可能失败或崩溃。
    """
    if adapter is None:
        return None
    # 优先使用 Adapter 接口
    if _is_adapter(adapter):
        val = _safe_call(adapter, "calculateValuationMetrics")
        try:
            if val and len(val) > 0:
                return getattr(val[0], "value", None)
        except (IndexError, TypeError, AttributeError):
            pass
    # 回退：raw Swap 对象（如 McpXcurrencySwap）直接调用 NPV
    return _swap_npv_fallback(adapter)


def calculate_var(adapter, horizon=None, confidence=None):
    """风险价值。horizon 如 1D/10D/1M/3M/1Y，confidence 如 0.95"""
    h = horizon or "1Y"
    metrics = _get_cached_risk_metrics(adapter)
    return _get_metric_value(metrics, ["VAR"], horizon=h) if metrics else None


def calculate_es(adapter, horizon=None, confidence=None):
    """预期短缺"""
    metrics = _get_cached_risk_metrics(adapter)
    val = _get_metric_value(metrics, ["ES"], horizon=horizon or "1Y") if metrics else None
    return val


def calculate_ee(adapter, horizon=None):
    """预期敞口"""
    metrics = _get_cached_credit_risk_metrics(adapter)
    return _get_metric_value(metrics, ["EE"], horizon=horizon or "1Y") if metrics else None


def calculate_pfe(adapter, horizon=None, confidence=None):
    """潜在未来敞口"""
    metrics = _get_cached_credit_risk_metrics(adapter)
    val = _get_metric_value(metrics, ["PFE"], horizon=horizon or "1Y") if metrics else None
    return val


def calculate_cva(adapter, credit_curve=None, recovery_rate=None, pd=None, lgd=None):
    """
    信用估值调整。推荐在方法中传入参数，而非 adapter 上设置。
    - credit_curve + recovery_rate: 使用信用曲线计算
    - pd + lgd: 简化公式 CVA = LGD × PD × max(NPV, 0)
    - 无参数: 使用 adapter 上已设置的 credit_curve（向后兼容）
    """
    if credit_curve is not None and credit_curve != "" and recovery_rate is not None and recovery_rate != "":
        try:
            rr = float(recovery_rate)
            if hasattr(adapter, "calculateCVA"):
                return adapter.calculateCVA(credit_curve, rr)
        except Exception:
            pass
    if pd is not None and pd != "" and lgd is not None and lgd != "":
        try:
            p, g = float(pd), float(lgd)
            if hasattr(adapter, "calculateCVAWithPDLGD"):
                return adapter.calculateCVAWithPDLGD(p, g)
            npv = calculate_npv(adapter)
            return g * p * (max(npv, 0) if npv is not None else 0)
        except Exception:
            pass
    metrics = _get_cached_credit_risk_metrics(adapter)
    return _get_metric_value(metrics, ["CVA"]) if metrics else None


def calculate_dfe(adapter):
    """债务估值调整"""
    metrics = _get_cached_credit_risk_metrics(adapter)
    val = _get_metric_value(metrics, ["DFE"]) if metrics else None
    return val


# ==================== 一站式 Adapter 创建（方案 B） ====================

@xl_func(
    "object swap, object curve, string instrument_id, string trade_id, "
    "int num_simulations: object",
    category="MCP", name="mcpVanillaSwapAdapterFull"
)
def mcp_vanilla_swap_adapter_full(
    swap, curve,
    instrument_id="STD_SWAP_001", trade_id="TRADE_001",
    num_simulations=1000
):
    """
    一站式创建已配置的 VanillaSwap Adapter（估值曲线、PFE 计算器）。
    信用曲线、PD、LGD 等请通过 mcpCVA(adapter, credit_curve, recovery_rate) 或 mcpCVA(adapter, pd, lgd) 传入。

    参数：
      swap: McpVanillaSwap 或 MVanillaSwap 对象
      curve: McpYieldCurve 或 MYieldCurve（估值曲线）
      instrument_id, trade_id: 标识
      num_simulations: PFE 模拟次数，默认 1000
    """
    if swap is None:
        return None
    mcp = _get_mcp()
    if mcp is None:
        return None
    try:
        # 创建 adapter
        if hasattr(mcp, 'MVanillaSwapAdapter'):
            adapter = mcp.MVanillaSwapAdapter(swap, instrument_id, trade_id)
        elif hasattr(mcp, 'CreateVanillaSwapAdapter'):
            handler = swap.getHandler() if hasattr(swap, 'getHandler') else swap
            adapter = mcp.CreateVanillaSwapAdapter(handler, instrument_id, trade_id)
        else:
            return None

        # 设置估值曲线
        if curve is not None:
            try:
                adapter.setValuationCurve(curve)
            except Exception:
                pass

        # 设置 PFE 计算器（VaR/ES/EE/PFE 依赖）
        SwapPFECalc = getattr(getattr(mcp, 'metrics', None), 'SwapPFECalculator', None) or getattr(mcp, 'SwapPFECalculator', None)
        if SwapPFECalc is not None and hasattr(adapter, 'setPFECalculator'):
            try:
                PFEConfig = getattr(SwapPFECalc, 'PFEConfig', None)
                if PFEConfig is not None:
                    cfg = PFEConfig()
                    cfg.num_simulations = num_simulations
                    cfg.confidence_level = 0.95
                    pfe_calc = SwapPFECalc(cfg)
                    adapter.setPFECalculator(pfe_calc)
            except (AttributeError, TypeError, Exception):
                pass

        return adapter
    except Exception:
        return None


@xl_func(
    "object swap, string instrument_id, string trade_id, int num_simulations: object",
    category="MCP", name="mcpXCurrencySwapAdapterFull"
)
def mcp_xcurrency_swap_adapter_full(
    swap,
    instrument_id="XCCY_SWAP_001", trade_id="TRADE_XCCY_001",
    num_simulations=1000
):
    """
    一站式创建已配置的 XCurrencySwap Adapter。
    swap 需为 McpXcurrencySwap（MXCurrencySwap），且创建时已通过 Leg 设置估值曲线。
    信用曲线通过 metricsCVA(adapter, credit_curve, recovery_rate) 传入。
    """
    if swap is None:
        return None
    mcp = _get_mcp()
    if mcp is None:
        return None
    try:
        if hasattr(mcp, 'CreateXCurrencySwapAdapter'):
            handler = swap.getHandler() if hasattr(swap, 'getHandler') else swap
            adapter = mcp.CreateXCurrencySwapAdapter(handler, instrument_id, trade_id, "")
        elif hasattr(mcp, 'MXCurrencySwapAdapter'):
            adapter = mcp.MXCurrencySwapAdapter(swap, instrument_id, trade_id, "")
        else:
            return None
        if hasattr(adapter, 'setResultTermCurrency'):
            try:
                adapter.setResultTermCurrency(True)
            except Exception:
                pass
        # 设置 PFE 计算器（VaR/ES/EE/PFE 依赖）
        XCCYPFECalc = getattr(getattr(mcp, 'metrics', None), 'XCCYPFECalculator', None) or getattr(mcp, 'XCCYPFECalculator', None)
        if XCCYPFECalc is not None and hasattr(adapter, 'setPFECalculator'):
            try:
                PFEConfig = getattr(XCCYPFECalc, 'PFEConfig', None)
                if PFEConfig is not None:
                    cfg = PFEConfig()
                    cfg.num_simulations = num_simulations
                    cfg.confidence_level = 0.95
                    pfe_calc = XCCYPFECalc(cfg)
                    adapter.setPFECalculator(pfe_calc)
            except (AttributeError, TypeError, Exception):
                pass
        return adapter
    except Exception:
        return None


@xl_func(
    "object loan_and_depos, object curve, string instrument_id, string trade_id, "
    "string portfolio_key, string currency: object",
    category="MCP", name="mcpLoanAndDeposAdapterFull"
)
def mcp_loan_and_depos_adapter_full(
    loan_and_depos, curve,
    instrument_id="DEPO_001", trade_id="TRADE_DEPO_001",
    portfolio_key="", currency="CNY"
):
    """
    一站式创建已配置的 LoanAndDepos Adapter（存款/拆借适配器）。

    参数：
      loan_and_depos: McpLoanAndDepos 或 MLoanAndDepos 对象
      curve: McpYieldCurve 或 MYieldCurve（估值曲线）
      instrument_id, trade_id: 标识
      portfolio_key, currency: 组合与币种
    """
    if loan_and_depos is None:
        return None
    mcp = _get_mcp()
    if mcp is None:
        return None
    try:
        if hasattr(mcp, 'MLoanAndDeposAdapter'):
            adapter = mcp.MLoanAndDeposAdapter(
                loan_and_depos, instrument_id, trade_id,
                portfolio_key or "", currency or "CNY"
            )
        else:
            return None

        if curve is not None:
            try:
                adapter.setValuationCurve(curve)
            except Exception:
                pass

        adapter._loan_and_depos_ref = loan_and_depos
        adapter._valuation_curve_ref = curve
        return adapter
    except Exception:
        return None


@xl_func(
    "string reference_date, object yield_curve: object",
    category="MCP", name="mcpBuildCreditCurve"
)
def mcp_build_credit_curve(reference_date, yield_curve):
    """
    从参考日期和无风险曲线构建信用曲线。
    reference_date 格式：YYYY-MM-DD 或 YYYY/MM/DD
    yield_curve: McpYieldCurve 或 MYieldCurve
    """
    if not reference_date or yield_curve is None:
        return None
    ref = str(reference_date).replace("/", "-")
    return _build_credit_curve_safe(ref, yield_curve)


# ==================== PyXLL Excel UDF ====================

@xl_func("object adapter: var", category="MCP", name="metricsNPV")
def metrics_npv(adapter):
    """
    metricsNPV(adapter) - 估值。
    参数需为 Adapter（如 mcpVanillaSwapAdapterFull、mcpXCurrencySwapAdapterFull 创建的对象），
    或 raw Swap（McpXcurrencySwap 等，需已设置估值曲线）。
    若传入未配置曲线的 Swap 可能崩溃，推荐使用 mcpXCurrencySwapAdapterFull 创建 Adapter。
    """
    try:
        return calculate_npv(adapter)
    except Exception:
        return None


@xl_func("object adapter, string horizon, float confidence: var",
         category="MCP", name="metricsVAR")
def metrics_var(adapter, horizon=None, confidence=None):
    """metricsVAR(adapter, horizon, confidence) - 风险价值。horizon 如 1D/10D/1M/3M/1Y，confidence 如 0.95"""
    return calculate_var(adapter, horizon, confidence)


@xl_func("object adapter, string horizon, float confidence: var",
         category="MCP", name="metricsES")
def mcp_es(adapter, horizon=None, confidence=None):
    """metricsES(adapter, horizon, confidence) - 预期短缺"""
    return calculate_es(adapter, horizon, confidence)


@xl_func("object adapter, string horizon: var", category="MCP", name="metricsEE")
def metrics_ee(adapter, horizon=None):
    """metricsEE(adapter, horizon) - 预期敞口"""
    return calculate_ee(adapter, horizon)


@xl_func("object adapter, string horizon, float confidence: var",
         category="MCP", name="metricsPFE")
def metrics_pfe(adapter, horizon=None, confidence=None):
    """metricsPFE(adapter, horizon, confidence) - 潜在未来敞口"""
    return calculate_pfe(adapter, horizon, confidence)


@xl_func(
    "object adapter, object credit_curve, float recovery_rate, float pd, float lgd: var",
    category="MCP", name="metricsCVA"
)
def metrics_cva(adapter, credit_curve=None, recovery_rate=None, pd=None, lgd=None):
    """
    metricsCVA(adapter, credit_curve, recovery_rate) 或 metricsCVA(adapter, pd, lgd)
    信用估值调整。参数传入方法，推荐方式。
    pd/lgd 时可用 metricsCVA_PDLGD(adapter, pd, lgd) 更简洁。
    """
    return calculate_cva(adapter, credit_curve, recovery_rate, pd, lgd)


@xl_func("object adapter, float pd, float lgd: var", category="MCP", name="metricsCVA_PDLGD")
def metrics_cva_pdlgd(adapter, pd, lgd):
    """metricsCVA_PDLGD(adapter, pd, lgd) - 简化 CVA，直接传入 PD 和 LGD"""
    return calculate_cva(adapter, pd=pd, lgd=lgd)


@xl_func("object adapter: var", category="MCP", name="metricsDFE")
def metrics_dfe(adapter):
    """metricsDFE(adapter) - 债务估值调整"""
    return calculate_dfe(adapter)


# ==================== 通用 Adapter 指标（适配所有 Adapter） ====================

_CATEGORY_METHODS = {
    "valuation": "calculateValuationMetrics",
    "risk": "calculateRiskMetrics",
    "attribution": "calculateAttributionMetrics",
    "carry": "calculateCarryMetrics",
    "credit_risk": "calculateCreditRiskMetrics",
}

_META_FIELDS = (
    "metric_name", "value", "description", "currency", "unit_code", "unit_raw",
    "risk_class", "risk_factor_id", "leg", "time_unit",
)


def _get_adapter_obj(adapter):
    """获取 Adapter 底层对象（包装类需 getInstance）"""
    if adapter is None:
        return None
    if hasattr(adapter, "getInstance"):
        try:
            return adapter.getInstance()
        except Exception:
            pass
    return adapter


def _metric_value_for_excel(m):
    """C++ 可能返回 NaN/Inf，经 PyXLL 写入 Excel 会显示 #NUM!；统一为有限浮点。"""
    import math
    try:
        x = float(getattr(m, "value", 0))
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(x) or math.isinf(x):
        return 0.0
    return x


def _collect_all_metrics(adapter, sources=None):
    """从 adapter 收集指标，sources 默认全部"""
    obj = _get_adapter_obj(adapter)
    if obj is None or not _is_adapter(obj):
        return []
    src = sources or list(_CATEGORY_METHODS.keys())
    results = []
    for cat in src:
        method = _CATEGORY_METHODS.get(cat)
        if not method:
            continue
        vals = _safe_call(obj, method, [])
        if vals:
            results.extend(vals)
    return results


# 归因指标别名：用户可输入 Carry/Rates/Credit 或 ATTRIBUTION_CARRY，双向匹配
_ATTRIBUTION_ALIASES = {
    "carry": ["ATTRIBUTION_CARRY"],
    "rates": ["ATTRIBUTION_RATES"],
    "credit": ["ATTRIBUTION_CREDIT"],
    "total": ["ATTRIBUTION_TOTAL"],
    "residual": ["ATTRIBUTION_RESIDUAL"],
    "attribution_carry": ["carry"],
    "attribution_rates": ["rates"],
    "attribution_credit": ["credit"],
    "attribution_total": ["total"],
    "attribution_residual": ["residual"],
}


def _find_metric(metrics, metric_name):
    """按 metric_name 匹配（大小写不敏感），支持 Carry<->ATTRIBUTION_CARRY 等别名"""
    if not metrics or not metric_name:
        return None, -1
    mname = str(metric_name).strip().lower()
    candidates = [mname]
    if mname in _ATTRIBUTION_ALIASES:
        candidates.extend(_ATTRIBUTION_ALIASES[mname])
    for i, m in enumerate(metrics):
        nm = getattr(m, "metric_name", None) or getattr(m, "description", "") or ""
        if not nm:
            continue
        nm_lower = str(nm).lower()
        for c in candidates:
            if nm_lower == c:
                return m, i
    return None, -1


def _flatten_metrics_arg(metrics_arg):
    """展平 Excel 传入的 metrics 参数（区域或列表）"""
    if metrics_arg is None:
        return []
    out = []
    if isinstance(metrics_arg, (list, tuple)):
        for x in metrics_arg:
            if isinstance(x, (list, tuple)):
                out.extend(_flatten_metrics_arg(x))
            elif x is not None and str(x).strip():
                out.append(str(x).strip())
    elif str(metrics_arg).strip():
        out.append(str(metrics_arg).strip())
    return list(dict.fromkeys(out))  # 去重保序


# CLN 归因阶梯指标：adapterMetric 无此标准指标，需委托 ClnAdapterAttributionLadder
_CLN_LADDER_METRICS = frozenset({"PV_t0", "PV_theta", "PV_rates", "PV_issuer", "PV_ref", "PV_t1"})


def _is_cln_adapter(adapter):
    """判断是否为 CLN Adapter（McpClnAdapter 或 MClnAdapter）"""
    if adapter is None:
        return False
    name = type(adapter).__name__
    if name in ("McpClnAdapter", "MClnAdapter"):
        return True
    # 包装类内部可能是 MClnAdapter
    if hasattr(adapter, "getInstance"):
        try:
            inner = adapter.getInstance()
            return inner is not None and type(inner).__name__ == "MClnAdapter"
        except Exception:
            pass
    return False


@xl_func("object adapter, string metric_name: var", category="MCP", name="adapterMetric")
def adapter_metric(adapter, metric_name):
    """
    通用 Adapter 单指标获取。metric_name 如 PV, CS01, DV01, ATTRIBUTION_CARRY 等。
    CLN 归因阶梯 PV_t0/PV_theta/PV_rates/PV_issuer/PV_ref/PV_t1 自动委托 ClnAdapterAttributionLadder。
    若未找到返回 "#Adapter: 无 {metric_name} 结果"
    """
    if adapter is None:
        return "#Adapter: adapter 为空"
    if isinstance(adapter, str):
        return "#Adapter: adapter 创建失败"
    if not metric_name or not str(metric_name).strip():
        return "#Adapter: metric_name 不能为空"
    mname = str(metric_name).strip()
    try:
        # CLN 归因阶梯：委托 ClnAdapterAttributionLadder
        if mname in _CLN_LADDER_METRICS and _is_cln_adapter(adapter):
            try:
                from pyxll_func.core.bond import ClnAdapterAttributionLadder
                result = ClnAdapterAttributionLadder(adapter, mname)
                if isinstance(result, (int, float)):
                    return float(result)
                if isinstance(result, str) and not result.startswith("#"):
                    return float(result)
                return result  # 可能是错误信息
            except Exception:
                pass
        metrics = _collect_all_metrics(adapter)
        m, _ = _find_metric(metrics, metric_name)
        if m is not None:
            return _metric_value_for_excel(m)
        adapter_type = type(adapter).__name__
        return f"#{adapter_type}: 无 {mname} 结果"
    except Exception as e:
        return f"#Adapter: {e}"


@xl_func(
    "object adapter, var metrics, string layout: var[][]",
    category="MCP", name="adapterMetrics",
    macro=False, recalc_on_open=True, auto_resize=True
)
def adapter_metrics(adapter, metrics=None, layout="V"):
    """
    指定多个指标返回。metrics 为指标名数组或 Excel 区域，如 {"PV","CS01","DV01"}。
    layout: V 竖向(默认) [[name,val],...], H 横向 [[names...],[values...]]
    """
    if adapter is None:
        return [["#Adapter: adapter 为空"]]
    if isinstance(adapter, str):
        return [["#Adapter: adapter 创建失败"]]
    try:
        all_m = _collect_all_metrics(adapter)
        names = _flatten_metrics_arg(metrics)
        if not names:
            return [["#Adapter: metrics 不能为空"]]
        triples = []
        for nm in names:
            m, _ = _find_metric(all_m, nm)
            val = _metric_value_for_excel(m) if m is not None else ""
            bk  = _get_bucket_key(m) if m is not None else ""
            triples.append((nm, bk, val))
        if layout and str(layout).strip().upper() == "H":
            return [
                [t[0] for t in triples],
                [t[1] for t in triples],
                [t[2] for t in triples],
            ]
        return [[t[0], t[1], t[2]] for t in triples]
    except Exception as e:
        return [[f"#Adapter: {e}"]]


def _get_bucket_key(m) -> str:
    """提取指标的 bucket_key（Horizon/tenor/VAR类型等区分字段）。
    优先读 bucket_spec.bucket_value，次读 bucket_spec.tenor，再读 time_unit。
    当 key 中不含置信度（无 ":"）时，若 metric 有 confidence_level 字段则自动拼接，
    例如 "1D" + confidence_level=0.95 → "1D:95"。
    """
    key = ""
    try:
        bs = getattr(m, "bucket_spec", None)
        if bs is not None:
            bv = getattr(bs, "bucket_value", None)
            if bv:
                key = str(bv)
            if not key:
                tv = getattr(bs, "tenor", None)
                if tv:
                    key = str(tv)
    except Exception:
        pass
    if not key:
        try:
            tu = getattr(m, "time_unit", None)
            if tu:
                key = str(tu)
        except Exception:
            pass
    # 若 key 中已包含 ":" 则已有置信度，直接返回
    if key and ":" in key:
        return key
    # 否则尝试从 confidence_level 字段补充置信度
    if key:
        try:
            cl = getattr(m, "confidence_level", None)
            if cl is not None:
                cl_f = float(cl)
                if 0.0 < cl_f <= 1.0:
                    key = key + ":" + str(int(round(cl_f * 100)))
        except Exception:
            pass
    return key


@xl_func(
    "object adapter, string category, string layout: var[][]",
    category="MCP", name="adapterMetricsByCategory",
    macro=False, recalc_on_open=True, auto_resize=True
)
def adapter_metrics_by_category(adapter, category, layout="V"):
    """
    返回一类指标全部结果。category: valuation/risk/attribution/carry/credit_risk。
    layout: V 竖向(默认) → 每行 [metric_name, bucket_key, value]
            H 横向        → 三行: [names...] / [bucket_keys...] / [values...]
    bucket_key：用于区分 VAR/ES 的 Horizon（如 1D/10D）、KRD 的 tenor 桶等。
    """
    if adapter is None:
        return [["#Adapter: adapter 为空"]]
    if isinstance(adapter, str):
        return [["#Adapter: adapter 创建失败"]]
    cat = str(category).strip().lower() if category else ""
    if cat not in _CATEGORY_METHODS:
        return [[f"#Adapter: category 需为 valuation/risk/attribution/carry/credit_risk 之一"]]
    try:
        metrics = _collect_all_metrics(adapter, sources=[cat])
        if not metrics:
            return [["#Adapter: 无该类别指标"]]
        triples = []  # (metric_name, bucket_key, value)
        for m in metrics:
            nm = getattr(m, "metric_name", None) or getattr(m, "description", "") or ""
            if not nm:
                continue
            val = _metric_value_for_excel(m)
            bk  = _get_bucket_key(m)
            triples.append((str(nm), bk, val))
        if not triples:
            return [["#Adapter: 无该类别指标"]]
        if layout and str(layout).strip().upper() == "H":
            return [
                [t[0] for t in triples],   # row 1: metric_name
                [t[1] for t in triples],   # row 2: bucket_key
                [t[2] for t in triples],   # row 3: value
            ]
        # V 模式：每行 3 列
        return [[t[0], t[1], t[2]] for t in triples]
    except Exception as e:
        return [[f"#Adapter: {e}"]]


@xl_func(
    "object adapter, object curve: object",
    category="MCP", name="bondAdapterSetPreviousCurve",
    macro=False, recalc_on_open=True,
)
def bond_adapter_set_previous_curve(adapter, curve):
    """
    在已创建的 McpBondAdapter 上调用 SetPreviousCurve（传入 McpBondCurve 等 SWIG 包装类，勿用 getHandler）。
    当构建 Adapter 的 VP 区域未包含 PreviousCurve 键时，可用本函数在旁路单元格补设，再计算 attribution。
    成功返回同一 adapter 对象。
    """
    if adapter is None:
        return "#Adapter: adapter 为空"
    if isinstance(adapter, str):
        return "#Adapter: adapter 创建失败"
    if curve is None:
        return "#Adapter: curve 为空"
    try:
        if hasattr(adapter, "SetPreviousCurve"):
            adapter.SetPreviousCurve(curve)
        else:
            return "#Adapter: 无 SetPreviousCurve"
        return adapter
    except Exception as e:
        return f"#Adapter: {e}"


@xl_func(
    "object adapter, string metric_name, string field: var",
    category="MCP", name="adapterMetricMeta",
    macro=False, recalc_on_open=True, auto_resize=True
)
def adapter_metric_meta(adapter, metric_name, field=None):
    """
    获取某指标的元数据。field 为空返回 [[field,value],...]；指定 field 返回该字段值。
    可选 field: metric_name, value, description, currency, unit_code, unit_raw, risk_class, risk_factor_id, leg, time_unit
    """
    if adapter is None:
        return "#Adapter: adapter 为空"
    if isinstance(adapter, str):
        return "#Adapter: adapter 创建失败"
    if not metric_name or not str(metric_name).strip():
        return "#Adapter: metric_name 不能为空"
    try:
        metrics = _collect_all_metrics(adapter)
        m, _ = _find_metric(metrics, metric_name)
        if m is None:
            return f"#Adapter: 无 {str(metric_name).strip()} 结果"
        f = str(field).strip() if field else ""
        if f:
            if hasattr(m, f):
                v = getattr(m, f)
                if hasattr(v, "tenor") or hasattr(v, "bucket_value"):
                    return getattr(v, "tenor", None) or getattr(v, "bucket_value", str(v))
                return v
            return f"#Adapter: 无字段 {f}"
        out = []
        for fn in _META_FIELDS:
            if hasattr(m, fn):
                v = getattr(m, fn)
                if hasattr(v, "tenor") or hasattr(v, "bucket_value"):
                    v = getattr(v, "tenor", None) or getattr(v, "bucket_value", str(v))
                out.append([fn, v])
        return out if out else [["metric_name", getattr(m, "metric_name", "")]]
    except Exception as e:
        return f"#Adapter: {e}"


# ==================== 向后兼容别名（SwapNPV 等） ====================

@xl_func("object adapter: var", category="MCP", name="SwapNPV")
def _metrics_npv(adapter):
    return calculate_npv(adapter)


@xl_func("object adapter, string horizon, float confidence: var", category="MCP", name="SwapVaR")
def _metrics_var(adapter, horizon=None, confidence=None):
    return calculate_var(adapter, horizon, confidence)


@xl_func("object adapter, string horizon, float confidence: var", category="MCP", name="SwapES")
def _metrics_es(adapter, horizon=None, confidence=None):
    return calculate_es(adapter, horizon, confidence)


@xl_func("object adapter, string horizon: var", category="MCP", name="SwapEE")
def _metrics_ee(adapter, horizon=None):
    return calculate_ee(adapter, horizon)


@xl_func("object adapter, string horizon, float confidence: var", category="MCP", name="SwapPFE")
def _metrics_pfe(adapter, horizon=None, confidence=None):
    return calculate_pfe(adapter, horizon, confidence)


@xl_func(
    "object adapter, object credit_curve, float recovery_rate, float pd, float lgd: var",
    category="MCP", name="SwapCVA"
)
def _metrics_cva(adapter, credit_curve=None, recovery_rate=None, pd=None, lgd=None):
    return calculate_cva(adapter, credit_curve, recovery_rate, pd, lgd)


@xl_func("object adapter: var", category="MCP", name="SwapDFE")
def _metrics_dfe(adapter):
    return calculate_dfe(adapter)
