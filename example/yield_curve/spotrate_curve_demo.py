"""
spotrate_curve_demo.py
Single-sided yield curve construction test program using spot rates

Functions:
1. Build single-sided yield curve
2. Test zero rate calculation for given dates
3. Test discount factor calculation for given dates
4. Test forward rate calculation for given tenors

Author: Mathema Team
"""

from typing import Tuple
from datetime import datetime, timedelta
from example.calendar.calendar_demo import McpNCalendar, usd_dates, GetCurrencyCalendar
from mcp.tool.tools_main import McpYieldCurve
from mcp.utils.enums import DayCounter, Frequency, InterpolatedVariable, InterpolationMethod

# Constant definitions
REFERENCE_DATE = '2024-12-13'
USD_CAL = GetCurrencyCalendar('USD', usd_dates)

def build_single_side_yield_curve():
    """
    Build single-sided yield curve
    
    Returns:
        McpYieldCurve: Constructed single-sided yield curve object
    """
    yc_args_usd = {
        'ReferenceDate': REFERENCE_DATE,
        'Tenors': ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M',
                  '10M', '11M', '1Y', '2Y', '3Y', '4Y', '5Y'],
        'ZeroRates': [0.0458, 0.04389, 0.045, 0.04389, 0.0433, 0.046, 0.0433,
                 0.0433, 0.0433, 0.0435, 0.0435, 0.0433, 0.0434, 0.0434, 0.0433, 
                 0.0433, 0.0433, 0.0433, 0.044000, 0.043, 0.042, 0.042],
        'Calendar': USD_CAL,
        'ShortName': 'USDSofrSnapYldCurve',
        'Symbol': 'USD',
        'DayCounter': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES,
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    return McpYieldCurve(yc_args_usd)

def test_yield_curve(yc):
    """
    测试收益率曲线功能
    
    参数:
        yc: McpYieldCurve对象
    """
    print("\n" + "="*50)
    print("收益率曲线测试开始")
    print("="*50)
    
    # 测试日期准备
    ref_date = datetime.strptime(REFERENCE_DATE, '%Y-%m-%d')
    test_dates = [
        ref_date + timedelta(days=7),   # 1周后
        ref_date + timedelta(days=30),  # 1个月后
        ref_date + timedelta(days=90),  # 3个月后
        ref_date + timedelta(days=365)  # 1年后
    ]
    
    # 1. 测试零息利率
    print("\n零息利率测试:")
    for date in test_dates:
        date_str = date.strftime('%Y-%m-%d')
        zero_rate = yc.ZeroRate(date_str)
        print(f"日期 {date_str} 的零息利率: {zero_rate:.6f}")
    
    # 2. 测试贴现因子
    print("\n贴现因子测试:")
    for date in test_dates:
        date_str = date.strftime('%Y-%m-%d')
        df = yc.DiscountFactor(date_str)
        print(f"日期 {date_str} 的贴现因子: {df:.6f}")
    
    # 3. 测试远期利率
    print("\n远期利率测试:")
    start_dates = test_dates[:-1]
    end_dates = test_dates[1:]
    for start, end in zip(start_dates, end_dates):
        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
        daycounter = DayCounter.Act365Fixed
        compounding = True
        frequency = Frequency.Annual
        fwd_rate = yc.ForwardRate(start_str, end_str, daycounter, compounding, frequency)
        print(f"从 {start_str} 到 {end_str} 的远期利率: {fwd_rate:.6f}")
    
    print("\n" + "="*50)
    print("收益率曲线测试完成")
    print("="*50)

def main():
    """主程序"""
    print("单边收益率曲线测试程序")
    print("参考日期:", REFERENCE_DATE)
    
    try:
        # 构建收益率曲线
        print("\n构建收益率曲线...")
        yc = build_single_side_yield_curve()
        print("收益率曲线构建成功!")
        
        # 测试曲线功能
        test_yield_curve(yc)
        
    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")
    finally:
        print("\n程序执行完毕")

if __name__ == "__main__":
    main()