
from mcp.tool.args_def import tool_def



def McpYieldCurve(*args):
	return tool_def.tool_create('McpYieldCurve', args)


def McpYieldCurve2(*args):
	return tool_def.tool_create('McpYieldCurve2', args)

def McpForwardCurve2(*args):
	return tool_def.tool_create('McpForwardCurve2', args)

def McpForwardCurve(*args):
	return tool_def.tool_create('McpForwardCurve', args)

def McpSwapCurve(*args):
	return tool_def.tool_create('McpSwapCurve', args)


def McpVolSurface(*args):
	return tool_def.tool_create('McpVolSurface', args)


def McpMktVolSurface(*args):
	return tool_def.tool_create('McpMktVolSurface', args)


def McpMktVolSurface2(*args):
	return tool_def.tool_create('McpMktVolSurface2', args)

def McpFXVolSurface(*args):
	return tool_def.tool_create('McpFXVolSurface', args)


def McpFXVolSurface2(*args):
	return tool_def.tool_create('McpFXVolSurface2', args)

def McpVolSurface2(*args):
	return tool_def.tool_create('McpVolSurface2', args)

def McpVanillaStrategy(*args):
	return tool_def.tool_create('McpVanillaStrategy', args)

def McpVanillaOption(*args):
	return tool_def.tool_create('McpVanillaOption', args)

def McpFXForward(*args):
	return tool_def.tool_create('McpFXForward', args)

def McpFXForward2(*args):
	return tool_def.tool_create('McpFXForward2', args)

def McpAsianOption(*args):
	return tool_def.tool_create('McpAsianOption', args)


def McpFixedRateBond(*args):
	return tool_def.tool_create('McpFixedRateBond', args)

def McpAmortizingBond(*args):
	return tool_def.tool_create('McpAmortizingBond', args)

def McpCommodityFuture(*args):
	return tool_def.tool_create('McpCommodityFuture', args)

def McpBondFuture(*args):
	return tool_def.tool_create('McpBondFuture', args)

def McpEquityFuture(*args):
	return tool_def.tool_create('McpEquityFuture', args)

def McpEquitySpot(*args):
	return tool_def.tool_create('McpEquitySpot', args)

def McpFund(*args):
	return tool_def.tool_create('McpFund', args)

def McpFXNDF(*args):
	return tool_def.tool_create('McpFXNDF', args)

def McpRepurchaseProduct(*args):
	return tool_def.tool_create('McpRepurchaseProduct', args)

def McpBlack76Swaption(*args):
	return tool_def.tool_create('McpBlack76Swaption', args)


def McpVanillaSwap(*args):
	return tool_def.tool_create('McpVanillaSwap', args)

def McpXCurrencySwap(*args):
	return tool_def.tool_create('McpXCurrencySwap', args)

def McpCurrencySwapLeg(*args):
	return tool_def.tool_create('McpCurrencySwapLeg', args)

def McpSchedule(*args):
	return tool_def.tool_create('McpSchedule', args)


def McpCustomForwardDefine(*args):
	return tool_def.tool_create('McpCustomForwardDefine', args)


def McpCustomForward(*args):
	return tool_def.tool_create('McpCustomForward', args)


def McpSwaptionCube(*args):
	return tool_def.tool_create('McpSwaptionCube', args)


def McpCapVolStripping(*args):
	return tool_def.tool_create('McpCapVolStripping', args)


def McpCalendar(*args):
	return tool_def.tool_create('McpCalendar', args)


def McpParametricCurve(*args):
	return tool_def.tool_create('McpParametricCurve', args)


def McpBondCurve(*args):
	return tool_def.tool_create('McpBondCurve', args)


def McpBondSpreadCurve(*args):
	return tool_def.tool_create('McpBondSpreadCurve', args)


def McpRounder(*args):
	return tool_def.tool_create('McpRounder', args)


def McpRateConvention(*args):
	return tool_def.tool_create('McpRateConvention', args)


def McpRateConventionGetAllPredefined():
	"""Return list of all predefined RateConvention names (for Python use)"""
	from mcp.wrapper import get_all_predefined_rate_conventions
	return get_all_predefined_rate_conventions()


