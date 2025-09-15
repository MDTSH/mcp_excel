import importlib
import json
import logging
import math
import traceback
from datetime import datetime
from enum import Enum, IntEnum

import pandas as pd

import mcp.mcp
from mcp.utils.enums import enum_wrapper, FXInterpolationType, InterpolatedVariable, CalculateTarget, CallPut
from mcp.utils.mcp_utils import debug_del_info, mcp_dt, mcp_const, lower_key_dict
from mcp.utils.svi import MSurfaceVol

from mcp.mcp import *

def is_mcp_wrapper(obj):
    return hasattr(obj, "is_mcp_wrapper")
    # or hasattr(obj, "getHandler")
    # return hasattr(obj, "getHandler")


def get_handler_wrapper(obj):
    if hasattr(obj, "getHandler"):
        return obj.getHandler()
    else:
        return obj


def to_mcp_args(args):
    result = []
    for item in args:
        if is_mcp_wrapper(item):
            result.append(item.getHandler())
        else:
            result.append(item)
    return result


def find_args_def_kv(tool_def, name, count, vals):
    item = tool_def.get_item(name)
    if item is None:
        return None, None
    kv = item.find_match_kv_list(count, vals)
    return kv, item
    # for kv in item.init_kv_list:
    #     if len(kv) == count:
    #         return kv, item
    # return [], item


def kv_to_view(kv, index, val, item_def):
    key = str(index)
    if index < len(kv):
        key = kv[index][0]
        t = kv[index][1]
        if t == 'const':
            val = enum_wrapper.key_of_value(val, item_def.get_const_field_enum(key))
    return key, val


def trace_args(obj, tool_def=None):
    if tool_def is None:
        tool_def = mcp_wrapper_utils.tool_def
    result = []
    view = []
    args_len = len(obj.raw_args)
    mcp_name = obj.__class__.__name__
    kv, item_def = find_args_def_kv(tool_def, mcp_name, args_len, obj.raw_args)
    for i in range(args_len):
        # for item in obj.raw_args:
        item = obj.raw_args[i]
        if is_mcp_wrapper(item):
            ta = trace_args(item, tool_def)
            result.append(ta)
            key = kv[i][0]
            val = ta
            vals = [key, val]
        else:
            result.append(item)
            key, val = kv_to_view(kv, i, item, item_def)
            if val == item:
                vals = [key, val]
            else:
                vals = [key, val, item]
        view.append(vals)
    return {
        "mcp_name": mcp_name,
        # "mcp_args": result,
        "mcp_args": view,
    }


cls_dict = {}


def get_cls(module_name, class_name):
    key = f"{module_name}@{class_name}"
    if key not in cls_dict:
        mdl = importlib.import_module(module_name)
        cls = getattr(mdl, class_name)
        cls_dict[key] = cls
        # print(f"get_cls create: {key}")
    return cls_dict[key]


def create_object_instance(module_name, class_name, args):
    cls = get_cls(module_name, class_name)
    return cls(*args)
    # mdl = importlib.import_module(module_name)
    # cls = getattr(mdl, class_name)
    # return cls(*args)


def create_object(trace_args):
    mcp_name = trace_args["mcp_name"]
    mcp_args = trace_args["mcp_args"]
    if 'package' in trace_args:
        pkg = trace_args['package']
    else:
        pkg = "mcp.wrapper"
    args = []
    for item in mcp_args:
        if len(item) == 3:
            val = item[2]
        else:
            val = item[1]
        if isinstance(val, dict):
            if "mcp_name" in val:
                args.append(create_object(val))
                continue
        args.append(val)
    module = importlib.import_module(pkg)
    cls = getattr(module, mcp_name)
    return cls(*args)


class McpLogging:

    def __init__(self):
        self.to_print = True

    def info(self, msg, exc_info=False):
        logging.info(msg, exc_info=exc_info)
        # print(msg)
        # if self.to_print:
        #     print(msg)
        #     if exc_info:
        #         traceback.print_exc()
        # else:
        #     logging.info(msg, exc_info=exc_info)


mcp_logging = McpLogging()


class McpCalendar(mcp.mcp.MCalendar):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f"McpCalendar args: {args}")
        super().__init__(*mcp_args)


class WrapperUtils:

    def __init__(self):
        self.tool_def = None


mcp_wrapper_utils = WrapperUtils()


class McpSnowBall(mcp.mcp.MSnowBall):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")

    def greek(self):
        return {
            "Gamma": self.Gamma(),
            "Delta": self.Delta(),
            "Vega": self.Vega(),
            "Theta": self.Theta(),
            "Rho": self.Rho(),
        }


class McpAutoCall(mcp.mcp.MAutoCall):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpPhenix(mcp.mcp.MPhenix):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpBarrierAutoCall(mcp.mcp.MBarrierAutoCall):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpTongXinAutoCall(mcp.mcp.MTongXinAutoCall):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpDoubleRanges(mcp.mcp.MDoubleRanges):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpTrippleRanges(mcp.mcp.MTrippleRanges):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpBDTTree(mcp.mcp.MBDTTree):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


