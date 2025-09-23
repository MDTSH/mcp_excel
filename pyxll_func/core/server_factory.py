from typing import Any, Dict, List, Union

from pyxll import xl_func, xl_arg

from mcp.server_version import mcp_server

@xl_func(macro=False, recalc_on_open=True)
@xl_func("str url :str")
def SetNode(url: str) -> str:
    """
    Set server node URL for access
    Parameters: url - Node URL
    Returns: Loaded node
    """
    print(f'urlurlurlurl{url}')
    mcp_server.create_McpNode(url)
    return 'Server node loaded!'


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("class_name", "str")
def McpBatchCreateObjects(identifiers, class_name=''):
    result = mcp_server.McpBatchCreateObjects(identifiers, class_name)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("settlement_date", "var")
def McpFixedRateBond_Svr(identifiers, settlement_date):
    """
    Get fixed rate bond
    Parameters: identifiers - Bond code, settlement_date - Settlement date
    Returns: Bond data
    """
    result = mcp_server.McpFixedRateBonds(identifiers, settlement_date)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpFixedRateBond", "object")
@xl_arg("flag", "bool")
def McpFixedRateBondData_Svr(mcpFixedRateBond, flag=False):
    """
    Get fixed rate bond data
    Parameters: mcpFixedRateBond - Bond object, flag - Format flag
    Returns: Bond data
    """
    obj = mcp_server.object_data_cache[mcpFixedRateBond]
    return decode(obj, flag)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondCurve_Svr(identifiers):
    """
    Get server-side bond curve
    Parameters: identifiers - Bond code
    Returns: Bond curve object
    """
    frb = mcp_server.McpBondCurves(identifiers)
    return frb

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpBondCurve", "object")
@xl_arg("flag", "bool")
def McpBondCurveData_Svr(mcpBondCurve, flag=False):
    """
    Get bond curve data
    Parameters: mcpBondCurve - Curve object, flag - Format flag
    Returns: Curve data
    """
    obj = mcp_server.object_data_cache[mcpBondCurve]
    return decode(obj, flag)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpParametricCurves_Svr(identifiers):
    """
    Get server-side parametric curve
    Parameters: identifiers - Curve code
    Returns: Parametric curve object
    """
    frb = mcp_server.McpParametricCurves(identifiers)
    return frb


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpParametricCurve", "object")
@xl_arg("flag", "bool")
def McpParametricCurvesData_Svr(mcpParametricCurve, flag=False):
    """
    Get parametric curve data
    Parameters: mcpParametricCurve - Curve object, flag - Format flag
    Returns: Curve data
    """
    obj = mcp_server.object_data_cache[mcpParametricCurve]
    return decode(obj, flag)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondRemainingMaturity_Svr(identifiers):
    """
    Get bond remaining maturity from server
    Parameters: identifiers - Bond identifier
    Returns: Remaining maturity
    """
    mcp_server.McpBondRemainingMaturity(identifiers)
    return mcp_server.McpBondRemainingMaturity(identifiers)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("ccy", "str")
def McpCalendar_Svr(ccy):
    """
    Create calendar object from server
    Parameters: ccy - Currency code
    Returns: Calendar object
    """
    result = mcp_server.McpCalenders(ccy)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpCalender", "object")
@xl_arg("flag", "bool")
def McpCalendersData_Svr(mcpCalender, flag=False):
    """
    Get calendar data
    Parameters: mcpCalender - Calendar object, flag - Format flag
    Returns: Calendar data
    """
    result = mcp_server.McpCalendersData(mcpCalender,flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "var")
