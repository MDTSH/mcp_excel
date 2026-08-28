import importlib
import json
import logging
import math
import traceback
from datetime import datetime
from enum import Enum, IntEnum

from mcp.optional_deps import pandas as pd

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
            cls_name = item.__class__.__name__
            # Keep typed objects for MXCurrencySwap overload resolution.
            # Otherwise they are converted to void* and may hit unsafe/disabled constructors.
            # NOTE: MFXForwardPointsCurve / McpFXForwardPointsCurve are intentionally NOT
            # kept here because MFXVolSurface void* constructor does:
            #   mcp::FXForwardPointsCurve _fxFwdPts = *(mcp::FXForwardPointsCurve*)fxForwardPointsCurve;
            # If we pass MFXForwardPointsCurve* (wrapper) instead of mcp::FXForwardPointsCurve*,
            # the vtable pointer gets read as a vector size, causing "vector too long".
            # Both EMFXForward and MFXSwap have void* overloads that work correctly with getHandler().
            if cls_name in (
                "MCurrencySwapLeg",
                "McpCurrencySwapLeg",
            ):
                result.append(item)
            else:
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
        try:
            from mcp.calendar_holidays_path import attach_holidays_file_path

            attach_holidays_file_path(self, args)
        except Exception:
            pass


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

    def ZeroRate(self, endDate, dayCounter=-1, compounding=True, frequency=366):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().ZeroRate(endDate, dayCounter, compounding, frequency)

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


class McpXccyBasisCurve(mcp.mcp.MXccyBasisCurve):
    """交叉货币基差曲线（CrossCurrencySpreadCurve）。

    两条构造路径（与 testXccyBasisCurve 的 T1/T2 约定一致）：
      Path A（FX 远期点）：
        McpXccyBasisCurve(refDate, spotDate, endDates, forwardPoints,
                          usdDiscCurve, cnyCleanCurve, fxSpot, scaleFactor,
                          interpolatedVariable=5, interpolationMethod=2, useGlobalSolver=False)
        - forwardPoints 为含 scale 的原始点数（如 "128.5,95.2"），scaleFactor=1e4
        - fxSpot 为直标 CNY per USD
      Path B（基差互换）：
        McpXccyBasisCurve(refDate, spotDate, endDates, basisSpreads,
                          cnyEstCurve, usdEstCurve, usdDiscCurve, cnyCleanCurve,
                          fxSpot, interpolatedVariable=5, interpolationMethod=2, useGlobalSolver=False)
        - basisSpreads 为小数（如 "0.0015,0.0015" = +15bp，加在 CNY 腿上）

    注意：C++ 侧以 noop-deleter 引用输入曲线，raw_args 持有输入曲线引用防止悬空。
    """

    def __init__(self, *args):
        self.raw_args = args  # 持有输入 M 曲线引用，保证生命周期长于本对象
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def DiscountFactor(self, endDate):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().DiscountFactor(endDate)

    def DiscountFactor2(self, startDate, endDate):
        if isinstance(startDate, datetime):
            startDate = mcp_dt.to_date1(startDate)
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().DiscountFactor2(startDate, endDate)

    def ZeroRate(self, endDate, dayCounter=-1):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().ZeroRate(endDate, dayCounter)

    def Spread(self, endDate, dayCounter=-1):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        return super().Spread(endDate, dayCounter)


class McpCreditCurve(mcp.mcp.MCreditCurve):
    """Python 封装类，参考 McpYieldCurve。Excel 应返回 McpCreditCurve@0 而非 MCreditCurve@0"""

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpCreditDefaultSwap(mcp.mcp.MCreditDefaultSwap):
    """Python 封装类，参考 McpCreditCurve。Excel 应返回 McpCreditDefaultSwap@0 而非 MCreditDefaultSwap@0"""

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpCdsAdapter:
    """Python 封装类，参考 McpYieldCurve。Excel 应返回 McpCdsAdapter@0 而非 MCdsAdapter@0。内部持有 MCdsAdapter，委托所有调用。"""

    def __init__(self, adapter):
        self._adapter = adapter
        self.is_mcp_wrapper = True
        self.raw_args = getattr(adapter, '_cds_ref', ()) if hasattr(adapter, '_cds_ref') else ()

    def getInstance(self):
        return self._adapter

    def __getattr__(self, name):
        return getattr(self._adapter, name)


