#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FR007 Interest Rate Swap Curve Test Program

This program demonstrates how to:
1. Construct FR007 interest rate swap curve
2. Calculate zero rates, discount factors and forward rates for different tenors
3. Support calculations for standard and custom tenors

Features:
- Support for multiple interest rate interpolation methods (linear interpolation, etc.)
- Provide detailed curve construction parameter output
- Support for standard tenors (ON, 1M, 3M, 1Y, etc.) and custom tenors
- Calculation result verification and summary table output

Author: Mathema Team
Last Updated: 2024
"""

import datetime
from typing import List, Dict, Any

from example.calendar.calendar_demo import GetCurrencyCalendar, usd_dates
from mcp import mcp, wrapper
from mcp.utils.enums import DayCounter, Frequency
from mcp.mcp import MYieldCurve2, MYieldCurve
from mcp.tool.tools_main import McpSwapCurve, McpVanillaSwap, McpVanillaSwapCurveData, McpYieldCurve2, McpYieldCurve


def print_curve_parameters(args: Dict[str, Any]) -> None:
    """Print swap curve construction parameters"""
    print("FR007 Interest Rate Swap Curve Construction Parameters:")
    print(f"  • Reference Date: {args['ReferenceDate']}")
    print(f"  • Swap Start Lag: {args['SwapStartLag']} days")
    print(f"  • Fixed Frequency: {args['FixedFrequency']}")
    print(f"  • Float Frequency: {args['FloatFrequency']}")
    print(f"  • Fixed Day Counter: {args['FixedDayCounter']}")
    print(f"  • Float Day Counter: {args['FloatDayCounter']}")
    print(f"  • Fixing Index: {args['FixingIndex']}")
    print("\n  Tenors and Corresponding Swap Rates:")
    for i, (date, coupon) in enumerate(zip(args['MaturityDates'], args['Coupons'])):
        print(f"    {i+1:2d}. {date}: {coupon*100:>6.4f}%")


def test_swap_curve_construction() -> McpSwapCurve:
    """Construct FR007 interest rate swap curve"""
    print("=" * 60)
    print("FR007 Interest Rate Swap Curve Construction")
    print("=" * 60)
    
    # Basic parameter settings
    referenceDate = '2024-9-21'
    cal_usd = GetCurrencyCalendar('USD', usd_dates)
    
    # Swap curve data parameters
    vsc_data_args = {
        "ReferenceDate": referenceDate,
        "SwapStartLag": 1,
        "Calendar": cal_usd,
        "PaymentDateAdjuster": "ModifiedFollowing",
        "AccrDateAdjuster": "Actual",
        "FixedFrequency": "Quarterly",
        "FloatFrequency": "Quarterly",
        "FixedDayCounter": "Act365Fixed",
        "FloatDayCounter": "Act365Fixed",
        "UseIndexEstimation": True,
        "FixingIndex": "7D",
        "FixingRateMethod": "COMPOUNDING",
        "FixInAdvance": True,
        "FixDaysBackward": 1,
        "Margin": 0,
        "MaturityDates": [
            '2025-3-21', '2025-6-23', '2025-9-22', '2026-9-21', 
            '2027-9-21', '2028-9-21', '2029-9-21', '2031-9-22', 
            '2034-9-21'
        ],
        "Coupons": [
            0.0184, 0.01755, 0.0171, 0.01715, 
            0.0176, 0.0182, 0.01885, 0.01965, 
            0.02065
        ],
        "BumpAmounts": [0.0000] * 9,
        "Buses": [1] * 9
    }
    
    # Print construction parameters
    print_curve_parameters(vsc_data_args)
    
    # Construct swap curve data
    print("\nConstructing swap curve data...")
    vsc_data_args_curve: mcp.MVanillaSwapCurveData = McpVanillaSwapCurveData(vsc_data_args)
    
    # Set up calibration set
    c_set = wrapper.McpCalibrationSet()
    c_set.addData(vsc_data_args_curve.getHandler())
    c_set.addEnd()
    
    # Construct swap curve
    fixed_sc_args = {
        "ReferenceDate": referenceDate,
        'CalibrationSet': c_set,
        'InterpolatedVariable': 'CONTINUOUSRATES',
        'InterpolationMethod': 'LINEARINTERPOLATION',
        'DayCounter': 'ActActISDA'
    }
    
    print("\nConstructing swap curve object...")
    swap_curve: mcp.MSwapCurve = McpSwapCurve(fixed_sc_args)
    print("Swap curve constructed successfully!")
    
    return swap_curve, cal_usd, referenceDate


def test_spot_rates_calculation(swap_curve: McpSwapCurve, cal_usd: Any, referenceDate: str) -> Dict[str, List]:
    """Test spot rate and discount factor calculation"""
    print("\n" + "=" * 60)
    print("Spot Rate and Discount Factor Calculation")
    print("=" * 60)
    
    # Test tenors
    tenors = ['0D', 'ON', '2W', '1M', '3M', '6M', '9M', '1Y', '2Y', '3Y', '4Y', '5Y', '7Y', '10Y']
    
    results = {
        'tenor': [],
        'maturity_date': [],
        'discount_factor': [],
        'zero_rate': []
    }
    
    for tenor in tenors:
        # Calculate maturity date
        if tenor == '0D':
            maturity_date = referenceDate
        else:
            maturity_date = cal_usd.ValueDate(referenceDate, tenor, 'ModifiedFollowing', True)
        
        # Calculate discount factor and zero rate
        discount_factor = swap_curve.DiscountFactor(maturity_date)
        zero_rate = swap_curve.ZeroRate(maturity_date)
        
        results['tenor'].append(tenor)
        results['maturity_date'].append(maturity_date)
        results['discount_factor'].append(round(discount_factor, 7))
        results['zero_rate'].append(zero_rate)
        
        print(f"Tenor {tenor:>3s}:")
        print(f"  • Maturity Date: {maturity_date}")
        print(f"  • Discount Factor: {discount_factor:.7f}")
        print(f"  • Zero Rate: {zero_rate*100:.6f}%")
        print()
    
    return results


def test_forward_rates_calculation(swap_curve: McpSwapCurve, cal_usd: Any, referenceDate: str) -> Dict[str, List]:
    """Test forward rate calculation"""
    print("=" * 60)
    print("Forward Rate Calculation")
    print("=" * 60)
    
    # Test tenors
    test_fw_tenors = ['1W', '1M', '2M', '3M', '4M', '5M', '6M', '1Y']
    
    results = {
        'tenor': [],
        'start_date': [],
        'end_date': [],
        'forward_rate': []
    }
    
    for tenor in test_fw_tenors:
        # Calculate start date and end date
        start_date = cal_usd.ValueDate(referenceDate, tenor)
        end_date = cal_usd.AddPeriod(start_date, '1M', 'ModifiedFollowing')
        
        # Calculate forward rate
        forward_rate = swap_curve.ForwardRate(
            start_date, end_date, 
            DayCounter.ActActISDA, 
            True, 
            Frequency.Continuous
        )
        
        results['tenor'].append(tenor)
        results['start_date'].append(start_date)
        results['end_date'].append(end_date)
        results['forward_rate'].append(forward_rate)
        
        print(f"Tenor {tenor:>3s}:")
        print(f"  • Start Date: {start_date}")
        print(f"  • End Date: {end_date}")
        print(f"  • Forward Rate: {forward_rate*100:.6f}%")
        print()
    
    return results


def validate_results(spot_results: Dict[str, List], forward_results: Dict[str, List]) -> None:
    """Validate calculation results (tolerance relaxed to 1e-4)"""
    print("=" * 60)
    print("Calculation Results Validation (Tolerance 1e-4)")
    print("=" * 60)
    
    expected_discount_factors = [
        1.0000000, 0.9998995, 0.9991462, 0.9983432, 
        0.9952878, 0.9907999, 0.9868674, 0.9829580,
        0.9662089, 0.9484981, 0.9295825, 0.9098264, 
        0.8710893, 0.8124332
    ]
    
    expected_forward_rates = [
        0.018390719, 0.018390719, 0.018390719, 
        0.018390719, 0.018390719, 0.01820524, 
        0.016339207, 0.01712576
    ]
    
    # Print detailed comparison results
    print("\nDiscount Factor Validation Details:")
    for i, (calc, expected) in enumerate(zip(spot_results['discount_factor'], expected_discount_factors)):
        diff = abs(calc - expected)
        print(
            f"Tenor {spot_results['tenor'][i]:>3s}: "
            f"Calculated={calc:.7f}, Expected={expected:.7f}, Difference={diff:.7f}"
        )
        assert diff < 1e-5, f"Discount factor validation failed: Tenor {spot_results['tenor'][i]}"
    
    # Forward rate validation
    for i, (calc, expected) in enumerate(zip(forward_results['forward_rate'], expected_forward_rates)):
        assert abs(calc - expected) < 1e-5, f"Forward rate validation failed: Tenor {forward_results['tenor'][i]}"
    
    print("All calculation results validation passed!")


def main():
    """Main function: run all tests"""
    try:
        print("FR007 Interest Rate Swap Curve Test Program Started")
        print(f"Run Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Construct swap curve
        swap_curve, cal_usd, referenceDate = test_swap_curve_construction()
        
        # 2. Calculate spot rates and discount factors
        spot_results = test_spot_rates_calculation(swap_curve, cal_usd, referenceDate)
        
        # 3. Calculate forward rates
        forward_results = test_forward_rates_calculation(swap_curve, cal_usd, referenceDate)
        
        # 4. Validate results
        validate_results(spot_results, forward_results)
        
        print("\n" + "=" * 60)
        print("Program execution completed!")
        print("All calculations executed successfully")
        print("=" * 60)
        
        return {
            'swap_curve': swap_curve,
            'spot_results': spot_results,
            'forward_results': forward_results
        }
        
    except Exception as e:
        print(f"\nProgram execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run main program
    results = main()