class DayCounter:
    NONE = -1
    Act360 = 0
    Act365Fixed = 1
    ThirtyE360 = 2
    ThirtyE360ISDA = 3
    ThirtyEPlus360 = 4
    ThirtyU360 = 5
    ActActISDA = 6
    ActActICMA = 7
    Act365L = 8
    ActActAFB = 9
    Act365Leap = 10
    ActActXTR = 11
    ActActICMAComplement = 12
    Act252 = 13


class Frequency:
    NoFrequency = -1
    Once = 0
    Annual = 1
    EveryEleventhMonth = -11
    EveryNinthMonth = -9
    EveryEigthMonth = -8
    Semiannual = 2
    EveryFifthMonth = -5
    EveryFourthMonth = 3
    Quarterly = 4
    Bimonthly = 6
    Monthly = 12
    Fourweekly = 13
    Biweekly = 26
    Weekly = 52
    EverySecondDay = 260
    Daily = 365
    Continuous = 366


class PaymentType:
    InArrears = 0
    InAdvance = 1
    InDiscount = 2


class DateAdjusterRule:
    Following = 0
    Preceding = 1
    ModifiedFollowing = 2
    ModifiedPreceding = 3
    IMM = 4
    Actual = 5
    LME = 6


class Direction:
    NONE = 0
    NEAREST = 1
    UP = 2
    DOWN = 3
    FRAC = 4
    TRUNC = 5


class PayoffStyle:
    NO_PAY = 1
    EXACT_PAY = 2
    FULL_PAY = 3


class InterpolationVariable:
    YIELDVOL = 0
    YIELDNORMALISEDVOL = 1
    YIELDPOINTSPERDAY = 2
    YIELDTOTALVARIANCE = 3
    PRICEVOL = 4
    PRICENORMALISEDVOL = 5
    PRICEPOINTSPERDAY = 6
    PRICETOTALVARIANCE = 7


class StrippingMethod:
    METHOD1 = 0
    METHOD2 = 1


class CapVolPaymentType:
    ARREARS = 0
    DISCOUNT = 1


class InterpolatedVariable:
    ZERORATES = -1
    SIMPLERATES = 0
    CONTINUOUSRATES = 1
    DISCOUNTFACTORS = 2
    HAZARDRATES = 3
    PND = 4
    SPREADS = 5
    YIELDVOLS = 6
    PRICEVOLS = 7
    YIELDTOTALVARIANCE = 8
    PRICETOTALVARIANCE = 9
    OVERNIGHTRATES = 10
    NORMALISEDYIELDVOL = 11
    NORMALISEDPRICEVOL = 12
    YIELDVOLPTSPERDAY = 13
    PRICEVOLPTSPERDAY = 14
    SIMPLEINFLATIONRATE = 15
    SIMPLEINFLATIONRATETIME = 16
    CONTINUOUSINFLATIONRATE = 17
    CONTINUOUSINFLATIONRATETIME = 18
    INFLATIONINDEX = 19
    FXFORWARDPOINTS = 20
    FORWARDSPLINEVARIABLE = 21


class SmileInterpolation:
    LINEAR = 0
    SVI = 1
    CUBICSPLINE = 2
    VANNAVOLGA = 3
    SABR = 4
    LINEAR_LOG_MONEYNESS = 5
    CUBICSPLINE_LOG_MONEYNESS = 6
    CUBICSPLINE_LINEAREXTRAPOLATION = 7
    SABR_CUBICSPLINE =8
    CUBICSPLINE_WINGRATIO = 9
    Q_VARIANCE_ON_LOG_MONEYNESS = 10
    Q_ORIGINAL_QAG = 11
    Q_FORWARD_DELTA_NATURAL_SPLINE = 12
    Q_MODIFIED_QAG = 13
    Q_FORWARD_DELTA_IMPLICIT_SPLINE = 14
    Q_STRIKE_NATURAL_SPLINE = 15
    Q_INVERTED_SURFACE_LOG_MONEYNESS = 16
    Q_INVERTED_SURFACE = 17
    Q_STRIKE_EXTENDED_SPLINE = 18
    Q_VARIANCE_EXTENDED_SPLINE = 19
    Q_MUREX_LOG_MONEYNESS = 20

