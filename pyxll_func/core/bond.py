# -*- coding: utf-8 -*-
"""
Bond Pricing Core Module

Provides Excel functions related to fixed rate bonds, including:
- Bond accrued interest calculation
- Bond cash flow analysis
- Bond pricing and yield calculation
- Bond risk metrics calculation
"""

import datetime
import json
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Union

from pyxll import xl_func, xl_arg, xl_return, RTD

# Simplified imports to avoid circular dependencies
try:
    from mcp import mcp
    from mcp.utils.async_func import async_func_manager, ThreadFuncRtd
    from mcp.utils.excel_utils import *
    from mcp.utils.mcp_utils import *
    from mcp.tool.args_def import tool_def
except ImportError:
    # If import fails, create empty placeholders
    mcp = None
    async_func_manager = None
    ThreadFuncRtd = None
    tool_def = None

class MFixedRateBond:
    """Fixed rate bond class"""
    
    def __init__(self, *args):
        """Initialize fixed rate bond object"""
        if mcp:
            super().__init__(*args)
            self.maturity_date = args[2] if len(args) > 2 else None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bond", "object")
def FrbAccruedInterestCHN(bond):
    """
    Calculate accrued interest for fixed rate bond in Chinese style
    
    Parameters:
        bond: Bond object
    
    Returns:
        float: Accrued interest amount, returns None if bond object doesn't support
    """
    if hasattr(bond, 'AccruedInterestCHN'):
        return bond.AccruedInterestCHN()
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bond", "object")
def FrbPreviousCouponDate(bond):
    """
    Get previous coupon date for fixed rate bond
    
    Parameters:
        bond: Bond object
        
    Returns:
        datetime: Previous coupon date, returns None if bond object doesn't support
    """
    if hasattr(bond, 'PreviousCouponDate'):
        return pd.to_datetime(bond.PreviousCouponDate())
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bond", "object")
def FrbNextCouponDate(bond):
    """
    Get next coupon date for fixed rate bond
    
    Parameters:
        bond: Bond object
        
    Returns:
        datetime: Next coupon date, returns None if bond object doesn't support
    """
    if hasattr(bond, 'NextCouponDate'):
        return pd.to_datetime(bond.NextCouponDate())
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
def FrbPrice(bond, curve):
    """
    Calculate fixed rate bond price
    
    Parameters:
        bond: Bond object
        curve: Yield curve object
        
    Returns:
        float: Bond price, returns None if bond object doesn't support
    """
    if hasattr(bond, 'Price'):
        return bond.Price(curve)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
def FrbFairValue(bond, curve):
    """
    Calculate fixed rate bond fair value
    
    Parameters:
        bond: Bond object
        curve: Yield curve object
        
    Returns:
        float: Bond fair value, returns None if bond object doesn't support
    """
    if hasattr(bond, 'FairValue'):
        return bond.FairValue(curve)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("fromDate", "datetime")
@xl_arg("toDate", "datetime")
def FrbActualPaidInterest(bond, fromDate, toDate):
    """
    Calculate actual interest payment for fixed rate bond in specified period
    
    Parameters:
        bond: Bond object
        fromDate: Start date
        toDate: End date
        
    Returns:
        float: Actual interest amount, returns None if bond object doesn't support
    """
    if hasattr(bond, 'ActualPaidInterest'):
        return bond.ActualPaidInterest(mcp_dt.to_pure_date(fromDate), mcp_dt.to_pure_date(toDate))
    return None


