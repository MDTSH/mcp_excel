import json
import time
from datetime import datetime, timedelta, date

import numpy
import pandas as pd
from pandas import DataFrame

from mcp.utils.enums import enum_wrapper
from mcp.utils.mcp_utils import mcp_dt, mcp_const
from mcp.wrapper import is_mcp_wrapper


class MethodName():
    McpFXVanilla = "McpFXVanilla"
    McpFXVanilla2 = "McpFXVanilla2"
    BsvStrikeImpliedFromDelta = "BsvStrikeImpliedFromDelta"
    BsvDeltaImpliedFromStrike = "BsvDeltaImpliedFromStrike"
    BsvVolImpliedFromPrice = "BsvVolImpliedFromPrice"
    BsvVolImpliedFromForwardPrice = "BsvVolImpliedFromForwardPrice"
    BsvStrikeImpliedFromPrice = "BsvStrikeImpliedFromPrice"

    McpVanillaBarriers = "McpVanillaBarriers"
    McpVanillaBarriers2 = "McpVanillaBarriers2"
    McpTargetRedemptionForward = "McpTargetRedemptionForward"
    McpTargetRedemptionForward2 = "McpTargetRedemptionForward2"
    McpPivotTargetRedemptionForward = "McpPivotTargetRedemptionForward"

    McpVanillaOption = "McpVanillaOption"
    McpAsianOption = "McpAsianOption"

    McpVanillaSwap = "McpVanillaSwap"
    McpVanillaSwap2 = "McpVanillaSwap2"
    McpYieldCurve = "McpYieldCurve"
    McpCapVolStripping = "McpCapVolStripping"
    McpSwaptionCube = "McpSwaptionCube"
    ScViewTenorSurface = "ScViewTenorSurface"
    McpBlack76Swaption = "McpBlack76Swaption"
    McpIROHistVols = "McpIROHistVols"
    McpIROHistVols2 = "McpIROHistVols2"
    McpHistVols = "McpHistVols"
    McpBDTData = "McpBDTData"
    McpBDTTree = "McpBDTTree"

    McpSwapCurve = "McpSwapCurve"
    McpSwapCurve2 = "McpSwapCurve2"
    McpBondCurve = "McpBondCurve"
    McpVolatilitySurface = "McpVolatilitySurface"
    McpOvernightRateCurveData = "McpOvernightRateCurveData"
    McpOvernightRateCurveData2 = "McpOvernightRateCurveData2"
    McpBillCurveData = "McpBillCurveData"
    McpBillCurveData2 = "McpBillCurveData2"
    McpBillFutureCurveData = "McpBillFutureCurveData"
    McpBillFutureCurveData2 = "McpBillFutureCurveData2"
    McpVanillaSwapCurveData = "McpVanillaSwapCurveData"
    McpVanillaSwapCurveData2 = "McpVanillaSwapCurveData2"
    McpVanillaSwapCurveData3 = "McpVanillaSwapCurveData3"
    McpVanillaSwapCurveData4 = "McpVanillaSwapCurveData4"
    McpFixedRateBondCurveData = "McpFixedRateBondCurveData"
    McpFixedRateBondCurveData2 = "McpFixedRateBondCurveData2"

    McpRatioForward = "McpRatioForward"
    # RtfStrikeImpliedFromPrice = "RatioForwardStrikeImpliedFromPrice"
    McpRatioForward2 = "McpRatioForward2"
    # Rtf2StrikeImpliedFromPrice = "RatioForward2StrikeImpliedFromPrice"
    McpParForward = "McpParForward"
    # PrfStrikeImpliedFromPrice = "ParForwardStrikeImpliedFromPrice"
    McpParForward2 = "McpParForward2"
    # Prf2StrikeImpliedFromPrice = "ParForward2StrikeImpliedFromPrice"
    McpSpreadForward = "McpSpreadForward"
    McpSpreadForward2 = "McpSpreadForward2"
    McpCapForward = "McpCapForward"
    McpCapForward2 = "McpCapForward2"
    McpFloorForward = "McpFloorForward"
    McpFloorForward2 = "McpFloorForward2"
    McpSeagullForward = "McpSeagullForward"
    McpSeagullForward2 = "McpSeagullForward2"

    McpGeneralForward = "McpGeneralForward"
    McpGeneralForwardDefine = "McpGeneralForwardDefine"

    McpScheduledRatioForward = "McpScheduledRatioForward"
    McpScheduledRatioForward2 = "McpScheduledRatioForward2"

    McpSchedRatioForward = "McpSchedRatioForward"
    McpSchedParForward = "McpSchedParForward"
    McpSchedRangeForward = "McpSchedRangeForward"
    McpSchedCapForward = "McpSchedCapForward"
    McpSchedFloorForward = "McpSchedFloorForward"
    McpSchedSeagullForward = "McpSchedSeagullForward"

    McpFixedRateBond = "McpFixedRateBond"

    DgtAssetOrNothingCall = "DgtAssetOrNothingCall"
    DgtAssetOrNothingPut = "DgtAssetOrNothingPut"
    DgtCashOrNothingCall = "DgtCashOrNothingCall"
    DgtCashOrNothingPut = "DgtCashOrNothingPut"
    DgtDownAssetAtTouch = "DgtDownAssetAtTouch"
    DgtDownCashAtTouch = "DgtDownCashAtTouch"
    DgtDownInAssetAtExpiry = "DgtDownInAssetAtExpiry"
    DgtDownInAssetCall = "DgtDownInAssetCall"
    DgtDownOutAssetPut = "DgtDownOutAssetPut"

    VbVanillaOption = "VbVanillaOption"
    VbAmericanCall = "VbAmericanCall"
    VbAmericanPut = "VbAmericanPut"

    VbUpDown = "VbUpDown"
    VbDoubleBarrier = "VbDoubleBarrier"


