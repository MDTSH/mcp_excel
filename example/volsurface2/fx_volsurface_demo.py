"""
Test program demonstrating single-sided volatility surface functionality:
1. Build single-sided yield curve YieldCurve
2. Build single-sided forward points curve FXForwardPointsCurve
3. Build single-sided volatility surface FXVolSurface
4. Query single-sided volatility surface

Note: Single-sided volatility surface only requires single-sided interest rate curve and single-sided forward points curve to build

Author: Mathema Team
"""

from example.calendar.calendar_demo import McpNCalendar, usd_dates, cny_dates, GetCurrencyCalendar
from mcp.tool.tools_main import McpYieldCurve, McpFXForwardPointsCurve, McpFXVolSurface
from mcp.utils.enums import DayCounter, DateAdjusterRule, DeltaType, Frequency, InterpolatedVariable, InterpolationMethod, CalculatedTarget, SmileInterpMethod


def construct_single_side_vol_surface():
    """
    Test single-sided market volatility surface construction functionality
    
    Returns:
        MMktVolSurface: Constructed single-sided volatility surface object
    """
    # 1. Initialize calendar objects
    cal = McpNCalendar(['USD', 'CNY'], [usd_dates, cny_dates])  # Create USD/CNY joint calendar
    cal_usd = GetCurrencyCalendar('USD', usd_dates)  # Separate USD calendar
    cal_cny = GetCurrencyCalendar('CNY', usd_dates)  # Separate CNY calendar
    
    # 2. Build USD single-sided yield curve
    yc_args_usd = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M',
                   '10M', '11M', '1Y', '2Y', '3Y', '4Y', '5Y'],
        'ZeroRates': [0.0458, 0.0439, 0.045, 0.0439, 0.0433, 0.046, 0.0433, 0.0433, 0.0433, 0.0435, 
                 0.0435, 0.0433, 0.0434, 0.0434, 0.0433, 0.0433, 0.0433, 0.0433, 0.044, 0.043, 0.042, 0.042],
        'Calendar': cal_usd,
        'ShortName': 'USDSofrSnapYldCurve',
        'Symbol': 'USD',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES,
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    yc_usd = McpYieldCurve(yc_args_usd)  # USD单边收益率曲线
    
    # 3. 构建CNY单边收益率曲线
    yc_args_cny = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['ON', '1W', '2W', '1M', '3M', '6M', '9M', '1Y'],
        'ZeroRates': [0.01404, 0.01758, 0.0187, 0.0171, 0.01735, 0.01744, 0.01759, 0.01774],
        'Calendar': cal_cny,
        'ShortName': 'CNYShibor3mSnapYldCurve',
        'Symbol': 'CNY',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES,
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    yc_cny = McpYieldCurve(yc_args_cny)  # CNY单边收益率曲线
    
    # 4. 构建USD/CNY单边远期点曲线
    fw_args = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', '11M', '1Y',
                   '18M', '2Y', '3Y', '4Y', '5Y'],
        'FXForwardPoints': [-39.5, -77.0, -116.0, -177.0, -360.35, -522.77, -709.23, -922.0, -1124.52, -1328.0,
                         -1531.0, -1749.28, -1940.0, -2145.0, -2388.0, -3450.0, -4330.0, -5696.61, -6000.0, -8050.0],
        'FXSpotRate': 7.2768,
        'Pair': 'USD/CNY',
        'Calendar': cal,
        'ShortName': 'USDCNYFwdSnapCurve',
        'Symbol': 'USD/CNY',
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION,
        'ScaleFactor': 10000
    }
    fc = McpFXForwardPointsCurve(fw_args)  # USD/CNY单边远期点曲线
    
    # 5. 构建USD/CNY单边波动率曲面
    vols  = [
        [0.05131,0.04998,0.04866,0.04734,0.04603,0.04478,0.04361,0.04258,0.04175,0.04108,0.04062,0.04035,0.04026,0.04034,0.04058,0.04092,0.04131],
        [0.05284,0.05215,0.05141,0.05047,0.04935,0.04820,0.04707,0.04605,0.04525,0.04462,0.04424,0.04409,0.04417,0.04448,0.04490,0.04534,0.04584],
        [0.05459,0.05368,0.05274,0.05171,0.05059,0.04943,0.04830,0.04728,0.04650,0.04587,0.04549,0.04534,0.04542,0.04572,0.04623,0.04687,0.04759],
        [0.05407,0.05290,0.05175,0.05064,0.04962,0.04870,0.04792,0.04734,0.04700,0.04686,0.04694,0.04721,0.04763,0.04815,0.04875,0.04940,0.05007],
        [0.05753,0.05701,0.05645,0.05583,0.05513,0.05443,0.05382,0.05340,0.05325,0.05337,0.05379,0.05445,0.05531,0.05631,0.05741,0.05858,0.05977],
        [0.05405,0.05314,0.05227,0.05146,0.05076,0.05021,0.04988,0.04982,0.05000,0.05054,0.05136,0.05235,0.05341,0.05445,0.05538,0.05624,0.05705],
        [0.05746,0.05686,0.05628,0.05574,0.05527,0.05492,0.05478,0.05489,0.05518,0.05586,0.05684,0.05803,0.05932,0.06065,0.06193,0.06317,0.06440],
        [0.05920,0.05875,0.05831,0.05790,0.05753,0.05729,0.05723,0.05744,0.05776,0.05850,0.05956,0.06084,0.06225,0.06371,0.06516,0.06659,0.06800],
        [0.06031,0.05995,0.05960,0.05927,0.05897,0.05878,0.05879,0.05906,0.05938,0.06015,0.06126,0.06260,0.06408,0.06563,0.06718,0.06873,0.07026],
        [0.06064,0.06007,0.05956,0.05915,0.05891,0.05885,0.05902,0.05945,0.05975,0.06050,0.06161,0.06299,0.06459,0.06640,0.06837,0.07044,0.07254],
        [0.06039,0.05997,0.05961,0.05933,0.05919,0.05921,0.05944,0.05991,0.06012,0.06078,0.06186,0.06324,0.06492,0.06691,0.06919,0.07166,0.07421],
        [0.05928,0.05884,0.05845,0.05817,0.05807,0.05819,0.05856,0.05919,0.05924,0.05980,0.06089,0.06228,0.06399,0.06602,0.06838,0.07091,0.07351],
        [0.05803,0.05757,0.05716,0.05687,0.05673,0.05682,0.05719,0.05789,0.05775,0.05819,0.05939,0.06093,0.06281,0.06498,0.06741,0.07002,0.07267]
    ]
    vol_str = ';'.join([','.join([str(v) for v in row]) for row in vols])
    
    vol_args = {
        'ShortName': 'USDCNYRSnapVolSurface',
        'ReferenceDate': '2024-12-13',
        'SpotDate': '2024-12-15',   
        'SpotPx': 7.2768,
        'Pair': 'USD/CNY',
        'Calendar': cal,
        'DayCounter': DayCounter.Act365Fixed,
        'DateAdjusterRule': DateAdjusterRule.ModifiedFollowing,
        'DomesticCurve': yc_cny,
        'ForeignCurve': yc_usd,
        'FxForwardPointsCurve': fc,
        'CalculatedTarget': CalculatedTarget.CCY1,
        'DeltaStrings': ['10DPUT', '15DPUT', '20DPUT', '25DPUT', '30DPUT', '35DPUT', '40DPUT', '45DPUT', 'ATM',
                         '45DCAL', '40DCAL', '35DCAL', '30DCAL', '25DCAL', '20DCAL', '15DCAL', '10DCAL'],
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '18M', '2Y'],
        'Volatilities': vols,
        'SmileInterpMethod': SmileInterpMethod.CUBICSPLINE,
        'DeltaType': DeltaType.FORWARD_DELTA,
        'PremiumAdjusted': False,
        'IsATMFwd': True,
    }
    
    return McpFXVolSurface(vol_args)  # 返回构建好的单边波动率曲面