def McpEuropeanDigital(*args):
	return tool_def.tool_create('McpEuropeanDigital', args)


def McpDigitalOption(*args):
	"""数字期权构造函数，等价于 McpEuropeanDigital（创建 MDigitalOption）"""
	return tool_def.tool_create('McpEuropeanDigital', args)


def McpDoubleDigitalOption(*args):
	"""双障碍数字期权构造函数（创建 MDoubleDigitalOption）"""
	return tool_def.tool_create('McpDoubleDigitalOption', args)


def McpVanillaBarriers(*args):
	return tool_def.tool_create('McpVanillaBarriers', args)


def McpFXForwardPointsCurve(*args):
	return tool_def.tool_create('McpFXForwardPointsCurve', args)


def McpFXForwardPointsCurve2(*args):
	return tool_def.tool_create('McpFXForwardPointsCurve2', args)


def McpOvernightRateCurveData(*args):
	return tool_def.tool_create('McpOvernightRateCurveData', args)


def McpBillCurveData(*args):
	return tool_def.tool_create('McpBillCurveData', args)


def McpBillFutureCurveData(*args):
	return tool_def.tool_create('McpBillFutureCurveData', args)


def McpFRACurveData(*args):
	return tool_def.tool_create('McpFRACurveData', args)


def McpVanillaSwapCurveData(*args):
	return tool_def.tool_create('McpVanillaSwapCurveData', args)


def McpFixedRateBondCurveData(*args):
	return tool_def.tool_create('McpFixedRateBondCurveData', args)


def McpHestonModel(*args):
	return tool_def.tool_create('McpHestonModel', args)


def McpOptionData(*args):
	return tool_def.tool_create('McpOptionData', args)

def McpLocalVol(*args):
	return tool_def.tool_create('McpLocalVol', args)

def McpCapFloor(*args):
	return tool_def.tool_create('McpCapFloor', args)

def McpHistVols(*args):
	return tool_def.tool_create('McpHistVols', args)


def McpFXForwardOutright(*args):
	return tool_def.tool_create('McpFXForwardOutright', args)


def McpBond(*args):
	return tool_def.tool_create('McpBond', args)


def McpCallableBond(*args):
	return tool_def.tool_create('McpCallableBond', args)


def McpCommodityFutureAdapter(*args):
	return tool_def.tool_create('McpCommodityFutureAdapter', args)


def McpVanillaSwapAdapter(*args):
	return tool_def.tool_create('McpVanillaSwapAdapter', args)


def McpXCurrencySwapAdapter(*args):
	return tool_def.tool_create('McpXCurrencySwapAdapter', args)


def McpRepoAdapter(*args):
	return tool_def.tool_create('McpRepoAdapter', args)


def McpFundAdapter(*args):
	return tool_def.tool_create('McpFundAdapter', args)


def McpFXNDFAdapter(*args):
	return tool_def.tool_create('McpFXNDFAdapter', args)


def McpFXForwardSwapAdapter(*args):
	return tool_def.tool_create('McpFXForwardSwapAdapter', args)


def McpFXOptionsAdapter(*args):
	return tool_def.tool_create('McpFXOptionsAdapter', args)


def McpStructuredDerivativeProductAdapter(*args):
	return tool_def.tool_create('McpStructuredDerivativeProductAdapter', args)


def McpEquitySpotAdapter(*args):
	return tool_def.tool_create('McpEquitySpotAdapter', args)


def McpEquityFutureAdapter(*args):
	return tool_def.tool_create('McpEquityFutureAdapter', args)


def McpBondFutureAdapter(*args):
	return tool_def.tool_create('McpBondFutureAdapter', args)


def McpBondAdapter(*args):
	return tool_def.tool_create('McpBondAdapter', args)


def McpEquityOptionAdapter(*args):
	return tool_def.tool_create('McpEquityOptionAdapter', args)


def McpCommodityOptionAdapter(*args):
	return tool_def.tool_create('McpCommodityOptionAdapter', args)