class InterpolationMethod:
    FLATINTERPOLATION = 0
    CLOSESTINTERPOLATION = 1
    LINEARINTERPOLATION = 2
    LINEARXY = 3
    LOGLINEAR = 4
    LAGRANGEPOLYNOMIAL = 5
    CUBICSPLINES = 6
    FORWARDFORWARDQUARTIC = 7
    EXPLICITCLAMPEDCUBICSPLINES = 8
    FORWARDSPLINEMETHOD = 9
    # for support ParametricCurveModel
    NS = 11
    NSS = 12
    CIR = 13
    VASICEK = 14
    
# class ParametricCurveModel:
#     NS = 1
#     NSS = 2
#     CIR = 3
#     VASICEK = 4

class ExtrapolationMethod:
    NONE = 0
    FLATEXTRAPOLATION = 1
    LINEAREXTRAPOLATION = 2
    TAYLOREXTRAPOLATION = 3


class FXInterpolationType:
    DELTA_INTERPOLATION = 1
    STRIKE_INTERPOLATION = 2
    LOG_MONEYNESS = 3


class BuySell:
    Buy = 1
    Sell = -1

class Side:
    Bank = 1
    Client = -1

class CallPut:
    Call = 0
    Put = 1


class IROptionQuotation:
    PARYIELDVOL = 0
    PREMIUMPER1M = 1
    PREMIUMPER10K = 2
    PERCENTAGEPREMIUM = 3
    YIELDVOLQUOTE = 4
    PRICEVOLQUOTE = 5

class IROptionType:
    FLOOR = 0
    CAP   = 1
    PAYER = 2
    RECEIVER = 3

class ResetRateMethod:
    COMPOUNDING = 1
    SIMPLE_AVERAGE = 2
    CALCULATE_AVERAGE = 3
    RESETRATE_MAX = 4
    RESETRATE_MIN = 5
    ADV_MIUNS_ARR = 6
    ADV_DIVIDE_ARR = 7
    ARR_DIVIDE_ADV = 8


class PayReceive:
    Pay = -1
    Receive = 1


class StrikeInterpType:
    LINEAR = 0
    SABR = 1


class SABRApproxMethods:
    HAGAN = 0
    JOHNSONBLEND = 1


class SwaptionSettlementMethods:
    DELIVERY = 0
    CASH = 1
    CASHZC = 2


class HistVolsModel:
    CLOSE_TO_CLOSE = 0
    EWMA = 1
    LINXIAO = 2
    RISKMETRICS = 3


class HistVolsReturnMethod:
    RETURN = 0
    LOG_RETURN = 1


class BDTDataRateType:
    ZERORATE = 0
    PARBOND = 1


class BDTDataVolType:
    FIXED_SIGMA = 0
    ZERORATE_VOL = 1
    PARBOND_VOL = 2


class BondOptionType:
    PUT = 0
    CALL = 1
    CALL_PUT = 2
    ASS = 3
    CNV = 4
    DCN = 5
    ETS = 6


class PayoffModel:
    SNOWBALL = 1
    PHENIX = 2
    BARRIER = 3
    TONGXIN = 4


class OptionExpiryNature:
    EUROPEAN = 0
    AMERICAN = 1
    BERMUDAN = 2


class PricingMethod:
    BLACKSCHOLES = 1
    BAW = 2
    JUZHONG = 3
    BINOMIAL = 4
    TRINOMIAL = 5
    PDE = 6
    BSPDE = 7
    BSREPLICATE = 8
    VANNAVOLGA = 9
    MONTECARLO = 10
    WILMOTT = 11
    MONTECARLO_CPU = 12
    LSMC = 13
    ADERSON = 14


