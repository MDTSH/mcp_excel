#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo program with several features:
1. Build bilateral yield curve McpYieldCurve2
2. Build bilateral forward points curve McpFXForwardPointsCurve2
3. Build bilateral volatility surface McpFXVolSurface2
4. FX vanilla option (European and American) pricing test program (via bilateral volatility surface FXVolSurface2)
5. Test FX vanilla option pricing results

Author: Mathema Team
Version: 2.1
Last Updated: March 2024
"""

import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from mcp.utils.enums import EnumWrapper, BuySell, CallPut, DateAdjusterRule, DayCounter, InterpolationMethod, Frequency, InterpolatedVariable, DeltaType, CalculatedTarget, OptionExpiryNature, PricingMethod, SmileInterpMethod, Side
import mcp.forward.fwd_wrapper
from example.calendar.calendar_demo import (
    McpNCalendar, 
    usd_dates, 
    cny_dates, 
    GetCurrencyCalendar
)
from mcp.mcp import MMktVolSurface2
from mcp.tool.tools_main import (
    McpYieldCurve2, 
    McpFXForwardPointsCurve2,  # 保持原始类名
    McpFXVolSurface2, 
    McpVanillaOption
)
from mcp.utils.enums import DayCounter

# ==================== Global Configuration ====================
CALENDAR = McpNCalendar(['USD', 'CNY'], [usd_dates, cny_dates])
USD_CAL = GetCurrencyCalendar('USD', usd_dates)
CNY_CAL = GetCurrencyCalendar('CNY', cny_dates)
REFERENCE_DATE = '2024-12-13'
w = EnumWrapper()
# ==================== Utility Functions ====================
def format_float(value: Any) -> Any:
    """Maintain original float precision, only for display formatting"""
    if isinstance(value, float):
        # Maintain original precision, do not actually modify value
        return value
    return value

# ==================== Market Data Construction ====================
def build_yield_curves() -> Tuple[Any, Any]:
    """Build bilateral yield curves"""
    yc_args_usd = {
        'ReferenceDate': REFERENCE_DATE,
        'Tenors': ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M',
                  '10M', '11M', '1Y', '2Y', '3Y', '4Y', '5Y'],
        'BidZeroRates': [0.0458, 0.04389, 0.045, 0.04389, 0.0433, 0.046, 0.0433,
                        0.0433, 0.0433, 0.0435, 0.0435, 0.0433, 0.0434, 0.0434, 0.0433, 0.0433, 0.0433,
                        0.0433, 0.044000, 0.043, 0.042, 0.042],
        'AskZeroRates': [0.04589, 0.0451, 0.04570, 0.0451, 0.0458, 0.0553, 0.0458,
                        0.0458, 0.0458, 0.046, 0.046, 0.0458, 0.04589, 0.04589,
                        0.0458, 0.0458, 0.0458, 0.0458, 0.0465, 0.046, 0.045, 0.045],
        'Calendar': USD_CAL,
        'ShortName': 'USDSofrSnapYldCurve',
        'Symbol': 'USD',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES, 
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }

    yc_args_cny = {
        'ReferenceDate': REFERENCE_DATE,
        'Tenors': ['ON', '1W', '2W', '1M', '3M', '6M', '9M', '1Y'],
        'BidZeroRates': [0.01403, 0.01758, 0.0187, 0.0171, 0.01735, 0.01744,
                        0.01758, 0.01774],
        'AskZeroRates': [0.01403, 0.01758, 0.0187, 0.0171, 0.01735, 0.01744,
                        0.01758, 0.01774],
        'Calendar': CNY_CAL,
        'ShortName': 'CNYShibor3mSnapYldCurve',
        'Symbol': 'CNY',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES, 
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }

    yc_usd = McpYieldCurve2(yc_args_usd)
    yc_cny = McpYieldCurve2(yc_args_cny)
    return yc_usd, yc_cny

def build_forward_curve() -> Any:
    """Build bilateral forward points curve"""
    fw_args = {
        'ReferenceDate': REFERENCE_DATE,
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', '11M', '1Y',
                   '18M', '2Y', '3Y', '4Y', '5Y'],
        'BidForwardPoints': [-39.5, -77.0, -116.0, -177.0, -360.35, -522.77, -709.23, -922.0, -1124.52, -1328.0,
                            -1531.0, -1749.28, -1940.0, -2145.0, -2388.0, -3450.0, -4330.0, -5696.61, -6000.0,
                            -8050.0],
        'AskForwardPoints': [-35.5, -75.2, -114.0, -167.0, -348.43, -509.23, -704.0, -915.0, -1105.48, -1283.0,
                            -1486.0, -1724.72, -1896.6, -2103.3, -2358.0, -2860.0, -4230.0, -5463.39, -4900.0,
                            -7550.0],
        'BidFXSpotRate': 7.2768,
        'AskFXSpotRate': 7.277,
        'Pair': 'USD/CNY',
        'Calendar': CALENDAR,
        'ShortName': 'USDCNYFwdSnapCurve',
        'Symbol': 'USD/CNY',
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    return McpFXForwardPointsCurve2(fw_args)  # Keep original class name

def build_vol_surface(yc_usd: Any, yc_cny: Any, fc: Any) -> Any:
    """Build bilateral volatility surface"""
    vol_args = {
        'ReferenceDate': REFERENCE_DATE,
        #'ShortName': 'USDCNYRSnapVolSurface',
        'Symbol': 'USD/CNY',
        'Calendar': CALENDAR,
        'DayCounter': DayCounter.Act365Fixed,
        'DateAdjusterRule': DateAdjusterRule.ModifiedFollowing,
        'PremiumAdjusted': False,
        'DeltaType': DeltaType.FORWARD_DELTA,
        'IsATMFwd': True,
        'FxForwardPointsCurve2': fc,
        'ForeignCurve2': yc_usd,
        'DomesticCurve2': yc_cny,
        'CalculatedTarget': CalculatedTarget.CCY1,
        'SmileInterpMethod': SmileInterpMethod.CUBICSPLINE,

        'DeltaStrings': ['10DPUT', '15DPUT', '20DPUT', '25DPUT', '30DPUT', '35DPUT', '40DPUT', '45DPUT', 'ATM',
                        '45DCAL', '40DCAL', '35DCAL', '30DCAL', '25DCAL', '20DCAL', '15DCAL', '10DCAL'],
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '18M', '2Y'],
        'BidVolatilities': '0.05131,0.049980,0.04865,0.04734,0.04602,0.04478,0.04360,0.04258,0.04174,0.04108,0.04062,0.040350,0.04026,0.04034,0.04058,0.04092,0.04131;'
                          '0.05284,0.05215,0.05141,0.05046,0.04935,0.0482,0.04707,0.04605,0.04525,0.04462,0.04424,0.04409,0.04417,0.04448,0.0449,0.04534,0.04584;'
                          '0.05459,0.05368,0.05274,0.05171,0.05059,0.04942,0.0483,0.04727,0.0465,0.04586,0.04549,0.04534,0.04541,0.045720,0.04623,0.04687,0.04759;'
                          '0.05407,0.0529,0.05175,0.05064,0.04962,0.0487,0.04792,0.04734,0.047,0.04686,0.04694,0.04721,0.04763,0.04815,0.04875,0.04940,0.05006;'
                          '0.05753,0.05701,0.05644,0.05583,0.05513,0.05443,0.05382,0.05339,0.05325,0.05337,0.05379,0.05445,0.05531,0.05631,0.05740,0.05857,0.059770;'
                          '0.05405,0.05314,0.052270,0.05146,0.05076,0.05021,0.04988,0.04982,0.05,0.05054,0.05136,0.05235,0.05341,0.05445,0.05538,0.05624,0.05705;'
                          '0.057460,0.05686,0.056280,0.05574,0.05527,0.05492,0.05477,0.05489,0.05518,0.05586,0.05684,0.05803,0.05932,0.06065,0.06193,0.06317,0.0644;'
                          '0.0592,0.05875,0.05831,0.0579,0.05753,0.05729,0.05722,0.05744,0.05776,0.05849,0.05956,0.06084,0.06225,0.06371,0.06516,0.06659,0.068;'
                          '0.06030,0.05995,0.0596,0.05926,0.05897,0.05878,0.05878,0.05905,0.05937,0.06014,0.06126,0.0626,0.06408,0.06563,0.06718,0.06873,0.07026;'
                          '0.06064,0.06007,0.05956,0.05915,0.05891,0.05885,0.05902,0.05945,0.05975,0.0605,0.06161,0.06299,0.06459,0.0664,0.06837,0.07044,0.07254;'
                          '0.06039,0.05996,0.05961,0.05933,0.05918,0.05921,0.05944,0.05991,0.06011,0.06078,0.06186,0.06324,0.06492,0.06691,0.06919,0.07166,0.07421;'
                          '0.05928,0.05884,0.05844,0.05817,0.058070,0.05819,0.05856,0.05918,0.05924,0.05980,0.06089,0.06227,0.06399,0.06602,0.06838,0.07091,0.07351;'
                          '0.05803,0.05756,0.05716,0.056870,0.05673,0.05682,0.05719,0.05789,0.05775,0.05819,0.05939,0.06093,0.06280,0.06498,0.06741,0.07002,0.07267',
        'AskVolatilities': '0.06631,0.06498,0.06366,0.06234,0.06103,0.05978,0.05860,0.05758,0.05674,0.05608,0.05562,0.05535,0.05526,0.05534,0.05558,0.05592,0.05631;'
                          '0.05783,0.05671,0.05557,0.05447,0.05335,0.05219,0.051070,0.05005,0.04924,0.04862,0.04824,0.04809,0.048170,0.04847,0.04906,0.0499,0.05083;'
                          '0.05859,0.05767,0.05674,0.05570,0.05459,0.05343,0.05230,0.05128,0.05049,0.04987,0.04949,0.04934,0.04942,0.04972,0.05023,0.05087,0.05159;'
                          '0.058070,0.05690,0.05575,0.05464,0.05362,0.0527,0.05192,0.051340,0.051,0.05086,0.05094,0.05121,0.05163,0.05215,0.05275,0.05339,0.05407;'
                          '0.06152,0.06101,0.06045,0.05982,0.05913,0.05843,0.05782,0.0574,0.05724,0.057370,0.05779,0.05844,0.05931,0.06030,0.06141,0.06258,0.06377;'
                          '0.05805,0.05714,0.05627,0.05546,0.05476,0.05421,0.05388,0.05382,0.05400,0.05454,0.05535,0.05635,0.05740,0.05844,0.05937,0.06024,0.06105;'
                          '0.06145,0.06085,0.060270,0.05973,0.05926,0.05891,0.05876,0.05888,0.059160,0.05985,0.06083,0.06200,0.06331,0.06463,0.06591,0.06715,0.06838;'
                          '0.0632,0.06274,0.06231,0.06189,0.06152,0.06128,0.06123,0.06143,0.06175,0.06249,0.06355,0.06483,0.06624,0.0677,0.06915,0.07058,0.07199;'
                          '0.06431,0.06394,0.0636,0.06326,0.06297,0.06278,0.06279,0.06306,0.06338,0.06415,0.06526,0.0666,0.06808,0.06963,0.07118,0.07273,0.07426;'
                          '0.06464,0.06407,0.06356,0.06315,0.06291,0.06285,0.06301,0.06344,0.06375,0.0645,0.06561,0.06699,0.06859,0.0704,0.07237,0.07444,0.07654;'
                          '0.06439,0.06397,0.06361,0.06333,0.06319,0.06321,0.06344,0.06391,0.06412,0.06478,0.06586,0.06724,0.06892,0.07091,0.07319,0.07566,0.07821;'
                          '0.06577,0.06533,0.06495,0.06466,0.06448,0.06446,0.06466,0.0652,0.06526,0.06582,0.06701,0.06854,0.07039,0.07251,0.07487,0.0774,0.08;'
                          '0.06703,0.06657,0.06616,0.06587,0.06573,0.06582,0.06619,0.06689,0.06675,0.06719,0.06839,0.06993,0.07181,0.07397,0.07641,0.07902,0.08166',

    }
    return McpFXVolSurface2(vol_args)

# ==================== Option Pricing ====================
def price_option(fx_vol2: Any) -> Dict[str, Any]:
    """Strictly maintain original option parameter structure"""
    vo_args = {
        'Pair': 'USD/CNY',
        'BuySell': BuySell.Buy,
        'OptionExpiryNature': OptionExpiryNature.EUROPEAN,
        'CallPut': CallPut.Call,
        'NumSimulation': 1000000,
        'Side': Side.Client,
        'PricingMethod': PricingMethod.BLACKSCHOLES,
        'ReferenceDate': REFERENCE_DATE,
        'ExpiryDate': '2025-02-14',
        'DeliveryDate': '2025-02-18',
        'PremiumDate': '2024-11-18',
        'Calendar': CALENDAR,
        'DayCounter': DayCounter.Act365Fixed,
        'FXVolSurface2': fx_vol2,
        'StrikePx': 7.3,
        'FaceAmount': 1000000,
        'CalculatedTarget': CalculatedTarget.CCY1,
        'SpotPx': 7.0671
    }
    
    vo = McpVanillaOption(vo_args)
    price = vo.Price(True)
    deltaUSD = vo.Delta(False, True)
    deltaCNY = vo.Delta(True, True)
    
    # Get pricing details
    fields = ['ReferenceDate', 'SpotPx', 'StrikePx', 'BuySell', 'CallPut', 
              'ExpiryDate', 'DeliveryDate', 'TimeToExpiry', 'TimeToExpiryTime',
              'DomesticRate', 'ForeignRate', 'ForwardPx', 'Volatility', 'FaceAmount',
              'OptionExpiryNature', 'PricingMethod']
    details = []
    detail = {
        'ReferenceDate': vo.GetReferenceDate(),
        'SpotPx': vo.GetSpot(),
        'StrikePx': vo.GetStrike(),
        'BuySell':w.key_of_value(vo.GetBuySell(),"BuySell"),
        'CallPut': w.key_of_value(vo.GetCallPutType(),"CallPut"),
        'ExpiryDate': vo.GetExpiryDate(),
        'DeliveryDate': vo.GetDeliveryDate(),
        'TimeToExpiry': vo.GetTimeToExpiry(),
        'DomesticRate': vo.GetAccRate(),
        'ForeignRate': vo.GetUndRate(),
        'ForwardPx': vo.GetForward(),
        'Volatility': vo.GetVol(),

    }
    details.append(detail)
    return {
        'price': price,
        'deltaUSD': deltaUSD,
        'deltaCNY': deltaCNY,
        'details': details
    }
# ==================== Main Program ====================
def main():
    """Main execution flow"""
    print("="*60)
    print(" FX Vanilla Option Pricing Test (Bilateral Volatility Surface) ")
    print("="*60)
    
    try:
        # 1. Build market data
        yc_usd, yc_cny = build_yield_curves()
        fc = build_forward_curve()
        fx_vol2 = build_vol_surface(yc_usd, yc_cny, fc)
        
        # 2. Execute pricing
        results = price_option(fx_vol2)
        
        # 3. Output results
        print(f"\nPricing Results:")
        print(f"price = {results['price']}\ndeltaUSD={results['deltaUSD']}\ndeltaCNY={results['deltaCNY']}")
        
        print("\nPricing Details:")
        for i, detail in enumerate(results['details'], 1):
            print(f"\nLeg {i}:")
            for k, v in detail.items():
                print(f"  {k}: {v}")
                
        return True
        
    except Exception as e:
        print(f"\nExecution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        import sys
        sys.exit(1)