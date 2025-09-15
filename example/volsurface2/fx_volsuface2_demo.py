"""
Test program demonstrating several features:
1. Build bilateral yield curve YieldCurve2
2. Build bilateral forward points curve FXForwardPointsCurve2
3. Build bilateral volatility surface FXVolSurface2
4. Query bilateral volatility surface

Note: Bilateral volatility surface requires bilateral interest rate curves and bilateral forward points curves to build

Author: Mathema Team

"""

from example.calendar.calendar_demo import McpNCalendar, usd_dates, cny_dates, GetCurrencyCalendar
from mcp.tool.tools_main import McpYieldCurve2, McpFXForwardPointsCurve2, McpFXVolSurface2
from mcp.utils.enums import DayCounter, DateAdjusterRule, DeltaType, Frequency, InterpolatedVariable, InterpolationMethod, CalculatedTarget, SmileInterpMethod


def test_fx_vol_surface2():
    """
    Test bilateral volatility surface construction functionality
    
    Returns:
        FXVolSurface2: Constructed bilateral volatility surface object
    """
    # 1. Initialize calendar objects
    cal = McpNCalendar(['USD', 'CNY'], [usd_dates, cny_dates])  # Create USD/CNY joint calendar
    cal_usd = GetCurrencyCalendar('USD', usd_dates)  # Separate USD calendar
    cal_cny = GetCurrencyCalendar('CNY', usd_dates)  # Separate CNY calendar
    
    # 2. Build USD yield curve
    yc_args_usd = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['ON', 'TN', 'SN', 'SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M',
                   '10M', '11M', '1Y', '2Y', '3Y', '4Y', '5Y'],
        'BidZeroRates': [0.0458, 0.0439, 0.045, 0.0439, 0.0433, 0.046, 0.0433, 0.0433, 0.0433, 0.0435, 
                         0.0435, 0.0433, 0.0434, 0.0434, 0.0433, 0.0433, 0.0433, 0.0433, 0.044, 0.043, 0.042, 0.042],
        'AskZeroRates': [0.0459, 0.0451, 0.0457, 0.0451, 0.0458, 0.0553, 0.0458, 0.0458, 0.0458, 0.046,
                         0.046, 0.0458, 0.0459, 0.0459, 0.0458, 0.0458, 0.0458, 0.0458, 0.0465, 0.046, 0.045, 0.045],
        'Calendar': cal_usd,
        'ShortName': 'USDSofrSnapYldCurve',
        'Symbol': 'USD',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES,
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    yc1 = McpYieldCurve2(yc_args_usd)  # USD yield curve
    
    # 3. Build CNY yield curve
    yc_args_cny = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['ON', '1W', '2W', '1M', '3M', '6M', '9M', '1Y'],
        'BidZeroRates': [0.01404, 0.01758, 0.0187, 0.0171, 0.01735, 0.01744, 0.01759, 0.01774],
        'AskZeroRates': [0.01404, 0.01758, 0.0187, 0.0171, 0.01735, 0.01744, 0.01759, 0.01774],
        'Calendar': cal_cny,
        'ShortName': 'CNYShibor3mSnapYldCurve',
        'Symbol': 'CNY',
        'DayCount': DayCounter.Act365Fixed,
        'Frequency': Frequency.Continuous,
        'Variable': InterpolatedVariable.SIMPLERATES,
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    yc2 = McpYieldCurve2(yc_args_cny)  # CNY收益率曲线
    
    # 4. 构建USD/CNY远期点曲线
    fw_args = {
        'ReferenceDate': '2024-12-13',
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', '11M', '1Y',
                   '18M', '2Y', '3Y', '4Y', '5Y'],
        'BidForwardPoints': [-39.5, -77.0, -116.0, -177.0, -360.35, -522.77, -709.23, -922.0, -1124.52, -1328.0,
                            -1531.0, -1749.28, -1940.0, -2145.0, -2388.0, -3450.0, -4330.0, -5696.61, -6000.0, -8050.0],
        'AskForwardPoints': [-35.5, -75.2, -114.0, -167.0, -348.43, -509.23, -704.0, -915.0, -1105.48, -1283.0,
                            -1486.0, -1724.72, -1896.6, -2103.3, -2358.0, -2860.0, -4230.0, -5463.39, -4900.0, -7550.0],
        'BidFXSpotRate': 7.2768,
        'AskFXSpotRate': 7.277,
        'Pair': 'USD/CNY',
        'Calendar': cal,
        'ShortName': 'USDCNYFwdSnapCurve',
        'Symbol': 'USD/CNY',
        'InterpolationMethod': InterpolationMethod.LINEARINTERPOLATION
    }
    fc = McpFXForwardPointsCurve2(fw_args)  # USD/CNY远期点曲线
    
    # 5. 构建USD/CNY波动率曲面 - 完整波动率数据
    bid_vols = [
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
    
    ask_vols = [
        [0.06631,0.06498,0.06366,0.06234,0.06103,0.05978,0.05861,0.05758,0.05675,0.05608,0.05562,0.05535,0.05526,0.05534,0.05558,0.05592,0.05631],
        [0.05783,0.05671,0.05557,0.05447,0.05335,0.05220,0.05107,0.05005,0.04925,0.04862,0.04824,0.04809,0.04817,0.04848,0.04906,0.04990,0.05083],
        [0.05859,0.05768,0.05674,0.05571,0.05459,0.05343,0.05230,0.05128,0.05050,0.04987,0.04949,0.04934,0.04942,0.04972,0.05023,0.05087,0.05159],
        [0.05807,0.05690,0.05575,0.05464,0.05362,0.05270,0.05192,0.05134,0.05100,0.05086,0.05094,0.05121,0.05163,0.05215,0.05275,0.05340,0.05407],
        [0.06153,0.06101,0.06045,0.05983,0.05913,0.05843,0.05782,0.05740,0.05725,0.05737,0.05779,0.05845,0.05931,0.06031,0.06141,0.06258,0.06377],
        [0.05805,0.05714,0.05627,0.05546,0.05476,0.05421,0.05388,0.05382,0.05400,0.05454,0.05536,0.05635,0.05741,0.05845,0.05938,0.06024,0.06105],
        [0.06145,0.06085,0.06027,0.05973,0.05926,0.05891,0.05876,0.05888,0.05916,0.05985,0.06083,0.06201,0.06331,0.06463,0.06591,0.06715,0.06838],
        [0.06320,0.06274,0.06231,0.06189,0.06153,0.06128,0.06123,0.06143,0.06175,0.06249,0.06355,0.06483,0.06624,0.06770,0.06915,0.07058,0.07199],
        [0.06431,0.06395,0.06360,0.06327,0.06297,0.06278,0.06279,0.06306,0.06338,0.06415,0.06526,0.06660,0.06808,0.06963,0.07118,0.07273,0.07426],
        [0.06464,0.06407,0.06356,0.06315,0.06291,0.06285,0.06302,0.06345,0.06375,0.06450,0.06561,0.06699,0.06859,0.07040,0.07237,0.07444,0.07654],
        [0.06439,0.06397,0.06361,0.06333,0.06319,0.06321,0.06344,0.06391,0.06412,0.06478,0.06586,0.06724,0.06892,0.07091,0.07319,0.07566,0.07821],
        [0.06577,0.06533,0.06495,0.06466,0.06448,0.06446,0.06467,0.06520,0.06526,0.06582,0.06701,0.06854,0.07039,0.07251,0.07487,0.07740,0.08000],
        [0.06703,0.06657,0.06616,0.06587,0.06573,0.06582,0.06619,0.06689,0.06675,0.06719,0.06839,0.06993,0.07181,0.07398,0.07641,0.07902,0.08167]
    ]
    
    # 将二维列表转换为分号分隔的字符串
    bid_vol_str = ';'.join([','.join([str(v) for v in row]) for row in bid_vols])
    ask_vol_str = ';'.join([','.join([str(v) for v in row]) for row in ask_vols])
    
    vol_args = {
        'ShortName': 'USDCNYRSnapVolSurface',
        'ReferenceDate': '2024-12-13',
        'Pair': 'USD/CNY',
        'Calendar': cal,
        'DayCounter': DayCounter.Act365Fixed,
        'DateAdjusterRule': DateAdjusterRule.ModifiedFollowing,
        'FxForwardPointsCurve2': fc,
        'ForeignCurve2': yc1,
        'DomesticCurve2': yc2,
        'CalculatedTarget': CalculatedTarget.CCY1,
        'DeltaStrings': ['10DPUT', '15DPUT', '20DPUT', '25DPUT', '30DPUT', '35DPUT', '40DPUT', '45DPUT', 'ATM',
                         '45DCAL', '40DCAL', '35DCAL', '30DCAL', '25DCAL', '20DCAL', '15DCAL', '10DCAL'],
        'Tenors': ['SW', '2W', '3W', '1M', '2M', '3M', '4M', '5M', '6M', '9M', '1Y', '18M', '2Y'],
        'BidVolatilities': bid_vols,
        'AskVolatilities': ask_vols,
        'SmileInterpMethod': SmileInterpMethod.CUBICSPLINE,
        'PremiumAdjusted': False,
        'IsATMFwd': True,
        'DeltaType': DeltaType.FORWARD_DELTA,
    }
    
    return McpFXVolSurface2(vol_args)  # 返回构建好的波动率曲面


def query_vol_surface(fx_vol, expiry_date, strike):
    """
    查询波动率曲面数据
    
    参数:
        fx_vol: MMktVolSurface2对象
        expiry_date: str, 到期日 'YYYY-MM-DD'
        strike: float, 执行价
        
    返回:
        dict: 包含查询结果的字典
    """
    results = {}
    
    # 查询利率
    results['ForeignRate_BID'] = fx_vol.GetForeignRate(expiry_date, False, 'BID')
    results['ForeignRate_ASK'] = fx_vol.GetForeignRate(expiry_date, False, 'ASK')
    results['DomesticRate_BID'] = fx_vol.GetDomesticRate(expiry_date, False, 'BID')
    results['DomesticRate_ASK'] = fx_vol.GetDomesticRate(expiry_date, False, 'ASK')
    
    # 查询波动率
    results['Volatility_BID'] = fx_vol.GetVolatility( strike, expiry_date, 'BID')
    results['Volatility_ASK'] = fx_vol.GetVolatility( strike, expiry_date, 'ASK')
    
    return results


def main():
    """
    主函数 - 执行市场波动率曲面测试和查询
    """
    print("="*50)
    print("外汇期权市场波动率曲面(双边)测试程序")
    print("="*50)
    
    try:
        # 1. 构建波动率曲面
        print("\n开始构建市场波动率曲面...")
        fx_vol = test_fx_vol_surface2()
        print("市场波动率曲面构建成功!\n")
        
        # 2. 测试查询功能
        test_cases = [
            {'expiry': '2024-12-18', 'strike': 7.0},
            {'expiry': '2025-01-15', 'strike': 7.1},
            {'expiry': '2025-03-20', 'strike': 7.2}
        ]
        
        for case in test_cases:
            print(f"\n测试查询 - 到期日: {case['expiry']}, 执行价: {case['strike']}")
            results = query_vol_surface(fx_vol, case['expiry'], case['strike'])
            
            print(f"USD利率(BID/ASK): {results['ForeignRate_BID']:.6f}/{results['ForeignRate_ASK']:.6f}")
            print(f"CNY利率(BID/ASK): {results['DomesticRate_BID']:.6f}/{results['DomesticRate_ASK']:.6f}")
            print(f"波动率(BID/ASK): {results['Volatility_BID']:.6f}/{results['Volatility_ASK']:.6f}")
        
    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")
    finally:
        print("\n程序执行完毕")


if __name__ == "__main__":
    main()