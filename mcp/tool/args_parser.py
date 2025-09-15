from pandas import DataFrame

from mcp.utils.enums import *
from mcp.utils.excel_utils import mcp_kv_wrapper, pf_nd_arrary_or_list
from mcp.wrapper import McpCalendar, McpRounder

mcp_kv_wrapper.raise_parse_exception = False


class McpArgsType:

    def __init__(self):
        self.args_type_dict = {
            "int": "number",
            "date": "str",
            "datetime": "str",
            "str": "str",
            "float": "number",
            "bool": "str",
            "intbool": "str",
            "calendar": "object",
            "curve": "object",
            "list": "list",
            "plainlist": "str",
            "datelist": "list",
            "object": "object",
            "mcphandler": "object",
            "const": "str",
            "vdate": "str",
            "vfloat": "str",
            "jsonlist": "list",
            "objectlist": "list",
        }

    def get_type(self, name):
        if name in self.args_type_dict:
            return self.args_type_dict[name]
        else:
            return "str"


mcp_args_type = McpArgsType()


class McpArgsDef:

    def __init__(self):
        self.args_def_dict = {}

    def add_def(self, method, kvs_list):
        self.args_def_dict[method] = {
            "kvs_list": kvs_list,
        }

    def get_def(self, method):
        if method in self.args_def_dict:
            return self.args_def_dict[method]
        else:
            method = str(method).lower()
            for item in self.args_def_dict:
                key = str(item).lower()
                if key.find(method) >= 0:
                    return self.args_def_dict[item]
            return []

    def parse_dict_list(self, args):
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
            # print("parse DataFrame:", args.__class__)
            # print("parse DataFrame:", result)
            return result
        else:
            return pf_nd_arrary_or_list(args)

    def parse_args(self, method, args, fmt="VP", data_fields=[]):
        # if not muti_args:
        #     args_list = [args]
        # else:
        #     args_list = args
        args_list = args
        temp_list = pf_nd_arrary_or_list(args_list)
        args_list = [self.parse_dict_list(item) for item in temp_list]
        kvs_list = []
        if method in self.args_def_dict:
            kvs_list = self.args_def_dict[method]["kvs_list"]
        if len(kvs_list) > 0:
            kvs = kvs_list[0]
            kv_list = kvs_list[1:]
            result, lack_keys = mcp_kv_wrapper.valid_parse_kv_list(method,
                                                                   args_list, fmt, data_fields, kvs, kv_list)
            if len(lack_keys) > 0:
                raise Exception("Missing fields: " + str(lack_keys))
            else:
                return result["vals"]
        else:
            raise Exception("Invalid method")