# ==================== Ride Strategy Related Functions ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("endDate", "datetime")
def FrbRCPaidInterest(bond, endDate):
    """
    RCPaidInterest(char* endDate)
    """
    if hasattr(bond, 'RCPaidInterest'):
        return bond.RCPaidInterest(mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yield", "float")
@xl_arg("endDate", "datetime")
def FrbRCConvergenceYield(bond, yield_, endDate):
    """
    RCConvergence(double yield, char* endDate)
    """
    if hasattr(bond, 'RCConvergence'):
        return bond.RCConvergence(yield_, mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
@xl_arg("endDate", "datetime")
def FrbRCConvergenceCurve(bond, curve, endDate):
    """
    RCConvergence(void* bondCurve, char* endDate)
    """
    if hasattr(bond, 'RCConvergence'):
        return bond.RCConvergence(curve.getHandler(), mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startYield", "float")
@xl_arg("endYield", "float")
@xl_arg("endDate", "datetime")
def FrbRCRolldownYields(bond, startYield, endYield, endDate):
    """
    RCRolldown(double startYield, double endYield, char* endDate)
    """
    if hasattr(bond, 'RCRolldown'):
        return bond.RCRolldown(startYield, endYield, mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
@xl_arg("endDate", "datetime")
def FrbRCRolldownCurve(bond, curve, endDate):
    """
    RCRolldown(void* bondCurve, char* endDate)
    """
    if hasattr(bond, 'RCRolldown'):
        return bond.RCRolldown(curve.getHandler(), mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("endDate", "datetime")
@xl_arg("investRate", "float")
def FrbRCReinvestReturn(bond, endDate, investRate):
    """
    RCReinvestReturn(char* endDate, double investRate)
    """
    if hasattr(bond, 'RCReinvestReturn'):
        return bond.RCReinvestReturn(mcp_dt.to_pure_date(endDate), investRate)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
@xl_arg("movedCurve", "object")
@xl_arg("endDate", "datetime")
def FrbRCMarketMoveCurves(bond, curve, movedCurve, endDate):
    """
    RCMarketMove(void* bondCurve, void* movedBondCurve, char* endDate)
    """
    if hasattr(bond, 'RCMarketMove'):
        return bond.RCMarketMove(curve.getHandler(), movedCurve.getHandler(), mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yield", "float")
@xl_arg("movedYield", "float")
@xl_arg("endDate", "datetime")
def FrbRCMarketMoveYields(bond, yield_, movedYield, endDate):
    """
    RCMarketMove(double yield, double movedYield, char* endDate)
    """
    if hasattr(bond, 'RCMarketMove'):
        return bond.RCMarketMove(yield_, movedYield, mcp_dt.to_pure_date(endDate))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("curve", "object")
@xl_arg("movedCurve", "object")
@xl_arg("endDate", "datetime")
def FrbRCRiddingReturn(bond, curve, movedCurve, endDate):
    """
    RCRiddingReturn(void* bondCurve, void* movedBondCurve, char* endDate)
    """
    if hasattr(bond, 'RCRiddingReturn'):
        return bond.RCRiddingReturn(curve.getHandler(), movedCurve.getHandler(), mcp_dt.to_pure_date(endDate))
    return None

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("frb", "object")
@xl_arg("bondCurve", "object")
@xl_arg("ccyLocRate", "float")
@xl_arg("fmt", "str")
def FrbFrtbGirrDeltas(frb, bondCurve, ccyLocRate=1.0, fmt="V"):
    if hasattr(frb, 'FrtbGirrDeltas'):
        s = frb.FrtbGirrDeltas(bondCurve.getHandler(),
                           ccyLocRate)
        return as_array(s, fmt)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("frb", "object")
@xl_arg("yld", "float")
@xl_arg("ccyLocRate", "float")
def FrbFrtbFxDelta(frb, yld, ccyLocRate):
    if hasattr(frb, 'FrtbFxDelta'):
        return frb.FrtbFxDelta(yld,
                           ccyLocRate)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("frb", "object")
@xl_arg("bondCurve", "object")
@xl_arg("isUp", "bool")
@xl_arg("ccyLocRate", "float")
def FrbFrtbGirrCurvature(frb, bondCurve, isUp=True, ccyLocRate=1.0):
    if hasattr(frb, 'FrtbGirrCurvature'):
        return frb.FrtbGirrCurvature(bondCurve,
                                 isUp,
                                 ccyLocRate)
    return None


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond", "object")
# @xl_arg("curve", "object")
# @xl_arg("isUp", "bool")
# @xl_arg("currency", "str")
# def FrbGirrCurvature(bond, curve, isUp=True, currency="CNY"):
#     return bond.GirrCurvature(curve.getHandler(), isUp, currency)
#
#
# @xl_func(macro=False, recalc_on_open=True, auto_resize=True)
# @xl_arg("bond", "object")
# @xl_arg("curve", "object")
# @xl_arg("deltaChg", "float")
# @xl_arg("fmt", "str")
# def FrbGirrDeltas(bond, curve, deltaChg=0.0001, fmt="V"):
#     return ac_schedule(bond.GirrDeltas(curve.getHandler(), deltaChg), fmt)
#
#
# @xl_func(macro=False, recalc_on_open=True, auto_resize=True)
# @xl_arg("bond", "object")
# @xl_arg("deltaChg", "float")
# @xl_arg("fmt", "str")
# def FrbGirrVegas(bond, deltaChg=0.0001, fmt="V"):
#     return ac_schedule(bond.GirrVegas(deltaChg), fmt)
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond", "object")
# @xl_arg("curve", "object")
# @xl_arg("deltaChg", "float")
# def FrbFrtpDelta(bond, curve, deltaChg=0.0001):
#     return bond.Frtp_Delta(curve.getHandler(), deltaChg)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
@xl_arg("curve", "object")
def FrbGSpread(bond, yld, curve):
    if hasattr(bond, 'GSpread'):
        return bond.GSpread(yld, curve)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
@xl_arg("curve", "object")
def FrbZSpread(bond, yld, curve):
    if hasattr(bond, 'ZSpread'):
        return bond.ZSpread(yld, curve)
    return None


# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond", "object")
# @xl_arg("curve", "object")
# def FrbPrice2(bond, curve):
#     return curve.ZeroRate(bond.maturity_date)
#
#
# @xl_func(macro=False, recalc_on_open=True)
# @xl_arg("bond", "object")
# @xl_arg("curve", "object")
# def FrbFairValue2(bond, curve):
#     yld = curve.ZeroRate(bond.maturity_date)
#     return bond.DirtyPriceFromYieldCHN(yld, True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
@xl_arg("compounding", "bool")
@xl_arg("settleDateAdjust", "int")
def FrbCleanPriceFromYieldCHN(bond, yld, compounding, settleDateAdjust):
    if hasattr(bond, 'CleanPriceFromYieldCHN'):
        return bond.CleanPriceFromYieldCHN(yld, compounding, settleDateAdjust)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
@xl_arg("compounding", "bool")
def FrbDirtyPriceFromYieldCHN(bond, yld, compounding):
    if hasattr(bond, 'DirtyPriceFromYieldCHN'):
        return bond.DirtyPriceFromYieldCHN(yld, compounding)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("dirtyPrice", "float")
@xl_arg("compounding", "bool")
def FrbYieldFromDirtyPriceCHN(bond, dirtyPrice, compounding):
    if hasattr(bond, 'YieldFromDirtyPriceCHN'):
        return bond.YieldFromDirtyPriceCHN(dirtyPrice, compounding)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("cleanPrice", "float")
@xl_arg("compounding", "bool")
def FrbYieldFromCleanPriceCHN(bond, cleanPrice, compounding):
    if hasattr(bond, 'YieldFromCleanPriceCHN'):
        return bond.YieldFromCleanPriceCHN(cleanPrice, compounding)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
def FrbPriceCHN(bond, yld):
    if hasattr(bond, 'PriceCHN'):
        return bond.PriceCHN(yld)
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
@xl_arg("forwardSettlementDate", "datetime")
@xl_arg("discountCurve", "object")
def FrbForwardPrice(bond, yld, forwardSettlementDate, discountCurve):
    if hasattr(bond, 'ForwardPrice'):
        return bond.ForwardPrice(yld, mcp_dt.to_pure_date(forwardSettlementDate), discountCurve)
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
def FrbDurationCHN(bond, yld):
    if hasattr(bond, 'DurationCHN'):
        return bond.DurationCHN(yld)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
def FrbMDurationCHN(bond, yld):
    if hasattr(bond, 'MDurationCHN'):
        return bond.MDurationCHN(yld)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
def FrbPVBPCHN(bond, yld):
    if hasattr(bond, 'PVBPCHN'):
        return bond.PVBPCHN(yld)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("yld", "float")
def FrbConvexityCHN(bond, yld):
    if hasattr(bond, 'ConvexityCHN'):
        return bond.ConvexityCHN(yld)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbAccruedDaysCHN(bond):
    if hasattr(bond, 'AccruedDaysCHN'):
        return bond.AccruedDaysCHN()
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbAccruedInterestCHN(bond):
    if hasattr(bond, 'AccruedInterestCHN'):
        return bond.AccruedInterestCHN()
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbMaturityDate(bond):
    if hasattr(bond, 'MaturityDate'):
        return bond.MaturityDate()
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbCouponRate(bond):
    if hasattr(bond, 'CouponRate'):
        return bond.CouponRate()
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbTimeToMaturity(bond):
    if hasattr(bond, 'TimeToMaturity'):
        return bond.TimeToMaturity()
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
def FrbCouponType(bond):
    if hasattr(bond, 'CouponType'):
        return bond.CouponType()
    return None

@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("bond", "object")
@xl_arg("fields", "str[]")
def FrbPayments(bond, fields):
    # PaymentDates = json.loads(bond.PaymentDates())
    # Payments = json.loads(bond.Payments())
    if hasattr(bond, 'PaymentDates') and hasattr(bond, 'Payments'):
        PaymentDates = bond.PaymentDates()
        Payments = bond.Payments()
        pos = []
        headers = []
        for i in range(len(PaymentDates)):
            po = {
                "PaymentDate": PaymentDates[i],
                "Payment": Payments[i],
            }
            pos.append(po)
            headers.append("Period" + str(i + 1))
        result = []
        for i in range(len(pos)):
            obj = []
            obj.append("Period" + str(i + 1))
            for field in fields:
                obj.append(pos[i][field])
            result.append(obj)
        return result
    return None

## Amortization Calculation
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
@xl_arg("initCost", "float")
def FrbAmCost(bond, startDate, endDate, initCost):
    if tool_def:
        args = [bond, startDate, endDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='AmCost')
        except Exception as e:
            s = f"FrbAmCost except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None

## Amortization Calculation, Amortized Cost
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
@xl_arg("initCost", "float")
def FrbAmEIR(bond, startDate, endDate, initCost):
    if tool_def:
        args = [bond, startDate, endDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='AmEIR')
        except Exception as e:
            s = f"FrbAmEIR except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None

## Amortization Calculation, Effective Interest Income
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
@xl_arg("initCost", "float")
def FrbAmERInstIncome(bond, startDate, endDate, initCost):
    if tool_def:
        args = [bond, startDate, endDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='AmERInstIncome')
        except Exception as e:
            s = f"FrbAmERInstIncome except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None
    
## Amortization Calculation, Accrued Interest Income
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
@xl_arg("initCost", "float")
def FrbAmAccuredInstIncome(bond, startDate, endDate, initCost):
    if tool_def:
        args = [bond, startDate, endDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='AmAccuredIncome')
        except Exception as e:
            s = f"FrbAmAccuredInstIncome except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None

## Amortization Calculation, Cash Flow
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
@xl_arg("initCost", "float")
def FrbAmCashflow(bond, startDate, endDate, initCost):
    if tool_def:
        args = [bond, startDate, endDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='AmCashflow')
        except Exception as e:
            s = f"FrbAmCashflow except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None
    
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("trade_cleanprice", "float")
@xl_arg("trade_date", "datetime")
def FrbAmortizationCleanPrice(bond, trade_cleanprice: float, trade_date: date):
    """
    Calculate the clean price amortization for a fixed-rate bond.
    bond.MaturityDate() and bond.GetRefDate() may return strings or dates;
    parse_excel_date(...) must return a datetime.date.

    Amortization formula:
      P(t) = 100 + (P(trade) - 100) * (T - t) / (T - trade_date)

    Constraints:
      – valuation_date = max(valuation_date, trade_date)
      – if valuation_date >= maturity_date, return 100
    """
    if hasattr(bond, 'MaturityDate') and hasattr(bond, 'GetRefDate'):
        try:
            # 1) parse maturity & valuation dates into datetime.date
            m = bond.MaturityDate()
            r = bond.GetRefDate()
            maturity_date  = parse_excel_date(m)   # must return datetime.date
            valuation_date = parse_excel_date(r)   # must return datetime.date

            # 2) clamp valuation_date to [trade_date, maturity_date]
            if valuation_date < trade_date:
                valuation_date = trade_date
            if valuation_date >= maturity_date:
                return 100.0

            # 3) compute days
            total_days    = (maturity_date - trade_date).days
            remaining_days = (maturity_date - valuation_date).days

            # 4) amortized clean price
            amortized_price = 100 + (trade_cleanprice - 100) * remaining_days / total_days
            return amortized_price

        except Exception as e:
            return f"FrbAmortizationCleanPrice except: {e}"
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("trade_cleanprice", "float")
@xl_arg("trade_date", "datetime")
def FrbAmortizationDirtyPrice(bond, trade_cleanprice: float, trade_date: date):
    if hasattr(bond, 'AccruedInterestCHN'):
        accrued = bond.AccruedInterestCHN()
        return accrued + FrbAmortizationCleanPrice(bond, trade_cleanprice,trade_date)
    return None



@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpBDTData(args1, args2, args3, args4, args5, fmt="VP|HD"):
    if mcp:
        data_fields = [
            ("Dates", "date"),
            ("Rates", "float"),
            ("Vols", "float"),
        ]
        args = [args1, args2, args3, args4, args5]
        args = mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
        result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpBDTData, args, [
            ("Dates", "plainlist"),
            ("Rates", "plainlist"),
            ("Vols", "plainlist"),
            ("RateType", "const"),
            ("VolType", "const"),
        ])
        if len(lack_keys) > 0:
            return "Missing fields: " + str(lack_keys)
        vals = result["vals"]
        #print("McpBDTData final args:")
        #print(vals)
        vs = mcp.MBDTData(*vals)
        mcp_method_args_cache.cache(str(vs), result)
        return vs
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("format", "str")
def McpBDTTree2(args1, args2, args3, args4, args5, fmt="VP|HD"):
    if mcp:
        method = "McpBDTTree"
        args = [args1, args2, args3, args4, args5]
        data_fields = [
            ("ExerciseDates", "date"),
            ("Strikes", "float"),
        ]
        kv1 = [
            ("Coupon", "float"),
            ("Frequency", "const"),
            ("ValuationDate", "date"),
            ("MaturityDate", "date"),
            ("BondOptionType", "const"),
            ("IsEmbedded", "bool"),
            ("Redemption", "float"),
            ("Strikes", "plainlist"),
            ("ExerciseDates", "plainlist"),
            ("BDTData", "mcphandler"),
            ("ShortRate", "float"),
            ("ShortVol", "float"),
            ("MinimumLocalVol", "float"),
            ("WeightOnYieldCurve", "float"),
            ("SpreadOnYieldCurve", "float"),
            ("LatticePoints", "int"),
            ("DayCounter", "const"),
        ]
        kv2 = [
            ("Coupon", "float"),
            ("Frequency", "const"),
            ("ValuationDate", "date"),
            ("MaturityDate", "date"),
            ("BondOptionType", "const"),
            ("IsEmbedded", "bool"),
            ("Redemption", "float"),
            ("Strikes", "plainlist"),
            ("ExerciseDates", "plainlist"),
            ("BondCurve", "mcphandler"),
            ("MinimumLocalVol", "float"),
            ("WeightOnYieldCurve", "float"),
            ("SpreadOnYieldCurve", "float"),
            ("LatticePoints", "int"),
            ("DayCounter", "const"),
            ("HistVolModel", "const"),
            ("HistVolReturnMethod", "const"),
            ("HistVolAnnualFactor", "float"),
            ("HistVolLamda", "float"),
            ("HistVolInterpolationMethod", "const"),
        ]
        result, lack_keys = mcp_kv_wrapper.valid_parse(method, args, fmt, data_fields, kv1, kv2)
        if len(lack_keys) > 0:
            return "Missing fields: " + str(lack_keys)
        vals = result["vals"]
        #print(method, "final args:")
        #print(vals)
        bond = mcp.MBDTTree(*vals)
        mcp_method_args_cache.cache(str(bond), result)
        return bond
    return None

    # data_fields = [
    #     ("ExerciseDates", "date"),
    #     ("Strikes", "float"),
    # ]
    # args = [args1, args2, args3, args4, args5]
    # args = mcp_kv_wrapper.std_all_args(args, fmt, data_fields)
    # result, lack_keys = mcp_kv_wrapper.parse_and_validate2(MethodName.McpBDTTree, args, [
    #     ("Coupon", "float"),
    #     ("Frequency", "const"),
    #     ("ValuationDate", "date"),
    #     ("MaturityDate", "date"),
    #     ("BondOptionType", "const"),
    #     ("IsEmbedded", "bool"),
    #     ("Redemption", "float"),
    #     ("Strikes", "plainlist"),
    #     ("ExerciseDates", "plainlist"),
    #     ("BDTData", "mcphandler"),
    #     ("ShortRate", "float"),
    #     ("ShortVol", "float"),
    #     ("MinimumLocalVol", "float"),
    #     ("WeightOnYieldCurve", "float"),
    #     ("SpreadOnYieldCurve", "float"),
    #     ("LatticePoints", "int"),
    #     ("DayCounter", "const"),
    # ])
    # if len(lack_keys) > 0:
    #     return "Missing fields: " + str(lack_keys)
    # vals = result["vals"]
    # print("McpBDTTree final args:")
    # print(vals)
    # vs = mcp.MBDTTree(*vals)
    # mcp_method_args_cache.cache(str(vs), result)
    # return vs


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bdt", "object")
def BdtBondPrice(bdt):
    if hasattr(bdt, 'Price'):
        return bdt.Price()
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bdt", "object")
def BdtOptionPrice(bdt):
    if hasattr(bdt, 'OptionPrice'):
        return bdt.OptionPrice()
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bdt", "object")
def BdtOptionFreePrice(bdt):
    if hasattr(bdt, 'OptionFreePrice'):
        return bdt.OptionFreePrice()
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtOptionOAS(bdt, marketPrice, tolerance=0.000001, maxNumIterations=100):
    # print("BdtOptionOAS call")
    # val = bdt.OptionAdjustSpread(marketPrice, tolerance, maxNumIterations)
    # print("BdtOptionOAS call: val=", val)
    # return val

    # return bdt.OptionAdjustSpread(marketPrice, tolerance, maxNumIterations)
    # print("BdtOptionOAS call")

    def async_callback():
        print("BdtOptionOAS async_callback")
        val = bdt.OptionAdjustSpread(marketPrice, tolerance, maxNumIterations)
        print("BdtOptionOAS async_callback: val=", val)
        return val
        # rtd.value = val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None
    # return ThreadFuncRtd(async_callback)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtDiscountSpread(bdt, marketPrice, tolerance=0.000001, maxNumIterations=100):
    # return bdt.BinaryTreeDiscountSpread(marketPrice, tolerance, maxNumIterations)
    print("BdtDiscountSpread call")

    def async_callback():
        print("BdtDiscountSpread async_callback")
        val = bdt.BinaryTreeDiscountSpread(marketPrice, tolerance, maxNumIterations)
        print("BdtDiscountSpread async_callback: val=", val)
        return val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("delta", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtOasDuration(bdt, marketPrice, delta=0.0001, tolerance=0.000001, maxNumIterations=100):
    # print("Bdt Oas Duration call")
    # val = bdt.Duration(marketPrice, delta, tolerance, maxNumIterations)
    # print("Bdt Oas Duration end")
    # return val
    print("BdtOasDuration call")

    def async_callback():
        print("BdtOasDuration async_callback")
        val = bdt.Duration(marketPrice, delta, tolerance, maxNumIterations)
        print("BdtOasDuration async_callback: val=", val)
        return val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("delta", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtOasConvexity(bdt, marketPrice, delta=0.0001, tolerance=0.000001, maxNumIterations=100):
    # return bdt.Convexity(marketPrice, delta, tolerance, maxNumIterations)
    # print("BdtOasConvexity call")
    #
    def async_callback():
        val = bdt.Convexity(marketPrice, delta, tolerance, maxNumIterations)
        print("BdtOasConvexity async_callback: val=", val)
        return val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("delta", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtOasPVBP(bdt, marketPrice, delta=0.0001, tolerance=0.000001, maxNumIterations=100):
    # return bdt.PVBP(marketPrice, delta, tolerance, maxNumIterations)
    # print("BdtOasPVBP call")
    #
    def async_callback():
        val = bdt.PVBP(marketPrice, delta, tolerance, maxNumIterations)
        print("BdtOasPVBP async_callback: val=", val)
        return val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("bdt", "object")
@xl_arg("marketPrice", "float")
@xl_arg("delta", "float")
@xl_arg("faceValue", "float")
@xl_arg("tolerance", "float")
@xl_arg("maxNumIterations", "int")
@xl_return("rtd")
def BdtOasDV01(bdt, marketPrice, delta=0.0001, faceValue=100, tolerance=0.000001, maxNumIterations=100):
    # return bdt.DV01(marketPrice, delta, faceValue, tolerance, maxNumIterations)
    # print("BdtOasDV01 call")
    #
    def async_callback():
        val = bdt.DV01(marketPrice, delta, faceValue, tolerance, maxNumIterations)
        print("BdtOasDV01 async_callback: val=", val)
        return val

    if async_func_manager:
        return async_func_manager.create(async_callback)
    return None

@xl_func(macro=False,recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpFixedRateBond(args1, args2, args3, args4, args5, fmt='VP'):
    if tool_def:
        args=[args1, args2, args3, args4, args5, fmt]
        try:
            return tool_def.xls_create(*args, key='McpFixedRateBond')
        except Exception as e:
            s = f"McpFixedRateBond except: {e}"
            logging.warning(args)
            logging.warning(s, exc_info=True)
            return s
    return None




@xl_func(macro=False,recalc_on_open=True,auto_resize=True)
def FrbKeyRateDuration(bond,curve,tenors,adjustWithEffectiveDuration,fmt='V'):
    if tool_def:
        args=[bond,curve,tenors,adjustWithEffectiveDuration,fmt]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='KeyRateDuration')
        except Exception as e:
            s = f"FrbKeyRateDuration except: {e}"
            logging.warning(args)
            logging.warning(s, exc_info=True)
            return s
    return None
