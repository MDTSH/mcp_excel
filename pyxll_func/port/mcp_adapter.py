import json
from typing import Any, Dict, List, Union
from datetime import datetime, date, timedelta

from mcp.tool.args_def import tool_def
from mcp.utils.enums import BondOptionType
from pyxll import xl_func, xl_arg
from metric_enums import get_metric_name

try:
    import mcp.mcp as mcp_module

    print(
        f"[OK] Successfully imported mcp module from: {mcp_module.__file__ if hasattr(mcp_module, '__file__') else 'unknown'}")
except Exception as e:
    print(f"[ERROR] Failed to import mcp module: {e}")
    import traceback

    traceback.print_exc()

REFERENCE_DATE = "2024-12-13"
SETTLEMENT_DATE = "2024-12-13"
MATURITY_DATE = "2027-12-13"  # 3年期债券
FREQUENCY = 2  # 半年付息
COUPON_RATE = 0.035  # 3.5% 票面利率
FACE_VALUE = 1000000.0  # 面值 100万
COUPON_TYPE_INTEREST = 3


def excel_date_to_string(excel_date):
    if isinstance(excel_date, float):
        # Excel的日期从1900-01-01开始
        base_date = datetime(1899, 12, 30)
        # 将Excel日期转换为timedelta
        delta_days = timedelta(days=float(excel_date))
        # 计算日期
        date_obj = base_date + delta_days
        # 格式化日期字符串
        date_string = date_obj.strftime('%Y-%m-%d')
        return date_string
    else:
        return excel_date


