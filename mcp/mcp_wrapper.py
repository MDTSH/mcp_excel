from mcp.mcp import MVanillaSwap


class WMVanillaSwap(MVanillaSwap):

    def __init__(self, map):
        super.__init__(
            # settlementDate, startDate, endDate,
            # coupon,
            # paymentCalendar.getHandler(),
            # fixedFrequency, fixedDayCounter,
            # useIndexEstimation,
            # floatingFrequency, floatingDayCounter,
            # yieldCurve.getHandler(),
            # floatingCalendar.getHandler(),
            # firstFixing, secondFixing,
            # eomRule,
            # compoundingFrequency,
            # notional,
            # csaId,
            # swapStartLag,
            # margin,
            # fixedAdjusterRule, floatAdjusterRule,
            # fixedLastOpenday, floatLastOpenday,
            # fixedLegPayReceive,
            # fixInAdvance,
            # fixDaysBackward, fixDaysForward,
            # endStub,
            # fixedPayType, floatPayType
        )