class McpArgsDefImpl(McpArgsDef):

    def __init__(self):
        super().__init__()
        self.McpCalendar()
        self.McpYieldCurve()
        self.McpVanillaOption()
        self.McpAsianOption()
        self.McpFixedRateBond()
        self.McpVanillaSwap()
        self.McpSchedule()

    def McpCalendar(self):
        self.add_def("McpCalendar", [
            [
                ("Ccys", "objectlist"),
                ("Path", "str"),
                ("IsFile", "bool", True),
            ],
            [
                ("Ccys", "objectlist"),
                ("Dates", "objectlist"),
                ("IsFile", "bool", False),
            ],
        ])

    def McpVanillaOption(self):
        self.add_def("McpVanillaOption", [
            [
                ("CallPut", "const"),
                ("ReferenceDate", "str"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("ExpiryDate", "str"),
                ("SettlementDate", "str"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("BuySell", "const"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PremiumDate", "str"),
                ("NumSimulation", "int", 1000),
                ("FaceAmount", "float", 1),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "str"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("FaceAmount", "float", 1),
                ("ExpiryDate", "str"),
                ("SettlementDate", "str"),
                ("PremiumDate", "str"),
                ("BuySell", "const"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("VolSurface", "object"),
                ("NumSimulation", "int", 1000),
                ("AccCurve", "object"),
                ("UndCurve", "object"),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "str"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("FaceAmount", "float"),
                ("ExpiryDate", "str"),
                ("SettlementDate", "str"),
                ("PremiumDate", "str"),
                ("BuySell", "const"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("VolSurface", "object"),
                ("NumSimulation", "int", 1000),
            ]
        ])

    def McpAsianOption(self):
        self.add_def("McpAsianOption", [
            [
                ("CallPut", "const"),
                ("ReferenceDate", "str"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "str"),
                ("ExpiryDate", "str"),
                ("SettlementDate", "str"),
                ("StrikePx", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "str"),
                ("NumFixings", "int", 10),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("TimeStep", "int", 10),
                ("NumSimulation", "int", 10000),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "str"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "str"),
                ("ExpiryDate", "str"),
                ("SettlementDate", "str"),
                ("StrikePx", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "str"),
                ("FixingFrequency", "const", Frequency.Monthly, "Monthly"),
                ("FixingDateAdjuster", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("KeepEndOfMonth", "bool", True),
                ("FixingLongStub", "bool", False),
                ("FixingEndStub", "bool", True),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("TimeStep", "int", 10),
                ("NumSimulation", "int", 10000),
            ],
        ])

    def McpYieldCurve(self):
        self.add_def("McpYieldCurve", [
            [
                ("ReferenceDate", "str"),
                ("Dates", "objectlist"),
                ("ZeroRates", "objectlist"),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("Variable", "const", InterpolatedVariable.SIMPLERATES, "SIMPLERATES"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
            ],
            [
                ("ReferenceDate", "str"),
                ("Tenors", "objectlist"),
                ("ZeroRates", "objectlist"),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("Variable", "const", InterpolatedVariable.SIMPLERATES, "SIMPLERATES"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ]
        ])

    def McpFixedRateBond(self):
        rounder = McpRounder(0, 8)
        self.add_def("McpFixedRateBond", [
            [("Calendar", "object", McpCalendar("", "", "")),
             ("ValuationDate", "str"),
             ("MaturityDate", "str"),
             ("Frequency", "const", Frequency.Annual, "Annual"),
             ("Coupon", "float"),
             ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
             ("ExInterestDays", "int", 0, 0),
             ("FaceValue", "float", 100, 100),
             ("PrevCpnDate", "date", ""),
             ("LastCpnDate", "date", ""),
             ("Issuer", "str", "", ""),
             ("DirtyPriceRounder", "object", rounder),
             ("CleanPriceRounder", "object", rounder),
             ("AccruedInterestRounder", "object", rounder),
             ("CashRounder", "object", rounder),
             ("RedempRounder", "object", rounder),
             ("IssueDate", "str", "", ""),
             ("FirstCouponDate", "str", "", ""),
             ("NextCallDate", "str", "", ""),
             ("EndToEnd", "bool", True),
             ("LongStub", "bool", False),
             ("EndStub", "bool", False),
             ("ApplyDayCount", "bool", False),
             ("DateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
             ]
        ])

    def McpVanillaSwap(self):
        self.add_def("McpVanillaSwap", [
            [
                ("ReferenceDate", "str"),
                ("StartDate", "str"),
                ("EndDate", "str"),
                ("RollDate", "str"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("Notional", "float", 1000000, 1000000),
                ("Coupon", "float"),
                ("Margin", "float"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixedEstimationCurve", "object", "", ""),
                ("FixedDiscountCurve", "object", "", ""),
                ("FixedPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FixedPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("FixedPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixedResetFrequency", "const", Frequency.Once, "Once"),
                ("FixedResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),  
                ("FixedResetDayCounter", "const",  DayCounter.Act365Fixed, "Act365Fixed"),     
                ("FloatPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FloatPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("FloatPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FloatResetFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FloatResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),   
                ("FloatResetDayCounter", "const",  DayCounter.Act365Fixed, "Act365Fixed"),     
                ("FixingFrequency", "const", Frequency.Weekly),
                ("FixingIndex", "str", "7D", "7D"),
                ("FixingDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),   
                ("FloatEstimationCurve", "object", "", ""),
                ("FloatDiscountCurve", "object", "", ""),
                ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixInAdvance", "bool", True, True),
                ("FixDaysBackward", "int", 2, 2),
                ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
                ("HistoryFixingDates", "objectlist"),
                ("HistoryFixingRates", "objectlist"),
                ("FixedExchangeNotional", "bool", False, False),
                ("FixedResidual", "float", 0, 0),
                ("FixedResidualType", "const", ResidualType.AbsoluteValue),
                ("FixedFirstAmortDate", "date"),
                ("FixedAmortisationType", "const", AmortisationType.AMRT_NONE),
                ("FloatExchangeNotional", "bool", False, False),
                ("FloatResidual", "float", 0, 0),
                ("FloatResidualType", "const", ResidualType.AbsoluteValue),
                ("FloatFirstAmortDate", "date"),
                ("FloatAmortisationType", "const", AmortisationType.AMRT_NONE),
                ("FixedResetPaymentDates", "objectlist", "[]"),
                ("FixedResetRates", "objectlist", "[]"),   
                ("FixedResetAmortAmounts", "objectlist", "[]"),
                ("FloatResetPaymentDates", "objectlist", "[]"),
                ("FloatResetRates", "objectlist", "[]"),
                ("FloatResetAmortAmounts", "objectlist", "[]"),
                ("FixedKeepEndOfMonth", "bool", True),
                ("FixedLongStub", "bool", False),
                ("FixedEndStub", "bool", True),
                ("FixedAdjStartDate", "bool", True),
                ("FixedAdjEndDate", "bool", True),
                ("FloatKeepEndOfMonth", "bool", True),
                ("FloatLongStub", "bool", False),
                ("FloatEndStub", "bool", True),
                ("FloatAdjStartDate", "bool", True),
                ("FloatAdjEndDate", "bool", True),
            ],
            # [
            #     ("Curve", "object", "", ""),
            #     ("ValueDate", "str"),
            #     ("StartDate", "str", "",""),
            #     ("EndDate", "str"),
            #     ("RollDate", "str", "",""),
            #     ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
            #     ("Notional", "float", 1000000, 1000000),
            #     ("Coupon", "float"),
            #     ("Margin", "float", 0, 0),
            #     ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
            #     ("FixedEstimationCurve", "object", "", ""),
            #     ("FixedDiscountCurve", "object", "", ""),
            #     ("FixedPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FixedPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
            #     ("FixedPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FixedResetFrequency", "const", Frequency.Once, "Once"),
            #     ("FixedResetDateAdjuster", "const", DateAdjusterRule.LME, "LME"),    #设置LME，代表缺省等于PaymentDateAdjuster
            #     ("FixedResetDayCounter", "const", DayCounter.Act252, "Act252"),      #设置Act252，代表缺省等于PaymentDayCounter
            #     ("FloatPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FloatPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
            #     ("FloatPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FloatResetFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FloatResetDateAdjuster", "const", DateAdjusterRule.LME, "LME"),    #设置LME，代表缺省等于PaymentDateAdjuster
            #     ("FloatResetDayCounter", "const", DayCounter.Act252, "Act252"),      #设置Act252，代表缺省等于PaymentDayCounter
            #     ("FixingFrequency", "const", Frequency.Weekly),
            #     ("FixingIndex", "str", "7D", "7D"),
            #     ("FixingDateAdjuster", "const", DateAdjusterRule.LME, "LME"),    #设置LME，代表缺省等于PaymentDateAdjuster
            #     ("FloatEstimationCurve", "object", "", ""),
            #     ("FloatDiscountCurve", "object", "", ""),
            #     ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
            #     ("FixInAdvance", "bool", True, True),
            #     ("FixDaysBackward", "int", 2, 2),
            #     ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
            #     ("HistoryFixingDates", "objectlist", "[]"),
            #     ("HistoryFixingRates", "objectlist", "[]"),
            #     ("FixedResetPaymentDates", "objectlist", "[]"),
            #     ("FixedResetRates", "objectlist", "[]"),   
            #     ("FixedResetNotionals", "objectlist", "[]"),
            #     ("FloatResetPaymentDates", "objectlist", "[]"),
            #     ("FloatResetRates", "objectlist", "[]"),
            #     ("FloatResetNotionals", "objectlist", "[]"),
            # ],
            [
                ("SettlementDate", "str"),
                ("StartDate", "str"),
                ("EndDate", "str"),
                ("Coupon", "float"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixedFrequency", "const", Frequency.Annual, "Annual"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("UseIndexEstimation", "bool", False),
                ("FloatingFrequency", "const", Frequency.Annual, "Annual"),
                ("FloatingDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixedEstimationCurve", "object", "", ""),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("FloatingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FirstFixing", "float"),
                ("SecondFixing", "float"),
                ("EomRule", "int", 1),
                ("CompoundingFrequency", "int", 0),
                ("Notional", "float", 1000000, 1000000),
                ("CsaId", "str", ""),
                ("SwapStartLag", "int", 2),
                ("Margin", "float"),
                ("FixedAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("FloatAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("FixedLastOpenday", "bool", False),
                ("FloatLastOpenday", "bool", False),
                ("FixedLegPayReceive", "const", PayReceive.Pay, "Pay"),
                ("FixInAdvance", "bool", True),
                ("FixDaysBackward", "int", 2),
                ("FixDaysForward", "int", 2),
                ("EndStub", "bool", False),
                ("FixedPayType", "const", PaymentType.InArrears, "InArrears"),
                ("FloatPayType", "const", PaymentType.InArrears, "InArrears")
            ],

        ])

    def McpSchedule(self):
        self.add_def("McpSchedule", [
            [
                ("StartDate", "str"),
                ("EndDate", "str"),
                ("Frequency", "const", Frequency.Monthly, "Monthly"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("AdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("KeepEndOfMonth", "bool", False, False),
                ("LongStub", "bool", False, False),
                ("EndStub", "bool", False, False),
                ("LastOpenday", "bool", False, False),
                ("AdjStartDate", "bool", True, True),
                ("AdjEndDate", "bool", True, True),
                ("StubDate", "str"),
                ("bothStub", "bool", False, False),
            ],
        ])

    def McpTest(self):
        self.add_def("McpTest", [
        ])


mcp_args_def = McpArgsDefImpl()