class FieldName():
    Price = "Price"
    UpBarrier = "UpBarrier"
    DownBarrier = "DownBarrier"
    CapRate = "CapRate"
    ForwardRate = "ForwardRate"
    FloorRate = "FloorRate"

    BuySell = "BuySell"
    CallPut = "CallPut"
    StrikePx = "StrikePx"
    Volatility = "Volatility"
    TimeToExpiry = "TimeToExpiry"
    timeToDelivery = "TimeToDelivery"
    DeliveryDate = "DeliveryDate"
    TimeToSettlement = "TimeToSettlement"
    DomesticRate = "DomesticRate"
    ForeignRate = "ForeignRate"
    SpotPx = "SpotPx"
    Forward = "ForwardPx"
    ReferenceDate = "ReferenceDate"
    ExpiryDate = "ExpiryDate"
    SettlementDate = "SettlementDate"
    Leverage = "Leverage"
    Barrier = "Barrier"

    DeltaRHS = "DeltaRHS"
    Tolerance = "Tolerance"
    MaxNumIterations = "MaxNumIterations"

    OptionExpiryNature = "OptionExpiryNature"
    PricingMethod = "PricingMethod"
    AverageMethod = "AverageMethod"
    StrikeType = "StrikeType"

    Premium = "Premium"
    DeltaL = "Delta(L)"
    DeltaR = "Delta(R)"
    Gamma = "Gamma"
    Vega = "Vega"
    Theta = "Theta"
    RhoL = "Rho(L)"
    RhoR = "Rho(R)"

    FaceValue = "FaceAmount"

    BarrierType = "BarrierType"

    MatrixData = "MatrixData"

    PremiumDate = "PremiumDate"
    DigitalType = 'DigitalType'


class McpListObject():

    def __init__(self):
        self.data = []

    def to_plain_string(self):
        return json.dumps(self.data)

    def to_date_string(self, fmt_func):
        dts = [mcp_dt.parse_excel_date(item) for item in self.data]
        ss = mcp_dt.to_date_list(dts, fmt_func)
        return json.dumps(ss)


def pf_mcp_list(val):
    return val


def pf_mcp_plain_list(val):
    try:
        if isinstance(val, list):
            return pf_object_list(val)
        else:
            json.loads(val)
            return val
    except:
        raise Exception("Parse list Exception:" + str(val))


def pf_mcp_date_list(val):
    try:
        xl_dts = json.loads(val)
        dts = [mcp_dt.parse_excel_date(float(item)) for item in xl_dts]
        ss = mcp_dt.to_date_list(dts, mcp_dt.to_date1)
        result = json.dumps(ss)
        print("xl_dts:", xl_dts)
        print("dts:", dts)
        print("ss:", ss)
        print("result:", result)
        return result
    except:
        raise Exception("Parse date list Exception:" + str(val))


