import json

from mcp import mcp
from mcp.mcp import MSchedRatioForward
from mcp.forward.compound import *


class McpSchedForward(McpBaseCompound):

    def __init__(self, *args):
        self.referenceDate = args[0]
        self.maturity = args[1]
        self.frequency = args[2]
        self.calendar: mcp.MCalendar = args[3]
        self.prevSettlementDate = args[4]
        self.firstSettlementDate = args[5]
        self.priceSettlementDate = args[6]
        self.endToEnd = args[7]
        self.longStub = args[8]
        self.endStub = args[9]
        self.applyDayCount = args[10]
        self.dateAdjuster = args[11]

        self.referenceDate_pure = mcp_dt.pure_digit(self.referenceDate)

        self.sd_maturity = []
        self.sd_settlement = []
        self.forwards = []
        self.periods = []

        self.generate_schedule()

        for i in range(len(self.sd_maturity)):
            maturity = self.sd_maturity[i]
            settlement = self.sd_settlement[i]
            self.add_period(maturity, settlement)

    def add_forward(self, maturity, settlement):
        return None

    def add_period(self, maturity, settlement):
        forward = self.add_forward(maturity, settlement)
        timeToExpiry = mcp_dt.time_to(self.referenceDate, maturity)
        timeToSettlement = mcp_dt.time_to(self.referenceDate, settlement)
        period = {
            FieldName.BuySell: buy_sell_view(self.buySell),
            FieldName.ExpiryDate: maturity,
            FieldName.ReferenceDate: self.referenceDate,
            FieldName.SpotPx: self.spotPx,
            FieldName.TimeToExpiry: timeToExpiry,
            FieldName.TimeToSettlement: timeToSettlement,
            FieldName.SettlementDate: settlement
        }
        self.periods.append(period)
        return period, forward

    def get_periods(self):
        return self.periods

    def get_forwards(self):
        return self.forwards

    def period_payoff(self, period_num, value_date, spots):
        period_nums = []
        if period_num <= 0 or period_num > len(self.forwards):
            period_nums = range(len(self.forwards))
        else:
            period_nums = [period_num - 1]
        payoffs = []
        for i in period_nums:
            fwd = self.forwards[i]
            payoff = fwd.payoff(value_date, spots)
            payoffs.append(payoff)
        return payoffs

    def period_leg_payoff(self, period_num, leg_num, value_date, spots):
        period_num -= 1
        if period_num >= 0 and period_num < len(self.forwards):
            fwd = self.forwards[period_num]
            return fwd.leg_payoff(value_date, spots, leg_num)
        else:
            return []

    def price(self, pricingMethod):
        result = 0
        for i in range(len(self.forwards)):
            fwd = self.forwards[i]
            sub_price = fwd.price(pricingMethod)
            result += sub_price
            # period = self.periods[i]
            # period[FieldName.Price] = sub_price
        return result

    def generate_schedule(self):
        lastOpenday = True
        adjStartDate = True
        adjEndDate = True
        stubDate = ""
        bothStub = True
        schedule = mcp.MSchedule(self.firstSettlementDate,
                                 self.maturity,
                                 self.frequency,
                                 self.calendar.getHandler(),
                                 self.dateAdjuster,
                                 self.endToEnd,
                                 self.longStub,
                                 self.endStub,
                                 lastOpenday,
                                 adjStartDate,
                                 adjEndDate,
                                 stubDate,
                                 bothStub)
        date_str = schedule.dates()
        temp_maturity = json.loads(date_str)
        # print("sd_maturity origin:", temp_maturity)
        for item in temp_maturity:
            item_pure = mcp_dt.pure_digit(item)
            if item_pure > self.referenceDate:
                self.sd_maturity.append(item)
        for item in self.sd_maturity:
            self.sd_settlement.append(self.calendar.AddBusinessDays(item, 2))
        # print("sd_maturity:", self.sd_maturity)
        # print("sd_settlement:", self.sd_settlement)