class McpBDTData(mcp.mcp.MBDTData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        print(self.__class__.__name__, "super.__init__")


# class McpBondCurve(mcp.mcp.MBondCurve):
#
#     def __init__(self, *args):
#         self.raw_args = args
#         self.is_mcp_wrapper = True
#         mcp_args = to_mcp_args(args)
#         super().__init__(*mcp_args)
#         print(self.__class__.__name__, "super.__init__")


class McpDayCounter(mcp.mcp.MDayCounter):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        # print(self.__class__.__name__, "super.__init__")

    def __del__(self):
        self.Dispose()
        if debug_del_info:
            print("DayCounter del")


class McpYieldCurve(mcp.mcp.MYieldCurve):
    ins_count = 0
    ins_del_count = 0

    def __init__(self, *args):
        McpYieldCurve.ins_count += 1
        # print(f'McpYieldCurve args: {args}')
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print("McpYieldCurve args:", mcp_args)
        super().__init__(*mcp_args)
        # print(self.__class__.__name__, "super.__init__")

    def DiscountFactor(self, endDate):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().DiscountFactor(endDate)

    def ZeroRate(self, endDate):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().ZeroRate(endDate)

    def DiscountFactors(self, dates):
        # if isinstance(dates, str):
        #     dates = json.loads(dates)
        return [self.DiscountFactor(date) for date in dates]

    def ZeroRates(self, dates):
        # if isinstance(dates, str):
        #     dates = json.loads(dates)
        return [self.ZeroRate(date) for date in dates]

    def __del__(self):
        del self.raw_args
        # self.Dispose()
        # McpYieldCurve.ins_del_count += 1
        if debug_del_info:
            print("YieldCurve del")


class McpYieldCurve2(mcp.mcp.MYieldCurve2):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def DiscountFactor(self, endDate, bidMidAsk='MID'):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().DiscountFactor(endDate, bidMidAsk)

    def ZeroRate(self, endDate, bidMidAsk='MID'):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().ZeroRate(endDate, bidMidAsk)


class ForwardUtils:

    @staticmethod
    def calc_forward(spot_px, t, acc_rate, und_rate, rate_type=InterpolatedVariable.CONTINUOUSRATES):
        if rate_type == InterpolatedVariable.SIMPLERATES:
            # return (1 + (acc_rate - und_rate) * time_to_expiry) * spot_px
            return spot_px * (1 + acc_rate * t) / (1 + und_rate * t)
        else:
            return math.exp((acc_rate - und_rate) * t) * spot_px

    @staticmethod
    def calc_und_rate(spot_px, t, acc_rate, forward, rate_type=InterpolatedVariable.CONTINUOUSRATES):
        if t == 0:
            t = 0.000001
        if rate_type == InterpolatedVariable.SIMPLERATES:
            # return acc_rate - (forward / spot_px - 1) / time_to_expiry
            return (spot_px / forward * (1 + acc_rate * t) - 1) / t
        else:
            return acc_rate - math.log(forward / spot_px) / t

    @staticmethod
    def calc_all(spot_px, time_to_expiry, acc_rate, und_rate, forward, calc_target=CalculateTarget.UndRate,
                 rate_type=InterpolatedVariable.CONTINUOUSRATES):
        if calc_target == CalculateTarget.Forward:
            forward = ForwardUtils.calc_forward(spot_px, time_to_expiry, acc_rate, und_rate, rate_type)
        else:
            und_rate = ForwardUtils.calc_und_rate(spot_px, time_to_expiry, acc_rate, forward, rate_type)
        return forward, und_rate

    @staticmethod
    def bid_ask_sign(buy_sell, call_put, is_client=False, is_mid=False):
        if call_put is None:
            side_spot = MktDataSide.Mid
            side_acc = MktDataSide.Mid
            side_und = MktDataSide.Mid
        else:
            if (buy_sell == mcp_const.Side_Buy and call_put == mcp_const.Call_Option) or (
                    buy_sell == mcp_const.Side_Sell and call_put == mcp_const.Put_Option):
                side_spot = MktDataSide.Bid
                side_acc = MktDataSide.Bid
                side_und = MktDataSide.Ask
            else:
                side_spot = MktDataSide.Ask
                side_acc = MktDataSide.Ask
                side_und = MktDataSide.Bid
        if buy_sell == mcp_const.Side_Buy:
            side_vol = MktDataSide.Bid
        else:
            side_vol = MktDataSide.Ask
        if is_mid:
            side_spot, side_acc, side_und, side_vol = MktDataSide.Mid, MktDataSide.Mid, MktDataSide.Mid, MktDataSide.Mid
        elif is_client:
            side_spot, side_acc, side_und, side_vol = ForwardUtils.opposite_side(side_spot, side_acc, side_und,
                                                                                 side_vol)
        return side_spot, side_acc, side_und, side_vol

    @staticmethod
    def opposite_side(*args):
        arr = []
        for item in args:
            if item == MktDataSide.Bid:
                arr.append(MktDataSide.Ask)
            elif item == MktDataSide.Ask:
                arr.append(MktDataSide.Bid)
            else:
                arr.append(MktDataSide.Mid)
        return tuple(arr)

    @staticmethod
    def premium_to_pips(amt, premium):
        return premium / amt * 10000

    @staticmethod
    def pips_to_premium(amt, pips):
        return pips / 10000 * amt


class MktDataSide(IntEnum):
    Mid = 0
    Bid = 1
    Ask = -1

class McpForwardCurve2(mcp.mcp.MForwardCurve2):
    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def GetCurve(self, bidMidAsk):
        return super().GetCurve(bidMidAsk)

    def ForwardRate(self, endDate, bidMidAsk):
        return super().ForwardRate(endDate, bidMidAsk)

class McpForwardCurve(mcp.mcp.MForwardCurve):
    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def ForwardRate(self, endDate):
        return super().ForwardRate(endDate)

def McpForwardCurveForward2ImpliedBaseRate(pair, forward, spot, termRate, spotDate, deliveryDate):
    return MFXForwardPointsCurve_Forward2ImpliedBaseRate(pair, forward, spot, termRate, spotDate, deliveryDate);

def McpForwardCurveForward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate, deliveryDate):
    return MFXForwardPointsCurve_Forward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate, deliveryDate);

def McpForwardCurveImpliedForward(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate):
    return MFXForwardPointsCurve_ImpliedForward(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate);

def McpForwardCurveImpliedFwdPoints(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate):
    return MFXForwardPointsCurve_ImpliedFwdPoints(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate);


