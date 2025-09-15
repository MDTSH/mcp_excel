#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo program with several features:
1. FX vanilla option (European and American) pricing test program (by directly providing rates, forward prices and volatility)
2. Test FX vanilla option pricing results

Author: Mathema Team
Version: 2.1
Last Updated: March 2024
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from mcp.utils.enums import EnumWrapper, BuySell, CallPut, DateAdjusterRule, DayCounter, InterpolationMethod, Frequency, InterpolatedVariable, DeltaType, CalculatedTarget, OptionExpiryNature, PricingMethod, SmileInterpMethod, Side
import mcp.forward.fwd_wrapper
from example.calendar.calendar_demo import (
    McpNCalendar, 
    usd_dates, 
    cny_dates, 
    GetCurrencyCalendar
)
from mcp.tool.tools_main import McpVanillaOption

w = EnumWrapper()
# Initialize calendar
CALENDAR = McpNCalendar(['USD', 'CNY'], [usd_dates, cny_dates])
USD_CAL = GetCurrencyCalendar('USD', usd_dates)
CNY_CAL = GetCurrencyCalendar('CNY', cny_dates)
REFERENCE_DATE = '2024-12-13'


def create_option_args() -> Dict[str, Any]:
    """Create option parameters"""
    return {
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
        'StrikePx': 7.3,
        'FaceAmount': 1000000,
        'CalculatedTarget': CalculatedTarget.CCY1,
        'SpotPx': 7.0671,
        'ForwardPx': 7.1865,
        'DomesticRate': 0.018580000000000003,
        'ForeignRate': 0.04746606688265108,
        'Volatility': 0.04841614234006056
    }


def price_option(option_args: Dict) -> Tuple[float, float, float]:
    """
    Option pricing and risk calculation
    Returns: (price, USD Delta, CNY Delta)
    """
    option = McpVanillaOption(option_args)
    price = option.Price(True)
    delta_usd = option.Delta(False, True)
    delta_cny = option.Delta(True, True)
    return price, delta_usd, delta_cny


def get_pricing_details(vo: mcp.forward.fwd_wrapper.McpVanillaOption) -> pd.DataFrame:
    """Get and transpose detailed data from pricing process"""
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
    return pd.DataFrame([detail]).transpose()

def format_results(price: float, delta_usd: float, delta_cny: float) -> str:
    """Format pricing results"""
    return (
        f"\nOption Pricing Results:\n"
        f"{'-'*40}\n"
        f"{'Price':<15}: {price:.6f}\n"
        f"{'USD Delta':<15}: {delta_usd:.6f}\n"
        f"{'CNY Delta':<15}: {delta_cny:.6f}\n"
        f"{'-'*40}"
    )


def test_vanilla_option() -> Dict[str, Any]:
    """Test Vanilla option pricing"""
    print("="*60)
    print("Vanilla Option Pricing Test")
    print("="*60)
    
    try:
        # 1. Prepare parameters
        option_args = create_option_args()
        print("\nOption parameters configured")
        
        # 2. Pricing and risk calculation
        price, delta_usd, delta_cny = price_option(option_args)
        print(format_results(price, delta_usd, delta_cny))
        
        # 3. Get and display transposed pricing details
        option = McpVanillaOption(option_args)
        pricing_details = get_pricing_details(option)
        
        print("\nPricing Process Details (Transposed):")
        print(pricing_details.to_string(
            justify='left',
            float_format=lambda x: f"{x:.6f}" if isinstance(x, float) else str(x)
        ))
        
        return {
            'price': price,
            'delta_usd': delta_usd,
            'delta_cny': delta_cny,
            'pricing_details': pricing_details
        }
        
    except Exception as e:
        print(f"\nPricing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_results = test_vanilla_option()