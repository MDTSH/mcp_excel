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
    Parameters: identifiers - 债券代码, settlement_date - 结算日期
    Returns: 债券数据
    """
    result = mcp_server.McpFixedRateBonds2(identifiers, settlement_date)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpFixedRateBond", "object")
@xl_arg("flag", "bool")
def McpFixedRateBondData_Svr(mcpFixedRateBond, flag=False):
    """
    Get fixed rate bond数据
    Parameters: mcpFixedRateBond - 债券对象, flag - 格式化标志
    Returns: 债券数据
    """
    obj = mcp_server.object_data_cache[mcpFixedRateBond]
    return decode(obj, flag)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondCurve_Svr(identifiers):
    """
    get服务器端债券曲线
    Parameters: identifiers - 债券代码
    Returns: 债券曲线对象
    """
    frb = mcp_server.McpBondCurves(identifiers)
    return frb

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpBondCurve", "object")
@xl_arg("flag", "bool")
def McpBondCurveData_Svr(mcpBondCurve, flag=False):
    """
    get债券曲线数据
    Parameters: mcpBondCurve - 曲线对象, flag - 格式化标志
    Returns: 曲线数据
    """
    obj = mcp_server.object_data_cache[mcpBondCurve]
    return decode(obj, flag)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpParametricCurves_Svr(identifiers):
    """
    get服务器端参数化曲线
    Parameters: identifiers - 曲线代码
    Returns: 参数化曲线对象
    """
    frb = mcp_server.McpParametricCurves(identifiers)
    return frb


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpParametricCurve", "object")
@xl_arg("flag", "bool")
def McpParametricCurvesData_Svr(mcpParametricCurve, flag=False):
    """
    get参数化曲线数据
    Parameters: mcpParametricCurve - 曲线对象, flag - 格式化标志
    Returns: 曲线数据
    """
    obj = mcp_server.object_data_cache[mcpParametricCurve]
    return decode(obj, flag)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondRemainingMaturity_Svr(identifiers):
    """
    From serverget债券剩余期限
    Parameters: identifiers - 债券标识符
    Returns: 剩余期限
    """
    mcp_server.McpBondRemainingMaturity(identifiers)
    return mcp_server.McpBondRemainingMaturity(identifiers)

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("ccy", "str")
def McpCalendar_Svr(ccy):
    """
    From servercreate日历对象
    Parameters: ccy - 货币代码
    Returns: 日历对象
    """
    result = mcp_server.McpCalenders(ccy)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpCalender", "object")
@xl_arg("flag", "bool")
def McpCalendersData_Svr(mcpCalender, flag=False):
    """
    get日历数据
    Parameters: mcpCalender - 日历对象, flag - 格式化标志
    Returns: 日历数据
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
    From servercreate普通利率互换对象(带参数)
    Parameters: identifiers - 互换标识符, enddate - 结束日期, swaprate - 互换利率, point - 点数
    Returns: 互换对象
    """
    result = mcp_server.McpVanillaSwaps2(identifiers, enddate, swaprate, point)
    return result


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("identifiers", "str")
# def McpVanillaSwap_Svr(identifiers):
#     """
#     From servercreate普通利率互换对象
#     Parameters: identifiers - 互换标识符
#     Returns: 互换对象
#     """
#     result = mcp_server.McpVanillaSwaps(identifiers)
#     return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("mcpVanillaSwap", "object")
@xl_arg("flag", "bool")
def McpVanillaSwapsData_Svr(mcpVanillaSwap, flag=False):
    """
    get普通利率互换数据
    Parameters: mcpVanillaSwap - 互换对象, flag - 格式化标志
    Returns: 互换数据
    """
    result = mcp_server.McpVanillaSwapsData(mcpVanillaSwap,flag)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpVolSurface_Svr(identifiers):
    """
    From servercreate波动率曲面对象
    Parameters: identifiers - 曲面标识符
    Returns: 曲面对象
    """
    result = mcp_server.McpVolSurfaces(identifiers)
    return result


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpVolSurfaces", "object")
@xl_arg("flag", "bool")
def McpVolSurfacesData_Svr(mcpVolSurfaces, flag=False):
    """
    get波动率曲面数据
    Parameters: mcpVolSurfaces - 曲面对象, flag - 格式化标志
    Returns: 曲面数据
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
#     From serverget历史数据
#     Parameters: identifiers - 标识符, reference_date - 参考日期, count - 数量, periods - 期间
#     Returns: 历史数据
#     """
#     result = mcp_server.McpHistory(identifiers, reference_date, count, periods)
#     return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("key", "str")
def McpBondMarketData_Svr(identifiers, key):
    """
    From serverget债券市场数据
    Parameters: identifiers - 债券标识符, key - 数据键
    Returns: 市场数据
    """
    result = mcp_server.McpBondMarketData(identifiers, key)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpBondMarketArgs_Svr(identifiers):
    """
    From serverget债券市场参数
    Parameters: identifiers - 债券标识符
    Returns: 市场参数
    """
    result = mcp_server.McpBondMarketArgs(identifiers)
    return result

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpSwapCurve_Svr(identifiers):
    """
    From servercreate互换曲线对象
    Parameters: identifiers - 曲线标识符
    Returns: 曲线对象
    """
    frb = mcp_server.McpSwapCurves(identifiers)
    return frb

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("flag", "bool")
def McpVolSurface2_Svr(identifiers, flag=False):
    """
    From server根据名称get波动率曲面(版本2)
    Parameters: identifiers - 标识符, flag - 格式化标志
    Returns: 波动率曲面
    """
    vsf = mcp_server.McpVolSurface2ByName(identifiers, flag)
    return vsf