class McpVolSurface2(mcp.mcp.MVolSurface2):
    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def GetVolatility(self, strike, expiryDate, bidMidAsk="BID"):
        return super().GetVolatility(strike, expiryDate, bidMidAsk)

    def get_strike_vol(self, strike, expiry_date, side=MktDataSide.Mid, forward=0.0):
        return self.GetVolatility(strike, expiry_date, self.side_to_mcp(side))

    def GetForward(self, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk):
        return super().GetForward(expiryOrDeliveryDate, isDeliveryDate, bidMidAsk)

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        # mcp_logging.info(f"get_forward_rate: {expiry_date}, {side}, {self.side_to_mcp(side)}")
        args = [expiry_date, False, self.side_to_mcp(side)]
        val = self.GetForward(*args)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val

    def get_risk_rate(self, expiry_date, side=MktDataSide.Mid):
        # mcp_logging.info(f"get_forward_rate: {expiry_date}, {side}, {self.side_to_mcp(side)}")
        args = [expiry_date, False, self.side_to_mcp(side)]
        val = self.GetRiskFreeRate(*args)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val

    def side_to_mcp(self, side):
        if side == MktDataSide.Bid:
            return 'BID'
        elif side == MktDataSide.Ask:
            return 'ASK'
        else:
            return 'MID'

    def GetRiskFreeRate(self, expiryOrDeliveryDate, isDeliveryDate, bidMidAsk):
        return super().GetRiskFreeRate(expiryOrDeliveryDate, isDeliveryDate, bidMidAsk)

    def GetSpot(self, bidMidAsk):
        return super().GetSpot(bidMidAsk)

    def GetReferenceDate(self):
        return super().GetReferenceDate()

    def GetSpotDate(self):
        return super().GetSpotDate()

    def StrikeFromString(self,strikeString, bidMidAsk, callPutType,  expiryDate, spot=0.0, forward=0.0):
        return super().StrikeFromString(strikeString, bidMidAsk, callPutType, expiryDate, spot, forward)

    def get_strike_from_string(self, s, expiry, side=MktDataSide.Mid, call_put=CallPut.Call, spot=0.0, fwd=0.0):
        args = [s, self.side_to_mcp(side), call_put, expiry, spot]
        val = self.StrikeFromString(*args)
        # logging.debug(f"StrikeFromString: {val}, args={args}")
        return val

    def GetDividend(self):
        return super().GetDiviend()
    
    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return super().GetDividend()

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetRiskFreeRate(expiry_date, False, self.side_to_mcp(side))

    def DeltaStringFromStrike(self, strike, callPutType, underlyingRate):
        return super().DeltaStringFromStrike(strike, callPutType, underlyingRate)

    def ExpiryDates(self, bidMidAsk):
        s = super().ExpiryDates(bidMidAsk)
        try:
            return json.loads(s)
        except:
            return []

    def ExpiryTimes(self, bidMidAsk):
        return super().ExpiryTimes(bidMidAsk)

    def Strikes(self, bidMidAsk):
        s = super().Strikes(bidMidAsk)
        try:
            return json.loads(s)
        except:
            return []

    def Volatilities(self, bidMidAsk):
        s = super().Volatilities(bidMidAsk)
        try:
            return json.loads(s)
        except:
            return []

    def GetForwards(self, bidMidAsk):
        return super().GetForwards(bidMidAsk)

class McpMktVolSurface2(mcp.mcp.MMktVolSurface2):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        self.calc_target = args[8]
        self.rate_type = InterpolatedVariable.SIMPLERATES
        t1 = datetime.now()
        super().__init__(*mcp_args)
        t2 = datetime.now()
        # print(f"new vol using {int((t2 - t1).total_seconds() * 1000)}ms")

    def GetParams(self, expiryDate, bidMidAsk='MID'):
        s = super().GetParams(expiryDate, bidMidAsk)
        try:
            return json.loads(s)
        except:
            return []

    def side_to_mcp(self, side):
        if side == MktDataSide.Bid:
            return 'BID'
        elif side == MktDataSide.Ask:
            return 'ASK'
        else:
            return 'MID'

    def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
        return ForwardUtils.calc_all(spot_px, time_to_expiry, acc_rate, und_rate, forward,
                                     self.calc_target, self.rate_type)

    def get_spot(self, side=MktDataSide.Mid):
        return self.GetSpot(self.side_to_mcp(side))

    def get_forward_points(self, expiry_date, side=MktDataSide.Mid):
        return self.GetForwardPoint(expiry_date, False, self.side_to_mcp(side))

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        # mcp_logging.info(f"get_forward_rate: {expiry_date}, {side}, {self.side_to_mcp(side)}")
        args = [expiry_date, False, self.side_to_mcp(side)]
        val = self.GetForward(*args)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val

    # def GetVolatility(self, interpVariable, maturityDate, side="MID", forward=0.0,
    #                   deltaOrStrike=FXInterpolationType.STRIKE_INTERPOLATION):
    #     # print(f"GetVolatility:  {(interpVariable, maturityDate, side, forward)}")
    #     val = super().GetVolatility(interpVariable, maturityDate, side, deltaOrStrike, forward)
    #     # print(f"GetVolatility: {val}, {(interpVariable, maturityDate, side, forward)}")
    #     return val

    def GetVolatility(self, strike, expiryDate, bidMidAsk="BID", midForward = 0.0, bidInputDeltaVolPair='',asknputDeltaVolPair=''):
        return super().GetVolatility(strike, expiryDate, bidMidAsk,midForward,bidInputDeltaVolPair,asknputDeltaVolPair)

    def GetVolatilityByDeltaStr(self, deltaString, expiryDate, bidMidAsk="BID", midForward = 0.0, bidInputDeltaVolPair='',asknputDeltaVolPair=''):
        return super().GetVolatility(deltaString, expiryDate, bidMidAsk,midForward,bidInputDeltaVolPair,asknputDeltaVolPair)

    def get_strike_vol(self, strike, expiry_date, side=MktDataSide.Mid, forward=0.0):
        return self.GetVolatility(strike, expiry_date, self.side_to_mcp(side), forward)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetForeignRate(expiry_date, False, self.side_to_mcp(side))

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetDomesticRate(expiry_date, False, self.side_to_mcp(side))

    def get_strike_from_string(self, s, expiry, side=MktDataSide.Mid, call_put=CallPut.Call, spot=0.0, fwd=0.0):
        args = [s, self.side_to_mcp(side), call_put, expiry, spot, fwd]
        val = self.StrikeFromString(*args)
        # logging.debug(f"StrikeFromString: {val}, args={args}")
        return val

    def GetVolatilities(self, bidAskMid='MID'):
        arr = json.loads(super().GetVolatilities(bidAskMid))
        result = []
        for sub in arr:
            result.append([item for item in sub])
        return result

    def GetDeltaStrings(self):
        return json.loads(super().GetDeltaStrings())

    def GetTenors(self):
        return json.loads(super().GetTenors())