@xl_arg("swaprate", "var")
@xl_arg("point", "var")
def McpVanillaSwap_Svr(identifiers, enddate='', swaprate='', point='0'):
    """
    Create vanilla interest rate swap object from server (with parameters)
    Parameters: identifiers - Swap identifier, enddate - End date, swaprate - Swap rate, point - Points
    Returns: Swap object
    """
    result = mcp_server.McpVanillaSwaps2(identifiers, enddate, swaprate, point)
    return result


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("identifiers", "str")
# def McpVanillaSwap_Svr(identifiers):
#     """
#     Create vanilla interest rate swap object from server
#     Parameters: identifiers - Swap identifier
#     Returns: Swap object
#     """
#     result = mcp_server.McpVanillaSwaps(identifiers)
#     return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("mcpVanillaSwap", "object")
@xl_arg("flag", "bool")
def McpVanillaSwapsData_Svr(mcpVanillaSwap, flag=False):
    """
    Get vanilla interest rate swap data
    Parameters: mcpVanillaSwap - Swap object, flag - Format flag
    Returns: Swap data
    """
    result = mcp_server.McpVanillaSwapsData(mcpVanillaSwap,flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpVolSurface_Svr(identifiers):
    """
    Create volatility surface object from server
    Parameters: identifiers - Surface identifier
    Returns: Surface object
    """
    result = mcp_server.McpVolSurfaces(identifiers)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpVolSurfaces", "object")
@xl_arg("flag", "bool")
def McpVolSurfacesData_Svr(mcpVolSurfaces, flag=False):
    """
    Get volatility surface data
    Parameters: mcpVolSurfaces - Surface object, flag - Format flag
    Returns: Surface data
    """
    result = mcp_server.McpVolSurfacesData(mcpVolSurfaces,flag)
    return result

# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("identifiers", "str")
# @xl_arg("reference_date", "str")
# @xl_arg("count", "str")
# @xl_arg("periods", "str")
# def McpHistory_Svr(identifiers, reference_date, count, periods):
#     """
#     Get historical data from server
#     Parameters: identifiers - Identifier, reference_date - Reference date, count - Count, periods - Periods
#     Returns: Historical data
#     """
#     result = mcp_server.McpHistory(identifiers, reference_date, count, periods)
#     return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("key", "str")
def McpBondMarketData_Svr(identifiers, key):
    """
    Get bond market data from server
    Parameters: identifiers - Bond identifier, key - Data key
    Returns: Market data
    """
    result = mcp_server.McpBondMarketData(identifiers, key)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondMarketArgs_Svr(identifiers):
    """
    Get bond market parameters from server
    Parameters: identifiers - Bond identifier
    Returns: Market parameters
    """
    result = mcp_server.McpBondMarketArgs(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpSwapCurve_Svr(identifiers):
    """
    Create swap curve object from server
    Parameters: identifiers - Curve identifier
    Returns: Curve object
    """
    frb = mcp_server.McpSwapCurves(identifiers)
    return frb

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("flag", "bool")
def McpVolSurface2_Svr(identifiers, flag=False):
    """
    Get volatility surface by name from server (version 2)
    Parameters: identifiers - Identifier, flag - Format flag
    Returns: Volatility surface
    """
    vsf = mcp_server.McpVolSurface2ByName(identifiers, flag)
    return vsf

# Note: Why distinguish Equity?
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpVolSurface2Equity_Svr(identifiers):
    """
    Get equity volatility surface from server (version 2)
    Parameters: identifiers - Identifier
    Returns: Equity volatility surface
    """
    vsf = mcp_server.McpVolSurface2Equity(identifiers)
    return vsf

# Note: What does Flag mean?
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("flag", "bool")
def McpVolSurface_Svr(identifiers, flag=False):
    """
    Get volatility surface by name from server
    Parameters: identifiers - Identifier, flag - Format flag
    Returns: Volatility surface
    """
    vsf = mcp_server.McpVolSurfaceByName(identifiers, flag)
    return vsf

# Note: Is there unilateral FX volatility surface now?
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpFXVolSurface_Svr(identifiers):
    """
    Get FX volatility surface by name from server
    Parameters: identifiers - Identifier
    Returns: FX volatility surface
    """
    vsf = mcp_server.McpFXVolSurfaceByName(identifiers)
    return vsf


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpFXVolSurface2_Svr(identifiers):
    """
    Get FX volatility surface by name from server (version 2)
    Parameters: identifiers - Identifier
    Returns: FX volatility surface
    """
    vsf = mcp_server.McpFXVolSurface2ByName(identifiers)
    return vsf

# Note: Can all XXXData be merged into one method?
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpSwapCurve", "object")
@xl_arg("flag", "bool")
def McpSwapCurvesData_Svr(mcpSwapCurve, flag=False):
    """
    Get swap curve data
    Parameters: mcpSwapCurve - Curve object, flag - Format flag
    Returns: Curve data
    """
    result = mcp_server.McpSwapCurvesData(mcpSwapCurve, flag)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifier", "str")
@xl_arg("key", "str")
def McpGetValue_Svr(identifier, key):
    """
    Get value from server
    Parameters: identifier - Identifier, key - Key
    Returns: Value
    """
    result = mcp_server.McpGetValue(identifier, key)
    return result

# Note: What does this mean? Please explain.
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("class_name", "str")
@xl_arg("flag", "bool")
def McpBatchGetRowData_Svr(identifiers, class_name='', flag=False):
    """
    Get batch row data from server
    Parameters: identifiers - Identifier, class_name - Class name, flag - Format flag
    Returns: Row data
    """
    result = mcp_server.McpBatchGetRowData(identifiers, class_name, flag)
    return result

# Note: What does this mean? Please explain.
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("flag", "bool")
def decode(obj, flag=False):
    """
    Decode object from server
    Parameters: obj - Object, flag - Format flag
    Returns: Decoded data
    """
    result = mcp_server.decode(obj, flag)
    return result

# Note: What does this mean? Please explain.
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("flag", "bool")
def decode2(obj, flag=False):
    """
    Decode object from server (method 2)
    Parameters: obj - Object, flag - Format flag
    Returns: Decoded data
    """
    result = mcp_server.decode2(obj, flag)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("curve_name", "str")
@xl_arg("yield_value", "str")
def McpZSpread_Svr(identifiers, curve_name, yield_value=''):
    """
    Calculate Z-Spread from server
    Parameters: identifiers - Identifier, curve_name - Curve name, yield_value - Yield value
    Returns: Z-Spread value
    """
    result = mcp_server.McpZSpread(identifiers, curve_name, yield_value)
    return result

# Note: What does this mean? Please explain.
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("key", "str")
def McpGet_Svr(identifiers, key):
    result = mcp_server.McpGet1(identifiers, key)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("curve_name", "str")
@xl_arg("yield_value", "str")
def McpGSpread_Svr(identifiers, curve_name, yield_value=''):
    result = mcp_server.McpGSpread(identifiers, curve_name, yield_value)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def CleanPriceFromYield_Svr(identifiers, yield_value=''):
    result = mcp_server.McpCleanPriceFromYield(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def McpDirtyPriceFromYield(identifiers, yield_value=''):
    result = mcp_server.McpDirtyPriceFromYield(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def McpDurationCHN_Svr(identifiers, yield_value=''):
    result = mcp_server.McpDurationCHN(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def McpMDurationCHN_Svr(identifiers, yield_value=''):
    result = mcp_server.McpMDurationCHN(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def McpConvexityCHN_Svr(identifiers, yield_value=''):
    result = mcp_server.McpConvexityCHN(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("curve_name", "str")
def McpFrbPrice_Svr(identifiers, curve_name):
    result = mcp_server.McpFrbPrice(identifiers, curve_name)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("yield_value", "str")
def McpPVBPCHN_Svr(identifiers, yield_value=''):
    result = mcp_server.McpPVBPCHN(identifiers, yield_value)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("dirty_price", "str")
def McpYieldFromDirtyPrice_Svr(identifiers, dirty_price=''):
    result = mcp_server.McpYieldFromDirtyPrice(identifiers, dirty_price)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("curve_name", "str")
def McpFairValue_Svr(identifiers, curve_name):
    result = mcp_server.McpFairValue(identifiers, curve_name)
    return result

@xl_func("str identifiers: var[][]")
def McpFixedLegNPV_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegNPV(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFloatingLegNPV_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegNPV(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFixedLegDuration_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegDuration(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFloatingLegDuration_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegDuration(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFixedLegMDuration_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegMDuration(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFloatingLegMDuration_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegMDuration(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFixedLegAnnuity_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegAnnuity(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFloatingLegAnnuity_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegAnnuity(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFixedLegDV01_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegDV01(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFloatingLegDV01_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegDV01(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFixedLegAccrued_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegAccrued(identifiers)
    return result
@xl_func("str identifiers: var[][]")
def McpFloatingLegAccrued_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegAccrued(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFixedLegPremium_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegPremium(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFloatingLegPremium_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegPremium(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFixedLegMarketValue_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegMarketValue(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFloatingLegMarketValue_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegMarketValue(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFixedLegCumPV_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegCumPV(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFloatingLegCumPV_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegCumPV(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFixedLegCumCF_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFixedLegCumCF(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpFloatingLegCumCF_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpFloatingLegCumCF(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
@xl_arg("point", "str")
def McpNPV_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpNPV(identifiers, enddate, swaprate, point)
    return result

@xl_func("str identifiers: var[][]")
def McpMarketParRate_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpMarketParRate(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
@xl_arg("point", "str")
def McpDuration_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpDuration(identifiers, enddate, swaprate, point)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
@xl_arg("point", "str")
def McpMDuration_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpMDuration(identifiers, enddate, swaprate, point)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
def McpPV01_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpPV01(identifiers, enddate, swaprate, point)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
def McpDV01_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpDV01(identifiers, enddate, swaprate, point)
    return result

@xl_func("str identifiers: var[][]")
def McpCF_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpCF(identifiers)
    return result


@xl_func("str identifiers: var[][]")
def McpValuationDayCF_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpValuationDayCF(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("enddate", "str")
@xl_arg("swaprate", "str")
@xl_arg("point", "str")
def McpMarketValues_Svr(identifiers, enddate=None, swaprate=None, point=None):
    result = mcp_server.McpMarketValues(identifiers, enddate, swaprate, point)
    return result

@xl_func("var identifiers_or_obj: var[][]", macro=False, recalc_on_open=False)
@xl_arg("identifiers_or_obj", "var")
@xl_arg("isAmount", "bool", default=True)
def McpMarketValue_Svr(identifiers_or_obj: Union[str, object], isAmount: bool = True) -> Union[List[List[Any]], float]:
    result = mcp_server.McpMarketValue(identifiers_or_obj, isAmount)
    return result

@xl_func("str identifiers: var[][]")
def McpAccrued_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpAccrued(identifiers)
    return result

@xl_func("str identifiers: var[][]")
def McpPNLs_Svr(identifiers: str) -> List[List[Any]]:
    result = mcp_server.McpPNLs(identifiers)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("npv", "str")
def McpCalculateSwapRateFromNPV_Svr(identifiers, npv=''):
    result = mcp_server.McpCalculateSwapRateFromNPV(identifiers, npv)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bondlist", "var[]")
@xl_arg("amountlist", "var[]")
@xl_arg("yieldlist", "var[]")
def McpFIPortDurations_Svr(bondlist, amountlist, yieldlist):
    result = mcp_server.McpFIPortDurations(bondlist, amountlist, yieldlist)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bondlist", "var[]")
@xl_arg("amountlist", "var[]")
@xl_arg("tenors", "var[]")
@xl_arg("curvename", "str")
def McpFIPortKRDs_Svr(bondlist, amountlist, tenors, curvename):
    result = mcp_server.McpFIPortKRDs(bondlist, amountlist, tenors, curvename)
    return result

@xl_func(macro=False, recalc_on_open=False)
@xl_arg("assetid", "str")
@xl_arg("field", "str")
def McpGet_Svr(assetid, field):
    result = mcp_server.McpGet1(assetid, field)
    return result

# New interface
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpCapVolSurface_Svr(identifiers):
    result = mcp_server.McpCapVolSurface(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpCapVolSurface", "object")
@xl_arg("flag", "bool")
def McpCapVolSurfaceData_Svr(mcpVolSurfaces, flag=False):
    result = mcp_server.McpCapVolSurfaceData(mcpVolSurfaces, flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpSwaptionCube_Svr(identifiers):
    result = mcp_server.McpSwaptionCubes(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpSwaptionCube", "object")
@xl_arg("flag", "bool")
def McpSwaptionCubesData_Svr(mcpSwaptionCube, flag=False):
    result = mcp_server.McpSwaptionCubesData(mcpSwaptionCube, flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("refdate", "str")
def McpFXForwardPointsCurve_Svr(identifiers,refdate=""):
    result = mcp_server.McpFXForwardPointsCurves(identifiers,refdate)
    return result

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpFXForwardPointsCurves", "object")
@xl_arg("flag", "bool")
def McpFXForwardPointsCurvesData_Svr(mcpFXForwardPointsCurves, flag=False):
    result = mcp_server.McpFXForwardPointsCurvesData(mcpFXForwardPointsCurves, flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("refdate", "str")
def McpFXForwardPointsCurves2_Svr(identifiers,refdate=""):
    result = mcp_server.McpFXForwardPointsCurves2(identifiers,refdate)
    return result

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpFXForwardPointsCurves2", "object")
@xl_arg("flag", "bool")
def McpFXForwardPointsCurves2Data_Svr(mcpFXForwardPointsCurves2, flag=False):
    result = mcp_server.McpFXForwardPointsCurves2Data(mcpFXForwardPointsCurves2, flag)
    return result

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpFixedRateBond", "object")
@xl_arg("flag", "bool")
def McpFixedRateBondsData_Svr(mcpFixedRateBond, flag=False):
    obj = mcp_server.object_data_cache[mcpFixedRateBond]
    return decode(obj, flag)