# _object_refs = {
#     'bonds': [],
#     'adapters': [],
#     'curves': [],
#     'market_data': []
# }


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("settlement_date", "var")
# @xl_arg("maturity_date", "var")
# @xl_arg("frequency", "int")
# @xl_arg("coupon_rate", "float")
# @xl_arg("coupon_type_interest", "int")
# @xl_arg("reference_date", "var")
# def MFixedRateBond(settlement_date="2024-12-13", maturity_date="2027-12-13", frequency=2, coupon_rate=0.035,
#                    coupon_type_interest=3, reference_date="2024-12-13"):
#     maturity_date = excel_date_to_string(maturity_date)
#     settlement_date = excel_date_to_string(settlement_date)
#     reference_date = excel_date_to_string(reference_date)
#     fixed_rate_bond = mcp_module.MFixedRateBond(
#         settlement_date,
#         maturity_date,
#         frequency,
#         coupon_rate,
#         coupon_type_interest,  # couponType = INTEREST (付息式)
#         reference_date,  # valueDate
#         100.0,  # issuePrice (发行价格，通常为100)
#         1  # dayCounter: Act365Fixed
#     )
#     # _object_refs['bonds'].append(fixed_rate_bond)
#     return fixed_rate_bond


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("reference_date", "var")
# @xl_arg("fixedratebond", "object")
# @xl_arg("option_type_call", "int")
# @xl_arg("exercise_dates_str", "str")
# @xl_arg("strikes_str", "str")
# @xl_arg("yieldcurve", "object")
# def MCallableBond(reference_date, fixedratebond, option_type_call, exercise_dates_str, strikes_str, yieldcurve):
#     #  option_type_call   BondOptionType 枚举值
#     reference_date = excel_date_to_string(reference_date)
#     callable_bond = mcp_module.MCallableBond(
#         reference_date,  # valuationDate
#         fixedratebond.getHandler(),  # underlyingBond (void*)
#         option_type_call,  # optionType: CALL=1
#         exercise_dates_str,  # exerciseDates (逗号分隔)
#         strikes_str,  # strikes (逗号分隔)
#         yieldcurve.getHandler()  # yieldCurve (void*)
#     )
#     return callable_bond


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("fmt", "str")
def MCallableBond(args1, args2, fmt='VP|VP'):
    try:
        args1_fmt, args2_fmt = fmt.split("|")
        args1_fmt = args1_fmt.strip().upper()
        args2_fmt = args2_fmt.strip().upper()
        if args1_fmt not in ["VP", "HD"] or args2_fmt not in ["VP", "HD"]:
            raise ValueError("fmt格式仅支持 VP(纵向) 或 HD(横向)，示例：VP|HD、HD|VP")
    except ValueError as e:
        error_msg = f"解析fmt参数失败：{e}，正确格式示例：VP|VP、VP|HD"
        print(error_msg)
        return error_msg

    print("\n=== [调试] args2 原始输入数据 ===")
    print(f"args2 类型: {type(args2)}")
    print(f"args2 长度: {len(args2)} 行")
    # 逐行打印 args2 内容
    for row_idx, row in enumerate(args2):
        print(f"args2 第 {row_idx + 1} 行: {row}")

    # 2. 解析 args1（基础参数）
    default_args1 = {
        "ReferenceDate": None,
        "FixedRateBond": None,
        "OptionType": "CALL",  # 默认CALL
        "BenchmarkCurve": None,
        "SpreadCurve": None,   # 方案A可选：BondSpreadCurve
        "VolDates": None,
        "IrVols": None,
    }
    try:
        # 解析 args1（VP/HD 格式）
        if args1_fmt == "VP":  # 纵向：[[key, value], [key, value]]
            for item in args1:
                if len(item) == 2:
                    key = item[0].strip()
                    value = item[1]
                    if key in default_args1:
                        default_args1[key] = value
        else:  # HD 横向：[[key1, key2], [value1, value2]]
            if len(args1) >= 2:
                keys = [k.strip() for k in args1[0]]
                values = args1[1]
                for idx, key in enumerate(keys):
                    if key in default_args1 and idx < len(values):
                        default_args1[key] = values[idx]

        # 校验 args1 核心参数
        if not default_args1["ReferenceDate"]:
            raise ValueError("args1中必须传入 ReferenceDate 参数")
        if not default_args1["FixedRateBond"]:
            raise ValueError("args1中必须传入 FixedRateBond 参数")
        if not default_args1["BenchmarkCurve"]:
            raise ValueError("args1中必须传入 BenchmarkCurve 参数")
        if default_args1["VolDates"] is None:
            raise ValueError("args1中必须传入 VolDates 参数")
        if default_args1["IrVols"] is None:
            raise ValueError("args1中必须传入 IrVols 参数")

        # 转换 ReferenceDate 格式
        reference_date = excel_date_to_string(default_args1["ReferenceDate"])

        # 核心调整：直接使用已有 BondOptionType 类转换字符串枚举
        option_type_str = default_args1["OptionType"].strip().upper()
        # 检查 BondOptionType 类是否有该属性
        if not hasattr(BondOptionType, option_type_str):
            raise ValueError(
                f"无效的OptionType：{option_type_str}，"
                f"支持的类型：{[attr for attr in dir(BondOptionType) if not attr.startswith('__')]}"
            )
        # 从 BondOptionType 类中获取对应的数值
        option_type_call = getattr(BondOptionType, option_type_str)
        # 3. 解析 args2（行权参数：ExerciseDates/Strikes）
        exercise_dates = []
        strikes = []

        print(f"[调试] 开始解析args2（格式：{args2_fmt}）")
        if args2_fmt == "VP":  # args2 纵向：[['ExerciseDates', d1, d2], ['Strikes', s1, s2]]
            # 遍历每行，提取键和对应的值列表
            for row in args2:
                if len(row) < 2:
                    continue
                key = row[0].strip()
                values = row[1:]  # 取第2列及以后的所有值

                if key == "ExerciseDates":
                    print(f"[调试] VP格式 - 行权日期原始值: {values}")
                    for date_val in values:
                        if date_val:
                            exercise_dates.append(excel_date_to_string(date_val))
                elif key == "Strikes":
                    print(f"[调试] VP格式 - 行权价原始值: {values}")
                    for strike_val in values:
                        if strike_val:
                            strikes.append(float(strike_val))

        else:  # args2 横向：[['ExerciseDates','Strikes'], [d1,s1], [d2,s2]]
            if len(args2) < 2:
                raise ValueError("HD格式args2至少需要2行（表头+数据）")

            # 提取表头和数据行
            header = [k.strip() for k in args2[0]]
            data_rows = args2[1:]

            # 找到日期和价格的列索引
            if "ExerciseDates" not in header or "Strikes" not in header:
                raise ValueError("HD格式args2表头必须包含 ExerciseDates 和 Strikes")
            date_col_idx = header.index("ExerciseDates")
            strike_col_idx = header.index("Strikes")

            # 遍历数据行提取值
            print(f"[调试] HD格式 - 表头: {header} | 数据行数: {len(data_rows)}")
            for row_idx, row in enumerate(data_rows):
                if len(row) <= max(date_col_idx, strike_col_idx):
                    print(f"[警告] HD格式第{row_idx + 1}行数据不足，跳过")
                    continue

                # 提取行权日期
                date_val = row[date_col_idx]
                if date_val:
                    exercise_dates.append(excel_date_to_string(date_val))

                # 提取行权价
                strike_val = row[strike_col_idx]
                if strike_val:
                    strikes.append(float(strike_val))
        exercise_dates_str = json.dumps(exercise_dates)
        # 行权价数组：标准JSON格式 [100.0,100.0,100.0]
        strikes_str = json.dumps(strikes)

        # 4. 调试打印最终格式
        print("\n=== [调试] 最终输出格式 ===")
        print(f"exercise_dates_str 类型: {type(exercise_dates_str)}")
        print(f"exercise_dates_str 内容: {exercise_dates_str}")
        print(f"strikes_str 内容: {strikes_str}")
        # 校验行权参数
        if not exercise_dates_str:
            raise ValueError("args2中未传入有效的 ExerciseDates")
        if not strikes_str:
            raise ValueError("args2中未传入有效的 Strikes")
        if len(exercise_dates) != len(strikes):
            raise ValueError(f"ExerciseDates数量({len(exercise_dates)})与Strikes数量({len(strikes)})不匹配")

        # 4. 调用原核心逻辑创建可赎回债券
        fixedratebond = default_args1["FixedRateBond"]
        benchmark_curve = default_args1["BenchmarkCurve"]
        vol_dates_str = json.dumps([excel_date_to_string(x) for x in default_args1["VolDates"] if x])
        ir_vols_str = json.dumps([float(x) for x in default_args1["IrVols"] if x is not None and x != ""])
        spread_curve = default_args1.get("SpreadCurve")
        if spread_curve:
            callable_bond = mcp_module.MCallableBond(
                reference_date,
                fixedratebond.getHandler(),
                option_type_call,
                exercise_dates_str,
                strikes_str,
                benchmark_curve.getHandler(),
                vol_dates_str,
                ir_vols_str,
                spread_curve.getHandler(),
            )
        else:
            callable_bond = mcp_module.MCallableBond(
                reference_date,
                fixedratebond.getHandler(),
                option_type_call,
                exercise_dates_str,
                strikes_str,
                benchmark_curve.getHandler(),
                vol_dates_str,
                ir_vols_str
            )
        return callable_bond

    except Exception as e:
        error_msg = f"创建MCallableBond失败：{e}"
        print(error_msg)
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCommodityFuture(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpCommodityFuture 对象

    参数:
        args1: 二维数组，包含商品期货的参数（key-value 格式）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCommodityFuture 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCommodityFuture')
    except Exception as e:
        error_msg = f"McpCommodityFuture except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondFuture(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpBondFuture 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBondFuture 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBondFuture')
    except Exception as e:
        error_msg = f"McpBondFuture except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEquityFuture(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpEquityFuture 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpEquityFuture 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpEquityFuture')
    except Exception as e:
        error_msg = f"McpEquityFuture except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEquitySpot(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpEquitySpot 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpEquitySpot 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpEquitySpot')
    except Exception as e:
        error_msg = f"McpEquitySpot except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFund(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpFund 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFund 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFund')
    except Exception as e:
        error_msg = f"McpFund except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXNDF(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpFXNDF 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXNDF 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXNDF')
    except Exception as e:
        error_msg = f"McpFXNDF except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpRepurchaseProduct(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpRepurchaseProduct 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpRepurchaseProduct 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpRepurchaseProduct')
    except Exception as e:
        error_msg = f"McpRepurchaseProduct except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpTotalReturnSwap(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpTotalReturnSwap（TRS 总收益互换）对象

    参数:
        args1-args5: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpTotalReturnSwap 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpTotalReturnSwap')
    except Exception as e:
        error_msg = f"McpTotalReturnSwap except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpTRSAdapter(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpTRSAdapter（TRS Adapter）对象

    参数:
        args1-args5: 参数数组（二维数组），需包含 TotalReturnSwap、InstrumentId、TradeId 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpTRSAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        result = tool_def.xls_create(*args, key='McpTRSAdapter')
        return result
    except Exception as e:
        error_msg = f"McpTRSAdapter except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondTRSAdapter(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpBondTRSAdapter（债券 TRS Adapter）对象

    参数 (VP 竖向格式):
        BondIsin         债券 ISIN 代码（如 XS3002940909）
        FaceValue        名义本金（面值，如 3000000）
        Currency         货币（如 CNH、USD）
        StartDate        起始日
        MaturityDate     到期日
        InitialCleanPrice 初始净价（小数，如 0.977879 = 97.7879%）
        InitialAccrued   初始应计利息（小数，默认 0）
        CouponRate       票息率（小数，如 0.07 = 7%）
        CouponFrequency  付息频率（SEMIANNUAL / ANNUAL / QUARTERLY）
        CouponStartDate  债券起息日
        DayCounter       日计数惯例（1=Act365Fixed）
        FixedFundingRate 固定资金利率（小数，如 0.032 = 3.2%）
        Direction        方向（1=多头/接受总收益方，-1=空头）
        PaymentCalendar  结算日历（McpCalendar 对象）

    返回:
        McpBondTRSAdapter 对象（缓存 key: McpBondTRSAdapter@N）
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        result = tool_def.xls_create(*args, key='McpBondTRSAdapter')
        return result
    except Exception as e:
        error_msg = f"McpBondTRSAdapter except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondTRS(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpBondTRS（债券 TRS 合约对象），VP 参数块风格，供 BondTrsMarketParRate 等函数调用。

    参数 (VP 竖向格式):
        BondIsin         债券 ISIN 代码（如 XS3002940909）
        FaceValue        名义本金面值（如 3000000）
        Currency         货币（如 CNY）
        StartDate        资金腿起息日
        MaturityDate     TRS 到期日
        InitialClean     起初净价（小数：0.977879 = 97.7879%）
        CouponRate       票面利率（小数：0.07 = 7%）
        CouponStartDate  债券起息日（用于构建票息日历）
        FixedFundingRate 约定固定融资费率（小数：0.032 = 3.2%）
        CouponFrequency  付息频率（SEMIANNUAL / ANNUAL / QUARTERLY / MONTHLY）
        Direction        方向（1=多方/做多总收益，-1=空方）
        InitialAccrued   起初应计利息（小数，默认 0.0）

    用法示例:
        =McpBondTRS(A33:B45,,,,,"VP")

    返回:
        McpBondTRS 对象（缓存 key: McpBondTRS@N），可传入 BondTrsMarketParRate 等函数
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        result = tool_def.xls_create(*args, key='McpBondTRS')
        return result
    except Exception as e:
        error_msg = f"McpBondTRS except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCreditDefaultSwap(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpCreditDefaultSwap（CDS 产品）对象

    参数:
        args1-args5: 参数数组，需包含 Notional、TradeDate、MaturityDate、ValuationDate、Spread、RecoveryRate 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCreditDefaultSwap 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCreditDefaultSwap')
    except Exception as e:
        error_msg = f"McpCreditDefaultSwap except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCdsAdapter(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpCdsAdapter（CDS Adapter）对象

    参数:
        args1-args5: 参数数组，需包含 CreditDefaultSwap、InstrumentId、TradeId、CreditCurve、YieldCurve 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCdsAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCdsAdapter')
    except Exception as e:
        error_msg = f"McpCdsAdapter except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpClnAdapter(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpClnAdapter（CLN 信用联结票据 Adapter）对象

    参数:
        args1-args5: 参数数组，需包含 Bond、CreditDefaultSwap、InstrumentId、TradeId、
                     CreditCurve、YieldCurve、Notional、Currency 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpClnAdapter 对象（需 MClnAdapter 已集成到 mcp 构建）
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpClnAdapter')
    except Exception as e:
        error_msg = f"McpClnAdapter except: {e}"
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardOutright(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpFXForwardOutright 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXForwardOutright 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpFXForwardOutright' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFXForwardOutright' not in tool_def.item_dict:
            error_msg = "McpFXForwardOutright: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXForwardOutright')
    except Exception as e:
        error_msg = f"McpFXForwardOutright except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBond(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpBond 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBond 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpBond' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpBond' not in tool_def.item_dict:
            error_msg = "McpBond: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBond')
    except Exception as e:
        error_msg = f"McpBond except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCallableBond(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpCallableBond 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCallableBond 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpCallableBond' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpCallableBond' not in tool_def.item_dict:
            error_msg = "McpCallableBond: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCallableBond')
    except Exception as e:
        error_msg = f"McpCallableBond except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardOutright1(args1, args2, args3, args4, args5, fmt="VP"):
    """
    创建 McpFXForwardOutright 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXForwardOutright 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpFXForwardOutright' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFXForwardOutright' not in tool_def.item_dict:
            error_msg = "McpFXForwardOutright: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXForwardOutright')
    except Exception as e:
        error_msg = f"McpFXForwardOutright except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        return error_msg


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond_type", "str")
# @xl_arg("bond", "object")
# @xl_arg("instrument_id", "str")
# @xl_arg("trade_id", "str")
# @xl_arg("product_type", "str")
# @xl_arg("valuation_curve", "object")
# @xl_arg("benchmark_curve", "object")
# @xl_arg("swap_curve", "object")
# @xl_arg("spread_curve", "object")
# @xl_arg("reference_date", "str")
# @xl_arg("credit_curve", "object")
# def McpBondAdapter(bond_type, bond, instrument_id='BOND_001', trade_id='TRADE_BOND_001', product_type='CASH_RATES',
#                    valuation_curve=None, benchmark_curve=None, swap_curve=None, spread_curve=None, reference_date=None,
#                    credit_curve=None):
#     # 判断是fixedratebond 还是 callablebond
#     # if bond_type =='FixedRateBond':
#     # mFixedRateBond = bond.getHandler()
#     product_type1 = mcp_module.ProductType_CASH_RATES
#     if product_type == 'CASH_RATES':
#         product_type1 = mcp_module.ProductType_CASH_RATES
#
#     print("\n[4] Creating BondAdapter...")
#     try:
#         bond_adapter = mcp_module.MBondAdapter(
#             bond,
#             instrument_id,
#             trade_id,
#             product_type1
#         )
#         print("    [OK] BondAdapter created")
#
#         print("\n[5] Setting valuation curve...")
#         try:
#             # 适配器方法现在接受原始指针（YieldCurve*）
#             # Python 包装类（MSwapCurve、MBondCurve 等）使用 getHandler() 获取原始指针
#             if valuation_curve is not None:
#                 if hasattr(valuation_curve, 'getHandler'):
#                     curve_ptr = valuation_curve.getHandler()
#                     bond_adapter.setValuationCurve(curve_ptr)
#                 else:
#                     # 如果已经是原始指针，直接传递
#                     bond_adapter.setValuationCurve(valuation_curve)
#                 print("    [OK] Valuation curve set")
#         except Exception as e:
#             print(f"    [ERROR] Failed to set valuation curve: {e}")
#             print(f"    [WARNING] Continuing without valuation curve (some metrics may not be available)")
#
#             # 5.1. 设置基准曲线（用于GSpread计算）
#             print("\n[5.1] Setting benchmark curve...")
#             try:
#                 # 适配器方法现在接受原始指针
#                 if benchmark_curve is not None:
#                     if hasattr(benchmark_curve, 'getHandler'):
#                         benchmark_curve_ptr = benchmark_curve.getHandler()  # 使用相同曲线作为基准
#                         bond_adapter.SetBenchmarkCurve(benchmark_curve_ptr)
#                         print("    [OK] Benchmark curve set")
#                     else:
#                         bond_adapter.SetBenchmarkCurve(benchmark_curve)
#                         print("    [OK] Benchmark curve set")
#             except Exception as e:
#                 print(f"    [WARNING] Failed to set benchmark curve: {e}")
#
#             # 5.2. 设置互换曲线（用于ISpread计算）
#             print("\n[5.2] Setting swap curve...")
#             try:
#                 # 适配器方法现在接受原始指针
#                 if swap_curve is not None:
#                     if hasattr(swap_curve, 'getHandler'):
#                         swap_curve_ptr = swap_curve.getHandler()  # 使用相同曲线作为互换曲线
#                         bond_adapter.SetSwapCurve(swap_curve_ptr)
#                         print("    [OK] Swap curve set")
#                     else:
#                         bond_adapter.SetSwapCurve(swap_curve)
#                         print("    [OK] Swap curve set")
#             except Exception as e:
#                 print(f"    [WARNING] Failed to set swap curve: {e}")
#
#             # 5.3. 设置信用利差曲线（用于CS01计算）
#             print("\n[5.3] Setting spread curve...")
#             try:
#                 if spread_curve is not None:
#                     if hasattr(mcp_module, "CreateBondSpreadCurve"):
#                         spread_curve_ptr = mcp_module.CreateBondSpreadCurve(reference_date, spread_curve)
#                         if spread_curve_ptr:
#                             # 适配器方法现在接受原始指针
#                             if hasattr(spread_curve_ptr, 'getHandler'):
#                                 bond_adapter.SetSpreadCurve(spread_curve_ptr.getHandler())
#                             else:
#                                 bond_adapter.SetSpreadCurve(spread_curve_ptr)
#                             print("    [OK] Spread curve set")
#                         else:
#                             print("    [WARNING] Failed to create spread curve (returned None)")
#                     else:
#                         print("    [WARNING] CreateBondSpreadCurve not available, skipping spread curve")
#             except Exception as e:
#                 print(f"    [WARNING] Failed to set spread curve: {e}")
#
#             # 5.4. 设置信用曲线（用于信用风险指标计算）
#             print("\n[5.4] Setting credit curve...")
#             try:
#                 if credit_curve is not None:
#                     if hasattr(mcp_module, "CreateCreditCurve"):
#                         credit_curve_ptr = mcp_module.CreateCreditCurve(reference_date, credit_curve)
#                         if credit_curve_ptr:
#                             # 适配器方法现在接受原始指针
#                             if hasattr(credit_curve_ptr, 'getHandler'):
#                                 bond_adapter.SetCreditCurve(credit_curve_ptr.getHandler())
#                             else:
#                                 bond_adapter.SetCreditCurve(credit_curve_ptr)
#                             print("    [OK] Credit curve set")
#                         else:
#                             print("    [WARNING] Failed to create credit curve (returned None)")
#                     else:
#                         print("    [WARNING] CreateCreditCurve not available, skipping credit curve")
#             except Exception as e:
#                 print(f"    [WARNING] Failed to set credit curve: {e}")
#
#     except Exception as e:
#         print(f"    [ERROR] Failed to create BondAdapter: {e}")
#         import traceback
#         traceback.print_exc()
#         return 'Failed to create BondAdapter'
#     # _object_refs['adapters'].append(bond_adapter)
#     return bond_adapter


def _metrics_to_dict(metrics: List[Any]) -> List[Dict[str, Any]]:
    """将指标列表转换为字典列表"""
    result = []
    for metric in metrics:
        try:
            result.append({
                'metric_type': get_metric_name(metric),
                'bucket_key': str(metric.bucket_key) if hasattr(metric, 'bucket_key') else "",
                'value': metric.value if hasattr(metric, 'value') else 0.0,
                'currency': str(metric.currency) if hasattr(metric, 'currency') else "",
                'unit': str(metric.unit) if hasattr(metric, 'unit') else "",
                'schema': str(metric.schema) if hasattr(metric, 'schema') else "",
                'description': str(metric.description) if hasattr(metric, 'description') else ""
            })
        except Exception as e:
            print(f"[WARNING] 转换指标失败: {e}")
            result.append({
                'metric_type': "ERROR",
                'bucket_key': "",
                'value': 0.0,
                'currency': "",
                'unit': "",
                'schema': "",
                'description': ""
            })
    return result


def cashflows_to_dict(cashflows: List[Any]) -> List[Dict[str, Any]]:
    """
    将现金流列表转换为字典列表（替代原print_cashflows的打印功能，返回结构化数据）

    Args:
        cashflows: 嵌套的现金流列表，外层是Leg，内层是单个现金流对象

    Returns:
        List[Dict]: 结构化的现金流字典列表，每个字典包含Leg编号和现金流详情
    """
    result = []
    # 处理空输入，和_metrics_to_dict保持一致的空值返回逻辑
    if not cashflows or len(cashflows) == 0:
        return result

    try:
        for leg_idx, leg in enumerate(cashflows):
            # 遍历每个Leg下的现金流
            for cf in leg:
                # 安全获取每个属性，缺失则返回默认值（和_metrics_to_dict风格一致）
                cashflow_dict = {
                    'leg_index': leg_idx + 1,  # Leg编号从1开始
                    'payment_date': str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                    'amount': float(cf.amount) if (
                            hasattr(cf, 'amount') and isinstance(cf.amount, (int, float))) else 0.0,
                    'flow_type': str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                    'discount_factor': float(cf.discount_factor) if (
                            hasattr(cf, 'discount_factor') and isinstance(cf.discount_factor,
                                                                          (int, float))) else 0.0,
                    'present_value': float(cf.present_value) if (
                            hasattr(cf, 'present_value') and isinstance(cf.present_value, (int, float))) else 0.0
                }
                result.append(cashflow_dict)
    except Exception as e:
        # 异常处理逻辑和_metrics_to_dict保持一致，打印警告并返回空列表/错误字典
        print(f"[WARNING] 转换现金流为字典失败: {e}")
        # 可选：如果需要记录错误项，可以追加错误字典
        # result.append({
        #     'leg_index': 0,
        #     'payment_date': "ERROR",
        #     'amount': 0.0,
        #     'flow_type': "ERROR",
        #     'discount_factor': 0.0,
        #     'present_value': 0.0
        # })

    return result


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond", "object")
# @xl_arg("instrument_id", "str")
# @xl_arg("trade_id", "str")
# @xl_arg("valuation_curve", "object")
# @xl_arg("benchmark_curve", "object")
# @xl_arg("swap_curve", "object")
# def McpBondAdapter1(bond, instrument_id='BOND_001', trade_id='TRADE_BOND_001',
#                     valuation_curve=None, benchmark_curve=None, swap_curve=None):
#     mFixedRateBond = bond.getInstance()
#     print("\n[4] Creating BondAdapter...")
#     try:
#         bond_adapter = mcp_module.MBondAdapter(
#             mFixedRateBond,
#             instrument_id,
#             trade_id,
#             1
#         )
#         print("    [OK] BondAdapter created")
#
#         bond_adapter.setValuationCurve(valuation_curve)
#         bond_adapter.SetBenchmarkCurve(benchmark_curve)
#         bond_adapter.SetSwapCurve(swap_curve)
#     except Exception as e:
#         print(f"    [ERROR] Failed to create BondAdapter: {e}")
#         import traceback
#         traceback.print_exc()
#         return 'Failed to create BondAdapter'
#     return bond_adapter
#

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCommodityFutureAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpCommodityFutureAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCommodityFutureAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpCommodityFutureAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpCommodityFutureAdapter' not in tool_def.item_dict:
            error_msg = "McpCommodityFutureAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1-args5 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCommodityFutureAdapter')
    except Exception as e:
        error_msg = f"McpCommodityFutureAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpVanillaSwapAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpVanillaSwapAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpVanillaSwapAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        # 检查 key 是否存在，如果不存在尝试刷新
        if 'McpVanillaSwapAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpVanillaSwapAdapter' not in tool_def.item_dict:
            error_msg = "McpVanillaSwapAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        # 将 args1-args5 和 fmt 组合成参数列表
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpVanillaSwapAdapter')
    except Exception as e:
        error_msg = f"McpVanillaSwapAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpXCurrencySwapAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpXCurrencySwapAdapter 对象（货币互换适配器）

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpXCurrencySwapAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpXCurrencySwapAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpXCurrencySwapAdapter' not in tool_def.item_dict:
            error_msg = "McpXCurrencySwapAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpXCurrencySwapAdapter')
    except Exception as e:
        error_msg = f"McpXCurrencySwapAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpRepoAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpRepoAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpRepoAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpRepoAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpRepoAdapter' not in tool_def.item_dict:
            error_msg = "McpRepoAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpRepoAdapter')
    except Exception as e:
        error_msg = f"McpRepoAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpLoanAndDeposAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpLoanAndDeposAdapter 对象（存款/拆借适配器）

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpLoanAndDeposAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpLoanAndDeposAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpLoanAndDeposAdapter' not in tool_def.item_dict:
            error_msg = "McpLoanAndDeposAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpLoanAndDeposAdapter')
    except Exception as e:
        error_msg = f"McpLoanAndDeposAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFRAAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpFRAAdapter 对象（远期利率协议适配器）

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFRAAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpFRAAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFRAAdapter' not in tool_def.item_dict:
            error_msg = "McpFRAAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFRAAdapter')
    except Exception as e:
        error_msg = f"McpFRAAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondLendingAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBondLendingAdapter 对象（债券借贷适配器）

    参数:
        args1: 参数数组（二维数组），含 ReferenceDate, StartDate, EndDate, BondMaturityDate,
               BondCouponRate, BondFrequency, Notional, LendingFeeRate, UnderlyingDirtyPrice,
               ValuationCurve, DiscountCurve 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBondLendingAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        if 'McpBondLendingAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpBondLendingAdapter' not in tool_def.item_dict:
            return "McpBondLendingAdapter: Invalid key. Please restart Excel."
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBondLendingAdapter')
    except Exception as e:
        return f"McpBondLendingAdapter except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCommodityLendingAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpCommodityLendingAdapter 对象（商品借贷适配器）

    参数:
        args1: 参数数组（二维数组），含 Underlying, ReferenceDate, StartDate, EndDate,
               Notional, LendingFeeRate, CommodityPrice, DiscountCurve 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCommodityLendingAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        if 'McpCommodityLendingAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpCommodityLendingAdapter' not in tool_def.item_dict:
            return "McpCommodityLendingAdapter: Invalid key. Please restart Excel."
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCommodityLendingAdapter')
    except Exception as e:
        return f"McpCommodityLendingAdapter except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpWMProductAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpWMProductAdapter 对象（理财适配器）

    参数:
        args1: 参数数组（二维数组），含 FundAdapter
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpWMProductAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        if 'McpWMProductAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpWMProductAdapter' not in tool_def.item_dict:
            return "McpWMProductAdapter: Invalid key. Please restart Excel."
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpWMProductAdapter')
    except Exception as e:
        return f"McpWMProductAdapter except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBillDiscountAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBillDiscountAdapter 对象（票据贴现适配器）

    参数:
        args1: 参数数组（二维数组），含 ValuationDate, StartDate, MaturityDate, Notional 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBillDiscountAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        if 'McpBillDiscountAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpBillDiscountAdapter' not in tool_def.item_dict:
            return "McpBillDiscountAdapter: Invalid key. Please restart Excel."
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBillDiscountAdapter')
    except Exception as e:
        return f"McpBillDiscountAdapter except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBillRepoAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBillRepoAdapter 对象（票据回购适配器）

    参数:
        args1: 参数数组（二维数组），含 ValuationDate, StartDate, EndDate, Notional, RepoRate 等
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBillRepoAdapter 对象
    """
    if tool_def is None:
        return "tool_def not available"
    try:
        if 'McpBillRepoAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpBillRepoAdapter' not in tool_def.item_dict:
            return "McpBillRepoAdapter: Invalid key. Please restart Excel."
        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBillRepoAdapter')
    except Exception as e:
        return f"McpBillRepoAdapter except: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBasisSwapAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBasisSwapAdapter 对象（基差互换适配器）

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBasisSwapAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpBasisSwapAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpBasisSwapAdapter' not in tool_def.item_dict:
            error_msg = "McpBasisSwapAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBasisSwapAdapter')
    except Exception as e:
        error_msg = f"McpBasisSwapAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondForwardAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBondForwardAdapter 对象（债券远期适配器）

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBondForwardAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpBondForwardAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpBondForwardAdapter' not in tool_def.item_dict:
            error_msg = "McpBondForwardAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBondForwardAdapter')
    except Exception as e:
        error_msg = f"McpBondForwardAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFundAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpFundAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFundAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpFundAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFundAdapter' not in tool_def.item_dict:
            error_msg = "McpFundAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFundAdapter')
    except Exception as e:
        error_msg = f"McpFundAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXNDFAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpFXNDFAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXNDFAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpFXNDFAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFXNDFAdapter' not in tool_def.item_dict:
            error_msg = "McpFXNDFAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXNDFAdapter')
    except Exception as e:
        error_msg = f"McpFXNDFAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForwardSwapAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpFXForwardSwapAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXForwardSwapAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpFXForwardSwapAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFXForwardSwapAdapter' not in tool_def.item_dict:
            error_msg = "McpFXForwardSwapAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXForwardSwapAdapter')
    except Exception as e:
        error_msg = f"McpFXForwardSwapAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXOptionsAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpFXOptionsAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpFXOptionsAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpFXOptionsAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpFXOptionsAdapter' not in tool_def.item_dict:
            error_msg = "McpFXOptionsAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpFXOptionsAdapter')
    except Exception as e:
        error_msg = f"McpFXOptionsAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpStructuredDerivativeProductAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpStructuredDerivativeProductAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpStructuredDerivativeProductAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpStructuredDerivativeProductAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpStructuredDerivativeProductAdapter' not in tool_def.item_dict:
            error_msg = "McpStructuredDerivativeProductAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpStructuredDerivativeProductAdapter')
    except Exception as e:
        error_msg = f"McpStructuredDerivativeProductAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEquitySpotAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpEquitySpotAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpEquitySpotAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpEquitySpotAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpEquitySpotAdapter' not in tool_def.item_dict:
            error_msg = "McpEquitySpotAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpEquitySpotAdapter')
    except Exception as e:
        error_msg = f"McpEquitySpotAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEquityFutureAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpEquityFutureAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpEquityFutureAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpEquityFutureAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpEquityFutureAdapter' not in tool_def.item_dict:
            error_msg = "McpEquityFutureAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpEquityFutureAdapter')
    except Exception as e:
        error_msg = f"McpEquityFutureAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpBondFutureAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBondFutureAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBondFutureAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpBondFutureAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpBondFutureAdapter' not in tool_def.item_dict:
            error_msg = "McpBondFutureAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBondFutureAdapter')
    except Exception as e:
        error_msg = f"McpBondFutureAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


# 必须声明返回 : object，否则 PyXLL 无法把 Python 实例放入对象缓存，单元格会退化成类名字符串（如 "McpBondAdapter"），
# adapterMetric 也会因收到 str 而报「adapter 创建失败」。写法对齐 pyxll_func/core/mcp_calendar.py 的 McpCalendar。
#
# 重要：声明 : object 时，若用 return 返回 str（错误提示），PyXLL 会把该 str 当作对象句柄显示为 str@1，无法区分成功/失败。
# 因此错误路径一律 raise，让 Excel 显示具体异常信息；成功路径只返回 mcp.wrapper.McpBondAdapter 实例（显示为 McpBondAdapter@n）。
@xl_func(
    "var[][] args1, var[][] args2, var[][] args3, var[][] args4, var[][] args5, str fmt: object",
    macro=False,
    recalc_on_open=True,
)
def McpBondAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpBondAdapter 对象

    参数:
        args1: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpBondAdapter 对象
    """
    if tool_def is None:
        raise RuntimeError("tool_def not available")

    try:
        if 'McpBondAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except Exception:
                pass
        if 'McpBondAdapter' not in tool_def.item_dict:
            raise RuntimeError("McpBondAdapter: Invalid key. Please restart Excel.")

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpBondAdapter')
    except Exception as e:
        print(f"args1: {args1}, fmt: {fmt}")
        print(f"McpBondAdapter except: {e}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"McpBondAdapter except: {e}") from e


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpEquityOptionAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpEquityOptionAdapter 对象

    参数:
        args1~args5: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpEquityOptionAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpEquityOptionAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpEquityOptionAdapter' not in tool_def.item_dict:
            error_msg = "McpEquityOptionAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpEquityOptionAdapter')
    except Exception as e:
        error_msg = f"McpEquityOptionAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpCommodityOptionAdapter(args1, args2=None, args3=None, args4=None, args5=None, fmt='VP'):
    """
    创建 McpCommodityOptionAdapter 对象

    参数:
        args1~args5: 参数数组（二维数组）
        fmt: 参数格式，默认 'VP'（纵向格式）

    返回:
        McpCommodityOptionAdapter 对象
    """
    if tool_def is None:
        error_msg = "tool_def not available"
        print(error_msg)
        return error_msg

    try:
        if 'McpCommodityOptionAdapter' not in tool_def.item_dict:
            try:
                tool_def.generate_key_word_dict()
            except:
                pass
        if 'McpCommodityOptionAdapter' not in tool_def.item_dict:
            error_msg = "McpCommodityOptionAdapter: Invalid key. Please restart Excel."
            print(error_msg)
            return error_msg

        args = [args1, args2, args3, args4, args5, fmt]
        return tool_def.xls_create(*args, key='McpCommodityOptionAdapter')
    except Exception as e:
        error_msg = f"McpCommodityOptionAdapter except: {e}"
        print(f"args1: {args1}, fmt: {fmt}")
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg


def _flatten_metrics_list(metrics_list: List[Dict[str, Any]]) -> List[List[Any]]:
    """
    将 List[Dict[str, Any]] 扁平化为Excel可平铺的二维列表
    :param metrics_list: 待扁平化的指标列表
    :return: 二维列表（首行为字段名，后续行为数据）
    """
    if not metrics_list:  # 空列表直接返回空二维列表
        return []

    # 提取所有字段名（取第一个字典的键作为表头，确保字段一致性）
    header = list(metrics_list[0].keys())
    # 初始化扁平化结果，先加入表头
    flattened_data = [header]

    # 遍历每个字典，按表头顺序提取对应值，组成数据行
    for metric_dict in metrics_list:
        data_row = []
        for field in header:
            # 若字典中不存在该字段，填充空值，避免报错
            value = metric_dict.get(field, "")
            # 将 None 值转换为空字符串，避免 Excel 显示 #N/A
            if value is None:
                value = ""
            data_row.append(value)
        flattened_data.append(data_row)

    return flattened_data


def _transpose_flattened_data(flattened_data: List[List[Any]]) -> List[List[Any]]:
    """
    将纵向格式的数据转置为横向格式

    :param flattened_data: 纵向格式的二维列表（首行为表头，后续行为数据）
    :return: 横向格式的二维列表（第一列为字段名，后续列为数据）
    """
    if not flattened_data or len(flattened_data) <= 1:
        # 如果为空或只有表头，返回原数据
        return flattened_data

    # 提取表头
    header = flattened_data[0]
    # 提取数据行
    data_rows = flattened_data[1:]

    # 转置：第一列为字段名，后续列为数据
    transposed = []
    for col_idx in range(len(header)):
        col_data = [header[col_idx]]  # 第一行是该列的字段名
        # 遍历所有数据行，提取该列的值
        for row in data_rows:
            if col_idx < len(row):
                value = row[col_idx]
                # 将 None 值转换为空字符串，避免 Excel 显示 #N/A
                if value is None:
                    value = ""
                col_data.append(value)
            else:
                col_data.append("")  # 如果该行缺少该列，填充空值
        transposed.append(col_data)

    return transposed


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("bond_adapters", "var[]")
def McpBondPortfolioAdapter(portfolio_key, portfolio_name, bond_adapters):
    bond_portfolio_adapter = mcp_module.BondPortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in bond_adapters:
        bond_portfolio_adapter.addBond(item)
    return bond_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpEquityPortfolioAdapter(portfolio_key, portfolio_name, adapters):
    equity_portfolio_adapter = mcp_module.EquityPortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        equity_portfolio_adapter.addStock(item)
    return equity_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpOptionPortfolioAdapter(portfolio_key, portfolio_name, adapters):
    option_portfolio_adapter = mcp_module.OptionPortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        option_portfolio_adapter.addOption(item)
    return option_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpFundPortfolioAdapter(portfolio_key, portfolio_name, adapters):
    fund_portfolio_adapter = mcp_module.FundPortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        fund_portfolio_adapter.addFund(item)
    return fund_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpFuturePortfolioAdapter(portfolio_key, portfolio_name, adapters):
    fund_portfolio_adapter = mcp_module.FuturePortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        fund_portfolio_adapter.addFutureInstrument(item)
    return fund_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpFXPortfolioAdapter(portfolio_key, portfolio_name, adapters):
    fund_portfolio_adapter = mcp_module.FXPortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        fund_portfolio_adapter.addFXInstrument(item)
    return fund_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolio_key", "str")
@xl_arg("portfolio_name", "str")
@xl_arg("adapters", "var[]")
def McpRatePortfolioAdapter(portfolio_key, portfolio_name, adapters):
    fund_portfolio_adapter = mcp_module.RatePortfolioAdapter(
        portfolio_key,
        portfolio_name
    )
    for item in adapters:
        fund_portfolio_adapter.addRateInstrument(item)
    return fund_portfolio_adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolioAdapter", "var[]")
def McpHierarchicalPortfolioManager(portfolioAdapter):
    manager = mcp_module.HierarchicalPortfolioManager()
    for item in portfolioAdapter:
        manager.addPortfolioAdapter(item)
    return manager


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("metric", "str")
@xl_arg("orientation", "str")
def PortMetrics(adapter, metric=None, orientation='VL'):
    """
    获取适配器的指标数据（集合输出）

    参数:
        adapter: 适配器对象
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，返回所有指标
        orientation: 展示方向，'VL'/'vertical' 为纵向（默认），'HL'/'horizontal' 为横向

    返回:
        返回二维列表（根据 orientation 决定纵向或横向格式）
    """
    metrics = {}
    try:
        if hasattr(adapter, "calculateValuationMetrics"):
            valuation_metrics = adapter.calculateValuationMetrics()
            metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
    try:
        if hasattr(adapter, "calculateRiskMetrics"):
            risk_metrics = adapter.calculateRiskMetrics()
            metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
    try:
        if hasattr(adapter, "calculateAttributionMetrics"):
            attribution_metrics = adapter.calculateAttributionMetrics()
            metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")

    try:
        if hasattr(adapter, "calculateCarryMetrics"):
            carry_metrics = adapter.calculateCarryMetrics()
            metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")
    try:
        if hasattr(adapter, "calculateCreditRiskMetrics"):
            credit_risk_metrics = adapter.calculateCreditRiskMetrics()
            metrics['credit_risk_metrics'] = _metrics_to_dict(credit_risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCreditRiskMetrics: {e}")
    try:
        if hasattr(adapter, "calculateCampisiAttribution"):
            campisi_metrics = adapter.calculateCampisiAttribution()
            metrics['campisi_metrics'] = _metrics_to_dict(campisi_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCampisiAttribution: {e}")
    try:
        if hasattr(adapter, "calculateKRDMetrics"):
            krd_metrics = adapter.calculateKRDMetrics()
            metrics['krd_metrics'] = _metrics_to_dict(krd_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateKRDMetrics: {e}")

    try:
        if hasattr(adapter, "calculateCashflows"):
            cashflows = adapter.calculateCashflows(useYieldCurve=True)
            metrics['cashflows'] = cashflows_to_dict(cashflows)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCashflows: {e}")

    # 根据 orientation 决定纵向或横向格式
    orientation_upper = orientation.upper() if orientation else 'VL'

    if metric is None:
        # 返回所有指标类型，带分组标题
        all_flattened = []
        # 按原始指标类型分组返回
        # 首先确定表头的列数（从第一个非空的指标列表获取）
        header_length = 0
        for metric_type, metric_list in metrics.items():
            if metric_list:
                flattened = _flatten_metrics_list(metric_list)
                if flattened:
                    header_length = len(flattened[0])  # 第一行是表头
                    break

        for metric_type, metric_list in metrics.items():
            # 添加指标类型作为分组标题（填充到与表头相同的列数）
            header_row = [f"=== {metric_type} ==="] + [""] * (header_length - 1) if header_length > 0 else [
                f"=== {metric_type} ==="]
            all_flattened.append(header_row)
            # 扁平化当前指标类型的数据并加入
            flattened = _flatten_metrics_list(metric_list)
            if flattened:
                all_flattened.extend(flattened)
                # 更新 header_length（以防后续的 metric_list 有更多列）
                if len(flattened[0]) > header_length:
                    header_length = len(flattened[0])
            # 添加空行分隔不同指标类型（填充到与表头相同的列数）
            empty_row = [""] * header_length if header_length > 0 else [""]
            all_flattened.append(empty_row)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            if all_flattened:
                return _transpose_flattened_data(all_flattened)
        return all_flattened
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return [[f"无效指标名！可选指标：{list(metrics.keys())}"]]

        # 返回指定 metric 的数据
        target_metrics_list = metrics[metric]
        flattened_metrics = _flatten_metrics_list(target_metrics_list)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            return _transpose_flattened_data(flattened_metrics)
        else:
            return flattened_metrics


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("metric", "str")
@xl_arg("metric_name", "str")
@xl_arg("bucket_key", "str")
@xl_arg("currency", "str")
@xl_arg("schema", "str")
def PortMetricsValue(adapter, metric=None, metric_name=None, bucket_key=None, currency=None, schema=None):
    """
    获取适配器的指标 value 值

    参数:
        adapter: 适配器对象
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，从所有指标中查找
        metric_name: 指标名称（可选），匹配 metric_type 字段
        bucket_key: bucket_key匹配（可选），匹配 bucket_key 字段
        currency: 货币匹配（可选），匹配 currency 字段
        schema: schema匹配（可选），匹配 schema 字段

    返回:
        如果只有一个匹配的 value: 返回该值（保持原类型）
        如果有多个匹配的 value: 返回逗号分隔的字符串
        如果没有匹配的记录: 返回空字符串
    """
    metrics = {}
    try:
        if hasattr(adapter, "calculateValuationMetrics"):
            valuation_metrics = adapter.calculateValuationMetrics()
            metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
    try:
        if hasattr(adapter, "calculateRiskMetrics"):
            risk_metrics = adapter.calculateRiskMetrics()
            metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
    try:
        if hasattr(adapter, "calculateAttributionMetrics"):
            attribution_metrics = adapter.calculateAttributionMetrics()
            metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")

    try:
        if hasattr(adapter, "calculateCarryMetrics"):
            carry_metrics = adapter.calculateCarryMetrics()
            metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")
    try:
        if hasattr(adapter, "calculateCreditRiskMetrics"):
            credit_risk_metrics = adapter.calculateCreditRiskMetrics()
            metrics['credit_risk_metrics'] = _metrics_to_dict(credit_risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCreditRiskMetrics: {e}")
    try:
        if hasattr(adapter, "calculateCampisiAttribution"):
            campisi_metrics = adapter.calculateCampisiAttribution()
            metrics['campisi_metrics'] = _metrics_to_dict(campisi_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCampisiAttribution: {e}")
    try:
        if hasattr(adapter, "calculateKRDMetrics"):
            krd_metrics = adapter.calculateKRDMetrics()
            metrics['krd_metrics'] = _metrics_to_dict(krd_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateKRDMetrics: {e}")

    try:
        if hasattr(adapter, "calculateCashflows"):
            cashflows = adapter.calculateCashflows(useYieldCurve=True)
            metrics['cashflows'] = cashflows_to_dict(cashflows)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCashflows: {e}")

    # 过滤指标数据
    target_metrics_list = []

    if metric is None:
        # 如果未指定 metric，收集所有指标类型的数据
        for metric_type, metric_list in metrics.items():
            target_metrics_list.extend(metric_list)
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return ""
        target_metrics_list = metrics[metric]

    # 如果提供了 metric_name，进一步过滤 metric_type 字段
    if metric_name is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if m.get('metric_type', '') == metric_name
        ]

    # 如果提供了 bucket_key，进一步过滤
    if bucket_key is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if bucket_key.lower() in str(m.get('bucket_key', '')).lower()
        ]

    # 如果提供了 currency，进一步过滤
    if currency is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if currency.lower() in str(m.get('currency', '')).lower()
        ]

    # 如果提供了 schema，进一步过滤
    if schema is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if schema.lower() in str(m.get('schema', '')).lower()
        ]

    # 收集所有匹配的 value 值
    values = []
    for metric_dict in target_metrics_list:
        value = metric_dict.get('value')
        if value is not None:
            values.append(value)

    # 根据 value 数量返回
    if len(values) == 0:
        return ""
    elif len(values) == 1:
        return values[0]
    else:
        # 多个 value，用逗号分隔
        return ",".join(str(v) for v in values)


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("adapter", "object")
# @xl_arg("metric", "str")
# @xl_arg("metric_name", "str")
# @xl_arg("bucket_key", "str")
# @xl_arg("orientation", "str")
# def PortMetrics(adapter, metric=None, metric_name=None, bucket_key=None, orientation='VL'):
#     """
#     获取适配器的指标数据
#
#     参数:
#         adapter: 适配器对象
#         metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，返回所有指标
#         orientation: 展示方向，'VL'/'vertical' 为纵向（默认），'HL'/'horizontal' 为横向
#         metric_name: 指标名称（可选），当指定了 metric 时，进一步过滤 metric_type 字段匹配的数据
#         bucket_key: bucket_key匹配（可选），用于匹配 bucket_key 字段，返回第一个匹配的 value 值（单个值）
#
#     返回:
#         如果提供了 bucket_key: 返回单个值（第一个匹配的 value）
#         如果提供了 metric_name 且只有一条数据且 bucket_key 为空: 返回单个 value
#         否则: 返回二维列表（根据 orientation 决定纵向或横向格式）
#     """
#     metrics = {}
#     try:
#         if hasattr(adapter, "calculateValuationMetrics"):
#             valuation_metrics = adapter.calculateValuationMetrics()
#             metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateRiskMetrics"):
#             risk_metrics = adapter.calculateRiskMetrics()
#             metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateAttributionMetrics"):
#             attribution_metrics = adapter.calculateAttributionMetrics()
#             metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")
#
#     try:
#         if hasattr(adapter, "calculateCarryMetrics"):
#             carry_metrics = adapter.calculateCarryMetrics()
#             metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateCreditRiskMetrics"):
#             credit_risk_metrics = adapter.calculateCreditRiskMetrics()
#             metrics['credit_risk_metrics'] = _metrics_to_dict(credit_risk_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCreditRiskMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateCampisiAttribution"):
#             campisi_metrics = adapter.calculateCampisiAttribution()
#             metrics['campisi_metrics'] = _metrics_to_dict(campisi_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCampisiAttribution: {e}")
#     try:
#         if hasattr(adapter, "calculateKRDMetrics"):
#             krd_metrics = adapter.calculateKRDMetrics()
#             metrics['krd_metrics'] = _metrics_to_dict(krd_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateKRDMetrics: {e}")
#
#     try:
#         if hasattr(adapter, "calculateCashflows"):
#             cashflows = adapter.calculateCashflows(useYieldCurve=True)
#             metrics['cashflows'] = cashflows_to_dict(cashflows)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCashflows: {e}")
#
#     # 过滤指标数据
#     target_metrics_list = []
#
#     if metric is None:
#         # 如果未指定 metric，收集所有指标类型的数据
#         for metric_type, metric_list in metrics.items():
#             target_metrics_list.extend(metric_list)
#     else:
#         # 如果指定了 metric，先校验有效性
#         if metric not in metrics:
#             return [[f"无效指标名！可选指标：{list(metrics.keys())}"]]
#         target_metrics_list = metrics[metric]
#
#     # 如果提供了 metric_name，进一步过滤 metric_type 字段
#     if metric_name is not None:
#         target_metrics_list = [
#             m for m in target_metrics_list
#             if m.get('metric_type', '') == metric_name
#         ]
#         # 如果只有一条数据并且 bucket_key 为空，只返回 value 字段
#         if len(target_metrics_list) == 1:
#             metric_dict = target_metrics_list[0]
#             bucket_key_value = metric_dict.get('bucket_key', '')
#             if not bucket_key_value or bucket_key_value == "":
#                 return metric_dict.get('value', 0.0)
#
#     # 如果提供了 bucket_key 参数，查找匹配的记录并返回 value
#     if bucket_key is not None:
#         for metric_dict in target_metrics_list:
#             metric_bucket_key = metric_dict.get('bucket_key', '')
#             # 支持包含匹配（不区分大小写）
#             if bucket_key.lower() in str(metric_bucket_key).lower():
#                 return metric_dict.get('value', 0.0)
#         # 如果没有匹配到，返回错误信息
#         return f"未找到匹配 bucket_key='{bucket_key}' 的记录"
#
#     # 如果没有提供 bucket_key，返回平铺的二维列表
#     # 根据 orientation 决定纵向或横向格式
#     orientation_upper = orientation.upper() if orientation else 'VL'
#
#     if metric is None:
#         # 返回所有指标类型，带分组标题
#         all_flattened = []
#         # 按原始指标类型分组返回
#         if metric_name is None:
#             # 如果未指定 metric_name，按原始分组返回
#             # 首先确定表头的列数（从第一个非空的指标列表获取）
#             header_length = 0
#             for metric_type, metric_list in metrics.items():
#                 if metric_list:
#                     flattened = _flatten_metrics_list(metric_list)
#                     if flattened:
#                         header_length = len(flattened[0])  # 第一行是表头
#                         break
#
#             for metric_type, metric_list in metrics.items():
#                 # 添加指标类型作为分组标题（填充到与表头相同的列数）
#                 header_row = [f"=== {metric_type} ==="] + [""] * (header_length - 1) if header_length > 0 else [
#                     f"=== {metric_type} ==="]
#                 all_flattened.append(header_row)
#                 # 扁平化当前指标类型的数据并加入
#                 flattened = _flatten_metrics_list(metric_list)
#                 if flattened:
#                     all_flattened.extend(flattened)
#                     # 更新 header_length（以防后续的 metric_list 有更多列）
#                     if len(flattened[0]) > header_length:
#                         header_length = len(flattened[0])
#                 # 添加空行分隔不同指标类型（填充到与表头相同的列数）
#                 empty_row = [""] * header_length if header_length > 0 else [""]
#                 all_flattened.append(empty_row)
#         else:
#             # 如果指定了 metric_name，只返回匹配的数据（不再分组）
#             flattened = _flatten_metrics_list(target_metrics_list)
#             if flattened:
#                 all_flattened.extend(flattened)
#
#         # 根据 orientation 决定是否转置
#         if orientation_upper in ('HL', 'HORIZONTAL'):
#             # 对于横向格式，需要对整个结果进行转置
#             # 但由于包含分组标题，转置比较复杂，这里先简单处理：如果有数据就转置最后一部分
#             if all_flattened:
#                 return _transpose_flattened_data(all_flattened)
#         return all_flattened
#     else:
#         # 返回指定 metric 的数据
#         flattened_metrics = _flatten_metrics_list(target_metrics_list)
#
#         # 根据 orientation 决定是否转置
#         if orientation_upper in ('HL', 'HORIZONTAL'):
#             return _transpose_flattened_data(flattened_metrics)
#         else:
#             return flattened_metrics


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("adapter", "object")
# @xl_arg("metric", "str")
# @xl_arg("metric_name", "str")
# @xl_arg("bucket_key", "str")
# @xl_arg("orientation", "str")
# def PortMetrics(adapter, metric=None, metric_name=None, bucket_key=None, orientation='VL'):
#     """
#     获取适配器的指标数据
#
#     参数:
#         adapter: 适配器对象
#         metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，返回所有指标
#         orientation: 展示方向，'VL'/'vertical' 为纵向（默认），'HL'/'horizontal' 为横向
#         metric_name: 指标名称（可选），当指定了 metric 时，进一步过滤 metric_type 字段匹配的数据
#         bucket_key: bucket_key匹配（可选），用于匹配 bucket_key 字段，返回第一个匹配的 value 值（单个值）
#
#     返回:
#         如果提供了 bucket_key: 返回单个值（第一个匹配的 value）
#         如果提供了 metric_name 且只有一条数据且 bucket_key 为空: 返回单个 value
#         否则: 返回二维列表（根据 orientation 决定纵向或横向格式）
#     """
#     metrics = {}
#     try:
#         if hasattr(adapter, "calculateValuationMetrics"):
#             valuation_metrics = adapter.calculateValuationMetrics()
#             metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateRiskMetrics"):
#             risk_metrics = adapter.calculateRiskMetrics()
#             metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateAttributionMetrics"):
#             attribution_metrics = adapter.calculateAttributionMetrics()
#             metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")
#
#     try:
#         if hasattr(adapter, "calculateCarryMetrics"):
#             carry_metrics = adapter.calculateCarryMetrics()
#             metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateCreditRiskMetrics"):
#             credit_risk_metrics = adapter.calculateCreditRiskMetrics()
#             metrics['credit_risk_metrics'] = _metrics_to_dict(credit_risk_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCreditRiskMetrics: {e}")
#     try:
#         if hasattr(adapter, "calculateCampisiAttribution"):
#             campisi_metrics = adapter.calculateCampisiAttribution()
#             metrics['campisi_metrics'] = _metrics_to_dict(campisi_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCampisiAttribution: {e}")
#     try:
#         if hasattr(adapter, "calculateKRDMetrics"):
#             krd_metrics = adapter.calculateKRDMetrics()
#             metrics['krd_metrics'] = _metrics_to_dict(krd_metrics)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateKRDMetrics: {e}")
#
#     try:
#         if hasattr(adapter, "calculateCashflows"):
#             cashflows = adapter.calculateCashflows(useYieldCurve=True)
#             metrics['cashflows'] = cashflows_to_dict(cashflows)
#     except Exception as e:
#         print(f"    [ERROR] Failed to calculateCashflows: {e}")
#
#         # 过滤指标数据
#         target_metrics_list = []
#
#         if metric is None:
#             # 如果未指定 metric，收集所有指标类型的数据
#             for metric_type, metric_list in metrics.items():
#                 target_metrics_list.extend(metric_list)
#         else:
#             # 如果指定了 metric，先校验有效性
#             if metric not in metrics:
#                 return [[f"无效指标名！可选指标：{list(metrics.keys())}"]]
#             target_metrics_list = metrics[metric]
#
#         # 如果提供了 metric_name，进一步过滤 metric_type 字段
#         if metric_name is not None:
#             target_metrics_list = [
#                 m for m in target_metrics_list
#                 if m.get('metric_type', '') == metric_name
#             ]
#             # 如果只有一条数据并且 bucket_key 为空，只返回 value 字段
#             if len(target_metrics_list) == 1:
#                 metric_dict = target_metrics_list[0]
#                 bucket_key_value = metric_dict.get('bucket_key', '')
#                 if not bucket_key_value or bucket_key_value == "":
#                     return metric_dict.get('value', 0.0)
#
#         # 如果提供了 bucket_key 参数，查找匹配的记录并返回 value
#         if bucket_key is not None:
#             for metric_dict in target_metrics_list:
#                 metric_bucket_key = metric_dict.get('bucket_key', '')
#                 # 支持包含匹配（不区分大小写）
#                 if bucket_key.lower() in str(metric_bucket_key).lower():
#                     return metric_dict.get('value', 0.0)
#             # 如果没有匹配到，返回错误信息
#             return f"未找到匹配 bucket_key='{bucket_key}' 的记录"
#
#         # 如果没有提供 bucket_key，返回平铺的二维列表
#         # 根据 orientation 决定纵向或横向格式
#         orientation_upper = orientation.upper() if orientation else 'VL'
#
#         if metric is None:
#             # 返回所有指标类型，带分组标题
#             all_flattened = []
#             # 按原始指标类型分组返回
#             if metric_name is None:
#                 # 如果未指定 metric_name，按原始分组返回
#                 # 首先确定表头的列数（从第一个非空的指标列表获取）
#                 header_length = 0
#                 for metric_type, metric_list in metrics.items():
#                     if metric_list:
#                         flattened = _flatten_metrics_list(metric_list)
#                         if flattened:
#                             header_length = len(flattened[0])  # 第一行是表头
#                             break
#
#                 for metric_type, metric_list in metrics.items():
#                     # 添加指标类型作为分组标题（填充到与表头相同的列数）
#                     header_row = [f"=== {metric_type} ==="] + [""] * (header_length - 1) if header_length > 0 else [
#                         f"=== {metric_type} ==="]
#                     all_flattened.append(header_row)
#                     # 扁平化当前指标类型的数据并加入
#                     flattened = _flatten_metrics_list(metric_list)
#                     if flattened:
#                         all_flattened.extend(flattened)
#                         # 更新 header_length（以防后续的 metric_list 有更多列）
#                         if len(flattened[0]) > header_length:
#                             header_length = len(flattened[0])
#                     # 添加空行分隔不同指标类型（填充到与表头相同的列数）
#                     empty_row = [""] * header_length if header_length > 0 else [""]
#                     all_flattened.append(empty_row)
#             else:
#                 # 如果指定了 metric_name，只返回匹配的数据（不再分组）
#                 flattened = _flatten_metrics_list(target_metrics_list)
#                 if flattened:
#                     all_flattened.extend(flattened)
#
#             # 根据 orientation 决定是否转置
#             if orientation_upper in ('HL', 'HORIZONTAL'):
#                 # 对于横向格式，需要对整个结果进行转置
#                 # 但由于包含分组标题，转置比较复杂，这里先简单处理：如果有数据就转置最后一部分
#                 if all_flattened:
#                     return _transpose_flattened_data(all_flattened)
#             return all_flattened
#         else:
#             # 返回指定 metric 的数据
#             flattened_metrics = _flatten_metrics_list(target_metrics_list)
#
#             # 根据 orientation 决定是否转置
#             if orientation_upper in ('HL', 'HORIZONTAL'):
#                 return _transpose_flattened_data(flattened_metrics)
#             else:
#                 return flattened_metrics
#

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolioAdapter", "object")
@xl_arg("metric", "str")
@xl_arg("orientation", "str")
def PortfolioMetrics(portfolioAdapter, metric=None, orientation='VL'):
    """
    获取组合适配器的指标数据（集合输出）

    参数:
        portfolioAdapter: 组合适配器对象
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，返回所有指标
        orientation: 展示方向，'VL'/'vertical' 为纵向（默认），'HL'/'horizontal' 为横向

    返回:
        返回二维列表（根据 orientation 决定纵向或横向格式）
    """
    metrics = {}
    try:
        valuation_metrics = portfolioAdapter.calculateValuationMetrics()
        metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
    try:
        risk_metrics = portfolioAdapter.calculateRiskMetrics()
        metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
    try:
        attribution_metrics = portfolioAdapter.calculateAttributionMetrics()
        metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")
    try:
        carry_metrics = portfolioAdapter.calculateCarryMetrics()
        metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")

    # 根据 orientation 决定纵向或横向格式
    orientation_upper = orientation.upper() if orientation else 'VL'

    if metric is None:
        # 返回所有指标类型，带分组标题
        all_flattened = []
        # 按原始指标类型分组返回
        # 首先确定表头的列数（从第一个非空的指标列表获取）
        header_length = 0
        for metric_type, metric_list in metrics.items():
            if metric_list:
                flattened = _flatten_metrics_list(metric_list)
                if flattened:
                    header_length = len(flattened[0])  # 第一行是表头
                    break

        for metric_type, metric_list in metrics.items():
            # 添加指标类型作为分组标题（填充到与表头相同的列数）
            header_row = [f"=== {metric_type} ==="] + [""] * (header_length - 1) if header_length > 0 else [
                f"=== {metric_type} ==="]
            all_flattened.append(header_row)
            # 扁平化当前指标类型的数据并加入
            flattened = _flatten_metrics_list(metric_list)
            if flattened:
                all_flattened.extend(flattened)
                # 更新 header_length（以防后续的 metric_list 有更多列）
                if len(flattened[0]) > header_length:
                    header_length = len(flattened[0])
            # 添加空行分隔不同指标类型（填充到与表头相同的列数）
            empty_row = [""] * header_length if header_length > 0 else [""]
            all_flattened.append(empty_row)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            if all_flattened:
                return _transpose_flattened_data(all_flattened)
        return all_flattened
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return [[f"无效指标名！可选指标：{list(metrics.keys())}"]]
        
        # 返回指定 metric 的数据
        target_metrics_list = metrics[metric]
        flattened_metrics = _flatten_metrics_list(target_metrics_list)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            return _transpose_flattened_data(flattened_metrics)
        else:
            return flattened_metrics


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("portfolioAdapter", "object")
@xl_arg("metric", "str")
@xl_arg("metric_name", "str")
@xl_arg("bucket_key", "str")
@xl_arg("currency", "str")
@xl_arg("schema", "str")
def PortfolioMetricsValue(portfolioAdapter, metric=None, metric_name=None, bucket_key=None, currency=None, schema=None):
    """
    获取组合适配器的指标 value 值

    参数:
        portfolioAdapter: 组合适配器对象
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，从所有指标中查找
        metric_name: 指标名称（可选），匹配 metric_type 字段
        bucket_key: bucket_key匹配（可选），匹配 bucket_key 字段
        currency: 货币匹配（可选），匹配 currency 字段
        schema: schema匹配（可选），匹配 schema 字段

    返回:
        如果只有一个匹配的 value: 返回该值（保持原类型）
        如果有多个匹配的 value: 返回逗号分隔的字符串
        如果没有匹配的记录: 返回空字符串
    """
    metrics = {}
    try:
        valuation_metrics = portfolioAdapter.calculateValuationMetrics()
        metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateValuationMetrics: {e}")
    try:
        risk_metrics = portfolioAdapter.calculateRiskMetrics()
        metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateRiskMetrics: {e}")
    try:
        attribution_metrics = portfolioAdapter.calculateAttributionMetrics()
        metrics['attribution_metrics'] = _metrics_to_dict(attribution_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateAttributionMetrics: {e}")
    try:
        carry_metrics = portfolioAdapter.calculateCarryMetrics()
        metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateCarryMetrics: {e}")

    # 过滤指标数据
    target_metrics_list = []

    if metric is None:
        # 如果未指定 metric，收集所有指标类型的数据
        for metric_type, metric_list in metrics.items():
            target_metrics_list.extend(metric_list)
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return ""
        target_metrics_list = metrics[metric]

    # 如果提供了 metric_name，进一步过滤 metric_type 字段
    if metric_name is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if m.get('metric_type', '') == metric_name
        ]

    # 如果提供了 bucket_key，进一步过滤
    if bucket_key is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if bucket_key.lower() in str(m.get('bucket_key', '')).lower()
        ]

    # 如果提供了 currency，进一步过滤
    if currency is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if currency.lower() in str(m.get('currency', '')).lower()
        ]

    # 如果提供了 schema，进一步过滤
    if schema is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if schema.lower() in str(m.get('schema', '')).lower()
        ]

    # 收集所有匹配的 value 值
    values = []
    for metric_dict in target_metrics_list:
        value = metric_dict.get('value')
        if value is not None:
            values.append(value)

    # 根据 value 数量返回
    if len(values) == 0:
        return ""
    elif len(values) == 1:
        return values[0]
    else:
        # 多个 value，用逗号分隔
        return ",".join(str(v) for v in values)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("hierarchical", "object")
