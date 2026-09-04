"""
指标枚举映射表

此文件包含 Metric ID 到名称的映射，用于在 Python 端正确显示指标名称。
映射表基于 C++ 端的 Metric 枚举和 getMetricName() 函数。

当 C++ 端没有正确设置 metric_name 字段时，可以使用此映射表根据 metric_id 获取正确的指标名称。
"""

# Metric ID 到名称的映射表
# 基于 include/mcp-metrics-framework/metrics_types.h 中的 Metric 枚举和 getMetricName() 函数
METRIC_ID_TO_NAME = {
    # Valuation metrics (估值指标)
    0: "PV",                      # Present Value
    1: "MARKET_VALUE",            # Market Value
    2: "NPV",                     # Net Present Value
    3: "SWAP_PRICE",              # Swap Price
    4: "CLEAN_PRICE",             # Clean Price
    5: "DIRTY_PRICE",             # Dirty Price
    6: "YIELD",                   # Yield
    7: "ACCRUED_INTEREST",       # Accrued Interest
    8: "REAL_YIELD",              # Real Yield
    9: "PAR_RATE",                # Par Rate
    10: "FORWARD_RATE",           # Forward Rate
    11: "Z_SPREAD",               # Z Spread
    12: "I_SPREAD",               # I Spread
    13: "ASWAP_SPREAD",           # Asset Swap Spread
    14: "OAS",                    # Option-Adjusted Spread
    15: "PAR_SPREAD",             # Par Spread
    16: "DISCOUNT_MARGIN",        # Discount Margin
    17: "IMPLIED_VOL",            # Implied Volatility
    18: "BREAKEVEN_INFLATION",    # Breakeven Inflation
    19: "BASIS_LEVEL",            # Basis Level
    20: "CALENDAR_SPREAD",        # Calendar Spread
    21: "FAIR_VALUE",             # Fair Value
    22: "MARKET_PRICE",           # Market Price
    23: "CONTRACT_PRICE",         # Contract Price
    24: "FUNDING_COST",           # Funding Cost
    25: "REPO_INCOME",            # Repo Income
    26: "START_NOMINAL",          # Repo Start Nominal
    27: "END_NOMINAL",            # Repo End Nominal
    28: "COLLATERAL_VALUE",       # Collateral Value
    29: "HAIRCUT_VALUE",          # Haircut Value
    30: "AGGREGATION_WEIGHT",     # Aggregation Weight
    31: "TRADE_COUNT",            # Trade Count

    # Risk metrics (风险指标)
    32: "DV01",                   # Dollar duration / IR parallel shift 1bp
    33: "COLLATERAL_DV01",        # Collateral DV01
    34: "CURVE_DV01",             # Curve DV01
    35: "RESET_DV01",             # Reset DV01
    36: "BUTTERFLY_DV01",         # Butterfly DV01
    37: "DURATION",               # Duration
    38: "EFFECTIVE_DURATION",     # Effective Duration
    39: "CONVEXITY",              # Convexity
    40: "ANNUITY",                # Annuity
    41: "KRD",                    # Key Rate Duration
    42: "CS01",                   # Credit spread sensitivity (1bp)
    43: "OASD",                   # OAS Duration
    44: "JUMP_TO_DEFAULT",        # Jump to default risk
    45: "DEFAULT_PROBABILITY",    # Default Probability
    46: "EXPECTED_LOSS",          # Expected Loss
    47: "CVA",                    # Credit Valuation Adjustment
    48: "DELTA",                  # Delta
    49: "FORWARD_DELTA",          # Forward Delta
    50: "GAMMA",                  # Gamma
    51: "RHO",                    # Rho
    52: "PHI",                    # Phi
    53: "VEGA",                   # Vega
    54: "THETA",                  # Theta
    55: "VANNA",                  # Vanna
    56: "VOLGA",                  # Volga (Vomma)
    57: "WEIGHTED_AVERAGE_LIFE",  # Weighted Average Life (WAL)
    58: "CONSTANT_PREPAYMENT_RATE", # Constant Prepayment Rate (CPR)
    59: "PREPAYMENT_SENSITIVITY",  # Prepayment Sensitivity
    60: "XCCY_BASIS_DV01",        # Cross-Currency Basis DV01
    61: "INFLATION_DV01",         # Inflation DV01
    62: "REAL_RATE_DV01",         # Real Rate DV01
    63: "ROLL_DOWN",              # Roll Down
    64: "VAR",                    # Value at Risk
    65: "ES",                     # Expected Shortfall (Conditional VaR)
    66: "PFE",                    # Potential Future Exposure
    67: "EE",                     # Expected Exposure (Trade EE)
    68: "COMPONENT_VAR",          # Component Value at Risk
    69: "INCREMENTAL_VAR",        # Incremental Value at Risk (IVaR_i = VaR(P) - VaR(P-i))
    70: "COMPONENT_ES",           # Component Expected Shortfall
    71: "COMPONENT_PFE",          # Component Potential Future Exposure
    72: "PORTFOLIO_VAR",          # Portfolio Value at Risk
    73: "PORTFOLIO_ES",           # Portfolio Expected Shortfall
    74: "PORTFOLIO_PFE",          # Portfolio Potential Future Exposure

    # Attribution metrics (归因指标)
    75: "DAILY_PNL",              # Daily PNL
    76: "DISCOUNTED_PNL",         # Discounted Daily PNL
    77: "CARRY_PNL",              # Carry PNL
    78: "CURVE_PNL",              # Curve PNL
    79: "SPREAD_PNL",             # Spread PNL
    80: "RESET_PNL",              # Reset PNL
    81: "DELTA_PNL",              # Delta PNL
    82: "VEGA_PNL",               # Vega PNL
    83: "THETA_PNL",              # Theta PNL
    84: "FX_PNL",                 # FX PNL
    85: "BASIS_PNL",              # Basis PNL
    86: "INFLATION_PNL",          # Inflation PNL
    87: "PREPAYMENT_PNL",         # Prepayment PNL
    88: "FUNDING_PNL",            # Funding PNL
    89: "MTM_PNL",                # Mark-to-market PnL
    90: "RPNL",                   # Realized PnL
    91: "MTM_PNL_DC",             # Discounted mark-to-market PnL

    # Campisi Attribution metrics (Campisi 归因指标)
    92: "PORTFOLIO_RETURN",       # Portfolio Total Return
    93: "BENCHMARK_RETURN",       # Benchmark Total Return
    94: "EXCESS_RETURN",          # Excess Return
    95: "RATE_LEVEL_EFFECT_PORTFOLIO",    # Rate Level Effect (Portfolio)
    96: "RATE_LEVEL_EFFECT_BENCHMARK",    # Rate Level Effect (Benchmark)
    97: "RATE_LEVEL_EFFECT_EXCESS",       # Rate Level Effect (Excess)
    98: "CURVE_SHAPE_EFFECT_PORTFOLIO",   # Curve Shape Effect (Portfolio)
    99: "CURVE_SHAPE_EFFECT_BENCHMARK",   # Curve Shape Effect (Benchmark)
    100: "CURVE_SHAPE_EFFECT_EXCESS",      # Curve Shape Effect (Excess)
    101: "CREDIT_SPREAD_EFFECT_PORTFOLIO", # Credit Spread Effect (Portfolio)
    102: "CREDIT_SPREAD_EFFECT_BENCHMARK", # Credit Spread Effect (Benchmark)
    103: "CREDIT_SPREAD_EFFECT_EXCESS",    # Credit Spread Effect (Excess)
    104: "CARRY_EFFECT_PORTFOLIO",         # Carry Effect (Portfolio)
    105: "CARRY_EFFECT_BENCHMARK",        # Carry Effect (Benchmark)
    106: "CARRY_EFFECT_EXCESS",            # Carry Effect (Excess)
    107: "SELECTION_EFFECT",              # Selection Effect
    108: "ALLOCATION_EFFECT",             # Allocation Effect
    109: "RESIDUAL_EFFECT",               # Residual Effect
    110: "SPREAD_DURATION",               # Spread Duration

    # Equity Attribution metrics (权益归因指标)
    111: "EQUITY_ALLOCATION_EFFECT",     # Equity Allocation Effect
    112: "EQUITY_SELECTION_EFFECT",      # Equity Selection Effect
    113: "EQUITY_INTERACTION_EFFECT",    # Equity Interaction Effect
    114: "EQUITY_MARKET_FACTOR_PNL",     # Equity Market Factor PnL
    115: "EQUITY_SIZE_FACTOR_PNL",       # Equity Size Factor PnL
    116: "EQUITY_VALUE_FACTOR_PNL",      # Equity Value Factor PnL
    117: "EQUITY_MOMENTUM_FACTOR_PNL",   # Equity Momentum Factor PnL
    118: "EQUITY_QUALITY_FACTOR_PNL",    # Equity Quality Factor PnL
    119: "EQUITY_VOLATILITY_FACTOR_PNL", # Equity Volatility Factor PnL
    120: "EQUITY_INDUSTRY_FACTOR_PNL",   # Equity Industry Factor PnL

    # Option Attribution metrics (期权归因指标)
    121: "GAMMA_PNL",                    # Gamma PNL
    122: "RHO_PNL",                      # Rho PNL
    123: "OPTION_RESIDUAL_PNL",          # Option Residual PNL

    # Carry metrics (Carry 指标)
    124: "THEORETICAL_CARRY",            # Theoretical Carry
    125: "COUPON_INCOME",                # Coupon Income
    126: "TIME_DECAY",                   # Time Decay

    # Unified Attribution metrics (统一归因指标)
    127: "PRICE_CHANGE_PNL",             # Price Change PnL
    128: "VOLATILITY_CHANGE_PNL",        # Volatility Change PnL
    129: "TIME_CARRY_PNL",               # Time/Carry PnL
    130: "TRANSACTION_COST_PNL",         # Transaction Cost PnL

    # Concentration metrics (集中度指标)
    131: "CONCENTRATION_HHI",            # HHI集中度指数
    132: "CONCENTRATION_TOP_N_RATIO",    # Top N占比
    133: "CONCENTRATION_MAX_BUCKET_RATIO", # 最大Bucket占比
    134: "CONCENTRATION_EFFECTIVE_BUCKETS", # 有效Bucket数量

    # Fund新增指标 (2026-05-12)
    392: "AVERAGE_COST",            # 持仓均价
    393: "CURRENT_NAV",             # 当前净值
    394: "BETA",                    # 贝塔系数
    395: "FUND_VOLATILITY",         # 基金波动率（年化）
    396: "SORTINO_RATIO",           # 索提诺比率
    397: "ALPHA",                   # 阿尔法系数
}


