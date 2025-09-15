from mcp.utils.enums import DayCounter, enum_wrapper
from mcp.utils.excel_utils import mcp_kv_wrapper
from mcp.forward.custom import general_fwd_register
from mcp.forward.fwd_wrapper import McpVanillaOption, FwdDefConst
from mcp.tool.args_def import tool_def
import mcp.forward.custom

def bisect(func, low, high, args=(), xtol=1e-4, maxiter=100):
    """
    A simple bisection method for root finding.
    
    Parameters:
    - func: The function for which the root is sought.
    - low, high: The interval in which to search for the root.
    - args: Additional arguments to pass to the function.
    - xtol: The tolerance (stopping criterion).
    - maxiter: Maximum number of iterations.
    
    Returns:
    - The estimated position of the root.
    """
    fl = func(low, *args)
    fh = func(high, *args)
    if fl * fh > 0:
        raise ValueError("Function must have different signs at the boundaries.")

    for _ in range(maxiter):
        mid = (low + high) / 2.0
        fm = func(mid, *args)
        if fm * fl < 0:
            high = mid
            fh = fm
        else:
            low = mid
            fl = fm
        
        if abs(high - low) < xtol:
            return mid
    
    return mid  # Or raise a warning/error if convergence not achieved

class QmUtils:

    @staticmethod
    def parse_qm_args(args1, arr):
        args2 = []
        for i in range(int(len(arr) / 2)):
            args2.append([arr[i * 2], arr[i * 2 + 1]])
        return [args1, args2, [], [], [], 'VP']

    @staticmethod
    def parse_dict_args(arr):
        d = {}
        for i in range(int(len(arr) / 2)):
            d[arr[i * 2]] = arr[i * 2 + 1]
        return d

    @staticmethod
    def gen_instance(name, args_list):
        # print(f"QmUtils.gen_instance: {name}, {args_list}")
        return tool_def.xls_create(*args_list, key=name)


class QmVanillaOption:

    @staticmethod
    def gen_instance(args_list):
        return QmUtils.gen_instance('McpVanillaOption', args_list)

    @staticmethod
    def price(args_list):
        return QmVanillaOption.gen_instance(args_list).price()

    @staticmethod
    def delta(args_list, isCcy2, isAmount):
        obj = QmVanillaOption.gen_instance(args_list)
        pricingMethod = enum_wrapper.parse2(1)
        result = obj.Delta(isCcy2, isAmount, pricingMethod)
        return result

    @staticmethod
    def MarketValue(args_list):
        return QmVanillaOption.gen_instance(args_list).MarketValue()

    @staticmethod
    def PresentValue(args_list):
        return QmVanillaOption.gen_instance(args_list).PV()
    
    @staticmethod
    def price_diff(strike, target_price, args_list):
        # 辅助函数，返回当前执行价格下的价格差
        for args in args_list:
            for arg in args:
                if arg[0].lower() == 'strikepx':
                    arg[1] = strike
                    break
        return QmVanillaOption.price(args_list) - target_price

    @staticmethod
    def StrikeImpliedFromPrice(target_price, args_list, low, high, xtol=1e-6):
        # 使用scipy.optimize.bisect进行求解
        implied_strike = bisect(QmVanillaOption.price_diff, low, high, args=(target_price, args_list), xtol=xtol)
        return implied_strike

class QmFXForward2:

    @staticmethod
    def gen_instance(args_list):
        return QmUtils.gen_instance('McpFXForward2', args_list)

    @staticmethod
    def price(args_list):
        return QmFXForward2.gen_instance(args_list).Price(True)

    @staticmethod
    def MarketValue(args_list):
        return QmFXForward2.gen_instance(args_list).MarketValue(True)

    @staticmethod
    def PresentValue(args_list):
        return QmFXForward2.gen_instance(args_list).PV(True)
    

class QmCustomForward:

    @staticmethod
    def gen_instance_spec(args_list, leg_args=[[]]):
        kvs = [
            ("ReferenceDate", "date"),
            ("SpotPx", "str"),
            ("BuySell", "const"),
            ("ExpiryDate", "date"),
            ("MktData", "object"),
            ("SettlementDate", "date"),
            ("PremiumDate", "date"),
            ("Calendar", "object"),
            ("Notional", "float"),
            ("DayCounter", "const"),
            ("UndDayCounter", "const", DayCounter.Act360),
            ("LegsForwardPx", "str", 'None'),
            ("LegsAccRate", "str", 'None'),
            ("LegsUndRate", "str", 'None'),
            ("LegsVolatility", "str", 'None'),
            # ("AccCurve", "object"),
            # ("UndCurve", "object"),
            ("CalculatedTarget", "const", 'CCY1'),
            ("Pair","str",'USD/CNY'),
        ]
        kvs3 = [
            ("ReferenceDate", "date"),
            ("SpotPx", "str"),
            ("BuySell", "const"),
            ("ExpiryDate", "date"),
            ("VolSurface", "object"),
            ("SettlementDate", "date"),
            ("PremiumDate", "date"),
            ("Calendar", "object"),
            ("Notional", "float"),
        ]
        kvs2 = [
            ("ReferenceDate", "date"),
            ("SpotPx", "str"),
            ("BuySell", "const"),
            ("ExpiryDate", "date"),
            ("VolSurface", "object"),
            ("SettlementDate", "date"),
            ("PremiumDate", "date"),
            ("Calendar", "object"),
            ("Notional", "float"),
            ("DayCounter", "const"),
            ("UndDayCounter", "const", DayCounter.Act360),
            ("AccCurve", "object"),
            ("UndCurve", "object"),
        ]
        args = args_list[0:5]
        fmt = args_list[5]
        data_fields = []
        result, lack_keys = mcp_kv_wrapper.process_kv_list(args, fmt, data_fields, [kvs, kvs2, kvs3])
        raw_dict = result["args_dict"]
        key, lack_keys_custom, strikes_dict = general_fwd_register.validate_args(raw_dict)
        lack_keys.extend(lack_keys_custom)
        if len(lack_keys) > 0:
            raise Exception("Missing fields: " + str(lack_keys))
            # return "Missing fields: " + str(lack_keys)
        legs = general_fwd_register.parse_legs_spec_args(leg_args)
        if len(legs) == 0:
            legs = general_fwd_register.parse_legs_spec_args2(raw_dict)
        vals = result["vals"]
        f_args = []
        f_args.extend(vals)
        f_args.extend([key, strikes_dict, legs])
        # print(f"strikes_dict: {strikes_dict}")
        forward = mcp.forward.custom.McpCustomForward(*f_args)
        return forward, key, vals, strikes_dict, result

    @staticmethod
    def gen_instance(args_list):
        tp = QmCustomForward.gen_instance_spec(args_list)
        return tp[0]

    @staticmethod
    def price(args_list):
        return QmCustomForward.gen_instance(args_list).price()

    @staticmethod
    def strike_from_price(args1, arr):
        cf = QmCustomForward.gen_instance(QmUtils.parse_qm_args(args1, arr))
        if cf.key == 'Cap Seagull':
            return cf.segull_strike_from_price(QmUtils.parse_dict_args(arr))
        else:
            return cf.strike_from_price(QmUtils.parse_dict_args(arr))