@xl_arg("parentkey", "str")
@xl_arg("metric", "str")
@xl_arg("orientation", "str")
def PortHierarchicalMetrics(hierarchical, parentkey, metric=None, orientation='VL'):
    """
    获取分层组合管理器的指标数据（集合输出）

    参数:
        hierarchical: 分层组合管理器对象
        parentkey: 父节点键
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，返回所有指标
        orientation: 展示方向，'VL'/'vertical' 为纵向（默认），'HL'/'horizontal' 为横向

    返回:
        返回二维列表（根据 orientation 决定纵向或横向格式）
    """
    metrics = {}
    try:
        valuation_metrics = hierarchical.calculateParentValuationMetrics(parentkey)
        metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentValuationMetrics: {e}")
    try:
        risk_metrics = hierarchical.calculateParentRiskMetrics(parentkey)
        metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentRiskMetrics: {e}")
    try:
        carry_metrics = hierarchical.calculateParentCarryMetrics(parentkey)
        metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentCarryMetrics: {e}")

    # 根据 orientation 决定纵向或横向格式
    orientation_upper = orientation.upper() if orientation else 'VL'

    if metric is None:
        # 返回所有指标类型，带分组标题
        all_flattened = []
        # 按原始指标类型分组返回
        # 首先确定表头的列数（从第一个非空的指标列表获取）
        header_length = 0
        for metric_type, metric_list in metrics.items():
            if metric_list:
                flattened = _flatten_metrics_list(metric_list)
                if flattened:
                    header_length = len(flattened[0])  # 第一行是表头
                    break

        for metric_type, metric_list in metrics.items():
            # 添加指标类型作为分组标题（填充到与表头相同的列数）
            header_row = [f"=== {metric_type} ==="] + [""] * (header_length - 1) if header_length > 0 else [
                f"=== {metric_type} ==="]
            all_flattened.append(header_row)
            # 扁平化当前指标类型的数据并加入
            flattened = _flatten_metrics_list(metric_list)
            if flattened:
                all_flattened.extend(flattened)
                # 更新 header_length（以防后续的 metric_list 有更多列）
                if len(flattened[0]) > header_length:
                    header_length = len(flattened[0])
            # 添加空行分隔不同指标类型（填充到与表头相同的列数）
            empty_row = [""] * header_length if header_length > 0 else [""]
            all_flattened.append(empty_row)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            if all_flattened:
                return _transpose_flattened_data(all_flattened)
        return all_flattened
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return [[f"无效指标名！可选指标：{list(metrics.keys())}"]]
        
        # 返回指定 metric 的数据
        target_metrics_list = metrics[metric]
        flattened_metrics = _flatten_metrics_list(target_metrics_list)

        # 根据 orientation 决定是否转置
        if orientation_upper in ('HL', 'HORIZONTAL'):
            return _transpose_flattened_data(flattened_metrics)
        else:
            return flattened_metrics


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("hierarchical", "object")
@xl_arg("parentkey", "str")
@xl_arg("metric", "str")
@xl_arg("metric_name", "str")
@xl_arg("bucket_key", "str")
@xl_arg("currency", "str")
@xl_arg("schema", "str")
def PortHierarchicalMetricsValue(hierarchical, parentkey, metric=None, metric_name=None, bucket_key=None, currency=None, schema=None):
    """
    获取分层组合管理器的指标 value 值

    参数:
        hierarchical: 分层组合管理器对象
        parentkey: 父节点键
        metric: 指标类型（可选），如 'valuation_metrics', 'risk_metrics' 等。如果为 None，从所有指标中查找
        metric_name: 指标名称（可选），匹配 metric_type 字段
        bucket_key: bucket_key匹配（可选），匹配 bucket_key 字段
        currency: 货币匹配（可选），匹配 currency 字段
        schema: schema匹配（可选），匹配 schema 字段

    返回:
        如果只有一个匹配的 value: 返回该值（保持原类型）
        如果有多个匹配的 value: 返回逗号分隔的字符串
        如果没有匹配的记录: 返回空字符串
    """
    metrics = {}
    try:
        valuation_metrics = hierarchical.calculateParentValuationMetrics(parentkey)
        metrics['valuation_metrics'] = _metrics_to_dict(valuation_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentValuationMetrics: {e}")
    try:
        risk_metrics = hierarchical.calculateParentRiskMetrics(parentkey)
        metrics['risk_metrics'] = _metrics_to_dict(risk_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentRiskMetrics: {e}")
    try:
        carry_metrics = hierarchical.calculateParentCarryMetrics(parentkey)
        metrics['carry_metrics'] = _metrics_to_dict(carry_metrics)
    except Exception as e:
        print(f"    [ERROR] Failed to calculateParentCarryMetrics: {e}")

    # 过滤指标数据
    target_metrics_list = []

    if metric is None:
        # 如果未指定 metric，收集所有指标类型的数据
        for metric_type, metric_list in metrics.items():
            target_metrics_list.extend(metric_list)
    else:
        # 如果指定了 metric，先校验有效性
        if metric not in metrics:
            return ""
        target_metrics_list = metrics[metric]

    # 如果提供了 metric_name，进一步过滤 metric_type 字段
    if metric_name is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if m.get('metric_type', '') == metric_name
        ]

    # 如果提供了 bucket_key，进一步过滤
    if bucket_key is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if bucket_key.lower() in str(m.get('bucket_key', '')).lower()
        ]

    # 如果提供了 currency，进一步过滤
    if currency is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if currency.lower() in str(m.get('currency', '')).lower()
        ]

    # 如果提供了 schema，进一步过滤
    if schema is not None:
        target_metrics_list = [
            m for m in target_metrics_list
            if schema.lower() in str(m.get('schema', '')).lower()
        ]

    # 收集所有匹配的 value 值
    values = []
    for metric_dict in target_metrics_list:
        value = metric_dict.get('value')
        if value is not None:
            values.append(value)

    # 根据 value 数量返回
    if len(values) == 0:
        return ""
    elif len(values) == 1:
        return values[0]
    else:
        # 多个 value，用逗号分隔
        return ",".join(str(v) for v in values)