def from_excel_ordinal(ordinal, _epoch0=datetime(1899, 12, 31)):
    if ordinal >= 60:
        ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
    return (_epoch0 + timedelta(days=ordinal)).replace(microsecond=0)


def to_excel_ordinal(date1):
    # Initializing a reference date
    # Note that here date is not 31st Dec but 30th!
    temp = datetime(1899, 12, 30)
    delta = pd.to_datetime(date1) - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


def pf_mcp_handler(obj):
    if isinstance(obj, str):
        raise Exception("Invalid object: " + obj)
    return obj.getHandler()


def pf_str(val):
    return str(val)


def pf_none(val):
    return val


def pf_int(val):
    if val is None:
        return None
    return int(val)


def pf_bool(val):
    val = str(val).lower()
    if val == "true" or val == "y":
        return True
    else:
        return False
    # return str(val).lower() == "true"


def pf_int_bool(val):
    b = pf_bool(val)
    if b:
        return 1
    else:
        return 0


def pf_float(val):
    if val is None:
        return None
    f = 0
    try:
        if isinstance(val, str):
            val = val.replace('%', 'e-2')
        f = float(val)
    except:
        raise Exception("Parse float Exception: " + str(val))
    return f


def pf_date_time(val):
    if val is None:
        return None
    return from_excel_ordinal(val)


def pf_date(val):
    if val is None:
        return ""
    try:
        if isinstance(val, str):
            dt = mcp_dt.parse_date(val)
        elif isinstance(val, datetime):
            dt = val
        elif isinstance(val, date):
            dt = val
        else:
            dt = pf_date_time(val)
        result = mcp_dt.to_date1(dt)
    except:
        raise Exception("Parse date Exception: " + str(val))
    return result


def pf_vfloat(val):
    if val is None:
        raise Exception("Parse float Exception: " + str(val))
    return pf_float(val)


def pf_vdate(val):
    if val is None:
        raise Exception("Parse date Exception: " + str(val))
    return pf_date(val)


const_dict = {}
const_dict["buy"] = mcp_const.Side_Buy
const_dict["sell"] = mcp_const.Side_Sell
const_dict["call"] = mcp_const.Call_Option
const_dict["put"] = mcp_const.Put_Option


# def pf_const(val):
#     key = str(val).lower()
#     if key in const_dict:
#         return const_dict[key]
#     else:
#         return val
def pf_const(val, enum_name=None):
    return enum_wrapper.parse2(val, enum_name)


def pf_object(val):
    if isinstance(val, str):
        raise Exception("Invalid object: " + val)
    return val


def pf_json_list(val):
    return json.loads(val)


def pf_nd_arrary_or_list(val):
    if isinstance(val, numpy.ndarray):
        return val.tolist()
    else:
        return val


def pf_object_list(val):
    return json.dumps(pf_nd_arrary_or_list(val))


def fmt_xls_array(val):
    temp = []
    if len(val) > 0:
        if isinstance(val[0], list):
            for item in val:
                temp.extend(item)
            val = temp
    return val


def pf_array_date(val):
    temp = fmt_xls_array(val)
    temp = [pf_date(item) for item in temp]
    return temp


def pf_array(val):
    return fmt_xls_array(val)


def pf_array_date_json(val):
    temp = fmt_xls_array(val)
    temp = [pf_date(item) for item in temp]
    return json.dumps(temp)


def pf_array_json(val):
    return json.dumps(fmt_xls_array(val))


def parse_dict_list(args):
    if isinstance(args, dict):
        result = []
        for key in args:
            result.append([key, args[key]])
        return result
    elif isinstance(args, DataFrame):
        result = []
        cols = args.columns.tolist()
        for col in cols:
            result.append([col, args[col].tolist()])
        return result
    else:
        return pf_nd_arrary_or_list(args)


