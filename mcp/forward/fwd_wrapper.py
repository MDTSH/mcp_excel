import json
import math
from statistics import mean

from mcp.mcp import MAdjustmentTable
from mcp.tool.fields_def import InitFields
from mcp.utils.enums import *
from mcp.utils.mcp_utils import *
from mcp.utils.excel_utils import FieldName
from mcp.wrapper import McpDayCounter, MktDataSide, get_volatility, ForwardUtils, McpMktData, to_mcp_args
import mcp.wrapper

pricing_method_class_name = PricingMethod().__class__.__name__
option_expiry_nature_class_name = OptionExpiryNature().__class__.__name__
fwd_pricing_method_class_name = FxFwdPricingMethod().__class__.__name__
barrier_type_class_name = BarrierType().__class__.__name__
digital_type_class_name = DigitalType().__class__.__name__

Payoff_Spot_Count = 30


# pricing_method_class_name = PricingMethod().__class__.__name__
# option_expiry_nature_class_name = OptionExpiryNature().__class__.__name__


def payoff_generate_spots(spot_px, rg, spot_count):
    spot_max = spot_px * (1 + rg)
    spot_min = spot_px * (1 - rg)
    d_step = (spot_max - spot_min) / spot_count
    spots = [spot_min + i * d_step for i in range(spot_count)]
    spots.append(spot_max)
    return spots, d_step


def payoff_spots(spot_px, rg, spot_count, pxs):
    spots, d_step = payoff_generate_spots(spot_px, rg, spot_count)
    for px in pxs:
        if spots.count(px) == 0:
            spots.append(px)
    spots.sort()
    return spots


class FwdDefConst:
    Field_Key = "Key".lower()
    Field_PackageName = "PackageName".lower()
    Field_BuySell = "BuySell".lower()
    Field_Strikes = "Strikes".lower()
    Field_StrikesStructure = "StrikesStructure".lower()
    Field_ProductStructure = "ProductStructure".lower()
    Field_Arguments = "Arguments".lower()

    Field_Legs_Args = "LegArgs".lower()
    Field_AccRate = "AccRate".lower()
    Field_UndRate = "UndRate".lower()
    Field_Volatility = "Volatility".lower()
    Field_PricingMethod = "PricingMethod".lower()
    Field_Forward = "ForwardPx".lower()

    Dict_LegType = {
        "Vanilla".lower(): 1,
        "Barrier_Down_In".lower(): 2,
        "Barrier_Down_Out".lower(): 3,
        "Barrier_Up_In".lower(): 4,
        "Barrier_Up_Out".lower(): 5,
        "European".lower(): 1,
        "American".lower(): 6,
        "Outright".lower(): 7,

        # "Asian_Fixed_Geometric".lower(): 8,
        # "Asian_Fixed_Arithmetic".lower(): 9,
        # "Asian_Floating_Geometric".lower(): 10,
        # "Asian_Floating_Arithmetic".lower(): 11,

        "Asian".lower(): 12,
        "EuropeanDigital".lower(): 13,
    }

    Barrier_Offset = 0.00000001


class PayoffWrapper:

    def __init__(self, spec, payoff_by_spots_impl=None, print_info=False, custom_del_ref=False):
        self.print_info = print_info
        self.spec = spec
        self.spec.payoff = self.payoff
        if not custom_del_ref:
            self.spec.del_ref = self.del_ref
        if payoff_by_spots_impl is not None:
            self.payoff_by_spots_impl = payoff_by_spots_impl
        else:
            self.payoff_by_spots_impl = None
            self.spec.payoff_by_spots = self.payoff_by_spots

    def del_ref(self):
        del self.spec.payoff_wrapper
        # self.spec.Dispose()
        del self.spec

    def payoff_strikes(self):
        return []

    def price(self, pricingMethod=None):
        pass

    def payoff_copy(self, value_date, spot):
        pass

    def payoff(self, value_date, spot=None, rg=0.03):
        pxs = self.spec.payoff_strikes()
        if spot is None:
            spot = mean(pxs)
        spots = payoff_spots(spot, rg, Payoff_Spot_Count, pxs)
        payoffs = self.payoff_by_spots(value_date, spots)
        return spots, payoffs

    def payoff_by_spots(self, value_date, spots):
        if self.payoff_by_spots_impl is not None:
            return self.payoff_by_spots_impl(value_date, spots)
        pnls = []
        base_price = self.spec.price()
        for spot in spots:
            if is_float(spot):
                fxv = self.spec.payoff_copy(value_date, spot)
                underlying_price = fxv.price()
                pnl = base_price - underlying_price
                pnls.append(pnl)
                fxv.del_ref()
                if self.print_info:
                    print("payoff_by_spots:", base_price, underlying_price)
            else:
                pnls.append("")
        return pnls


class PctCcyWrapper:

    @staticmethod
    def generic_value(obj, name, key):
        # 'Pct': fc(False, False),
        # 'Ccy1': fc(False, True),
        # 'Ccy2': fc(True, True),
        result = 0
        if hasattr(obj, name):
            fc = getattr(obj, name)
            if key == 'Pct':
                result = fc(False, False)
            elif key == 'Ccy1':
                result = fc(False, True)
            elif key == 'Ccy2':
                result = fc(True, True)
            elif key == 'Pips':
                if name == 'Premium':
                    result = fc(True, False)
        return result


class PayoffSpec():

    def __init__(self):
        self.print_info = False

    def del_ref(self):
        pass

    def payoff_strikes(self):
        return []

    def price(self, pricingMethod=None):
        return 0

    def payoff_copy(self, value_date, spot):
        return self

    def payoff2(self, value_date, spot=None, rg=0.03):
        return self.payoff_of_mcp(value_date, [])

    def payoff_of_mcp(self, value_date, spots):
        try:
            if spots is None:
                spots = []
            s = self.Payoff(value_date, json.dumps(spots))
            arr = json.loads(s)
            # spot=arr[0], pnl=arr[1]
            return arr[0], arr[1]
        except:
            return [], []

    def payoff(self, value_date, spot=None, rg=0.03):
        pxs = self.payoff_strikes()
        if spot is None:
            spot = mean(pxs)
        spots = payoff_spots(spot, rg, Payoff_Spot_Count, pxs)
        payoffs = self.payoff_by_spots(value_date, spots)
        return spots, payoffs

    def payoff_by_spots(self, value_date, spots, buy_sell=None, strike=None, amount=None, is_forward=False):
        pnls = []
        if is_forward:
            for spot in spots:
                pnl = buy_sell*amount*(spot - strike)
                pnls.append(pnl)
            return pnls
        else:
            base_price = self.price()
            for spot in spots:
                if is_float(spot):
                    fxv = self.payoff_copy(value_date, spot)
                    underlying_price = fxv.price()
                    pnl = base_price - underlying_price
                    pnls.append(pnl)
                    # fxv.del_ref()
                    if self.print_info:
                        print("payoff_by_spots:", base_price, underlying_price)
                else:
                    pnls.append("")
            return pnls

    def legs(self):
        return [self.get_field_dict()]

    def gen_field_dict(self, args, fields_list):
        d = {}
        for fields in fields_list:
            if len(fields) == len(args):
                for item, val in zip(fields, args):
                    f, t = item[0], item[1]
                    if t == 'const':
                        name = enum_wrapper.key_of_value(val, f)
                        if name is not None and name != '':
                            d[f] = name
                        else:
                            d[f] = val
                    else:
                        d[f] = val
                break
        print(f"gen_field_dict: {d}")
        return d


