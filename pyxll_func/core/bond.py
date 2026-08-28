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
from datetime import date
import json
import logging
from typing import Any, Dict, List, Optional, Union

from mcp.optional_deps import pandas as pd

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

def _frb_bond_acct_call(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                          quantity, dailyAccrual, realizedPnl, method):
    if tool_def:
        args = [bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                quantity, dailyAccrual, realizedPnl]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method=method)
        except Exception as e:
            s = f"{method} except: {e}"
            logging.warning(s, exc_info=True)
            return s
    return None

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("classification", "str")
@xl_arg("prevDate", "datetime")
@xl_arg("currDate", "datetime")
@xl_arg("initCost", "float")
@xl_arg("prevClean", "float")
@xl_arg("currClean", "float")
@xl_arg("quantity", "float")
@xl_arg("dailyAccrual", "float")
@xl_arg("realizedPnl", "float")
def FrbBondAcctPandl(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                     quantity, dailyAccrual, realizedPnl):
    return _frb_bond_acct_call(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                               quantity, dailyAccrual, realizedPnl, 'BondAcctPandlImpact')

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("classification", "str")
@xl_arg("prevDate", "datetime")
@xl_arg("currDate", "datetime")
@xl_arg("initCost", "float")
@xl_arg("prevClean", "float")
@xl_arg("currClean", "float")
@xl_arg("quantity", "float")
@xl_arg("dailyAccrual", "float")
@xl_arg("realizedPnl", "float")
def FrbBondAcctOci(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                    quantity, dailyAccrual, realizedPnl):
    return _frb_bond_acct_call(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                               quantity, dailyAccrual, realizedPnl, 'BondAcctOciImpact')

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("classification", "str")
@xl_arg("prevDate", "datetime")
@xl_arg("currDate", "datetime")
@xl_arg("initCost", "float")
@xl_arg("prevClean", "float")
@xl_arg("currClean", "float")
@xl_arg("quantity", "float")
@xl_arg("dailyAccrual", "float")
@xl_arg("realizedPnl", "float")
def FrbBondAcctPnl(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                   quantity, dailyAccrual, realizedPnl):
    return _frb_bond_acct_call(bond, classification, prevDate, currDate, initCost, prevClean, currClean,
                               quantity, dailyAccrual, realizedPnl, 'BondAcctAccountingPnl')

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("bond", "object")
@xl_arg("prevDate", "datetime")
@xl_arg("currDate", "datetime")
@xl_arg("initCost", "float")
def FrbBondAcctAmCost(bond, prevDate, currDate, initCost):
    if tool_def:
        args = [bond, prevDate, currDate, initCost]
        try:
            return tool_def.xls_call(*args, key='McpFixedRateBond', method='BondAcctAmCost')
        except Exception as e:
            s = f"FrbBondAcctAmCost except: {e}"
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

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpABSTranche(args1, args2, args3, args4, args5, fmt='VP'):
    """
    创建 ABS 档位对象（资产支持证券）
    参数：UnderlyingBond(MFixedRateBond), TrancheType(PRIORITY/SUBORDINATED/PRIVATE_PLACEMENT),
    ABSMarket(INTERBANK/EXCHANGE_SZSE/EXCHANGE_SSE), SettlementDate, FaceValue, Currency, 等
    优先档/私募档可用 FrbPrice、FrbDirtyPrice 等；次级档用 FrbAbsPrice（蒙特卡洛）
    """
    if tool_def:
        args = [args1, args2, args3, args4, args5, fmt]
        try:
            return tool_def.xls_create(*args, key='McpABSTranche')
        except Exception as e:
            s = f"McpABSTranche except: {e}"
            logging.warning(args)
            logging.warning(s, exc_info=True)
            return s
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


# ========== LoanAndDepos (Lnd) ==========

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpLoanAndDepos(args1, args2, args3, args4, args5, fmt='VP'):
    """Create LoanAndDepos object (loan/deposit, fixed or floating rate)"""
    if tool_def:
        args = [args1, args2, args3, args4, args5, fmt]
        try:
            return tool_def.xls_create(*args, key='McpLoanAndDepos')
        except Exception as e:
            s = f"McpLoanAndDepos except: {e}"
            logging.warning(args)
            logging.warning(s, exc_info=True)
            return s
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("lnd", "object")
@xl_arg("estimatingCurve", "object")
@xl_arg("discountingCurve", "object")
def LndNPV(lnd, estimatingCurve, discountingCurve):
    """LoanAndDepos NPV (fair value)"""
    if hasattr(lnd, 'NPV'):
        return lnd.NPV(estimatingCurve, discountingCurve)
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("lnd", "object")
@xl_arg("estimatingCurve", "object")
@xl_arg("discountingCurve", "object")
def LndPrice(lnd, estimatingCurve, discountingCurve):
    """LoanAndDepos Price (same as NPV)"""
    if hasattr(lnd, 'Price'):
        return lnd.Price(estimatingCurve, discountingCurve)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("lnd", "object")
def LndNotional(lnd):
    """LoanAndDepos notional amount"""
    if hasattr(lnd, 'Notional'):
        return lnd.Notional()
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("lnd", "object")
def LndEndDate(lnd):
    """LoanAndDepos end/maturity date"""
    if hasattr(lnd, 'EndDate'):
        s = lnd.EndDate()
        if s:
            return pd.to_datetime(s)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("lnd", "object")
def LndPreviousCouponDate(lnd):
    """LoanAndDepos previous coupon date"""
    if hasattr(lnd, 'GetPreviousCouponDate'):
        s = lnd.GetPreviousCouponDate()
        if s:
            return pd.to_datetime(s)
    return None


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("lnd", "object")
def LndNextCouponDate(lnd):
    """LoanAndDepos next coupon date"""
    if hasattr(lnd, 'GetNextCouponDate'):
        s = lnd.GetNextCouponDate()
        if s:
            return pd.to_datetime(s)
    return None


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("lnd", "object")
@xl_arg("estimatingCurve", "object")
@xl_arg("discountingCurve", "object")
@xl_return("var[][]")
def LndCashflows(lnd, estimatingCurve, discountingCurve):
    """LoanAndDepos cashflows - 返回 list 格式 (表头+数据行)，参考 FrbKeyRateDuration 的 auto_resize 返回格式"""
    if hasattr(lnd, 'Cashflows'):
        s = lnd.Cashflows(estimatingCurve, discountingCurve)
        if s:
            try:
                flows = json.loads(s)
                if not flows:
                    return None
                # 第一行可能是 header (CashFlows, CCY_FIXED)，数据行从 index 1 开始
                # 用第一个数据行的 keys 作为列头，转为 2D 数组供 Excel 显示
                data_rows = [f for f in flows if isinstance(f, dict) and "Payment" in f]
                if not data_rows:
                    return flows  # 无法解析时返回原始 list
                headers = list(data_rows[0].keys())
                result = [headers] + [[row.get(h) for h in headers] for row in data_rows]
                return result
            except json.JSONDecodeError:
                return [[s]]
    return None