class McpFXVolSurface2(mcp.mcp.MFXVolSurface2):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        self.calc_target = args[8]
        self.rate_type = InterpolatedVariable.SIMPLERATES
        t1 = datetime.now()
        super().__init__(*mcp_args)
        t2 = datetime.now()
        # print(f"new vol using {int((t2 - t1).total_seconds() * 1000)}ms")

    def GetParams(self, expiryDate, bidMidAsk='MID'):
        s = super().GetParams(expiryDate, bidMidAsk)
        try:
            return json.loads(s)
        except:
            return []

    def side_to_mcp(self, side):
        if side == MktDataSide.Bid:
            return 'BID'
        elif side == MktDataSide.Ask:
            return 'ASK'
        else:
            return 'MID'

    def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
        return ForwardUtils.calc_all(spot_px, time_to_expiry, acc_rate, und_rate, forward,
                                     self.calc_target, self.rate_type)

    def get_spot(self, side=MktDataSide.Mid):
        return self.GetSpot(self.side_to_mcp(side))

    def get_forward_points(self, expiry_date, side=MktDataSide.Mid):
        return self.GetForwardPoint(expiry_date, False, self.side_to_mcp(side))

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        # mcp_logging.info(f"get_forward_rate: {expiry_date}, {side}, {self.side_to_mcp(side)}")
        args = [expiry_date, False, self.side_to_mcp(side)]
        val = self.GetForward(*args)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val

    # def GetVolatility(self, interpVariable, maturityDate, side="MID", forward=0.0,
    #                   deltaOrStrike=FXInterpolationType.STRIKE_INTERPOLATION):
    #     # print(f"GetVolatility:  {(interpVariable, maturityDate, side, forward)}")
    #     val = super().GetVolatility(interpVariable, maturityDate, side, deltaOrStrike, forward)
    #     # print(f"GetVolatility: {val}, {(interpVariable, maturityDate, side, forward)}")
    #     return val

    def GetVolatility(self, strike, expiryDate, bidMidAsk="BID", midForward=0.0, bidInputDeltaVolPair='',
                      asknputDeltaVolPair=''):
        return super().GetVolatility(strike, expiryDate, bidMidAsk, midForward, bidInputDeltaVolPair,
                                     asknputDeltaVolPair)

    def GetVolatilityByDeltaStr(self, deltaString, expiryDate, bidMidAsk="BID", midForward=0.0, bidInputDeltaVolPair='',
                                asknputDeltaVolPair=''):
        return super().GetVolatility(deltaString, expiryDate, bidMidAsk, midForward, bidInputDeltaVolPair,
                                     asknputDeltaVolPair)

    def get_strike_vol(self, strike, expiry_date, side=MktDataSide.Mid, forward=0.0):
        return self.GetVolatility(strike, expiry_date, self.side_to_mcp(side), forward)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetForeignRate(expiry_date, False, self.side_to_mcp(side))

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetDomesticRate(expiry_date, False, self.side_to_mcp(side))

    def get_strike_from_string(self, s, expiry, side=MktDataSide.Mid, call_put=CallPut.Call, spot=0.0, fwd=0.0):
        args = [s, self.side_to_mcp(side), call_put, expiry, spot, fwd]
        val = self.StrikeFromString(*args)
        # logging.debug(f"StrikeFromString: {val}, args={args}")
        return val

    def GetVolatilities(self, bidAskMid='MID'):
        arr = json.loads(super().GetVolatilities(bidAskMid))
        result = []
        for sub in arr:
            result.append([item for item in sub])
        return result

    def GetDeltaStrings(self):
        return json.loads(super().GetDeltaStrings())

    def GetTenors(self):
        return json.loads(super().GetTenors())


class McpMktData:

    def __init__(self, d):
        d = lower_key_dict(d)
        keys = ['BidVolSurface', 'AskVolSurface', 'BidFXForwardCurve', 'AskFXForwardCurve']
        lack_keys = []
        for key in keys:
            key_lower = key.lower()
            if key_lower not in d:
                lack_keys.append(key)
        if len(lack_keys) > 0:
            raise Exception(f"Missing fields: {lack_keys}")

        self.bid_vs = d[keys[0].lower()]
        self.ask_vs = d[keys[1].lower()]
        self.bid_fwd_curve = d[keys[2].lower()]
        self.ask_fwd_curve = d[keys[3].lower()]
        self.mid_vs = None

        rate_type_key = 'RateInterpolatedVariable'.lower()
        if rate_type_key in d:
            self.rate_type = enum_wrapper.parse2(d[rate_type_key], 'InterpolatedVariable')
        else:
            self.rate_type = InterpolatedVariable.CONTINUOUSRATES
        calc_target_key = 'CalculateTarget'.lower()
        if calc_target_key in d:
            self.calc_target = enum_wrapper.parse2(d[calc_target_key], 'CalculateTarget')
        else:
            self.calc_target = CalculateTarget.UndRate

    def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
        return ForwardUtils.calc_all(spot_px, time_to_expiry, acc_rate, und_rate, forward,
                                     self.calc_target, self.rate_type)

    def side_wrapper_spec(self, args, obj, f):
        arr = [obj]
        arr.extend(args)
        return f(*arr)

    def side_wrapper(self, side, object_bid, object_ask, args: list, f):
        if side == MktDataSide.Bid:
            return self.side_wrapper_spec(args, object_bid, f)
        elif side == MktDataSide.Ask:
            return self.side_wrapper_spec(args, object_ask, f)
        else:
            bid = self.side_wrapper_spec(args, object_bid, f)
            ask = self.side_wrapper_spec(args, object_ask, f)
            return (bid + ask) / 2

    def forward_points(self, fwd_curve, expiry_date):
        return fwd_curve.FXForwardPoints(expiry_date, 'Mid')

    def get_forward_points(self, expiry_date, side=MktDataSide.Mid):
        return self.side_wrapper(side, self.bid_fwd_curve, self.ask_fwd_curve, [expiry_date], self.forward_points)

    def forward_rate(self, fwd_curve, expiry_date):
        return fwd_curve.FXForwardOutright(expiry_date, 'Mid')

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.side_wrapper(side, self.bid_fwd_curve, self.ask_fwd_curve, [expiry_date], self.forward_rate)
        # if side == MktDataSide.Bid:
        #     return self.und_rate(expiry_date, self.bid_vs)
        # elif side == MktDataSide.Ask:
        #     return self.und_rate(expiry_date, self.ask_vs)
        # else:
        #     bid = self.und_rate(expiry_date, self.bid_vs)
        #     ask = self.und_rate(expiry_date, self.ask_vs)
        #     return (bid + ask) / 2

    def strike_vol(self, vs, strike, expiry_date, forward=0.0):
        return vs.GetVolatility(strike, expiry_date, forward)

    def get_strike_vol(self, strike, expiry_date, side=MktDataSide.Mid, forward=0.0):
        return self.side_wrapper(side, self.bid_vs, self.ask_vs, [strike, expiry_date, forward], self.strike_vol)
        # if side == MktDataSide.Bid:
        #     return self.strike_vol(strike, expiry_date, self.bid_vs)
        # elif side == MktDataSide.Ask:
        #     return self.strike_vol(strike, expiry_date, self.ask_vs)
        # else:
        #     if self.mid_vs is not None:
        #         return self.strike_vol(strike, expiry_date, self.mid_vs)
        #     else:
        #         bid = self.strike_vol(strike, expiry_date, self.bid_vs)
        #         ask = self.strike_vol(strike, expiry_date, self.ask_vs)
        #         return (bid + ask) / 2

    def und_rate(self, vs, expiry_date):
        return vs.get_und_rate(expiry_date)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.side_wrapper(side, self.bid_vs, self.ask_vs, [expiry_date], self.und_rate)
        # if side == MktDataSide.Bid:
        #     return self.und_rate(expiry_date, self.bid_vs)
        # elif side == MktDataSide.Ask:
        #     return self.und_rate(expiry_date, self.ask_vs)
        # else:
        #     if self.mid_vs is not None:
        #         return self.und_rate(expiry_date, self.mid_vs)
        #     else:
        #         bid = self.und_rate(expiry_date, self.bid_vs)
        #         ask = self.und_rate(expiry_date, self.ask_vs)
        #         return (bid + ask) / 2

    def acc_rate(self, vs, expiry_date):
        return vs.get_acc_rate(expiry_date)

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.side_wrapper(side, self.bid_vs, self.ask_vs, [expiry_date], self.acc_rate)
        # if side == MktDataSide.Bid:
        #     return self.acc_rate(expiry_date, self.bid_vs)
        # elif side == MktDataSide.Ask:
        #     return self.acc_rate(expiry_date, self.ask_vs)
        # else:
        #     if self.mid_vs is not None:
        #         return self.acc_rate(expiry_date, self.mid_vs)
        #     else:
        #         bid = self.acc_rate(expiry_date, self.bid_vs)
        #         ask = self.acc_rate(expiry_date, self.ask_vs)
        #         return (bid + ask) / 2