class McpVanillaOption(mcp.wrapper.McpVanillaOption, PayoffSpec):
    ins_count = 0
    del_count = 0

    def __init__(self, *args):
        # print(f"McpVanillaOption args: {args}")
        super(PayoffSpec, self).__init__()
        self.print_info = False
        McpVanillaOption.ins_count += 1
        self._del_id = McpVanillaOption.ins_count
        self.pips_unit = 10000

        vo_type = args[-1]

        self.field_dict = None

        self.timeToExpiry = None
        self.timeToDelivery = None
        self.forward = None
        self.calc_target = CalculateTarget.CCY1
        self.ttet = 0.0
        if vo_type == 1 :
            vo_type = 1
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.spotPx = args[2]
            self.expiryDate = args[3]
            self.deliveryDate = args[4]
            self.strikePx = args[5]
            self.domesticRate = args[6]
            self.foreignRate = args[7]
            self.forward = args[8]
            self.volatility = args[9]
            self.premiumDate = args[10]
            self.calendar = args[11]
            self.dayCounter = args[12]
            self.optionExpiryNature = args[13]
            self.pricingMethod = args[14]
            self.buySell = args[15]
            self.faceAmount = args[16]
            self.numSimulate = args[17]
            self.timeToExpiryTime = 0
            self.calculationTarget = 2
            self.leverage = self.faceAmount
            self.ttet = args[18]               #args[-4]
            self.calc_target = args[19]       # args[-3]
            self.pips_unit = args[-2]
            if len(args) > 20:
                self.pair = args[20]
            else:
                self.pair = "USD/CNY"
        elif vo_type == 2:
            # print(f"McpVanillaOption args: {args}")
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.spotPx = args[2]
            self.expiryDate = args[3]
            self.deliveryDate = args[4]
            self.strikePx = args[5]
            self.forward = args[6]
            self.premiumDate = args[7]
            self.calendar = args[8]
            self.dayCounter = args[9]
            self.optionExpiryNature = args[10]
            self.pricingMethod = args[11]
            self.buySell = args[12]
            self.faceAmount = args[13]
            self.numSimulate = args[14]

            self.ttet = args[-4]
            self.calc_target = args[-3]
            self.pips_unit = args[-2]

            self.leverage = self.faceAmount

            mkt_data: McpMktData = args[15]
            # self.is_client = args[18]
            self.is_client = True if args[18].lower() == "client" else False
            side_spot, side_acc, side_und, side_vol = ForwardUtils.bid_ask_sign(self.buySell, self.callPut,
                                                                                self.is_client)
            self.domesticRate = mkt_data.get_acc_rate(self.expiryDate, side_acc)
            self.foreignRate = mkt_data.get_und_rate(self.expiryDate, side_und)
            # if self.forward is None or self.forward == -1.0:
            #     self.forward = mkt_data.get_forward_rate(self.expiryDate, side_spot)
            #     midForward = 0.5 * (mkt_data.get_forward_rate(self.expiryDate, MktDataSide.Bid) + mkt_data.get_forward_rate(self.expiryDate, MktDataSide.Ask))
            # else:
            #     midForward = self.forward
            ## 获取波动率，需要传入中间价，所以这里忽略vanillaoption自带的forward，直接计算中间价远期价格（MidForward）
            self.forward = mkt_data.get_forward_rate(self.expiryDate, side_spot)
            midForward = 0.5 * (mkt_data.get_forward_rate(self.expiryDate, MktDataSide.Bid) + mkt_data.get_forward_rate(
                self.expiryDate, MktDataSide.Ask))

            self.volatility = mkt_data.get_strike_vol(self.strikePx, self.expiryDate, side_vol, midForward)

            try:
                vol = float(args[17])
            except:
                vol = None
            if vol is not None:
                self.volatility = vol
            # print(f"vanilla: forward={self.forward}/{args[6]}, undRate={self.undRate}, vol={self.volatility}")
        elif vo_type == 5:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.spotPx = args[2]
            self.expiryDate = args[3]
            self.deliveryDate = args[4]
            self.strikePx = args[5]
            self.domesticRate = args[6]
            self.foreignRate = args[7]
            self.volatility = args[8]
            self.premiumDate = args[9]
            self.calendar = args[10]
            self.dayCounter = args[11]
            self.optionExpiryNature = args[12]
            self.pricingMethod = args[13]
            self.buySell = args[14]
            self.faceAmount = args[15]
            self.numSimulate = args[16]

            self.timeToExpiryTime = args[17]
            self.leverage = self.faceAmount
            self.ttet = args[17]
        elif vo_type == 6:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.strikePx = args[4]
            self.domesticRate = args[5]
            self.foreignRate = args[6]
            self.volatility = args[7]
            self.premiumDate = args[8]
            self.forward = args[9]
            self.calendar = args[10]
            self.dayCounter = args[11]
            self.optionExpiryNature = args[12]
            self.pricingMethod = args[13]
            self.buySell = args[14]
            self.faceAmount = args[15]
            self.numSimulate = args[16]
            self.leverage = self.faceAmount
            self.ttet = args[17]
            self.spotPx = 0.0
        elif vo_type == 7:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.strikePx = args[4]
            self.volSurface2 = args[5]
            self.premiumDate = args[6]
            self.optionExpiryNature = args[7]
            self.pricingMethod = args[8]
            self.side = args[9]
            self.buySell = args[10]
            self.faceAmount = args[11]
            self.numSimulate = args[12]
            self.ttet = args[13]
        elif vo_type == 8: # fxvolsurface / strike
            vo_type = 8
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.strikePx = args[4]
            self.fxVolSurface = args[5]
            self.premiumDate = args[6]
            self.buySell = args[7]
            self.spotPx = args[8]
            self.forward = args[9]
            self.volatility = args[10]
            self.domesticRate = args[11]
            self.foreignRate = args[12]
            self.timeToExpiryTime = args[13]
            self.calendar = args[14]
            self.dayCounter = args[15]
            self.optionExpiryNature = args[16]
            self.pricingMethod = args[17]
            self.faceAmount = args[18]
            self.numSimulate = args[19]
            self.leverage = self.faceAmount
            # self.ttet = args[18]               #args[-4]
            # self.calc_target = args[18]       # args[-3]
            # self.volatility = args[20]
            self.pips_unit = args[-2]
        elif vo_type == 9:  # fxvolsurface / deltastr
            vo_type = 9
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.deltaStr = args[4]
            self.fxVolSurface = args[5]
            self.premiumDate = args[6]
            self.buySell = args[7]
            self.spotPx = args[8]
            self.forward = args[9]
            self.volatility = args[10]
            self.domesticRate = args[11]
            self.foreignRate = args[12]
            self.timeToExpiryTime = args[13]
            self.calendar = args[14]
            self.dayCounter = args[15]
            self.optionExpiryNature = args[16]
            self.pricingMethod = args[17]
            self.faceAmount = args[18]
            self.numSimulate = args[19]
            self.leverage = self.faceAmount
            # self.ttet = args[18]               #args[-4]
            # self.calc_target = args[18]       # args[-3]
            # self.volatility = args[20]
            self.pips_unit = args[-2]
        elif vo_type == 10:  # Assuming you're numbering sequentially
            vo_type = 10
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.strikePx = args[4]
            self.fxVolSurface2 = args[5]
            self.side = args[6] if len(args) > 6 else -1
            self.buySell = args[7] if len(args) > 7 else 1
            self.premiumDate = args[8] if len(args) > 8 else ""
            self.timeToExpiryTime = args[9] if len(args) > 9 else 0.0
            self.spotPx = args[10] if len(args) > 10 else float('nan')
            self.forward = args[11] if len(args) > 11 else float('nan')
            self.volatility = args[12] if len(args) > 12 else float('nan')
            self.domesticRate = args[13] if len(args) > 13 else float('nan')
            self.foreignRate = args[14] if len(args) > 14 else float('nan')
            self.optionExpiryNature = args[15] if len(args) > 15 else 0
            self.pricingMethod = args[16] if len(args) > 16 else 1
            self.faceAmount = args[17] if len(args) > 17 else 1.0
            self.numSimulate = args[18] if len(args) > 18 else 500000
            self.leverage = self.faceAmount
            self.pips_unit = args[-2] if len(args) > 17 else None
        elif vo_type == 11:  # Next sequential number
            vo_type = 11
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.expiryDate = args[2]
            self.deliveryDate = args[3]
            self.deltaStr = args[4]  # Note the different parameter here
            self.fxVolSurface2 = args[5]
            self.side = args[6] if len(args) > 6 else -1
            self.buySell = args[7] if len(args) > 7 else 1
            self.premiumDate = args[8] if len(args) > 8 else ""
            self.timeToExpiryTime = args[9] if len(args) > 9 else 0.0
            self.spotPx = args[10] if len(args) > 10 else float('nan')
            self.forward = args[11] if len(args) > 11 else float('nan')
            self.volatility = args[12] if len(args) > 12 else float('nan')
            self.domesticRate = args[13] if len(args) > 13 else float('nan')
            self.foreignRate = args[14] if len(args) > 14 else float('nan')
            self.optionExpiryNature = args[15] if len(args) > 15 else 0
            self.pricingMethod = args[16] if len(args) > 16 else 1
            self.faceAmount = args[17] if len(args) > 17 else 1.0
            self.numSimulate = args[18] if len(args) > 18 else 500000
            self.leverage = self.faceAmount
            self.pips_unit = args[-2] if len(args) > 17 else None
        elif vo_type == 12:
            vo_type = 12
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.spotPx = args[2]
            self.expiryDate = args[3]
            self.deliveryDate = args[4]
            self.deltaStr = args[5]
            self.domesticRate = args[6]
            self.foreignRate = args[7]
            self.forward = args[8]
            self.volatility = args[9]
            self.premiumDate = args[10]
            self.calendar = args[11]
            self.dayCounter = args[12]
            self.optionExpiryNature = args[13]
            self.pricingMethod = args[14]
            self.buySell = args[15]
            self.faceAmount = args[16]
            self.numSimulate = args[17]
            self.timeToExpiryTime =  args[18]
            self.calculationTarget =  args[19]
            self.leverage = self.faceAmount
            self.ttet = args[18]               #args[-4]
            self.calc_target = args[19]       # args[-3]
            self.pips_unit = args[-2]
            if len(args) > 20:
                self.pair = args[20]
            else:
                self.pair = "USD/CNY"
        else:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.strikePx = args[2]
            self.spotPx = args[3]
            self.faceAmount = args[4]
            self.expiryDate = args[5]
            self.deliveryDate = args[6]
            self.priceSettlementDate = args[7]
            self.premiumDate = self.priceSettlementDate
            self.buySell = args[8]
            self.optionExpiryNature = args[9]
            self.pricingMethod = args[10]
            self.dayCounter = args[11]
            self.calendar = args[12]
            self.volSurface = args[13]
            self.leverage = self.faceAmount

            if len(args) >= 15:
                self.numSimulate = args[14]
            else:
                self.numSimulate = 1000

            if len(args) >= 17:
                self.domesticRate = args[15].ZeroRate(self.expiryDate)
                self.foreignRate = args[16].ZeroRate(self.expiryDate)
            else:
                self.domesticRate = self.volSurface.get_acc_rate(self.expiryDate)
                self.foreignRate = self.volSurface.get_und_rate(self.expiryDate)
            self.volatility = get_volatility(self.volSurface, self.strikePx, self.expiryDate)
            self.ttet = args[17]
        #if vo_type != 7 and vo_type != 6:
        if vo_type not in (6, 7, 8, 9, 10, 11, 12):
            day_counter = McpDayCounter(self.dayCounter)
            # print(f"referenceDate={self.referenceDate}, expiryDate={self.expiryDate}")
            self.timeToExpiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
            self.timeToDelivery = day_counter.YearFraction(self.premiumDate, self.deliveryDate)
            if self.forward is None:
                forward = math.exp((self.domesticRate - self.foreignRate) * self.timeToExpiry) * self.spotPx
                self.forward = forward