def query_vol_surface(mkt_vol, expiry_date, strike):
    """
    查询波动率曲面数据
    
    参数:
        mkt_vol: MMktVolSurface对象
        expiry_date: str, 到期日 'YYYY-MM-DD'
        strike: float, 执行价
        
    返回:
        dict: 包含查询结果的字典
    """
    results = {}
    
    # 查询利率
    results['ForeignRate'] = mkt_vol.GetForeignRate(expiry_date)
    results['DomesticRate'] = mkt_vol.GetDomesticRate(expiry_date)
    
    # 查询波动率
    results['Volatility'] = mkt_vol.GetVolatility(strike, expiry_date)
    
    return results


def main():
    """
    主函数 - 执行单边市场波动率曲面测试和查询
    """
    print("="*50)
    print("外汇期权单边市场波动率曲面测试程序")
    print("="*50)
    
    try:
        # 1. 构建波动率曲面
        print("\n开始构建单边市场波动率曲面...")
        mkt_vol = construct_single_side_vol_surface()
        print("单边市场波动率曲面构建成功!\n")
        
        # 2. 测试查询功能
        test_cases = [
            {'expiry': '2024-12-18', 'strike': 7.0},
            {'expiry': '2025-01-15', 'strike': 7.1},
            {'expiry': '2025-03-20', 'strike': 7.2}
        ]
        
        for case in test_cases:
            print(f"\n测试查询 - 到期日: {case['expiry']}, 执行价: {case['strike']}")
            results = query_vol_surface(mkt_vol, case['expiry'], case['strike'])
            
            print(f"USD利率: {results['ForeignRate']:.6f}")
            print(f"CNY利率: {results['DomesticRate']:.6f}")
            print(f"波动率: {results['Volatility']:.6f}")
        
    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")
    finally:
        print("\n程序执行完毕")


if __name__ == "__main__":
    main()