class KeyValueWrapper():

    def __init__(self):
        self.kv_dict = {}
        self.parse_func_dict = {
            "int": pf_int,
            "date": pf_date,
            "datetime": pf_date_time,
            "str": pf_str,
            "float": pf_float,
            "bool": pf_bool,
            "intbool": pf_int_bool,
            "calendar": pf_mcp_handler,
            "curve": pf_mcp_handler,
            "list": pf_mcp_list,
            "plainlist": pf_mcp_plain_list,
            "datelist": pf_mcp_date_list,
            "object": pf_object,
            "mcphandler": pf_mcp_handler,
            "const": pf_const,
            "vdate": pf_vdate,
            "vfloat": pf_vfloat,
            "jsonlist": pf_json_list,
            "objectlist": pf_object_list,
            "array": pf_array,
            "array_date": pf_array_date,
            "array_json": pf_array_json,
            "array_date_json": pf_array_date_json,
        }
        self.method_dict = {}
        self.all_keys = {}
        self.args_parser: ArgsParser = None
        self.raise_parse_exception = True

    def _std_key_result(self, result):
        keys = []
        vals = []
        for key in result:
            keys.append(key)
            vals.append(result[key])
        return {
            "keys": keys,
            "vals": vals,
            "result": result
        }

    def args_list_std_key(self, args_list, fmt="VP"):
        result = {}
        # mcp_kv_wrapper.
        args_list = self.std_all_args(args_list, fmt, [])
        for args in args_list:
            for item in args:
                if len(item) >= 2:
                    view = item[0]
                    key = str(view).lower()
                    if key in self.all_keys:
                        key = self.all_keys[key]
                    else:
                        key = view
                    result[key] = item[1]
        return self._std_key_result(result)

    def args_std_key(self, args):
        result = {}
        for item in args:
            if len(item) >= 2:
                view = item[0]
                key = str(view).lower()
                if key in self.all_keys:
                    key = self.all_keys[key]
                else:
                    key = view
                result[key] = item[1]
        return self._std_key_result(result)

    def add_method(self, method, kvs):
        lower_keys = {}
        parse_dict = {}
        reverse_keys = {}
        keys = []
        val_dict = {}
        for kv in kvs:
            # view, fk = kv
            view = kv[0]
            fk = kv[1]
            key = str(view).lower()
            keys.append(key)
            lower_keys[key] = view
            parse_dict[key] = str(fk).lower()
            reverse_keys[view] = key
            self.all_keys[key] = view
            if len(kv) >= 3:
                val_default = kv[2]
                val_dict[key] = val_default

        sub_dict = {
            "keys": keys,
            "lower_keys": lower_keys,
            "parse_dict": parse_dict,
            "reverse_keys": reverse_keys,
            "val_dict": val_dict
        }
        # print("add_method:", sub_dict)
        self.kv_dict[method] = sub_dict
        self.method_dict[method.lower()] = method

    def get_method_dict(self, method):
        method = method.lower()
        if method not in self.method_dict:
            return None
        method = self.method_dict[method]
        return self.kv_dict[method]

    def parse_val_func(self, func_key):
        if func_key in self.parse_func_dict:
            return self.parse_func_dict[func_key]
        else:
            return pf_none

    def prase_range_vals(self, method, args_list):
        # vals = []
        # for args in args_list:
        #     vals.append(self.parse_vals(method, args))
        # return self.merge_vals(method, vals)
        raw_dict = self.parse_raw_range_vals(args_list)
        return self.raw_to_std_result(method, raw_dict)

    def parse_raw_vals(self, args):
        result = {}
        for arg in args:
            if len(arg) >= 2:
                key = str(arg[0]).lower()
                result[key] = arg[1]
        return result

    def parse_raw_range_vals(self, args_list):
        args = []
        for item in args_list:
            args.extend(item)
        return self.parse_raw_vals(args)

    def raw_to_std_result(self, method, raw_dict):
        temp_dict = {}
        sub_dict = self.kv_dict[method]
        parse_dict = sub_dict["parse_dict"]
        for key in raw_dict:
            if key in parse_dict:
                raw_val = raw_dict[key]
                fk = parse_dict[key]
                f = self.parse_val_func(fk)
                try:
                    if f == pf_const:
                        val = pf_const(raw_val, key)
                    else:
                        val = f(raw_val)
                    temp_dict[key] = val
                except Exception as e:
                    if self.raise_parse_exception:
                        raise e
        result = self._std_parse_result(sub_dict, temp_dict)
        return result

    def parse_and_validate3(self, method, args_list, kvs):
        if method not in self.kv_dict:
            self.add_method(method, kvs)
        raw_dict = self.parse_raw_range_vals(args_list)
        result = self.raw_to_std_result(method, raw_dict)
        lack_keys = self.validate_all_fields(method, result)
        return result, lack_keys, raw_dict

    def valid_parse(self, method, args_list, fmt, data_fields, kvs, kvs2=None):
        # args = mcp_kv_wrapper.std_all_args(args_list, fmt, data_fields)
        # if method not in self.kv_dict:
        #     self.add_method(method, kvs)
        # result, lack_keys = self.parse_and_validate(method, args)
        # if kvs2 is not None:
        #     method2 = method + "2"
        #     if method2 not in self.kv_dict:
        #         self.add_method(method2, kvs2)
        #     result2, lack_keys2 = self.parse_and_validate(method2, args)
        #     if len(lack_keys2) < len(lack_keys):
        #         result = result2
        #         lack_keys = lack_keys2
        # return result, lack_keys
        kv_list = []
        if kvs2 is not None:
            kv_list.append(kvs2)
        return self.valid_parse_kv_list(method, args_list, fmt, data_fields, kvs, kv_list)

    def valid_parse_kv_list(self, method, args_list, fmt, data_fields, kvs, kv_list):
        args = mcp_kv_wrapper.std_all_args(args_list, fmt, data_fields)
        # print("std_all_args:", args)
        if method not in self.kv_dict:
            self.add_method(method, kvs)
        result, lack_keys = self.parse_and_validate(method, args)
        for i in range(len(kv_list)):
            kvs2 = kv_list[i]
            method2 = method + str(i)
            if method2 not in self.kv_dict:
                self.add_method(method2, kvs2)
            result2, lack_keys2 = self.parse_and_validate(method2, args)
            if len(lack_keys2) < len(lack_keys):
                result = result2
                lack_keys = lack_keys2
        return result, lack_keys

    def valid_parse3(self, method, args_list, fmt, data_fields, kvs):
        # print("valid_parse3: args_list=", args_list)
        args = mcp_kv_wrapper.std_all_args(args_list, fmt, data_fields)
        # print("valid_parse3: args=", args)
        return self.parse_and_validate3(method, args, kvs)

    def parse_and_validate2(self, method, args_list, kvs):
        if method not in self.kv_dict:
            self.add_method(method, kvs)
        return self.parse_and_validate(method, args_list)

    def parse_and_validate(self, method, args_list):
        result = self.prase_range_vals(method, args_list)
        lack_keys = self.validate_all_fields(method, result)
        return result, lack_keys

    def parse_vals(self, method, args):
        # # print("parse_vals:", args)
        # temp_dict = {}
        # sub_dict = self.kv_dict[method]
        # parse_dict = sub_dict["parse_dict"]
        # # print("sub_dict", sub_dict)
        # # print("parse_dict", parse_dict)
        # for arg in args:
        #     if len(arg) >= 2:
        #         key = str(arg[0]).lower()
        #         if key in parse_dict:
        #             fk = parse_dict[key]
        #             f = self.parse_val_func(fk)
        #             val = f(arg[1])
        #             temp_dict[key] = val
        # result = self._std_parse_result(sub_dict, temp_dict)
        # return result
        raw_dict = self.parse_raw_vals(args)
        return self.raw_to_std_result(method, raw_dict)

    def _std_parse_result(self, sub_dict, temp_dict):
        result_keys = []
        vals = []
        d = {}
        lower_keys = sub_dict["lower_keys"]
        keys = sub_dict["keys"]
        val_dict = sub_dict["val_dict"]
        for key in keys:
            view = lower_keys[key]
            val = None
            if key in temp_dict:
                val = temp_dict[key]
            elif key in val_dict:
                val = val_dict[key]
            if val is not None:
                result_keys.append(view)
                vals.append(val)
                d[view] = val
            # if key in temp_dict:
            #     result_keys.append(view)
            #     vals.append(temp_dict[key])
            #     d[view] = temp_dict[key]
        return {
            "keys": result_keys,
            "vals": vals,
            "dict": d,
        }

    def merge_vals(self, method, vals):
        sub_dict = self.kv_dict[method]
        reverse_keys = sub_dict["reverse_keys"]
        full_dict = {}
        for val in vals:
            val_dict = val["dict"]
            for k in val_dict:
                v = val_dict[k]
                key = reverse_keys[k]
                full_dict[key] = v
        result = self._std_parse_result(sub_dict, full_dict)
        # result["lack_keys"] = self.valid_key_value(method, result)
        return result

    def validate_all_fields(self, method, result):
        sub_dict = self.kv_dict[method]
        lack_keys = []
        lower_keys = sub_dict["lower_keys"]
        result_dict = result["dict"]
        keys = sub_dict["keys"]
        for key in keys:
            view = lower_keys[key]
            if view not in result_dict:
                lack_keys.append(view)
        return lack_keys

    def std_all_args(self, args, fmt: str, data_fields):
        return self.args_parser.parse_all(args, fmt, data_fields)

    def parse_data(self, data: list, fields):
        r = []
        if len(data) < 2:
            # raise Exception("Parse data exception")
            return r
        headers = []
        result = {}
        for header in data[0]:
            header = str(header).lower()
            headers.append(header)
            # result[header] = []
        # lack_keys = []
        kv = {}
        for field in fields:
            k, v = field
            k = str(k).lower()
            kv[k] = v
            result[k] = []
            # if k not in result:
            #     lack_keys.append(k)
        # if len(lack_keys) > 0:
        #     return result, lack_keys
        for i in range(1, len(data)):
            row = data[i]
            for j in range(len(headers)):
                header = headers[j]
                if header in result:
                    t = kv[header]
                    f = self.parse_func_dict[t]
                    v = f(row[j])
                    result[header].append(v)
        # r = []
        for key in result:
            vals = result[key]
            if len(vals) > 0:
                r.append([key, json.dumps(vals)])
        return r

    def set_fields(self, st: object, map):
        def lower_title(s: str):
            return s[0:1].lower() + s[1:]

        for key in map:
            k = lower_title(key)
            setattr(st, k, map[key])
            # st.__dict__[k] = map[key]


