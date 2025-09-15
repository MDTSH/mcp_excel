from mcp.utils.enums import DateAdjusterRule, DayCounter, enum_wrapper
from mcp.forward.fwd_wrapper import McpVanillaOption
from mcp.mcp import MCalendar
from mcp.utils.mcp_utils import mcp_const
from mcp.wrapper import McpMktData, ForwardUtils, McpDayCounter
from mcp.xscript.utils import SttUtils


class McpVanillaOptionBatch:

    def __init__(self, d):
        self.vanilla: McpVanillaOption = d['VanillaOption'.lower()]
        self.mkt_data: McpMktData = d['MktData'.lower()]
        self.adjust_bid = SttUtils.get_value('BID调整', d, 0)
        self.adjust_ask = SttUtils.get_value('ASK调整', d, 0)
        self.adjust_risk = SttUtils.get_value('风险准备金', d, 0)
        self.und_day_counter = enum_wrapper.parse2(SttUtils.get_value('UndDayCounter', d, DayCounter.Act360),
                                                   'DayCounter')
        self.und_day_counter = McpDayCounter(self.und_day_counter)

    def adjust_forward(self, points):
        forward = self.vanilla.spotPx
        if self.vanilla.buySell == mcp_const.Side_Buy:
            forward += (points + self.adjust_bid) / 10000
        else:
            forward += (points + self.adjust_ask + self.adjust_risk) / 10000
        return forward

    def calc_price(self, tenor, strike_px, d={}):
        calendar: MCalendar = self.vanilla.calendar
        ref_date = self.vanilla.referenceDate
        ref_date_t2 = calendar.AddBusinessDays(ref_date, 2)
        stl_date = calendar.AddPeriod(ref_date_t2, tenor, DateAdjusterRule.ModifiedFollowing)
        expiry_date = calendar.AddBusinessDays(stl_date, -2)
        premium_date = ref_date_t2
        side_spot, side_acc, side_und, side_vol = ForwardUtils.bid_ask_sign(self.vanilla.buySell, self.vanilla.callPut)
        vol = self.mkt_data.get_strike_vol(strike_px, stl_date, side_vol)

        points = self.mkt_data.get_forward_points(stl_date, side_spot)
        forward = self.adjust_forward(points)
        time_to = self.und_day_counter.YearFraction(premium_date, stl_date)
        acc_rate = self.mkt_data.get_acc_rate(stl_date, side_acc)
        und_rate = self.mkt_data.get_und_rate(stl_date, side_und)
        forward, und_rate = self.mkt_data.calc_all(self.vanilla.spotPx, time_to, acc_rate, und_rate, forward)

        print(f"acc_rate={acc_rate}, und_rate={und_rate}, points={points}, forward={forward}")

        args = []
        args.extend(self.vanilla.args)
        args[3] = expiry_date
        args[4] = stl_date
        args[9] = premium_date
        args[5] = strike_px
        args[6] = acc_rate
        args[7] = und_rate
        args[8] = vol
        vo = McpVanillaOption(*args)
        print(f"calc_price args: {args}")
        return vo.price()
