"""
spotrate_curve2_demo.py
Bilateral yield curve construction test program using spot rates

Functions:
1. Build bilateral yield curve (YieldCurve2)
2. Test zero rate calculation for given dates (BID/ASK)
3. Test discount factor calculation for given dates (BID/ASK)


Author: Mathema Team
"""

from typing import Tuple
from datetime import datetime, timedelta
from example.calendar.calendar_demo import McpNCalendar, usd_dates, GetCurrencyCalendar
from mcp.tool.tools_main import McpYieldCurve2
from mcp.utils.enums import DayCounter, Frequency, InterpolatedVariable, InterpolationMethod

# Constant definitions
REFERENCE_DATE = '2024-12-13'
USD_CAL = GetCurrencyCalendar('USD', usd_dates)

def build_double_side_yield_curve() -> McpYieldCurve2:
    """
    Build bilateral yield curve
    
    Returns:
        McpYieldCurve2: Constructed bilateral yield curve object
    """
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
    return McpYieldCurve2(yc_args_usd)

def test_yield_curve(yc: McpYieldCurve2):
    """
    Test bilateral yield curve functionality
    
    Parameters:
        yc: McpYieldCurve2 object
    """
    print("\n" + "="*50)
    print("Bilateral Yield Curve Test Started")
    print("="*50)
    
    # Prepare test dates
    ref_date = datetime.strptime(REFERENCE_DATE, '%Y-%m-%d')
    test_dates = [
        ref_date + timedelta(days=7),   # 1 week later
        ref_date + timedelta(days=30),  # 1 month later
        ref_date + timedelta(days=90),  # 3 months later
        ref_date + timedelta(days=365)  # 1 year later
    ]
    
    # 1. Test zero rates (BID/ASK)
    print("\nZero Rate Test (BID/ASK):")
    for date in test_dates:
        date_str = date.strftime('%Y-%m-%d')
        bid_rate = yc.ZeroRate(date_str, 'BID')
        ask_rate = yc.ZeroRate(date_str, 'ASK')
        print(f"Date {date_str} zero rates - BID: {bid_rate:.6f}, ASK: {ask_rate:.6f}")
    
    # 2. Test discount factors (BID/ASK)
    print("\nDiscount Factor Test (BID/ASK):")
    for date in test_dates:
        date_str = date.strftime('%Y-%m-%d')
        bid_df = yc.DiscountFactor(date_str, 'BID')
        ask_df = yc.DiscountFactor(date_str, 'ASK')
        print(f"Date {date_str} discount factors - BID: {bid_df:.6f}, ASK: {ask_df:.6f}")
    

    print("\n" + "="*50)
    print("Bilateral Yield Curve Test Completed")
    print("="*50)

def main():
    """Main program"""
    print("Bilateral Yield Curve Test Program")
    print("Reference Date:", REFERENCE_DATE)
    
    try:
        # Build yield curve
        print("\nBuilding bilateral yield curve...")
        yc = build_double_side_yield_curve()
        print("Bilateral yield curve constructed successfully!")
        
        # Test curve functionality
        test_yield_curve(yc)
        
    except Exception as e:
        print(f"\nProgram execution error: {str(e)}")
    finally:
        print("\nProgram execution completed")

if __name__ == "__main__":
    main()