class KeyValueWrapperEx(KeyValueWrapper):

    def __init__(self):
        super().__init__()

    def parse_func(self, func_key):
        if func_key in self.parse_func_dict:
            return self.parse_func_dict[func_key]
        else:
            return pf_none

    def process_kv_list(self, args_list, fmt, data_fields, kv_list):
        args_dict = self.args_parser.parse_all(args_list, fmt, data_fields, True)
        return self.parse_args_dict(args_dict, kv_list)

    # def process_kv(self, args_list, fmt, data_fields, kv):
    #     args_dict = self.args_parser.parse_all(args_list, fmt, data_fields, True)
    #     return self._parse_kv(args_dict, kv)

    def plain_parse(self, args, kv):
        if len(args) != len(kv):
            raise Exception(f"Length not match: args={len(args)},fields={len(kv)}")
        args_dict = {}
        for i in range(len(args)):
            if args[i] is not None:
                args_dict[str(kv[i][0]).lower()] = args[i]
        return self._parse_kv(args_dict, kv)

    def parse_args_dict(self, args_dict, kv_list):
        lack_keys = None
        result = None
        lower_args = {}
        for key in args_dict:
            lower_args[str(key).lower()] = args_dict[key]
        for kv in kv_list:
            result1, lack_keys1 = self._parse_kv(lower_args, kv)
            if lack_keys is None or len(lack_keys1) < len(lack_keys):
                result, lack_keys = (result1, lack_keys1)
                # print(f"parse_args_dict lack_keys: {lack_keys1}, {kv}")
            if len(lack_keys) == 0:
                break
        result["args_dict"] = args_dict
        return result, lack_keys

    def _parse_kv(self, args_dict, kvs):
        lack_keys = []
        dt = {}
        lt = []
        keys = []
        # origin_dt = {}
        for kv in kvs:
            key = str(kv[0]).lower()
            val = None
            if key in args_dict:
                raw_val = args_dict[key]
                f = self.parse_func(kv[1])
                try:
                    if f == pf_const:
                        val = pf_const(raw_val, key)
                    else:
                        val = f(raw_val)
                except Exception as e:
                    if self.raise_parse_exception:
                        raise e
            if val is None and len(kv) >= 3:
                val = kv[2]
            if val is not None:
                keys.append(kv[0])
            else:
                lack_keys.append(kv[0])
            dt[key] = val
            # origin_dt[kv[0]] = val
            lt.append(val)
        result = {
            "keys": keys,
            "vals": lt,
            "dict": dt,
            # "args_dict": args_dict,
        }
        return result, lack_keys


