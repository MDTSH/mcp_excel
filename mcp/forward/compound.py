from datetime import datetime

import mcp.mcp
from mcp.utils.excel_utils import FieldName
from mcp.utils.mcp_utils import mcp_const
from mcp.wrapper import MOptVolSurface, is_vol_surface, get_volatility
import mcp.wrapper
from mcp.forward.fwd_wrapper import *


class McpBaseCompound():

    def __init__(self):
        self.pricingMethod = None

    def price(self):
        pass

    def copy(self, args, guess_strike):
        return self

    def guess_strike_args(self, args):
        tolerance = 0.0000000001
        if FieldName.Tolerance in args:
            tolerance = float(args[FieldName.Tolerance])
        deltaRHS = True
        if FieldName.DeltaRHS in args:
            deltaRHS = str(args[FieldName.DeltaRHS]).lower() == "true"
        maxNumIterations = 100
        if FieldName.MaxNumIterations in args:
            maxNumIterations = int(args[FieldName.MaxNumIterations])
        return deltaRHS, tolerance, maxNumIterations

    def guess_strike(self, low, high, price, args):
        print("guess_strike:", low, high, price, args)
        dt_start = datetime.now()
        deltaRHS, tolerance, maxNumIterations = self.guess_strike_args(args)
        strike = None
        d_low = self.copy(args, low).price(self.pricingMethod)
        d_low -= price
        d_high = self.copy(args, high).price(self.pricingMethod)
        d_high -= price
        for i in range(maxNumIterations):
            mid = (high + low) / 2
            d_mid = self.copy(args, mid).price(self.pricingMethod) - price
            if abs(d_mid) <= tolerance:
                strike = mid
                break
            if d_low * d_mid < 0:
                high = mid
                d_high = d_mid
            else:
                low = mid
                d_low = d_mid
        dt_end = datetime.now()
        print("guess_strike use %s s, %s" % (dt_end - dt_start, args))
        return strike

    def strike_from_price(self, args):
        return None

    def floor_guess_price(self):
        return self.spotPx * 0.1

    def ceiling_guess_price(self):
        return self.spotPx * 2

    def getPricingMethod(self):
        return self.pricingMethod


class McpVanillaCompound(McpBaseCompound):

    def __init__(self):
        self.vanillas = []
        self.buy_sells = []
        self.leverages = []

    def price(self, pricingMethod):
        price = 0.0
        for i in range(len(self.vanillas)):
            fxv: McpVanillaOption = self.vanillas[i]
            sub_price = fxv.Price(pricingMethod)
            price += sub_price
        return price

    def legs(self):
        return [vs.field_dict for vs in self.vanillas]

    def get_vol(self, vs, strike, expiry_date):
        if not isinstance(vs, mcp.MVolatilitySurface) and not isinstance(vs, MOptVolSurface):
            raise Exception("Invalid VolatilitySurface")
        vol = vs.GetVolatility(strike, expiry_date, 2)
        return vol

    def get_rate(self, vs, expiry_date):
        if not isinstance(vs, mcp.MVolatilitySurface) and not isinstance(vs, MOptVolSurface):
            raise Exception("Invalid VolatilitySurface")
        acc_rate = vs.InterpolateRate(expiry_date, False, False)
        und_rate = vs.InterpolateRate(expiry_date, True, False)
        return acc_rate, und_rate

    def leg_payoff(self, value_date, spots, leg_num):
        leg_nums = []
        if leg_num <= 0 or leg_num > len(self.vanillas):
            leg_nums = range(len(self.vanillas))
        else:
            leg_nums = [leg_num - 1]
        payoffs = []
        for i in leg_nums:
            vanilla: McpVanillaOption = self.vanillas[i]
            payoff = vanilla.pay_off(value_date, spots, self.pricingMethod)
            payoffs.append(payoff)
        return payoffs

    def payoff_strikes(self):
        return []

    def payoff_by_spot(self, value_date, spot, rg):

        spots = payoff_spots(spot, rg, Payoff_Spot_Count, self.payoff_strikes())
        payoffs = self.payoff(value_date, spots)
        return spots, payoffs

    def payoff(self, value_date, spots: list):
        payoffs = []
        for fxv in self.vanillas:
            sub_payoff = fxv.pay_off(value_date, spots, self.pricingMethod)
            payoffs.append(sub_payoff)
        result = []
        for i in range(len(spots)):
            sub_result = 0
            for item in payoffs:
                sub_result += item[i]
            result.append(sub_result)
        return result