class McpSchedRatioForward(McpSchedForward):

    def __init__(self, *args):
        self.referenceDate = args[0]
        self.maturityDate = args[1]
        self.frequency = args[2]
        self.spotPx = args[3]
        self.buySell = args[4]
        self.dayCount = args[5]
        self.strikePx = args[6]
        self.calendar = args[7]
        self.volSurface: mcp.MVolatilitySurface = args[8]
        self.prevSettlementDate = args[9]
        self.firstSettlementDate = args[10]
        self.priceSettlementDate = args[11]
        self.optionExpiryNature = args[12]
        self.pricingMethod = args[13]
        self.accRate = args[14]
        self.undRate = args[15]
        self.volatility = args[16]

        endToEnd = True
        longStub = False
        endStub = True
        # applyDayCount = mcp.MDayCounter()
        dateAdjuster = 5
        super_args = [self.referenceDate, self.maturityDate, self.frequency, self.calendar,
                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate,
                      endToEnd, longStub, endStub, self.dayCount, dateAdjuster]
        super().__init__(*super_args)

    def add_forward(self, maturity, settlement):
        sub_args = [self.referenceDate,
                self.spotPx,
                self.buySell,
                maturity,
                self.strikePx,
                self.accRate,
                self.undRate,
                self.volatility,
                settlement,
                self.priceSettlementDate,
                self.calendar,
                self.dayCount,
                self.optionExpiryNature,
                self.pricingMethod]
        forward = McpRatioForward(*sub_args)
        self.forwards.append(forward)
        return forward

    def add_period(self, maturity, settlement):
        period, forward = super().add_period(maturity, settlement)

        acc_rate = self.volSurface.InterpolateRate(maturity, True, False)
        dom_rate = self.volSurface.InterpolateRate(maturity, False, False)
        vol = self.volSurface.GetVolatility(self.strikePx, maturity, 2)
        forward_rate = math.exp((acc_rate - dom_rate) * period[FieldName.TimeToExpiry]) * self.spotPx
        period[FieldName.DomesticRate] = acc_rate
        period[FieldName.ForeignRate] = dom_rate
        period[FieldName.Volatility] = vol
        period[FieldName.Forward] = forward_rate
        period[FieldName.StrikePx] = self.strikePx

    def copy(self, args, guess_strike):
        return McpSchedRatioForward(self.referenceDate, self.maturityDate, self.frequency,
                                    self.spotPx, self.buySell, self.dayCount, guess_strike,
                                    self.calendar, self.volSurface, self.prevSettlementDate,
                                    self.firstSettlementDate, self.priceSettlementDate, self.optionExpiryNature,
                                    self.pricingMethod, self.accRate, self.undRate, self.volatility)

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        return self.guess_strike(self.spotPx * 0.5, self.spotPx * 1.5, price, args)


class McpSchedParForward(McpSchedRatioForward):

    def __init__(self, *args):
        leverage = 1
        super_args = [args[0], args[1], args[2], args[3], args[4],
                      leverage,
                      args[5], args[6], args[7], args[8], args[9], args[10]]
        super().__init__(*super_args)