class FxFwdPricingMethod:
    MARKETFWD = 1
    INTERESTPARITY = 2


class AverageMethod:
    Arithmetic = 0
    Geometric = 1


class StrikeType:
    Fixed = 0
    Floating = 1


class BarrierType:
    INACTIVE = 1
    KNOCK_DOWN_IN = 2
    KNOCK_DOWN_OUT = 3
    KNOCK_UP_IN = 4
    KNOCK_UP_OUT = 5
    DOUBLE_KNOCK_IN = 6
    DOUBLE_KNOCK_OUT = 7

class InterestRateType:
    DEPOSIT = 1
    CONTINUOUSLY_COMPOUNDED = 2
    DISCOUNT_FACTOR = 3


class FXVolatilitySurfaceType:
    VARIANCE_ON_LOG_MONEYNESS = 0
    ORIGINAL_QAG = 1
    FORWARD_DELTA_NATURAL_SPLINE = 2
    MODIFIED_QAG = 3
    FORWARD_DELTA_IMPLICIT_SPLINE = 4
    STRIKE_NATURAL_SPLINE = 5
    INVERTED_SURFACE_LOG_MONEYNESS = 6
    INVERTED_SURFACE = 7
    STRIKE_EXTENDED_SPLINE = 8
    VARIANCE_EXTENDED_SPLINE = 9
    MUREX_LOG_MONEYNESS = 10


class FXVolatilityInterpolationType:
    LINEAR_VOLATILITY = 1
    LINEAR_TOTAL_VARIANCE = 2
    SPLINE_VOLATILITY = 3
    SPLINE_TOTAL_VARIANCE = 4
    INTERMEDIATE_SMILE_ON_LTV = 5

FXVolInterpType = FXVolatilityInterpolationType

class SmileInterpMethod:
    LINEAR = 0
    SVI = 1
    CUBICSPLINE = 2
    VANNAVOLGA = 3
    SABR = 4
    LINEAR_LOG_MONEYNESS = 5
    CUBICSPLINE_LOG_MONEYNESS = 6
    SVI_LOG_MONEYNESS = 7
    SABR_LOG_MONEYNESS =8
    Q_VARIANCE_ON_LOG_MONEYNESS = 10
    Q_ORIGINAL_QAG = 11
    Q_FORWARD_DELTA_NATURAL_SPLINE = 12
    Q_MODIFIED_QAG = 13
    Q_FORWARD_DELTA_IMPLICIT_SPLINE = 14
    Q_STRIKE_NATURAL_SPLINE = 15
    Q_INVERTED_SURFACE_LOG_MONEYNESS = 16
    Q_INVERTED_SURFACE = 17
    Q_STRIKE_EXTENDED_SPLINE = 18
    Q_VARIANCE_EXTENDED_SPLINE = 19
    Q_MUREX_LOG_MONEYNESS = 20


class DeltaType:
    SPOT_DELTA = 0
    FORWARD_DELTA = 1

class ATMVolType:
    DELTA_NEUTRAL_STRADDLE = 1
    FORWARD_STRIKE = 2
    SPOT_STRIKE = 3

class AsianOptionType:
    Asian_Fixed_Geometric = 8
    Asian_Fixed_Arithmetic = 9
    Asian_Floating_Geometric = 10
    Asian_Floating_Arithmetic = 11

class StrategyType:
    ATM_STRADDLE = 0
    RISK_REVERSAL = 1
    BUTTERFLY = 2
    STRANGLE = 3

class ParametricCurveModel:
    NS = 1
    NSS = 2
    CIR = 3
    VASICEK = 4


class CalculateTarget:
    NONE = 0
    Forward = 1
    UndRate = 2
    AccRate = 3

    FXForward = 1
    CCY1 = 2
    CCY2 = 3


class CalculatedTarget:
    FXForward = 1
    CCY1 = 2
    CCY2 = 3