class McpRatioForward(McpVanillaCompound):

    def __init__(self, *args):
        super().__init__()
        if len(args) == 14:
            self.mode = 3

            self.referenceDate = args[0]
            self.spotPx = args[1]
            self.buySell = args[2]
            self.expiryDate = args[3]
            self.strikePx = args[4]
            self.accRate = args[5]
            self.undRate = args[6]
            self.volatility = args[7]
            self.settlementDate = args[8]
            self.priceSettlementDate = args[9]
            self.calendar = args[10]
            self.dayCount = args[11]
            self.optionExpiryNature = args[12]
            self.pricingMethod = args[13]

            self.buy_sells = [self.buySell, -1 * self.buySell]

            arg1 = [mcp_const.Call_Option, self.referenceDate, self.strikePx, self.spotPx,
                    self.volatility, self.expiryDate, self.settlementDate, self.accRate, self.undRate,
                    self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
            leg1 = McpVanillaOption(*arg1)
            arg2 = [mcp_const.Put_Option, self.referenceDate, self.strikePx, self.spotPx,
                    self.volatility, self.expiryDate, self.settlementDate, self.accRate, self.undRate,
                    self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
            leg2 = McpVanillaOption(*arg2)

            self.vanillas = [leg1, leg2]
        elif len(args) == 15:
            self.callPut = args[0]
            self.referenceDate = args[1]
            self.strikePx = args[2]
            self.spotPx = args[3]
            self.faceAmount = args[4]
            self.expiryDate = args[5]
            self.settlementDate = args[6]
            self.priceSettlementDate = args[7]
            self.Ratio = args[8]
            self.buySell = args[9]
            self.packageName = args[10]
            self.K1 = args[11]
            self.calendar = args[12]
            self.volSurface = args[13]
            self.K2 = args[14]

            self.buy_sells = [self.buySell, -1 * self.buySell]

            arg1 = [mcp_const.Call_Option, self.referenceDate, self.strikePx, self.spotPx,
                    self.faceAmount, self.expiryDate, self.settlementDate, self.priceSettlementDate, self.Ratio,
                    self.buy_sells[0], 0, self.K1, self.calendar, self.volSurface, self.K2]
            leg1 = McpVanillaOption(*arg1)
            arg2 = [mcp_const.Put_Option, self.referenceDate, self.strikePx, self.spotPx,
                    self.faceAmount, self.expiryDate, self.settlementDate, self.priceSettlementDate, self.Ratio,
                    self.buy_sells[1], 0, self.K1, self.calendar, self.volSurface, self.K2]
            leg2 = McpVanillaOption(*arg2)
        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def payoff_strikes(self):
        return [self.strikePx]

    def copy(self, args, guess_strike):
        return McpRatioForward(self.referenceDate,
                               self.spotPx,
                               self.buySell,
                               self.expiryDate,
                               guess_strike,
                               self.accRate,
                               self.undRate,
                               self.volatility,
                               self.settlementDate,
                               self.priceSettlementDate,
                               self.calendar,
                               self.dayCount,
                               self.optionExpiryNature,
                               self.pricingMethod)

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        return self.guess_strike(self.spotPx * 0.5, self.spotPx * 1.5, price, args)


class McpParForward(McpRatioForward):

    def __init__(self, *args):
        super().__init__(*args)


class McpRangeForward(McpVanillaCompound):

    def __init__(self, *args):
        super().__init__()
        if len(args) == 13:
            self.mode = 3

            self.referenceDate = args[0]
            self.spotPx = args[1]
            self.buySell = args[2]
            self.expiryDate = args[3]
            self.upBarrier = args[4]
            self.downBarrier = args[5]
            self.volSurface = args[6]
            self.settlementDate = args[7]
            self.priceSettlementDate = args[8]
            self.calendar = args[9]
            self.dayCount = args[10]
            self.optionExpiryNature = args[11]
            self.pricingMethod = args[12]

            self.buy_sells = [self.buySell, -1 * self.buySell]

            up_vol = self.get_vol(self.volSurface, self.upBarrier, self.expiryDate)
            down_vol = self.get_vol(self.volSurface, self.downBarrier, self.expiryDate)
            acc_rate, und_rate = self.get_rate(self.volSurface, self.expiryDate)

            arg1 = [mcp_const.Call_Option, self.referenceDate, self.upBarrier, self.spotPx,
                    up_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                    self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
            leg1 = McpVanillaOption(*arg1)
            arg2 = [mcp_const.Call_Option, self.referenceDate, self.downBarrier, self.spotPx,
                    down_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                    self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
            leg2 = McpVanillaOption(*arg2)
            self.vanillas = [leg1, leg2]
        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def payoff_strikes(self):
        return [self.upBarrier, self.downBarrier]

    def copy(self, args, guess_strike):
        up = None
        down = None
        if FieldName.UpBarrier in args:
            up = args[FieldName.UpBarrier]
            down = guess_strike
        elif FieldName.DownBarrier in args:
            up = guess_strike
            down = args[FieldName.DownBarrier]
        if self.mode == 3:
            arg = [self.referenceDate,
                   self.spotPx,
                   self.buySell,
                   self.expiryDate,
                   up,
                   down,
                   self.volSurface,
                   self.settlementDate,
                   self.priceSettlementDate,
                   self.calendar,
                   self.dayCount,
                   self.optionExpiryNature,
                   self.pricingMethod]
            return McpRangeForward(*arg)
        else:
            return None


class McpCapForward(McpVanillaCompound):

    def __init__(self, ignor_rate_check, *args):
        super().__init__()
        if len(args) == 13:
            self.mode = 2

            self.referenceDate = args[0]
            self.spotPx = args[1]
            self.buySell = args[2]
            self.expiryDate = args[3]
            self.capRate = args[4]
            self.forwardRate = args[5]
            self.volSurface = args[6]
            self.settlementDate = args[7]
            self.priceSettlementDate = args[8]
            self.calendar = args[9]
            self.dayCount = args[10]
            self.optionExpiryNature = args[11]
            self.pricingMethod = args[12]

            self.buy_sells = [mcp_const.Side_Buy, mcp_const.Side_Sell, mcp_const.Side_Sell]

            cap_vol = self.get_vol(self.volSurface, self.capRate, self.expiryDate)
            forward_vol = self.get_vol(self.volSurface, self.forwardRate, self.expiryDate)
            acc_rate, und_rate = self.get_rate(self.volSurface, self.expiryDate)

            if self.buySell == mcp_const.Side_Buy:
                arg1 = [mcp_const.Call_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Put_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Call_Option, self.referenceDate, self.capRate, self.spotPx,
                        cap_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check and self.capRate <= self.forwardRate:
                    raise Exception("Check CapRate > ForwardRate fail")
            else:
                arg1 = [mcp_const.Put_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Call_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Put_Option, self.referenceDate, self.capRate, self.spotPx,
                        cap_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check and self.capRate >= self.forwardRate:
                    raise Exception("Check CapRate < ForwardRate fail")
            leg1 = McpVanillaOption(*arg1)
            leg2 = McpVanillaOption(*arg2)
            leg3 = McpVanillaOption(*arg3)
            self.vanillas = [leg1, leg2, leg3]
        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def payoff_strikes(self):
        return [self.capRate, self.forwardRate]

    def copy(self, args, guess_strike):
        cap = None
        fwd = None
        if FieldName.CapRate in args:
            cap = args[FieldName.CapRate]
            fwd = guess_strike
        elif FieldName.ForwardRate in args:
            cap = guess_strike
            fwd = args[FieldName.ForwardRate]
        if self.mode == 2:
            arg = [self.referenceDate,
                   self.spotPx,
                   self.buySell,
                   self.expiryDate,
                   cap,
                   fwd,
                   self.volSurface,
                   self.settlementDate,
                   self.priceSettlementDate,
                   self.calendar,
                   self.dayCount,
                   self.optionExpiryNature,
                   self.pricingMethod]
            return McpCapForward(True, *arg)
        else:
            return None

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        if FieldName.CapRate in args:
            cap = args[FieldName.CapRate]
            if self.buySell == mcp_const.Side_Buy:
                high = cap
                low = self.floor_guess_price()
            else:
                high = self.ceiling_guess_price()
                low = cap
            return self.guess_strike(low, high, price, args)
        elif FieldName.ForwardRate in args:
            fwd = args[FieldName.ForwardRate]
            if self.buySell == mcp_const.Side_Buy:
                high = self.ceiling_guess_price()
                low = fwd
            else:
                high = fwd
                low = self.floor_guess_price()
            return self.guess_strike(low, high, price, args)
        return None


class McpFloorForward(McpVanillaCompound):

    def __init__(self, ignor_rate_check, *args):
        super().__init__()
        if len(args) == 13:
            self.mode = 2

            self.referenceDate = args[0]
            self.spotPx = args[1]
            self.buySell = args[2]
            self.expiryDate = args[3]
            self.floorRate = args[4]
            self.forwardRate = args[5]
            self.volSurface = args[6]
            self.settlementDate = args[7]
            self.priceSettlementDate = args[8]
            self.calendar = args[9]
            self.dayCount = args[10]
            self.optionExpiryNature = args[11]
            self.pricingMethod = args[12]

            self.buy_sells = [mcp_const.Side_Buy, mcp_const.Side_Sell, mcp_const.Side_Buy]

            floor_vol = self.get_vol(self.volSurface, self.floorRate, self.expiryDate)
            forward_vol = self.get_vol(self.volSurface, self.forwardRate, self.expiryDate)
            acc_rate, und_rate = self.get_rate(self.volSurface, self.expiryDate)

            if self.buySell == mcp_const.Side_Buy:
                arg1 = [mcp_const.Call_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Put_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Put_Option, self.referenceDate, self.floorRate, self.spotPx,
                        floor_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check and self.floorRate >= self.forwardRate:
                    raise Exception("Check FloorRate < ForwardRate fail")
            else:
                arg1 = [mcp_const.Put_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Call_Option, self.referenceDate, self.forwardRate, self.spotPx,
                        forward_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Call_Option, self.referenceDate, self.floorRate, self.spotPx,
                        floor_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check and self.floorRate <= self.forwardRate:
                    raise Exception("Check FloorRate > ForwardRate fail")
            leg1 = McpVanillaOption(*arg1)
            leg2 = McpVanillaOption(*arg2)
            leg3 = McpVanillaOption(*arg3)
            self.vanillas = [leg1, leg2, leg3]
        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def payoff_strikes(self):
        return [self.floorRate, self.forwardRate]

    def copy(self, args, guess_strike):
        floor = None
        fwd = None
        if FieldName.FloorRate in args:
            floor = args[FieldName.FloorRate]
            fwd = guess_strike
        elif FieldName.ForwardRate in args:
            floor = guess_strike
            fwd = args[FieldName.ForwardRate]
        if self.mode == 2:
            arg = [self.referenceDate,
                   self.spotPx,
                   self.buySell,
                   self.expiryDate,
                   floor,
                   fwd,
                   self.volSurface,
                   self.settlementDate,
                   self.priceSettlementDate,
                   self.calendar,
                   self.dayCount,
                   self.optionExpiryNature,
                   self.pricingMethod]
            return McpFloorForward(True, *arg)
        else:
            return None

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        if FieldName.FloorRate in args:
            floor = args[FieldName.FloorRate]
            if self.buySell == mcp_const.Side_Buy:
                high = self.ceiling_guess_price()
                low = floor
            else:
                high = floor
                low = self.floor_guess_price()
            return self.guess_strike(low, high, price, args)
        elif FieldName.ForwardRate in args:
            fwd = args[FieldName.ForwardRate]
            if self.buySell == mcp_const.Side_Buy:
                high = fwd
                low = self.floor_guess_price()
            else:
                high = self.ceiling_guess_price()
                low = fwd
            return self.guess_strike(low, high, price, args)
        return None


class McpSeagullForward(McpVanillaCompound):

    def __init__(self, ignor_rate_check, *args):
        super().__init__()
        if len(args) == 14:
            self.mode = 2

            self.referenceDate = args[0]
            self.spotPx = args[1]
            self.buySell = args[2]
            self.expiryDate = args[3]
            self.capRate = args[4]
            self.upBarrier = args[5]
            self.downBarrier = args[6]
            self.volSurface = args[7]
            self.settlementDate = args[8]
            self.priceSettlementDate = args[9]
            self.calendar = args[10]
            self.dayCount = args[11]
            self.optionExpiryNature = args[12]
            self.pricingMethod = args[13]

            self.buy_sells = [mcp_const.Side_Buy, mcp_const.Side_Sell, mcp_const.Side_Sell]

            cap_vol = self.get_vol(self.volSurface, self.capRate, self.expiryDate)
            up_vol = self.get_vol(self.volSurface, self.upBarrier, self.expiryDate)
            down_vol = self.get_vol(self.volSurface, self.downBarrier, self.expiryDate)
            acc_rate, und_rate = self.get_rate(self.volSurface, self.expiryDate)

            if self.buySell == mcp_const.Side_Buy:
                arg1 = [mcp_const.Call_Option, self.referenceDate, self.upBarrier, self.spotPx,
                        up_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Put_Option, self.referenceDate, self.downBarrier, self.spotPx,
                        down_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Call_Option, self.referenceDate, self.capRate, self.spotPx,
                        cap_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check:
                    if self.downBarrier < self.upBarrier < self.capRate:
                        pass
                    else:
                        raise Exception("Check DownBarrier < UpBarrier < CapRate fail")
            else:
                arg1 = [mcp_const.Put_Option, self.referenceDate, self.downBarrier, self.spotPx,
                        down_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[0], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg2 = [mcp_const.Call_Option, self.referenceDate, self.upBarrier, self.spotPx,
                        up_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[1], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                arg3 = [mcp_const.Put_Option, self.referenceDate, self.capRate, self.spotPx,
                        cap_vol, self.expiryDate, self.settlementDate, acc_rate, und_rate,
                        self.buy_sells[2], self.optionExpiryNature, self.pricingMethod, self.calendar, self.dayCount]
                if not ignor_rate_check:
                    if self.capRate < self.downBarrier < self.upBarrier:
                        pass
                    else:
                        raise Exception("Check CapRate < DownBarrier < UpBarrier  fail")
            leg1 = McpVanillaOption(*arg1)
            leg2 = McpVanillaOption(*arg2)
            leg3 = McpVanillaOption(*arg3)
            self.vanillas = [leg1, leg2, leg3]
        else:
            raise Exception("Unknown args, length=" + str(len(args)))

    def payoff_strikes(self):
        return [self.capRate, self.upBarrier, self.downBarrier]

    def copy(self, args, guess_strike):
        cap = None
        up = None
        down = None
        if FieldName.CapRate in args:
            cap = args[FieldName.CapRate]
        if FieldName.UpBarrier in args:
            up = args[FieldName.UpBarrier]
        if FieldName.DownBarrier in args:
            down = args[FieldName.DownBarrier]
        if cap is None:
            cap = guess_strike
        elif up is None:
            up = guess_strike
        elif down is None:
            down = guess_strike

        if self.mode == 2:
            arg = [self.referenceDate,
                   self.spotPx,
                   self.buySell,
                   self.expiryDate,
                   cap,
                   up,
                   down,
                   self.volSurface,
                   self.settlementDate,
                   self.priceSettlementDate,
                   self.calendar,
                   self.dayCount,
                   self.optionExpiryNature,
                   self.pricingMethod]
            return McpSeagullForward(True, *arg)
        else:
            return None

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        if FieldName.CapRate not in args:
            up = args[FieldName.UpBarrier]
            down = args[FieldName.DownBarrier]
            if self.buySell == mcp_const.Side_Buy:
                high = self.ceiling_guess_price()
                low = up
            else:
                high = down
                low = self.floor_guess_price()
            return self.guess_strike(low, high, price, args)
        elif FieldName.UpBarrier not in args:
            cap = args[FieldName.CapRate]
            down = args[FieldName.DownBarrier]
            if self.buySell == mcp_const.Side_Buy:
                high = cap
                low = down
            else:
                high = self.ceiling_guess_price()
                low = down
            return self.guess_strike(low, high, price, args)
        elif FieldName.DownBarrier not in args:
            cap = args[FieldName.CapRate]
            up = args[FieldName.UpBarrier]
            if self.buySell == mcp_const.Side_Buy:
                high = up
                low = self.floor_guess_price()
            else:
                high = up
                low = cap
            return self.guess_strike(low, high, price, args)
        return None