# ==================== TRS (Total Return Swap) 总收益互换 ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("price", "float")
def TrsSetCurrentPrice(trs, price):
    """设置 TRS 当前标的价格（估值前必须调用）"""
    if hasattr(trs, 'setCurrentPrice'):
        trs.setCurrentPrice(price)
        return True
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("discountCurve", "object")
@xl_arg("fundingCurve", "object")
def TrsPrice(trs, discountCurve, fundingCurve):
    """TRS 估值：需先调用 TrsSetCurrentPrice 设置标的价格"""
    if hasattr(trs, 'Price'):
        try:
            # MSwapCurve/MBondCurve 不继承 MYieldCurve，SWIG void* 重载会导致
            # C++ 中非法 static_cast 造成崩溃，需先提取底层 mcp::*Curve* 指针
            disc_arg = discountCurve.getHandler() if hasattr(discountCurve, 'getHandler') else discountCurve
            fund_arg = fundingCurve.getHandler() if hasattr(fundingCurve, 'getHandler') else fundingCurve
            return trs.Price(disc_arg, fund_arg)
        except Exception as e:
            return f"#TRS: {e}"
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def TrsAdapterNPV(adapter):
    """TRS Adapter 估值（NPV），需已设置 DiscountCurve、FundingCurve、UnderlyingPrice"""
    if adapter is None:
        return "#TRS: adapter 为空"
    if isinstance(adapter, str) and ('except' in adapter or 'Missing' in adapter or 'vector too long' in adapter):
        return f"#TRS: adapter 创建失败，请检查 McpTRSAdapter 参数区域是否包含 TotalReturnSwap、DiscountCurve、FundingCurve、UnderlyingPrice"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#TRS: 无效的 adapter 对象"
    try:
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
            return "#TRS: 无结果(value 为空)"
        return "#TRS: 无结果。请确保 McpTRSAdapter 已设置 DiscountCurve、FundingCurve、UnderlyingPrice"
    except RuntimeError as e:
        err = str(e).lower()
        if 'bad allocation' in err or 'allocation' in err:
            return "#TRS: 估值失败(bad allocation)。请确保：1) 已设置 DiscountCurve、FundingCurve、UnderlyingPrice；2) 曲线与 TRS 在同一工作簿且未被删除；3) 日期格式正确(YYYY-MM-DD)"
        if 'vector too long' in err:
            return "#TRS: 估值失败(vector too long)"
        return f"#TRS: {e}"
    except Exception as e:
        return f"#TRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def TRSAdapterPV(adapter):
    """TRS Adapter 现值（PV）

    从 McpTRSAdapter 的估值指标中提取 PV 指标值。
    需已通过 McpTRSAdapter 设置 DiscountCurve、FundingCurve 和 UnderlyingPrice。

    参数:
        adapter: McpTRSAdapter 对象

    返回:
        PV 数值（本币），或错误信息
    """
    if adapter is None:
        return "#TRS: adapter 为空"
    if isinstance(adapter, str):
        return f"#TRS: adapter 创建失败 → {adapter}"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#TRS: 无效的 adapter 对象"
    try:
        val = adapter.calculateValuationMetrics()
        for m in (val or []):
            nm = getattr(m, 'metric_name', None) or ''
            if str(nm) == 'PV':
                return float(getattr(m, 'value', 0))
        # 兜底：取第一个指标（通常也是 PV/NPV）
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#TRS: 无 PV 结果。请确保 McpTRSAdapter 已设置 DiscountCurve、FundingCurve、UnderlyingPrice"
    except Exception as e:
        return f"#TRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def TRSAdapterImpliedPrice(adapter):
    """TRS Adapter 隐含价格（IMPLIED_PRICE = PV / 名义本金）

    从 McpTRSAdapter 的估值指标中提取 IMPLIED_PRICE 指标值。
    IMPLIED_PRICE = PV / Notional，为每单位名义本金的净盈亏比率（无量纲）。
    需已通过 McpTRSAdapter 设置 DiscountCurve、FundingCurve 和 UnderlyingPrice。

    参数:
        adapter: McpTRSAdapter 对象

    返回:
        隐含价格比率（PV / Notional），或错误信息
    """
    if adapter is None:
        return "#TRS: adapter 为空"
    if isinstance(adapter, str):
        return f"#TRS: adapter 创建失败 → {adapter}"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#TRS: 无效的 adapter 对象"
    try:
        val = adapter.calculateValuationMetrics()
        for m in (val or []):
            nm = getattr(m, 'metric_name', None) or ''
            if str(nm) == 'IMPLIED_PRICE':
                return float(getattr(m, 'value', 0))
        return "#TRS: 无 IMPLIED_PRICE 结果。请确认 mcp 模块已重新编译（新增 IMPLIED_PRICE 指标）"
    except Exception as e:
        return f"#TRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("discountCurve", "object")
@xl_arg("fundingCurve", "object")
def TrsImpliedPrice(trs, discountCurve, fundingCurve):
    """TRS 隐含价格 = PV / 名义本金（股票/权益标的，无量纲比率）

    参数:
        trs:           MTotalReturnSwap 对象（需先调用 TrsSetCurrentPrice 注入当前价格）
        discountCurve: 折现曲线（MYieldCurve 对象）
        fundingCurve:  资金曲线（MYieldCurve 对象）

    返回:
        隐含价格比率（PV / Notional），如 0.002 表示每单位本金盈亏 0.2%
    """
    if trs is None:
        return "#TRS: trs 对象为空"
    if discountCurve is None:
        return "#TRS: discountCurve 为空"
    if fundingCurve is None:
        return "#TRS: fundingCurve 为空"
    if not hasattr(trs, 'getImpliedPrice'):
        return "#TRS: 对象不支持 getImpliedPrice，请重新编译 mcp 模块"
    try:
        disc_arg = discountCurve.getHandler() if hasattr(discountCurve, 'getHandler') else discountCurve
        fund_arg = fundingCurve.getHandler() if hasattr(fundingCurve, 'getHandler') else fundingCurve
        return trs.getImpliedPrice(disc_arg, fund_arg)
    except Exception as e:
        return f"#TRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("discountCurve", "object")