class McpClnAdapter:
    """Python 封装类，信用联结票据（CLN）Adapter。内部持有 MClnAdapter，委托所有调用。"""

    def __init__(self, adapter):
        self._adapter = adapter
        self.is_mcp_wrapper = True
        self.raw_args = getattr(adapter, '_cds_ref', ()) if hasattr(adapter, '_cds_ref') else ()

    def getInstance(self):
        return self._adapter

    def __getattr__(self, name):
        return getattr(self._adapter, name)


class McpBondAdapter:
    """Python 封装类，债券 Adapter。Excel 应返回 McpBondAdapter@0 而非 MBondAdapter@0。内部持有 MBondAdapter，委托所有调用。"""

    def __init__(self, adapter):
        self._adapter = adapter
        self.is_mcp_wrapper = True
        self.raw_args = ()

    def getInstance(self):
        return self._adapter

    def SetPreviousCurve(self, curve):
        """与 SWIG 重载一致：传入 MYieldCurve/MBondCurve/MSwapCurve 等包装类；勿传 getHandler() 裸指针。"""
        if curve is None:
            return
        return self._adapter.SetPreviousCurve(curve)

    def __getattr__(self, name):
        return getattr(self._adapter, name)


class McpRawMarketManager:
    """Python 封装类，Raw Market Data 管理器。Excel 应返回 McpRawMarketManager@0。内部持有 MRawMarketManager 或 RawMarketDataManager，委托所有调用。参考 EXCEL_INTEGRATION_PITFALLS 2.3。"""

    def __init__(self, manager):
        self._mgr = manager
        self.is_mcp_wrapper = True
        self.raw_args = ()

    def getInstance(self):
        return self._mgr

    def __getattr__(self, name):
        return getattr(self._mgr, name)


class McpMarketDataJsonReader:
    """单文件 MCP 市场 JSON（与 MRawMarketManager 目录模式对等）。内部为 MMarketDataJsonReader。"""

    def __init__(self, reader):
        self._r = reader
        self.is_mcp_wrapper = True
        self.raw_args = ()

    def getInstance(self):
        return self._r

    def __getattr__(self, name):
        return getattr(self._r, name)


_EXCEL_MCP_HANDLE_CLASSES = {}


def excel_mcp_object_handle(inner, display_class_name: str):
    """
    将 LiveStore/RawMD 返回的 M* SWIG 对象包装为 Excel 显示的 Mcp*@n 句柄。
    不能 Mcp*(getHandler()) 再构造（*2 类型仅支持 shared_ptr 重载）；委托全部方法到 inner。
    """
    if inner is None:
        return None
    if getattr(inner, "__class__", None).__name__ == display_class_name:
        if hasattr(inner, "getInstance"):
            return inner
        if not hasattr(inner, "_mcp_inner"):
            return inner
    Cls = _EXCEL_MCP_HANDLE_CLASSES.get(display_class_name)
    if Cls is None:

        def __init__(self, inner_obj):
            object.__setattr__(self, "_mcp_inner", inner_obj)
            object.__setattr__(self, "is_mcp_wrapper", True)
            object.__setattr__(self, "raw_args", ())

        def __getattr__(self, name):
            return getattr(object.__getattribute__(self, "_mcp_inner"), name)

        def getInstance(self):
            return object.__getattribute__(self, "_mcp_inner")

        Cls = type(
            display_class_name,
            (),
            {
                "__init__": __init__,
                "__getattr__": __getattr__,
                "getInstance": getInstance,
            },
        )
        _EXCEL_MCP_HANDLE_CLASSES[display_class_name] = Cls
    return Cls(inner)


class McpLiveMarketDataStore:
    """全量快照 + 增量 patch；get* 返回的 M* 指针在 applyUpdate 后保持稳定（原地换芯）。"""

    def __init__(self, store):
        self._s = store
        self.is_mcp_wrapper = True
        self.raw_args = ()

    def getInstance(self):
        return self._s

    def __getattr__(self, name):
        return getattr(self._s, name)


def md_json_reader_yield_curve2(reader, curve_id):
    """reader: mcp.mcp.MMarketDataJsonReader；返回 SWIG MYieldCurve2 或 None。"""
    return reader.getYieldCurve2(curve_id)


def md_json_reader_fx_forward_points_curve2(reader, curve_id):
    return reader.getFXForwardPointsCurve2(curve_id)


def md_json_reader_fx_vol_surface2(reader, curve_id):
    return reader.getFXVolSurface2(curve_id)


def md_live_store_yield_curve2(store, curve_id):
    return store.getYieldCurve2(curve_id)


def md_live_store_fx_forward_points_curve2(store, curve_id):
    return store.getFXForwardPointsCurve2(curve_id)


