#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bilateral Yield Curve Test Program

This program demonstrates how to:
1. Construct bilateral yield curves (bid/ask)
2. Calculate zero rates and discount factors for different tenors
3. Support calculations for standard and custom tenors

Features:
- Support for bid/ask bilateral quotes
- Provide detailed curve construction parameter output
- Calculation result verification and debugging information

Author: Mathema Team
Last Updated: 2024
"""

import datetime
from typing import Dict, List, Tuple, Any  # Added Any import

from example.calendar.calendar_demo import GetCurrencyCalendar, usd_dates
from mcp import mcp, wrapper
from mcp.mcp import MYieldCurve2
from mcp.tool.tools_main import McpYieldCurve2


def print_curve_parameters(args: Dict) -> None:
    """Print curve construction parameters"""
    print("Bilateral Yield Curve Construction Parameters:")
    print(f"  • Reference Date: {args['ReferenceDate']}")
    # print(f"  • Calendar: {args['Calendar'].getCalendarName()}")
    print(f"  • Interpolation Method: {args['InterpolationMethod']}")
    
    print("\n  Tenors and Corresponding Rates:")
    for i, (tenor, bid, ask) in enumerate(zip(
        args['Tenors'], args['BidZeroRates'], args['AskZeroRates']
    )):
        print(f"    {i+1:2d}. {tenor:>4s}: Bid={bid*100:6.4f}%  Ask={ask*100:6.4f}%")


def construct_yield_curve() -> Tuple[MYieldCurve2, Dict]:
    """Construct bilateral yield curve"""
    print("=" * 60)
    print("Bilateral Yield Curve Construction")
    print("=" * 60)
    
    reference_date = '2024-8-9'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    curve_args = {
        'ReferenceDate': reference_date,
        'Tenors': [
            'ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', 
            '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M',
            '11M', '1Y', '2Y', '3Y', '4Y', '5Y'
        ],
        'BidZeroRates': [
            0.0524, 0.0525, 0.0525, 0.0525, 0.0535, 0.0537,
            0.0536, 0.053, 0.0526, 0.0518, 0.0512, 0.0504,
            0.0498, 0.049, 0.0488, 0.0482, 0.0475, 0.0473,
            0.0424, 0.0391, 0.038, 0.0376
        ],
        'AskZeroRates': [
            0.0531, 0.0545, 0.0545, 0.0552, 0.0543, 0.0545,
            0.0542, 0.0537, 0.0534, 0.0528, 0.0522, 0.0514,
            0.0518, 0.051, 0.0498, 0.0502, 0.0495, 0.0483,
            0.0454, 0.0421, 0.041, 0.0406
        ],
        'Calendar': cal_usd,
        'Frequency': 'NoFrequency',
        'Variable': 'SIMPLERATES',
        'InterpolationMethod': 'LINEARINTERPOLATION'
    }
    
    print_curve_parameters(curve_args)
    
    print("\nConstructing yield curve object...")
    yield_curve = McpYieldCurve2(curve_args)
    print("Curve constructed successfully!")
    
    return yield_curve, curve_args


def calculate_rates(yield_curve: MYieldCurve2, cal_usd: Any) -> Dict:
    """Calculate rates and discount factors for various tenors"""
    print("\n" + "=" * 60)
    print("Interest Rate Calculation Results")
    print("=" * 60)
    
    test_tenors = ['ON', '1W', '2W', '30D', '1M', '2M', '1Y']
    
    results = {
        'tenor': [],
        'maturity_date': [],
        'bid_rate': [],
        'ask_rate': [],
        'mid_rate': [],
        'bid_discount_factor': [],
        'ask_discount_factor': [],
        'mid_discount_factor': []
    }
    
    for tenor in test_tenors:
        print(yield_curve.GetReferenceDate())
        spot_date = cal_usd.ValueDate(yield_curve.GetReferenceDate())
        maturity_date = cal_usd.FXOExpiryDateFromTenor(
            yield_curve.GetReferenceDate(), 
            tenor, 
            spot_date
        )
        
        # Calculate rates
        bid_rate = yield_curve.ZeroRate(maturity_date, 'bid')
        ask_rate = yield_curve.ZeroRate(maturity_date, 'ask')
        mid_rate = yield_curve.ZeroRate(maturity_date, 'mid')
        
        # Calculate discount factors
        bid_df = yield_curve.DiscountFactor(maturity_date, 'bid')
        ask_df = yield_curve.DiscountFactor(maturity_date, 'ask')
        mid_df = yield_curve.DiscountFactor(maturity_date, 'mid')
        
        # Store results
        results['tenor'].append(tenor)
        results['maturity_date'].append(maturity_date)
        results['bid_rate'].append(bid_rate)
        results['ask_rate'].append(ask_rate)
        results['mid_rate'].append(mid_rate)
        results['bid_discount_factor'].append(bid_df)
        results['ask_discount_factor'].append(ask_df)
        results['mid_discount_factor'].append(mid_df)
        
        # Print results
        print(f"Tenor {tenor:>3s}:")
        print(f"  • Maturity Date: {maturity_date}")
        print(f"  • Bid Rate: {bid_rate*100:.6f}%")
        print(f"  • Ask Rate: {ask_rate*100:.6f}%")
        print(f"  • Mid Rate: {mid_rate*100:.6f}%")
        print(f"  • Bid Discount Factor: {bid_df:.8f}")
        print(f"  • Ask Discount Factor: {ask_df:.8f}")
        print()
    
    return results


def validate_results(results: Dict) -> None:
    """Validate calculation results"""
    print("=" * 60)
    print("Calculation Results Validation")
    print("=" * 60)
    
    expected_bid_rates = [
        0.0524, 0.0525, 0.052928571, 
        0.05364, 0.05362, 0.05309375, 
        0.047313333
    ]
    
    # Validate bid rates
    print("\nBid Rate Validation:")
    for i, (calc, expected) in enumerate(zip(results['bid_rate'], expected_bid_rates)):
        diff = abs(calc - expected)
        print(
            f"Tenor {results['tenor'][i]:>3s}: "
            f"Calculated={calc:.8f}, Expected={expected:.8f}, Difference={diff:.8f}"
        )
        assert diff < 1e-8, f"Bid rate validation failed: Tenor {results['tenor'][i]}"
    
    print("\nAll validations passed!")


def test_bilateral_yield_curve():
    """Test bilateral yield curve"""
    try:
        print("Bilateral Yield Curve Test Started")
        print(f"Run Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Construct yield curve
        yield_curve, curve_args = construct_yield_curve()
        
        # 2. Calculate various rates
        results = calculate_rates(yield_curve, curve_args['Calendar'])
        
        # 3. Validate results
        validate_results(results)
        
        print("\n" + "=" * 60)
        print("Test Completed!")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_results = test_bilateral_yield_curve()