def is_vol_surface(vs):
    b = isinstance(vs, MOptVolSurface)
    b = b or isinstance(vs, mcp.wrapper.McpVolSurface)
    b = b or isinstance(vs, mcp.wrapper.McpMktVolSurface)
    b = b or isinstance(vs, mcp.wrapper.McpFXVolSurface)
    b = b or isinstance(vs, mcp.wrapper.McpFXVolSurface2)
    b = b or isinstance(vs, mcp.wrapper.McpMktData)
    b = b or isinstance(vs, mcp.mcp.MMktVolSurface2)
    b = b or isinstance(vs, mcp.mcp.MVolSurface2)
    return b


def get_volatility(vs, strike, expiry_date):
    b = is_vol_surface(vs)
    if b:
        return vs.GetVolatility(strike, expiry_date)
    else:
        return None


class MOptVolSurface():

    def __init__(self, *args):
        self.vs = args[0]
        self.yield_curve = args[1]
        self.und_rate = args[2]

    def GetVolatility(self, strike, expiry_date, type):
        if isinstance(self.vs, MSurfaceVol):
            return self.vs.GetVolatility(strike, expiry_date, type)
        elif isinstance(self.vs, mcp.mcp.MHistVols):
            return self.vs.GetVol(expiry_date)
        else:
            raise Exception("Invalid VolatilitySurface")

    def get_und_rate(self, expiry_date):
        return self.InterpolateRate(expiry_date, True, False)

    def get_acc_rate(self, expiry_date):
        return self.InterpolateRate(expiry_date, False, False)

    def InterpolateRate(self, expiry_date, is_acc, is_false=False):
        if (is_acc):
            return self.yield_curve.ZeroRate(expiry_date)
        else:
            return self.und_rate


# class McpVolSurface(mcp.mcp.MVolatilitySurface):

#     def __init__(self, *args):
#         self.rate_type = InterpolatedVariable.CONTINUOUSRATES
#         self.calc_target = CalculateTarget.UndRate
#         self.raw_args = args
#         self.is_mcp_wrapper = True
#         mcp_args = to_mcp_args(args)
#         super().__init__(*mcp_args)
#         # print(self.__class__.__name__, "super.__init__")

#     def GetVolatility(self, interpVariable, maturityDate, forward=0.0,
#                       deltaOrStrike=FXInterpolationType.STRIKE_INTERPOLATION):
#         return super().GetVolatility(interpVariable, maturityDate)

#     def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
#         forward = ForwardUtils.calc_forward(spot_px, time_to_expiry, acc_rate, und_rate)
#         return forward, und_rate

#     def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
#         return None

#     def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
#         return self.InterpolateRate(expiry_date, True, False)

#     def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
#         return self.InterpolateRate(expiry_date, False, False)

#     def get_strike_vol(self, strike, expiry_date, side='MID', forward=0):
#         return self.GetVolatility(strike, expiry_date, forward)

#     def __del__(self):
#         self.Dispose()
#         if debug_del_info:
#             print("vs del")

class McpVolSurface(mcp.mcp.MVolSurface):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        # print(self.__class__.__name__, "super.__init__")

    def __del__(self):
        self.Dispose()
        if debug_del_info:
            print("vs del")

class McpMktVolSurface(mcp.mcp.MMktVolSurface):
    ins_count = 0
    ins_del_count = 0

    def __init__(self, *args):
        McpMktVolSurface.ins_count += 1
        self.rate_type = InterpolatedVariable.CONTINUOUSRATES
        self.calc_target = args[15]  #CalculateTarget.UndRate
        self.raw_args = args
        self.is_mcp_wrapper = True
        self.und_curve = args[5]
        self.acc_curve = args[6]
        mcp_args = to_mcp_args(args)
        # print("McpMktVolSurface args: ", args)
        # print("McpMktVolSurface mcp_args: ", mcp_args)
        super().__init__(*mcp_args)
        # print(self.__class__.__name__, "super.__init__")

    def __del__(self):
        # del self.und_curve
        # del self.acc_curve
        # del self.raw_args
        self.Dispose()
        McpMktVolSurface.ins_del_count += 1
        if debug_del_info:
            print("mkt vs del")

    def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
        forward = ForwardUtils.calc_forward(spot_px, time_to_expiry, acc_rate, und_rate)
        return forward, und_rate

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        return None

    def InterpolateRate(self, expiry_date, b1, b2):
        if b1:
            return self.get_und_rate(expiry_date)
        else:
            return self.get_acc_rate(expiry_date)

    # def GetVolatility(self, interpVariable, maturityDate, forward=0.0,
    #                   deltaOrStrike=FXInterpolationType.STRIKE_INTERPOLATION):
    #     return super().GetVolatility(interpVariable, maturityDate, deltaOrStrike, forward)

    def GetVolatility(self, strike, expiryDate, forward=0.0, inputDeltaVolPair=''):
        return super().GetVolatility(strike, expiryDate, forward, inputDeltaVolPair)

    def GetVolatilityByDeltaStr(self, deltaString, expiryDate, forward=0.0, inputDeltaVolPair=''):
        return super().GetVolatility(deltaString, expiryDate, forward, inputDeltaVolPair)

    def get_strike_vol(self, strike, expiry_date, side='MID', forward=0.0):
        return self.GetVolatility(strike, expiry_date, forward)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.und_curve.ZeroRate(expiry_date)

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.acc_curve.ZeroRate(expiry_date)