def md_live_store_fx_vol_surface2(store, curve_id):
    return store.getFXVolSurface2(curve_id)


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
    return MFXForwardPointsCurve.Forward2ImpliedBaseRate(pair, forward, spot, termRate, spotDate, deliveryDate);

def McpForwardCurveForward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate, deliveryDate):
    return MFXForwardPointsCurve.Forward2ImpliedTermRate(pair, forward, spot, baseRate, spotDate, deliveryDate);

def McpForwardCurveImpliedForward(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate):
    return MFXForwardPointsCurve.ImpliedForward(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate);

def McpForwardCurveImpliedFwdPoints(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate):
    return MFXForwardPointsCurve.ImpliedFwdPoints(pair,  baseRate,  termRate,  spot, spotDate,  deliveryDate);


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
        self.calc_target = args[8] if len(args) > 8 else None
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
        self.calc_target = args[8] if len(args) > 8 else None
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
    
    def GetVolatility(self, strike, expiryDate, forward=0.0):
        return super().GetVolatility(strike, expiryDate, forward)

    def get_strike_vol(self, strike, expiry_date, side='MID', forward=0.0):
        return self.GetVolatility(strike, expiry_date, forward)

    def get_und_rate(self, expiry_date, side=MktDataSide.Mid):
        return self.GetDividend()

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        # return self.acc_curve.ZeroRate(expiry_date)
        return self.GetRiskFreeRate(expiry_date, False)
    
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
        # return self.und_curve.ZeroRate(expiry_date)
        return self.GetForeignRate(expiry_date,  False, True)

    def get_acc_rate(self, expiry_date, side=MktDataSide.Mid):
        # return self.acc_curve.ZeroRate(expiry_date)
        return self.GetDomesticRate(expiry_date, False, True)

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


class McpAmortizingBond(mcp.mcp.MAmortizingBond):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def _loads(self, s):
        if s is None or s == "":
            return s
        try:
            return json.loads(s)
        except Exception:
            return s

    def Payments(self):
        return self._loads(super().Payments())

    def PaymentDates(self):
        return self._loads(super().PaymentDates())

    def InterestPayments(self):
        return self._loads(super().InterestPayments())

    def PrincipalPayments(self):
        return self._loads(super().PrincipalPayments())


class McpCommodityFuture(mcp.mcp.MCommodityFuture):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f'McpCommodityFuture mcp_args: {mcp_args}')
        super().__init__(*mcp_args)

    def curve_handler(self, curve):
        """
        统一处理曲线对象，返回 (handler, is_param) 元组
        用于 setDiscountCurve, setConvenienceYieldCurve, setForwardCurve 等方法
        """
        if isinstance(curve, mcp.mcp.MParametricCurve):
            return curve.getHandler(), True
        else:
            if hasattr(curve, "getHandler"):
                return curve.getHandler(), False
            else:
                raise Exception('unsupported curve:' + str(curve))

    def setDiscountCurve(self, curve):
        """设置折现曲线"""
        curve_handler, is_param = self.curve_handler(curve)
        return super().setDiscountCurve(curve_handler, is_param)

    def setConvenienceYieldCurve(self, curve):
        """设置便利收益率曲线"""
        curve_handler, is_param = self.curve_handler(curve)
        return super().setConvenienceYieldCurve(curve_handler, is_param)

    def setForwardCurve(self, curve):
        """设置远期曲线"""
        curve_handler, is_param = self.curve_handler(curve)
        return super().setForwardCurve(curve_handler, is_param)


class McpBondFuture(mcp.mcp.MBondFuture):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpEquityFuture(mcp.mcp.MEquityFuture):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpEquitySpot(mcp.mcp.MEquitySpot):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpFund(mcp.mcp.MFund):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpFXNDF(mcp.mcp.MFXNDF):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpRepurchaseProduct(mcp.mcp.MRepurchaseProduct):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpTotalReturnSwap(mcp.mcp.MTotalReturnSwap):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class _McpAdapterProxy:
    """代理基类：为 adapter 对象提供正确的 PyXLL 缓存 key 前缀（McpXxx@N）。
    所有属性/方法访问均透明转发给被包装的 C++ 对象。
    """
    is_mcp_wrapper = True

    def __init__(self, adapter):
        object.__setattr__(self, '_adapter', adapter)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_adapter'), name)

    def getHandler(self):
        a = object.__getattribute__(self, '_adapter')
        return a.getHandler() if hasattr(a, 'getHandler') else a