class ArgsParser:

    def __init__(self, parse_func_dict):
        self.parse_func_dict = parse_func_dict
        self.custom_dict = {}

    def to_valid_data_type(self, data_fields):
        df = []
        for f, t in data_fields:
            t = str(t).lower()
            if t == "double":
                t = "vdouble"
            elif t == "date":
                t = "vdate"
            df.append((f, t))
        return df

    def parse_all(self, args, fmt: str, data_fields, dict_result=False):
        # print("parse_all raw:", args)
        fmt = str(fmt).upper()
        result = []
        if fmt is not None:
            fmts = fmt.split("|")
        else:
            fmts = []
        field_pair = None
        val_pair = None
        data_fields = self.to_valid_data_type(data_fields)
        for i in range(len(args)):
            data = args[i]
            # print("parse_all:", i, data)
            if len(data) == 1 and len(data[0]) == 1:
                # print("invalid data of:", data)
                continue
            if i < len(fmts):
                fm = fmts[i]
            else:
                fm = "VP"
            if fm == "DT":
                result.append([["@bd", data]])
            elif fm == "MT":
                temp = self.parse_matrix(data, data_fields)
                result.append(temp)
                #print(f"parse_all MT: {temp}")
            elif fm[1] == "P":
                result.append(self.parse_param(fm, data))
            elif fm[1] == "D":
                result.append(self.parse_data(fm, data, data_fields))
            elif fm[1] == "F":
                field_pair = (fm, data)
            elif fm[1] == "V":
                val_pair = (fm, data)
            elif fm[1] == "L":
                result.append(self.parse_list(fm, data))
            if field_pair is not None and val_pair is not None:
                result.append(self.parse_fs_vs(field_pair[0], field_pair[1], val_pair[0], val_pair[1]))
                field_pair = None
                val_pair = None
            # print("parse_all:", i, result)
        # print("parse_all std:", result)
        if dict_result:
            d = {}
            # print("parse_all:", result)
            for item in result:
                for sub_item in item:
                    # d[str(sub_item[0]).lower()] = sub_item[1]
                    d[str(sub_item[0])] = sub_item[1]
            return d
        else:
            return result

    def parse_matrix(self, data, data_fields):
        result = []
        _, kv = self.init_parse_data(data_fields)
        if len(data) >= 2 and len(data[0]) >= 2:
            keys = str(data[0][0]).split('/')
            if len(keys) >= 1:
                name = keys[0]
                dt = []
                for i in range(1, len(data)):
                    dt.append(data[i][1:])
                vol_rows = []
                for row in dt:
                    items = [str(item) for item in row]
                    vol_rows.append(",".join(items))
                dt_str = ";".join(vol_rows)
                result.append([name, dt_str])
            if len(keys) >= 2:
                name_row = keys[1]
                dt_row = []
                for i in range(1, len(data)):
                    dt_row.append(data[i][0])
                sub_result = self.parse_array_data(kv, name_row, dt_row)
                if sub_result is not None:
                    result.append(sub_result)
            if len(keys) >= 3:
                name_col = keys[2]
                dt_col = data[0][1:]
                sub_result = self.parse_array_data(kv, name_col, dt_col)
                if sub_result is not None:
                    result.append(sub_result)
        return result

    def parse_array_data(self, kv, key, arr):
        key_lower = key.lower()
        if key_lower in kv:
            tp = kv[key_lower]
            f = self.parse_func_dict[tp]
            return [key, [f(val) for val in arr]]
        else:
            return None

    def parse_fs_vs(self, ff, fd, vf, vd):
        fields = self.parse_array(ff, fd)
        vals = self.parse_array(vf, vd)
        return self.field_val_pair(fields, vals)

    def parse_array(self, fmt, data):
        r = []
        if fmt[0] == "V":
            r = [item[0] for item in data]
        elif fmt[0] == "H":
            r = data[0]
        return r

    def field_val_pair(self, fields, vals):
        r = []
        count = min(len(fields), len(vals))
        for i in range(count):
            r.append([fields[i], vals[i]])
        return r

    def parse_param(self, fmt, data: list):
        if fmt == "HP":
            return self.field_val_pair(data[0], data[1])
        else:
            return data

    def parse_list(self, fmt, data: list):
        result = []
        if fmt == 'VL':
            for line in data:
                if len(line) > 1:
                    result.append([line[0], line[1:]])
        elif fmt == 'HL':
            headers = data[0]
            for i in range(len(headers)):
                vals = [data[j][i] for j in range(1, len(data))]
                result.append([headers[i], vals])
        return result

    def parse_data(self, fmt, data: list, fields):
        result, kv = self.init_parse_data(fields)
        # print("parse_data:", kv, result)
        if fmt == "HD":
            headers = self.header_of_hd(data)
            # print("parse_data headers:", headers)
            for i in range(1, len(data)):
                row = data[i]
                for j in range(len(headers)):
                    header = headers[j]
                    if header in result:
                        if header in kv:
                            t = kv[header]
                            f = self.parse_func_dict[t]
                            v = f(row[j])
                            result[header].append(v)

        elif fmt == "VD":
            headers = self.header_of_vd(data)
            # print("parse_data headers:", headers)
            for i in range(0, len(data)):
                row = data[i]
                header = headers[i]
                if header in kv:
                    t = kv[header]
                    f = self.parse_func_dict[t]
                    for j in range(1, len(row)):
                        v = f(row[j])
                        result[header].append(v)
        r = self.parse_data_result(result)
        # print("parse_data r:", r)
        return r

    def parse_data_result(self, result):
        r = []
        for key in result:
            vals = result[key]
            if len(vals) > 0:
                r.append([key, vals])
                # r.append([key, json.dumps(vals)])

        return r

    def init_parse_data(self, fields):
        result = {}
        kv = {}
        for field in fields:
            k, v = field
            k = str(k).lower()
            kv[k] = v
            result[k] = []
        return result, kv

    def header_of_hd(self, data):
        headers = []
        for header in data[0]:
            header = str(header).lower()
            headers.append(header)
        return headers

    def header_of_vd(self, data):
        headers = []
        for row in data:
            header = str(row[0]).lower()
            headers.append(header)
        return headers

    def add_custom_parser(self, key, f):
        self.custom_dict[key] = f