# to薛苗：为什么还要区分Euqity？？？
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpVolSurface2Equity_Svr(identifiers):
    """
    From serverget股票波动率曲面(版本2)
    Parameters: identifiers - 标识符
    Returns: 股票波动率曲面
    """
    vsf = mcp_server.McpVolSurface2Equity(identifiers)
    return vsf

# to薛苗：Flag是什么意思？？？
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("flag", "bool")
def McpVolSurface_Svr(identifiers, flag=False):
    """
    From server根据名称get波动率曲面
    Parameters: identifiers - 标识符, flag - 格式化标志
    Returns: 波动率曲面
    """
    vsf = mcp_server.McpVolSurfaceByName(identifiers, flag)
    return vsf

# to薛苗：现在有单边外汇波动率曲面吗？？？
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpFXVolSurface_Svr(identifiers):
    """
    From server根据名称get外汇波动率曲面
    Parameters: identifiers - 标识符
    Returns: 外汇波动率曲面
    """
    vsf = mcp_server.McpFXVolSurfaceByName(identifiers)
    return vsf


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
def McpFXVolSurface2_Svr(identifiers):
    """
    From server根据名称get外汇波动率曲面(版本2)
    Parameters: identifiers - 标识符
    Returns: 外汇波动率曲面
    """
    vsf = mcp_server.McpFXVolSurface2ByName(identifiers)
    return vsf

# to薛苗：所有XXXData是否可以合并到一个方法中？？？
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("mcpSwapCurve", "object")
@xl_arg("flag", "bool")
def McpSwapCurvesData_Svr(mcpSwapCurve, flag=False):
    """
    get互换曲线数据
    Parameters: mcpSwapCurve - 曲线对象, flag - 格式化标志
    Returns: 曲线数据
    """
    result = mcp_server.McpSwapCurvesData(mcpSwapCurve, flag)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifier", "str")
@xl_arg("key", "str")
def McpGetValue_Svr(identifier, key):
    """
    From serverget值
    Parameters: identifier - 标识符, key - 键
    Returns: 值
    """
    result = mcp_server.McpGetValue(identifier, key)
    return result

# to薛苗：什么意思，给解释？？？
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("class_name", "str")
@xl_arg("flag", "bool")
def McpBatchGetRowData_Svr(identifiers, class_name='', flag=False):
    """
    From server批量get行数据
    Parameters: identifiers - 标识符, class_name - 类名, flag - 格式化标志
    Returns: 行数据
    """
    result = mcp_server.McpBatchGetRowData(identifiers, class_name, flag)
    return result

# to薛苗：什么意思，给解释？？？
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("flag", "bool")
def decode(obj, flag=False):
    """
    From server解码对象
    Parameters: obj - 对象, flag - 格式化标志
    Returns: 解码后的数据
    """
    result = mcp_server.decode(obj, flag)
    return result

# to薛苗：什么意思，给解释？？？
@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("obj", "object")
@xl_arg("flag", "bool")
def decode2(obj, flag=False):
    """
    From server解码对象(方法2)
    Parameters: obj - 对象, flag - 格式化标志
    Returns: 解码后的数据
    """
    result = mcp_server.decode2(obj, flag)
    return result


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("identifiers", "str")
@xl_arg("curve_name", "str")
@xl_arg("yield_value", "str")
def McpZSpread_Svr(identifiers, curve_name, yield_value=''):
    """
    From server计算Z-Spread
    Parameters: identifiers - 标识符, curve_name - 曲线名称, yield_value - 收益率值
    Returns: Z-Spread值
    """
    result = mcp_server.McpZSpread(identifiers, curve_name, yield_value)
    return result

# to薛苗：什么意思，给解释？？？
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

# 新增接口
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