class McpTRSAdapter(_McpAdapterProxy):
    """MTRSAdapter 的 Python 代理，确保 PyXLL 缓存 key 为 McpTRSAdapter@N。"""

    def MarketParRate(self, discountCurve=None, fundingCurve=None):
        """委托给内部 _trs_ref 计算 par 融资费率，使 adapter 无需再单独构建 raw TRS 对象。

        若 discountCurve/fundingCurve 为 None，则自动使用 McpTRSAdapter 构造时已注入的曲线。
        当前标的价格也自动从 adapter 的 _underlying_price_ref 同步到 raw TRS。
        """
        trs_ref = self.__dict__.get('_trs_ref')
        if trs_ref is None:
            raise RuntimeError(
                "TRSAdapter.MarketParRate: 未找到内部 TRS 对象（_trs_ref）；"
                "请确认通过 McpTRSAdapter VP 块创建 adapter"
            )
        disc = discountCurve if discountCurve is not None else self.__dict__.get('_discount_curve_ref')
        fund = (fundingCurve if fundingCurve is not None
                else self.__dict__.get('_funding_curve_ref') or disc)
        if disc is None:
            raise RuntimeError(
                "TRSAdapter.MarketParRate: 未注入折现曲线，"
                "请在 McpTRSAdapter VP 块中设置 DiscountCurve"
            )
        price = self.__dict__.get('_underlying_price_ref')
        if price is not None and hasattr(trs_ref, 'setCurrentPrice'):
            trs_ref.setCurrentPrice(float(price))
        # MSwapCurve/MBondCurve 不继承 MYieldCurve，SWIG 重载解析会回落到 void* 重载，
        # 导致把 MSwapCurve* 直接 static_cast 成 mcp::YieldCurve* 造成非法内存访问崩溃。
        # 通过 getHandler() 提取底层 mcp::SwapCurve*/mcp::BondCurve* 指针（继承自 mcp::YieldCurve），
        # 作为 void* 传入后，C++ 中的 static_cast<mcp::YieldCurve*> 才是安全的。
        disc_arg = disc.getHandler() if hasattr(disc, 'getHandler') else disc
        fund_arg = fund.getHandler() if hasattr(fund, 'getHandler') else fund
        return trs_ref.MarketParRate(disc_arg, fund_arg)


def _bondtrs_freq_to_int(freq):
    """把 SEMIANNUAL/ANNUAL/QUARTERLY/MONTHLY 字符串映射为底层 enum int
    （与 BondTotalReturnSwap::CouponFrequency 一致：1/2/4/12）。
    数值传入则直接转 int（兼容 1/2/4/12 或 0/1/2/3 风格输入）。
    """
    if freq is None:
        return 2
    if isinstance(freq, (int, float)):
        v = int(freq)
        # 若用户传入旧的 0/1/2/3 风格，做一次桥接（0=ANNUAL, 1=SEMIANNUAL, 2=QUARTERLY, 3=MONTHLY）
        legacy_map = {0: 1, 1: 2, 2: 4, 3: 12}
        return legacy_map.get(v, v if v in (1, 2, 4, 12) else 2)
    s = str(freq).strip().upper()
    return {"ANNUAL": 1, "SEMIANNUAL": 2, "SEMI-ANNUAL": 2,
            "QUARTERLY": 4, "MONTHLY": 12}.get(s, 2)


# 兼容性兜底：若 _mcp.pyd 还没重编译（不含 MBondTRS / MBondTRSAdapter），
# 用占位类避免拖垮整个 wrapper 模块导入。真正调用时才报错提示用户去编译。
_HAS_MBONDTRS = hasattr(mcp.mcp, 'MBondTRS') and hasattr(mcp.mcp, 'MBondTRSAdapter')

if not _HAS_MBONDTRS:
    class _MissingMBondTRS:
        def __init__(self, *_, **__):
            raise RuntimeError(
                "MBondTRS / MBondTRSAdapter 未在 _mcp.pyd 中导出 — "
                "请重新编译 mcp_python（powershell scripts/build-mcp-python-for-mcpexcel.ps1）"
            )
    _MBondTRSBase = _MissingMBondTRS
else:
    _MBondTRSBase = mcp.mcp.MBondTRS