def is_swig_object(obj):
    return "Swig Object" in str(obj)

class McpFXVolSurface(mcp.mcp.MFXVolSurface):
    ins_count = 0
    ins_del_count = 0

    def __init__(self, *args):
        if (is_swig_object(args)):
            self.raw_args = args
            self.is_mcp_wrapper = True
            mcp_args = to_mcp_args(args)
            # print(f'McpFixedRateBond mcp_args: {mcp_args}')
            super().__init__(*mcp_args)
        else:
            McpMktVolSurface.ins_count += 1
            self.rate_type = InterpolatedVariable.CONTINUOUSRATES
            self.calc_target = args[15]  #CalculateTarget.UndRate
            self.raw_args = args
            self.is_mcp_wrapper = True
            self.und_curve = args[5]
            self.acc_curve = args[6]
            mcp_args = to_mcp_args(args)
            # print("McpMktVolSurface args: ", args)
            # print("McpMktVolSurface mcp_args: ", mcp_args)
            super().__init__(*mcp_args)
            # print(self.__class__.__name__, "super.__init__")

    def __del__(self):
        # del self.und_curve
        # del self.acc_curve
        # del self.raw_args
        self.Dispose()
        McpMktVolSurface.ins_del_count += 1
        if debug_del_info:
            print("mkt vs del")

    def calc_all(self, spot_px, time_to_expiry, acc_rate, und_rate, forward):
        forward = ForwardUtils.calc_forward(spot_px, time_to_expiry, acc_rate, und_rate)
        return forward, und_rate

    def get_forward_rate(self, expiry_date, side=MktDataSide.Mid):
        return None

    def InterpolateRate(self, expiry_date, b1, b2):
        if b1:
            return self.get_und_rate(expiry_date)
        else:
            return self.get_acc_rate(expiry_date)

    # def GetVolatility(self, interpVariable, maturityDate, forward=0.0,
    #                   deltaOrStrike=FXInterpolationType.STRIKE_INTERPOLATION):
    #     return super().GetVolatility(interpVariable, maturityDate, deltaOrStrike, forward)

    def GetVolatility(self, strike, expiryDate, forward=0.0, inputDeltaVolPair=''):
        return super().GetVolatility(strike, expiryDate, forward, inputDeltaVolPair)

    def GetVolatilityByDeltaStr(self, deltaString, expiryDate, forward=0.0, inputDeltaVolPair=''):
        return super().GetVolatility(deltaString, expiryDate, forward, inputDeltaVolPair)

    def get_strike_vol(self, strike, expiry_date, side='MID', forward=0.0):
        return self.GetVolatility(strike, expiry_date, forward)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.und_curve.ZeroRate(expiry_date)

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.acc_curve.ZeroRate(expiry_date)

class McpRounder(mcp.mcp.MRounder):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpFixedRateBond(mcp.mcp.MFixedRateBond):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f'McpFixedRateBond mcp_args: {mcp_args}')
        super().__init__(*mcp_args)

    def Payments(self):
        s = super().Payments()
        return json.loads(s)

    def PaymentDates(self):
        s = super().PaymentDates()
        return json.loads(s)

    def curve_handler(self, curve):
        # if isinstance(curve, mcp.mcp.MYieldCurve) or isinstance(curve, mcp.mcp.MBondCurve):
        #     return curve.getHandler(), False
        # elif isinstance(curve, mcp.mcp.MParametricCurve):
        #     return curve.getHandler(), True
        # else:
        #     raise Exception('unsupported curve:' + str(curve))
        if isinstance(curve, mcp.mcp.MParametricCurve):
            return curve.getHandler(), True
        else:
            if hasattr(curve, "getHandler"):
                return curve.getHandler(), False
            else:
                raise Exception('unsupported curve:' + str(curve))

    def Price(self, curve):
        return super().Price(*self.curve_handler(curve))

    def FairValue(self, curve):
        return super().FairValue(*self.curve_handler(curve))

    def GSpread(self, yld, curve):
        return super().GSpread(yld, *self.curve_handler(curve))

    def ZSpread(self, yld, curve):
        return super().ZSpread(yld, *self.curve_handler(curve))

    def FrtbGirrDeltas(self, curve, ccyLocRate=1.0):
        curve, is_param = self.curve_handler(curve)
        s = super().FrtbGirrDeltas(curve, ccyLocRate, is_param)
        return json.loads(s)

    def FrtbGirrCurvature(self, curve, isUp=True, ccyLocRate=1.0):
        curve, is_param = self.curve_handler(curve)
        return super().FrtbGirrCurvature(curve, isUp, ccyLocRate, is_param)

    def KeyRateDuration(self, curve, tenors, adjustWithEffectiveDuration=True):
        s = json.dumps(tenors)
        try:
            curve, is_param = self.curve_handler(curve)
            raw = super().KeyRateDuration(curve, s, adjustWithEffectiveDuration, is_param)
            return json.loads(raw)
        except:
            print(f'KeyRateDuration except')
            return []

    def ForwardPrice(self, yld, forwardSettlementDate, curve):
        curve, is_param = self.curve_handler(curve)
        return super().ForwardPrice(yld, forwardSettlementDate, curve, is_param)
    