class DigitalType:
    CASH_OR_NOTHING_CALL = 1
    ASSET_OR_NOTHING_CALL = 2
    CASH_OR_NOTHING_PUT = 3
    ASSET_OR_NOTHING_PUT = 4
    DOWN_CASH_AT_TOUCH = 5
    DOWN_ASSET_AT_TOUCH = 6
    UP_CASH_AT_TOUCH = 7
    UP_ASSET_AT_TOUCH = 8
    DOWN_IN_CASH_AT_EXPIRY = 9
    DOWN_IN_ASSET_AT_EXPIRY = 10
    UP_IN_CASH_AT_EXPIRY = 11
    UP_IN_ASSET_AT_EXPIRY = 12
    DOWN_OUT_CASH_AT_EXPIRY = 13
    DOWN_OUT_ASSET_AT_EXPIRY = 14
    UP_OUT_CASH_AT_EXPIRY = 15
    UP_OUT_ASSET_AT_EXPIRY = 16
    DOWN_IN_CASH_CALL = 17
    DOWN_IN_ASSET_CALL = 18
    UP_IN_CASH_CALL = 19
    UP_IN_ASSET_CALL = 20
    DOWN_IN_CASH_PUT = 21
    DOWN_IN_ASSET_PUT = 22
    UP_IN_CASH_PUT = 23
    UP_IN_ASSET_PUT = 24
    DOWN_OUT_CASH_CALL = 25
    DOWN_OUT_ASSET_CALL = 26
    UP_OUT_CASH_CALL = 27
    UP_OUT_ASSET_CALL = 28
    DOWN_OUT_CASH_PUT = 29
    DOWN_OUT_ASSET_PUT = 30
    UP_OUT_CASH_PUT = 31
    UP_OUT_ASSET_PUT = 32


class BondCouponType:
    BULLET = 1
    DISC = 2
    INTEREST = 3


class XsModelType:
    BlackSchole = 1
    BlackScholeF = 2
    Bachelier = 3
    BachelierF = 4
    Heson = 5
    HesonF = 6


class ModelType:
    BlackSchole = 1
    Bachelier = 2
    Heston = 3
    Dupire = 4
    DupireNLSF = 5
    # BlackSchole = 1
    # BlackScholeF = 2
    # Bachelier = 3
    # BachelierF = 4
    # Heson = 5
    # HesonF = 6

class LocalVolModel:
    Heston = 3
    Dupire = 4
    DupireNLSF = 5
    
class XScriptRunMode:
    AutoSelect = 0
    SingleThread = 1
    MultithreadCPU = 2
    GPU = 3


class LogLevel:
    Trace = 0
    Debug = 1
    Info = 2
    Warn = 3
    Error = 4
    Critical = 5
    Off = 6


class AssetClass:
    Forex = 1
    Equity = 2
    Commodity = 3
    Interest = 4

class ExchangePrincipal:
    BOTHENDS = 0
    STARTONLY = 1
    ENDONLY = 2
    NOEXCHANGE = 3

class AmortisationType:
    AMRT_NONE = 0
    AMRT_LINEAR_RT = 1
    AMRT_CONSTANT = 2
    AMRT_CONST_ANNU = 3
    AMRT_CPN_REINVEST = 5
    AMRT_LINEAR_AMT = 7
    AMRT_SCHEDULED = 8

class ResidualType:
    AbsoluteValue = 0
    Percent = 1
		
    
def key_value_of_enum(inst: object):
    keys = dir(inst)
    kv = {}
    for key in keys:
        if not key[0] == "_":
            kv[key] = getattr(inst, key)
    return inst.__class__.__name__, kv


class EnumFieldValue():

    def __init__(self):
        self.default_value = None
        self.value_dict = {}

    def add(self, class_name, value):
        class_name = str(class_name).lower()
        self.value_dict[class_name] = value
        if len(self.value_dict) == 1:
            self.default_value = value

    def get(self, enum_name=None):
        if len(self.value_dict) > 1 and enum_name is not None:
            enum_name = str(enum_name).lower()
            for key in self.value_dict:
                if enum_name.find(key) >= 0:
                    return self.value_dict[key]
        return self.default_value