@xl_arg("fundingCurve", "object")
def TrsMarketParRate(trs, discountCurve=None, fundingCurve=None):
    """TRS 市场 par 固定融资费率：让本 TRS 当前 PV=0 的固定融资费率。

    参数:
        trs:           McpTRSAdapter 或 MTotalReturnSwap 对象。
                       - McpTRSAdapter：无需额外传曲线，adapter 内已注入；当前价格也自动同步。
                       - MTotalReturnSwap：需先调用 TrsSetCurrentPrice，并显式传入曲线。
        discountCurve: 折现曲线（可选；传入 McpTRSAdapter 时可省略，使用 adapter 内部曲线）
        fundingCurve:  资金曲线（可选；同上）

    返回:
        小数形式的 par 融资费率，例如 0.052 表示 5.2%。
        与 VanillaSwap.MarketParRate 同口径：不带 direction，是投资人「今天再签同样合约」的市场报价。
    """
    if trs is None:
        return "#TRS: trs 对象为空"
    is_adapter = hasattr(trs, '_trs_ref') or hasattr(trs, 'calculateValuationMetrics')
    if not is_adapter and discountCurve is None:
        return "#TRS: discountCurve 为空（传入 raw TRS 时必须提供折现曲线）"
    if not hasattr(trs, 'MarketParRate'):
        return "#TRS: 对象不支持 MarketParRate，请重新编译 mcp 模块"
    try:
        disc_arg = discountCurve.getHandler() if hasattr(discountCurve, 'getHandler') else discountCurve
        fund_arg = fundingCurve.getHandler() if hasattr(fundingCurve, 'getHandler') else fundingCurve
        return trs.MarketParRate(disc_arg, fund_arg)
    except Exception as e:
        return f"#TRS: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def TrsAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """TRS Adapter 现金流：参考 XCcySwapFloatingLegs，返回表头+数据行供 Excel 平铺。

    不使用 volatile：volatile 会在每次全表重算时强制重算，修改到期日等易触发 Excel 长时间卡死。
    请在公式中用 +0*ROW(曲线单元格) 等方式建立对曲线/注入单元格的依赖，保证计算顺序。"""
    if adapter is None:
        return [["#TRS: adapter 为空"]]
    if isinstance(adapter, str) and ('except' in adapter or 'Missing' in adapter or 'vector too long' in adapter):
        return [["#TRS: adapter 创建失败，请检查 McpTRSAdapter 参数区域"]]
    if not hasattr(adapter, 'calculateCashflows'):
        return [["#TRS: 无效的 adapter 对象"]]
    try:
        dc = getattr(adapter, "_discount_curve_ref", None)
        fc = getattr(adapter, "_funding_curve_ref", None)
        if dc is not None and hasattr(adapter, "setDiscountCurve"):
            adapter.setDiscountCurve(dc)
        if fc is not None and hasattr(adapter, "setFundingCurve"):
            adapter.setFundingCurve(fc)
        useYieldCurve = True
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            try:
                rows = []
                for leg_idx, leg in enumerate(flows):
                    leg_items = list(leg) if not isinstance(leg, list) else leg
                    for cf in leg_items:
                        if hasattr(cf, 'payment_date'):
                            po = {
                                "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                                "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                                "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                                "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                                "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                                "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                            }
                            rows.append(po)
                        elif isinstance(cf, dict):
                            rows.append(cf)
                if rows:
                    # 与 XCcySwapFloatingLegs 一致：fields 指定列，无 fields 时全部显示
                    _field_alias = {
                        "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                        "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                    }
                    default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                    # 展平 Excel 传入的 2D range（如 D1:I1）
                    def _flatten_fields(f):
                        if not f:
                            return []
                        if isinstance(f, (list, tuple)) and len(f) > 0:
                            first = f[0]
                            if isinstance(first, (list, tuple)):
                                return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                            return [str(x) for x in f if x]
                        return []
                    out_fields = _flatten_fields(fields) if fields else default_fields
                    if not out_fields:
                        out_fields = default_fields

                    def _parse_yyyymmdd(s):
                        if not s:
                            return None
                        s = str(s).strip().replace("-", "/")[:10]
                        parts = s.split("/")
                        if len(parts) != 3:
                            return None
                        try:
                            return (int(parts[0]), int(parts[1]), int(parts[2]))
                        except ValueError:
                            return None

                    expired_note = None
                    try:
                        all_df_1 = all(
                            abs(float(r.get("DiscountFactor", 0) or 0) - 1.0) < 1e-9
                            for r in rows
                        )
                        curve_not_flat = False
                        if dc is not None and hasattr(dc, "DiscountFactor"):
                            try:
                                _p = float(dc.DiscountFactor("2026/04/11", "2027/04/11"))
                                curve_not_flat = abs(_p - 1.0) > 1e-5
                            except TypeError:
                                _p = float(dc.DiscountFactor("2027/04/11"))
                                curve_not_flat = abs(_p - 1.0) > 1e-5
                            except Exception:
                                curve_not_flat = False
                        m_t = _parse_yyyymmdd(
                            adapter.getMaturityDate() if hasattr(adapter, "getMaturityDate") else None
                        )
                        r_t = _parse_yyyymmdd(
                            dc.GetReferenceDate() if (dc is not None and hasattr(dc, "GetReferenceDate")) else None
                        )
                        if all_df_1 and curve_not_flat and m_t and r_t and r_t > m_t:
                            expired_note = (
                                "提示：折现曲线基准日晚于合约到期日，现金流均已发生；"
                                "YieldCurve 对 t<=0 的 DF 恒为 1，故 DiscountFactor 全为 1、PresentValue=Amount。"
                                "与仍存续的 TRS（如 Trade1）不同属正常。"
                            )
                    except Exception:
                        pass

                    result = []
                    if expired_note:
                        note_row = ["NOTE", expired_note] + [""] * (len(out_fields) - 1)
                        result.append(note_row)
                    # 标题行
                    result.append(["#"] + list(out_fields))
                    for i, row in enumerate(rows, start=1):
                        obj = [f"Period{i}"]
                        for field in out_fields:
                            key = _field_alias.get(field, field)
                            v = row.get(key, "")
                            obj.append(v if v is not None else "")
                        result.append(obj)
                    return result
                return [["#TRS: 无现金流数据"]]
            except (TypeError, AttributeError) as te:
                return [[f"#TRS: 现金流解析失败: {te}"]]
    except RuntimeError as e:
        err = str(e).lower()
        if 'bad allocation' in err or 'allocation' in err:
            return [["#TRS: 现金流计算失败(bad allocation)。请确保：1) 已设置 DiscountCurve、FundingCurve、UnderlyingPrice；2) 曲线与 TRS 在同一工作簿且未被删除；3) 日期格式正确(YYYY-MM-DD)"]]
        if 'vector too long' in err:
            return [["#TRS: 现金流结果过长，无法输出到 Excel"]]
        return [[f"#TRS: {e}"]]
    except Exception as e:
        return [[f"#TRS: {e}"]]
    return [["#TRS: 无现金流数据"]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("legType", "str")
@xl_arg("fixedRate", "float")
def TrsSetFundingLegType(trs, legType, fixedRate=0.0):
    """设置 TRS 资金腿类型：legType='FIXED' 或 'FLOATING'（默认），fixedRate 为小数（如 0.052 表示 5.2%）"""
    if trs is None:
        return "#TRS: trs 为空"
    try:
        leg_int = 1 if str(legType).strip().upper() == "FIXED" else 0
        if hasattr(trs, 'setFundingLegType'):
            trs.setFundingLegType(leg_int, float(fixedRate))
            return f"OK: FundingLegType={legType}, Rate={fixedRate}"
        return "#TRS: 对象不支持 setFundingLegType"
    except Exception as e:
        return f"#TRS: {e}"


def McpBondTRS(bondIsin, faceValue, currency, startDate, maturityDate,
               initialClean, couponRate, couponStartDate, fixedFundingRate,
               couponFrequency="SEMIANNUAL", direction=1, initialAccrued=0.0):
    """创建债券 TRS 对象（BondTotalReturnSwap）

    所有比例字段均以小数输入，与 C++ ctor 完全一致：
        initialClean=0.977879   表示 97.7879%（净价 / 面值）
        initialAccrued=0.031452 表示  3.1452%（应计 / 面值）
        couponRate=0.07         表示 7%
        fixedFundingRate=0.032  表示 3.2%
    couponFrequency 取字符串（"SEMIANNUAL" 等）或 enum int（1=ANNUAL, 2=SEMI, 4=Q, 12=M）。
    """
    try:
        import mcp
        from mcp.utils.excel_utils import pf_date
        start = pf_date(startDate)
        end = pf_date(maturityDate)
        cpStart = pf_date(couponStartDate)
        cal = mcp.McpCalendar("", "", "")
        return mcp.McpBondTRS(
            bondIsin=bondIsin,
            faceValue=faceValue,
            currency=currency,
            startDate=start,
            maturityDate=end,
            initialCleanPrice=float(initialClean),
            initialAccrued=float(initialAccrued),
            couponRate=float(couponRate),
            couponFrequency=couponFrequency,
            couponStartDate=cpStart,
            dayCounter=int(mcp.DayCounter.Act365Fixed),
            fixedFundingRate=float(fixedFundingRate),
            direction=int(direction),
            paymentCalendar=cal,
        )
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("curve", "object")
def BondTrsSetDiscountCurve(adapter, curve):
    """设置 McpBondTRSAdapter 的折现曲线（用于 NPV 及现金流折现）
    
    参数:
        adapter: McpBondTRSAdapter 对象
        curve:   折现曲线（McpYieldCurve / McpBondCurve / McpSwapCurve 对象）
    
    返回:
        "OK" 或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    if curve is None:
        return "#BondTRS: curve 为空"
    try:
        if hasattr(adapter, 'setDiscountCurve'):
            adapter.setDiscountCurve(curve)
            setattr(adapter, "_mcp_bond_trs_discount_curve", curve)
            return "OK"
        return "#BondTRS: adapter 不支持 setDiscountCurve"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("curve", "object")
def BondTrsSetFundingCurve(adapter, curve):
    """设置 McpBondTRSAdapter 的资金腿折现曲线（未设置时默认与 DiscountCurve 相同）
    
    参数:
        adapter: McpBondTRSAdapter 对象
        curve:   资金腿曲线（McpYieldCurve / McpSwapCurve 等）
    
    返回:
        "OK" 或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    if curve is None:
        return "#BondTRS: curve 为空"
    try:
        if hasattr(adapter, 'setFundingCurve'):
            adapter.setFundingCurve(curve)
            return "OK"
        return "#BondTRS: adapter 不支持 setFundingCurve"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("currentCleanPrice", "float")
def BondTrsSetCurrentPrice(adapter, currentCleanPrice):
    """设置 McpBondTRSAdapter 的当前净价（小数，如 0.985 表示面值的 98.5%）

    参数:
        adapter:           McpBondTRSAdapter 对象
        currentCleanPrice: 当前净价（小数；与 InitialCleanPrice 单位一致）

    返回:
        "OK" 或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    try:
        if hasattr(adapter, 'setCurrentCleanPrice'):
            adapter.setCurrentCleanPrice(float(currentCleanPrice))
            setattr(adapter, "_mcp_bond_trs_current_clean", float(currentCleanPrice))
            return f"OK: CurrentCleanPrice={currentCleanPrice}"
        return "#BondTRS: adapter 不支持 setCurrentCleanPrice"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