class McpVanillaSwap(mcp.mcp.MVanillaSwap):

    def __init__(self, *args):
        # if len(args) == 35:
        #     curve = args[0]
        #     origin_args = args
        #     args = list(args)[1:]
        #     args[1] = args[0]
        #     args[3] = args[0]
        #     args[9] = curve
        #     args[10] = curve
        #     args[26] = curve
        #     args[27] = curve
        #     # print("origin args:", origin_args)
        #     # print("args:", args)

        #print(f'McpVanillaSwap args: {args}')

        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print("McpVanillaSwap mcp_args:",mcp_args)
        super().__init__(*mcp_args)

    def FrtbGirrDeltas(self, ccyLocRate=1.0):
        s = super().FrtbGirrDeltas(ccyLocRate)
        return json.loads(s)

    def FixedLegs(self):
        vanillaSwap = self
        PaymentDates = json.loads(vanillaSwap.FixedLegPaymentDates())
        AccrStartDates = json.loads(vanillaSwap.FixedLegAccrStartDates())
        AccrEndDates = json.loads(vanillaSwap.FixedLegAccrEndDates())
        AccrDays = json.loads(vanillaSwap.FixedLegAccrDays())
        AccrYearFrac = json.loads(vanillaSwap.FixedLegAccrYearFrac())
        AccrRates = json.loads(vanillaSwap.FixedLegAccrRates())
        Payments = json.loads(vanillaSwap.FixedLegPayments())
        DiscountFactors = json.loads(vanillaSwap.FixedLegDiscountFactors())
        PVs = json.loads(vanillaSwap.FixedLegPVs())
        CumPVs = json.loads(vanillaSwap.FixedLegCumPVs())
        PaymentDateYearFracs = json.loads(vanillaSwap.FixedLegPaymentDateYearFracs())
        CFs = json.loads(vanillaSwap.FixedLegCFs())
        return pd.DataFrame({
            "PaymentDate": PaymentDates,
            "AccrStartDate": AccrStartDates,
            "AccrEndDate": AccrEndDates,
            "AccrDay": AccrDays,
            "AccrYearFrac": AccrYearFrac,
            "AccrRate": AccrRates,
            "Payment": Payments,
            "DiscountFactor": DiscountFactors,
            "PV": PVs,
            "CumPV": CumPVs,
            "PaymentDateYearFrac": PaymentDateYearFracs,
            # "CF": CFs,
        })

    def FloatingLegs(self):
        vanillaSwap = self
        PaymentDates = json.loads(vanillaSwap.FloatingLegPaymentDates())
        AccrStartDates = json.loads(vanillaSwap.FloatingLegAccrStartDates())
        AccrEndDates = json.loads(vanillaSwap.FloatingLegAccrEndDates())
        AccrDays = json.loads(vanillaSwap.FloatingLegAccrDays())
        AccrYearFrac = json.loads(vanillaSwap.FloatingLegAccrYearFrac())
        AccrRates = json.loads(vanillaSwap.FloatingLegAccrRates())
        Payments = json.loads(vanillaSwap.FloatingLegPayments())
        DiscountFactors = json.loads(vanillaSwap.FloatingLegDiscountFactors())
        PVs = json.loads(vanillaSwap.FloatingLegPVs())
        CumPVs = json.loads(vanillaSwap.FloatingLegCumPVs())
        PaymentDateYearFracs = json.loads(vanillaSwap.FloatingLegPaymentDateYearFracs())
        CFs = json.loads(vanillaSwap.FloatingLegCFs())
        return pd.DataFrame({
            "PaymentDate": PaymentDates,
            "AccrStartDate": AccrStartDates,
            "AccrEndDate": AccrEndDates,
            "AccrDay": AccrDays,
            "AccrYearFrac": AccrYearFrac,
            "AccrRate": AccrRates,
            "Payment": Payments,
            "DiscountFactor": DiscountFactors,
            "PV": PVs,
            "CumPV": CumPVs,
            "PaymentDateYearFrac": PaymentDateYearFracs,
            # "CF": CFs,
        })

class McpXCurrencySwap(mcp.mcp.MXCurrencySwap):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpCurrencySwapLeg(mcp.mcp.MCurrencySwapLeg):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpSchedule(mcp.mcp.MSchedule):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f"McpSchedule args: {args}")
        super().__init__(*mcp_args)

    def dates(self):
        s = super().dates()
        return json.loads(s)

    def asTimes(self, value_date):
        s = super().asTimes(value_date)
        return json.loads(s)


class McpVanillaOption(mcp.mcp.MVanillaOption):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def FrtbGirrCurvatures(self, yieldCurve1, yieldCurve2, calendar, isUp, ccy2LocRate):
        s = super().FrtbGirrCurvatures(get_handler_wrapper(yieldCurve1),
                                       get_handler_wrapper(yieldCurve2),
                                       get_handler_wrapper(calendar),
                                       isUp,
                                       ccy2LocRate)

        return json.loads(s)

    def FrtbGirrDeltas(self, yieldCurve1, yieldCurve2, calendar, ccy2LocRate):
        s = super().FrtbGirrDeltas(get_handler_wrapper(yieldCurve1),
                                   get_handler_wrapper(yieldCurve2),
                                   get_handler_wrapper(calendar),
                                   ccy2LocRate)
        return json.loads(s)



class McpFXForward(mcp.mcp.MFXForward):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpFXForward2(mcp.mcp.MFXForward2):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        self.strikePx = args[0]
        self.FXForwardPointsCurve2 = args[1]
        self.DiscountCurve = args[2]
        self.SettlementDate = args[3]
        self.BuySell = args[4]
        self.FaceAmount = args[5]
        self.Side = args[6]
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def MarketValue(self, isAmount):
        s = super().MarketValue(isAmount)
        return s
    
    def PV(self, isAmount):
        s = super().PV(isAmount)
        return s
    
    def Price(self, isAmount):
        s = super().Price(isAmount)
        return s

    def Delta(self, isAmount):
        s = super().Delta(isAmount)
        return s

    def Gamma(self, isAmount):
        s = super().Gamma(isAmount)
        return s

    def Theta(self, isAmount):
        s = super().Theta(isAmount)
        return s
    
    def Rho(self, isAmount):
        s = super().Rho(isAmount)
        return s

    def Vanna(self, isAmount):
        s = super().Vanna(isAmount)
        return s
    
    def Volga(self, isAmount):
        s = super().Volga(isAmount)
        return s

    def ForwardDelta(self, isAmount):
        s = super().ForwardDelta(isAmount)
        return s
    

class McpSwaptionCube(mcp.mcp.MSwaptionCube):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpBlack76Swaption(mcp.mcp.MBlack76Swaption):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpCapVolStripping(mcp.mcp.MCapVolStripping):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpCapletFloorlet(mcp.mcp.MCapletFloorlet):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpCapFloor(mcp.mcp.MCapFloor):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpSwapCurve(mcp.mcp.MSwapCurve):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f"McpSwapCurve args: {args}")
        # print(f"McpSwapCurve mcp_args: {args}")
        super().__init__(*mcp_args)