# 不知道加这个有什么作用，但是如果加了，会导致Forward=-1，计算有问题
#            if mcp_dt.same_date(self.referenceDate, self.expiryDate):
#                self.forward = -1
        if vo_type == 5:
            mcp_args = [self.callPut, self.referenceDate, self.spotPx, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.domesticRate, self.foreignRate,
                        self.volatility, self.premiumDate,
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate, self.ttet, self.calendar.getHandler()]
        elif vo_type == 6:
            mcp_args = [self.callPut, self.referenceDate, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.domesticRate, self.foreignRate,
                        self.volatility, self.premiumDate, self.forward, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate, self.ttet]
        elif vo_type == 7:
            mcp_args = [self.callPut, self.referenceDate, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.volSurface2, 
                        self.premiumDate, self.optionExpiryNature,
                        self.pricingMethod, self.side, self.buySell, self.faceAmount, self.numSimulate, self.ttet]
        elif vo_type == 1:
            mcp_args = [self.callPut, self.referenceDate, self.spotPx, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.domesticRate, self.foreignRate, self.forward,
                        self.volatility, self.premiumDate, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate,
                        self.ttet, self.calc_target, self.pair]
        elif vo_type == 12:
            mcp_args = [self.callPut, self.referenceDate, self.spotPx, self.expiryDate,
                        self.deliveryDate, self.deltaStr, self.domesticRate, self.foreignRate, self.forward,
                        self.volatility, self.premiumDate, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate,
                        self.ttet, self.calc_target, self.pair]
        elif vo_type == 8:
            mcp_args = [self.callPut, self.referenceDate, self.expiryDate, self.deliveryDate, 
                        self.strikePx, self.fxVolSurface, self.premiumDate, self.buySell, 
                        self.spotPx, self.forward, self.volatility, self.domesticRate, self.foreignRate,
                        self.timeToExpiryTime, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod,  self.faceAmount, self.numSimulate]
        elif vo_type == 9:
            mcp_args = [self.callPut, self.referenceDate, self.expiryDate, self.deliveryDate, 
                        self.deltaStr, self.fxVolSurface, self.premiumDate, self.buySell, 
                        self.spotPx, self.forward, self.volatility, self.domesticRate, self.foreignRate,
                        self.timeToExpiryTime, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod,  self.faceAmount, self.numSimulate]
        elif vo_type == 10:  # Assuming sequential numbering
            mcp_args = [
                self.callPut,
                self.referenceDate,
                self.expiryDate,
                self.deliveryDate,
                self.strikePx,
                self.fxVolSurface2,
                self.side,
                self.buySell,
                self.premiumDate,
                self.timeToExpiryTime,
                self.spotPx,
                self.forward,
                self.volatility,
                self.domesticRate,
                self.foreignRate,
                self.optionExpiryNature,
                self.pricingMethod,
                self.faceAmount,
                self.numSimulate
            ]
        elif vo_type == 11:  # Next sequential number
            mcp_args = [
                self.callPut,
                self.referenceDate,
                self.expiryDate,
                self.deliveryDate,
                self.deltaStr,  # Note the different parameter here
                self.fxVolSurface2,
                self.side,
                self.buySell,
                self.premiumDate,
                self.timeToExpiryTime,
                self.spotPx,
                self.forward,
                self.volatility,
                self.domesticRate,
                self.foreignRate,
                self.optionExpiryNature,
                self.pricingMethod,
                self.faceAmount,
                self.numSimulate
            ]
        else:
            mcp_args = [self.callPut, self.referenceDate, self.spotPx, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.domesticRate, self.foreignRate, self.forward,
                        self.volatility, self.premiumDate, self.calendar.getHandler(),
                        self.dayCounter, self.optionExpiryNature,
                        self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate,
                        self.ttet, self.calc_target]
        # print(f"McpVanillaOption mcp_args: {mcp_args}")
        if vo_type == 7:
            super().__init__(*mcp_args)
            self.args = [self.callPut, self.referenceDate, self.expiryDate,
                        self.deliveryDate, self.strikePx, self.volSurface2, 
                        self.premiumDate, self.optionExpiryNature,
                        self.pricingMethod, self.side, self.buySell, self.faceAmount, self.numSimulate, self.ttet]
        elif vo_type in (8, 9, 10, 11, 12):
            super().__init__(*mcp_args)
            # self.args = [self.callPut, self.referenceDate, self.expiryDate,
            #             self.deliveryDate, self.strikePx, self.fxVolSurface, 
            #             self.premiumDate, self.optionExpiryNature,
            #             self.pricingMethod, self.side, self.buySell, self.faceAmount, self.numSimulate, self.ttet]
        else:
            super().__init__(*mcp_args)
            # self.forward = self.GetForward()
            self.args = [self.callPut, self.referenceDate, self.spotPx, self.expiryDate,
                         self.deliveryDate, self.strikePx, self.domesticRate, self.foreignRate, self.forward,
                         self.volatility, self.premiumDate, self.calendar,
                         self.dayCounter, self.optionExpiryNature,
                         self.pricingMethod, self.buySell, self.faceAmount, self.numSimulate,
                         self.ttet, self.calc_target, 1]
            self.forward = self.GetForward()
            self.spot_px = self.spotPx
        # print(f"McpVanillaOption self.args: {self.price()}, {self.args}")

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = {
                FieldName.PremiumDate: self.premiumDate,

                FieldName.BuySell: buy_sell_view(self.buySell),
                FieldName.CallPut: call_put_view(self.callPut),
                FieldName.StrikePx: self.strikePx,
                FieldName.Volatility: self.volatility,
                FieldName.TimeToExpiry: self.timeToExpiry,
                FieldName.timeToDelivery: self.timeToDelivery,
                FieldName.DomesticRate: self.domesticRate,
                FieldName.ForeignRate: self.foreignRate,
                FieldName.SpotPx: self.spotPx,
                FieldName.ReferenceDate: self.referenceDate,
                FieldName.ExpiryDate: self.expiryDate,
                FieldName.DeliveryDate: self.deliveryDate,
                FieldName.Forward: self.forward,
                FieldName.FaceValue: self.faceAmount,
                FieldName.Premium: self.price(),
                FieldName.DeltaL: self.delta(False),
                FieldName.DeltaR: self.delta(True),
                FieldName.Gamma: self.gamma(),
                FieldName.Vega: self.vega(),
                FieldName.Theta: self.theta(),
                FieldName.RhoL: self.rho(False),
                FieldName.RhoR: self.rho(True),
                FieldName.OptionExpiryNature: enum_wrapper.key_of_value(self.optionExpiryNature,
                                                                        option_expiry_nature_class_name),
                FieldName.PricingMethod: enum_wrapper.key_of_value(self.pricingMethod,
                                                                   pricing_method_class_name),
                'Vanna': self.Vanna(),
                'Volga': self.Volga(),
            }
        return self.field_dict

    def greek(self):
        return {
            "Gamma": self.Gamma(),
            "Delta": self.Delta(True),
            "Vega": self.Vega(),
        }

    def Premium(self, is_ccy2, is_amount):
        if is_amount:
            amt = self.Price(True)
            if not is_ccy2:
                if self.spot_px > 0:
                    amt = amt / self.spot_px
            return amt
        else:
            p = self.Price(False)
            if is_ccy2:
                p = p * self.pips_unit
            else:
                if self.spot_px > 0:
                    p = p / self.spot_px
            return p

    def price(self, price_method=None):
        if price_method is None or price_method == 0:
            return super().Price()
        else:
            return super().Price(price_method)

    def delta(self, delta_rhs, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Delta(delta_rhs, price_method)

    def rho(self, is_demestic_ccy, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Rho(is_demestic_ccy, price_method)

    def gamma(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Gamma(price_method)

    def theta(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Theta(price_method)

    def vega(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Vega(price_method)

    def vanna(self):
        return super().Vanna()

    def volga(self):
        return super().Volga()

    def forward_delta(self, delta_rhs):
        return super().ForwardDelta(delta_rhs)

    def payoff_strikes(self):
        return [self.strikePx]

    def payoff_by_spots(self, value_date, spots):
        s, pnls = self.payoff_of_mcp(value_date, spots)
        # print(f"vo payoff_of_mcp: {pnls}, {s}, {spots}")
        return pnls

    def payoff_copy(self, value_date, spot):
        return self.copy(spot, value_date)

    # def del_ref(self):
    #     del self.payoff_wrapper.spec
    #     del self.payoff_wrapper

    def prices(self, value_dates, spots, pricingMethod=None):
        if pricingMethod is None:
            pricingMethod = self.pricingMethod
        prices = []
        for value_date in value_dates:
            sub_prices = []
            for spot in spots:
                fxv = self.copy(spot, value_date)
                price = fxv.price(pricingMethod)
                fxv.del_ref()
                sub_prices.append(price)
            prices.append(sub_prices)
        # gc.collect(0)
        return prices

    def getPricingMethod(self):
        return self.pricingMethod

    # def payoff_by_spots(self, value_date, spots):
    #     try:
    #         s = self.Payoff(value_date, json.dumps(spots))
    #         arr = json.loads(s)
    #         return arr[1]
    #     except:
    #         logging.info(f"vanilla Payoff except: {value_date}, {spots}", exc_info=True)
    #         return []

    def copy(self, spotPx, reference_date):
        args = []
        args.extend(self.args)
        args[1] = reference_date
        args[2] = spotPx
        # args[8] = -1
        # args[10] = self.calendar.AddBusinessDays(reference_date, 2)
        # print(f"McpVanillaOption copy: {args}")
        return McpVanillaOption(*args)


class McpAsianOption(mcp.mcp.MAsianOption, PayoffSpec):

    def __init__(self, *args):
        self.field_dict = None
        # args = list(args)
        self.args = args
        self.pips_unit = args[-2]
        args_count = len(args)
        self.strikePx = args[7]
        self.spot_px = args[2]
        if args_count == 22:
            # if isinstance(args[13], mcp.mcp.MCalendar):
            #     args[13] = args[13].getHandler()
            self.pricingMethod = args[17]
        elif args_count == 26:
            # if isinstance(args[17], mcp.mcp.MCalendar):
            #     args[17] = args[17].getHandler()
            self.pricingMethod = args[21]
            args = list(args)
            args.append('')
        elif args_count == 27:
            self.pricingMethod = args[21]
        args = mcp.wrapper.to_mcp_args(args[:-1])

        print("McpAsianOption args:", args)
        self.field_dict = self.gen_field_dict(self.args, InitFields.AsianOption())
        self.raw_args = self.args
        self.is_mcp_wrapper = True
        print(f"McpAsianOption mcp args json: {mcp.wrapper.trace_args(self)}")
        super().__init__(*args)

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = self.gen_field_dict(self.args, InitFields.AsianOption())
        return self.field_dict

    def price(self, price_method=None):
        if price_method is None:
            price_method = self.pricingMethod
        price = super().Price(price_method)
        return price

    # def del_ref(self):
    #     del self.payoff_wrapper.spec
    #     del self.payoff_wrapper

    def payoff_strikes(self):
        return [self.strikePx]

    def payoff_copy(self, value_date, spot):
        return self.copy(spot, value_date)

    def payoff_by_spots(self, value_date, spots):
        # print("spots: ", spots)
        payoffs = json.loads(self.Payoff(value_date, json.dumps(spots)))
        # print("payoffs: ", payoffs)
        return payoffs[1]

    def pay_off(self, value_date, spots, pricingMethod=None):
        if pricingMethod is None:
            pricingMethod = self.pricingMethod
        pnls = []
        option_price = self.price(pricingMethod)
        for spot in spots:
            fxv = self.copy(spot, value_date)
            underlying_price = fxv.price(pricingMethod)
            pnl = option_price - underlying_price
            pnls.append(pnl)
        return pnls

    def greek(self):
        return {
            "Gamma": self.Gamma(),
            "Delta": self.Delta(True),
            "Vega": self.Vega(),
        }

    def Premium(self, is_ccy2, is_amount):
        if is_amount:
            amt = self.Price(True)
            if not is_ccy2:
                amt = amt / self.spot_px
            return amt
        else:
            p = self.Price(False)
            if is_ccy2:
                p = p * self.pips_unit
            else:
                p = p / self.spot_px
            return p

    def delta(self, delta_rhs, price_method=None):
        if price_method is None:
            price_method = PricingMethod.BLACKSCHOLES
        return super().Delta(delta_rhs, True, price_method)

    def rho(self, is_demestic_ccy, price_method=None):
        if price_method is None:
            price_method = PricingMethod.BLACKSCHOLES
        return super().Rho(is_demestic_ccy, price_method)

    def gamma(self, price_method=None):
        if price_method is None:
            price_method = PricingMethod.BLACKSCHOLES
        return super().Gamma(price_method)

    def theta(self, price_method=None):
        if price_method is None:
            price_method = PricingMethod.BLACKSCHOLES
        return super().Theta(price_method)

    def vega(self, price_method=None):
        if price_method is None:
            price_method = PricingMethod.BLACKSCHOLES
        return super().Vega(price_method)

    def vanna(self):
        return 0

    def volga(self):
        return 0

    def forward_delta(self, delta_rhs):
        return 0

    def prices(self, value_dates, spots, pricingMethod=None):
        if pricingMethod is None:
            pricingMethod = self.pricingMethod
        prices = []
        for value_date in value_dates:
            sub_prices = []
            for spot in spots:
                asian_option = self.copy(spot, value_date)
                price = asian_option.price(pricingMethod)
                sub_prices.append(price)
            prices.append(sub_prices)
        return prices

    def getPricingMethod(self):
        return self.pricingMethod

    def copy(self, spotPx, reference_date):
        args_copy = list(self.args)
        args_copy[1] = reference_date
        args_copy[2] = spotPx
        return McpAsianOption(*args_copy)
        # return McpAsianOption(self.callPut,
        #                       reference_date,
        #                       self.strikePx,
        #                       spotPx,
        #                       self.volatility,
        #                       self.expiryDate,
        #                       self.settlementDate,
        #                       self.accRate,
        #                       self.undRate,
        #                       self.buySell,
        #                       self.averageMethod,
        #                       self.strikeType,
        #                       self.pricingMethod,
        #                       self.faceValue,
        #                       self.timeStep,
        #                       self.numSimulation,
        #                       self.calendar,
        #                       self.dayCounter,
        #                       self.premiumDate)


class McpFXVanilla(mcp.wrapper.McpVanillaOption, PayoffSpec):
    ins_count = 0
    ins_del_count = 0

    def __init__(self, *args):
        self.print_info = False
        McpFXVanilla.ins_count += 1
        self._ins_id = McpFXVanilla.ins_count
        if debug_del_info:
            print("fxv ins new: ", self._ins_id)
        self.field_dict = None
        # self.payoff_wrapper = PayoffWrapper(self)

        self.opt_type = 0
        self.pricing_method = 1
        if len(args) >= 12:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.spotPx = args[2]
            self.buySell = args[3]
            self.expiryDate = args[4]
            self.settlementDate = args[5]
            self.strikePx = args[6]
            self.domesticRate = args[7]
            self.foreignRate = args[8]
            self.volatility = args[9]
            self.faceAmount = args[10]
            self.calendar = args[11]
            if len(args) >= 14:
                self.opt_type = args[12]
                self.pricing_method = args[13]
            if len(args) >= 15:
                self.dayCounter = args[14]
            else:
                self.dayCounter = DayCounter.Act365Fixed
            day_counter = McpDayCounter(self.dayCounter)
            self.timeToExpiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
            self.timeToSettlement = day_counter.YearFraction(self.referenceDate, self.settlementDate)
            forward = math.exp((self.domesticRate - self.foreignRate) * self.timeToExpiry) * self.spotPx
            self.forward = forward

            super().__init__(self.callPut, self.strikePx, self.volatility,
                             self.timeToExpiry, self.timeToSettlement,
                             self.domesticRate, self.foreignRate, self.spotPx, self.buySell,
                             self.faceAmount, self.opt_type, self.pricing_method)

        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def __del__(self):
        self.Dispose()
        del self.field_dict
        McpFXVanilla.ins_del_count += 1
        if debug_del_info:
            print("fxv ins del: ", self._ins_id)

    # def del_ref(self):
    #     del self.payoff_wrapper.spec
    #     del self.payoff_wrapper
    #     self.Dispose()

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = {
                FieldName.BuySell: buy_sell_view(self.buySell),
                FieldName.CallPut: call_put_view(self.callPut),
                FieldName.StrikePx: self.strikePx,
                FieldName.Volatility: self.volatility,
                FieldName.TimeToExpiry: self.timeToExpiry,
                FieldName.TimeToSettlement: self.timeToSettlement,
                FieldName.DomesticRate: self.domesticRate,
                FieldName.ForeignRate: self.foreignRate,
                FieldName.SpotPx: self.spotPx,
                FieldName.ReferenceDate: self.referenceDate,
                FieldName.ExpiryDate: self.expiryDate,
                FieldName.SettlementDate: self.settlementDate,
                FieldName.Forward: self.forward,
                FieldName.FaceValue: self.faceAmount,
                FieldName.Premium: self.price(),
                FieldName.DeltaL: self.delta(False),
                FieldName.DeltaR: self.delta(True),
                FieldName.Gamma: self.gamma(),
                FieldName.Vega: self.vega(),
                FieldName.Theta: self.theta(),
                FieldName.RhoL: self.rho(False),
                FieldName.RhoR: self.rho(True),
                FieldName.OptionExpiryNature: enum_wrapper.key_of_value(self.opt_type,
                                                                        option_expiry_nature_class_name),
                FieldName.PricingMethod: enum_wrapper.key_of_value(self.pricing_method,
                                                                   pricing_method_class_name),
            }
        return self.field_dict

    def strike_from_price(self, price):
        bs = mcp.MBSVanilla()
        args = [self.callPut, price, self.volatility, self.timeToExpiry, self.timeToSettlement,
                self.domesticRate, self.foreignRate, self.spotPx]
        strike = bs.StrikeImpliedFromPrice(*args)
        return strike

    def greek(self):
        return {
            "Gamma": self.Gamma(),
            "Delta": self.Delta(True),
            "Vega": self.Vega(),
        }

    def price(self, price_method=None):
        if price_method is None or price_method == 0:
            return super().Price()
        else:
            return super().Price(price_method)

    def delta(self, delta_rhs, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Delta(delta_rhs, price_method)

    def rho(self, is_demestic_ccy, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Rho(is_demestic_ccy, price_method)

    def gamma(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Gamma(price_method)

    def theta(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Theta(price_method)

    def vega(self, price_method=None):
        if price_method is None:
            price_method = -1
        return super().Vega(price_method)

    def payoff_copy(self, value_date, spot):
        return McpFXVanilla(
            self.callPut,
            value_date,
            spot,
            self.buySell,
            self.expiryDate,
            self.settlementDate,
            self.strikePx,
            self.domesticRate,
            self.foreignRate,
            self.volatility,
            self.faceAmount,
            self.calendar,
            self.opt_type,
            self.pricing_method,
            self.dayCounter
        )

    def payoff_strikes(self):
        return [self.strikePx]


class McpFXForward(mcp.mcp.MFXForward, PayoffSpec):

    def __init__(self, *args):
        self.print_info = False
        self.field_dict = None
        # self.payoff_wrapper = PayoffWrapper(self, None)

        self.args = args
        #if len(args) >= 13:
        if len(args) == 13:
            self.strikePx = args[0]
            self.spotPx = args[1]
            self.accRate = args[2]
            self.undRate = args[3]
            self.forward = args[4]
            self.referenceDate = args[5]
            self.expiryDate = args[6]
            self.settlementDate = args[7]
            self.calendar = args[8]
            self.dayCounter = args[9]
            # if isinstance(args[9], MDayCounter):
            #     self.dayCounter = args[9]
            # else:
            #     self.dayCounter = MDayCounter(args[9])
            self.pricing_method = args[10]
            self.buySell = args[11]
            self.leverage = args[12]

            day_counter = McpDayCounter(self.dayCounter)
            self.timeToExpiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
            self.timeToSettlement = day_counter.YearFraction(self.referenceDate, self.settlementDate)

            s_args = [self.strikePx, self.spotPx, self.accRate,
                      self.undRate, self.forward,
                      self.timeToExpiry, self.timeToSettlement, self.pricing_method,
                      self.buySell, self.leverage]

            super().__init__(*s_args)

            v_acc_rate = self.accRate
            v_und_rate = self.undRate
            forward = super().GetForward()
            if self.pricing_method == FxFwdPricingMethod.MARKETFWD:
                forward = self.forward
                v_acc_rate = ""
                v_und_rate = ""

            self.act_forward = forward

            self.v_acc_rate = v_acc_rate
            self.v_und_rate = v_und_rate
            self.forward = forward
        else:
            super().__init__(*args)

    def __del__(self):
        self.Dispose()
        if debug_del_info:
            print("fxfwd del")

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = {
                FieldName.BuySell: buy_sell_view(self.buySell),
                FieldName.StrikePx: self.strikePx,
                FieldName.TimeToExpiry: self.timeToExpiry,
                FieldName.TimeToSettlement: self.timeToSettlement,
                FieldName.DomesticRate: self.v_acc_rate,
                FieldName.ForeignRate: self.v_und_rate,
                FieldName.SpotPx: self.spotPx,
                FieldName.ReferenceDate: self.referenceDate,
                FieldName.ExpiryDate: self.expiryDate,
                FieldName.SettlementDate: self.settlementDate,
                FieldName.Forward: self.forward,
                FieldName.FaceValue: self.leverage,

                FieldName.Premium: self.price(),
                FieldName.DeltaL: self.delta(False),
                FieldName.DeltaR: self.delta(True),
                FieldName.Gamma: self.gamma(),
                FieldName.Vega: self.vega(),
                FieldName.Theta: self.theta(),
                FieldName.RhoL: self.rho(False),
                FieldName.RhoR: self.rho(True),
                FieldName.PricingMethod: enum_wrapper.key_of_value(self.pricing_method,
                                                                   fwd_pricing_method_class_name),
            }
        return self.field_dict

    def price(self, isAmount=True):
        if isAmount is None:
            isAmount = True
        price = self.Price(isAmount)
        return price
    
    # def price(self, price_method=None):
    #     if price_method is None or price_method == 0:
    #         price_method = self.pricing_method
    #     price = super().Price(price_method)
    #     return price

    def Delta(self, isCcy2=False, isAmount=True, pricingMethod=1):
        # return self.leverage
        return super().Delta(isCcy2, isAmount)

    def Rho(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return super().Rho(isCcy2, isAmount)

    def Phi(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return super().Phi(isCcy2, isAmount)
    
    def Gamma(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return super().Gamma()

    def Vega(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return super().Vega()

    def Theta(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return super().Theta()

    def Volga(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return 0

    def Vanna(self, isCcy2=False, isAmount=True, pricingMethod=1):
        return 0

    def ForwardDelta(self, isCcy2=False, isAmount=True, pricingMethod=1):
        #return self.leverage
        return super().ForwardDelta(isCcy2,isAmount)
    
    def delta(self, delta_rhs, price_method=None):
        #return self.leverage
        return super().Delta(delta_rhs)

    def rho(self, is_demestic_ccy, price_method=None):
        #return 0
        return super().Rho(is_demestic_ccy)

    def gamma(self, price_method=None):
        return 0
        # return super().Gamma()

    def theta(self, price_method=None):
        return 0
        # return super().Theta()

    def vega(self, price_method=None):
        return 0
        # return super().Vega()

    def vanna(self):
        return 0

    def volga(self):
        return 0

    def forward_delta(self, delta_rhs):
        return self.leverage

    def payoff_of_mcp(self, value_date, spots):
        return self.payoff(value_date)

    def payoff_strikes(self):
        return [self.strikePx]

    def payoff_copy(self, value_date, spot):
        n_args = list(self.args)
        n_args[5] = value_date
        n_args[1] = spot
        return McpFXForward(*n_args)


class McpVanillaBarriers(mcp.mcp.MVanillaBarriers, PayoffSpec):

    def __init__(self, *args):
        self.print_info = False
        self.field_dict = None
        if len(args) == 25:
            self.mode = 2
            self.callPut = args[0]
            self.barrierType = args[1]
            self.referenceDate = args[2]
            self.spotPx = args[3]
            self.buySell = args[4]
            self.expiryDate = args[5]
            self.deliveryDate = args[6]
            self.strikePx = args[7]
            self.barrier = args[8]
            self.accRate = args[9]
            self.undRate = args[10]
            self.volatility = args[11]
            self.faceValue = args[12]
            self.rebate = args[13]
            self.pricingMethod = args[14]
            self.optionExpiryNature = args[15]
            self.barrierLow = args[16]
            self.rr25 = args[17]
            self.bf25 = args[18]
            self.discreteFactor = args[19]
            self.discreteAdjusted = args[20]
            self.calendar = args[21]
            self.dayCounter = args[22]
            self.premiumDate = args[23]
            self.numSimulation = int(args[24])

            day_counter = McpDayCounter(self.dayCounter)
            self.timeToExpiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
            self.timeToDelivery = day_counter.YearFraction(self.premiumDate, self.deliveryDate)

            print(f"McpVanillaBarriers args: {args}")
            mcp_args = to_mcp_args(args)
            super().__init__(*mcp_args)

            # super().__init__(self.callPut, self.barrierType, self.referenceDate, self.spotPx, self.buySell,
            #                  self.expiryDate, self.settlementDate, self.strikePx, self.barrier, self.accRate,
            #                  self.undRate, self.volatility, self.faceValue, self.rebate, self.adjTable.getHandler(),
            #                  self.adjustmentOnly, self.calendar.getHandler(), self.dayCounter)

            self.forward = math.exp((self.accRate - self.undRate) * self.timeToDelivery) * self.spotPx

        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def __del__(self):
        self.Dispose()
        if debug_del_info:
            print("br del")

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = {
                FieldName.BuySell: buy_sell_view(self.buySell),
                FieldName.CallPut: call_put_view(self.callPut),
                FieldName.StrikePx: self.strikePx,
                FieldName.Volatility: self.volatility,
                FieldName.TimeToExpiry: self.timeToExpiry,
                FieldName.TimeToSettlement: self.timeToSettlement,
                FieldName.DomesticRate: self.accRate,
                FieldName.ForeignRate: self.undRate,
                FieldName.SpotPx: self.spotPx,
                FieldName.ReferenceDate: self.referenceDate,
                FieldName.ExpiryDate: self.expiryDate,
                FieldName.SettlementDate: self.settlementDate,
                FieldName.Barrier: self.barrier,
                FieldName.FaceValue: self.faceValue,
                FieldName.Premium: self.price(),
                FieldName.OptionExpiryNature: FieldName.Barrier,
                FieldName.PricingMethod: enum_wrapper.key_of_value(PricingMethod.BLACKSCHOLES,
                                                                   pricing_method_class_name),
                FieldName.BarrierType: enum_wrapper.key_of_value(self.barrierType,
                                                                 barrier_type_class_name),
                FieldName.Forward: self.forward,

            }
        return self.field_dict

    def price(self, price_method=None):
        price = super().Price()
        return price

    def payoff_copy(self, value_date, spot):
        new_args = list(self.args)
        new_args[2] = value_date
        new_args[3] = spot
        return McpVanillaBarriers(*new_args)

    def payoff_by_spots(self, value_date, spots):
        s, pnls = self.payoff_of_mcp(value_date, spots)
        # print(f"vo payoff_of_mcp: {pnls}, {s}, {spots}")
        return pnls

    def payoff_strikes(self):
        return [
            self.strikePx,
            self.barrier,
            self.barrier + FwdDefConst.Barrier_Offset,
            self.barrier - FwdDefConst.Barrier_Offset
        ]

    # def Delta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Delta(isCcy2)
    #
    # def Rho(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Rho(isCcy2)
    #
    # def Gamma(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Gamma()
    #
    # def Vega(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Vega()
    #
    # def Theta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Theta()
    #
    # def Volga(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0
    #
    # def Vanna(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0
    #
    # def ForwardDelta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0

    def delta(self, delta_rhs, price_method=None):
        return super().Delta(delta_rhs)

    def rho(self, is_demestic_ccy, price_method=None):
        return super().Rho(is_demestic_ccy)

    def gamma(self, price_method=None):
        return super().Gamma()

    def theta(self, price_method=None):
        return super().Theta()

    def vega(self, price_method=None):
        return super().Vega()


class McpEuropeanDigital(mcp.mcp.MEuropeanDigital, PayoffSpec):

    def __init__(self, *args):
        self.print_info = False
        self.field_dict = None
        self.args = args

        self.referenceDate = args[0]
        self.digitalType = args[1]
        self.buySell = args[2]
        self.spotPx = args[3]
        self.strikePx = args[4]
        self.volatility = args[5]
        self.expiryDate = args[6]
        self.settlementDate = args[7]
        self.accRate = args[8]
        self.undRate = args[9]
        #self.faceValue = args[10]
        self.premiumDate = args[10]
        self.payoff_arg = args[11]
        self.calendar = args[12]
        self.dayCounter = args[13]
        self.pricingMethod = args[14]
        self.replicateDelta = args[15],
        self.rr25 = args[16]
        self.bf25 = args[17]
        #self.adjustmentOnly = args[16]

        day_counter = McpDayCounter(self.dayCounter)
        self.timeToExpiry = day_counter.YearFraction(self.referenceDate, self.expiryDate)
        self.timeToSettlement = day_counter.YearFraction(self.referenceDate, self.settlementDate)
        self.forward = mcp.wrapper.ForwardUtils.calc_forward(self.spotPx, self.timeToExpiry, self.accRate, self.undRate)

        # print(f"McpEuropeanDigital args: {args}")
        mcp_args = mcp.wrapper.to_mcp_args(args)

        super().__init__(*mcp_args)

        # self.price()
        self.tn_points = json.loads(self.GetTurningPoints())
        arr = []
        for item in self.tn_points:
            arr.extend([
                item,
                item + FwdDefConst.Barrier_Offset,
                item - FwdDefConst.Barrier_Offset
            ])
        self.strikes = arr

    def get_field_dict(self):
        if self.field_dict is None:
            self.field_dict = {
                FieldName.BuySell: buy_sell_view(self.buySell),
                # FieldName.CallPut: call_put_view(self.callPut),
                FieldName.StrikePx: self.strikePx,
                FieldName.Volatility: self.volatility,
                FieldName.TimeToExpiry: self.timeToExpiry,
                FieldName.TimeToSettlement: self.timeToSettlement,
                FieldName.DomesticRate: self.accRate,
                FieldName.ForeignRate: self.undRate,
                FieldName.SpotPx: self.spotPx,
                FieldName.ReferenceDate: self.referenceDate,
                FieldName.ExpiryDate: self.expiryDate,
                FieldName.SettlementDate: self.settlementDate,
                FieldName.Barrier: self.barrier,
                FieldName.FaceValue: self.payoff_arg,
                FieldName.Premium: self.price(),
                FieldName.DeltaL: self.delta(False),
                FieldName.DeltaR: self.delta(True),
                FieldName.Gamma: self.gamma(),
                FieldName.Vega: self.vega(),
                FieldName.Theta: self.theta(),
                FieldName.RhoL: self.rho(False),
                FieldName.RhoR: self.rho(True),
                FieldName.OptionExpiryNature: 'EUROPEAN',
                FieldName.PricingMethod: enum_wrapper.key_of_value(PricingMethod.BLACKSCHOLES,
                                                                   pricing_method_class_name),
                FieldName.DigitalType: enum_wrapper.key_of_value(self.digitalType,
                                                                 digital_type_class_name),
                FieldName.Forward: self.forward,
                "Payoff": self.payoff_arg,

            }
        return self.field_dict

    def price(self, price_method=None):
        price = super().Price()
        return price

    def payoff_copy(self, value_date, spot):
        new_args = list(self.args)
        new_args[0] = value_date
        new_args[3] = spot
        return McpEuropeanDigital(*new_args)

    def payoff_strikes(self):
        return self.strikes

    # def Delta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Delta(isCcy2)
    #
    # def Rho(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Rho(isCcy2)
    #
    # def Gamma(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Gamma()
    #
    # def Vega(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Vega()
    #
    # def Theta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return super().Theta()
    #
    # def Volga(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0
    #
    # def Vanna(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0
    #
    # def ForwardDelta(self, isCcy2=False, isAmount=True, pricingMethod=1):
    #     return 0

    def delta(self, delta_rhs, price_method=None):
        return super().Delta(delta_rhs)

    def rho(self, is_demestic_ccy, price_method=None):
        return super().Rho(is_demestic_ccy)

    def gamma(self, price_method=None):
        return super().Gamma()

    def theta(self, price_method=None):
        return super().Theta()

    def vega(self, price_method=None):
        return super().Vega()