@xl_arg("valuationDate", "date")
def BondTrsSetValuationDate(adapter, valuationDate):
    """设置 McpBondTRSAdapter 的估值日

    估值日影响：(1) 只剩余票息计入；(2) 累计利息按估值日重算。
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    try:
        from mcp.utils.excel_utils import pf_date
        d = pf_date(valuationDate)
        if hasattr(adapter, 'setValuationDate'):
            adapter.setValuationDate(d)
            setattr(adapter, "_mcp_bond_trs_valuation_date", d)
            return f"OK: ValuationDate={d}"
        return "#BondTRS: adapter 不支持 setValuationDate"
    except Exception as e:
        return f"#BondTRS: {e}"


def _bond_trs_sync_adapter(adapter):
    """将 adapter 上存储的市场数据属性同步到 C++ 层（每次估值前调用）。

    McpBondTRSAdapter 创建时若已嵌入 DiscountCurve/CurrentPrice/ValuationDate，
    该函数确保它们在 C++ BondTRSAdapter 里生效（以防对象重建后状态丢失）。
    """
    c = getattr(adapter, '_mcp_bond_trs_discount_curve', None)
    if c is not None and hasattr(adapter, 'setDiscountCurve'):
        adapter.setDiscountCurve(c)
    cp = getattr(adapter, '_mcp_bond_trs_current_clean', None)
    if cp is not None and hasattr(adapter, 'setCurrentCleanPrice'):
        adapter.setCurrentCleanPrice(float(cp))
    vd = getattr(adapter, '_mcp_bond_trs_valuation_date', None)
    if vd is not None and hasattr(adapter, 'setValuationDate'):
        adapter.setValuationDate(vd)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BondTrsNPV(adapter):
    """债券 TRS Adapter 净现值 (NPV)

    参数:
        adapter: McpBondTRSAdapter 对象。
                 若在 McpBondTRSAdapter 参数块中已填写 DiscountCurve / CurrentPrice /
                 ValuationDate，无需额外调用 BondTrsSetXxx，Excel 会自动联动更新。

    返回:
        NPV 数值（本币），或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    if isinstance(adapter, str):
        return f"#BondTRS: adapter 创建失败 → {adapter}"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#BondTRS: 无效的 adapter 对象"
    try:
        _bond_trs_sync_adapter(adapter)
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BondTRS: 无估值结果（请检查 DiscountCurve / CurrentPrice 是否已填入参数块）"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BondTRSAdapterPV(adapter):
    """债券 TRS Adapter 现值（PV）

    从 McpBondTRSAdapter 的估值指标中提取 PV 指标值。
    需已通过 BondTrsSetDiscountCurve 设置折现曲线。

    参数:
        adapter: McpBondTRSAdapter 对象

    返回:
        PV 数值（本币），或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    if isinstance(adapter, str):
        return f"#BondTRS: adapter 创建失败 → {adapter}"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#BondTRS: 无效的 adapter 对象"
    try:
        _bond_trs_sync_adapter(adapter)
        val = adapter.calculateValuationMetrics()
        for m in (val or []):
            nm = getattr(m, 'metric_name', None) or ''
            if str(nm) == 'PV':
                return float(getattr(m, 'value', 0))
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BondTRS: 无 PV 结果（请检查 DiscountCurve / CurrentPrice 是否已填入参数块）"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BondTRSAdapterImpliedPrice(adapter):
    """债券 TRS Adapter 隐含价格（IMPLIED_PRICE = PV / 面值 × 100）

    从 McpBondTRSAdapter 的估值指标中提取 IMPLIED_PRICE 指标值。
    IMPLIED_PRICE = PV / FaceValue × 100，为百元净价口径，与债券市场报价一致。
    需已通过 BondTrsSetDiscountCurve 设置折现曲线。

    注意：IMPLIED_PRICE 反映 TRS 合约本身 NPV 与面值之比，
          不同于 MARKET_PRICE（标的债券市场全价）。

    参数:
        adapter: McpBondTRSAdapter 对象

    返回:
        每百元面值的隐含价格点数，或错误信息
    """
    if adapter is None:
        return "#BondTRS: adapter 为空"
    if isinstance(adapter, str):
        return f"#BondTRS: adapter 创建失败 → {adapter}"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return "#BondTRS: 无效的 adapter 对象"
    try:
        val = adapter.calculateValuationMetrics()
        for m in (val or []):
            nm = getattr(m, 'metric_name', None) or ''
            if str(nm) == 'IMPLIED_PRICE':
                return float(getattr(m, 'value', 0))
        return "#BondTRS: 无 IMPLIED_PRICE 结果。请确认 mcp 模块已重新编译（新增 IMPLIED_PRICE 指标）"
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("discountCurve", "object")
def BondTrsImpliedPrice(trs, discountCurve):
    """债券 TRS 隐含价格 = PV / 面值 × 100（百元净价口径，与债券市场报价一致）

    参数:
        trs:           MBondTRS 对象（需先调用 BondTrsSetCurrentPrice、BondTrsSetValuationDate）
        discountCurve: 折现曲线（MYieldCurve 对象）

    返回:
        每百元面值的隐含价格点数，如 0.23 表示每百元面值盈亏 0.23 元
        注：此值反映 TRS 合约本身 NPV 与面值之比，不同于债券市场全价（MARKET_PRICE）
    """
    if trs is None:
        return "#BondTRS: trs 对象为空"
    if discountCurve is None:
        return "#BondTRS: discountCurve 为空"
    if not hasattr(trs, 'getImpliedPrice'):
        return "#BondTRS: 对象不支持 getImpliedPrice，请重新编译 mcp 模块"
    try:
        disc_arg = discountCurve.getHandler() if hasattr(discountCurve, 'getHandler') else discountCurve
        return trs.getImpliedPrice(disc_arg)
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("trs", "object")
@xl_arg("discountCurve", "object")
def BondTrsMarketParRate(trs, discountCurve=None):
    """债券 TRS 市场 par 固定融资费率：让本 Bond TRS 当前 PV=0 的固定融资费率。

    参数:
        trs:           McpBondTRSAdapter 或 MBondTRS 对象。
                       - McpBondTRSAdapter：已通过 BondTrsSetDiscountCurve 注入曲线时可省略 discountCurve；
                         当前净价（BondTrsSetCurrentPrice）和估值日（BondTrsSetValuationDate）也自动同步。
                       - MBondTRS：需先调用 BondTrsSetCurrentPrice / BondTrsSetValuationDate，
                         并显式传入 discountCurve。
        discountCurve: 折现曲线（可选；传入 McpBondTRSAdapter 时可省略）

    返回:
        小数形式的 par 融资费率，例如 0.032 表示 3.2%。
        含义：投资人在当前估值日、当前净价下，再签一笔同期限同标的同结构 TRS 的合理融资费率报价。
    """
    if trs is None:
        return "#BondTRS: trs 对象为空"
    is_adapter = hasattr(trs, '_bond_trs_ref') or hasattr(trs, 'calculateValuationMetrics')
    if not is_adapter and discountCurve is None:
        return "#BondTRS: discountCurve 为空（传入 raw MBondTRS 时必须提供折现曲线）"
    if not hasattr(trs, 'MarketParRate'):
        return "#BondTRS: 对象不支持 MarketParRate，请重新编译 mcp 模块"
    try:
        # McpBondCurve/McpSwapCurve 不继承 MYieldCurve，SWIG void* 重载会导致崩溃；
        # 用 getHandler() 提取底层 mcp::*Curve* 指针（继承自 mcp::YieldCurve，safe）
        disc_arg = discountCurve.getHandler() if hasattr(discountCurve, 'getHandler') else discountCurve
        return trs.MarketParRate(disc_arg)
    except Exception as e:
        return f"#BondTRS: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("discountCurve", "object")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BondTrsAdapterCashflows(adapter, useYieldCurve=True, discountCurve=None, fields=None):
    """债券 TRS Adapter 现金流：TOTAL_RETURN（CAPITAL+COUPON）+ FUNDING。

    参数:
        adapter:       McpBondTRSAdapter 对象
        useYieldCurve: 保留兼容参数，C++ 当前忽略该标志（传 TRUE 或省略均可）。
        discountCurve: 折现曲线（第 3 参数，强烈建议显式传入，避免 Excel 计算顺序导致 DF=1）。
                       传入后函数自动建立对曲线的 Excel 依赖，确保折现因子正确计算。
                       若省略，回退到 BondTrsSetDiscountCurve 注入的曲线。
        fields:        输出列名列表（可选）。

    用法示例：
        =BondTrsAdapterCashflows(B56)            — 仅 adapter，依赖 BondTrsSetDiscountCurve 顺序
        =BondTrsAdapterCashflows(B56, TRUE)      — 向后兼容旧公式，同上
        =BondTrsAdapterCashflows(B56, TRUE, B38) — 显式传入折现曲线（推荐），避免 DF=1"""
    if adapter is None:
        return [["#BondTRS: adapter 为空"]]
    if not hasattr(adapter, 'calculateCashflows'):
        return [["#BondTRS: 无效的 adapter 对象"]]
    try:
        # 若显式传入 discountCurve，先更新 adapter 上存储的曲线引用，再统一 sync
        if discountCurve is not None:
            setattr(adapter, '_mcp_bond_trs_discount_curve', discountCurve)
        _bond_trs_sync_adapter(adapter)
        # Excel 常把第二参显式成 FALSE；旧版 C++ 曾用 useYieldCurve 控制是否折现
        useYieldCurve = True
        flows = adapter.calculateCashflows(useYieldCurve)
        rows = []
        # 腿 0 = 总收益（CAPITAL + COUPON），腿 1 = FUNDING（与 C++ BondTRSAdapter::calculateCashflows 一致）
        leg_labels = ["TOTAL_RETURN", "FUNDING"]
        for leg_idx, leg in enumerate(flows):
            leg_name = leg_labels[leg_idx] if leg_idx < len(leg_labels) else f"LEG{leg_idx}"
            leg_items = list(leg) if not isinstance(leg, list) else leg
            for cf in leg_items:
                if hasattr(cf, 'payment_date'):
                    flow_type = (str(getattr(cf, 'flow_type', '')) or
                                 str(getattr(cf, 'leg_type', '')) or leg_name)
                    rows.append({
                        "Leg": leg_name,
                        "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                        "Amount": float(cf.amount) if hasattr(cf, 'amount') else 0.0,
                        "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                        "LegType": flow_type,
                        "DiscountFactor": float(getattr(cf, 'discount_factor', 0.0)) or 0.0,
                        "PresentValue": float(getattr(cf, 'present_value', 0.0)) or 0.0,
                    })
        if rows:
            default_fields = ["Leg", "PaymentDate", "Amount", "Currency", "LegType",
                              "DiscountFactor", "PresentValue"]
            if fields:
                flat_fields = [str(x) for row in (fields if isinstance(fields[0], (list, tuple)) else [fields])
                               for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                out_fields = flat_fields if flat_fields else default_fields
            else:
                out_fields = default_fields
            # 标题行
            result = [["#"] + list(out_fields)]
            for i, row in enumerate(rows, start=1):
                obj = [f"CF{i}"]
                for field in out_fields:
                    obj.append(row.get(field, ""))
                result.append(obj)
            return result
        return [["#BondTRS: 无现金流数据"]]
    except Exception as e:
        return [[f"#BondTRS: {e}"]]


# ========== CDS (Credit Default Swap) ==========

def _get_cds_adapter_obj(adapter):
    """McpCdsAdapter 包装时需用 getInstance() 获取内部 MCdsAdapter 再调用 C++ 方法，避免 crash"""
    if hasattr(adapter, 'getInstance'):
        return adapter.getInstance()
    return adapter


def _check_cds_adapter(adapter, prefix="#CDS"):
    if adapter is None:
        return f"{prefix}: adapter 为空"
    if isinstance(adapter, str):
        if any(x in adapter for x in ('except', 'Missing', 'Error', 'ObjectCacheKeyError', 'McpCdsAdapter')):
            return f"{prefix}: adapter 创建失败或对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"
    if not hasattr(adapter, 'calculateValuationMetrics'):
        return f"{prefix}: 无效的 adapter 对象"
    return None


def _check_cds_npv_ready(adapter):
    """预检查：NPV 可计算时 CDS 才有效，否则 calculateRiskMetrics/calculateCashflows 可能 crash"""
    try:
        obj = _get_cds_adapter_obj(adapter)
        obj.calculateValuationMetrics()
        return None
    except Exception as e:
        err_str = str(e)
        if "internal legs not initialized" in err_str.lower() or "legs not initialized" in err_str.lower():
            return "#CDS: CDS 内部 legs 未初始化。请检查 McpCreditDefaultSwap 参数：TradeDate/MaturityDate/ValuationDate 有效，ValuationDate <= MaturityDate，且 CDS 构造成功"
        return f"#CDS: {e}"


def _get_cds_metric_value(adapter, metric_name, from_valuation=True, from_attribution=False):
    """从 CdsAdapter 的 valuation、risk 或 attribution 指标中按名称查找并返回值"""
    obj = _get_cds_adapter_obj(adapter)
    if from_attribution:
        results = obj.calculateAttributionMetrics()
    else:
        results = obj.calculateValuationMetrics() if from_valuation else obj.calculateRiskMetrics()
    if not results:
        return None
    for m in results:
        name = getattr(m, 'metric_name', None) or getattr(m, 'description', '')
        if name and str(name) == metric_name:
            return float(getattr(m, 'value', 0))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterNPV(adapter):
    """
    CDS Adapter 估值（NPV），需已设置 CreditCurve、YieldCurve、Notional、Currency
    """
    try:
        # 尽早防御：adapter 为 None 或异常类型时直接返回
        if adapter is None:
            return "#CDS: adapter 为空"
        if isinstance(adapter, str):
            return f"#CDS: adapter 创建失败或对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"
        err = _check_cds_adapter(adapter)
        if err:
            return err
        obj = _get_cds_adapter_obj(adapter)
        val = obj.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
            return "#CDS: 无结果(value 为空)"
        return "#CDS: 无结果。请确保已设置 CreditCurve、YieldCurve、Notional、Currency"
    except BaseException as e:
        if 'ObjectCacheKeyError' in type(e).__name__ or 'ObjectCacheKey' in str(e):
            return "#CDS: adapter 对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"
        err_str = str(e).lower()
        if "internal legs not initialized" in err_str or "legs not initialized" in err_str:
            return "#CDS: CDS 内部 legs 未初始化。请检查 McpCreditDefaultSwap：TradeDate/MaturityDate/ValuationDate 为有效日期(YYYY-MM-DD)，ValuationDate<=MaturityDate"
        if "valuation date" in err_str and "maturity" in err_str:
            return "#CDS: ValuationDate 不能晚于 MaturityDate，请检查 McpCreditDefaultSwap 日期参数"
        return f"#CDS: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterCS01(adapter):
    """
    CDS Adapter 信用利差敏感度 (CS01)
    """
    try:
        if adapter is None:
            return "#CDS: adapter 为空"
        if isinstance(adapter, str):
            return "#CDS: adapter 创建失败或对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"
        err = _check_cds_adapter(adapter)
        if err:
            return err
        # 预检查：NPV 不可计算时 calculateRiskMetrics 会 crash
        npv_err = _check_cds_npv_ready(adapter)
        if npv_err:
            return npv_err
        obj = _get_cds_adapter_obj(adapter)
        val = obj.calculateRiskMetrics()
        if val:
            for m in val:
                if hasattr(m, 'metric_name') and str(m.metric_name) == 'CS01':
                    return float(getattr(m, 'value', 0))
        return "#CDS: 无 CS01 结果。请先确保 NPV 可计算：1) TradeDate/MaturityDate/ValuationDate 有效；2) ValuationDate <= MaturityDate；3) 已设置 CreditCurve、YieldCurve"
    except BaseException as e:
        if 'ObjectCacheKeyError' in type(e).__name__ or 'ObjectCacheKey' in str(e):
            return "#CDS: adapter 对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"
        return f"#CDS: {e}"


def _cds_metric_udf(adapter, metric_name, from_valuation=True, from_attribution=False):
    """通用 CDS 指标 UDF 实现"""
    if adapter is None:
        return f"#CDS: adapter 为空"
    if isinstance(adapter, str):
        return "#CDS: adapter 创建失败或对象缓存无效"
    err = _check_cds_adapter(adapter)
    if err:
        return err
    npv_err = _check_cds_npv_ready(adapter)
    if npv_err:
        return npv_err
    v = _get_cds_metric_value(adapter, metric_name, from_valuation, from_attribution)
    if v is not None:
        return float(v)
    if from_attribution and "ATTRIBUTION" in metric_name:
        return f"#CDS: 无 {metric_name} 结果。归因需在 McpCdsAdapter 中配置 PrevYieldCurve、PrevCreditCurve（T-1 曲线），并重建 mcp 使 MCdsAdapter 含 setPrevYieldCurve/setPrevCreditCurve"
    return f"#CDS: 无 {metric_name} 结果"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterRPV01(adapter):
    """CDS Adapter RPV01（保费端久期）"""
    return _cds_metric_udf(adapter, "RPV01", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterProtPV(adapter):
    """CDS Adapter PV Protection（保护端 PV）"""
    return _cds_metric_udf(adapter, "PV_PROTECTION", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterPremPV(adapter):
    """CDS Adapter PV Premium（保费端 PV）"""
    return _cds_metric_udf(adapter, "PV_PREMIUM", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterCleanMTM(adapter):
    """CDS Adapter Clean MTM"""
    return _cds_metric_udf(adapter, "CLEAN_MTM", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterDirtyMTM(adapter):
    """CDS Adapter Dirty MTM"""
    return _cds_metric_udf(adapter, "DIRTY_MTM", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterAccruedPremium(adapter):
    """CDS Adapter Accrued Premium"""
    return _cds_metric_udf(adapter, "ACCRUED_INTEREST", from_valuation=True)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def CdsAdapterAttribution(adapter, metric):
    """
    CDS Adapter 归因指标。metric 可选: Carry, Rates, Credit, Total, Residual
    """
    metric_map = {
        "Carry": "ATTRIBUTION_CARRY",
        "Rates": "ATTRIBUTION_RATES",
        "Credit": "ATTRIBUTION_CREDIT",
        "Total": "ATTRIBUTION_TOTAL",
        "Residual": "ATTRIBUTION_RESIDUAL",
    }
    mname = metric_map.get(str(metric).strip() if metric else "", "")
    if not mname:
        return "#CDS: metric 需为 Carry/Rates/Credit/Total/Residual 之一"
    return _cds_metric_udf(adapter, mname, from_valuation=False, from_attribution=True)


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "var")
@xl_return("var[][]")
def CdsAdapterAttributionAll(adapter):
    """CDS Adapter 全部归因指标，返回 2D 数组 [metric_name, value]"""
    try:
        if adapter is None:
            return [["#CDS: adapter 为空"]]
        err = _check_cds_adapter(adapter)
        if err:
            return [[err]]
        npv_err = _check_cds_npv_ready(adapter)
        if npv_err:
            return [[npv_err]]
        obj = _get_cds_adapter_obj(adapter)
        results = obj.calculateAttributionMetrics()
        if not results:
            return [["#CDS: 无归因结果"]]
        out = []
        for m in results:
            name = getattr(m, 'metric_name', None) or getattr(m, 'description', '') or ''
            val = float(getattr(m, 'value', 0))
            out.append([str(name), val])
        return out
    except BaseException as e:
        return [[f"#CDS: {e}"]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
@xl_arg("tenor", "str")
def CdsAdapterDV01Tenor(adapter, tenor):
    """CDS Adapter 按 tenor 的 DV01，tenor 如 0.5Y, 1Y, 3Y, 5Y, 10Y"""
    try:
        if adapter is None:
            return "#CDS: adapter 为空"
        err = _check_cds_adapter(adapter)
        if err:
            return err
        npv_err = _check_cds_npv_ready(adapter)
        if npv_err:
            return npv_err
        obj = _get_cds_adapter_obj(adapter)
        results = obj.calculateRiskMetrics()
        if not results:
            return "#CDS: 无风险指标"
        t = str(tenor).strip().upper() if tenor else ""
        if not t:
            return "#CDS: tenor 不能为空"
        for m in results:
            desc = getattr(m, 'description', '') or ''
            bucket = getattr(m, 'bucket_spec', None)
            bucket_tenor = bucket.tenor if bucket and hasattr(bucket, 'tenor') else ''
            if 'DV01' in desc and (t in desc or t in bucket_tenor):
                return float(getattr(m, 'value', 0))
        return f"#CDS: 无 DV01 {tenor}"
    except BaseException as e:
        return f"#CDS: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "var")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def CdsAdapterSchedule(adapter, fields=None):
    """
    CDS Adapter 支付计划表。fields 可选列: Period, PayDate, StartDate, EndDate, AccDays,
    AlphaFull, AlphaRem, DaysToPay, T_years, DF, Q, Q_prev, dQ, PremFactor, ProtFactor, FeeAmount
    """
    try:
        if adapter is None:
            return [["#CDS: adapter 为空"]]
        err = _check_cds_adapter(adapter)
        if err:
            return [[err]]
        npv_err = _check_cds_npv_ready(adapter)
        if npv_err:
            return [[npv_err]]
        obj = _get_cds_adapter_obj(adapter)
        if not hasattr(obj, 'calculateCdsSchedule'):
            return [["#CDS: adapter 不支持 calculateCdsSchedule"]]
        rows = obj.calculateCdsSchedule()
        if not rows:
            return [["#CDS: 无 Schedule 数据"]]
        default_fields = [
            "pay_date", "acc_start", "acc_end", "acc_days", "alpha_full", "alpha_rem",
            "days_to_pay", "t_years", "df", "Q", "Q_prev", "dQ", "prem_factor", "prot_factor", "fee_amount"
        ]
        out_fields = [str(f).strip().lower() for f in (fields or []) if f]
        if not out_fields:
            out_fields = default_fields
        result = [out_fields]
        for row in rows:
            r = []
            for f in out_fields:
                v = getattr(row, f, None)
                if v is None and hasattr(row, '_asdict'):
                    v = row._asdict().get(f)
                r.append(v if v is not None else "")
            result.append(r)
        return result
    except BaseException as e:
        return [[f"#CDS: {e}"]]


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
@xl_arg("tenor", "str")
def CdsAdapterCS01Tenor(adapter, tenor=None):
    """CDS Adapter CS01。tenor 可选，不传则返回整体 CS01"""
    if tenor:
        try:
            if adapter is None:
                return "#CDS: adapter 为空"
            err = _check_cds_adapter(adapter)
            if err:
                return err
            npv_err = _check_cds_npv_ready(adapter)
            if npv_err:
                return npv_err
            obj = _get_cds_adapter_obj(adapter)
            results = obj.calculateRiskMetrics()
            t = str(tenor).strip().upper()
            for m in results:
                desc = getattr(m, 'description', '') or ''
                if 'CS01' in desc and t in desc:
                    return float(getattr(m, 'value', 0))
            return f"#CDS: 无 CS01 {tenor}"
        except BaseException as e:
            return f"#CDS: {e}"
    return CdsAdapterCS01(adapter)


# ========== CLN (Credit Linked Note) ==========

def _get_cln_adapter_obj(adapter):
    """McpClnAdapter 包装时需用 getInstance() 获取内部对象"""
    if hasattr(adapter, 'getInstance'):
        return adapter.getInstance()
    return adapter


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def ClnAdapterDV01(adapter):
    """CLN Adapter DV01"""
    try:
        if adapter is None:
            return "#CLN: adapter 为空"
        obj = _get_cln_adapter_obj(adapter)
        if not hasattr(obj, 'calculateRiskMetrics'):
            return "#CLN: 无效的 adapter"
        results = obj.calculateRiskMetrics()
        for m in results:
            name = getattr(m, 'metric_name', None) or getattr(m, 'description', '')
            if name and 'DV01' in str(name):
                return float(getattr(m, 'value', 0))
        return "#CLN: 无 DV01"
    except BaseException as e:
        return f"#CLN: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
def ClnAdapterCS01(adapter):
    """CLN Adapter CS01"""
    try:
        if adapter is None:
            return "#CLN: adapter 为空"
        obj = _get_cln_adapter_obj(adapter)
        if not hasattr(obj, 'calculateRiskMetrics'):
            return "#CLN: 无效的 adapter"
        results = obj.calculateRiskMetrics()
        for m in results:
            name = getattr(m, 'metric_name', None) or getattr(m, 'description', '')
            if name and 'CS01' in str(name):
                return float(getattr(m, 'value', 0))
        return "#CLN: 无 CS01"
    except BaseException as e:
        return f"#CLN: {e}"


def _get_cln_attribution_value(adapter, metric_name):
    """从 ClnAdapter 的 attribution 指标中按名称查找并返回值"""
    obj = _get_cln_adapter_obj(adapter)
    if not hasattr(obj, 'calculateAttributionMetrics'):
        return None
    results = obj.calculateAttributionMetrics()
    if not results:
        return None
    for m in results:
        name = getattr(m, 'metric_name', None) or getattr(m, 'description', '')
        if name and str(name) == metric_name:
            return float(getattr(m, 'value', 0))
    return None


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
@xl_arg("metric", "str")
def ClnAdapterAttribution(adapter, metric):
    """
    CLN Adapter 归因指标。metric 可选: Carry, Rates, Credit, Total, Residual
    需已设置 PrevYieldCurve、PrevCreditCurve 才有归因结果
    """
    metric_map = {
        "Carry": "ATTRIBUTION_CARRY",
        "Rates": "ATTRIBUTION_RATES",
        "Credit": "ATTRIBUTION_CREDIT",
        "Total": "ATTRIBUTION_TOTAL",
        "Residual": "ATTRIBUTION_RESIDUAL",
    }
    mname = metric_map.get(str(metric).strip() if metric else "", "")
    if not mname:
        return "#CLN: metric 需为 Carry/Rates/Credit/Total/Residual 之一"
    try:
        if adapter is None:
            return "#CLN: adapter 为空"
        if isinstance(adapter, str):
            return "#CLN: adapter 创建失败"
        v = _get_cln_attribution_value(adapter, mname)
        if v is not None:
            return float(v)
        return "#CLN: 无归因(需设置 PrevYieldCurve/PrevCreditCurve)"
    except BaseException as e:
        return f"#CLN: {e}"


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "var")
@xl_arg("step", "str")
def ClnAdapterAttributionLadder(adapter, step):
    """
    CLN Adapter 归因阶梯 PV 值。step 可选: PV_t0, PV_theta, PV_rates, PV_issuer, PV_ref, PV_t1
    由 NPV 与归因 deltas 推导。双曲线模式下 PV_issuer=PV_rates
    """
    try:
        if adapter is None:
            return "#CLN: adapter 为空"
        if isinstance(adapter, str):
            return "#CLN: adapter 创建失败"
        obj = _get_cln_adapter_obj(adapter)
        npv_results = obj.calculateValuationMetrics() if hasattr(obj, 'calculateValuationMetrics') else []
        npv = None
        if npv_results and len(npv_results) > 0:
            v = getattr(npv_results[0], 'value', getattr(npv_results[0], 'value_', None))
            if v is not None:
                npv = float(v)
        if npv is None:
            return "#CLN: 无 NPV"
        attr = obj.calculateAttributionMetrics()
        if not attr:
            hint = "若已配置 PrevYieldCurve/PrevCreditCurve 仍报错，请重建 mcp（mcpPortLib 需含 MClnAdapter.setPrevYieldCurve/setPrevCreditCurve）"
            return f"#CLN: 无归因(需 PrevYieldCurve/PrevCreditCurve)。{hint}"
        d = {}
        for m in attr:
            nm = getattr(m, 'metric_name', None) or ''
            v = getattr(m, 'value', getattr(m, 'value_', 0))
            d[nm] = float(v) if v is not None else 0.0
        total = d.get('ATTRIBUTION_TOTAL', 0)
        carry = d.get('ATTRIBUTION_CARRY', 0)
        rates = d.get('ATTRIBUTION_RATES', 0)
        credit = d.get('ATTRIBUTION_CREDIT', 0)
        pv_t0 = npv - total
        pv_theta = pv_t0 + carry
        pv_rates = pv_theta + rates
        pv_ref = pv_rates + credit  # = npv = PV_t1
        step_map = {
            "PV_t0": pv_t0,
            "PV_theta": pv_theta,
            "PV_rates": pv_rates,
            "PV_issuer": pv_rates,  # 双曲线无独立 issuer
            "PV_ref": pv_ref,
            "PV_t1": npv,
        }
        s = str(step).strip() if step else ""
        if s in step_map:
            return step_map[s]
        return f"#CLN: step 需为 PV_t0/PV_theta/PV_rates/PV_issuer/PV_ref/PV_t1"
    except BaseException as e:
        return f"#CLN: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def CdsAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    CDS Adapter 现金流，参考 TrsAdapterCashflows。返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#CDS: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#CDS: adapter 创建失败或对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"]]
        err = _check_cds_adapter(adapter)
        if err:
            return [[err]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#CDS: 无效的 adapter 对象"]]
        # 预检查：NPV 不可计算时 calculateCashflows 会 crash
        npv_err = _check_cds_npv_ready(adapter)
        if npv_err:
            return [[npv_err]]
        obj = _get_cds_adapter_obj(adapter)
        flows = obj.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
            if rows:
                # 与 TrsAdapterCashflows 一致：Period 列 + fields 指定列，支持 _flatten_fields、_field_alias
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]

                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []

                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#CDS: 无现金流"]]
    except BaseException as e:
        if 'ObjectCacheKeyError' in type(e).__name__ or 'ObjectCacheKey' in str(e):
            return [["#CDS: adapter 对象缓存无效，请检查 McpCdsAdapter 参数区域或重新计算"]]
        return [[f"#CDS: {e}"]]


# ==================== LoanAndDepos Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def LoanAndDeposAdapterNPV(adapter):
    """
    LoanAndDepos Adapter 估值（NPV），需已设置 ValuationCurve
    """
    try:
        if adapter is None:
            return "#DEPO: adapter 为空"
        if isinstance(adapter, str):
            return "#DEPO: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#DEPO: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#DEPO: 无结果。请确保已设置 ValuationCurve"
    except BaseException as e:
        return f"#DEPO: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def LoanAndDeposAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    LoanAndDepos Adapter 现金流，参考 TrsAdapterCashflows。返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#DEPO: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#DEPO: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#DEPO: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                # 与 TrsAdapterCashflows 一致：Period 列 + fields 指定列，支持 _flatten_fields、_field_alias
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]

                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []

                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#DEPO: 无现金流"]]
    except BaseException as e:
        return [[f"#DEPO: {e}"]]


# ==================== BillDiscount Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BillDiscountAdapterNPV(adapter):
    """
    BillDiscount Adapter 估值（NPV），需已设置 ValuationCurve
    """
    try:
        if adapter is None:
            return "#BILL: adapter 为空"
        if isinstance(adapter, str):
            return "#BILL: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#BILL: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BILL: 无结果。请确保已设置 ValuationCurve"
    except BaseException as e:
        return f"#BILL: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BillDiscountAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    BillDiscount Adapter 现金流
    """
    try:
        if adapter is None:
            return [["#BILL: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#BILL: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#BILL: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {"PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                                "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue"}
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                out_fields = (fields and [str(x) for x in (fields[0] if isinstance(fields[0], (list, tuple)) else fields) if x]) or default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#BILL: 无现金流"]]
    except BaseException as e:
        return [[f"#BILL: {e}"]]


# ==================== BillRepo Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BillRepoAdapterNPV(adapter):
    """
    BillRepo Adapter 估值（NPV），需已设置 DiscountCurve
    """
    try:
        if adapter is None:
            return "#BILL_REPO: adapter 为空"
        if isinstance(adapter, str):
            return "#BILL_REPO: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#BILL_REPO: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BILL_REPO: 无结果。请确保已设置 DiscountCurve"
    except BaseException as e:
        return f"#BILL_REPO: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BillRepoAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    BillRepo Adapter 现金流
    """
    try:
        if adapter is None:
            return [["#BILL_REPO: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#BILL_REPO: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#BILL_REPO: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {"PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                                "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue"}
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                out_fields = (fields and [str(x) for x in (fields[0] if isinstance(fields[0], (list, tuple)) else fields) if x]) or default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#BILL_REPO: 无现金流"]]
    except BaseException as e:
        return [[f"#BILL_REPO: {e}"]]


# ==================== FRA Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def FRAAdapterNPV(adapter):
    """
    FRA Adapter 估值（NPV），需已设置 ValuationCurve
    """
    try:
        if adapter is None:
            return "#FRA: adapter 为空"
        if isinstance(adapter, str):
            return "#FRA: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#FRA: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#FRA: 无结果。请确保已设置 ValuationCurve"
    except BaseException as e:
        return f"#FRA: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def FRAAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    FRA Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#FRA: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#FRA: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#FRA: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#FRA: 无现金流"]]
    except BaseException as e:
        return [[f"#FRA: {e}"]]


# ==================== BondLending Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BondLendingAdapterNPV(adapter):
    """
    BondLending Adapter 估值（NPV），需已设置 ValuationCurve 和 DiscountCurve
    """
    try:
        if adapter is None:
            return "#BL: adapter 为空"
        if isinstance(adapter, str):
            return "#BL: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#BL: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BL: 无结果。请确保已设置 ValuationCurve 和 DiscountCurve"
    except BaseException as e:
        return f"#BL: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BondLendingAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    BondLending Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#BL: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#BL: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#BL: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#BL: 无现金流"]]
    except BaseException as e:
        return [[f"#BL: {e}"]]


# ==================== CommodityLending Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def CommodityLendingAdapterNPV(adapter):
    """
    CommodityLending Adapter 估值（NPV），需已设置 DiscountCurve
    """
    try:
        if adapter is None:
            return "#CL: adapter 为空"
        if isinstance(adapter, str):
            return "#CL: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#CL: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#CL: 无结果。请确保已设置 DiscountCurve"
    except BaseException as e:
        return f"#CL: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def CommodityLendingAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    CommodityLending Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#CL: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#CL: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#CL: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#CL: 无现金流"]]
    except BaseException as e:
        return [[f"#CL: {e}"]]


# ==================== WMProduct Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def WMProductAdapterNPV(adapter):
    """
    WMProduct Adapter 估值（NPV），需已设置 DiscountCurve（在 FundAdapter 上）
    """
    try:
        if adapter is None:
            return "#WM: adapter 为空"
        if isinstance(adapter, str):
            return "#WM: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#WM: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#WM: 无结果。请确保 FundAdapter 已设置 DiscountCurve"
    except BaseException as e:
        return f"#WM: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def WMProductAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    WMProduct Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#WM: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#WM: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#WM: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#WM: 无现金流"]]
    except BaseException as e:
        return [[f"#WM: {e}"]]


# ==================== BasisSwap Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BasisSwapAdapterNPV(adapter):
    """
    BasisSwap Adapter 估值（NPV），需已设置 4 条曲线
    """
    try:
        if adapter is None:
            return "#BS: adapter 为空"
        if isinstance(adapter, str):
            return "#BS: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#BS: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BS: 无结果。请确保已设置 4 条曲线"
    except BaseException as e:
        return f"#BS: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BasisSwapAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    BasisSwap Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#BS: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#BS: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#BS: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#BS: 无现金流"]]
    except BaseException as e:
        return [[f"#BS: {e}"]]


# ==================== BondForward Adapter UDF ====================

@xl_func(macro=False, recalc_on_open=True)
@xl_arg("adapter", "object")
def BondForwardAdapterNPV(adapter):
    """
    BondForward Adapter 估值（NPV），需已设置 DiscountCurve
    """
    try:
        if adapter is None:
            return "#BF: adapter 为空"
        if isinstance(adapter, str):
            return "#BF: adapter 创建失败或对象缓存无效"
        if not hasattr(adapter, 'calculateValuationMetrics'):
            return "#BF: 无效的 adapter 对象"
        val = adapter.calculateValuationMetrics()
        if val and len(val) > 0:
            v = getattr(val[0], 'value', None)
            if v is not None:
                return float(v)
        return "#BF: 无结果。请确保已设置 DiscountCurve"
    except BaseException as e:
        return f"#BF: {e}"


@xl_func(macro=False, recalc_on_open=True, auto_resize=True)
@xl_arg("adapter", "object")
@xl_arg("useYieldCurve", "bool")
@xl_arg("fields", "str[]")
@xl_return("var[][]")
def BondForwardAdapterCashflows(adapter, useYieldCurve=True, fields=None):
    """
    BondForward Adapter 现金流，返回 2D 数组（表头+数据行）供 Excel 平铺显示
    """
    try:
        if adapter is None:
            return [["#BF: adapter 为空"]]
        if isinstance(adapter, str):
            return [["#BF: adapter 创建失败或对象缓存无效"]]
        if not hasattr(adapter, 'calculateCashflows'):
            return [["#BF: 无效的 adapter 对象"]]
        flows = adapter.calculateCashflows(useYieldCurve)
        if flows and len(flows) > 0:
            rows = []
            for leg in flows:
                leg_items = list(leg) if not isinstance(leg, list) else leg
                for cf in leg_items:
                    if hasattr(cf, 'payment_date'):
                        po = {
                            "PaymentDate": str(cf.payment_date) if hasattr(cf, 'payment_date') else "",
                            "Amount": float(cf.amount) if (hasattr(cf, 'amount') and isinstance(getattr(cf, 'amount', None), (int, float))) else 0.0,
                            "Currency": str(cf.currency) if hasattr(cf, 'currency') else "",
                            "FlowType": str(cf.flow_type) if hasattr(cf, 'flow_type') else "",
                            "DiscountFactor": float(cf.discount_factor) if (hasattr(cf, 'discount_factor') and isinstance(getattr(cf, 'discount_factor', None), (int, float))) else 0.0,
                            "PresentValue": float(cf.present_value) if (hasattr(cf, 'present_value') and isinstance(getattr(cf, 'present_value', None), (int, float))) else 0.0,
                        }
                        rows.append(po)
                    elif isinstance(cf, dict):
                        rows.append(cf)
            if rows:
                _field_alias = {
                    "PaymentDates": "PaymentDate", "Payments": "Amount", "Amounts": "Amount",
                    "DiscountFactors": "DiscountFactor", "PresentValues": "PresentValue",
                }
                default_fields = ["PaymentDate", "Amount", "Currency", "FlowType", "DiscountFactor", "PresentValue"]
                def _flatten_fields(f):
                    if not f:
                        return []
                    if isinstance(f, (list, tuple)) and len(f) > 0:
                        first = f[0]
                        if isinstance(first, (list, tuple)):
                            return [str(x) for row in f for x in (row if isinstance(row, (list, tuple)) else [row]) if x]
                        return [str(x) for x in f if x]
                    return []
                out_fields = _flatten_fields(fields) if fields else default_fields
                if not out_fields:
                    out_fields = default_fields
                result = []
                for i, row in enumerate(rows, start=1):
                    obj = [f"Period{i}"]
                    for field in out_fields:
                        key = _field_alias.get(field, field)
                        v = row.get(key, "")
                        obj.append(v if v is not None else "")
                    result.append(obj)
                return result
        return [["#BF: 无现金流"]]
    except BaseException as e:
        return [[f"#BF: {e}"]]