def get_metric_name(metric_result):
    """
    从 MetricResult 对象获取指标名称

    参数:
        metric_result: MetricResult 对象（SWIG 包装的 C++ 对象）

    返回:
        str: 指标名称字符串
    """
    # 策略：优先使用 metric_ 枚举值（最可靠），因为 C++ 端可能没有正确设置 metric_id 和 metric_name

    # 1. 首先尝试使用 metric_ 枚举值（最可靠）
    if hasattr(metric_result, 'metric_'):
        try:
            metric_enum = getattr(metric_result, 'metric_', None)
            if metric_enum is not None:
                # SWIG 将 C++ 枚举转换为 Python 整数，所以 metric_enum 可能是整数
                if isinstance(metric_enum, int):
                    # 如果是整数，使用映射表获取名称
                    return METRIC_ID_TO_NAME.get(metric_enum, f"Metric_{metric_enum}")
                else:
                    # 如果是字符串或其他类型，尝试解析
                    metric_str = str(metric_enum)
                    # 提取枚举名称（例如 "Metric::PV" -> "PV", "mcp::metrics::Metric::DIRTY_PRICE" -> "DIRTY_PRICE"）
                    if '::' in metric_str:
                        # 提取最后一个 :: 后面的部分
                        parts = metric_str.split('::')
                        enum_name = parts[-1]
                        return enum_name
                    elif '.' in metric_str:
                        return metric_str.split('.')[-1]
                    else:
                        # 如果看起来像数字字符串，尝试转换为整数
                        try:
                            metric_id = int(metric_str)
                            return METRIC_ID_TO_NAME.get(metric_id, f"Metric_{metric_id}")
                        except ValueError:
                            return metric_str
        except Exception as e:
            # 如果转换失败，继续尝试其他方法
            pass

    # 2. 如果 metric_ 不可用，检查 metric_name 字段
    if hasattr(metric_result, 'metric_name'):
        metric_name_value = getattr(metric_result, 'metric_name', '')
        if metric_name_value and metric_name_value.strip():
            # 如果 metric_name 不是默认的 "PV"，直接使用
            if metric_name_value != 'PV':
                return metric_name_value
            # 如果 metric_name 是 "PV"，检查 metric_id 是否为 0
            if hasattr(metric_result, 'metric_id'):
                metric_id = getattr(metric_result, 'metric_id', -1)
                if metric_id == 0:
                    return 'PV'  # 确实是 PV
                # metric_id 不是 0 但 metric_name 是 "PV"，说明 C++ 端没有正确设置，使用 metric_id 映射
                return METRIC_ID_TO_NAME.get(metric_id, f"Metric_{metric_id}")

    # 3. 如果 metric_name 不可用，使用 metric_id 映射
    if hasattr(metric_result, 'metric_id'):
        metric_id = getattr(metric_result, 'metric_id', -1)
        if metric_id >= 0:  # 有效的 metric_id
            return METRIC_ID_TO_NAME.get(metric_id, f"Metric_{metric_id}")

    # 4. 如果所有方法都失败，返回未知指标
    return "Unknown_Metric"


def get_metric_name_by_id(metric_id):
    """
    根据 metric_id 获取指标名称

    参数:
        metric_id: int, 指标 ID

    返回:
        str: 指标名称字符串
    """
    return METRIC_ID_TO_NAME.get(metric_id, f"Metric_{metric_id}")