class McpBondTRS(_MBondTRSBase):
    """债券 TRS（BondTotalReturnSwap）的 Python 代理，缓存 key 为 McpBondTRS@N。

    构造参数顺序与 mcp::BondTotalReturnSwap 严格一致；所有比例均为小数：
        couponRate=0.07 表示 7%、initialCleanPrice=0.977879 表示 97.7879%
    couponFrequency 接受字符串（"SEMIANNUAL" 等）或 enum int（1/2/4/12）。
    """
    is_mcp_wrapper = True

    def __init__(self, bondIsin, faceValue, currency,
                 startDate, maturityDate,
                 initialCleanPrice, initialAccrued,
                 couponRate, couponFrequency, couponStartDate,
                 dayCounter, fixedFundingRate, direction,
                 paymentCalendar=None):
        self.raw_args = (bondIsin, faceValue, currency, startDate, maturityDate,
                         initialCleanPrice, initialAccrued, couponRate,
                         couponFrequency, couponStartDate, dayCounter,
                         fixedFundingRate, direction, paymentCalendar)
        cal_handle = get_handler_wrapper(paymentCalendar) if paymentCalendar is not None else None
        super().__init__(
            str(bondIsin),
            float(faceValue),
            str(currency or "CNY"),
            str(startDate),
            str(maturityDate),
            float(initialCleanPrice),
            float(initialAccrued),
            float(couponRate),
            int(_bondtrs_freq_to_int(couponFrequency)),
            str(couponStartDate),
            int(dayCounter),
            float(fixedFundingRate),
            int(direction),
            cal_handle,
        )


class McpBondTRSAdapter(_McpAdapterProxy):
    """MBondTRSAdapter 的 Python 代理，缓存 key 为 McpBondTRSAdapter@N。

    使用流程（Excel）：
        1. McpBondTRS(...)                          → McpBondTRS@N
        2. McpBondTRSAdapter(McpBondTRS, ...)       → McpBondTRSAdapter@N
        3. BondTrsSetDiscountCurve(adapter, curve)  → 注入折现曲线（CNH_SWAP）
        4. BondTrsSetCurrentPrice(adapter, price)   → 注入估值日净价（小数，如 0.977879）
        5. BondTrsNPV(adapter)                      → C++ BondTRSAdapter::calculateValuationMetrics()
        6. BondTrsAdapterCashflows(adapter)         → C++ BondTRSAdapter::calculateCashflows()

    构造重载：
        - McpBondTRSAdapter(McpBondTRS, instrument_id="", trade_id="", portfolio_key="")
        - McpBondTRSAdapter(data_dict)：字典构造（向后兼容旧 args_def 路径），
          字典字段与 DefMcpBondTRSAdapter.init_kv_list 对应。
    """

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            d = args[0]
            cal = d.get('PaymentCalendar')
            bond_trs = McpBondTRS(
                bondIsin=d.get('BondIsin', ''),
                faceValue=d.get('FaceValue', 0.0),
                currency=d.get('Currency', 'CNY'),
                startDate=d.get('StartDate'),
                maturityDate=d.get('MaturityDate'),
                initialCleanPrice=d.get('InitialCleanPrice', 0.0),
                initialAccrued=d.get('InitialAccrued', 0.0),
                couponRate=d.get('CouponRate', 0.0),
                couponFrequency=d.get('CouponFrequency', 'SEMIANNUAL'),
                couponStartDate=d.get('CouponStartDate'),
                dayCounter=int(d.get('DayCounter', 1)),
                fixedFundingRate=d.get('FixedFundingRate', 0.0),
                direction=int(d.get('Direction', 1)),
                paymentCalendar=cal,
            )
            instrument_id = str(d.get('InstrumentId', ''))
            trade_id = str(d.get('TradeId', ''))
            portfolio_key = str(d.get('PortfolioKey', ''))
        else:
            bond_trs = args[0] if args else kwargs.get('bondTrs')
            instrument_id = str(args[1] if len(args) > 1 else kwargs.get('instrument_id', ''))
            trade_id = str(args[2] if len(args) > 2 else kwargs.get('trade_id', ''))
            portfolio_key = str(args[3] if len(args) > 3 else kwargs.get('portfolio_key', ''))

        if not _HAS_MBONDTRS:
            raise RuntimeError(
                "MBondTRSAdapter 未在 _mcp.pyd 中导出 — "
                "请重新编译 mcp_python（powershell scripts/build-mcp-python-for-mcpexcel.ps1）"
            )
        if not isinstance(bond_trs, mcp.mcp.MBondTRS):
            raise TypeError("McpBondTRSAdapter: first argument must be McpBondTRS / MBondTRS")

        adapter = mcp.mcp.MBondTRSAdapter(bond_trs, instrument_id, trade_id, portfolio_key)
        super().__init__(adapter)
        object.__setattr__(self, '_bond_trs_ref', bond_trs)  # 防止 GC

    def MarketParRate(self, discountCurve=None):
        """委托给内部 _bond_trs_ref 计算 par 融资费率，使 adapter 无需另外构建 McpBondTRS 对象。

        若 discountCurve 为 None，则自动使用 BondTrsSetDiscountCurve 已注入的折现曲线。
        当前净价和估值日也自动从 adapter 存储的值同步到 raw BondTRS 对象。
        """
        bond_trs = object.__getattribute__(self, '_bond_trs_ref')
        curve = (discountCurve if discountCurve is not None
                 else self.__dict__.get('_mcp_bond_trs_discount_curve'))
        if curve is None:
            raise RuntimeError(
                "BondTRSAdapter.MarketParRate: 未注入折现曲线，"
                "请在 McpBondTRSAdapter 参数块中添加 DiscountCurve 行（推荐），"
                "或调用 BondTrsSetDiscountCurve，或传入 discountCurve 参数"
            )
        cp = self.__dict__.get('_mcp_bond_trs_current_clean')
        if cp is not None and hasattr(bond_trs, 'setCurrentCleanPrice'):
            bond_trs.setCurrentCleanPrice(float(cp))
        vd = self.__dict__.get('_mcp_bond_trs_valuation_date')
        if vd is not None and hasattr(bond_trs, 'setValuationDate'):
            bond_trs.setValuationDate(vd)
        # McpBondCurve/McpSwapCurve 不继承 MYieldCurve，SWIG void* 重载会导致
        # C++ 中非法 static_cast 崩溃；用 getHandler() 提取底层 mcp::*Curve* 指针
        curve_arg = curve.getHandler() if hasattr(curve, 'getHandler') else curve
        return bond_trs.MarketParRate(curve_arg)

    def __repr__(self):
        try:
            return (f"McpBondTRSAdapter(instrument_id='{self._adapter.getInstrumentId()}', "
                    f"trade_id='{self._adapter.getTradeId()}', "
                    f"notional={self._adapter.getNotional()}, "
                    f"currency='{self._adapter.getCurrency()}')")
        except Exception:
            return "McpBondTRSAdapter(<uninitialized>)"


