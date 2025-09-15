#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FX Forward Points Curve (Single-sided) Demo Program

This program demonstrates how to use the MCP library to construct and operate single-sided FX forward points curves, including:
1. Construct McpFXForwardPointsCurve object
2. Calculate forward points for specified tenors
3. Calculate forward exchange rate prices
4. Support for standard and non-standard tenor calculations

Features:
- Single-sided quotes
- Support for multiple interpolation methods (linear interpolation, etc.)
- Support for standard tenors (ON, TN, SN, SW, 1M, 2M, etc.)
- Support for non-standard tenor (broken date) calculations
- Provide detailed calculation result output

Author: Mathema Team
Last Updated: 2024
"""

import pandas as pd
from datetime import datetime
from example.calendar.calendar_demo import McpNCalendar, usd_dates, cny_dates
from mcp.utils.enums import DateAdjusterRule
from mcp.tool.tools_main import McpFXForwardPointsCurve

def print_curve_parameters(args: dict) -> None:
    """Print single-sided curve construction parameters"""
    print("FX Forward Points Single-sided Curve Construction Parameters:")
    print(f"  Reference Date: {args['ReferenceDate']}")
    print(f"  Currency Pair: {args['Pair']}")
    print(f"  Spot Rate: {args['FXSpotRate']}")
    print(f"  Interpolation Method: {args['InterpolationMethod']}")
    print(f"  Number of Tenors: {len(args['Tenors'])}")
    print("\n  Tenors and Corresponding Forward Points:")
    for i, (tenor, points) in enumerate(zip(args['Tenors'], args['FXForwardPoints'])):
        print(f"    {i+1:2d}. {tenor:>4s}: {points:>8.1f}")

def test_forward_points_curve_basic():
    """Basic single-sided FX forward points curve test"""
    print("=" * 60)
    print("FX Forward Points Single-sided Curve Demo")
    print("=" * 60)
    
    # Construct calendar object
    cal = McpNCalendar(['USD', 'CNY'], [usd_dates, cny_dates])
    
    # Construct curve parameters (single-sided)
    args = {
        'ReferenceDate': '2024-8-9',
        'Tenors': ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M',
                   '11M', '1Y'],
        'FXForwardPoints': [-22.0, -7.4, -7.3, -53, -112, -169, -250, -496.6, -733, -956, -1192, -1393, -1580, -1761,
                         -1925.8, -2100, -2257.5, -2395],
        "FXSpotRate": 7.1650,
        "Pair": 'USD/CNY',
        'Calendar': cal,
        'InterpolationMethod': 'LINEARINTERPOLATION',
        'ScaleFactor': 10000,
    }
    
    # Print construction parameters
    print_curve_parameters(args)
    
    print("\nConstructing single-sided forward points curve...")
    curve = McpFXForwardPointsCurve(args)
    print("Single-sided curve constructed successfully!")
    
    # Calculate spot value date
    spot_date = cal.ValueDate(args['ReferenceDate'])
    print(f"\nSpot Value Date: {spot_date}")
    
    return curve, cal, spot_date

def test_standard_tenors_calculation(curve, cal, spot_date):
    """Test standard tenor calculations"""
    print("\n" + "=" * 60)
    print("Standard Tenor Forward Points and Exchange Rate Calculations")
    print("=" * 60)
    
    # Test tenors
    test_tenors = ['2W', '1M', '2M', '3M', '6M', '1Y']
    
    results = []
    for tenor in test_tenors:
        # Calculate expiry date
        expire_date = cal.AddPeriod(spot_date, tenor, DateAdjusterRule.Following)
        
        # Calculate forward points
        points = curve.FXForwardPoints(expire_date)
        
        # Calculate forward exchange rate
        rate = curve.FXForwardOutright(expire_date)
        
        results.append({
            'tenor': tenor,
            'expire_date': expire_date,
            'points': points,
            'rate': rate
        })
        
        print(f"Tenor {tenor:>3s}:")
        print(f"  Expiry Date: {expire_date}")
        print(f"  Forward Points: {points:>8.2f}")
        print(f"  Forward Rate: {rate:>8.4f}")
        print()
    
    return results

def test_broken_date_calculation(curve, cal):
    """Test non-standard tenor date calculations"""
    print("=" * 60)
    print("Non-standard Tenor Date Forward Points Calculations")
    print("=" * 60)
    
    # Test non-standard tenor dates
    broken_dates = ['2024-10-10', '2024-11-15', '2024-12-20']
    
    results = []
    for broken_date in broken_dates:
        # Calculate forward points
        points = curve.FXForwardPoints(broken_date)
        
        # Calculate forward exchange rate
        rate = curve.FXForwardOutright(broken_date)
        
        results.append({
            'date': broken_date,
            'points': points,
            'rate': rate
        })
        
        print(f"Non-standard tenor date: {broken_date}")
        print(f"  Forward Points: {points:>8.2f}")
        print(f"  Forward Rate: {rate:>8.4f}")
        print()
    
    return results

def create_summary_dataframe(standard_results, broken_results):
    """Create summary results table"""
    print("\n" + "=" * 60)
    print("Calculation Results Summary Table")
    print("=" * 60)
    
    # Standard tenor results
    print("\nStandard Tenor Results:")
    df_standard = pd.DataFrame(standard_results)
    display_cols = ['tenor', 'expire_date', 'points', 'rate']
    df_display = df_standard[display_cols].copy()
    
    # Format numerical values
    df_display['points'] = df_display['points'].round(2)
    df_display['rate'] = df_display['rate'].round(4)
    
    print(df_display.to_string(index=False))
    
    # Non-standard tenor date results
    print("\nNon-standard Tenor Date Results:")
    df_broken = pd.DataFrame(broken_results)
    display_cols_broken = ['date', 'points', 'rate']
    df_broken_display = df_broken[display_cols_broken].copy()
    
    # Format numerical values
    df_broken_display['points'] = df_broken_display['points'].round(2)
    df_broken_display['rate'] = df_broken_display['rate'].round(4)
    
    print(df_broken_display.to_string(index=False))
    
    return df_standard, df_broken

def main():
    """Main function: run all demo features"""
    try:
        print("FX Forward Points Single-sided Curve Demo Program Started")
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Basic curve construction
        curve, cal, spot_date = test_forward_points_curve_basic()
        
        # 2. Standard tenor calculations
        standard_results = test_standard_tenors_calculation(curve, cal, spot_date)
        
        # 3. Non-standard tenor date calculations
        broken_results = test_broken_date_calculation(curve, cal)
        
        # 4. Create summary table
        df_standard, df_broken = create_summary_dataframe(standard_results, broken_results)
        
        print("\n" + "=" * 60)
        print("Program execution completed!")
        print("All single-sided calculations executed successfully")
        print("=" * 60)
        
        return {
            'curve': curve,
            'standard_results': df_standard,
            'broken_results': df_broken
        }
        
    except Exception as e:
        print(f"\nProgram execution error: {str(e)}")
        return None

if __name__ == "__main__":
    # Run main program
    results = main()