class McpSchedRangeForward(McpSchedForward):

    def __init__(self, *args):
        self.referenceDate = args[0]
        self.maturityDate = args[1]
        self.frequency = args[2]
        self.spotPx = args[3]
        self.buySell = args[4]
        # self.leverage = args[5]
        self.upBarrier = args[5]
        self.downBarrier = args[6]
        self.calendar = args[7]
        self.volSurface: mcp.MVolatilitySurface = args[8]
        self.prevSettlementDate = args[9]
        self.firstSettlementDate = args[10]
        self.priceSettlementDate = args[11]

        self.leverage = 1

        endToEnd = True
        longStub = False
        endStub = True
        applyDayCount = mcp.MDayCounter()
        dateAdjuster = 5
        super_args = [self.referenceDate, self.maturityDate, self.frequency, self.calendar,
                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate,
                      endToEnd, longStub, endStub, applyDayCount, dateAdjuster]
        super().__init__(*super_args)

    def add_forward(self, maturity, settlement):
        sub_args = [self.referenceDate, self.spotPx, self.buySell, maturity,
                    self.upBarrier, self.downBarrier, self.volSurface,
                    settlement, self.priceSettlementDate, self.calendar]
        forward = McpRangeForward(*sub_args)
        self.forwards.append(forward)
        return forward

    def add_period(self, maturity, settlement):
        period, forward = super().add_period(maturity, settlement)
        period[FieldName.UpBarrier] = self.upBarrier
        period[FieldName.DownBarrier] = self.downBarrier

    def copy(self, args, guess_strike):
        up = None
        down = None
        if FieldName.UpBarrier in args:
            up = args[FieldName.UpBarrier]
            down = guess_strike
        elif FieldName.DownBarrier in args:
            up = guess_strike
            down = args[FieldName.DownBarrier]
        return McpSchedRangeForward(self.referenceDate, self.maturityDate, self.frequency,
                                    self.spotPx, self.buySell,
                                    up, down,
                                    self.calendar, self.volSurface,
                                    self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate)

    def strike_from_price(self, args):
        price = args[FieldName.Price]
        if FieldName.UpBarrier in args:
            up = args[FieldName.UpBarrier]
            return self.guess_strike(self.floor_guess_price(), up, price, args)
        elif FieldName.DownBarrier in args:
            down = args[FieldName.DownBarrier]
            return self.guess_strike(down, self.ceiling_guess_price(), price, args)
        return None


class McpSchedCapForward(McpSchedForward):

    def __init__(self, ignor_rate_check, *args):
        self.referenceDate = args[0]
        self.maturityDate = args[1]
        self.frequency = args[2]
        self.spotPx = args[3]
        self.buySell = args[4]
        self.capRate = args[5]
        self.forwardRate = args[6]
        self.calendar = args[7]
        self.volSurface: mcp.MVolatilitySurface = args[8]
        self.prevSettlementDate = args[9]
        self.firstSettlementDate = args[10]
        self.priceSettlementDate = args[11]

        self.leverage = 1
        self.ignor_rate_check = ignor_rate_check

        endToEnd = True
        longStub = False
        endStub = True
        applyDayCount = mcp.MDayCounter()
        dateAdjuster = 5
        super_args = [self.referenceDate, self.maturityDate, self.frequency, self.calendar,
                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate,
                      endToEnd, longStub, endStub, applyDayCount, dateAdjuster]
        super().__init__(*super_args)

    def add_forward(self, maturity, settlement):
        sub_args = [self.referenceDate, self.spotPx, self.buySell, maturity,
                    self.capRate, self.forwardRate, self.volSurface,
                    settlement, self.priceSettlementDate, self.calendar]
        forward = McpCapForward(self.ignor_rate_check, *sub_args)
        self.forwards.append(forward)
        return forward

    def add_period(self, maturity, settlement):
        period, forward = super().add_period(maturity, settlement)
        period[FieldName.CapRate] = self.capRate
        period[FieldName.ForwardRate] = self.forwardRate

    def copy(self, args, guess_strike):
        cap = None
        fwd = None
        if FieldName.CapRate in args:
            cap = args[FieldName.CapRate]
            fwd = guess_strike
        elif FieldName.ForwardRate in args:
            cap = guess_strike
            fwd = args[FieldName.ForwardRate]
        return McpSchedCapForward(True, self.referenceDate, self.maturityDate, self.frequency,
                                  self.spotPx, self.buySell,
                                  cap, fwd,
                                  self.calendar, self.volSurface,
                                  self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate)

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