class EnumWrapper():

    def __init__(self):
        self.field_dict = {}
        self.enum_kv = {}
        self.enum_vk = {}
        enum_list = [DayCounter(),
                     Frequency(),
                     PaymentType(),
                     DateAdjusterRule(),
                     Direction(),
                     BarrierType(),
                     PayoffStyle(),
                     InterpolationVariable(),
                     StrippingMethod(),
                     CapVolPaymentType(),
                     InterpolatedVariable(),
                     InterpolationMethod(),
                     BuySell(),
                     Side(),
                     CallPut(),
                     IROptionQuotation(),
                     IROptionType(),
                     ResetRateMethod(),
                     PayReceive(),
                     StrikeInterpType(),
                     SABRApproxMethods(),
                     SwaptionSettlementMethods(),
                     HistVolsModel(),
                     HistVolsReturnMethod(),
                     BDTDataVolType(),
                     BDTDataRateType(),
                     BondOptionType(),
                     PayoffModel(),
                     OptionExpiryNature(),
                     PricingMethod(),
                     AverageMethod(),
                     StrikeType(),
                     FxFwdPricingMethod(),
                     InterestRateType(),
                     SmileInterpolation(),
                     FXVolatilitySurfaceType(),
                     FXVolatilityInterpolationType(),
                     FXVolInterpType(),
                     DeltaType(),
                     ATMVolType(),
                     StrategyType(),
                     ExtrapolationMethod(),
                     FXInterpolationType(),
                     SmileInterpMethod(),
                     AsianOptionType(),
                     ParametricCurveModel(),
                     CalculateTarget(),
                     CalculatedTarget(),
                     DigitalType(),
                     BondCouponType(),
                     XsModelType(),
                     ModelType(),
                     XScriptRunMode(),
                     LogLevel(),
                     AssetClass(),
                     LocalVolModel(),
                     ExchangePrincipal(),
                     AmortisationType(),
                     ResidualType(),
                     ]
        for item in enum_list:
            self.parse_enum(item)

    def parse_enum(self, item):
        name, kv = key_value_of_enum(item)
        self.enum_kv[name] = {}
        self.enum_vk[name] = {}
        for key in kv:
            field_name = str(key).lower()
            self.enum_kv[name][field_name] = kv[key]
            self.enum_vk[name][kv[key]] = key
            if field_name not in self.field_dict:
                self.field_dict[field_name] = EnumFieldValue()
            efv: EnumFieldValue = self.field_dict[field_name]
            efv.add(name, kv[key])

    def key_of_value(self, val, enum_name):
        if enum_name in self.enum_vk:
            vk = self.enum_vk[enum_name]
            if val in vk:
                return vk[val]
        return ""

    def value_of_key(self, key, enum_name):
        if enum_name in self.enum_kv:
            kv = self.enum_kv[enum_name]
            if key in kv:
                return kv[key]
            lower_key = key.lower()
            if lower_key in kv:
                return kv[lower_key]
        return None

    def parse(self, field_name: str, enum_name=None):
        field_name = field_name.lower()
        if field_name in self.field_dict:
            efv: EnumFieldValue = self.field_dict[field_name]
            return efv.get(enum_name)
        return None

    def parse2(self, field_name: str, enum_name=None):
        if isinstance(field_name, int) or isinstance(field_name, float):
            return int(field_name)
        field_name_lower = field_name.lower().strip()
        result = None
        if field_name_lower in self.field_dict:
            efv: EnumFieldValue = self.field_dict[field_name_lower]
            result = efv.get(enum_name)
        if result is not None:
            return result
        else:
            raise Exception("Invalid enum: " + str(field_name))


enum_wrapper = EnumWrapper()