class McpLoanAndDepos(mcp.mcp.MLoanAndDepos):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    
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


if hasattr(mcp.mcp, "MBasisSwap"):

    class McpBasisSwap(mcp.mcp.MBasisSwap):

        def __init__(self, *args):
            self.raw_args = args
            self.is_mcp_wrapper = True
            mcp_args = to_mcp_args(args)
            super().__init__(*mcp_args)

else:

    class McpBasisSwap:  # type: ignore[no-redef]

        def __init__(self, *args):
            raise RuntimeError(
                "MBasisSwap is not in the deployed mcp binding; rebuild PythonLib/SWIG"
            )


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

def _as_bool(v, default=True):
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    return str(v).strip().lower() in ("true", "1", "yes")


def _zero_rate_convert(df, r_cc, compounding, frequency):
    """由 DiscountFactor 折算指定复利口径的零息利率。

    用于底层 ZeroRate 不支持 compounding/frequency 的曲线类 (MBondCurve/MSwapCurve/
    MBondSpreadCurve)。r_cc 为同一日计数基准下的连续复利零息利率, 由 t=-ln(DF)/r_cc
    反推 year fraction 后按目标口径折算, 保证与底层连续复利结果严格自洽。
    DF≈1 (利率≈0) 时各口径结果均收敛于 r_cc 本身, 直接返回。
    """
    compounding = _as_bool(compounding, True)
    try:
        freq = int(frequency)
    except (TypeError, ValueError):
        freq = 366
    if compounding and freq == 366:
        return r_cc
    if abs(r_cc) < 1e-12:
        return r_cc
    t = -math.log(df) / r_cc
    if not compounding:
        return (1.0 / df - 1.0) / t
    n = freq if freq > 0 else 1
    return n * (df ** (-1.0 / (n * t)) - 1.0)


def _par_rate_convert(c_bey, compounding, frequency):
    """把底层 ParRate 返回的半年付息等价收益率 (BEY) 换算到目标复利口径。

    口径关系: BEY 为半年复利一次的年化利率, 半年增长因子 g=1+c/2。
    年复利(有效年利率)=g^2-1, n 复利=n*(g^(2/n)-1), 连续复利=2*ln(g)。
    单利口径即简单年化, 与 BEY 定义一致, 直接返回。
    """
    compounding = _as_bool(compounding, True)
    try:
        freq = int(frequency)
    except (TypeError, ValueError):
        freq = 2
    if not compounding:
        return c_bey
    if freq == 2 or freq <= 0:
        return c_bey
    g = 1.0 + c_bey / 2.0
    if freq == 366:
        return 2.0 * math.log(g)
    return freq * (g ** (2.0 / freq) - 1.0)


