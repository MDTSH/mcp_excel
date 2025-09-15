import datetime
import json

from pyxll import xl_func, xl_arg, xl_return, RTD

import mcp.mcp
import mcp.forward.compound
import mcp.forward.custom
import mcp.forward.batch
from mcp.utils.enums import DayCounter, InterpolatedVariable
from mcp.forward.custom import general_fwd_register, FwdDefConst
from mcp.utils.mcp_utils import *
from mcp.utils.excel_utils import *
from mcp.tool.args_def import tool_def
from mcp.tool.quick_method import QmCustomForward
import mcp.wrapper
import logging


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpRatioForward(args1, args2, args3, args4, args5, fmt=None):
#     args = [args1, args2, args3, args4, args5]
#     if fmt is None:
#         result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpRatioForward2, args, [
#             ("ReferenceDate", "date"),
#             ("SpotPx", "float"),
#             ("BuySell", "const"),
#             ("ExpiryDate", "date"),
#             ("StrikePx", "float"),
#             ("AccRate", "float"),
#             ("UndRate", "float"),
#             ("Volatility", "float"),
#             ("SettlementDate", "date"),
#             ("PriceSettlementDate", "date"),
#             ("Calendar", "object"),
#             ("DayCounter", "object"),
#             ("OptionExpiryNature", "const"),
#             ("PricingMethod", "const")])
#
#         if len(lack_keys) > 0:
#             return "Missing fields: " + str(lack_keys)
#         vals = result["vals"]
#         print("McpRatioForward vals:", vals)
#         forward = mcp.forward.compound.McpRatioForward(*vals)
#         mcp_method_args_cache.cache(str(forward), result)
#     else:
#         data_fields = [
#             ("PackageName", "str"),
#             ("SpotPx", "float"),
#             ("BuySell", "const"),
#             ("FaceAmount", "float"),
#             ("CallPut", "str"),
#             ("K1", "float"),
#             ("K2", "float"),
#             ("Ratio", "float"),
#             ("Strike", "float"),
#             ("ReferenceDate", "date"),
#             ("ExpiryDate", "date"),
#             ("SettlementDate", "date"),
#             ("PriceSettlementDate", "date"),
#             ("Calendar", "object"),
#             ("VolSurface", "object")
#         ]
#
#         kvs = [
#             ("CallPut", "str"),
#             ("ReferenceDate", "date"),
#             ("Strike", "float"),
#             ("SpotPx", "float"),
#             ("FaceAmount", "float"),
#             ("ExpiryDate", "date"),
#             ("SettlementDate", "date"),
#             ("PriceSettlementDate", "date"),
#             ("Ratio", "float"),
#             ("BuySell", "const"),
#             ("PackageName", "str"),
#             ("K1", "float"),
#             ("Calendar", "object"),
#             ("VolSurface", "object"),
#             ("K2", "float")
#         ]
#
#         result, lack_keys = mcp_kv_wrapper.valid_parse("McpRatioForward", args, fmt, data_fields, kvs)
#         if len(lack_keys) > 0:
#             return "Missing fields: " + str(lack_keys)
#         vals = result["vals"]
#         print("McpRatioForward final args:", vals)
#         forward = mcp.forward.compound.McpRatioForward(*vals)
#         mcp_method_args_cache.cache(str(forward), result)
#     return forward


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("forward", "object")
# def ForwardPrice(forward):
#     return forward.price()


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("forward", "object")
@xl_arg("valueDate", "datetime")
@xl_arg("spots", "float[]")
@xl_return("var[][]")
def ForwardPayoff(forward, valueDate, spots):
    valueDate = date_to_string(valueDate)
    payoffs = forward.payoff_by_spots(valueDate, spots)
    result = [[payoffs[i]] for i in range(len(payoffs))]
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("forward", "object")
@xl_arg("valueDate", "datetime")
@xl_arg("spot", "float")
@xl_arg("range", "float")
@xl_return("var[][]")
def ForwardPayoffBySpot(forward, valueDate, spot, rg=0.003):
    valueDate = date_to_string(valueDate)
    spot_bid, spot_ask = forward.parse_spot(spot)
    spot_mid = (spot_bid + spot_ask) / 2
    spots, payoffs = forward.payoff(valueDate, spot_mid, rg)
    result = [[spots[i], payoffs[i]] for i in range(len(payoffs))]
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("forward", "object")
@xl_arg("valueDate", "datetime")
@xl_arg("spots", "var[]")
@xl_arg("legNum", "int")
@xl_return("var[][]")
def ForwardLegsPayoff(forward, valueDate, spots, legNum=0):
    if legNum is None:
        legNum = 0
    valueDate = date_to_string(valueDate)
    payoffs = forward.leg_payoff(valueDate, spots, legNum)
    result = []
    for i in range(len(spots)):
        sub_result = []
        for payoff in payoffs:
            if i < len(payoff):
                sub_result.append(payoff[i])
            else:
                sub_result.append('')
        result.append(sub_result)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("forward", "object")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def ForwardLegs(forward, fields):
    legs = forward.legs()
    result = []
    leg_header = []
    for i in range(len(legs)):
        leg_header.append("Leg" + str(i + 1))
    result.append(leg_header)
    for field in fields:
        sub_obj = []
        for leg in legs:
            if field in leg:
                sub_obj.append(leg[field])
            else:
                sub_obj.append("")
        result.append(sub_obj)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "var")
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
@xl_arg("argsKey", "str")
def ForwardStrikeImpliedFromPrice(forward, args1, args2, args3, args4, args5, fmt="VP", argsKey=None):
    if isinstance(forward, str):
        return forward
    args_list = [args1, args2, args3, args4, args5]
    # result = mcp_kv_wrapper.args_list_std_key(args_list)
    result = mcp_kv_wrapper.args_parser.parse_all(args_list, fmt, [], True)
    if argsKey is not None and argsKey != "":
        mcp_method_args_cache.cache(str(argsKey), result)
    if debug_args_info:
        print("ForwardStrikeImpliedFromPrice:", result)
    strike = forward.strike_from_price(result)
    return strike


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "var")
def ForwardPips(forward):
    if isinstance(forward, str):
        return forward
    return forward.pips()


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpParForward(args1, args2, args3, args4, args5):
#     args = [args1, args2, args3, args4, args5]
#     result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpRatioForward2, args, [
#         ("ReferenceDate", "date"),
#         ("SpotPx", "float"),
#         ("BuySell", "const"),
#         ("ExpiryDate", "date"),
#         ("StrikePx", "float"),
#         ("AccRate", "float"),
#         ("UndRate", "float"),
#         ("Volatility", "float"),
#         ("SettlementDate", "date"),
#         ("PriceSettlementDate", "date"),
#         ("Calendar", "object"),
#         ("DayCounter", "object"),
#         ("OptionExpiryNature", "const"),
#         ("PricingMethod", "const")])
#
#     if len(lack_keys) > 0:
#         return "Missing fields: " + str(lack_keys)
#     vals = result["vals"]
#     forward = mcp.forward.compound.McpParForward(*vals)
#     mcp_method_args_cache.cache(str(forward), result)
#     return forward
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpRangeForward(args1, args2, args3, args4, args5):
#     args = [args1, args2, args3, args4, args5]
#     result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpSpreadForward, args, [
#         ("ReferenceDate", "date"),
#         ("SpotPx", "float"),
#         ("BuySell", "const"),
#         ("ExpiryDate", "date"),
#         ("UpBarrier", "float"),
#         ("DownBarrier", "float"),
#         # ("AccRate", "float"),
#         # ("UndRate", "float"),
#         # ("Volatility", "float"),
#         ("VolSurface", "object"),
#         ("SettlementDate", "date"),
#         ("PriceSettlementDate", "date"),
#         ("Calendar", "object"),
#         ("DayCounter", "object"),
#         ("OptionExpiryNature", "const"),
#         ("PricingMethod", "const")])
#     if len(lack_keys) > 0:
#         return "Missing fields: " + str(lack_keys)
#     vals = result["vals"]
#     forward = mcp.forward.compound.McpRangeForward(*vals)
#     mcp_method_args_cache.cache(str(forward), result)
#     return forward
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpSpreadForward(args1, args2, args3, args4, args5):
#     return McpRangeForward(args1, args2, args3, args4, args5)
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpCapForward(args1, args2, args3, args4, args5):
#     args = [args1, args2, args3, args4, args5]
#     result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpCapForward, args, [
#         ("ReferenceDate", "date"),
#         ("SpotPx", "float"),
#         ("BuySell", "const"),
#         ("ExpiryDate", "date"),
#         ("CapRate", "float"),
#         ("ForwardRate", "float"),
#         # ("AccRate", "float"),
#         # ("UndRate", "float"),
#         # ("Volatility", "float"),
#         ("VolSurface", "object"),
#         ("SettlementDate", "date"),
#         ("PriceSettlementDate", "date"),
#         ("Calendar", "object"),
#         ("DayCounter", "object"),
#         ("OptionExpiryNature", "const"),
#         ("PricingMethod", "const")
#     ])
#     if len(lack_keys) > 0:
#         return "Missing fields: " + str(lack_keys)
#     vals = result["vals"]
#     print("McpCapForward vals:", vals)
#     forward = mcp.forward.compound.McpCapForward(False, *vals)
#     mcp_method_args_cache.cache(str(forward), result)
#     return forward
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpFloorForward(args1, args2, args3, args4, args5):
#     args = [args1, args2, args3, args4, args5]
#     result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpFloorForward, args, [
#         ("ReferenceDate", "date"),
#         ("SpotPx", "float"),
#         ("BuySell", "const"),
#         ("ExpiryDate", "date"),
#         ("FloorRate", "float"),
#         ("ForwardRate", "float"),
#         # ("AccRate", "float"),
#         # ("UndRate", "float"),
#         # ("Volatility", "float"),
#         ("VolSurface", "object"),
#         ("SettlementDate", "date"),
#         ("PriceSettlementDate", "date"),
#         ("Calendar", "object"),
#         ("DayCounter", "object"),
#         ("OptionExpiryNature", "const"),
#         ("PricingMethod", "const")
#     ])
#     if len(lack_keys) > 0:
#         return "Missing fields: " + str(lack_keys)
#     vals = result["vals"]
#     print("McpFloorForward vals:", vals)
#     forward = mcp.forward.compound.McpFloorForward(False, *vals)
#     mcp_method_args_cache.cache(str(forward), result)
#     return forward
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("args1", "var[][]")
# @xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
# def McpSeagullForward(args1, args2, args3, args4, args5):
#     args = [args1, args2, args3, args4, args5]
#     result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpSeagullForward, args, [
#         ("ReferenceDate", "date"),
#         ("SpotPx", "float"),
#         ("BuySell", "const"),
#         ("ExpiryDate", "date"),
#         ("CapRate", "float"),
#         ("UpBarrier", "float"),
#         ("DownBarrier", "float"),
#         # ("AccRate", "float"),
#         # ("UndRate", "float"),
#         # ("Volatility", "float"),
#         ("VolSurface", "object"),
#         ("SettlementDate", "date"),
#         ("PriceSettlementDate", "date"),
#         ("Calendar", "object"),
#         ("DayCounter", "object"),
#         ("OptionExpiryNature", "const"),
#         ("PricingMethod", "const")
#     ])
#     if len(lack_keys) > 0:
#         return "Missing fields: " + str(lack_keys)
#     vals = result["vals"]
#     forward = mcp.forward.compound.McpSeagullForward(False, *vals)
#     mcp_method_args_cache.cache(str(forward), result)
#     return forward


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("leg_args", "var[][]")
@xl_arg("fmt", "str")
def McpCustomForward(args1, args2, args3, args4, args5, leg_args, fmt="VP"):
    # kvs = [
    #     ("ReferenceDate", "date"),
    #     ("SpotPx", "str"),
    #     ("BuySell", "const"),
    #     ("ExpiryDate", "date"),
    #     ("MktData", "object"),
    #     ("SettlementDate", "date"),
    #     ("PremiumDate", "date"),
    #     ("Calendar", "object"),
    #     ("Notional", "float"),
    #     ("DayCounter", "const"),
    #     ("UndDayCounter", "const", DayCounter.Act360),
    #     ("LegsForwardPx", "str", 'None'),
    #     ("LegsAccRate", "str", 'None'),
    #     ("LegsUndRate", "str", 'None'),
    #     ("LegsVolatility", "str", 'None'),
    #     # ("AccCurve", "object"),
    #     # ("UndCurve", "object"),
    # ]
    # kvs3 = [
    #     ("ReferenceDate", "date"),
    #     ("SpotPx", "str"),
    #     ("BuySell", "const"),
    #     ("ExpiryDate", "date"),
    #     ("VolSurface", "object"),
    #     ("SettlementDate", "date"),
    #     ("PremiumDate", "date"),
    #     ("Calendar", "object"),
    #     ("Notional", "float"),
    # ]
    # kvs2 = [
    #     ("ReferenceDate", "date"),
    #     ("SpotPx", "str"),
    #     ("BuySell", "const"),
    #     ("ExpiryDate", "date"),
    #     ("VolSurface", "object"),
    #     ("SettlementDate", "date"),
    #     ("PremiumDate", "date"),
    #     ("Calendar", "object"),
    #     ("Notional", "float"),
    #     ("DayCounter", "const"),
    #     ("UndDayCounter", "const", DayCounter.Act360),
    #     ("AccCurve", "object"),
    #     ("UndCurve", "object"),
    # ]
    # args = [args1, args2, args3, args4, args5]
    # # if fmt is None:
    # #     result, lack_keys, raw_dict = mcp_kv_wrapper.parse_and_validate3("McpCustomForward", args, kvs)
    # #     result2, lack_keys2, raw_dict2 = mcp_kv_wrapper.parse_and_validate3("McpCustomForward2", args, kvs2)
    # #     if len(lack_keys2) <= lack_keys:
    # #         result = result2
    # #         lack_keys = lack_keys2
    # #         raw_dict = raw_dict2
    # #
    # #     key, lack_keys_custom, strikes_dict = general_fwd_register.validate_args(raw_dict)
    # #     lack_keys.extend(lack_keys_custom)
    # #     if len(lack_keys) > 0:
    # #         return "Missing fields: " + str(lack_keys)
    # #     strikes_dict[FwdDefConst.Field_Legs_Args] = general_fwd_register.parse_legs_spec_args(args6)
    # #     print(FwdDefConst.Field_Legs_Args, strikes_dict[FwdDefConst.Field_Legs_Args])
    # #     vals = result["vals"]
    # #     forward = mcp.forward.custom.McpCustomForward(key, vals[2], strikes_dict, vals)
    # #     cache_result = general_fwd_register.create_cache_result(key, vals[2], strikes_dict, result)
    # #     mcp_method_args_cache.cache(str(forward), cache_result)
    # # else:
    # data_fields = []
    # result, lack_keys = mcp_kv_wrapper.process_kv_list(args, fmt, data_fields, [kvs, kvs2, kvs3])
    # raw_dict = result["args_dict"]
    # # result, lack_keys, raw_dict = mcp_kv_wrapper.valid_parse3("McpCustomForward", args, fmt, data_fields, kvs)
    # # result2, lack_keys2, raw_dict2 = mcp_kv_wrapper.valid_parse3("McpCustomForward2", args, fmt, data_fields, kvs2)
    # # # print("McpCustomForward lack_keys:", lack_keys)
    # # # print("McpCustomForward lack_keys2:", lack_keys2)
    # # if len(lack_keys2) <= len(lack_keys):
    # #     result = result2
    # #     lack_keys = lack_keys2
    # #     raw_dict = raw_dict2
    # # print("lack_keys:", lack_keys)
    # key, lack_keys_custom, strikes_dict = general_fwd_register.validate_args(raw_dict)
    # # print("lack_keys_custom:", lack_keys_custom)
    # lack_keys.extend(lack_keys_custom)
    # if len(lack_keys) > 0:
    #     return "Missing fields: " + str(lack_keys)
    # legs = general_fwd_register.parse_legs_spec_args(leg_args)
    # # strikes_dict[FwdDefConst.Field_Legs_Args] = general_fwd_register.parse_legs_spec_args(leg_args)
    # vals = result["vals"]
    # # f_args = [key, vals[2], strikes_dict, vals]
    # f_args = []
    # f_args.extend(vals)
    # f_args.extend([key, strikes_dict, legs])
    # if debug_args_info:
    #     print(FwdDefConst.Field_Legs_Args, strikes_dict[FwdDefConst.Field_Legs_Args])
    #     print("McpCustomForward final args: ", f_args)
    # # print("McpCustomForward final args: ", f_args)
    #
    # # d = {}
    # # keys = result["keys"]
    # # for i in range(len(vals)):
    # #     d[keys[i]] = vals[i]
    # # del_list = ["VolSurface", "Calendar", "UndCurve", "AccCurve"]
    # # for item in del_list:
    # #     if item in d:
    # #         del d[item]
    # # update_list = ["DayCounter","BuySell"]
    # # for item in update_list:
    # #     if item in d and item in raw_dict:
    # #         d[item] = raw_dict[item]
    # # d.update({
    # #     "LegsArgs": legs,
    # #     "StrikeDict": strikes_dict,
    # #     "Package": key,
    # # })
    # # print("McpCustomForward fwdArgsDict: ", d)
    #
    # forward = mcp.forward.custom.McpCustomForward(*f_args)
    args_list = [args1, args2, args3, args4, args5, fmt]
    forward, key, vals, strikes_dict, result = QmCustomForward.gen_instance_spec(args_list, leg_args)
    cache_result = general_fwd_register.create_cache_result(key, vals[2], strikes_dict, result)
    mcp_method_args_cache.cache(str(forward), cache_result)
    return forward


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("valueDates", "datetime[]")
@xl_arg("spots", "float[]")
@xl_return("var[][]")
def ForwardPrices(obj, valueDates, spots):
    dates = mcp_dt.to_date_list(valueDates, mcp_dt.to_pure_date)
    prices = obj.prices(dates, spots)
    return prices


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
@xl_arg("pricingMethod", "var")
def ForwardPrice(forward, pricingMethod=None):
    if pricingMethod is None:
        return forward.price()
    else:
        return forward.price(enum_wrapper.parse2(pricingMethod))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardDeltaL(forward):
    return forward.delta(True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardDeltaR(forward):
    return forward.delta(False)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardRhoL(forward):
    return forward.rho(True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardRhoR(forward):
    return forward.rho(False)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardGamma(forward):
    return forward.gamma()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardVega(forward):
    return forward.vega()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("forward", "object")
def ForwardTheta(forward):
    return forward.theta()


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("args", "var[][]")
@xl_arg("valueDates", "datetime[]")
@xl_arg("field", "str")
@xl_arg("data", "float[]")
@xl_return("var[][]")
def ForwardStrikes(obj, args, valueDates, field, data):
    args_list = [args]
    # print("args_list:", args_list)
    impl_args = mcp_kv_wrapper.args_list_std_key(args_list)
    # print("impl_args:", impl_args)
    dates = mcp_dt.to_date_list(valueDates, mcp_dt.to_pure_date)
    # print("obj:", obj)
    result = obj.implied_strikes(impl_args["result"], dates, field, data)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
# @xl_arg("args3", "var[][]")
# @xl_arg("args4", "var[][]")
# @xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpCustomForwardDefine(args1, args2, fmt="VP"):
    args = [args1, args2]
    kvs = [
        ("PackageName", "str"),
        ("BuySell", "str"),
        ("Strikes", "str"),
        ("StrikesStructure", "str"),
        ("ProductStructure", "str")
    ]
    kvs2 = [
        ("PackageName", "str"),
        ("BuySell", "str"),
        ("Strikes", "str"),
        ("Arguments", "str"),
        ("StrikesStructure", "str"),
        ("ProductStructure", "str")
    ]
    data_fields = []
    def_dicts = []
    for item in args:
        if len(item) == 1 and len(item[0]) == 1:
            continue
        result, lack_keys = mcp_kv_wrapper.process_kv_list([item], fmt, data_fields, [kvs, kvs2])
        raw_dict = result["args_dict"]
        def_dicts.append(raw_dict)
    # result, lack_keys, raw_dict = mcp_kv_wrapper.valid_parse3("McpCustomForwardDefine",
    #                                                           args, fmt, data_fields, kvs)
    # result2, lack_keys2, raw_dict2 = mcp_kv_wrapper.valid_parse3("McpCustomForwardDefine2",
    #                                                              args, fmt, data_fields, kvs2)
    # if len(lack_keys2) <= len(lack_keys):
    #     result = result2
    #     lack_keys = lack_keys2
    #     raw_dict = raw_dict2
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    # print("McpCustomForwardDefine final args:", raw_dict)
    # print(f"McpCustomForwardDefine fwdArgsDict: '{raw_dict['BuySell']}': {raw_dict},")
    #print(f"McpCustomForwardDefine: {def_dicts}")
    result = general_fwd_register.add(def_dicts)
    return result


class CfdRtd(RTD):

    def __init__(self, key):
        self.key = key

    def connect(self):
        general_fwd_register.add_def_listener(self.key, self.on_data)

    def on_data(self, data):
        self.value = str(data)

    def disconnect(self):
        general_fwd_register.remove_def_listener(self.key, self.on_data)


@xl_func("str key: rtd", macro=False)
def McpCfdStatus(key):
    return CfdRtd(key)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpFXForwardOutright(args1, args2, args3, args4, args5, fmt="VP"):
    args = [args1, args2, args3, args4, args5]
    data_fields = []
    kv1 = [
        ("ReferenceDate", "date"),
        ("SpotDate", "date"),
        ("EndDate", "date"),
        ("ForwardOutright", "float"),
        ("Notional", "float"),
        ("BaseCcy", "str"),
        ("TermCcy", "str"),
    ]
    kv2 = None
    result, lack_keys = mcp_kv_wrapper.valid_parse("McpFXForwardOutright", args, fmt, data_fields, kv1, kv2)
    if len(lack_keys) > 0:
        return "Missing fields: " + str(lack_keys)
    vals = result["vals"]
    #print("McpFXForwardOutright vals:", vals)
    mcp_item = mcp.mcp.MFXForwardOutright(*vals)
    mcp_method_args_cache.cache(str(mcp_item), result)
    return mcp_item


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("fxfo", "object")
@xl_arg("estimationCurve1", "object")
@xl_arg("discountingCurve1", "object")
@xl_arg("estimationCurve2", "object")
@xl_arg("discountingCurve2", "object")
@xl_arg("fx", "float")
def FxfoPrice(fxfo, estimationCurve1, discountingCurve1, estimationCurve2, discountingCurve2, fx):
    return fxfo.Price(estimationCurve1.getHandler(),
                      discountingCurve1.getHandler(),
                      estimationCurve2.getHandler(),
                      discountingCurve2.getHandler(),
                      fx)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("fxfo", "object")
@xl_arg("estimationCurve1", "object")
@xl_arg("discountingCurve1", "object")
@xl_arg("estimationCurve2", "object")
@xl_arg("discountingCurve2", "object")
@xl_arg("fx", "float")
def FxfoNPV(fxfo, estimationCurve1, discountingCurve1, estimationCurve2, discountingCurve2, fx):
    return fxfo.NPV(estimationCurve1.getHandler(),
                    discountingCurve1.getHandler(),
                    estimationCurve2.getHandler(),
                    discountingCurve2.getHandler(),
                    fx)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("fxfo", "object")
@xl_arg("estimationCurve1", "object")
@xl_arg("discountingCurve1", "object")
@xl_arg("estimationCurve2", "object")
@xl_arg("discountingCurve2", "object")
@xl_arg("fxSpot", "float")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def FxfoFrtbGirrDeltas(fxfo, estimationCurve1, discountingCurve1, estimationCurve2,
                       discountingCurve2, fxSpot, ccy2LocRate, fmt="V"):
    s = fxfo.FrtbGirrDeltas(estimationCurve1.getHandler(),
                            discountingCurve1.getHandler(),
                            estimationCurve2.getHandler(),
                            discountingCurve2.getHandler(),
                            fxSpot,
                            ccy2LocRate)
    return as_2d_array(s, fmt)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("fxfo", "object")
@xl_arg("ccyLocMarketSpot", "float")
@xl_arg("isLocCcy2", "bool")
@xl_arg("ccy2LocRate", "float")
def FxfoFrtbFxDelta(fxfo, ccyLocMarketSpot, isLocCcy2=True, ccy2LocRate=1.0):
    return fxfo.FrtbFxDelta(ccyLocMarketSpot,
                            isLocCcy2,
                            ccy2LocRate)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("fxfo", "object")
@xl_arg("ccy1LocMarketSpot", "float")
@xl_arg("ccy2LocMarketSpot", "float")
@xl_arg("ccy2LocRate", "float")
@xl_arg("fmt", "str")
def FxfoFrtbFxDeltas(fxfo, ccy1LocMarketSpot, ccy2LocMarketSpot, ccy2LocRate=1.0, fmt="V"):
    s = fxfo.FrtbFxDeltas(ccy1LocMarketSpot,
                          ccy2LocMarketSpot,
                          ccy2LocRate)
    return as_array(s, fmt)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("fxfpc", "object")
@xl_arg("endDate", "datetime")
def FxfpcFXForwardPoints(fxfpc, endDate):
    return fxfpc.FXForwardPoints(mcp_dt.to_pure_date(endDate))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("fxfpc", "object")
@xl_arg("endDate", "datetime")
def FxfpcFXForwardOutright(fxfpc, endDate):
    return fxfpc.FXForwardOutright(mcp_dt.to_pure_date(endDate))


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("objs", "object[]")
def McpPortfolio(objs):
    return mcp.forward.custom.McpPortfolio(objs)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("portfolio", "object")
@xl_arg("changes", "float[]")
@xl_arg("columns", "str[]")
@xl_arg("reference_date", "date")
@xl_arg("spot", "float")
@xl_arg("diff", "bool")
@xl_arg("pricingMethod", "var")
@xl_return("var[][]")
def McpSpotLadder(portfolio, changes, columns, reference_date, spot, diff=False, pricingMethod=None):
    column_value = [column.strip() for column in columns]
    reference_date = date_to_string(reference_date)
    result = portfolio.spot_ladder(spot, reference_date, changes, column_value, diff, pricingMethod)
    #print(result)
    return result


import mcp.xscript.utils as xsutils


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
def McpVanillaOptionBatch(args):
    d = xsutils.SttUtils.parse_excel_kv_dict(args)
    d = xsutils.SttUtils.to_lower_key(d)
    return mcp.forward.batch.McpVanillaOptionBatch(d)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("obj", "object")
@xl_arg("tenor", "str")
@xl_arg("strike_px", "float")
def McpBatchCalcPrice(obj, tenor, strike_px):
    return obj.calc_price(tenor, strike_px)


"""不确定"""
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args", "var[][]")
def McpMktData(args):
    d = xsutils.SttUtils.parse_excel_kv_dict(args)
    d = xsutils.SttUtils.to_lower_key(d)
    try:
        return mcp.wrapper.McpMktData(d)
    except:
        s = f"McpMktData except: {args}"
        # logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("spotPx", "float")
@xl_arg("domesticRate", "float")
@xl_arg("foreignRate", "float")
@xl_arg("timeToExpiry", "float")
@xl_arg("rateInterp", "var")
def McpCalcForward(spotPx, domesticRate, foreignRate, timeToExpiry, rateInterp=InterpolatedVariable.CONTINUOUSRATES):
    rate_type = enum_wrapper.parse2(rateInterp, 'InterpolatedVariable')
    return mcp.wrapper.ForwardUtils.calc_forward(spotPx, timeToExpiry, domesticRate, foreignRate, rate_type)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("spotPx", "float")
@xl_arg("domesticRate", "float")
@xl_arg("forward", "float")
@xl_arg("timeToExpiry", "float")
@xl_arg("rateInterp", "var")
def McpCalcUndRate(spotPx, domesticRate, forward, timeToExpiry, rateInterp=InterpolatedVariable.CONTINUOUSRATES):
    rate_type = enum_wrapper.parse2(rateInterp, 'InterpolatedVariable')
    return mcp.wrapper.ForwardUtils.calc_und_rate(spotPx, timeToExpiry, domesticRate, forward, rate_type)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFXForward(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpFXForward')
    except Exception as e:
        s = f"McpFXForward except: {e}"
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
def McpFXForward2(args1, args2, args3, args4, args5, fmt='VP'):
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key='McpFXForward2')
    except Exception as e:
        s = f"McpFXForward2 except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s