class McpSchedFloorForward(McpSchedForward):

    def __init__(self, ignor_rate_check, *args):
        self.referenceDate = args[0]
        self.maturityDate = args[1]
        self.frequency = args[2]
        self.spotPx = args[3]
        self.buySell = args[4]
        self.floorRate = args[5]
        self.forwardRate = args[6]
        self.calendar = args[7]
        self.volSurface: mcp.MVolatilitySurface = args[8]
        self.prevSettlementDate = args[9]
        self.firstSettlementDate = args[10]
        self.priceSettlementDate = args[11]

        self.leverage = 1
        self.ignor_rate_check = ignor_rate_check

        endToEnd = True
        longStub = False
        endStub = True
        applyDayCount = mcp.MDayCounter()
        dateAdjuster = 5
        super_args = [self.referenceDate, self.maturityDate, self.frequency, self.calendar,
                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate,
                      endToEnd, longStub, endStub, applyDayCount, dateAdjuster]
        super().__init__(*super_args)

    def add_forward(self, maturity, settlement):
        sub_args = [self.referenceDate, self.spotPx, self.buySell, maturity,
                    self.floorRate, self.forwardRate, self.volSurface,
                    settlement, self.priceSettlementDate, self.calendar]
        forward = McpFloorForward(self.ignor_rate_check, *sub_args)
        self.forwards.append(forward)
        return forward

    def add_period(self, maturity, settlement):
        period, forward = super().add_period(maturity, settlement)
        period[FieldName.FloorRate] = self.floorRate
        period[FieldName.ForwardRate] = self.forwardRate

    def copy(self, args, guess_strike):
        floor = None
        fwd = None
        if FieldName.FloorRate in args:
            floor = args[FieldName.FloorRate]
            fwd = guess_strike
        elif FieldName.ForwardRate in args:
            floor = guess_strike
            fwd = args[FieldName.ForwardRate]
        return McpSchedFloorForward(True, self.referenceDate, self.maturityDate, self.frequency,
                                    self.spotPx, self.buySell,
                                    floor, fwd,
                                    self.calendar, self.volSurface,
                                    self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate)

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


class McpSchedSeagullForward(McpSchedForward):

    def __init__(self, ignor_rate_check, *args):
        self.referenceDate = args[0]
        self.maturityDate = args[1]
        self.frequency = args[2]
        self.spotPx = args[3]
        self.buySell = args[4]
        self.capRate = args[5]
        self.upBarrier = args[6]
        self.downBarrier = args[7]
        self.calendar = args[8]
        self.volSurface: mcp.MVolatilitySurface = args[9]
        self.prevSettlementDate = args[10]
        self.firstSettlementDate = args[11]
        self.priceSettlementDate = args[12]

        self.leverage = 1
        self.ignor_rate_check = ignor_rate_check

        endToEnd = True
        longStub = False
        endStub = True
        applyDayCount = mcp.MDayCounter()
        dateAdjuster = 5
        super_args = [self.referenceDate, self.maturityDate, self.frequency, self.calendar,
                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate,
                      endToEnd, longStub, endStub, applyDayCount, dateAdjuster]
        super().__init__(*super_args)

    def add_forward(self, maturity, settlement):
        sub_args = [self.referenceDate, self.spotPx, self.buySell, maturity,
                    self.capRate, self.upBarrier, self.downBarrier, self.volSurface,
                    settlement, self.priceSettlementDate, self.calendar]
        forward = McpSeagullForward(self.ignor_rate_check, *sub_args)
        self.forwards.append(forward)
        return forward

    def add_period(self, maturity, settlement):
        period, forward = super().add_period(maturity, settlement)
        period[FieldName.CapRate] = self.capRate
        period[FieldName.UpBarrier] = self.upBarrier
        period[FieldName.DownBarrier] = self.downBarrier

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
        return McpSchedSeagullForward(True, self.referenceDate, self.maturityDate, self.frequency,
                                      self.spotPx, self.buySell,
                                      cap, up, down,
                                      self.calendar, self.volSurface,
                                      self.prevSettlementDate, self.firstSettlementDate, self.priceSettlementDate)

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


class McpScheduledRatioForward(MSchedRatioForward):

    def __init__(self, *args):
        super().__init__(*args)

    def price(self):
        return super().Price()