class McpParametricCurve(mcp.mcp.MParametricCurve):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpCalibrationSet(mcp.mcp.MCalibrationSet):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpBondCurve(mcp.mcp.MBondCurve):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
    
        # try:
        #     # print('McpBondCurve raw args:', args)
        #     self.raw_args = args
        #     mode = args[1]
        #     if isinstance(mode, str):
        #         mode = str(mode).lower()
        #         if mode == 'frb':
        #             args = self.parse_frb(args)
        #     # print('McpBondCurve args:', args)
        #     # self.raw_args = args
        #     self.is_mcp_wrapper = True
        #     mcp_args = to_mcp_args(args)
        #     # print('McpBondCurve mcp_args:', mcp_args)
        #     super().__init__(*mcp_args)
        # except:
        #     traceback.print_exc()
        #     raise Exception('McpBondCurve __init__ except')

    def parse_frb(self, args):
        args = list(args)
        # for item in args:
        #     print(f'***{item}')
        bc_args = args[0:5]
        MaturityDates = args[5]
        Frequencies = args[6]
        Coupons = args[7]
        YieldsOrDirtyPrice = args[8]
        DayCounter = args[9]
        IsYield = args[10]

        BumpAmounts = args[11]
        BUses = args[12]
        cal = args[13]

        dates = json.loads(MaturityDates)

        Coupons = self.ensure_length(Coupons, len(dates), 0)
        Frequencies = self.ensure_length(Frequencies, len(dates), 1)
        BumpAmounts = self.ensure_length(BumpAmounts, len(dates), 0)
        BUses = self.ensure_length(BUses, len(dates), 1)

        frbcd_args = [
            # 1,
            args[0],
            MaturityDates,
            Frequencies,
            Coupons,
            YieldsOrDirtyPrice,
            DayCounter,
            IsYield,
            BumpAmounts,
            BUses,
            cal.getHandler()
        ]
        # print(frbcd_args)
        # logging.info(f"MFixedRateBondCurveData args: {frbcd_args}")
        frbcd = mcp.mcp.MFixedRateBondCurveData(*frbcd_args)
        # print(frbcd)
        cs = McpCalibrationSet()
        cs.addData(frbcd.getHandler())
        cs.addEnd()
        bc_args[1] = cs
        return bc_args

    def ensure_length(self, s, count, default_val):
        if s is None or s == '':
            arr = []
        else:
            try:
                arr = json.loads(s)
            except:
                arr = []
        if len(arr) < count:
            for i in range(len(arr), count):
                arr.append(default_val)
        return json.dumps(arr)


class McpFXForwardPointsCurve(mcp.mcp.MFXForwardPointsCurve):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpFXForwardPointsCurve2(mcp.mcp.MFXForwardPointsCurve2):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def FXForwardPoints(self, endDate, bidMidAsk='MID'):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().FXForwardPoints(endDate, bidMidAsk)

    def FXForwardOutright(self, endDate, bidMidAsk='MID'):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().FXForwardOutright(endDate, bidMidAsk)


class McpOvernightRateCurveData(mcp.mcp.MOvernightRateCurveData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpBillCurveData(mcp.mcp.MBillCurveData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpBillFutureCurveData(mcp.mcp.MBillFutureCurveData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpVanillaSwapCurveData(mcp.mcp.MVanillaSwapCurveData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpRateConvention(mcp.mcp.MRateConvention):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpFixedRateBondCurveData(mcp.mcp.MFixedRateBondCurveData):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        # logging.info(f"McpFixedRateBondCurveData args: {args}")
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpAdjustmentTable(mcp.mcp.MAdjustmentTable):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        super().__init__()

class OptionDataRateType:
    Rate = 0
    YieldCurve = 1
    YieldCurve2 = 2

class McpOptionData(mcp.mcp.MOptionData):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        # print(f"McpOptionData args: {args}")
        self.asset_class = args[0]
        self.spot = args[1]
        self.risk_free_curve: McpYieldCurve = args[8]
        self.risk_free_rate = args[-2]
        self.underlying_rate = args[-1]
        self.is_risk_free_rate_curve = False
        mcp_args = to_mcp_args(args)
        print(f"McpOptionData mcp args: {mcp_args}")
        super().__init__(*mcp_args)


class McpLocalVol(mcp.mcp.MLocalVol):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
        # print(f"McpLocalVol args: {args}")
        # if len(args) == 18: #Forex
        #     self.ReferenceDate = args[0]
        #     self.Spot = args[1]
        #     self.ExpiryDates = args[2]
        #     self.OptionTypes = args[4]
        #     self.Strikes = args[3]
        #     self.Premiums = args[5]
        #     self.PremiumAdjusted = args[6]
        #     self.DomesticCurve = args[7]
        #     self.ForeignCurve = args[8]
        #     self.FxForwardPointsCurve = args[9]
        #     self.CalculatedTarget = args[10]
        #     self.LocalVolModel = args[11]
        #     self.LogLevel = args[12]
        #     self.TraceFile = args[13]
        #     self.Calendar = args[14]
        #     self.DateAdjusterRule = args[15]
        #     self.SpotDate = args[16]
        #     self.ImpVols = args[17]
        #     self.MiniStrikeSize = args[18]
        # elif len(args) == 16:  # Equity
        #     self.ReferenceDate = args[0]
        #     self.Spot = args[1]
        #     self.ExpiryDates = args[2]
        #     self.OptionTypes = args[3]
        #     self.Strikes = args[4]
        #     self.Premiums = args[5]
        #     self.RiskFreeRateCurve = args[6]
        #     self.Dividend = args[7]
        #     self.LocalVolModel = args[8]
        #     self.LogLevel = args[9]
        #     self.TraceFile = args[10]
        #     self.Calendar = args[11]
        #     self.DateAdjusterRule = args[12]
        #     self.SpotDate = args[13]
        #     self.ImpVols = args[14]
        #     self.MiniStrikeSize = args[15]
        # elif len(args) == 15:  #Future
        #     self.ReferenceDate = args[0]
        #     self.ExpiryDates = args[1]
        #     self.OptionTypes = args[2]
        #     self.Strikes = args[3]
        #     self.Premiums = args[4]
        #     self.RiskFreeRateCurve = args[5]
        #     self.ForwardCurve = args[6]
        #     self.LocalVolModel = args[7]
        #     self.LogLevel = args[8]
        #     self.TraceFile = args[9]
        #     self.Calendar = args[10]
        #     self.DateAdjusterRule = args[11]
        #     self.SpotDate = args[12]
        #     self.ImpVols = args[13]
        #     self.MiniStrikeSize = args[14]
        # mcp_args = to_mcp_args(args)
        # print(f"MLocalVol mcp args: {mcp_args}")
        # super().__init__(*mcp_args

    def get_forward_rate(self, expiry_date):
        val = self.GetForward(expiry_date, False)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val



class McpHistVols(mcp.mcp.MHistVols):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)
   

    def GetVolatility(self, expiry_date):
        val = self.GetVolatility(expiry_date, False)
        # logging.debug(f"GetForward: {val}, args={args}")
        return val


class McpSingleCumulative(mcp.mcp.MSingleCumulative):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpDoubleCumulative(mcp.mcp.MDoubleCumulative):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpEFXForward(mcp.mcp.EMFXForward):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpEFXSwap(mcp.mcp.MFXSwap):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

class McpVanillaStrategy(mcp.mcp.MVanillaStrategy):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)