class McpSwapCurve(mcp.mcp.MSwapCurve):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        # print(f"McpSwapCurve args: {args}")
        # print(f"McpSwapCurve mcp_args: {args}")
        super().__init__(*mcp_args)

    def ZeroRate(self, endDate, dayCounter=-1, compounding=True, frequency=366):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        r_cc = super().ZeroRate(endDate, dayCounter)
        compounding = _as_bool(compounding, True)
        try:
            freq = int(frequency)
        except (TypeError, ValueError):
            freq = 366
        if compounding and freq == 366:
            return r_cc
        df = super().DiscountFactor(endDate)
        return _zero_rate_convert(df, r_cc, compounding, freq)


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

    def ZeroRate(self, endDate, dayCounter=-1, compounding=True, frequency=366):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        r_cc = super().ZeroRate(endDate, dayCounter)
        compounding = _as_bool(compounding, True)
        try:
            freq = int(frequency)
        except (TypeError, ValueError):
            freq = 366
        if compounding and freq == 366:
            return r_cc
        df = super().DiscountFactor(endDate)
        return _zero_rate_convert(df, r_cc, compounding, freq)

    def ParRate(self, endDate, compounding=True, frequency=2):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        c = super().ParRate(endDate)
        return _par_rate_convert(c, compounding, frequency)

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


class McpBondSpreadCurve(mcp.mcp.MBondSpreadCurve):
    """Python 封装类，与 McpBondCurve 一致，供 Excel 返回 McpBondSpreadCurve@0。支持 setBenchmarkCurve / getBenchmarkCurve（与 C++ BondSpreadCurve 一致）。"""

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def ZeroRate(self, endDate, dayCounter=-1, compounding=True, frequency=366):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        r_cc = super().ZeroRate(endDate, dayCounter)
        compounding = _as_bool(compounding, True)
        try:
            freq = int(frequency)
        except (TypeError, ValueError):
            freq = 366
        if compounding and freq == 366:
            return r_cc
        df = super().DiscountFactor(endDate)
        return _zero_rate_convert(df, r_cc, compounding, freq)

    def ParRate(self, endDate, compounding=True, frequency=2):
        if isinstance(endDate, datetime):
            endDate = mcp_dt.to_date1(endDate)
        c = super().ParRate(endDate)
        return _par_rate_convert(c, compounding, frequency)


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


if hasattr(mcp.mcp, "MFRACurveData"):
    class McpFRACurveData(mcp.mcp.MFRACurveData):

        def __init__(self, *args):
            self.raw_args = args
            self.is_mcp_wrapper = True
            mcp_args = to_mcp_args(args)
            super().__init__(*mcp_args)
else:
    class McpFRACurveData:

        def __init__(self, *args):
            raise RuntimeError("MFRACurveData is not available in _mcp. Rebuild the MCP Python extension after updating mcplib.h.")


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


def get_all_predefined_rate_conventions():
    """
    Return list of all predefined RateConvention names.
    Calls static method MRateConvention.predefinedNames() directly.
    C++ returns char* (JSON array or comma-separated).
    """
    s = mcp.mcp.MRateConvention.predefinedNames()
    if not s:
        return []
    if isinstance(s, (list, tuple)):
        return list(s)
    s = str(s).strip()
    if s.startswith('['):
        return json.loads(s)
    return [n.strip() for n in s.split(',') if n.strip()]


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
        if args and args[0].__class__.__name__ in ("McpFXVolSurface", "MFXVolSurface"):
            # The FXVolSurface overload is typed as MFXVolSurface* in SWIG.
            # Passing getHandler() would turn it into FXVolSurface* and fail overload resolution.
            mcp_args = [args[0], *args[1:]]
        else:
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
        return val

    def create_bumped(self, shift: float, mode: int = 0) -> "McpLocalVol":
        """
        返回扰动后的新 McpLocalVol 实例（不修改自身）。
        mode: 0=Proportional（比例缩放，默认）
              1=Additive（绝对平移）
              2=Recalibrate（重新校准，精度最高）
        """
        bumped_ptr = self.CreateBumped(shift, mode)
        # CreateBumped 返回 new MLocalVol*，SWIG 会包装为 MLocalVol 对象
        # 将其转换为 McpLocalVol（通过 getHandler 重建）
        result = McpLocalVol.__new__(McpLocalVol)
        result.is_mcp_wrapper = True
        # 直接使用返回的 MLocalVol 对象（SWIG 已创建实例）
        mcp.mcp.MLocalVol.__init__(result, bumped_ptr.getHandler())
        return result



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

    # PV：今日折现现值（NPV）。
    # 优先调用 SWIG 暴露的 EMFXForward.PV（C++ 已实现：转发到
    # Experimental::FXInstrument::PV，等价 DiscMarketValue）；
    # 若当前 mcp.so/mcp.pyd 是旧版尚未包含 PV 接口，则回退到
    # DiscMarketValue 以保证 Excel McpPV(...) 立即可用。
    def PV(self, isAmount=True):
        try:
            return super().PV(isAmount)
        except AttributeError:
            return super().DiscMarketValue(isAmount)