mcp_kv_wrapper = KeyValueWrapperEx()
mcp_kv_wrapper.args_parser = ArgsParser(mcp_kv_wrapper.parse_func_dict)


class MethodArgsCache():

    def __init__(self):
        self.cache_dict = {}
        self.key_count = 0

    def generate_key(self):
        self.key_count += 1
        key = "cache_key@" + str(self.key_count)
        return key

    def cache(self, key, args):
        # self.cache_dict[key] = args
        pass

    def get_cache(self, key):
        if key in self.cache_dict:
            return self.cache_dict[key]
        else:
            return None


mcp_method_args_cache = MethodArgsCache()


class ExcelDataCache():

    def __init__(self):
        self.cache_dict = {}
        self.key_count = 0

    def cache(self, key_word, data):
        key = key_word + " " + str(datetime.now())
        if key in self.cache_dict:
            time.sleep(0.001)
            key = key_word + " " + str(datetime.now())
        self.cache_dict[key] = data
        return key

    def get_cache(self, key):
        if key in self.cache_dict:
            return self.cache_dict[key]
        else:
            # return pd.DataFrame([""], columns=[""])
            return [[]]


data_cache = ExcelDataCache()


def xls_raw_dict(result, kvs_list):
    const_dict = {}
    for kvs in kvs_list:
        for kv in kvs:
            if kv[1] == "const":
                const_dict[kv[0]] = kv[0]
    d = {}
    keys = result["keys"]
    vals = result["vals"]
    raw_dict = result["args_dict"]
    for i in range(len(vals)):
        if is_mcp_wrapper(vals[i]):
            pass
        else:
            d[keys[i]] = vals[i]
    # del_list = ["VolSurface", "Calendar", "UndCurve", "AccCurve"]
    # for item in del_list:
    #     if item in d:
    #         del d[item]
    # update_list = ["DayCounter", "BuySell"]
    # for item in update_list:
    #     if item in d and item in raw_dict:
    #         d[item] = raw_dict[item]
    for key in d:
        if key in const_dict:
            d[key] = raw_dict[key]
    return d