class McpEFXSwap(mcp.mcp.MFXSwap):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    # PV(isAmount): 折现现值 / NPV（持有方视角 MTM）
    # 直接转发到 mcp::FXSwap::PV（C++ 基础类新增），内部走
    #   m_nearLeg.PV + m_farLeg.PV
    # 使用通过 SetValuationCurve / SetDiscountCurve 注入到 nearLeg/farLeg 的曲线。
    # 与估值引擎 fx_linear_adapter.cpp 端 swap_->PV(true) 走同一份 C++ 实现，
    # 也与 EMFXForward.PV / FX 期权 PV 同口径。
    # 替代了之前 MFXSwap::DiscMarketValue 的 stub（返回 0）+ try-except 兜底。
    # 仍保留 try-except，以防加载到旧版未含 PV 的 mcp.so/mcp.pyd。
    def PV(self, isAmount=True):
        try:
            return super().PV(isAmount)
        except AttributeError:
            return super().DiscMarketValue(isAmount)

class McpDoubleDigitalOption(mcp.mcp.MDoubleDigitalOption):
    """双障碍数字期权 Python wrapper。

    主要目的：补齐 PV(isAmount) 接口，使 Excel/Python 调用 McpPV(...) 时，
    与估值引擎 fx_options_adapter.cpp::computeMetrics 中 PV = DiscMarketValue(true)
    保持一致语义（多头有价值为正）。
    """

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def PV(self, isAmount=True):
        try:
            return super().PV(isAmount)
        except (AttributeError, TypeError, NotImplementedError):
            return super().DiscMarketValue(isAmount)


class McpVanillaStrategy(mcp.mcp.MVanillaStrategy):

    def __init__(self, *args):
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpStructuredDerivativeProduct(mcp.mcp.MStructuredDerivativeProduct):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpFXForwardOutright(mcp.mcp.MFXForwardOutright):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    # PV(isAmount): 折现现值 / NPV（持有方视角 MTM）
    # 直接转发到 mcp::FXForwardOutright::PV（C++ 基础类新增），内部走
    #   NPV(空指针, 空指针)
    # 然后 fallback 到通过 SetValuationCurve / SetDiscountCurve1 注入的成员曲线。
    # 与估值引擎 fx_linear_adapter.cpp 端 forward_->PV(true) 走同一份 C++ 实现，
    # 也与 EMFXForward.PV / FX 期权 PV 同口径，让 Excel/引擎 PV 完全同源。
    # 调用者需先通过 SetValuationCurve(fxFwdPtsCurve) 与
    # SetDiscountCurve1(ccy2DiscCurve) 注入曲线；曲线缺失时退化为 PV=0 / DF=1。
    def PV(self, isAmount=True):
        try:
            return super().PV(isAmount)
        except AttributeError:
            return super().NPV(None, None)


class McpBond(mcp.mcp.MBond):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)


class McpCallableBond(mcp.mcp.MCallableBond):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def curve_handler(self, curve):
        # BondSpreadCurve 不是 MCallableBond::Price 直接支持的估值曲线类型，
        # 若传入 spread curve，则回退到其 benchmark curve 作为 Price 入参。
        if isinstance(curve, mcp.mcp.MParametricCurve):
            return curve.getHandler(), True

        curve_type_name = type(curve).__name__ if curve is not None else ""
        if "BondSpreadCurve" in curve_type_name and hasattr(curve, "getBenchmarkCurve"):
            bench = curve.getBenchmarkCurve()
            if hasattr(bench, "getHandler"):
                return bench.getHandler(), False

        if hasattr(curve, "getHandler"):
            return curve.getHandler(), False
        raise Exception("unsupported curve:" + str(curve))

    def Price(self, curve):
        return super().Price(*self.curve_handler(curve))

    def FairValue(self, curve):
        return super().FairValue(*self.curve_handler(curve))